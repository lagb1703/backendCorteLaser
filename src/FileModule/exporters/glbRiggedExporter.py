from dataclasses import dataclass
from math import atan2, cos, sin

import geopandas as gpd
import numpy as np
from shapely import LineString, MultiLineString, Polygon
from shapely.ops import unary_union
import trimesh  # type: ignore

from src.FileModule.exporters.gltfSkinWriter import (
    GltfSkinWriter,
    RigNode,
    RigPrimitive,
)
from src.FileModule.exporters.meshExporter import MeshExporter


@dataclass
class BendHinge:
    lineIndex: int
    axis: LineString
    firstPiece: int
    secondPiece: int


class GlbRiggedExporter(MeshExporter):
    """Create a skinned GLB whose bend joints rotate around local X."""

    sheetThickness = 0.01
    boneHeight = sheetThickness / 2
    intersectionEpsilon = 1e-8

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        polygonList, linesList = self.splitGeometries(geometries)
        solidPolygons = self.buildSolidPolygons(polygonList)
        allBendLines = unary_union(linesList) if linesList else None

        identity = np.eye(4, dtype=np.float64)
        nodes: list[RigNode] = [
            RigNode(
                name="rig_root",
                localMatrix=identity.copy(),
                parent=None,
                isJoint=True,
                extras={"type": "rig-root"},
            )
        ]
        worldBindByNode: dict[int, np.ndarray] = {0: identity.copy()}
        inverseBindMatrices: list[np.ndarray] = [identity.copy()]
        platePrimitives: list[RigPrimitive] = []
        lineJointSlots: dict[int, int] = {}
        lineJointCounts: dict[int, int] = {}

        for partIndex, solidPolygon in enumerate(solidPolygons):
            pieces = self.splitSolidPolygon(solidPolygon, allBendLines)
            if not pieces:
                continue
            hinges = self.__buildHinges(pieces, linesList)
            pieceControllers = self.__buildPartRig(
                partIndex,
                pieces,
                hinges,
                nodes,
                worldBindByNode,
                inverseBindMatrices,
                lineJointSlots,
                lineJointCounts,
            )
            for pieceIndex, piece in enumerate(pieces):
                jointSlot = pieceControllers[pieceIndex]
                primitive = self.__createPiecePrimitive(piece, jointSlot)
                if primitive is not None:
                    platePrimitives.append(primitive)

        for lineIndex, lineString in enumerate(linesList):
            if not lineString.geoms:
                continue
            lineMesh = self.createBendLineMesh(lineString)
            if lineMesh is None:
                continue
            jointSlot = lineJointSlots.get(lineIndex, 0)
            platePrimitives.append(
                RigPrimitive(
                    vertices=np.asarray(lineMesh.vertices),
                    normals=np.asarray(lineMesh.vertex_normals),
                    faces=np.asarray(lineMesh.faces),
                    jointIndices=np.full(len(lineMesh.vertices), jointSlot),
                    material=1,
                )
            )

        return GltfSkinWriter().write(
            nodes,
            inverseBindMatrices,
            platePrimitives,
        )

    def __buildHinges(
        self,
        pieces: list[Polygon],
        linesList: list[MultiLineString],
    ) -> list[BendHinge]:
        hinges: list[BendHinge] = []
        seen: set[tuple[int, int, int]] = set()
        for lineIndex, lineString in enumerate(linesList):
            if not lineString.geoms:
                continue
            axis = lineString.geoms[0]
            if not isinstance(axis, LineString) or axis.length <= self.intersectionEpsilon:
                continue
            coordinates = list(axis.coords)
            start = np.asarray(coordinates[0][:2], dtype=np.float64)
            end = np.asarray(coordinates[-1][:2], dtype=np.float64)
            direction = end - start
            length = float(np.linalg.norm(direction))
            if length <= self.intersectionEpsilon:
                continue

            positive: list[tuple[float, int]] = []
            negative: list[tuple[float, int]] = []
            for pieceIndex, piece in enumerate(pieces):
                intersection = piece.boundary.intersection(axis)
                if intersection.is_empty or intersection.length <= self.intersectionEpsilon:
                    continue
                reference = piece.representative_point()
                relative = np.asarray(
                    [reference.x, reference.y], dtype=np.float64
                ) - start
                crossProduct = direction[0] * relative[1] - direction[1] * relative[0]
                sideEpsilon = self.intersectionEpsilon * max(length, 1.0)
                if abs(crossProduct) <= sideEpsilon:
                    continue
                position = axis.project(intersection.representative_point())
                if crossProduct > 0:
                    positive.append((float(position), pieceIndex))
                else:
                    negative.append((float(position), pieceIndex))

            positive.sort()
            negative.sort()
            for (_, positivePiece), (_, negativePiece) in zip(positive, negative):
                if positivePiece == negativePiece:
                    continue
                pair = tuple(sorted((positivePiece, negativePiece)))
                key = (lineIndex, pair[0], pair[1])
                if key in seen:
                    continue
                seen.add(key)
                hinges.append(
                    BendHinge(
                        lineIndex=lineIndex,
                        axis=axis,
                        firstPiece=pair[0],
                        secondPiece=pair[1],
                    )
                )
        return hinges

    def __buildPartRig(
        self,
        partIndex: int,
        pieces: list[Polygon],
        hinges: list[BendHinge],
        nodes: list[RigNode],
        worldBindByNode: dict[int, np.ndarray],
        inverseBindMatrices: list[np.ndarray],
        lineJointSlots: dict[int, int],
        lineJointCounts: dict[int, int],
    ) -> dict[int, int]:
        incident: dict[int, list[BendHinge]] = {
            index: [] for index in range(len(pieces))
        }
        for hinge in hinges:
            incident[hinge.firstPiece].append(hinge)
            incident[hinge.secondPiece].append(hinge)

        pieceControllers: dict[int, int] = {}
        pieceControllerNodes: dict[int, int] = {}
        visited: set[int] = set()
        componentIndex = 0
        pieceOrder = sorted(
            range(len(pieces)), key=lambda index: pieces[index].area, reverse=True
        )

        for rootPiece in pieceOrder:
            if rootPiece in visited:
                continue
            rootName = f"part_{partIndex}_root"
            if componentIndex:
                rootName = f"{rootName}_{componentIndex}"
            rootNodeIndex = len(nodes)
            identity = np.eye(4, dtype=np.float64)
            nodes.append(
                RigNode(
                    name=rootName,
                    localMatrix=identity.copy(),
                    parent=0,
                    isJoint=True,
                    extras={
                        "type": "part-root",
                        "part": partIndex,
                    },
                )
            )
            worldBindByNode[rootNodeIndex] = identity.copy()
            rootJointSlot = len(inverseBindMatrices)
            inverseBindMatrices.append(identity.copy())
            pieceControllers[rootPiece] = rootJointSlot
            pieceControllerNodes[rootPiece] = rootNodeIndex
            visited.add(rootPiece)
            queue = [rootPiece]

            while queue:
                parentPiece = queue.pop(0)
                for hinge in incident[parentPiece]:
                    childPiece = (
                        hinge.secondPiece
                        if hinge.firstPiece == parentPiece
                        else hinge.firstPiece
                    )
                    if childPiece in visited:
                        continue

                    parentNodeIndex = pieceControllerNodes[parentPiece]
                    parentWorldBind = worldBindByNode[parentNodeIndex]
                    targetWorldBind = self.__axisBindMatrix(hinge.axis)
                    localMatrix = np.linalg.inv(parentWorldBind) @ targetWorldBind
                    occurrence = lineJointCounts.get(hinge.lineIndex, 0)
                    lineJointCounts[hinge.lineIndex] = occurrence + 1
                    jointName = f"bend_line_{hinge.lineIndex}"
                    if occurrence:
                        jointName = f"{jointName}_{occurrence}"
                    alignNodeIndex = len(nodes)
                    nodes.append(
                        RigNode(
                            name=f"{jointName}_align",
                            localMatrix=localMatrix,
                            parent=parentNodeIndex,
                        )
                    )
                    worldBindByNode[alignNodeIndex] = targetWorldBind
                    jointNodeIndex = len(nodes)
                    nodes.append(
                        RigNode(
                            name=jointName,
                            localMatrix=np.eye(4, dtype=np.float64),
                            parent=alignNodeIndex,
                            isJoint=True,
                            extras=self.__bendExtras(
                                hinge, partIndex, occurrence
                            ),
                        )
                    )
                    worldBindByNode[jointNodeIndex] = targetWorldBind
                    jointSlot = len(inverseBindMatrices)
                    inverseBindMatrices.append(np.linalg.inv(targetWorldBind))
                    lineJointSlots.setdefault(hinge.lineIndex, jointSlot)
                    pieceControllers[childPiece] = jointSlot
                    pieceControllerNodes[childPiece] = jointNodeIndex
                    visited.add(childPiece)
                    queue.append(childPiece)
            componentIndex += 1

        return pieceControllers

    def __createPiecePrimitive(
        self, piece: Polygon, jointSlot: int
    ) -> RigPrimitive | None:
        vertices: list[tuple[float, ...]] = list(piece.exterior.coords)[:-1]
        ringEndIndices = [len(vertices)]
        for interior in piece.interiors:
            vertices.extend(list(interior.coords)[:-1])
            ringEndIndices.append(len(vertices))
        if not vertices:
            return None
        mesh = self.createExtrudedMesh(vertices, ringEndIndices)
        return RigPrimitive(
            vertices=np.asarray(mesh.vertices),
            normals=np.asarray(mesh.vertex_normals),
            faces=np.asarray(mesh.faces),
            jointIndices=np.full(len(mesh.vertices), jointSlot),
            material=0,
        )

    def __axisBindMatrix(self, axis: LineString) -> np.ndarray:
        coordinates = list(axis.coords)
        start = np.asarray(coordinates[0][:2], dtype=np.float64)
        end = np.asarray(coordinates[-1][:2], dtype=np.float64)
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length <= self.intersectionEpsilon:
            raise ValueError("A bend line must have a non-zero axis")
        direction /= length
        angle = atan2(float(direction[1]), float(direction[0]))
        rotation = np.array(
            [
                [cos(angle), -sin(angle), 0.0],
                [sin(angle), cos(angle), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        midpoint = (start + end) / 2
        matrix = np.eye(4, dtype=np.float64)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = [midpoint[0], midpoint[1], self.boneHeight]
        return matrix

    def __bendExtras(
        self, hinge: BendHinge, partIndex: int, occurrence: int
    ) -> dict[str, object]:
        coordinates = list(hinge.axis.coords)
        start = np.asarray(coordinates[0][:2], dtype=np.float64)
        end = np.asarray(coordinates[-1][:2], dtype=np.float64)
        direction = end - start
        length = float(np.linalg.norm(direction))
        direction /= length
        return {
            "type": "bend-line",
            "bendLineIndex": hinge.lineIndex,
            "occurrence": occurrence,
            "part": partIndex,
            "start": [float(start[0]), float(start[1]), self.boneHeight],
            "end": [float(end[0]), float(end[1]), self.boneHeight],
            "axis": [float(direction[0]), float(direction[1]), 0.0],
        }

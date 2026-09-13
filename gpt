from dataclasses import dataclass
from io import BytesIO
from math import atan2, cos, sin

import geopandas as gpd
import numpy as np
from shapely import LineString, MultiLineString, Polygon
from shapely.ops import unary_union
import trimesh  # type: ignore

from src.FileModule.exporters.meshExporter import MeshExporter


@dataclass
class BendHinge:
    lineIndex: int
    axis: LineString
    firstPiece: int
    secondPiece: int


class GlbExporter(MeshExporter):
    """Create a GLB whose son nodes fold around their own bend line.

    Every piece is emitted as its own node. A son node's local matrix places
    its origin on the bend line it hangs from, with local +X along that line,
    and its mesh is baked into that frame. Rotating a son around its local X
    therefore folds it exactly on the bend line, and its own sons follow.
    """

    sheetThickness = 0.01
    hingeHeight = sheetThickness / 2
    intersectionEpsilon = 1e-8

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        polygonList, linesList = self.splitGeometries(geometries)
        solidPolygons = self.buildSolidPolygons(polygonList)
        allBendLines = unary_union(linesList) if linesList else None

        scene = trimesh.Scene()
        counters = {"son": 0, "father": 0}

        for partIndex, solidPolygon in enumerate(solidPolygons):
            pieces = self.splitSolidPolygon(solidPolygon, allBendLines)
            if not pieces:
                continue
            hinges = self.__buildHinges(pieces, linesList)
            self.__addPartNodes(scene, partIndex, pieces, hinges, counters)

        buffer = BytesIO()
        scene.export(buffer, file_type="glb")
        return buffer.getvalue()

    def __addPartNodes(
        self,
        scene: trimesh.Scene,
        partIndex: int,
        pieces: list[Polygon],
        hinges: list[BendHinge],
        counters: dict[str, int],
    ) -> None:
        incident: dict[int, list[BendHinge]] = {
            index: [] for index in range(len(pieces))
        }
        for hinge in hinges:
            incident[hinge.firstPiece].append(hinge)
            incident[hinge.secondPiece].append(hinge)

        frames: dict[int, np.ndarray] = {}
        nodeNames: dict[int, str] = {}
        lineOccurrences: dict[int, int] = {}
        visited: set[int] = set()
        pieceOrder = sorted(
            range(len(pieces)), key=lambda index: pieces[index].area, reverse=True
        )

        for rootPiece in pieceOrder:
            if rootPiece in visited:
                continue
            rootName = "father" if counters["father"] == 0 else f"father{counters['father']}"
            counters["father"] += 1
            identity = np.eye(4, dtype=np.float64)
            frames[rootPiece] = identity
            nodeNames[rootPiece] = rootName
            visited.add(rootPiece)
            self.__addPieceNode(
                scene,
                pieces[rootPiece],
                rootName,
                None,
                identity,
                identity,
                {
                    "type": "part-root",
                    "role": "father",
                    "nodeId": rootName,
                    "part": int(partIndex),
                },
            )

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

                    frame = self.__hingeFrame(hinge.axis, pieces[childPiece])
                    localMatrix = np.linalg.inv(frames[parentPiece]) @ frame
                    occurrence = lineOccurrences.get(hinge.lineIndex, 0)
                    lineOccurrences[hinge.lineIndex] = occurrence + 1
                    nodeName = f"son{counters['son']}"
                    counters["son"] += 1

                    frames[childPiece] = frame
                    nodeNames[childPiece] = nodeName
                    visited.add(childPiece)
                    self.__addPieceNode(
                        scene,
                        pieces[childPiece],
                        nodeName,
                        nodeNames[parentPiece],
                        localMatrix,
                        frame,
                        self.__bendExtras(
                            hinge,
                            partIndex,
                            occurrence,
                            nodeName,
                            nodeNames[parentPiece],
                            frame,
                        ),
                    )
                    queue.append(childPiece)

    def __addPieceNode(
        self,
        scene: trimesh.Scene,
        piece: Polygon,
        nodeName: str,
        parentNodeName: str | None,
        localMatrix: np.ndarray,
        frame: np.ndarray,
        extras: dict[str, object],
    ) -> None:
        vertices: list[tuple[float, ...]] = list(piece.exterior.coords)[:-1]
        ringEndIndices = [len(vertices)]
        for interior in piece.interiors:
            vertices.extend(list(interior.coords)[:-1])
            ringEndIndices.append(len(vertices))
        if not vertices:
            return

        mesh = self.createExtrudedMesh(vertices, ringEndIndices)
        mesh.apply_transform(np.linalg.inv(frame))
        scene.add_geometry(
            mesh,
            node_name=nodeName,
            geom_name=f"{nodeName}_mesh",
            parent_node_name=parentNodeName,
            transform=localMatrix,
            metadata=extras,
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

    def __hingeFrame(self, axis: LineString, childPiece: Polygon) -> np.ndarray:
        coordinates = list(axis.coords)
        start = np.asarray(coordinates[0][:2], dtype=np.float64)
        end = np.asarray(coordinates[-1][:2], dtype=np.float64)
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length <= self.intersectionEpsilon:
            raise ValueError("A bend line must have a non-zero axis")
        direction = direction / length

        # Keep the folded piece on the local +Y side so that a positive angle
        # always folds the same way, whatever direction the DXF drew the line in.
        midpoint = (start + end) / 2
        reference = childPiece.representative_point()
        relative = np.asarray([reference.x, reference.y], dtype=np.float64) - midpoint
        if direction[0] * relative[1] - direction[1] * relative[0] < 0:
            direction = -direction

        angle = atan2(float(direction[1]), float(direction[0]))
        rotation = np.array(
            [
                [cos(angle), -sin(angle), 0.0],
                [sin(angle), cos(angle), 0.0],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )
        matrix = np.eye(4, dtype=np.float64)
        matrix[:3, :3] = rotation
        matrix[:3, 3] = [midpoint[0], midpoint[1], self.hingeHeight]
        return matrix

    def __bendExtras(
        self,
        hinge: BendHinge,
        partIndex: int,
        occurrence: int,
        nodeName: str,
        parentNodeName: str,
        frame: np.ndarray,
    ) -> dict[str, object]:
        coordinates = list(hinge.axis.coords)
        start = np.asarray(coordinates[0][:2], dtype=np.float64)
        end = np.asarray(coordinates[-1][:2], dtype=np.float64)
        direction = np.asarray(frame[:2, 0], dtype=np.float64)
        return {
            "type": "bend-node",
            "role": "son",
            "nodeId": nodeName,
            "parentId": parentNodeName,
            "part": int(partIndex),
            "bendLineIndex": int(hinge.lineIndex),
            "occurrence": int(occurrence),
            "start": [float(start[0]), float(start[1]), self.hingeHeight],
            "end": [float(end[0]), float(end[1]), self.hingeHeight],
            "axis": [float(direction[0]), float(direction[1]), 0.0],
        }

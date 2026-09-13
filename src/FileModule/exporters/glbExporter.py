from dataclasses import dataclass
from io import BytesIO
from math import atan2

import geopandas as gpd
import numpy as np
import trimesh  # type: ignore
from shapely import LineString, Point, Polygon
from shapely.ops import unary_union

from src.FileModule.exporters.meshExporter import MeshExporter


@dataclass
class Hinge:
    """The edge two pieces share after a bend line cut them apart."""

    firstPiece: int
    secondPiece: int
    pivot: np.ndarray
    axis: np.ndarray
    lineIndex: int
    # The bend line this hinge lies on, or the shared edge itself when the cut
    # cannot be traced back to one.
    axisLine: LineString


class GlbExporter(MeshExporter):
    """Create a GLB whose son nodes fold around their own bend line.

    Every piece becomes its own node. A son node's frame sits on the bend line
    it hangs from, at half the sheet thickness, with local +X along that line
    and the piece itself on local +Y; its mesh is baked into that frame.
    Rotating a son around its local X therefore folds it exactly on the bend
    line, a positive angle always folds upwards, and its own sons follow
    because they live in its frame.
    """

    sheetThickness = 0.01
    pivotHeight = sheetThickness / 2
    epsilon = 1e-9

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        polygonList, linesList = self.splitGeometries(geometries)
        solidPolygons = self.buildSolidPolygons(polygonList)
        # Only the first geometry of each group is the bend line; the rest mark
        # the extent of its bend zone and must not cut the part.
        bendAxes = [lineString.geoms[0] for lineString in linesList if lineString.geoms]
        allLines = unary_union(bendAxes) if bendAxes else None

        scene = trimesh.Scene()
        counters = {"father": 0, "son": 0}

        for partIndex, solidPolygon in enumerate(solidPolygons):
            pieces = self.splitSolidPolygon(solidPolygon, allLines)
            if not pieces:
                continue
            hinges = self.__buildHinges(pieces, bendAxes)
            self.__addPartNodes(scene, partIndex, pieces, hinges, counters)

        buffer = BytesIO()
        scene.export(buffer, file_type="glb")
        return buffer.getvalue()

    def __addPartNodes(
        self,
        scene: trimesh.Scene,
        partIndex: int,
        pieces: list[Polygon],
        hinges: list[Hinge],
        counters: dict[str, int],
    ) -> None:
        incident: dict[int, list[Hinge]] = {
            index: [] for index in range(len(pieces))
        }
        for hinge in hinges:
            incident[hinge.firstPiece].append(hinge)
            incident[hinge.secondPiece].append(hinge)

        frames: dict[int, np.ndarray] = {}
        nodeNames: dict[int, str] = {}
        # A slot can interrupt one bend line, so it hinges more than one pair.
        lineOccurrences: dict[int, int] = {}
        visited: set[int] = set()
        pieceOrder = sorted(
            range(len(pieces)), key=lambda index: pieces[index].area, reverse=True
        )

        for rootPiece in pieceOrder:
            if rootPiece in visited:
                continue
            rootName = (
                "father" if counters["father"] == 0 else f"father{counters['father']}"
            )
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

                    axis = self.__orientAxis(
                        hinge.axis, hinge.pivot, pieces[childPiece]
                    )
                    frame = self.__hingeFrame(hinge.pivot, axis)
                    # Both frames are expressed in world space, so cancelling
                    # the parent's leaves the child's matrix relative to it.
                    localMatrix = np.linalg.inv(frames[parentPiece]) @ frame
                    nodeName = f"son{counters['son']}"
                    counters["son"] += 1
                    occurrence = lineOccurrences.get(hinge.lineIndex, 0)
                    lineOccurrences[hinge.lineIndex] = occurrence + 1

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
                            axis,
                            partIndex,
                            occurrence,
                            nodeName,
                            nodeNames[parentPiece],
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
        vertices: list[tuple[float, ...]] = self.ringCoordinates(piece.exterior)
        ringEnds = [len(vertices)]
        for interior in piece.interiors:
            vertices.extend(self.ringCoordinates(interior))
            ringEnds.append(len(vertices))
        if not vertices:
            return

        mesh = self.createExtrudedMesh(vertices, ringEnds)
        # Bake the mesh into its own frame, so that localMatrix @ meshLocal
        # puts every vertex back where the flat sheet had it.
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
        self, pieces: list[Polygon], bendAxes: list[LineString]
    ) -> list[Hinge]:
        hinges: list[Hinge] = []
        for firstIndex in range(len(pieces)):
            for secondIndex in range(firstIndex + 1, len(pieces)):
                sharedEdge = self.__sharedEdge(pieces[firstIndex], pieces[secondIndex])
                if sharedEdge is None:
                    continue
                axis = self.__edgeDirection(sharedEdge)
                if axis is None:
                    continue
                middle = sharedEdge.interpolate(0.5, normalized=True)
                pivot = np.array(
                    [middle.x, middle.y, self.pivotHeight], dtype=np.float64
                )
                lineIndex = self.__bendLineOf(middle, bendAxes)
                hinges.append(
                    Hinge(
                        firstIndex,
                        secondIndex,
                        pivot,
                        axis,
                        lineIndex,
                        bendAxes[lineIndex] if lineIndex >= 0 else sharedEdge,
                    )
                )
        return hinges

    def __bendLineOf(self, middle: Point, bendAxes: list[LineString]) -> int:
        """Which bend line the shared edge was cut along, -1 when none of them.

        The edge is a piece of that line, so its middle sits on it; anything
        further away is a cut this exporter did not make from a bend.
        """
        if not bendAxes:
            return -1
        closest = min(range(len(bendAxes)), key=lambda i: bendAxes[i].distance(middle))
        return closest if bendAxes[closest].distance(middle) <= self.epsilon else -1

    def __sharedEdge(
        self, firstPiece: Polygon, secondPiece: Polygon
    ) -> LineString | None:
        shared = firstPiece.boundary.intersection(secondPiece.boundary)
        if shared.is_empty or shared.length <= self.epsilon:
            return None
        if isinstance(shared, LineString):
            return shared
        # A corner touch adds points to the intersection; keep the longest line.
        segments = [
            geometry
            for geometry in getattr(shared, "geoms", [])
            if isinstance(geometry, LineString) and geometry.length > self.epsilon
        ]
        return max(segments, key=lambda segment: segment.length) if segments else None

    def __edgeDirection(self, sharedEdge: LineString) -> np.ndarray | None:
        coordinates = list(sharedEdge.coords)
        start = np.asarray(coordinates[0][:2], dtype=np.float64)
        end = np.asarray(coordinates[-1][:2], dtype=np.float64)
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length <= self.epsilon:
            return None
        return np.array(
            [direction[0] / length, direction[1] / length, 0.0], dtype=np.float64
        )

    def __hingeFrame(self, pivot: np.ndarray, axis: np.ndarray) -> np.ndarray:
        # Turn local +X onto the bend line, which puts the piece on local +Y,
        # so that folding is a plain rotation around the node's own X axis.
        frame = trimesh.transformations.rotation_matrix(
            atan2(float(axis[1]), float(axis[0])), [0.0, 0.0, 1.0]
        )
        frame[:3, 3] = pivot
        return frame

    def __orientAxis(
        self, axis: np.ndarray, pivot: np.ndarray, childPiece: Polygon
    ) -> np.ndarray:
        # Keep the folded piece on the left of the axis, so that a positive
        # angle always folds upwards whatever direction the DXF drew the line.
        reference = childPiece.representative_point()
        relative = np.array(
            [reference.x - pivot[0], reference.y - pivot[1]], dtype=np.float64
        )
        crossProduct = axis[0] * relative[1] - axis[1] * relative[0]
        return -axis if crossProduct < 0 else axis

    def __bendExtras(
        self,
        hinge: Hinge,
        axis: np.ndarray,
        partIndex: int,
        occurrence: int,
        nodeName: str,
        parentNodeName: str,
    ) -> dict[str, object]:
        # The fold is always a rotation around the node's own X axis; `axis` is
        # that same direction read in the flat sheet, for the front end to show.
        # `start` and `end` span the whole bend line, while `bendPivot` sits on
        # the stretch of it where the two pieces really touch. It cannot be
        # called `pivot`: three.js reserves `userData.pivot` and, on any node
        # that has children, moves the node and zeroes its first child to
        # rebuild a pivot its own exporter writes, which tears the part apart.
        start, end = self.__bendLineEnds(hinge)
        return {
            "type": "bend-node",
            "role": "son",
            "nodeId": nodeName,
            "parentId": parentNodeName,
            "part": int(partIndex),
            "bendLineIndex": int(hinge.lineIndex),
            "occurrence": int(occurrence),
            "start": start,
            "end": end,
            "bendPivot": [float(value) for value in hinge.pivot],
            "axis": [float(value) for value in axis],
        }

    def __bendLineEnds(self, hinge: Hinge) -> tuple[list[float], list[float]]:
        coordinates = list(hinge.axisLine.coords)
        return (
            [float(coordinates[0][0]), float(coordinates[0][1]), self.pivotHeight],
            [float(coordinates[-1][0]), float(coordinates[-1][1]), self.pivotHeight],
        )

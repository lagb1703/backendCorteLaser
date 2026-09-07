from abc import ABC
from shapely.affinity import scale
from typing import Hashable

import geopandas as gpd
import pandas as pd
import mapbox_earcut as earcut
import numpy as np
import trimesh  # type: ignore
from shapely import Geometry, MultiLineString, Polygon
from shapely.ops import split, unary_union

from src.FileModule.exporters.geometryExporter import GeometryExporter


class MeshExporter(GeometryExporter, ABC):

    def splitGeometries(
        self, geometries: gpd.GeoSeries
    ) -> tuple[list[Polygon], list[MultiLineString]]:
        polygonList: list[Polygon] = geometries[
            geometries.geometry.geom_type == "Polygon"
        ].tolist()
        linesList: list[MultiLineString] = geometries[
            geometries.geometry.geom_type == "MultiLineString"
        ].tolist()
        return polygonList, linesList

    def buildHierarchy(
        self, polygonList: list[Polygon]
    ) -> tuple[pd.DataFrame, dict[Hashable, list[int]]]:
        gdf = gpd.GeoDataFrame(geometry=polygonList)
        if gdf.empty:
            return gdf, {}

        gdf["width"] = gdf.geometry.bounds["maxx"] - gdf.geometry.bounds["minx"]
        gdf["high"] = gdf.geometry.bounds["maxy"] - gdf.geometry.bounds["miny"]
        gdf = gdf.sort_values(by=["width", "high"], ascending=[False, False])
        shrunk_gdf = gdf.copy()
        shrunk_gdf["geometry"] = shrunk_gdf.geometry.buffer(-1e-5)

        # Eliminar geometrías que se hayan colapsado por ser demasiado pequeñas
        valid_shrunk = shrunk_gdf[~shrunk_gdf.is_empty]
        joined = gpd.sjoin(gdf, valid_shrunk, how="inner", predicate="covers")  # type: ignore
        childrenMap: dict[Hashable, list[int]] = {}
        for leftIndex, group in joined.groupby(joined.index):
            childrenMap[leftIndex] = [int(right) for right in group["index_right"]]
        return gdf, childrenMap

    def buildSolidPolygons(self, polygonList: list[Polygon]) -> list[Polygon]:
        parents: dict[int, int | None] = {}
        for childIndex, child in enumerate(polygonList):
            containingPolygons = [
                (parent.area, parentIndex)
                for parentIndex, parent in enumerate(polygonList)
                if parentIndex != childIndex
                and parent.area > child.area
                and parent.covers(child)
            ]
            parents[childIndex] = (
                min(containingPolygons)[1] if containingPolygons else None
            )

        depths: dict[int, int] = {}

        def getDepth(index: int) -> int:
            if index in depths:
                return depths[index]
            parent = parents[index]
            depths[index] = 0 if parent is None else getDepth(parent) + 1
            return depths[index]

        solidPolygons: list[Polygon] = []
        for index, polygon in enumerate(polygonList):
            if getDepth(index) % 2 != 0:
                continue
            holesCoordinates = [list(interior.coords) for interior in polygon.interiors]
            for childIndex, parent in parents.items():
                if parent == index and getDepth(childIndex) == getDepth(index) + 1:
                    holesCoordinates.append(
                        list(polygonList[childIndex].exterior.coords)
                    )
            solidPolygons.append(
                Polygon(shell=list(polygon.exterior.coords), holes=holesCoordinates)
            )
        return solidPolygons

    def splitSolidPolygon(
        self, solidPolygon: Polygon, splitter: Geometry | None
    ) -> list[Polygon]:
        if splitter is None or splitter.is_empty:
            return [solidPolygon]

        # Overshoot each bend line a little so `split` can cut all the way
        # across the polygon. Scaling about each line's own centroid keeps it
        # collinear; scaling about the origin would displace it off the bend.
        parts = splitter.geoms if hasattr(splitter, "geoms") else [splitter]
        splitter = unary_union(
            [scale(part, xfact=1.01, yfact=1.01, origin="centroid") for part in parts]
        )
        splitResult = split(solidPolygon, splitter)
        pieces: list[Polygon] = []
        geometries = (
            splitResult.geoms if hasattr(splitResult, "geoms") else [splitResult]
        )
        for geometry in geometries:
            if isinstance(geometry, Polygon):
                pieces.append(geometry)
            elif geometry.geom_type == "MultiPolygon":
                pieces.extend(geometry.geoms)
        return pieces

    def createExtrudedMesh(
        self, vertices: list[tuple[float, ...]], holeIndices: list[int]
    ) -> trimesh.Trimesh:
        verticesFormat = np.array(vertices, dtype=np.float64)[:, :2]
        faces = earcut.triangulate_float64(
            verticesFormat, np.asarray(holeIndices, dtype=np.uint32)
        )
        faces = faces.reshape(int(faces.shape[0] / 3), 3)
        mesh = trimesh.creation.extrude_triangulation(verticesFormat, faces, 0.01)
        mesh.visual.face_colors = [0, 0, 255, 255]  # type: ignore
        return mesh

    def createBendLineMesh(self, lineString: MultiLineString) -> trimesh.Trimesh | None:
        coords = list(lineString.geoms[0].coords)
        vertices: list[tuple[float, float, float]] = []
        faces: list[list[int]] = []
        thickness = 0.0005
        for i in range(len(coords) - 1):
            x1, y1 = coords[i][0], coords[i][1]
            x2, y2 = coords[i + 1][0], coords[i + 1][1]
            dx, dy = x2 - x1, y2 - y1
            length = (dx**2 + dy**2) ** 0.5
            if length == 0:
                continue
            nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
            baseIndex = len(vertices)
            vertices.extend(
                [
                    (x1 + nx, y1 + ny, 0.011),
                    (x1 - nx, y1 - ny, 0.011),
                    (x2 - nx, y2 - ny, 0.011),
                    (x2 + nx, y2 + ny, 0.011),
                ]
            )
            faces.extend(
                [
                    [baseIndex, baseIndex + 1, baseIndex + 2],
                    [baseIndex, baseIndex + 2, baseIndex + 3],
                ]
            )

        if not vertices:
            return None

        mesh = trimesh.Trimesh(vertices=np.array(vertices), faces=np.array(faces))
        mesh.visual.face_colors = [255, 0, 0, 255]  # type: ignore
        return mesh

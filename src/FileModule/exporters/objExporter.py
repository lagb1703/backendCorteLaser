from io import BytesIO

import geopandas as gpd
from shapely import Geometry, Polygon
import trimesh  # type: ignore

from src.FileModule.exporters.meshExporter import MeshExporter


class ObjExporter(MeshExporter):

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        meshes: list[trimesh.Trimesh] = []
        polygonList, linesList = self.splitGeometries(geometries)
        gdf, childrenMap = self.buildHierarchy(polygonList)
        processed: set[int] = set()

        for index in gdf.index:
            if index in processed:
                continue
            polygon: Geometry = polygonList[index]
            if not isinstance(polygon, Polygon):
                continue
            childIndices = [
                child
                for child in childrenMap.get(index, [])
                if child != index and child not in processed
            ]
            processed.add(index)
            processed.update(childIndices)
            vertices: list[tuple[float, ...]] = self.ringCoordinates(polygon.exterior)
            holeIndices: list[int] = []
            for childIndex in childIndices:
                geometry: Geometry = gdf.loc[childIndex, "geometry"]
                if not isinstance(geometry, Polygon):
                    continue
                holeIndices.append(len(vertices))
                vertices.extend(self.ringCoordinates(geometry.exterior))
            holeIndices.append(len(vertices))
            meshes.append(self.createExtrudedMesh(vertices, holeIndices))

        """for lineString in linesList:
            mesh = self.createBendLineMesh(lineString)
            if mesh is not None:
                meshes.append(mesh)"""

        scene = trimesh.Scene(meshes)
        buffer = BytesIO()
        scene.export(buffer, file_type="obj")
        return buffer.getvalue()

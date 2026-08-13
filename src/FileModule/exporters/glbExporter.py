from io import BytesIO

import geopandas as gpd
from shapely import Geometry, Polygon
from shapely.ops import split, unary_union
import trimesh  # type: ignore

from src.FileModule.exporters.meshExporter import MeshExporter


class GlbExporter(MeshExporter):

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        polygonList, linesList = self.splitGeometries(geometries)
        gdf, childrenMap = self.buildHierarchy(polygonList)
        processed: set[int] = set()
        solidPolygons: list[Polygon] = []

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
            holesCoordinates = []
            for childIndex in childIndices:
                geometry: Geometry = gdf.loc[childIndex, "geometry"]
                if isinstance(geometry, Polygon):
                    holesCoordinates.append(geometry.exterior.coords)
            solidPolygons.append(
                Polygon(shell=polygon.exterior.coords, holes=holesCoordinates)
            )

        allBendLines = unary_union(linesList) if linesList else None
        scene = trimesh.Scene()
        meshCount = 0

        for solidPolygon in solidPolygons:
            if allBendLines is not None and not allBendLines.is_empty:
                slicedResult = split(solidPolygon, allBendLines)
                pieces: list[Polygon] = []
                if hasattr(slicedResult, "geoms"):
                    for geometry in slicedResult.geoms:
                        if geometry.geom_type == "Polygon":
                            pieces.append(geometry)
                        elif geometry.geom_type == "MultiPolygon":
                            pieces.extend(geometry.geoms)
                elif slicedResult.geom_type == "Polygon":
                    pieces.append(slicedResult)
            else:
                pieces = [solidPolygon]

            rootNode: str | None = None
            for pieceIndex, piece in enumerate(pieces):
                vertices = list(piece.exterior.coords)[:-1]
                holeIndices: list[int] = []
                for interior in piece.interiors:
                    holeIndices.append(len(vertices))
                    vertices.extend(list(interior.coords)[:-1])
                if not vertices:
                    continue
                holeIndices.append(len(vertices))

                mesh = self.createExtrudedMesh(vertices, holeIndices)
                if pieceIndex == 0:
                    nodeName = f"base_plate_{meshCount}"
                    scene.add_geometry(mesh, node_name=nodeName)
                    rootNode = nodeName
                else:
                    nodeName = f"flap_{meshCount}_{pieceIndex}"
                    scene.add_geometry(
                        mesh, node_name=nodeName, parent_node_name=rootNode
                    )

            meshCount += 1

        for lineIndex, lineString in enumerate(linesList):
            lineMesh = self.createBendLineMesh(lineString)
            if lineMesh is not None:
                scene.add_geometry(
                    lineMesh, node_name=f"bend_line_axis_{lineIndex}"
                )

        buffer = BytesIO()
        scene.export(buffer, file_type="glb")
        return buffer.getvalue()

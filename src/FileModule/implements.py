from operator import le
from typing import Hashable
from fastapi import HTTPException
import numpy as np
import mapbox_earcut as earcut
from src.FileModule.geometriesAnalyzer import GeometriesAnalyzer
from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.enums import ExceptionsEnum
from io import StringIO, BytesIO, TextIOWrapper
from shapely import (
    Polygon,
    touches,
    wkb,
    MultiPolygon,
    MultiLineString,
    GeometryCollection,
    Geometry,
)
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.affinity import scale, translate
from ezdxf.filemanagement import read  # type: ignore
from ezdxf.lldxf.const import DXFStructureError  # type: ignore
from shapely.ops import polygonize, split, unary_union
from ezdxf import path
from shapely.geometry import LineString
import trimesh  # type: ignore
import numpy as np  # type: ignore


class ShapelyAnalyzer(GeometriesAnalyzer):

    def __init__(self, geometries: list[Geometry]):
        self.__geometries = gpd.GeoSeries(geometries)

    def checkGeometries(self) -> bool:
        validGeometry: bool = bool(
            self.__geometries.notna().all() and self.__geometries.is_valid.all()
        )
        gdf = gpd.GeoDataFrame({"geometry": self.__geometries})
        candidates = gpd.sjoin(gdf, gdf, how="inner", predicate="intersects")
        overlaps: list[tuple[int, int]] = []
        for _, row in candidates.iterrows():
            i = int(row.name)  # type: ignore
            j = int(row["index_right"])
            if i >= j:
                continue
            b1 = gdf.loc[i, "geometry"].boundary  # type: ignore
            b2 = gdf.loc[j, "geometry"].boundary  # type: ignore
            if touches(b1, b2):  # type: ignore
                overlaps.append((i, j))
        return validGeometry and len(overlaps) == 0

    def getMinimumRectangle(self) -> tuple[float, float, float, float]:
        union = self.__geometries.unary_union  # type: ignore
        rect = union.minimum_rotated_rectangle
        minx, miny, maxx, maxy = rect.bounds
        return (float(minx), float(miny), float(maxx), float(maxy))

    def getPerimeter(self) -> float:
        union = self.__geometries.unary_union  # type: ignore
        return union.length

    def createImage(self) -> bytes:
        fig, ax = plt.subplots(figsize=(6, 6))  # type: ignore
        self.__geometries[self.__geometries.geom_type == "Polygon"].plot(ax=ax, facecolor="none", edgecolor="black")  # type: ignore
        self.__geometries[self.__geometries.geom_type == "MultiLineString"].plot(ax=ax, facecolor="none", edgecolor="red")  # type: ignore
        ax.set_aspect("equal")
        ax.axis("off")
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)  # type: ignore
        plt.close(fig)
        image_bytes = buf.getvalue()
        buf.close()
        return image_bytes

    def createOBJ(self) -> bytes:
        meshes: list[trimesh.Trimesh] = []
        poly_list: list[Polygon] = self.__geometries[
            self.__geometries.geometry.geom_type == "Polygon"
        ].tolist()
        lines_list: list[MultiLineString] = self.__geometries[
            self.__geometries.geometry.geom_type == "MultiLineString"
        ].tolist()
        gdf = gpd.GeoDataFrame(geometry=poly_list)
        gdf["width"] = gdf.geometry.bounds["maxx"] - gdf.geometry.bounds["minx"]
        gdf["high"] = gdf.geometry.bounds["maxy"] - gdf.geometry.bounds["miny"]
        gdf = gdf.sort_values(by=["width", "high"], ascending=[False, False])
        joined = gpd.sjoin(gdf, gdf, how="inner", predicate="intersects")  # type: ignore
        children_map: dict[Hashable, list[int]] = {}
        for left_idx, group in joined.groupby(joined.index):
            children_map[left_idx] = [int(r) for r in group["index_right"]]
        processed: set[int] = set()
        for idx in gdf.index:
            if idx in processed:
                continue
            polygon: Geometry = poly_list[idx]
            if not isinstance(polygon, Polygon):
                continue
            child_indices = [
                c for c in children_map.get(idx, []) if c != idx and c not in processed
            ]
            processed.add(idx)
            processed.update(child_indices)
            vertices: list[tuple[float, ...]] = list(polygon.exterior.coords)[:-1]
            holes = []
            for ci in child_indices:
                geo: Geometry = gdf.loc[ci, "geometry"]
                if not isinstance(geo, Polygon):
                    continue
                holes.append(len(vertices))
                vertices.extend(list(geo.exterior.coords)[:-1])
            holes.append(len(vertices))
            verticesFormat = np.array(vertices, dtype=np.float64)[:, :2]
            faces = earcut.triangulate_float64(
                verticesFormat, np.asarray(holes, dtype=np.uint32)
            )
            faces = faces.reshape(int(faces.shape[0] / 3), 3)
            mesh = trimesh.creation.extrude_triangulation(verticesFormat, faces, 0.01)
            mesh.visual.face_colors = [0, 0, 255, 255]  # type: ignore
            meshes.append(mesh)
        for lineString in lines_list:
            coords = list(lineString.geoms[0].coords)
            vertices = []
            faces = []
            thickness = 0.0005
            for i in range(len(coords) - 1):
                x1, y1 = coords[i][0], coords[i][1]
                x2, y2 = coords[i + 1][0], coords[i + 1][1]
                dx, dy = x2 - x1, y2 - y1
                length = (dx**2 + dy**2) ** 0.5
                if length == 0:
                    continue
                nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
                base_idx = len(vertices)
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
                        [base_idx, base_idx + 1, base_idx + 2],
                        [base_idx, base_idx + 2, base_idx + 3],
                    ]
                )
            if vertices:
                mesh = trimesh.Trimesh(
                    vertices=np.array(vertices), faces=np.array(faces)
                )
                mesh.visual.face_colors = [255, 0, 0, 255]  # type: ignore
                meshes.append(mesh)
        scene = trimesh.Scene(meshes)
        buf = BytesIO()
        scene.export(buf, file_type="obj")
        return buf.getvalue()

    def createGlb(self) -> bytes:
        # 1. Filter out raw geometries
        poly_list: list[Polygon] = self.__geometries[
            self.__geometries.geometry.geom_type == "Polygon"
        ].tolist()
        lines_list: list[MultiLineString] = self.__geometries[
            self.__geometries.geometry.geom_type == "MultiLineString"
        ].tolist()
        # 2. Process hierarchy maps to determine which polygons are holes
        gdf = gpd.GeoDataFrame(geometry=poly_list)
        gdf["width"] = gdf.geometry.bounds["maxx"] - gdf.geometry.bounds["minx"]
        gdf["high"] = gdf.geometry.bounds["maxy"] - gdf.geometry.bounds["miny"]
        gdf = gdf.sort_values(by=["width", "high"], ascending=[False, False])
        joined = gpd.sjoin(gdf, gdf, how="inner", predicate="intersects")  # type: ignore
        children_map: dict = {}
        for left_idx, group in joined.groupby(joined.index):
            children_map[left_idx] = [int(r) for r in group["index_right"]]
        processed: set[int] = set()
        solid_polygons: list[Polygon] = []
        # Assemble true Shapely Polygons with their native holes intact
        for idx in gdf.index:
            if idx in processed:
                continue
            polygon = poly_list[idx]
            if not isinstance(polygon, Polygon):
                continue
            child_indices = [
                c for c in children_map.get(idx, []) if c != idx and c not in processed
            ]
            processed.add(idx)
            processed.update(child_indices)
            # Gather all child polygon coordinate loops acting as holes
            holes_coords = []
            for ci in child_indices:
                geo = gdf.loc[ci, "geometry"]
                if isinstance(geo, Polygon):
                    holes_coords.append(geo.exterior.coords)
            # Build the complete unified shape with its inner holes
            solid_poly = Polygon(shell=polygon.exterior.coords, holes=holes_coords)
            solid_polygons.append(solid_poly)
        # 3. Combine all bend lines into a unified slicing structure
        all_bend_lines = unary_union(lines_list) if lines_list else None
        scene = trimesh.Scene()
        mesh_count = 0
        # 4. Iterate over solid bodies, slice them, and construct the GLB Scene Tree
        for solid_poly in solid_polygons:
            # Slice the object along the bend lines if they exist
            if all_bend_lines and not all_bend_lines.is_empty:
                sliced_result = split(solid_poly, all_bend_lines)
                pieces = []
                if hasattr(sliced_result, "geoms"):
                    for g in sliced_result.geoms:
                        if g.geom_type == "Polygon":
                            pieces.append(g)
                        elif g.geom_type == "MultiPolygon":
                            pieces.extend(g.geoms)
                else:
                    if sliced_result.geom_type == "Polygon":
                        pieces.append(sliced_result)
            else:
                pieces = [solid_poly]

            # 5. Triangulate and extrude each piece independently
            root_node = None
            for p_idx, piece in enumerate(pieces):
                # Formulate the earcut arrays for this specific slice
                vertices = list(piece.exterior.coords)[:-1]
                holes = []

                # If a hole was cut in half by a bend line, Shapely automatically
                # turns it into a valid boundary or internal interior ring here!
                for interior in piece.interiors:
                    holes.append(len(vertices))
                    vertices.extend(list(interior.coords)[:-1])

                if not vertices:
                    continue

                verticesFormat = np.array(vertices, dtype=np.float64)[:, :2]
                faces = earcut.triangulate_float64(
                    verticesFormat, np.asarray(holes, dtype=np.uint32)
                )
                faces = faces.reshape(int(faces.shape[0] / 3), 3)

                # Extrude the isolated piece
                mesh = trimesh.creation.extrude_triangulation(
                    verticesFormat, faces, 0.01
                )
                mesh.visual.face_colors = [0, 0, 255, 255]  # Blue Sheet Metal

                # Establish explicit Parent-Child relations for frontend target parsing
                if p_idx == 0:
                    node_name = f"base_plate_{mesh_count}"
                    scene.add_geometry(mesh, node_name=node_name)
                    root_node = node_name
                else:
                    node_name = f"flap_{mesh_count}_{p_idx}"
                    scene.add_geometry(
                        mesh, node_name=node_name, parent_node_name=root_node
                    )

            mesh_count += 1

        # 6. Preserve your original red visual markers for the bend lines
        for l_idx, lineString in enumerate(lines_list):
            coords = list(lineString.geoms[0].coords)
            vertices = []
            faces = []
            thickness = 0.0005
            for i in range(len(coords) - 1):
                x1, y1 = coords[i][0], coords[i][1]
                x2, y2 = coords[i + 1][0], coords[i + 1][1]
                dx, dy = x2 - x1, y2 - y1
                length = (dx**2 + dy**2) ** 0.5
                if length == 0:
                    continue
                nx, ny = -dy / length * thickness / 2, dx / length * thickness / 2
                base_idx = len(vertices)
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
                        [base_idx, base_idx + 1, base_idx + 2],
                        [base_idx, base_idx + 2, base_idx + 3],
                    ]
                )
            if vertices:
                line_mesh = trimesh.Trimesh(
                    vertices=np.array(vertices), faces=np.array(faces)
                )
                line_mesh.visual.face_colors = [255, 0, 0, 255]  # Red line
                scene.add_geometry(line_mesh, node_name=f"bend_line_axis_{l_idx}")

        # 7. Export natively to binary GLB
        buf = BytesIO()
        scene.export(buf, file_type="glb")
        return buf.getvalue()

    def save(self) -> bytes:
        geometries_list = self.__geometries.tolist()
        geom_collection = GeometryCollection(geometries_list)
        return wkb.dumps(geom_collection)  # type: ignore


class DxfAdapter(GeometriesAdapter[Geometry]):

    unitsToMeters: dict[int, float] = {
        0: 0,
        1: 0.0254,
        2: 0.3048,
        3: 1609.34,
        4: 0.001,
        5: 0.01,
        6: 1.0,
        7: 1000.0,
        8: 2.54e-08,
        9: 2.54e-05,
        10: 0.9144,
        11: 1e-10,
        12: 1e-09,
        13: 1e-06,
        14: 0.1,
        15: 10.0,
        16: 100.0,
        17: 1e09,
        18: 1.495978707e11,
        19: 9.461e15,
        20: 3.086e16,
    }

    def makeGeometries(self, data: bytes) -> list[Geometry]:
        buf = None
        try:
            buf = TextIOWrapper(BytesIO(data), encoding="latin-1")
            doc = read(buf)
        except DXFStructureError:
            try:
                if buf is not None:
                    buf.close()
                buf = StringIO(data.decode("utf-8", errors="replace"))
                doc = read(buf)
            except Exception as e:
                raise ValueError(f"Failed to parse DXF data: {e}") from e
        finally:
            if buf is not None:
                try:
                    buf.detach()
                except Exception:
                    try:
                        buf.close()
                    except Exception:
                        pass
        msp = doc.modelspace()
        geoms: list[LineString] = []
        geometries: list[Geometry] = []
        for entity in msp.query("*[layer!='BEND']").query("*[layer!='BEND_EXTENT']"):
            try:
                p_path = path.make_path(entity)
                vertices = list(p_path.flattening(distance=0.01))
                if len(vertices) < 2:
                    continue
                if p_path.is_closed:
                    geometries.append(Polygon(vertices))
                else:
                    geoms.append(LineString(vertices))
            except Exception:
                continue
        units = doc.units
        if units == 0:
            raise HTTPException(
                404,
                ExceptionsEnum.BAD_FILE.name.replace(":file", "").replace(
                    ":description", "falta de unidades de medida"
                ),
            )
        convertFactor = DxfAdapter.unitsToMeters.get(units)
        if convertFactor is None:
            raise HTTPException(
                404,
                ExceptionsEnum.BAD_FILE.name.replace(":file", "").replace(
                    ":description", "unidad desconocida"
                ),
            )
        geometries.extend(polygonize(geoms))
        stringLines: list[MultiLineString] = []
        for line in msp.query("*[layer=='BEND']"):
            p_path = path.make_path(line)
            vertices = list(p_path.flattening(distance=0.1))
            stringLines.append(MultiLineString([LineString(vertices)]))
        for i, line in enumerate(msp.query("*[layer=='BEND_EXTENT']")):
            p_path = path.make_path(line)
            vertices = list(p_path.flattening(distance=0.1))
            line = LineString(vertices)
            index = 0
            minDis: float = 0xFFFFFFFFFF
            for j, stringLine in enumerate(stringLines):
                distance = stringLine.geoms[0].distance(line)
                if distance < minDis:
                    index = j
                    minDis = distance
            msl = list(stringLines[index].geoms)
            msl.append(line)
            stringLines[index] = MultiLineString(msl)
        geometries.extend(stringLines)
        all_bounds = gpd.GeoSeries(geometries).total_bounds
        cx = (all_bounds[0] + all_bounds[2]) / 2
        cy = (all_bounds[1] + all_bounds[3]) / 2
        scaledGeometries: list[Geometry] = []
        for poly in geometries:
            p = translate(poly, -cx, -cy)
            p = scale(p, xfact=convertFactor, yfact=convertFactor, origin=(0, 0, 0))
            scaledGeometries.append(p)
        return scaledGeometries


class WKBAdapter(GeometriesAdapter[Geometry]):

    def makeGeometries(self, data: bytes) -> list[Geometry]:
        try:
            if isinstance(data, (bytes, bytearray)):
                try:
                    data_str = data.decode("ascii").strip()
                    if all(c in "0123456789abcdefABCDEF" for c in data_str):
                        geom = wkb.loads(data_str)
                    else:
                        geom = wkb.loads(data)
                except (UnicodeDecodeError, Exception):
                    geom = wkb.loads(data)
            else:
                geom = wkb.loads(data)
            return self.__flatten(geom)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"No se pudo decodificar WKB: {e}")

    def __flatten(self, geom: Geometry) -> list[Geometry]:
        if isinstance(geom, (Polygon, LineString)):
            return [geom]
        if isinstance(geom, (MultiPolygon,)):
            return list(geom.geoms)
        if isinstance(geom, GeometryCollection):
            result: list[Geometry] = []
            for g in geom.geoms:
                result.extend(self.__flatten(g))
            return result
        return [geom]

from fastapi import HTTPException
import copy
import numpy as np
from math import inf
import mapbox_earcut as earcut
from src.FileModule.geometriesAnalyzer import GeometriesAnalyzer
from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.enums import ExceptionsEnum
from io import StringIO, BytesIO, TextIOWrapper
from shapely import Point, Polygon, touches, wkb, MultiPolygon, GeometryCollection  # type: ignore
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.affinity import scale
from ezdxf.filemanagement import read  # type: ignore
from ezdxf.lldxf.const import DXFStructureError  # type: ignore
from shapely.ops import polygonize
from ezdxf import path
from shapely.geometry import LineString
import trimesh  # type: ignore
import numpy as np  # type: ignore


class ShapelyAnalyzer(GeometriesAnalyzer):

    def __init__(self, geometries: list[Polygon]):
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
        self.__geometries.plot(ax=ax, facecolor="none", edgecolor="black")  # type: ignore
        ax.set_aspect("equal")
        ax.axis("off")
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", pad_inches=0)  # type: ignore
        plt.close(fig)
        image_bytes = buf.getvalue()
        buf.close()
        return image_bytes

    def createOBJ(self, thickness: float = 1.0) -> bytes:
        meshes = []
        poly_list: list[Polygon] = self.__geometries.tolist()
        maxArea: float = -inf
        index: int = 0
        for i, poly in enumerate(poly_list):
            minX, minY, maxX, maxY = poly.bounds
            area = abs(maxX - minX) * abs(maxY - minY)
            if maxArea < area:
                maxArea = area
                index = i
        nut: Polygon = poly_list[index]
        nminX, nminY, nmaxX, nmaxY = nut.bounds
        allIn: bool = True
        for i, poly in enumerate(self.__geometries):
            if i == index:
                continue
            minX, minY, maxX, maxY = poly.bounds
            allIn &= nminX < minX and nminY < minY and nmaxX > maxX and nmaxY > maxY
        holes: list[int] = []
        vertices: list[tuple[float, ...]] = []
        if allIn:
            vertices.extend(list(nut.exterior.coords)[:-1])
            for i, poly in enumerate(self.__geometries):
                if i == index:
                    continue
                ext_coords = list(poly.exterior.coords)[:-1]
                holes.append(len(vertices))
                vertices.extend(ext_coords)
            holes.append(len(vertices))
            verticesFormat = np.zeros((len(vertices), 2)).astype(np.float64)
            for i in range(len(vertices)):
                vertex = np.asarray(vertices[i], dtype=np.float64)
                verticesFormat[i][0] = vertex[0]
                verticesFormat[i][1] = vertex[1]
            faces = earcut.triangulate_float64(
                verticesFormat, np.asarray(holes, dtype=np.uint32)
            )
            faces = faces.reshape(int(faces.shape[0] / 3), 3)
            meshes.append(trimesh.Trimesh(vertices=vertices, faces=faces))
        else:
            gdf = gpd.GeoDataFrame(geometry=poly_list)
            gdf["width"] = gdf.geometry.bounds["maxx"] - gdf.geometry.bounds["minx"]
            gdf["high"] = gdf.geometry.bounds["maxy"] - gdf.geometry.bounds["miny"]
            gdf = gdf.sort_values(by=["width", "high"], ascending=[False, False])
            processed: set[int] = set()
            for idx in gdf.index:
                if idx in processed:
                    continue
                polygon: Polygon = poly_list[idx]
                children = gdf.sjoin(
                    gpd.GeoDataFrame(geometry=[polygon]),
                    how="inner",
                )
                print(f"{children=}")
                child_indices = [
                    int(c) for c in children.index if c != idx and c not in processed
                ]
                print(f"{child_indices=}")
                processed.add(idx)
                processed.update(child_indices)
                vertices: list[tuple[float, ...]] = list(polygon.exterior.coords)[:-1]
                holes = []
                for ci in child_indices:
                    holes.append(len(vertices))
                    vertices.extend(list(gdf.loc[ci, "geometry"].exterior.coords)[:-1])
                holes.append(len(vertices))
                verticesFormat = np.zeros((len(vertices), 2), dtype=np.float64)
                for i, v in enumerate(vertices):
                    verticesFormat[i] = v[:2]
                faces = earcut.triangulate_float64(
                    verticesFormat, np.asarray(holes, dtype=np.uint32)
                )
                faces = faces.reshape(int(faces.shape[0] / 3), 3)
                meshes.append(trimesh.Trimesh(vertices=vertices, faces=faces))
        scene = trimesh.Scene(meshes)
        buf = BytesIO()
        scene.export(buf, file_type="obj")
        return buf.getvalue()

    def save(self) -> bytes:
        geometries_list = self.__geometries.tolist()
        geom_collection = GeometryCollection(geometries_list)
        return wkb.dumps(geom_collection)  # type: ignore


class DxfAdapter(GeometriesAdapter[Polygon]):

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

    def makeGeometries(self, data: bytes) -> list[Polygon]:
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
        polygons: list[Polygon] = []
        layers = set(entity.dxf.layer for entity in doc.modelspace())
        print(layers)
        for entity in msp.query("*[layer!='BEND']").query("*[layer!='BEND_EXTENT']"):
            try:
                p_path = path.make_path(entity)
                vertices = list(p_path.flattening(distance=0.01))
                if len(vertices) < 2:
                    continue
                if p_path.is_closed:
                    polygons.append(Polygon(vertices))
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
        polygons.extend(polygonize(geoms))
        scaledPolygons: list[Polygon] = []
        for poly in polygons:
            p = scale(poly, xfact=convertFactor, yfact=convertFactor, origin=(0, 0, 0))
            scaledPolygons.append(p)
        print(f"{len(scaledPolygons)=}")
        return scaledPolygons


class WKBAdapter(GeometriesAdapter[Polygon]):

    def makeGeometries(self, data: bytes) -> list[Polygon]:
        try:
            geom = wkb.loads(data)
            if isinstance(geom, Polygon):
                return [geom]
            elif isinstance(geom, MultiPolygon):
                return list(geom.geoms)
            elif isinstance(geom, GeometryCollection):
                polys = [g for g in geom.geoms if isinstance(g, Polygon)]  # type: ignore
                return polys
            else:
                raise ValueError(
                    "WKB geometry no es un Polígono/Multipolígono compatible"
                )
        except Exception as e2:
            raise ValueError(f"No se pudo decodificar WKB: {e2}")

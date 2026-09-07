from fastapi import HTTPException
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
from shapely.affinity import scale, translate
from ezdxf.filemanagement import read  # type: ignore
from ezdxf.lldxf.const import DXFStructureError  # type: ignore
from shapely.ops import polygonize
from ezdxf import path
from shapely.geometry import LineString
from src.FileModule.exporters import (
    GeometryExporter,
    GlbExporter,
    ImageExporter,
    ObjExporter,
)


class ShapelyAnalyzer(GeometriesAnalyzer):

    def __init__(
        self,
        geometries: list[Geometry],
        exporters: dict[str, GeometryExporter] | None = None,
    ):
        self.__geometries = gpd.GeoSeries(geometries)
        self.__exporters = exporters if exporters is not None else {
            "png": ImageExporter(),
            "obj": ObjExporter(),
            "glb": GlbExporter(),
        }

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

    def export(self, format: str) -> bytes:
        exporter = self.__exporters.get(format)
        if exporter is None:
            raise ValueError(f"Unsupported export format: {format}")
        return exporter.export(self.__geometries)

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

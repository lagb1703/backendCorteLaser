from fastapi import HTTPException
from src.FileModule.geometriesAnalizer import GeometriesAnaliser
from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.enums import ExceptionsEnum
from io import StringIO, BytesIO, TextIOWrapper
from shapely import Polygon, touches, wkb, MultiPolygon, GeometryCollection # type: ignore
from typing import Dict, List
import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Tuple
from shapely.affinity import scale
from ezdxf.filemanagement import read # type: ignore
from ezdxf.lldxf.const import DXFStructureError # type: ignore
from ezdxf_shapely import convert_all, polygonize # type: ignore
from ezdxf import path
from shapely.geometry import LineString

class ShapelyAnalizer(GeometriesAnaliser):
    
    def __init__(self, geometries: List[Polygon]):
        self.__geometries = gpd.GeoSeries(geometries)
        
    def checkGeometries(self)->bool:
        validGeometry:bool = bool(self.__geometries.notna().all() and self.__geometries.is_valid.all())
        gdf = gpd.GeoDataFrame({'geometry': self.__geometries})
        candidates = gpd.sjoin(gdf, gdf, how='inner', predicate='intersects')
        overlaps: List[Tuple[int, int]] = []
        for _, row in candidates.iterrows():
            i = int(row.name) # type: ignore
            j = int(row['index_right']) 
            if i >= j:
                continue
            b1 = gdf.loc[i, 'geometry'].boundary # type: ignore
            b2 = gdf.loc[j, 'geometry'].boundary # type: ignore
            if touches(b1, b2): # type: ignore
                overlaps.append((i, j))
        return validGeometry and len(overlaps) == 0
    
    def getMinimunRectangle(self)->Tuple[float, float, float, float]:
        union = self.__geometries.unary_union # type: ignore
        rect = union.minimum_rotated_rectangle
        minx, miny, maxx, maxy = rect.bounds
        return (float(minx), float(miny), float(maxx), float(maxy))
    
    def getPerimeter(self)->int:
        union = self.__geometries.unary_union # type: ignore
        return int(union.length)
    
    def createImage(self)->bytes:
        fig, ax = plt.subplots(figsize=(6,6)) # type: ignore
        self.__geometries.plot(ax=ax, facecolor='none', edgecolor='black') # type: ignore
        ax.set_aspect('equal')
        ax.axis('off')
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0) # type: ignore
        plt.close(fig)
        image_bytes = buf.getvalue()
        buf.close()
        return image_bytes
    
    def save(self)->bytes:
        geometries_list = self.__geometries.tolist()
        geom_collection = GeometryCollection(geometries_list)
        return wkb.dumps(geom_collection) # type: ignore
    
class DxfAdapter(GeometriesAdapter[Polygon]):
    
    unitsToMeters:Dict[int, float] = {
            0: 0,  # Unidades sin definir
            1: 0.0254,  # Pulgadas a metros
            2: 0.3048,  # Pies a metros
            3: 1609.34,  # Millas a metros
            4: 0.001,  # Milímetros a metros
            5: 0.01,  # Centímetros a metros
            6: 1.0,  # Metros
            7: 1000.0,  # Kilómetros a metros
            8: 2.54e-08,  # Micro-pulgadas a metros
            9: 2.54e-05,  # Mils a metros
            10: 0.9144,  # Yardas a metros
            11: 1e-10,  # Ángstroms a metros
            12: 1e-09,  # Nanómetros a metros
            13: 1e-06,  # Micrones a metros
            14: 0.1,  # Decímetros a metros
            15: 10.0,  # Decámetros a metros
            16: 100.0,  # Hectómetros a metros
            17: 1e+09,  # Gigámetros a metros
            18: 1.495978707e+11,  # Unidades astronómicas a metros
            19: 9.461e+15,  # Años luz a metros
            20: 3.086e+16,  # Parsecs a metros
    }
    
    def makeGeometries(self, data: bytes)-> List[Polygon]:
        buf = None
        try:
            buf = TextIOWrapper(BytesIO(data), encoding='latin-1')
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
        geoms:List[LineString] = []
        for entity in msp:
            try:
                p_path = path.make_path(entity)
                vertices = list(p_path.flattening(distance=0.01))
                if len(vertices) > 1:
                    geoms.append(LineString(vertices))
            except Exception:
                continue
        units = doc.units
        if units == 0:
            raise HTTPException(404, ExceptionsEnum.BAD_FILE.name.replace(":file", "").replace(":description", "falta de unidades de medida"))
        convertFactor = DxfAdapter.unitsToMeters.get(units)
        if convertFactor is None:
            raise HTTPException(404, ExceptionsEnum.BAD_FILE.name.replace(":file", "").replace(":description", "unidad desconocida"))
        polygons = list(polygonize(geoms))
        return [scale(poly, xfact=convertFactor, yfact=convertFactor, origin=(0,0)) for poly in polygons]

class WKBAdapter(GeometriesAdapter[Polygon]):
    
    def makeGeometries(self, data: bytes)-> List[Polygon]:
        try:
            geom = wkb.loads(data)
            if isinstance(geom, Polygon):
                return [geom]
            elif isinstance(geom, MultiPolygon):
                return list(geom.geoms)
            elif isinstance(geom, GeometryCollection):
                polys = [g for g in geom.geoms if isinstance(g, Polygon)] # type: ignore
                return polys
            else:
                raise ValueError("WKB geometry no es un Polígono/Multipolígono compatible")
        except Exception as e2:
            raise ValueError(f"No se pudo decodificar WKB: {e2}")
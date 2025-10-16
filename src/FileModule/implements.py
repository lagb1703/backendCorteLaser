from src.FileModule.geometriesAnalizer import GeometriesAnaliser
from src.FileModule.geometriesAdapter import GeometriesAdapter
from io import StringIO, BytesIO
from shapely import Polygon
from typing import List
import geopandas as gpd
import matplotlib.pyplot as plt
from typing import Tuple
from ezdxf.filemanagement import read # type: ignore
from ezdxf_shapely import convert_all, polygonize # type: ignore

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
            inter = b1.intersection(b2) # type: ignore
            length = getattr(inter, 'length', 0.0) # type: ignore
            if length > 1e-8:
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
    
class DxfAdapter(GeometriesAdapter[Polygon]):
    
    def makeGeometries(self, data: bytes)-> List[Polygon]:
        buf = StringIO(data.decode("utf-8"))
        doc = read(buf)
        msp = doc.modelspace()
        p = convert_all(msp)
        return polygonize(p)
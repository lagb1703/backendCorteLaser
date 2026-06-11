from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.geometriesAnalizer import GeometriesAnaliser
from src.FileModule.implements import ShapelyAnalizer, DxfAdapter, WKBAdapter
from typing import Any
from functools import lru_cache

class GeometryAnaliserCreator:
    
    def __init__(self):
        self.__filesToGeometries: dict[str, GeometriesAdapter[Any]] = {
            "dxf": DxfAdapter(),
            "wkb": WKBAdapter() 
        }
        
    def createGeometry(self, extention: str, data: bytes)->GeometriesAnaliser:
        adapter: GeometriesAdapter[Any] | None = self.__filesToGeometries.get(extention)
        if adapter is None:
            raise ValueError(f"Unsupported file extension: {extention}")
        poligons = adapter.makeGeometries(data)
        return ShapelyAnalizer(poligons)

@lru_cache()
def get_geometry_analiser_creator() -> GeometryAnaliserCreator:
    return GeometryAnaliserCreator()

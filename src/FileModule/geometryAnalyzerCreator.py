from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.geometriesAnalyzer import GeometriesAnalyzer
from src.FileModule.implements import ShapelyAnalyzer, DxfAdapter, WKBAdapter
from typing import Any
from functools import lru_cache

class GeometryAnalyzerCreator:
    
    def __init__(self):
        self.__filesToGeometries: dict[str, GeometriesAdapter[Any]] = {
            "dxf": DxfAdapter(),
            "wkb": WKBAdapter() 
        }
        
    def createGeometry(self, extension: str, data: bytes)->GeometriesAnalyzer:
        adapter: GeometriesAdapter[Any] | None = self.__filesToGeometries.get(extension)
        if adapter is None:
            raise ValueError(f"Unsupported file extension: {extension}")
        polygons = adapter.makeGeometries(data)
        return ShapelyAnalyzer(polygons)

@lru_cache()
def get_geometry_analyzer_creator() -> GeometryAnalyzerCreator:
    return GeometryAnalyzerCreator()

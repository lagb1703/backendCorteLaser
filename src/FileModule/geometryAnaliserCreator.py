from src.FileModule.geometriesAdapter import GeometriesAdapter
from src.FileModule.geometriesAnalizer import GeometriesAnaliser
from src.FileModule.implements import ShapelyAnalizer, DxfAdapter, WKBAdapter
from typing import Dict, Any

class GeometryAnaliserCreator:
    
    __instance: 'GeometryAnaliserCreator | None' = None
    
    def __init__(self):
        self.__filesToGeometries: Dict[str, GeometriesAdapter[Any]] = {
            "dxf": DxfAdapter(),
            "wkb": WKBAdapter() 
        }
        
    def createGeometry(self, extention: str, data: bytes)->GeometriesAnaliser:
        adapter: GeometriesAdapter[Any] | None = self.__filesToGeometries.get(extention)
        if adapter is None:
            raise ValueError(f"Unsupported file extension: {extention}")
        poligons = adapter.makeGeometries(data)
        return ShapelyAnalizer(poligons)
    
    @staticmethod
    def getInstance():
        if GeometryAnaliserCreator.__instance is None:
            GeometryAnaliserCreator.__instance = GeometryAnaliserCreator()
        return GeometryAnaliserCreator.__instance
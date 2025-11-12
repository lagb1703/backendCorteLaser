from src.MaterialModule.dtos import Material, Thickness
from src.utils.PostgressClient import PostgressClient
from typing import List
from datetime import datetime

class MaterialService:
    
    __instance: 'MaterialService | None' = None
    
    @staticmethod
    def getInstance()->'MaterialService':
        if MaterialService.__instance is None:
            MaterialService.__instance = MaterialService()
        return MaterialService.__instance
    
    def __init__(self):
        self.__postgress = PostgressClient.getInstance()
        
    async def getAllMaterials(self)->List[Material]:
        return []
    
    async def getAllThickness(self)->List[Thickness]:
        return []
    
    async def getMaterialById(self, materialId: str)->Material:
        return Material(name="", price=0.0, lastModification=datetime.now())
    
    async def getThicknessByMaterial(self, materialId: str)->List[Thickness]:
        return []
    
    async def addNewMaterial(self, material: Material)->str:
        return ""
    
    async def addNewThickness(self, thickness: Thickness, materialId: str)->str:
        return ""
    
    async def changeMaterial(self, materialId: str, material: Material)->None:
        pass
    
    async def changeThickness(self, thicknessId: str, thickness: Thickness)->None:
        pass
    
    async def addMaterialThickness(self, materialId: str, thicknessId: str)->None:
        pass
    
    async def deleteMaterialThickness(self, materialId: str, thicknessId: str)->None:
        pass
    
    async def deleteMaterial(self, materialId: str)->None:
        pass
    
    async def delteThickness(self, thicknessId: str)->None:
        pass
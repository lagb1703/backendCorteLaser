from src.MaterialModule.dtos import Material, Thickness
from src.MaterialModule.enums import MaterialSql
from src.utils.PostgressClient import PostgressClient
from typing import List
import logging
import asyncpg # type: ignore
from fastapi import HTTPException

class MaterialService:
    
    __instance: 'MaterialService | None' = None
    
    @staticmethod
    def getInstance()->'MaterialService':
        if MaterialService.__instance is None:
            MaterialService.__instance = MaterialService()
        return MaterialService.__instance
    
    def __init__(self):
        self.__postgress = PostgressClient.getInstance()
        self.__logger = logging.getLogger("MaterialService")
        
    async def getMtIdByMaterialIdThicknessId(self, materialId: str | int, thicknessId: str | int)-> int | str | None:
        try:
            return (await self.__postgress.query(MaterialSql.getMtIdByMaterialIdThicknessId.value, [int(materialId), int(thicknessId)]))[0]["mtId"]
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
        
    async def getAllMaterials(self)->List[Material]:
        try:
            materials = await self.__postgress.query(MaterialSql.getAllMaterials.value, [])
            return [Material.model_validate(m) for m in materials]
        except Exception as e:
            self.__logger.info(str(e))
            raise
            
    
    async def getAllThickness(self)->List[Thickness]:
        try:
            thickness = await self.__postgress.query(MaterialSql.getAllThickness.value, [])
            return [Thickness.model_validate(t) for t in thickness]
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def getMaterialById(self, materialId: str | int)->Material:
        try:
            material = (await self.__postgress.query(MaterialSql.getMaterialById.value, [int(materialId)]))[0]
            return Material.model_validate(material)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def getThicknessById(self, thicknessId: str | int)->Thickness:
        try:
            thickness = (await self.__postgress.query(MaterialSql.getThicknessById.value, [int(thicknessId)]))[0]
            return Thickness.model_validate(thickness)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def getThicknessByMaterial(self, materialId: str)->List[Thickness]:
        try:
            thickness = await self.__postgress.query(MaterialSql.getAllThicknessByMaterialId.value, [int(materialId)])
            return [Thickness.model_validate(t) for t in thickness]
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
    async def getThicknessNoLinkedToMaterial(self, materialId: str | int)-> List[Thickness]:
        try:
            thickness = await self.__postgress.query(MaterialSql.getThicknessNoLinkedToMaterial.value, [int(materialId)])
            return [Thickness.model_validate(t) for t in thickness]
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def addNewMaterial(self, material: Material)->str | int:
        try:
            material.weight = int(material.weight)
            return (await self.__postgress.save(MaterialSql.addNewMaterial.value, material.__dict__))["p_id"]
        except asyncpg.exceptions.UniqueViolationError as e:
            self.__logger.info(f"Unique violation: {e}")
            raise HTTPException(status_code=409, detail="Registro duplicado")
        except Exception as e:
            self.__logger.info(str(e))
            raise
            
    
    async def addNewThickness(self, thickness: Thickness)->str | int:
        try:
            return (await self.__postgress.save(MaterialSql.addNewThickness.value, thickness.__dict__))["p_id"]
        except asyncpg.exceptions.UniqueViolationError as e:
            self.__logger.info(f"Unique violation: {e}")
            raise HTTPException(status_code=409, detail="Registro duplicado")
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def changeMaterial(self, materialId: str, material: Material)->None:
        try:
            material.weight = int(material.weight)
            await self.__postgress.update(MaterialSql.changeMaterial.value, material.__dict__,materialId)
        except asyncpg.exceptions.UniqueViolationError as e:
            self.__logger.info(f"Unique violation: {e}")
            raise HTTPException(status_code=409, detail="Nombre del material duplicado")
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def changeThickness(self, thicknessId: str, thickness: Thickness)->None:
        try:
            await self.__postgress.update(MaterialSql.changeThickness.value, thickness.__dict__,thicknessId)
        except asyncpg.exceptions.UniqueViolationError as e:
            self.__logger.info(f"Unique violation: {e}")
            raise HTTPException(status_code=409, detail="Nombre del thickness duplicado")
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def addMaterialThickness(self, materialId: str, thicknessId: str)->int | str:
        try:
            return (await self.__postgress.save(MaterialSql.addMaterialThickness.value, {
                    "materialId":materialId,
                    "thicknessId":thicknessId
                }))["p_id"]
        except asyncpg.exceptions.UniqueViolationError as e:
            self.__logger.info(f"Unique violation: {e}")
            raise HTTPException(status_code=409, detail="Registro duplicado para material y espesor")
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def deleteMaterialThickness(self, materialId: str, thicknessId: str)->None:
        try:
            mtId = await self.getMtIdByMaterialIdThicknessId(materialId, thicknessId)
            if mtId is None:
                return 
            await self.__postgress.delete(MaterialSql.deleteMaterialThickness.value, mtId)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def deleteMaterial(self, materialId: str)->None:
        try:
            await self.__postgress.delete(MaterialSql.deleteMaterial.value, materialId)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def deleteThickness(self, thicknessId: str)->None:
        try:
            await self.__postgress.delete(MaterialSql.deleteThickness.value, thicknessId)
        except Exception as e:
            self.__logger.info(str(e))
            raise
from src.autentification.AuthService import AuthService
from src.MaterialModule.materialService import MaterialService
from src.MaterialModule.dtos import Material, Thickness
from typing import List
from fastapi import APIRouter

router = APIRouter(prefix="material", tags=["materiales"])

authService = AuthService.getInstance()

materialService = MaterialService.getInstance()

@router.get("/materials")
async def getAllMaterials()->List[Material]:
    return await materialService.getAllMaterials()

@router.get("/thickness")
async def getAllThickness()->List[Thickness]:
    return await materialService.getAllThickness()

@router.get("/material")
async def getMaterialById(materialId: str)->Material:
    return await materialService.getMaterialById(materialId)

@router.get("/thickness")
async def getThicknessByMaterial(materialId: str)->List[Thickness]:
    return await materialService.getThicknessByMaterial(materialId)

@router.post("/material")
async def addNewMaterial()
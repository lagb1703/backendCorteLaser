from src.autentification.AuthService import AuthService
from src.MaterialModule.materialService import MaterialService
from src.MaterialModule.dtos import Material, Thickness
from src.UserModule.dtos import UserToken
from typing import List, Annotated
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/material", tags=["materiales"])

authService = AuthService.getInstance()

materialService = MaterialService.getInstance()

@router.get("/materials")
async def getAllMaterials()->List[Material]:
    return await materialService.getAllMaterials()

@router.get("/thickness/all")
async def getAllThickness()->List[Thickness]:
    return await materialService.getAllThickness()

@router.get("/material")
async def getMaterialById(materialId: str)->Material:
    return await materialService.getMaterialById(materialId)

@router.get("/thickness")
async def getThicknessByMaterial(materialId: str)->List[Thickness]:
    return await materialService.getThicknessByMaterial(materialId)

@router.post("/material")
async def addNewMaterial(material: Material, _: Annotated[UserToken, Depends(authService.setUserAdmin)])-> str | int:
    return await materialService.addNewMaterial(material)

@router.put("/material/{materialId}")
async def changeMaterial(materialId: str, material: Material, _: Annotated[UserToken, Depends(authService.setUserAdmin)])-> None:
    return await materialService.changeMaterial(materialId, material)

@router.delete("/material/{materialId}")
async def deleteMaterial(materialId: str, _: Annotated[UserToken, Depends(authService.setUserAdmin)])-> None:
    return await materialService.deleteMaterial(materialId)

@router.post("/thickness/{materialId}")
async def addNewThickness(thickness: Thickness, materialId: str, _: Annotated[UserToken, Depends(authService.setUserAdmin)])->str | int:
    return await materialService.addNewThickness(thickness, materialId)

@router.put("/thickness/{thicknessId}")
async def changeThickness(thicknessId: str, thickness: Thickness, _: Annotated[UserToken, Depends(authService.setUserAdmin)])-> None:
    return await materialService.changeThickness(thicknessId, thickness)

@router.delete("/thickness/{thicknessId}")
async def delteThickness(thicknessId: str, _: Annotated[UserToken, Depends(authService.setUserAdmin)])-> None:
    return await materialService.deleteThickness(thicknessId)

@router.post("/mt/{materialId}/{thicknessId}")
async def addMaterialThickness(materialId: str, thicknessId: str, _: Annotated[UserToken, Depends(authService.setUserAdmin)]):
    return await materialService.addMaterialThickness(materialId, thicknessId)

@router.delete("/mt/{materialId}/{thicknessId}")
async def deleteMaterialThickness(materialId: str, thicknessId: str, _: Annotated[UserToken, Depends(authService.setUserAdmin)]):
    return await materialService.deleteMaterialThickness(materialId, thicknessId)
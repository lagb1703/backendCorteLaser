from src.MaterialModule.materialService import MaterialService, get_material_service
from src.MaterialModule.dtos import Material, Thickness
from src.UserModule.dtos import UserToken
from src.UserModule import get_current_admin_user
from typing import Annotated
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/material", tags=["materiales"])

@router.get("/materials")
async def getAllMaterials(
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->list[Material]:
    return await material_service.getAllMaterials()

@router.get("/thickness/all")
async def getAllThickness(
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->list[Thickness]:
    return await material_service.getAllThickness()

@router.get("/material")
async def getMaterialById(
    materialId: str,
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->Material:
    return await material_service.getMaterialById(materialId)

@router.get("/thickness")
async def getThicknessByMaterial(
    materialId: str,
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->list[Thickness]:
    return await material_service.getThicknessByMaterial(materialId)

@router.get("/thickness/noLinked")
async def getThicknessNoLinkedToMaterial(
    materialId: str,
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->list[Thickness]:
    return await material_service.getThicknessNoLinkedToMaterial(materialId)

@router.post("/material", status_code=201)
async def addNewMaterial(
    material: Material,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)-> str | int:
    return await material_service.addNewMaterial(material)

@router.put("/material/{materialId}")
async def changeMaterial(
    materialId: str,
    material: Material,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)-> None:
    return await material_service.changeMaterial(materialId, material)

@router.delete("/material/{materialId}")
async def deleteMaterial(
    materialId: str,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)-> None:
    return await material_service.deleteMaterial(materialId)

@router.post("/thickness", status_code=201)
async def addNewThickness(
    thickness: Thickness,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)->str | int:
    return await material_service.addNewThickness(thickness)

@router.put("/thickness/{thicknessId}")
async def changeThickness(
    thicknessId: str,
    thickness: Thickness,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)-> None:
    return await material_service.changeThickness(thicknessId, thickness)

@router.delete("/thickness/{thicknessId}")
async def delteThickness(
    thicknessId: str,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
)-> None:
    return await material_service.deleteThickness(thicknessId)

@router.post("/mt/{materialId}/{thicknessId}", status_code=201)
async def addMaterialThickness(
    materialId: str,
    thicknessId: str,
    speed: float,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
):
    result = await material_service.addMaterialThickness(materialId, thicknessId, speed)
    return result

@router.patch("/mt/{materialId}/{thicknessId}/speed")
async def changeSpeedMaterialThickness(
    materialId: str,
    thicknessId: str,
    speed: float,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
):
    return await material_service.changeSpeedMaterialThickness(materialId, thicknessId, speed)

@router.delete("/mt/{materialId}/{thicknessId}", status_code=204)
async def deleteMaterialThickness(
    materialId: str,
    thicknessId: str,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    material_service: Annotated[MaterialService, Depends(get_material_service)]
):
    return await material_service.deleteMaterialThickness(materialId, thicknessId)

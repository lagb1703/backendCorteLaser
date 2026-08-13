from fastapi import APIRouter, UploadFile, Depends, HTTPException
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService, get_file_service
from src.UserModule import get_current_user, get_current_admin_user
from typing import Annotated
from src.autentification.Security import Security, get_security
from src.UserModule.UserService import UserService, get_user_service
from authlib.jose.errors import ExpiredTokenError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.autentification.enums import ExceptionsEnum

router = APIRouter(prefix="/file", tags=["files"])

@router.get("")
async def getAllUserInfoFiles(
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getAllUserInfoFiles(u)

@router.post("/save")
async def saveFile(
    file: UploadFile,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.saveFile(file, u)

@router.get("/metadata")
async def getFileMetadata(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getFileInfo(id, u)

@router.get("/donwload")
async def getFile(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getFile(id, u)

@router.get("/image")
async def getImage(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getImage(id, u)

@router.get("/OBJ")
async def getOBJ(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getOBJ(id, u)

@router.get("/Gbl")
async def getGbl(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getGbl(id, u)

@router.get("/glb-rigged")
async def getGlbRigged(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getGlbRigged(id, u)


@router.delete("")
async def deleteFile(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    await file_service.deleteFile(id, u)
    
@router.get("/price")
async def getPrice(
    id: str,
    materialId: str,
    thicknessId: str,
    amount: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getPrice(id, materialId, thicknessId, int(amount), u)

@router.post("/price")
async def setPriceCalculator(
    exp: str,
    u: Annotated[UserToken, Depends(get_current_admin_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    await file_service.setPriceCalculator(exp)
    
@router.get("/price/estimate")
async def getPriceEstimate(
    u: Annotated[UserToken, Depends(get_current_admin_user)],
    file_service: Annotated[FileService, Depends(get_file_service)]
):
    return await file_service.getPriceEstimate()

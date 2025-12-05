from fastapi import APIRouter, UploadFile, Depends
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import AuthService
from src.FileModule.fileService import FileService
from typing import Annotated

router = APIRouter(prefix="/file", tags=["files"])

authService = AuthService.getInstance()

fileService: FileService = FileService.getInstance()

@router.get("")
async def getAllUserInfoFiles(u: Annotated[UserToken, Depends(authService.setUser)]):
    return await fileService.getAllUserInfoFiles(u)

@router.post("/save")
async def saveFile(file: UploadFile, u: Annotated[UserToken, Depends(authService.setUser)]):
    return await fileService.saveFile(file, u)

@router.get("/donwload")
async def getFile(id: str, u: Annotated[UserToken, Depends(authService.setUser)]):
    return await fileService.getFile(id, u)

@router.get("/image")
async def getImage(id: str, u: Annotated[UserToken, Depends(authService.setUser)]):
    return await fileService.getImage(id, u)

@router.delete("")
async def deleteFile(id: str, u: Annotated[UserToken, Depends(authService.setUser)]):
    await fileService.deleteFile(id, u)
    
@router.get("/price")
async def getPrice(id: str, materialId: str, thicknessId: str, amount: str, u: Annotated[UserToken, Depends(authService.setUser)]):
    return await fileService.getPrice(id, materialId, thicknessId, int(amount), u)
from fastapi import APIRouter, UploadFile
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import AuthService
from src.FileModule.fileService import FileService

router = APIRouter(prefix="/file", tags=["files"])

authService = AuthService.getInstance()

fileService: FileService = FileService.getInstance()

@router.post("/save")
async def saveFile(file: UploadFile):
    u = UserToken(id=0, email="p@gmail.com", isAdmin=False)
    return await fileService.saveFile(file, u)

@router.get("/donwload")
async def getFile(id: str):
    u = UserToken(id=0, email="p@gmail.com", isAdmin=False)
    return await fileService.getFile(id, u)
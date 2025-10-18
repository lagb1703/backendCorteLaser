import datetime
from src.FileModule.geometryAnaliserCreator import GeometryAnaliserCreator
from src.FileModule.storageService import StorageService
from src.FileModule.enums import ExceptionsEnum, FolderName
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from typing import List
from src.FileModule.dtos import FileDb
from src.utils.PostgressClient import PostgressClient
from io import BytesIO

class FileService:
    
    __instance: 'FileService | None' = None
    
    @staticmethod
    def getInstance():
        if FileService.__instance is None:
            FileService.__instance = FileService()
        return FileService.__instance
    
    def __init__(self):
        self.__storage: StorageService = StorageService.getInstance()
        self.__creator: GeometryAnaliserCreator = GeometryAnaliserCreator.getInstance()
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        
    async def __getFileInfo(self, id: str | int, user: UserToken)->FileDb:
        return FileDb(id=0, name="figura.dxf", date=datetime.datetime.now(), md5="", bucket="", userId=0)
    async def __saveFileInfo(self, fileDb: FileDb, user:UserToken)->int | str:
        return 0
    async def __deleteFileInfo(self, id: str | int) -> None:
        pass
    
    async def saveFile(self, file: UploadFile, user: UserToken)->str | int:
        if file.filename is None:
            raise HTTPException(400, ExceptionsEnum.BAD_FILE.value.replace(":file", "").replace(":description", "Nombre no valido"))
        fileInfo = FileDb(id=None, name=file.filename, date=None, md5="", bucket="", userId=user.id)
        id = await self.__saveFileInfo(fileInfo, user)
        fileBytes: bytes = await file.read()
        self.__storage.upload(fileBytes, file.filename, FolderName.ORIGINAL.value)
        geo = self.__creator.createGeometry(file.filename.split(".")[1], fileBytes)
        self.__storage.upload(geo.save(), f"{fileInfo.name.split('.')[0]}.wkb", FolderName.WKB.value)
        return id
    
    async def getFile(self, id: str | int, user: UserToken)->StreamingResponse:
        fileInfo = await self.__getFileInfo(id, user)
        file: bytes = self.__storage.download(fileInfo.name, FolderName.ORIGINAL.value)
        return StreamingResponse(
            BytesIO(file),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={fileInfo.name}"}
        )
    
    async def deleteFile(self, id: str | int, user: UserToken)->None:
        fileInfo = await self.__getFileInfo(id, user)
        await self.__deleteFileInfo(id)
        self.__storage.delete(fileInfo.name, FolderName.ORIGINAL.value)
        self.__storage.delete(f"{fileInfo.name.split('.')[0]}.wkb", FolderName.WKB.value)
        
    async def getImage(self, id: str | int, user: UserToken)->StreamingResponse:
        fileInfo = await self.__getFileInfo(id, user)
        onlyName:str = fileInfo.name.split('.')[0]
        fileWBT:bytes = self.__storage.download(f"{onlyName}.wkb", FolderName.WKB.value)
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.createImage()
        return StreamingResponse(
            content=BytesIO(image),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={onlyName}.png"}
        )
        
    async def getAllUserInfoFiles(self, user: UserToken)->List[FileDb]:
        return []
    
    async def getPrice(self, id: str | int, materialId: str, thicknessId: str, user: UserToken)->float:
        return 0.0
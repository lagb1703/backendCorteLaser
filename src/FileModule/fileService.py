from src.FileModule.geometryAnaliserCreator import GeometryAnaliserCreator
from src.FileModule.storageService import StorageService
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from src.FileModule.dtos import FileDbType
# Response not needed


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
        
    async def saveFile(self, file: UploadFile, user: UserToken)->int | str:
        if file.filename is None:
            raise HTTPException(400, "falta la extención del archivo")
        file_bytes = await file.read()
        geometryData = self.__creator.createGeometry(file.filename.split(".")[1], file_bytes)
        if not geometryData.checkGeometries():
            raise HTTPException(400, "Documento no valido")
        id = await self.__storage.uploadFile(
            file_bytes, 
            f"originals/{file.filename}", 
            user, 
            file.content_type
        )
        await self.__storage.upload(geometryData.save(), f"wbk/{file.filename.split('.')[0]}.wbk", content="application/octet-stream")
        return id
    
    async def getFile(self, id: str | int, user: UserToken)-> StreamingResponse:
        return await self.__storage.downloadFile(id, user)
    
    async def deleteFile(self, id: str | int, user: UserToken)-> None:
        await self.__storage.deleteFile(id, user)
    
    def getImage(self, id: str | int, user: UserToken)->StreamingResponse:
        self.
    
    def getAllUserInfoFiles(self, user: UserToken)-> List[FileDbType]:
        return []
from datetime import datetime
from src.FileModule.storageWapper import StorageWapper
from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.dtos import FileDbType
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from io import BytesIO

class StorageService:
    
    __instance: 'StorageService | None' = None
    
    @staticmethod
    def getInstance():
        if StorageService.__instance is None:
            StorageService.__instance = StorageService()
        return StorageService.__instance
    
    def __init__(self):
        self.__storage = StorageWapper()
        self.__postgress = PostgressClient.getInstance()
        
    async def __addFileDB(self, user: UserToken, name: str | None)-> str | int:
        return 0
    
    async def __deleteFileDb(self, id: str | int):
        pass
    
    async def __getFileInfo(self, id: str | int)->FileDbType:
        return FileDbType(id=0, name="pepe", date=datetime.now(), md5="afasdfas", bucket="pepe", userId=1)
    
    async def uploadFile(self, file:UploadFile, user: UserToken)->str | int:
        fileContent: bytes = await file.read()
        fileName: str = file.filename if file.filename is not None else ""
        id = await self.__addFileDB(user, fileName)
        self.__storage.upload(fileContent, fileName, file.content_type)
        return id
    
    async def downloadFile(self, id: str | int, user: UserToken)->StreamingResponse:
        fileInfo = await self.__getFileInfo(id)
        if fileInfo.userId != user.id:
            raise HTTPException(401, "el archivo no esta a nombre del usaurio")
        fileData: bytes = self.__storage.download(fileInfo.name)
        return StreamingResponse(
            BytesIO(fileData), 
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={fileInfo.name}"}
        )
    
    async def deleteFile(self, id: str | int, user: UserToken)->None:
        fileInfo = await self.__getFileInfo(id)
        if fileInfo.userId != user.id:
            raise HTTPException(401, "el archivo no esta a nombre del usaurio")
        await self.__deleteFileDb(fileInfo.id)
        self.__storage.delete(fileInfo.name)
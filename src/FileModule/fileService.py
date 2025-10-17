from src.FileModule.geometryAnaliserCreator import GeometryAnaliserCreator
from src.FileModule.storageService import StorageService
from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
from src.FileModule.dtos import FileDbType
from io import BytesIO
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
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        self.__creator: GeometryAnaliserCreator = GeometryAnaliserCreator.getInstance()
        
    async def saveFile(self, file: UploadFile, user: UserToken)->int | str:
        if file.filename is None:
            raise HTTPException(400, "falta la extención del archivo")
        file_bytes = await file.read()
        
        a = self.__creator.createGeometry(file.filename.split(".")[1], file_bytes)
        # data is expected to be bytes (PNG). Wrap in BytesIO for streaming.
        # buf = BytesIO(data)
        # headers = {
        #     "Content-Disposition": f"attachment; filename=\"{file.filename.rsplit('.',1)[0]}.png\""
        # }
        # Return StreamingResponse with proper content type
        # return StreamingResponse(buf, media_type="image/png", headers=headers)
        return 0
    
    def getFile(self, id: str | int, user: UserToken)-> FileResponse:
        raise NotImplementedError()
    
    def deleteFile(self, id: str | int, user: UserToken)-> None:
        raise NotImplementedError()
    
    def getImage(self, id: str | int, user: UserToken)->FileResponse:
        raise NotImplementedError()
    
    def getAllUserInfoFiles(self, user: UserToken)-> List[FileDbType]:
        return []
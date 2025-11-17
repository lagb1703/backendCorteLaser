from src.FileModule.geometryAnaliserCreator import GeometryAnaliserCreator
from src.FileModule.storageService import StorageService
from src.FileModule.enums import ExceptionsEnum, FileSql, FolderName
from src.FileModule.costCalculator import CostCalculator
from src.MaterialModule.materialService import MaterialService
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from fastapi.responses import  StreamingResponse
from typing import List
from src.FileModule.dtos import FileDb, PriceResponse
from src.utils.PostgressClient import PostgressClient
from io import BytesIO
import hashlib
import logging

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
        self.__materialService: MaterialService = MaterialService.getInstance()
        self.__logger = logging.getLogger("FileService")
        
    async def __getFileInfo(self, id: str | int, user: UserToken)->FileDb:
        try:
            file = (await self.__postgress.query(FileSql.getFileById.value, [int(id)]))[0]
            file["date"]=str(file["date"])
            return FileDb.model_validate(file)
        except Exception as e:
            self.__logger.info(str(e))
            raise
            
    async def __saveFileInfo(self, fileDb: FileDb, user:UserToken)->int | str:
        try:
            fileDb.userId = user.id
            return (await self.__postgress.save(FileSql.saveFile.value, fileDb.__dict__))["p_id"]
        except Exception as e:
            self.__logger.info(str(e))
            raise
            
    async def __deleteFileInfo(self, id: str | int) -> None:
        try:
            await self.__postgress.delete(FileSql.deleteFile.value, id)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    async def __saveQuote(self, fileId: str | int, mtId: str | int)-> int | str:
        try:
            id = (await self.__postgress.save(FileSql.saveQuote.value, {
                    "fileId":fileId,
                    "mtId":mtId
                }))
            print(id)
            return id["p_id"]
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
    async def saveFile(self, file: UploadFile, user: UserToken)->str | int:
        if file.filename is None:
            raise HTTPException(400, ExceptionsEnum.BAD_FILE.value.replace(":file", "").replace(":description", "Nombre no valido"))
        fileBytes: bytes = await file.read()
        fileInfo = FileDb(id=None, name=file.filename, date=None, md5=hashlib.md5(fileBytes).hexdigest(), bucket=FolderName.ORIGINAL.value, userId=user.id)
        id = await self.__saveFileInfo(fileInfo, user)
        self.__storage.upload(fileBytes, f"{fileInfo.md5}.{file.filename.split('.')[1]}", FolderName.ORIGINAL.value)
        geo = self.__creator.createGeometry(file.filename.split(".")[1], fileBytes)
        self.__storage.upload(geo.save(), f"{fileInfo.md5}.wkb", FolderName.WKB.value)
        return id
    
    async def getFile(self, id: str | int, user: UserToken)->StreamingResponse:
        fileInfo = await self.__getFileInfo(id, user)
        file: bytes = self.__storage.download(f"{fileInfo.md5}.{fileInfo.name.split('.')[1]}", FolderName.ORIGINAL.value)
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
        fileWBT:bytes = self.__storage.download(f"{fileInfo.md5}.wkb", FolderName.WKB.value)
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.createImage()
        return StreamingResponse(
            content=BytesIO(image),
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename={fileInfo.name}.png"}
        )
        
    async def getAllUserInfoFiles(self, user: UserToken)->List[FileDb]:
        try:
            rows = await self.__postgress.query(FileSql.getAllUserFiles.value, [user.id])
            result: List[FileDb] = []
            for r in rows:
                r["date"]=str(r["date"])
                result.append(FileDb.model_validate(r))
            return result
        except Exception as e:
            print(str(e))
            raise HTTPException(500, "")
            
    
    async def getPrice(self, id: str | int, materialId: str, thicknessId: str, user: UserToken)->PriceResponse:
        cost = CostCalculator()
        fileInfo = await self.__getFileInfo(id, user)
        fileWBT:bytes = self.__storage.download(f"{fileInfo.md5}.wkb", FolderName.WKB.value)
        geo = self.__creator.createGeometry("wkb", fileWBT)
        perimeter = geo.getPerimeter()
        minX, minY, maxX, maxY = geo.getMinimunRectangle()
        area = (maxX - minX)*(maxY-minY)
        mtId = await self.__materialService.getMtIdByMaterialIdThicknessId(materialId, thicknessId)
        if mtId is None:
            raise
        return PriceResponse(
            price=cost.getPrice(1000, 100, area, perimeter),
            quoteId=await self.__saveQuote(id, mtId)
        )
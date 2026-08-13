from src.FileModule.geometryAnalyzerCreator import (
    GeometryAnalyzerCreator,
    get_geometry_analyzer_creator,
)
from src.FileModule.storageService import StorageService, get_storage_service
from src.FileModule.enums import ExceptionsEnum, FileSql, FolderName
from src.FileModule.interfaces import PriceElements
from src.FileModule.costService import CostService, get_cost_service
from src.MaterialModule.materialService import MaterialService, get_material_service
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from typing import Any
from src.FileModule.dtos import FileDb, PriceResponse
from src.utils.PostgresClient import PostgresClient, get_postgres_client
from io import BytesIO
import hashlib
import logging
from asyncpg.exceptions import UniqueViolationError  # type: ignore
from math import ceil


class FileService:

    def __init__(
        self,
        storage: StorageService,
        creator: GeometryAnalyzerCreator,
        postgres: PostgresClient,
        material_service: MaterialService,
        cost_service: CostService,
    ):
        self.__storage = storage
        self.__creator = creator
        self.__postgres = postgres
        self.__materialService = material_service
        self.__costService = cost_service
        self.__logger = logging.getLogger("FileService")

    def __single_result_or_http_error(
        self,
        rows: list[dict[str, Any]] | None,
        not_found_message: str = "Recurso no encontrado",
    ) -> dict[str, Any]:
        if rows is None or len(rows) == 0:
            raise HTTPException(status_code=404, detail=not_found_message)
        return rows[0]

    async def getFileInfo(self, id: str | int, user: UserToken) -> FileDb:
        try:
            rows = await self.__postgres.query(FileSql.getFileById.value, [int(id)])
            file = self.__single_result_or_http_error(
                rows, f"Archivo con id {id} no encontrado"
            )
            file["date"] = str(file["date"]) if file.get("date") is not None else None
            if file.get("userId") != user.id and not user.isAdmin:
                raise HTTPException(
                    status_code=403, detail=ExceptionsEnum.NOT_AUTHORIZED.value
                )
            return FileDb.model_validate(file)
        except HTTPException:
            raise
        except Exception as e:
            self.__logger.info(str(e))
            raise

    async def __saveFileInfo(self, fileDb: FileDb, user: UserToken) -> int | str:
        try:
            fileDb.userId = user.id
            return (
                await self.__postgres.save(FileSql.saveFile.value, fileDb.model_dump())
            )["p_id"]
        except Exception as e:
            self.__logger.info(str(e))
            raise

    async def __deleteFileInfo(self, id: str | int) -> None:
        try:
            await self.__postgres.delete(FileSql.deleteFile.value, id)
        except Exception as e:
            self.__logger.info(str(e))
            raise

    async def saveFile(self, file: UploadFile, user: UserToken) -> str | int:
        try:
            if file.filename is None:
                raise HTTPException(
                    400,
                    ExceptionsEnum.BAD_FILE.value.replace(":file", "").replace(
                        ":description", "Nombre no valido"
                    ),
                )
            fileBytes: bytes = await file.read()
            geo = self.__creator.createGeometry(file.filename.split(".")[-1], fileBytes)
            fileInfo = FileDb(
                id=None,
                name=file.filename,
                date=None,
                md5=hashlib.md5(fileBytes).hexdigest(),
                bucket=FolderName.ORIGINAL.value,
                userId=user.id,
            )
            id = await self.__saveFileInfo(fileInfo, user)
            self.__storage.upload(
                fileBytes,
                f"{fileInfo.md5}.{file.filename.split('.')[1]}",
                FolderName.ORIGINAL.value,
            )
            self.__storage.upload(
                geo.save(), f"{fileInfo.md5}.wkb", FolderName.WKB.value
            )
            return id
        except ValueError as e:
            raise HTTPException(400, str(e))
        except UniqueViolationError as e:
            print(e)
            raise HTTPException(
                status_code=409, detail=ExceptionsEnum.DUPLICATED_FILE.value
            )
        except HTTPException as e:
            raise

    async def getFile(self, id: str | int, user: UserToken) -> StreamingResponse:
        fileInfo = await self.getFileInfo(id, user)
        file: bytes = self.__storage.download(
            f"{fileInfo.md5}.{fileInfo.name.split('.')[1]}", FolderName.ORIGINAL.value
        )
        return StreamingResponse(
            BytesIO(file),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={fileInfo.name}"},
        )

    async def deleteFile(self, id: str | int, user: UserToken) -> None:
        fileInfo = await self.getFileInfo(id, user)
        await self.__deleteFileInfo(id)
        self.__storage.delete(f"{fileInfo.md5}.dxf", FolderName.ORIGINAL.value)
        self.__storage.delete(f"{fileInfo.md5}.wkb", FolderName.WKB.value)

    async def getImage(self, id: str | int, user: UserToken) -> StreamingResponse:
        fileInfo = await self.getFileInfo(id, user)
        fileWBT: bytes = self.__storage.download(
            f"{fileInfo.md5}.wkb", FolderName.WKB.value
        )
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.export("png")
        return StreamingResponse(
            content=BytesIO(image),
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename={fileInfo.name}.png"
            },
        )

    async def getOBJ(self, id: str | int, user: UserToken) -> StreamingResponse:
        fileInfo = await self.getFileInfo(id, user)
        fileWBT: bytes = self.__storage.download(
            f"{fileInfo.md5}.wkb", FolderName.WKB.value
        )
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.export("obj")
        return StreamingResponse(
            content=BytesIO(image),
            media_type="model/obj",
            headers={
                "Content-Disposition": f"attachment; filename={fileInfo.name}.obj"
            },
        )

    async def getGbl(self, id: str | int, user: UserToken) -> StreamingResponse:
        fileInfo = await self.getFileInfo(id, user)
        fileWBT: bytes = self.__storage.download(
            f"{fileInfo.md5}.wkb", FolderName.WKB.value
        )
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.export("glb")
        return StreamingResponse(
            content=BytesIO(image),
            media_type="model/glb",
            headers={
                "Content-Disposition": f"attachment; filename={fileInfo.name}.obj"
            },
        )

    async def getGlbRigged(self, id: str | int, user: UserToken) -> StreamingResponse:
        fileInfo = await self.getFileInfo(id, user)
        fileWBT: bytes = self.__storage.download(
            f"{fileInfo.md5}.wkb", FolderName.WKB.value
        )
        geo = self.__creator.createGeometry("wkb", fileWBT)
        image = geo.export("glb-rigged")
        return StreamingResponse(
            content=BytesIO(image),
            media_type="model/gltf-binary",
            headers={
                "Content-Disposition": f"attachment; filename={fileInfo.name}.glb"
            },
        )

    async def getAllUserInfoFiles(self, user: UserToken) -> list[FileDb]:
        try:
            rows = await self.__postgres.query(FileSql.getAllUserFiles.value, [user.id])
            result: list[FileDb] = []
            for r in rows:
                r["date"] = str(r["date"])
                result.append(FileDb.model_validate(r))
            return result
        except Exception as e:
            print(str(e))
            raise HTTPException(500, "")

    async def getPrice(
        self,
        id: str | int,
        materialId: str,
        thicknessId: str,
        amount: int,
        user: UserToken,
    ) -> PriceResponse:
        fileInfo = await self.getFileInfo(id, user)
        fileWBT: bytes = self.__storage.download(
            f"{fileInfo.md5}.wkb", FolderName.WKB.value
        )
        geo = self.__creator.createGeometry("wkb", fileWBT)
        perimeter = geo.getPerimeter()
        minX, minY, maxX, maxY = geo.getMinimumRectangle()
        area = (maxX - minX) * (maxY - minY)
        material = await self.__materialService.getMaterialById(materialId)
        thickness = await self.__materialService.getMtByMaterialIdAndThicknessId(
            thicknessId, materialId
        )
        if thickness.speed is None:
            thickness.speed = 1.0
        p = PriceElements(
            materialPrice=material.price,
            thicknessPrice=thickness.price,
            area=area,
            weight=material.weight,
            perimeter=perimeter,
            speed=thickness.speed,
            amount=amount,
            blends=0,
            mtPrice=thickness.mtPrice,
        )
        price = await self.__costService.getPrice(p)
        price = ceil(price * 100) / 100
        price = max(price, 1500)
        return PriceResponse(price=price, area=area, perimeter=perimeter)

    async def setPriceCalculator(self, exp: str) -> None:
        await self.__costService.setPriceCalculator(exp)

    async def getPriceEstimate(self) -> str:
        return await self.__costService.getPriceEstimate()


def get_file_service() -> FileService:
    return FileService(
        storage=get_storage_service(),
        creator=get_geometry_analyzer_creator(),
        postgres=get_postgres_client(),
        material_service=get_material_service(),
        cost_service=get_cost_service(),
    )

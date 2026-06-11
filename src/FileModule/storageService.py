from fastapi import HTTPException
from src.FileModule.storageWrapper import StorageWrapper, get_storage_wrapper
from src.FileModule.enums import ExceptionsEnum

class StorageService:
    
    def __init__(self, storage: StorageWrapper):
        self.__storage = storage
        
    def upload(self, data: bytes, name: str, folder: str, content_type: str | None = None)->None:
        self.__storage.upload(data, f"{folder}/{name}", content_type=content_type)
    def download(self, name: str, folder: str)->bytes:
        try:
            return self.__storage.download(f"{folder}/{name}")
        except Exception as _:
            raise HTTPException(404, ExceptionsEnum.FILE_NOT_FOUND.value.replace(":file", f"{folder}/{name}"))
    def delete(self, name: str, folder: str)->None:
        self.__storage.delete(f"{folder}/{name}")

def get_storage_service() -> StorageService:
    return StorageService(storage=get_storage_wrapper())

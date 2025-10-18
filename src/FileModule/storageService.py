from src.FileModule.storageWapper import StorageWapper

class StorageService:
    
    __instance: 'StorageService | None' = None
    
    @staticmethod
    def getInstance():
        if StorageService.__instance is None:
            StorageService.__instance = StorageService()
        return StorageService.__instance
    
    def __init__(self):
        self.__storage = StorageWapper()
        
    def upload(self, data: bytes, name: str, folder: str, content_type: str | None = None)->None:
        self.__storage.upload(data, f"{folder}/{name}", content_type=content_type)
    def download(self, name: str, folder: str)->bytes:
        return self.__storage.download(f"{folder}/{name}")
    def delete(self, name: str, folder: str)->None:
        self.__storage.delete(f"{folder}/{name}")
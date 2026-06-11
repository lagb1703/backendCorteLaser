from google.cloud import storage  # type: ignore
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from functools import lru_cache

class StorageWapper:
    
    def __init__(self, credentials_url: str, bucket_name: str) -> None:
        self.__client = storage.Client.from_service_account_json(credentials_url)  # type: ignore
        self.__bucket = self.__client.bucket(bucket_name)  # type: ignore
        
    def upload(self, data: bytes, name: str, content_type: str | None = None) -> None:
        blob = self.__bucket.blob(name) # type: ignore
        if content_type:
            blob.upload_from_string(data, content_type=content_type) # type: ignore
        else:
            blob.upload_from_string(data) # type: ignore
            
    def download(self, name: str) -> bytes:
        blob = self.__bucket.blob(name) # type: ignore
        return blob.download_as_bytes() # type: ignore
    
    def delete(self, name: str) -> None:
        blob = self.__bucket.blob(name)  # type: ignore
        blob.delete()  # type: ignore

@lru_cache()
def get_storage_wapper() -> StorageWapper:
    e = Enviroment.getInstance()
    return StorageWapper(
        credentials_url=e.get(EnviromentsEnum.GOOGLE_APPLICATION_CREDENTIALS.value),
        bucket_name=e.get(EnviromentsEnum.GOOGLE_BUCKET_NAME.value)
    )

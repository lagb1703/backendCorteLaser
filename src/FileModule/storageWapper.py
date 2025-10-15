from google.cloud import storage  # type: ignore
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum

class StorageWapper:
    
    def __init__(self) -> None:
        e = Enviroment.getInstance()
        credentials_url = e.get(EnviromentsEnum.GOOGLE_APPLICATION_CREDENTIALS.value)
        self.__client = storage.Client.from_service_account_json(credentials_url)  # type: ignore
        bucketName:str = e.get(EnviromentsEnum.GOOGLE_BUCKET_NAME.value)
        self.__bucket = self.__client.bucket(bucketName)  # type: ignore
        
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
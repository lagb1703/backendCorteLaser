from pydantic import BaseModel

class FileDb(BaseModel):
    id: int | str | None = None
    name: str
    date: str | None = None
    md5: str
    bucket: str
    userId: str | int | None = None
    
class PriceResponse(BaseModel):
    price: float
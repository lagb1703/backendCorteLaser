from pydantic import BaseModel
from typing import Optional

class FileDb(BaseModel):
    id: Optional[int | str] = None
    name: str
    date: Optional[str] = None
    md5: str
    bucket: str
    userId: Optional[str | int] = None
    
class PriceResponse(BaseModel):
    price: float
    quoteId: int | str
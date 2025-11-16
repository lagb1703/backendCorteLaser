from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class FileDb(BaseModel):
    id: int | str | None
    name: str
    date: datetime | None
    md5: str
    bucket: str
    userId: Optional[str | int]
    
class PriceResponse(BaseModel):
    price: float
    quoteId: int | str
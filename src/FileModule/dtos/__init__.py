from pydantic import BaseModel
from datetime import datetime

class FileDbType(BaseModel):
    id: int | str
    name: str
    date: datetime
    md5: str
    bucket: str
    userId: str | int
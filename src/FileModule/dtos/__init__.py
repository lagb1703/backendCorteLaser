from pydantic import BaseModel
from datetime import datetime

class FileDb(BaseModel):
    id: int | str | None
    name: str
    date: datetime | None
    md5: str
    bucket: str
    userId: str | int
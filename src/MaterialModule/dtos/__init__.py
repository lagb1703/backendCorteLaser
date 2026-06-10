from pydantic import BaseModel
from datetime import datetime

class Material(BaseModel):
    materialId: str | int | None = None
    name: str
    price: int
    weight: float
    lastModification: datetime | None = None
    
class Thickness(BaseModel):
    thicknessId: str | int | None = None
    mtId: str | int | None = None
    materialId: str | int | None = None
    name: str
    price: int
    speed: float | None = None
    lastModification: datetime | None = None  
    
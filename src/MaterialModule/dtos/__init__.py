from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class Material(BaseModel):
    materialId: Optional[str | int] = None
    name: str
    price: int
    weight: float
    lastModification: Optional[datetime] = None
    
class Thickness(BaseModel):
    thicknessId: Optional[str | int] = None
    mtId: Optional[str | int] = None
    materialId: Optional[str | int] = None
    name: str
    price: int
    lastModification: Optional[datetime] = None  
    
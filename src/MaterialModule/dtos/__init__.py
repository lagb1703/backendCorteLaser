from pydantic import BaseModel
from datetime import datetime

class Material(BaseModel):
    name: str
    price: float
    lastModification: datetime
    
class Thickness(BaseModel):
    name: str
    price: float
    lastModification: datetime  
    
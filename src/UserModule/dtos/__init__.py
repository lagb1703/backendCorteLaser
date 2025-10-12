from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    names: str
    lastNames: str
    email: EmailStr
    address: str
    password: str
    phone: str
    isAdmin: bool = False
    
class UserToken(BaseModel):
    id: int
    email: str
    isAdmin: Optional[bool] = False
    
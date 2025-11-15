from pydantic import BaseModel, EmailStr
from typing import Optional

class User(BaseModel):
    names: str
    lastNames: str
    email: EmailStr
    address: str
    password: str
    phone: int
    isAdmin: bool
    
class UserToken(BaseModel):
    id: int
    email: str
    isAdmin: Optional[bool]
    
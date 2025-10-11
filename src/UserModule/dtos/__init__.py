from pydantic import BaseModel, EmailStr

class User(BaseModel):
    names: str
    lastNames: str
    email: EmailStr
    address: str
    password: str
    phone: str
    isAdmin: bool = False
    
class UserLogin(BaseModel):
    email: EmailStr
    password: str
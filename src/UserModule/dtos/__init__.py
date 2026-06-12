from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int | None = None
    names: str
    lastNames: str
    email: EmailStr
    address: str
    password: str
    phone: int
    isAdmin: bool | None = False
    identification: str
    identificationTypeId: int | str
    identificationType: str | None = None
    
class UserToken(BaseModel):
    id: int
    email: str
    isAdmin: bool | None
    
class IdentificationType(BaseModel):
    identificationTypeId: str | int
    type: str
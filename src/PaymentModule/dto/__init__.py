from pydantic import BaseModel, EmailStr
from typing import Optional, Literal

class PaymentMethod(BaseModel):
    type: Literal["CARD", "NEQUI", "PSE", "BANCOLOMBIA_QR", "BANCOLOMBIA_TRANSFER"]
    installments: Optional[int] = None

class Transation(BaseModel):
    currency: str = "COP"
    customer_email: Optional[EmailStr]
    payment_method: Optional[PaymentMethod] = None
    reference: Optional[EmailStr]
    MTid: int | str
    id: int | str
    materialId: str
    thicknessId: str
    
class TransationResponse(BaseModel):
    id: str
    customer_email: EmailStr
    payment_method_type: str
    
class Quote(BaseModel):
    material: str
    materialId: str
    thickness: str
    thicknessId: str
    fileId: str
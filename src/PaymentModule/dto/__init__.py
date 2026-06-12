from pydantic import BaseModel, model_validator, Field, EmailStr
from typing import Literal, Annotated
from fastapi import HTTPException
from src.PaymentModule.enums import ExceptionsEnum
import re

class ReferenceType(BaseModel):
    materialId: Annotated[str, Field(examples=["1"])]
    thicknessId: Annotated[str, Field(examples=["1"])]
    fileId: Annotated[str, Field(examples=["1"])]
    amount: Annotated[int, Field(examples=[1])]
    
class BilingType(BaseModel):
    name: Annotated[str, Field(examples=["Pedro Pérez"])]
    email: Annotated[EmailStr, Field(examples=["rangotv56@gmail.com"])]
    identification: Annotated[str, Field(examples=["123456789"])]

class PaymentTypeResponse(BaseModel):
    id: str
    created_at: str
    amount_in_cents: int
    reference: str
    payment_method_type: str
    redirect_url: str
    
class WompiTokenizerType(BaseModel):
    number: Annotated[str, Field(examples=["4242424242424242"])]
    cvc: Annotated[str, Field(examples=["789"])]
    exp_month: Annotated[str, Field(examples=["12"])]
    exp_year: Annotated[str, Field(examples=["29"])]
    card_holder: Annotated[str, Field(examples=["Pedro Pérez"])]
    
class PaymentMethodWompi(BaseModel):
    type: Annotated[Literal["CARD", "PSE", "NEQUI", "BANCOLOMBIA_QR", "BANCOLOMBIA_TRANSFER"], Field(examples=["CARD"])]
    phone_number: Annotated[str | None, Field(examples=["3017222568"])] = None
    token: str | None = None
    installments: Annotated[int | None, Field(examples=[1])] = None
    @model_validator(mode="after")
    def check_consistensy(self):
        match(self.type):
            case "CARD":
                pass
            case "NEQUI":
                if not self.phone_number:
                    raise HTTPException(400, ExceptionsEnum.NO_NEQUI_PHONE_NUMBER.value)
                if not re.match(r"^3\d{9}$", self.phone_number):
                    raise HTTPException(400, ExceptionsEnum.NO_VALID_COLOMBIAN_PHONE_NUMBER.value)
            case _:
                pass
        return self
    
class PaymentType(BaseModel):
    id: str | int | None = None
    status: str | None = None
    paymentMethodId: str | int | None = None
    acceptance_token: str
    accept_personal_auth: str
    amount_in_cents: Annotated[int | None, Field(examples=[150000])] = None
    payment_method: PaymentMethodWompi
    card: WompiTokenizerType | None = None
    reference: str | None = None 
    items: list[ReferenceType]
    userId: str | int | None = None
    billing: BilingType
    address: str | None = None
    @model_validator(mode="after")
    def check_card_consistency(self):
        if self.payment_method.type == "CARD" and self.card is None:
            raise HTTPException(400, ExceptionsEnum.NO_CARD_INFO.value)
        return self
    
class AcceptanceTokenType(BaseModel):
    acceptance_token: str
    permalink: str
    type: str
    
class AcceptanceTokens(BaseModel):
    presigned_acceptance: AcceptanceTokenType
    presigned_personal_data_auth: AcceptanceTokenType
    
class DbPaymentType(BaseModel):
    id: str | int
    p_id: str
    status: str
    reference: str
    created_at: str
    paymentMethod: str
    
class PaymentMethodType(BaseModel):
    id: str | int
    name: str

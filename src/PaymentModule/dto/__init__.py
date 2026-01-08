from pydantic import BaseModel, model_validator, Field
from typing import Literal, Optional, Annotated, List
from fastapi import HTTPException
from src.PaymentModule.enums import ExceptionsEnum
import re

class ReferenceType(BaseModel):
    materialId: Annotated[str, Field(examples=["1"])]
    thicknessId: Annotated[str, Field(examples=["1"])]
    fileId: Annotated[str, Field(examples=["1"])]
    amount: Annotated[int, Field(examples=[1])]

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
    phone_number: Annotated[Optional[str], Field(examples=["3017222568"])] = None
    token: Optional[str] = None
    installments: Annotated[Optional[int], Field(examples=[1])] = None
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
    id: Optional[str | int] = None
    status: Optional[str] = None
    paymentMethodId: Optional[str | int] = None
    acceptance_token: str
    accept_personal_auth: str
    amount_in_cents: Optional[Annotated[int, Field(examples=[150000])]] = None
    payment_method: PaymentMethodWompi
    card: Optional[WompiTokenizerType]
    reference: Optional[str] = None 
    items: List[ReferenceType]
    userId: Optional[str | int] = None
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
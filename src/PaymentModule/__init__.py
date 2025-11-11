from fastapi import APIRouter, Depends
from src.PaymentModule.paymentService import PaymentService
from src.PaymentModule.dto import AcceptanceTokens, PaymentType
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import AuthService
from typing import Annotated


router = APIRouter(prefix="/payment", tags=["pagos"])

paymentService: PaymentService = PaymentService.getInstance()

authService = AuthService.getInstance()

@router.get("/acceptancesTokens")
async def getAcceptanceTokens()->AcceptanceTokens:
    return await paymentService.getAcceptanceTokens()

@router.post("/")
async def makePayment(payment: PaymentType, u: Annotated[UserToken, Depends(authService.setUser)]):
    return await paymentService.makePayment(payment, u)

@router.get("/")
async def verifyPayment(id: str, u: Annotated[UserToken, Depends(authService.setUser)])->str:
    return await paymentService.verifyPayment(id)

@router.get("/verify")
async def untilNotGetPending(id: str, u: Annotated[UserToken, Depends(authService.setUser)])->str:
    return await paymentService.untilNotGetPending(id)
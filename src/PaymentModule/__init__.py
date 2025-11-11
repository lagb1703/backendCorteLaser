from fastapi import APIRouter, Depends, Request, Response
from src.PaymentModule.paymentService import PaymentService
from src.PaymentModule.dto import AcceptanceTokens, PaymentType, DbPaymentType
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import AuthService
from typing import Annotated, List


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
async def getPayments(u: Annotated[UserToken, Depends(authService.setUser)])->List[DbPaymentType]:
    return paymentService.getPayments(u.id)

@router.get("/verify")
async def verifyPayment(id: str, u: Annotated[UserToken, Depends(authService.setUser)])->str:
    return await paymentService.verifyPayment(id)

@router.get("/verify/APROVED")
async def untilNotGetPending(id: str, u: Annotated[UserToken, Depends(authService.setUser)])->str:
    return await paymentService.untilNotGetPending(id)

@router.post("/webhook")
async def webhook(request: Request, response: Response)->None:
    return await paymentService.webhook(request, response)
from fastapi import APIRouter, Depends, Request, Response
from src.PaymentModule.paymentService import PaymentService, get_payment_service
from src.PaymentModule.dto import AcceptanceTokens, PaymentMethodType, PaymentType, DbPaymentType
from src.UserModule.dtos import UserToken
from src.UserModule import get_current_user
from typing import Annotated, List

router = APIRouter(prefix="/payment", tags=["pagos"])

@router.get("/acceptancesTokens")
async def getAcceptanceTokens(
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->AcceptanceTokens:
    return await payment_service.getAcceptanceTokens()

@router.post("/")
async def makePayment(
    payment: PaymentType,
    u: Annotated[UserToken, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
):
    return await payment_service.makePayment(payment, u)

@router.get("/")
async def getPayments(
    u: Annotated[UserToken, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->List[DbPaymentType]:
    return await payment_service.getPayments(u.id)

@router.get("/paymentsMethods")
async def getPaymentMethods(
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->List[PaymentMethodType]:
    return await payment_service.getPaymentMethods()

@router.get("/verify")
async def verifyPayment(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->str:
    return await payment_service.verifyPayment(id)

@router.get("/verify/APROVED")
async def untilNotGetPending(
    id: str,
    u: Annotated[UserToken, Depends(get_current_user)],
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->str:
    return await payment_service.untilNotGetPending(id)

@router.post("/webhook")
async def webhook(
    request: Request,
    response: Response,
    payment_service: Annotated[PaymentService, Depends(get_payment_service)]
)->None:
    return await payment_service.webhook(request, response)

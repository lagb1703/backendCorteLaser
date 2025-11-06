from fastapi import APIRouter, Request, Depends
from src.PaymentModule.dto import Transation
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import AuthService
from src.PaymentModule.PaymentService import PaymentService

from typing import Annotated

segurity = AuthService.getInstance()

paymentService = PaymentService.getIntance()

router = APIRouter(prefix="/payments", tags=["payments"])

@router.get("/quoters")
async def getAllQuoters(user: Annotated[UserToken, Depends(segurity.setUser)]):
    return await paymentService.getAllQuoters(user)

@router.post("/payment")
async def createPayment(request: Request, user: Annotated[UserToken, Depends(segurity.setUser)], transation: Transation):
    return await paymentService.createPayment(request, user, transation)

@router.get("/payment")
async def getPaymnet(id: str, user: Annotated[UserToken, Depends(segurity.setUser)]):
    return await paymentService.getPayment(id)

@router.post("/webhook")
async def webHook(request: Request):
    return await paymentService.webHook(request)
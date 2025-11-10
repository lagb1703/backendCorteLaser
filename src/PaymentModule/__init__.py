from fastapi import APIRouter
from src.PaymentModule.paymentService import PaymentService
from src.PaymentModule.dto import AcceptanceTokens, PaymentType

router = APIRouter(prefix="/payment", tags=["pagos"])

paymentService: PaymentService = PaymentService.getInstance()

@router.get("/acceptancesTokens")
async def getAcceptanceTokens()->AcceptanceTokens:
    return await paymentService.getAcceptanceTokens()

@router.post("/")
async def makePayment(payment: PaymentType):
    return await paymentService.makePayment(payment)
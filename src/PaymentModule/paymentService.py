from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService
from src.PaymentModule.wompiWapper import WompiWapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import List, Dict, Any
from fastapi import Response, Request
from math import ceil
from src.PaymentModule.enums import PaymentStatus, PaymentSql

class PaymentService:
    
    __instance: 'PaymentService | None' = None
    
    @staticmethod
    def getInstance()->'PaymentService':
        if PaymentService.__instance is None:
            PaymentService.__instance = PaymentService()
        return PaymentService.__instance
    
    def __init__(self):
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        self.__fileService: FileService = FileService.getInstance()
        self.__wompiWapper: WompiWapper = WompiWapper()
        
    async def __makeDatabsePayment(self, payment: PaymentType, user: UserToken)->str:
        try:
            data: Dict[str, Any] = {
                "p_id": payment.id,
                "status": payment.status,
                "reference": payment.reference,
                "paymentMethodId": payment.paymentMethodId
            }
            return (await self.__postgress.save(PaymentSql.savePayment.value, data))["p_id"]
        except Exception as e:
            print(e)
            raise
        
    async def getPaymentMethods(self)->List[PaymentMethodType]:
        try:
            rows = await self.__postgress.query(PaymentSql.getAllPaymentMethods.value, [])
            return [PaymentMethodType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
    
    async def getAcceptanceTokens(self)->AcceptanceTokens:
        return await self.__wompiWapper.getAcceptanceTokens()
    
    async def makePayment(self, payment: PaymentType, user: UserToken)->str:
        payment.reference += f"@{user.id}"
        mt: List[str] = payment.reference.split("@")[0].split("-")
        fileId: str = mt[0]
        materialId: str = mt[1]
        thicknessId: str = mt[2]
        price: int = ceil((await self.__fileService.getPrice(fileId, materialId, thicknessId, user)).price)
        payment.amount_in_cents = price
        result = await self.__wompiWapper.makePayment(payment, user.email)
        payment.id = result.id
        payment.status = await self.verifyPayment(result.id)
        await self.__makeDatabsePayment(payment, user)
        return result.id
    
    async def verifyPayment(self, id: str)->str:
        result = await self.__wompiWapper.verifyPayment(id)
        return result["status"]
    
    async def untilNotGetPending(self, id: str)->str:
        result:str = ""
        i = 0
        while result != PaymentStatus.APPROVED.value and i < 10:
            result = await self.verifyPayment(id)
        return result
    
    async def getPayments(self, userId: int)->List[DbPaymentType]:
        try:
            rows = await self.__postgress.query(PaymentSql.getPaymentsByUserId.value, [userId])
            return [DbPaymentType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
    
    async def webhook(self, request: Request, response: Response)->None:
        response.status_code = 200
        body = await request.body()
        print(body)
        return
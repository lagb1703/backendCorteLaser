from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService
from src.PaymentModule.wompiWapper import WompiWapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import List
from fastapi import Response, Request
from src.PaymentModule.enums import PaymentStatus

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
        
    def getPaymentMethods(self)->List[PaymentMethodType]:
        return []
    
    async def getAcceptanceTokens(self)->AcceptanceTokens:
        return await self.__wompiWapper.getAcceptanceTokens()
    
    async def makePayment(self, payment: PaymentType, user: UserToken)->str:
        result = await self.__wompiWapper.makePayment(payment, user.email)
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
    
    def getPayments(self, userId: str)->List[DbPaymentType]:
        return []
    
    def webhook(self, request: Request, response: Response)->None:
        pass
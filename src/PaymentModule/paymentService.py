from src.utils.PostgressClient import PostgressClient
from src.FileModule.fileService import FileService
from src.PaymentModule.wompiWapper import WompiWapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import List
from fastapi import Response, Request

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
    
    async def makePayment(self, payment: PaymentType)->str:
        result = await self.__wompiWapper.makePayment(payment)
        return "result.id"
    
    def verifyPayment(self, id: str)->str:
        return ""
    
    def untilNotGetPending(self, id: str)->str:
        return ""
    
    def getPayments(self, userId: str)->List[DbPaymentType]:
        return []
    
    def webhook(self, request: Request, response: Response)->None:
        pass
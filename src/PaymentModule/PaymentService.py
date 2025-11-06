from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService
from src.PaymentModule.dto import Quote, Transation, TransationResponse
from src.PaymentModule.wompyWapper import WompyWarpper

from typing import Any, Dict, List
from fastapi import Request
import uuid
from datetime import datetime
class PaymentService:
    
    __instance: 'PaymentService | None' = None
    
    @staticmethod
    def getIntance()->'PaymentService':
        if PaymentService.__instance is None:
            PaymentService.__instance = PaymentService()
        return PaymentService.__instance
    
    def __init__(self):
        self.__wapper = WompyWarpper()
        self.__postgress = PostgressClient.getInstance()
        self.__fileService = FileService.getInstance()
        
    async def getAllQuoters(self, user: UserToken)->List[Quote]:
        return []
    async def createPayment(self, request: Request, user: UserToken, transation: Transation)->str:
        
        # Crear la estructura de datos que requiere Wompy
        wompy_data: Dict[str, Any] = {
            "amount_in_cents": 1000,
            "currency": "COP",
            "customer_email": "luis.giraldo3@utp.edu.co",
            "reference": f"ORDER-{uuid.uuid4().hex[:8]}-{int(datetime.now().timestamp())}",
            "payment_method": transation.payment_method.__dict__,
            "redirect_url": "https://tu-sitio.com/payment-success"
        }
        
        print(f"Enviando datos a Wompy: {wompy_data}")
        
        try:
            p = await self.__wapper.sendPayment(wompy_data)
            print(f"Respuesta de Wompy: {p}")
            return p.get("data", {}).get("id", "")
        except Exception as e:
            print(f"Error al enviar pago a Wompy: {e}")
            raise
    async def getPayment(self, id: str)->TransationResponse:
        return TransationResponse(id="1", customer_email="pdpd@gmail.com", payment_method_type="tarjeta")
    async def webHook(self, request:Request)-> Dict[str, bool]:
        return {"received": True}
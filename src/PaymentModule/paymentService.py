from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService
from src.PaymentModule.wompiWapper import WompiWapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import List, Dict, Any
from fastapi import Response, Request
from src.PaymentModule.enums import PaymentStatus, PaymentSql
from src.utils.EmailClient import EmailClient
from src.CmrModule.CmrService import CmrService
from email.message import EmailMessage
from json import loads
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
import uuid
class PaymentService:
    
    __instance: 'PaymentService | None' = None
    
    @staticmethod
    def getInstance()->'PaymentService':
        if PaymentService.__instance is None:
            PaymentService.__instance = PaymentService()
        return PaymentService.__instance
    
    def __init__(self):
        e: Enviroment = Enviroment.getInstance()
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        self.__fileService: FileService = FileService.getInstance()
        self.__wompiWapper: WompiWapper = WompiWapper()
        self.__emailClient: EmailClient = EmailClient()
        self.__bussinessEmail: str = e.get(EnviromentsEnum.GOOGLE_MAIL_USER.value)
        self.__cmrService: CmrService = CmrService.getInstance()
        
    async def __getPaymentInfoByReference(self, reference: str)->Dict[str, Any]:
        rows = await self.__postgress.query(PaymentSql.getPaymentInfoByReference.value, [reference])
        if not rows:
            return {}
        raw = rows[0].get("FU_PA_PAYMENTPKG_GETPAYMENTINFOBYREFERENCE")
        if raw is None:
            return {}
        if isinstance(raw, str):
            try:
                return loads(raw)
            except Exception:
                return {}
        # Si ya es JSON/objeto, devolver tal cual
        return raw
        
    async def __makeDatabsePayment(self, payment: PaymentType, amount: int, user: UserToken)->str:
        try:
            data: Dict[str, Any] = {
                "p_id": payment.id,
                "status": payment.status,
                "reference": payment.reference,
                "items": [r.model_dump() for r in payment.items],
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
        payment.userId = user.id
        payment.reference = uuid.uuid4().hex
        price = 0
        for i in payment.items:
            filePrice = await self.__fileService.getPrice(i.fileId, i.materialId, i.thicknessId, i.amount, user)
            price += filePrice.price
        price = int(price * 100)
        payment.amount_in_cents = price
        result = await self.__wompiWapper.makePayment(payment, user.email)
        payment.id = result.id
        payment.status = await self.verifyPayment(result.id)
        await self.__makeDatabsePayment(payment, price, user)
        if payment.status == PaymentStatus.APPROVED.value:
            await self.sendMessages(payment)
            return result.id
        email = EmailMessage()
        email["To"] = payment.billing.email
        email["Subject"] = "Problemas con el pago"
        email.set_content(f"""
        Hola,
        Hemos detectado un problema con el pago.
        Referencia de la transacción: {payment.reference}
        Estado actual: {payment.status}

        Por favor, responde a este correo y indica la referencia para que podamos ayudarte a resolverlo lo antes posible.

        Atentamente,
        Equipo de soporte
        """)
        await self.__emailClient.send(email)
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
            rows = await self.__postgress.query(PaymentSql.getPaymentsByUserId.value, [int(userId)])
            return [DbPaymentType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
        
    async def sendMessages(self, payment: PaymentType)->None:
        if payment.reference is None:
            return
        paymentInfo: Dict[str, Any] = await self.__getPaymentInfoByReference(payment.reference)
        items: List[Dict[str, Any]] = paymentInfo.get("items") or []
        if isinstance(items, str):
            try:
                items = loads(items)
            except Exception:
                items = []
        if isinstance(items, dict):
            items = [items]
        users: List[Dict[str, Any]] = paymentInfo.get("user") or []
        if isinstance(users, str):
            try:
                users = loads(users)
            except Exception:
                users = []
        if isinstance(users, dict):
            users = [users]
        if len(users) == 0 or len(items) == 0:
            return
        details = ""
        for info in items:
            name = info.get("name")
            fileId = info.get("fileId")
            materialName = info.get("materialName")
            thicknessName = info.get("thicknessName")
            amount_i = info.get("amount")
            details += f'- Archivo: {name} (ID: {fileId}) (material: {materialName}) (espesor: {thicknessName}) (cantidad: {amount_i})\n'
        email = EmailMessage()
        email["To"] = users[0].get("email")
        email["Subject"] = "Pago exitoso — Confirmación de pago"
        email.set_content(f"""
        Hola.
        Referencia de la transacción: {payment.reference}
        Estado: {payment.status}

        Detalles:
        {details}

        Tu pedido está siendo procesado y te notificaremos cuando esté listo para descarga o envío.

        Gracias por confiar en nosotros.

        Atentamente,
        Equipo de soporte
        """)
        await self.__emailClient.send(email)
        paymentInfo["amount_in_cents"] = payment.amount_in_cents
        paymentInfo["reference"] = payment.reference
        paymentInfo["billing"] = payment.billing.model_dump()
        paymentInfo["address"] = payment.address
        await self.__cmrService.addTask(paymentInfo)
        return
    
    async def webhook(self, request: Request, response: Response)->None:
        response.status_code = 200
        body = await request.body()
        data = loads(body)["data"]
        if(data is None or "transaction" not in data):
            return
        status = data["transaction"]["status"]
        reference: str = data["transaction"]["reference"]
        email_customer = data["transaction"]["customer_email"]
        amount_in_cents = data["transaction"]["amount_in_cents"]
        if status == PaymentStatus.APPROVED.value:
            payment = PaymentType(
                reference=reference,
                status=status,
                amount_in_cents=amount_in_cents
            ) # type: ignore
            await self.sendMessages(payment)
            return
        email = EmailMessage()
        email["To"] = email_customer
        email["Subject"] = "Problemas con el pago"
        email.set_content(f"""
        Hola,
        Hemos detectado un problema con el pago.
        Referencia de la transacción: {reference}
        Estado actual: {status}

        Por favor, responde a este correo o indica la referencia para que podamos ayudarte a resolverlo lo antes posible.

        Atentamente,
        Equipo de soporte
        """)
        await self.__emailClient.send(email)
        return
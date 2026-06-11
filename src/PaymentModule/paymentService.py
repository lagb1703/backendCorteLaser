from src.utils.PostgresClient import PostgresClient, get_postgres_client
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService, get_file_service
from src.PaymentModule.wompiWrapper import WompiWrapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import Any
from fastapi import Response, Request
from src.PaymentModule.enums import PaymentStatus, PaymentSql
from src.utils.EmailClient import EmailClient, get_email_client
from src.CmrModule.CmrService import CmrService, get_cmr_service
from email.message import EmailMessage
from json import loads, dumps
from src.utils import Environment
from src.utils.enums import EnvironmentsEnum
import uuid

class PaymentService:
    
    def __init__(
        self,
        postgres: PostgresClient,
        file_service: FileService,
        wompi_wrapper: WompiWrapper,
        email_client: EmailClient,
        cmr_service: CmrService,
        business_email: str
    ):
        self.__postgres = postgres
        self.__fileService = file_service
        self.__wompiWrapper = wompi_wrapper
        self.__emailClient = email_client
        self.__bussinessEmail = business_email
        self.__cmrService = cmr_service
        
    async def __getPaymentInfoByReference(self, reference: str)->dict[str, Any]:
        rows = await self.__postgres.query(PaymentSql.getPaymentInfoByReference.value, [reference])
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
        return raw
        
    async def __makeDatabsePayment(self, payment: PaymentType, amount: int, user: UserToken)->str:
        try:
            data: dict[str, Any] = {
                "p_id": payment.id,
                "status": payment.status,
                "reference": payment.reference,
                "items": [r.model_dump() for r in payment.items],
                "paymentMethodId": payment.paymentMethodId
            }
            print(dumps(data))
            return (await self.__postgres.save(PaymentSql.savePayment.value, data))["p_id"]
        except Exception as e:
            print(e)
            raise
        
    async def getPaymentMethods(self)->list[PaymentMethodType]:
        try:
            rows = await self.__postgres.query(PaymentSql.getAllPaymentMethods.value, [])
            return [PaymentMethodType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
    
    async def getAcceptanceTokens(self)->AcceptanceTokens:
        return await self.__wompiWrapper.getAcceptanceTokens()
    
    async def makePayment(self, payment: PaymentType, user: UserToken)->str:
        payment.userId = user.id
        payment.reference = uuid.uuid4().hex
        price = 0
        for i in payment.items:
            filePrice = await self.__fileService.getPrice(i.fileId, i.materialId, i.thicknessId, i.amount, user)
            price += filePrice.price
        price = int(price * 100)
        payment.amount_in_cents = price
        result = await self.__wompiWrapper.makePayment(payment, user.email)
        payment.id = result.id
        payment.status = await self.verifyPayment(result.id)
        await self.__makeDatabsePayment(payment, price, user)
        return result.id
    
    async def verifyPayment(self, id: str)->str:
        result = await self.__wompiWrapper.verifyPayment(id)
        return result["status"]
    
    async def untilNotGetPending(self, id: str)->str:
        result:str = ""
        i = 0
        while result != PaymentStatus.APPROVED.value and i < 10:
            result = await self.verifyPayment(id)
        return result
    
    async def getPayments(self, userId: int)->list[DbPaymentType]:
        try:
            rows = await self.__postgres.query(PaymentSql.getPaymentsByUserId.value, [int(userId)])
            return [DbPaymentType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
    
    async def webhook(self, request: Request, response: Response)->None:
        print("Received webhook")
        response.status_code = 200
        body = await request.body()
        data = loads(body)["data"]
        if(data is None or "transaction" not in data):
            return
        print(data)
        status = data["transaction"]["status"]
        reference: str = data["transaction"]["reference"]
        email_customer = data["transaction"]["customer_email"]
        amount_in_cents = data["transaction"]["amount_in_cents"]
        if status == PaymentStatus.APPROVED.value:
            paymentInfo: dict[str, Any] = await self.__getPaymentInfoByReference(reference)
            print("paymentInfo raw:", paymentInfo)
            items: list[dict[str, Any]] = paymentInfo.get("items") or []
            if isinstance(items, str):
                try:
                    items = loads(items)
                except Exception:
                    items = []
            if isinstance(items, dict):
                items = [items]
            users: list[dict[str, Any]] = paymentInfo.get("user") or []
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
            email["To"] = email_customer
            email["Subject"] = "Pago exitoso — Confirmación de pago"
            email.set_content(f"""
            Hola.
            Referencia de la transacción: {reference}
            Estado: {status}

            Detalles:
            {details}

            Tu pedido está siendo procesado y te notificaremos cuando esté listo para descarga o envío.

            Gracias por confiar en nosotros.

            Atentamente,
            Equipo de soporte
            """)
            await self.__emailClient.send(email)
            paymentInfo["amount_in_cents"] = amount_in_cents
            paymentInfo["reference"] = reference
            await self.__cmrService.addTask(paymentInfo)
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

def get_payment_service() -> PaymentService:
    e = Environment.getInstance()
    return PaymentService(
        postgres=get_postgres_client(),
        file_service=get_file_service(),
        wompi_wrapper=WompiWrapper(),
        email_client=get_email_client(),
        cmr_service=get_cmr_service(),
        business_email=e.get(EnvironmentsEnum.GOOGLE_MAIL_USER.value)
    )

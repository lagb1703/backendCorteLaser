from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import FileService
from src.PaymentModule.wompiWapper import WompiWapper
from src.PaymentModule.dto import PaymentMethodType, AcceptanceTokens, PaymentType, DbPaymentType
from typing import List, Dict, Any
from fastapi import Response, Request
from math import ceil
from src.PaymentModule.enums import PaymentStatus, PaymentSql
from src.MaterialModule.materialService import MaterialService
from src.utils.EmailClient import EmailClient
from email.message import EmailMessage
from json import loads
from src.UserModule.UserService import UserService
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum

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
        self.__materialService: MaterialService = MaterialService.getInstance()
        self.__userService: UserService = UserService.getInstance()
        self.__emailClient: EmailClient = EmailClient()
        self.__bussinessEmail: str = e.get(EnviromentsEnum.GOOGLE_MAIL_USER.value)
        
    async def __makeDatabsePayment(self, payment: PaymentType, amount: int, user: UserToken)->str:
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
        print(payment.reference)
        mt: List[str] = payment.reference.split("@")[0].split("-")
        print(mt)
        fileId: str = mt[0]
        materialId: str = mt[1]
        thicknessId: str = mt[2]
        amount: int = int(mt[3])
        price: int = ceil((await self.__fileService.getPrice(fileId, materialId, thicknessId, amount, user)).price)
        payment.amount_in_cents = price
        result = await self.__wompiWapper.makePayment(payment, user.email)
        payment.id = result.id
        payment.status = await self.verifyPayment(result.id)
        await self.__makeDatabsePayment(payment, amount, user)
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
            rows = await self.__postgress.query(PaymentSql.getPaymentsByUserId.value, [str(userId)])
            return [DbPaymentType.model_validate(r) for r in rows]
        except Exception as e:
            print(e)
            raise
    
    async def webhook(self, request: Request, response: Response)->None:
        response.status_code = 200
        body = await request.body()
        data = loads(body)["data"]
        status = data["transaction"]["status"]
        reference: str = data["transaction"]["reference"]
        email = data["transaction"]["customer_email"]
        mti, _, userId = reference.split("@")
        fileId, materialId, thicknessId, amount = mti.split("-")
        user = await self.__userService.getUSerById(userId)
        userToken = UserToken(id=int(userId), email=email, isAdmin=False)
        file = await self.__fileService.getFileInfo(fileId, userToken)
        if status == PaymentStatus.APPROVED.value:
            material = await self.__materialService.getMaterialById(materialId)
            thickness = await self.__materialService.getThicknessById(thicknessId)
            email = EmailMessage()
            email["To"] = user.email
            email["Subject"] = "Pago exitoso — Confirmación de pago"
            email.set_content(f"""
            Hola,

            Hemos recibido exitosamente el pago del archivo "{file.name}".
            Referencia de la transacción: {reference}
            Estado: {status}

            Detalles:
            - Material: {getattr(material, 'name', material)}
            - Espesor: {getattr(thickness, 'name', thickness)}
            - Cantidad: {amount}

            Tu pedido está siendo procesado y te notificaremos cuando esté listo para descarga o envío.

            Gracias por confiar en nosotros.

            Atentamente,
            Equipo de soporte
            """)
            await self.__emailClient.send(email)
            email = EmailMessage()
            # Enviar email al administrador con toda la información del usuario y del archivo
            email["To"] = self.__bussinessEmail
            email["Subject"] = "Nueva compra realizada — Detalles del usuario y archivo"
            user_name = f"{user.names} {user.lastNames}"
            user_email = getattr(user, "email", userId)
            user_address = user.address
            user_id = getattr(user, "id", userId)
            file_name = getattr(file, "name", "N/A")
            file_price = data["transaction"]["amount_in_cents"]
            phone = user.phone
            material_name = getattr(material, "name", material)
            thickness_name = getattr(thickness, "name", thickness)

            email.set_content(f"""
            Hola,

            Se ha registrado una nueva compra. A continuación todos los detalles disponibles:

            Usuario:
            - ID: {user_id}
            - Nombre: {user_name}
            - Email: {user_email}
            - Dirección: {user_address}
            - Telefono: {phone}

            Archivo:
            - ID: {fileId}
            - Nombre: {file_name}
            - Precio (archivo): {file_price}

            Material y espesor:
            - Id del glosor: {materialId}
            - Material: {material_name}
            - Id del espesor: {thicknessId}
            - Espesor: {thickness_name}
            - Cantidad: {amount}

            Pago:
            - Referencia: {reference}
            - Estado: {status}
            - Datos completos de la transacción: {str(data)}

            Por favor revisa la orden y procede según corresponda.

            Atentamente,
            Sistema de notificaciones
            """)
            await self.__emailClient.send(email)
            print("Notificación al administrador enviada: ", self.__bussinessEmail)
            return
        email = EmailMessage()
        email["To"] = user.email
        email["Subject"] = "Probemas con el pago"
        email.set_content(f"""
        Hola,
        Hemos detectado un problema con el pago del archivo "{file.name}".
        Referencia de la transacción: {reference}
        Estado actual: {status}

        Por favor, responde a este correo o indica la referencia para que podamos ayudarte a resolverlo lo antes posible.

        Atentamente,
        Equipo de soporte
        """)
        await self.__emailClient.send(email)
        print(data)
        print(status, reference, email)
        return
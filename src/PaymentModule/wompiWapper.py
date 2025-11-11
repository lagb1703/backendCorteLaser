from fastapi import HTTPException
from src.PaymentModule.paymentMethod import CardMethod, NequiMethod, PaymentMethod
from src.PaymentModule.dto import PaymentType, AcceptanceTokens, PaymentTypeResponse
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from src.PaymentModule.enums import ExceptionsEnum
import httpx
from typing import Dict

class WompiWapper:
    
    def __init__(self):
        e: Enviroment = Enviroment.getInstance()
        self.__link: str = e.get(EnviromentsEnum.WOMPY_URL.value)
        self.__pubKey: str = e.get(EnviromentsEnum.WOMPY_PUBLIC_KEY.value)
        self.__prKey: str = e.get(EnviromentsEnum.WOMPY_PRIVATE_KEY.value)
        self.__paymentMethods: Dict[str, PaymentMethod] = {
            "NEQUI":NequiMethod(),
            "CARD":CardMethod()
        }
        
    async def getAcceptanceTokens(self)-> AcceptanceTokens:
        url = f"{self.__link}merchants/{self.__pubKey}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                try:
                    tokens: AcceptanceTokens = AcceptanceTokens.model_validate(data["data"])
                except Exception as e:
                    raise HTTPException(502, f"Respuesta invalida desde WOMPI: {str(e)}")
                return tokens
            except httpx.TimeoutException:
                raise HTTPException(504, ExceptionsEnum.WOMPI_TIME_OUT.value)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                raise HTTPException(502, ExceptionsEnum.WOMPI_BAD_STATUS.value.replace(":Error", str(status)))
            except httpx.RequestError as e:
                raise HTTPException(502, ExceptionsEnum.WOMPI_BAD_STATUS.value.replace(":Error", str(e)))
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Error interno al obtener acceptance tokens: {str(e)}")
    
    async def makePayment(self, payment: PaymentType, userEmail: str)-> PaymentTypeResponse:
        paymentMethod: PaymentMethod | None = self.__paymentMethods.get(payment.payment_method.type)
        if paymentMethod is None:
            raise 
        return await paymentMethod.generatePayment(payment, userEmail)
    
    def verifyPayment(self, id: str)-> str:
        return ""
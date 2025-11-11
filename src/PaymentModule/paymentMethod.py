from fastapi import HTTPException
from src.PaymentModule.dto import PaymentTypeResponse, PaymentType#, WompiTokenizerType
from abc import ABC, abstractmethod
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from src.PaymentModule.enums import ExceptionsEnum
from typing import Dict, Any
import httpx

class PaymentMethod(ABC):
    
    def __init__(self):
        e: Enviroment = Enviroment.getInstance()
        self._link: str = e.get(EnviromentsEnum.WOMPY_URL.value)
        self._pubKey: str = e.get(EnviromentsEnum.WOMPY_PUBLIC_KEY.value)
        self._prKey: str = e.get(EnviromentsEnum.WOMPY_PRIVATE_KEY.value)
        
    async def _send(self, payload: Dict[str, Any])->PaymentTypeResponse:
        url = f"{self._link}transactions"
        print(payload)
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url=url, json=payload, headers={
                    "Authorization": f"Bearer {self._prKey}"
                })
                data = resp.json()
                print(data)
                resp.raise_for_status()
                try:
                    result: PaymentTypeResponse = PaymentTypeResponse.model_validate(data["data"])
                except Exception as e:
                    raise HTTPException(502, f"Respuesta invalida desde WOMPI al crear pago: {str(e)}")
                return result
            except httpx.TimeoutException:
                raise HTTPException(504, ExceptionsEnum.WOMPI_TIME_OUT.value)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                template = getattr(ExceptionsEnum, "WOMPI_BAD_STATUS", None)
                msg = template.value.replace(":Error", str(status)) if template is not None else f"WOMPI returned status {status}"
                raise HTTPException(502, msg)
            except httpx.RequestError as e:
                template = getattr(ExceptionsEnum, "WOMPI_BAD_STATUS", None)
                msg = template.value.replace(":Error", str(e)) if template is not None else f"WOMPI request error: {str(e)}"
                raise HTTPException(502, msg)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Error interno al generar pago: {str(e)}")
            
    async def _getPaymentSourceId(self, payload: Dict[str, Any])-> int:
        url = f"{self._link}payment_sources"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url=url, json=payload, headers={
                    "Authorization": f"Bearer {self._prKey}"
                })
                resp.raise_for_status()
                data = resp.json()
                return data["data"]["id"]
            except httpx.TimeoutException:
                raise HTTPException(504, ExceptionsEnum.WOMPI_TIME_OUT.value)
            except httpx.HTTPStatusError as e:
                status = e.response.status_code
                template = getattr(ExceptionsEnum, "WOMPI_BAD_STATUS", None)
                print(e)
                msg = template.value.replace(":Error", str(status)) if template is not None else f"WOMPI returned status {status}"
                raise HTTPException(502, msg)
            except httpx.RequestError as e:
                template = getattr(ExceptionsEnum, "WOMPI_BAD_STATUS", None)
                msg = template.value.replace(":Error", str(e)) if template is not None else f"WOMPI request error: {str(e)}"
                raise HTTPException(502, msg)
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(500, f"Error interno al generar pago: {str(e)}")
        
    
    @abstractmethod
    async def generatePayment(self, payment: PaymentType, userEmail: str)->PaymentTypeResponse:
        pass
    
    @abstractmethod
    async def tokenizer(self, paymentInfo: Dict[str, Any])->str:
        pass
    
class CardMethod(PaymentMethod):

    async def tokenizer(self, paymentInfo: Dict[str, Any])->str:
        url = f"{self._link}tokens/cards"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url=url, json=paymentInfo, headers={
                    "Authorization":f"Bearer {self._pubKey}"
                })
                resp.raise_for_status()
                data = resp.json()
                return data["data"]["id"]
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

    async def generatePayment(self, payment: PaymentType, userEmail: str)->PaymentTypeResponse:
        if payment.card is None:
            raise HTTPException(400, ExceptionsEnum.NO_CARD_INFO.value)
        token = await self.tokenizer(payment.card.__dict__)
        sourcePayload:Dict[str, str | int] = {
            "type":payment.payment_method.type,
            "token":token,
            "acceptance_token":payment.acceptance_token,
            "customer_email": userEmail
        }
        paymentSourceId: int = await self._getPaymentSourceId(sourcePayload)
        payload: Dict[str, Any] = {
            "acceptance_token":payment.acceptance_token,
            "amount_in_cents": payment.amount_in_cents,
            "currency": "COP",
            "customer_email": userEmail,
            "payment_method": {
                "type": payment.payment_method.type,
                "token": token,
                "installments": payment.payment_method.installments
            },
            "payment_source_id": paymentSourceId,
            "redirect_url": "https://mitienda.com.co/pago/resultado",
            "reference": payment.reference
        }
        return await self._send(payload)
    
class NequiMethod(PaymentMethod):
    
    async def tokenizer(self, paymentInfo: Dict[str, Any])->str:
        url = f"{self._link}tokens/nequi"
        urlGet = f"{self._link}tokens/nequi/"
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url=url, json=paymentInfo, headers={
                    "Authorization":f"Bearer {self._pubKey}"
                })
                resp.raise_for_status()
                data = resp.json()
                id:str = data["data"]["id"]
                resp = await client.get(url=f"{urlGet}{id}", headers={
                    "Authorization":f"Bearer {self._pubKey}"
                })
                data = resp.json()
                if data["data"]["status"] != "APPROVED":
                    raise
                return id
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

    async def generatePayment(self, payment: PaymentType, userEmail: str)->PaymentTypeResponse:
        pm = payment.payment_method
        if not getattr(pm, "phone_number", None):
            raise HTTPException(400, ExceptionsEnum.NO_NEQUI_PHONE_NUMBER.value)
        token = await self.tokenizer({
            "phone_number": pm.phone_number
        })
        sourcePayload:Dict[str, str | int] = {
            "type":payment.payment_method.type,
            "token":token,
            "acceptance_token":payment.acceptance_token,
            "customer_email": userEmail
        }
        paymentSourceId: int = await self._getPaymentSourceId(sourcePayload)
        payload: Dict[str, Any] = {
            "acceptance_token":payment.acceptance_token,
            "amount_in_cents": payment.amount_in_cents,
            "currency": "COP",
            "customer_email": userEmail,
            "payment_method": {
                "type": payment.payment_method.type,
                "token": token,
                "installments": payment.payment_method.installments
            },
            "payment_source_id": paymentSourceId,
            "redirect_url": "https://mitienda.com.co/pago/resultado",
            "reference": payment.reference
        }
        return await self._send(payload)
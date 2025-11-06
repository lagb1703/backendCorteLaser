from fastapi import HTTPException
import httpx
from typing import Dict, Any
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from src.PaymentModule.enums import ExceptionsEnum

import hmac
import hashlib

class WompyWarpper:
    
    def __init__(self):
        e = Enviroment.getInstance()
        self.__url: str = e.get(EnviromentsEnum.WOMPY_URL.value)
    
    async def verifySignature(self, body: bytes, signature: str)->bool:
        e = Enviroment.getInstance()
        secret = e.get(EnviromentsEnum.WOMPY_EVENT_KEY.value)
        if not secret:
            return True
        mac = hmac.new(secret.encode("utf-8"), body, hashlib.sha256)
        expected = mac.hexdigest()
        return hmac.compare_digest(expected, signature)
    
    async def sendPayment(self, data: Dict[str, Any])->Dict[str, Any]:
        try:
            e = Enviroment.getInstance()
            url = f"{self.__url}transactions"
            headers = {
                "Authorization": f"Bearer {e.get(EnviromentsEnum.WOMPY_PRIVATE_KEY.value)}",
                "Content-Type": "application/json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=data, headers=headers, timeout=30.0)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            error_detail = ExceptionsEnum.WOMPY_CONECTION_ERROR.value
            if e.response.status_code == 422:
                try:
                    error_response = e.response.json()
                    error_detail = f"Error de validación en Wompy: {error_response.get('error', {}).get('reason', 'Datos inválidos')}"
                except:
                    error_detail = "Error 422: Los datos enviados no son válidos según Wompy"
            raise HTTPException(status_code=e.response.status_code, detail=error_detail) from e
        except httpx.TimeoutException as e:
            # Captura timeouts de la solicitud
            raise HTTPException(504, ExceptionsEnum.TIME_OUT_EXCEPTION.value) from e
        except httpx.ConnectError as e:
            # Captura errores de conexión (DNS, conexión rechazada, etc.)
            raise HTTPException(503, ExceptionsEnum.WOMPY_DNS_ERROR.value) from e
        except httpx.RequestError as e:
            # Captura otras excepciones relacionadas con la solicitud de httpx
            raise HTTPException(500, ExceptionsEnum.WOMPY_NO_KNOWLEDGE_ERROR.value) from e
        except Exception as e:
            raise HTTPException(500, ExceptionsEnum.WOMPY_NO_KNOWLEDGE_ERROR.value) from e
    
    async def getPayment(self, id: str | int)->Dict[str, Any]:#transactions/
        try:
            url = f"{self.__url}transactions/{id}"
            e = Enviroment.getInstance()
            headers = {
                "Authorization": f"Bearer {e.get(EnviromentsEnum.WOMPY_PRIVATE_KEY.value)}",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, timeout=30.0)
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            # Captura errores de estado HTTP (4xx o 5xx)
            raise HTTPException(status_code=e.response.status_code, detail=ExceptionsEnum.WOMPY_CONECTION_ERROR.value) from e
        except httpx.TimeoutException as e:
            # Captura timeouts de la solicitud
            raise HTTPException(504, ExceptionsEnum.TIME_OUT_EXCEPTION.value) from e
        except httpx.ConnectError as e:
            # Captura errores de conexión (DNS, conexión rechazada, etc.)
            raise HTTPException(503, ExceptionsEnum.WOMPY_DNS_ERROR.value) from e
        except httpx.RequestError as e:
            # Captura otras excepciones relacionadas con la solicitud de httpx
            raise HTTPException(500, ExceptionsEnum.WOMPY_NO_KNOWLEDGE_ERROR.value) from e
        except Exception as e:
            raise HTTPException(500, ExceptionsEnum.WOMPY_NO_KNOWLEDGE_ERROR.value) from e
    
    async def webHookTraslate(self, body: bytes, signature: str)->Dict[str, Any]:
        return {}
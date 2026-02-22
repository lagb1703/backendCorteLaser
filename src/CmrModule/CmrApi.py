from abc import ABC, abstractmethod
from typing import Any, Dict, List
from src.UserModule.dtos import User
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
import httpx
from datetime import datetime
from json import dumps

class CmrApi(ABC):
    
    def __init__(self):
        e:Enviroment = Enviroment.getInstance()
        self._baseUrl: str = e.get(EnviromentsEnum.CRM_API_URL.value)
    
    @abstractmethod
    async def createNewCustomer(self, user: User)->str:
        pass
    
    @abstractmethod
    async def searchCustomerByDocument(self, document: str)->User | None:
        pass
    
    @abstractmethod
    async def updateCustomer(self, user: User, document: str)->None:
        pass
    
    @abstractmethod
    async def addTask(self, payments: Dict[str, Any])->None:
        pass
    
class Bitrix24(CmrApi):
    
    def __init__(self):
        super().__init__()
        e:Enviroment = Enviroment.getInstance()
        self.__customIdField: str = e.get(EnviromentsEnum.CRM_CUSTOM_IDENTIFICATION_FIELD.value)
    
    async def createNewCustomer(self, user: User)->str:
        url: str = self._baseUrl + "crm.contact.add"
        data: Dict[str, Any] = {
            "fields": {
                "NAME": user.names,
                "LAST_NAME": user.lastNames,
                "PHONE": [{"VALUE": user.phone, "VALUE_TYPE": "WORK"}],
                "EMAIL": [{"VALUE": user.email, "VALUE_TYPE": "WORK"}],
                self.__customIdField: user.identification,  # Custom field for identification
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resoponse = await client.post(url, json=data)
            if resoponse.status_code == 200:
                respData = resoponse.json()
                return str(respData.get("result", ""))
        return ''
    
    async def searchCustomerByDocument(self, document: str)->User | None:
        url: str = self._baseUrl + "crm.contact.list"
        data: Dict[str, Any] = {
            "filter": {
                self.__customIdField: document
            },
            "select": [
                "ID",
                "NAME",
                "LAST_NAME",
                "PHONE",
                "EMAIL"
            ]
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=data)
            if response.status_code == 200:
                respData = response.json()
                results = respData.get("result", [])
                if results:
                    contact = results[0]
                    return User(
                        id=int(contact.get("ID", 0)),
                        names=contact.get("NAME", ""),
                        lastNames=contact.get("LAST_NAME", ""),
                        email=contact.get("EMAIL", [{}])[0].get("VALUE", ""),
                        address='',
                        password='',
                        phone=contact.get("PHONE", [{}])[0].get("VALUE", 0),
                        isAdmin=False,
                        identification=document,
                        identificationTypeId='',
                        identificationType=''
                    )
    
    async def updateCustomer(self, user: User, document: str)->None:
        url: str = self._baseUrl + "crm.contact.update"
        data: Dict[str, Any] = {
            "fields": {
                "NAME": user.names,
                "LAST_NAME": user.lastNames,
                "PHONE": [{"VALUE": user.phone, "VALUE_TYPE": "WORK"}],
                "EMAIL": [{"VALUE": user.email, "VALUE_TYPE": "WORK"}],
                self.__customIdField: user.identification,  # Custom field for identification
            }
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(url, json=data)
            
    async def addTask(self, payments: Dict[str, Any])->None:
        url: str = self._baseUrl + "crm.deal.add"
        user = await self.searchCustomerByDocument(payments['user'][0].get("identification", ""))
        details: str = "Detalles de la compra:\n"
        items: List[Dict[str, Any]] = payments.get("items", [])
        amount_in_cents = payments["amount_in_cents"]
        reference = payments["reference"]
        for info in items:
            name = info.get("name")
            fileId = info.get("fileId")
            materialName = info.get("materialName")
            thicknessName = info.get("thicknessName")
            amount_i = info.get("amount")
            details += f'- Archivo: {name} (ID: {fileId}) (material: {materialName}) (espesor: {thicknessName}) (cantidad: {amount_i})\n'
        details += f"información sobre facturación:\nNombre: {payments['billing']['name']}\nEmail: {payments['billing']['email']}\nIdentificación: {payments['billing']['identification']}\n"
        if payments["address"]:
            details += f"información sobre envío:\nDirección: {payments['address']}"
        else:
            details += "información sobre envío:\nSe recogerá en tienda"
        data: Dict[str, Any] = {
            "fields": {
                "UF_CRM_1705079121953": reference,
                "UF_CRM_1705082852859":payments['user'][0].get("address", ""),
                "UF_CRM_1707322834825": "213",
                "TITLE": "(Ignorar prueba desde API) Nueva venta desde la web",
                "TYPE_ID": "COMPLEX",
                "CATEGORY_ID": "0",
                "STAGE_ID": "PREPAYMENT_INVOICE",
                "IS_RECURRING": "N",
                "IS_RETURN_CUSTOMER": "N",
                "IS_REPEATED_APPROACH": "N",
                "PROBABILITY": "0",
                "CURRENCY_ID": "COP",
                "OPPORTUNITY": f"{amount_in_cents / 100:.2f}",
                "IS_MANUAL_OPPORTUNITY": "Y",
                "TAX_VALUE": "0.00",
                "CONTACT_ID": user.id if user else None,
                "BEGINDATE": datetime.now().astimezone().isoformat(timespec='seconds'),
                "CLOSEDATE": datetime.now().astimezone().isoformat(timespec='seconds'),
                "OPENED": "Y",
                "COMMENTS": f"{details}",
                "SOURCE_ID": "STORE",
                "SOURCE_DESCRIPTION": "Venta desde la plataforma de Corte Laser",
                "ADDITIONAL_INFO": dumps(payments)
            },
            "params": { "REGISTER_SONET_EVENT": "Y" } 
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(url, json=data)
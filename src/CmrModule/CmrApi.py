from abc import ABC, abstractmethod
from typing import Any, Dict
from src.UserModule.dtos import User
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
import httpx

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
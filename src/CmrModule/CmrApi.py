from abc import ABC, abstractmethod
from src.UserModule.dtos import User
import httpx

class CmrApi(ABC):
    
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
    
    async def createNewCustomer(self, user: User)->str:
        return ''
    
    async def searchCustomerByDocument(self, document: str)->User | None:
        return User(
            names='',
            lastNames='',
            email='l@l.com',
            address='',
            password='',
            phone=0,
            isAdmin=False,
            identification='',
            identificationTypeId='',
            identificationType=''
        )
    
    async def updateCustomer(self, user: User, document: str)->None:
        return None
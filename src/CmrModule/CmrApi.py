from abc import ABC, abstractmethod
from src.UserModule.dtos import User
import httpx

class CmrApi(ABC):
    
    @abstractmethod
    def createNewCustomer(self, user: User)->str:
        pass
    
    @abstractmethod
    def searchCustomerByDocument(self, document: str)->User:
        pass
    
    @abstractmethod
    def updateCustomer(self, user: User, document: str)->None:
        pass
    
class Bitrix24(CmrApi):
    pass
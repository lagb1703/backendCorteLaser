from src.CmrModule.CmrApi import CmrApi, Bitrix24
from src.UserModule.dtos import User

class CmrService:
    
    __instance = None
    
    @staticmethod
    def getInstance():
        if CmrService.__instance is None:
            CmrService()
        return CmrService.__instance
    
    def __init__(self):
        self.cmr: CmrApi = Bitrix24()
        
    def addNewCustomer(self, user: User):
        return self.cmr.createNewCustomer(user)
    
    def updateCustomer(self, user: User, document: str):
        return self.cmr.updateCustomer(user, document)
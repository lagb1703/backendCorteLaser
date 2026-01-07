from src.CmrModule.CmrApi import CmrApi, Bitrix24
from src.UserModule.dtos import User

class CmrService:
    
    __instance = None
    
    @staticmethod
    def getInstance()-> 'CmrService':
        if CmrService.__instance is None:
            CmrService.__instance = CmrService()
        return CmrService.__instance
    
    def __init__(self):
        self.cmr: CmrApi = Bitrix24()
        
    async def addNewCustomer(self, user: User)->str:
        client: User | None = await self.cmr.searchCustomerByDocument(user.identification)
        if client is None:
            return ''
        return await self.cmr.createNewCustomer(user)
    
    async def updateCustomer(self, user: User, document: str):
        return await self.cmr.updateCustomer(user, document)
from typing import Any
from src.CmrModule.CmrApi import CmrApi, Bitrix24
from src.UserModule.dtos import User
from src.utils import Environment
from src.utils.enums import EnvironmentsEnum

class CmrService:
    
    def __init__(self, cmr_api: CmrApi):
        self.cmr: CmrApi = cmr_api
        
    async def addNewCustomer(self, user: User)->str:
        client: User | None = await self.cmr.searchCustomerByDocument(user.identification)
        print(client)
        if client is not None:
            return ''
        return await self.cmr.createNewCustomer(user)
    
    async def updateCustomer(self, user: User, document: str):
        return await self.cmr.updateCustomer(user, document)
    
    async def addTask(self, payments: dict[str, Any])->None:
        return await self.cmr.addTask(payments)

def get_bitrix24() -> Bitrix24:
    e = Environment.getInstance()
    base_url = e.get(EnvironmentsEnum.CRM_API_URL.value)
    custom_id_field = e.get(EnvironmentsEnum.CRM_CUSTOM_IDENTIFICATION_FIELD.value)
    return Bitrix24(base_url=base_url, custom_id_field=custom_id_field)

def get_cmr_service() -> CmrService:
    return CmrService(cmr_api=get_bitrix24())

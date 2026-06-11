from fastapi import APIRouter, Depends
from typing import Annotated
from src.CmrModule.CmrService import CmrService, get_cmr_service
from src.UserModule.dtos import User

router = APIRouter(prefix="/crm", tags=["CRM"])

@router.post("/customer")
async def add_customer(
    user: User,
    crm_service: Annotated[CmrService, Depends(get_cmr_service)]
):
    return await crm_service.addNewCustomer(user)

@router.put("/customer/{document}")
async def update_customer(
    document: str,
    user: User,
    crm_service: Annotated[CmrService, Depends(get_cmr_service)]
):
    return await crm_service.updateCustomer(user, document)

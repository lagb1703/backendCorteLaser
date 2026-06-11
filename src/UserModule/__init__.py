from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from src.UserModule.dtos import User, UserToken
from src.UserModule.UserService import UserService, get_user_service
from typing import Annotated
from src.autentification.Segurity import Segurity, get_segurity
from src.UserModule.enums import ExceptionsEnum
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from authlib.jose.errors import ExpiredTokenError

router = APIRouter(prefix="/user", tags=["User"])

security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingresa tu token JWT sin el prefijo 'Bearer'"
)

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    segurity: Segurity = Depends(get_segurity)
) -> UserToken:
    try:
        token = credentials.credentials
        return segurity.setUser(token)
    except ExpiredTokenError as _:
        raise HTTPException(401, ExceptionsEnum.EXPIRED_TOKEN.value)

async def get_current_admin_user(
    current_user: Annotated[UserToken, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
) -> UserToken:
    user = await user_service.getUSerById(current_user.id)
    current_user.isAdmin = user.isAdmin
    if not current_user.isAdmin:
        raise HTTPException(status_code=403, detail=ExceptionsEnum.NO_ROLL.value)
    return current_user

@router.get("/")
async def getUser(
    user: Annotated[UserToken, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
)->User:
    return await user_service.getUSerById(user.id)

@router.post("/register")
async def register(
    user: User,
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.register(user)

@router.get("/all")
async def getAllUser(
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.getAllUser()

@router.get("/userId")
async def getUserById(
    userId: int,
    _: Annotated[UserToken, Depends(get_current_admin_user)],
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.getUSerById(userId)

@router.patch("/address/{address}")
async def changeAddress(
    user: Annotated[UserToken, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    address: str = ""
)->None:
    return await user_service.changeAddress(address, user)

@router.get("/identificationTypes")
async def getAllIdentificationTypes(
    user_service: Annotated[UserService, Depends(get_user_service)]
):
    return await user_service.getAllIdentificationTypes()

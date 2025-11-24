from __future__ import annotations
from fastapi import APIRouter, Depends
from src.UserModule.dtos import User, UserToken
from src.UserModule.UserService import UserService
from typing import Annotated
from src.autentification.AuthService import AuthService

router = APIRouter(prefix="/user", tags=["User"])

userService = UserService.getInstance()

authService = AuthService.getInstance()


@router.get("/")
async def getUser(user: Annotated[UserToken, Depends(authService.setUser)])->User:
    return await userService.getUSerById(user.id)

@router.post("/register")
async def register(user: User):
    return await userService.register(user)


@router.get("/all")
async def getAllUser(_: Annotated[UserToken, Depends(authService.setUserAdmin)]):
    """
    Obtiene todos los usuarios. Requiere autenticación.
    """
    return await userService.getAllUser()


@router.get("/userId")
async def getUserById(userId: int, _: Annotated[UserToken, Depends(authService.setUserAdmin)]):
    """
    Obtiene un usuario por ID. Requiere autenticación.
    """
    return await userService.getUSerById(userId)

@router.patch("/")
async def changeAddress(user: Annotated[UserToken, Depends(authService.setUser)], address: str = "")->None:
    return await userService.changeAddress(address, user)
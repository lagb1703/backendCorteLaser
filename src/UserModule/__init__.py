from __future__ import annotations
from fastapi import APIRouter, Depends
from src.UserModule.dtos import User, UserToken
from src.UserModule.UserService import UserService
from typing import Annotated
from src.autentification.AuthService import AuthService

router = APIRouter(prefix="/user", tags=["User"])

userService = UserService.getInstance()

authService = AuthService.getInstance()


@router.post("/register")
async def register(user: User):
    return userService.register(user)


@router.get("/all")
async def getAllUser():
    """
    Obtiene todos los usuarios. Requiere autenticación.
    """
    return userService.getAllUser()


@router.get("/")
async def getUserById(user: Annotated[UserToken, Depends(authService.setUser)]):
    """
    Obtiene un usuario por ID. Requiere autenticación.
    """
    return userService.getUSerById(user.id)
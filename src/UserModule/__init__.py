from __future__ import annotations
from fastapi import APIRouter, Depends
from src.UserModule.dtos import User
from src.UserModule.UserService import UserService
from typing import TYPE_CHECKING

# Importar Segurity de manera perezosa para evitar importación circular.
def _get_segurity_class():
    # import local dentro de la función para romper la dependencia circular en tiempo de import
    from src.autentification.Segurity import Segurity as _Segurity
    return _Segurity

router = APIRouter(prefix="/user", tags=["User"])

userService = UserService.getInstance()

# Proveer acceso perezoso a la instancia de Segurity para evitar importación circular.
_segurity_instance = None

def get_segurity():
    """Devuelve la instancia singleton de Segurity. Se importa y crea bajo demanda."""
    global _segurity_instance
    if _segurity_instance is None:
        Segurity = _get_segurity_class()
        _segurity_instance = Segurity.getInstance()
    return _segurity_instance

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
async def getUserById(id: str):
    """
    Obtiene un usuario por ID. Requiere autenticación.
    """
    return userService.getUSerById(id)
from fastapi import APIRouter, Request, Depends
from src.autentification.dtos import UserLogin
from src.autentification.AuthService import AuthService, get_auth_service
from typing import Annotated

router = APIRouter(prefix="/auth", tags=["seguridad"])

@router.post("/login")
async def login(
    userLogin: UserLogin,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    return await auth_service.login(userLogin.email, userLogin.password)

@router.get("/login/google")
async def loginGoogle(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    return await auth_service.loginGoogle(request)

@router.get("/login/google/callback", name="auth_google_callback")
async def auth_google_callback(
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    return await auth_service.googleCallBack(request)

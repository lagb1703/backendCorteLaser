from fastapi import APIRouter, Request
from src.autentification.dtos import UserLogin
from src.autentification.AuthService import AuthService

router = APIRouter(prefix="/auth", tags=["seguridad"])

authService = AuthService.getInstance()

@router.post("/login")
async def login(userLogin: UserLogin):
    return authService.login(userLogin.email, userLogin.password)


@router.get("/login/google")
async def loginGoogle(request: Request):
    return await authService.loginGoogle(request)


@router.get("/login/google/callback")
async def auth_google_callback(request: Request):
    return await authService.googleCallBack(request)
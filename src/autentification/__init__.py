from fastapi import APIRouter, Request
from src.autentification.AuthService import AuthService
from src.autentification.dtos import UserLogin

auth = AuthService.getInstance()

router = APIRouter(prefix="/auth", tags=["seguridad"])

@router.post("/login")
async def login(userLogin: UserLogin):
    return auth.login(userLogin.email, userLogin.password)

@router.get("/login/google")
async def loginGoogle(request: Request):
    return await auth.loginGoogle(request)

@router.get("/login/google/callback")
async def auth_google_callback(request: Request):
    return await auth.googleCallBack(request)
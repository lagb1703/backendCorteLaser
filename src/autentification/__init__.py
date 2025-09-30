from fastapi import APIRouter
from autentification.AuthService import AuthService

auth = AuthService.getInstance()

router = APIRouter(prefix="auth", tags=["seguridad", "google"])

@router.get("/prueba")
async def prueba():
    print("prueba")
    return "prueba"
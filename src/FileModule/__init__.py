from fastapi import APIRouter, Request
from src.autentification.dtos import UserLogin
from src.autentification.AuthService import AuthService

router = APIRouter(prefix="/file", tags=["seguridad"])

authService = AuthService.getInstance()
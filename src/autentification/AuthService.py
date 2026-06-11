from __future__ import annotations
from typing import Any, TYPE_CHECKING
from src.autentification.Security import Security, get_security
from fastapi import HTTPException
from starlette.requests import Request
from src.autentification.enums import ExceptionsEnum
from src.utils import Environment
from src.utils.enums import EnvironmentsEnum
from authlib.integrations.starlette_client import OAuth  # type: ignore
from fastapi.responses import RedirectResponse
from src.UserModule.UserService import UserService, get_user_service

if TYPE_CHECKING:
    from src.UserModule.dtos import UserToken

class AuthService:
    
    def __init__(self, security: Security, user_service: UserService):
        e = Environment.getInstance()
        self.__security = security
        self.__userService = user_service
        self.__oauth = OAuth()
        self.__oauth.register( # type: ignore
            name="google",
            client_id=e.get(EnvironmentsEnum.GOOGLE_CLIENT_ID.value),
            client_secret=e.get(EnvironmentsEnum.GOOGLE_CLIENT_SECRET.value),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            }
        )
        
    async def login(self, userName: str, password: str)->str | bytes:
        user = await self.__userService.login(userName, password)
        return self.__security.getToken(user)
    
    async def loginGoogle(self, request: Request)-> Any:
        redirect_uri = request.url_for("auth_google_callback")
        return await self.__oauth.google.authorize_redirect(request, redirect_uri) # type: ignore
    
    async def googleCallBack(self, request: Request):
        try:
            token = await self.__oauth.google.authorize_access_token(request)  # type: ignore
            user_info = token.get("userinfo")  # type: ignore
            if not user_info:
                raise HTTPException(status_code=400, detail=ExceptionsEnum.NO_TOKEN.value)
            email: Any = user_info.get("email") # type: ignore
            if not email or not isinstance(email, str):
                raise HTTPException(status_code=400, detail=ExceptionsEnum.NO_TOKEN.value)
            from src.UserModule.dtos import UserToken
            e = Environment.getInstance()
            user = await self.__userService.getUserByEmail(email)
            if user.id is None:
                raise HTTPException(404, "usuario no encontrado")
            t: UserToken = UserToken(id=user.id, email=email, isAdmin=user.isAdmin)
            return RedirectResponse(f"{e.get(EnvironmentsEnum.GOOGLE_CALLBACK_URL.value)}?token={str(self.__security.getToken(t))}")

        except Exception as e:
            raise HTTPException(status_code=400, detail=ExceptionsEnum.GOOGLE_AUTH_ERROR.value.replace(":Error", str(e)))
        
    def refreshToken(self, token: str) -> str | bytes:
        return self.__security.refreshToken(token)

def get_auth_service() -> AuthService:
    return AuthService(
        security=get_security(),
        user_service=get_user_service()
    )

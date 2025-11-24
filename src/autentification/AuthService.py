from __future__ import annotations
from typing import Any, TYPE_CHECKING
from src.autentification.Segurity import Segurity
from fastapi import HTTPException, Depends
from starlette.requests import Request
from src.autentification.enums import ExceptionsEnum
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from authlib.integrations.starlette_client import OAuth  # type: ignore
from authlib.jose.errors import ExpiredTokenError
import ssl
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

if TYPE_CHECKING:
    from src.UserModule.dtos import UserToken

security = HTTPBearer(
    scheme_name="BearerAuth",
    description="Ingresa tu token JWT sin el prefijo 'Bearer'"
)

class AuthService:
    
    __instance: 'AuthService | None' = None
    
    @staticmethod
    def getInstance():
        if AuthService.__instance is None:
            AuthService.__instance = AuthService()
        return AuthService.__instance
    
    def __init__(self):
        from src.UserModule.UserService import UserService
        e = Enviroment.getInstance()
        self.__segurity = Segurity()
        self.__userService = UserService.getInstance()
        self.__oauth = OAuth()
        self.__oauth.register( # type: ignore
            name="google",
            client_id=e.get(EnviromentsEnum.GOOGLE_CLIENT_ID.value),
            client_secret=e.get(EnviromentsEnum.GOOGLE_CLIENT_SECRET.value),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={
                "scope": "openid email profile"
            }
        )
        
    async def login(self, userName: str, password: str)->str | bytes:
        user = await self.__userService.login(userName, password)
        return self.__segurity.getToken(user)
    
    async def loginGoogle(self, request: Request)-> Any:
        redirect_uri = request.url_for("auth_google_callback")
        return await self.__oauth.google.authorize_redirect(request, redirect_uri) # type: ignore
    
    async def googleCallBack(self, request: Request)-> str | bytes:
        try:
            token = await self.__oauth.google.authorize_access_token(request)  # type: ignore
            user_info = token.get("userinfo")  # type: ignore
            if not user_info:
                raise HTTPException(status_code=400, detail=ExceptionsEnum.NO_TOKEN.value)
            email: Any = user_info.get("email") # type: ignore
            if not email or not isinstance(email, str):
                raise HTTPException(status_code=400, detail=ExceptionsEnum.NO_TOKEN.value)
            from src.UserModule.dtos import UserToken
            t: UserToken = UserToken(id=0, email=email, isAdmin=True)
            return self.__segurity.getToken(t)

        except ssl.SSLError as ssl_error:
            raise HTTPException(status_code=400, detail=ExceptionsEnum.SSL_ERROR.value.replace(":error", str(ssl_error)))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=ExceptionsEnum.GOOGLE_AUTH_ERROR.value.replace(":Error", str(e)))
        
    def setUser(self, credentials: HTTPAuthorizationCredentials = Depends(security))->'UserToken':
        try:
            token = credentials.credentials
            return self.__segurity.setUser(token)
        except ExpiredTokenError as _:
            raise HTTPException(401, ExceptionsEnum.EXPIRED_TOKEN.value)
    
    async def setUserAdmin(self, credentials: HTTPAuthorizationCredentials = Depends(security))->'UserToken':
        token = credentials.credentials
        userToken =  self.__segurity.setUser(token)
        user = await self.__userService.getUSerById(userToken.id)
        userToken.isAdmin = user.isAdmin
        if not userToken.isAdmin:
            raise HTTPException(status_code=403, detail=ExceptionsEnum.NO_ROLL.value)
        return userToken
        
    def refreshToken(self, token: str) -> str | bytes:
        return self.__segurity.refreshToken(token)
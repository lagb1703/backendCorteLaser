from typing import Any
from src.autentification.Segurity import Segurity
from src.UserModule.UserService import UserService
from fastapi import HTTPException
from starlette.requests import Request
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from authlib.integrations.starlette_client import OAuth  # type: ignore
import ssl

class AuthService:
    
    __instance: 'AuthService | None' = None
    
    @staticmethod
    def getInstance():
        if AuthService.__instance is None:
            AuthService.__instance = AuthService()
        return AuthService.__instance
        
    
    def __init__(self):
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
        
    def login(self, userName: str, password: str)->str | bytes:
        user = self.__userService.login(userName, password)
        return self.__segurity.getToken(user)
    
    async def loginGoogle(self, request: Request)-> Any:
        redirect_uri = request.url_for("auth_google_callback")
        return await self.__oauth.google.authorize_redirect(request, redirect_uri) # type: ignore
    
    async def googleCallBack(self, request: Request)-> str | bytes:
        try:
            token = await self.__oauth.google.authorize_access_token(request) # type: ignore
            user_info = token.get("userinfo") # type: ignore
            
            if not user_info:
                raise HTTPException(status_code=400, detail="No se pudo obtener la información del usuario")
            return f"pepe el mago"
            
        except ssl.SSLError as ssl_error:
            raise HTTPException(status_code=400, detail=f"Error de certificado SSL. Verifica la configuración de red: {ssl_error}")
        except HTTPException:
            # Re-lanzar HTTPExceptions tal como están
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error autenticando con Google: {e}")
        
    def refreshToken(self, token: str) -> str | bytes:
        return self.__segurity.refreshToken(token)
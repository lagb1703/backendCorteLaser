from autentification.Segurity import Segurity
from src.UserModule.UserService import UserService
from src.UserModule.dtos import User
from fastapi import HTTPException
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from google.oauth2 import id_token
from google.auth.transport import requests

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
        self.__userService = UserService()
        self.__googleClient: str = e.get(EnviromentsEnum.GOOGLE_CLIENT.value)
    def login(self, userName: str, password: str)->bool:
        return self.__userService.login(userName, password)
    
    def loginGoogle(self, googleToken: str)->str | bytes:
        user_info = id_token.verify_oauth2_token(googleToken, requests.Request(), self.__googleClient) # type: ignore
        if not user_info:
            raise HTTPException(status_code=401, detail="Token de Google inválido")
        print(user_info) # type: ignore
        user = User(
            names=user_info["names"],  # type: ignore
            lastNames=user_info["lastNames"], # type: ignore
            email=user_info["email"], # type: ignore
            address=user_info["address"], # type: ignore
            password=user_info["password"], # type: ignore
            phone=user_info["phone"], # type: ignore
            isAdmin=False
        )
        token = self.__segurity.getToken(user)
        return token
        
    def refreshToken(self, token: str) -> str | bytes:
        return self.__segurity.refreshToken(token)
from .JWTWarpper import JWTWarpper
from src.autentification.enums import ExceptionsEnum
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from fastapi import Request, HTTPException
from src.UserModule.dtos import User

class Segurity:
    
    def __init__(self):
        e = Enviroment.getInstance()
        self.__jwt = JWTWarpper(e.get(EnviromentsEnum.JWT_KEY.value))
        
    def validateToken(self, token: str | bytes)->bool:
        try:
            self.__jwt.decode(token)
            return True
        except:
            return False
        
    def getToken(self, user: User)-> str | bytes:
        payload = user.__dict__
        return self.__jwt.encode(payload)
    
    def setUser(self, request: Request)->None:
        token = request.scope.get("authorization")
        if token is None or not isinstance(token, str):
            raise HTTPException(401, ExceptionsEnum.NO_TOKEN.value)
        token_value: str = token.split("Bearer ")[1]
        user = self.__jwt.decode(token_value)
        request.scope["user"] = user
        
    def refreshToken(self, token: str | bytes) -> str | bytes:
        return self.__jwt.refresh(token)
        

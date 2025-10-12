from __future__ import annotations
from typing import TYPE_CHECKING
from .JWTWarpper import JWTWarpper
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum

if TYPE_CHECKING:
    from src.UserModule.dtos import UserToken

class Segurity:
    
    __instance: 'Segurity | None' = None
    
    @staticmethod
    def getInstance()->'Segurity':
        if Segurity.__instance is None:
            Segurity.__instance = Segurity()
        return Segurity.__instance
    
    def __init__(self):
        from src.UserModule.dtos import UserToken
        e = Enviroment.getInstance()
        self.__jwt = JWTWarpper(e.get(EnviromentsEnum.JWT_KEY.value))
        self.__tokenDto = UserToken
        
    def validateToken(self, token: str | bytes)->bool:
        try:
            self.__jwt.decode(token)
            return True
        except:
            return False
        
    def getToken(self, user: 'UserToken')-> str | bytes:
        payload = user.__dict__
        return self.__jwt.encode(payload)
    
    def setUser(self, token: str | bytes)->'UserToken':
        user = self.__jwt.decode(token)
        return self.__tokenDto(
            id=user["id"],
            email=user["email"],
        )
        
    def refreshToken(self, token: str | bytes) -> str | bytes:
        return self.__jwt.refresh(token)
        

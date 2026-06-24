from __future__ import annotations
from typing import TYPE_CHECKING
from .JWTWarpper import JWTWarpper
from src.utils import Environment
from src.utils.enums import EnvironmentsEnum

if TYPE_CHECKING:
    from src.UserModule.dtos import UserToken

class Security:
    
    def __init__(self, jwt_key: str):
        from src.UserModule.dtos import UserToken
        self.__jwt = JWTWarpper(jwt_key)
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
        return self.__tokenDto.model_validate(user)
        
    def refreshToken(self, token: str | bytes) -> str | bytes:
        return self.__jwt.refresh(token)

def get_security() -> Security:
    e = Environment.getInstance()
    return Security(jwt_key=e.get(EnvironmentsEnum.JWT_KEY.value))

from authlib.jose import jwt, JWTClaims
from datetime import datetime, timezone, timedelta
from typing import Any
from src.autentification.enums import ExceptionsEnum

class JWTWarpper:
    
    def __init__(self, key: str | None = None, exp: timedelta | None = None):
        self.__key: str | None = key
        self.__exp: timedelta | None = exp
        self.__header = {"alg": "HS256"}
        
    def encode(self, payload: dict[str, Any], key: str | None = None, exp: timedelta | None = None)->bytes:
        if key is None and self.__key is None:
            raise Exception(ExceptionsEnum.NO_KEY.value)
        if key is None:
            key = self.__key
        if exp is not None:
            exp_time = int((datetime.now(timezone.utc) + exp).timestamp())
        elif self.__exp is not None:
            exp_time = int((datetime.now(timezone.utc) + self.__exp).timestamp())
        else:
            exp_time = int((datetime.now(timezone.utc) + timedelta(hours=1)).timestamp())
        payload['exp'] = exp_time
        token: bytes = jwt.encode(self.__header, payload, key) # type: ignore
        if isinstance(token, bytes):
            return token
        return bytes()
    
    def decode(self, token: str | bytes, key: str | None = None)->JWTClaims:
        if key is None and self.__key is not None:
            key = self.__key
        elif key is None:
            raise ValueError(ExceptionsEnum.NO_KEY.value)
        payload = jwt.decode(token, key) # type: ignore
        payload.validate() # type: ignore
        return payload
    
    def refresh(self, token: str | bytes, key: str | None = None, exp: timedelta | None = None)-> str | bytes:
        if key is None and self.__key is not None:
            key = self.__key
        elif key is None:
            raise ValueError(ExceptionsEnum.NO_KEY.value)
        payload = jwt.decode(token, key) # type: ignore
        return self.encode(payload, key, exp)
        
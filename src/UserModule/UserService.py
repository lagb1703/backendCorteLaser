from fastapi import HTTPException
from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import User, UserToken
from hashlib import sha256
from src.UserModule.enums import UserSql
from typing import List
from src.utils.EmailClient import EmailClient
from email.message import EmailMessage

import logging
class UserService:
    
    __instance: 'UserService | None' = None
    
    @staticmethod
    def getInstance():
        if UserService.__instance == None:
            UserService.__instance = UserService()
        return UserService.__instance
    
    def __init__(self):
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        self.__logger = logging.getLogger("UserService")
        self.__emailClient: EmailClient = EmailClient()
        
    async def login(self, userName: str, password: str)->UserToken:
        try:
            passSha256: str = sha256(password.encode('utf-8')).hexdigest()
            user = await self.__postgress.query(UserSql.login.value, [userName, passSha256])
            return UserToken.model_validate(user[0])
        except Exception as e:
            self.__logger.info(str(e))
            raise HTTPException(400, "")
    
    async def register(self, user: User)->bool:
        try:
            user.password = sha256(user.password.encode('utf-8')).hexdigest()
            id: int | str | None = (await self.__postgress.save(UserSql.register.value, user.__dict__))["p_id"]
            if id is None:
                raise HTTPException(400, "")
            email = EmailMessage()
            email["To"] = user.email
            email["Subject"] = "Bienvenido a CorteLazer"
            email.set_content("Recientemente se ha incrito una cuenta a nombre de este correo, si no ha sido usted, porfavor, responda este correo")
            await self.__emailClient.send(email)
            return True
        except Exception as e:
            self.__logger.info(str(e))
        return True
    
    async def getAllUser(self)->List[User]:
        try:
            rows = await self.__postgress.query(UserSql.getAllUser.value, [])
            users: List[User] = [User.model_validate(r) for r in rows]
            return users
        except Exception as e:
            self.__logger.info(str(e))
            raise 
    
    async def getUSerById(self, id: str | int)->User:
        try:
            rows = await self.__postgress.query(UserSql.getUSerById.value, [int(id)])
            return User.model_validate(rows[0])
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
    async def changeAddress(self, address: str, user: UserToken)->None:
        try:
            await self.__postgress.update(UserSql.changeAddress.value, {
                "address": address
            }, user.id)
        except Exception as e:
            self.__logger.info(str(e))
            raise
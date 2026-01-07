from fastapi import HTTPException
from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import User, UserToken
from hashlib import sha256
from src.UserModule.enums import UserSql, ExceptionsEnum
from typing import List
from src.utils.EmailClient import EmailClient
from src.CmrModule.CmrService import CmrService
from email.message import EmailMessage
from asyncpg.exceptions import UniqueViolationError # type: ignore

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
        self.__cmrService: CmrService = CmrService.getInstance()
        
    async def login(self, userName: str, password: str)->UserToken:
        try:
            passSha256: str = sha256(password.encode('utf-8')).hexdigest()
            user = await self.__postgress.query(UserSql.login.value, [userName, passSha256])
            if len(user) == 0:
                raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")
            return UserToken.model_validate(user[0])
        except HTTPException as e:
            self.__logger.info(str(e))
            raise
        except Exception as e:
            self.__logger.info(str(e))
            raise HTTPException(status_code=500, detail="Algo falló al procesar el inicio de sesión; por favor contacte al administrador.")

    async def register(self, user: User)->bool:
        try:
            print(user)
            user.password = sha256(user.password.encode('utf-8')).hexdigest()
            id: int | str | None = (await self.__postgress.save(UserSql.register.value, user.__dict__))["p_id"]
            if id is None:
                raise HTTPException(400, "")
            email = EmailMessage()
            email["To"] = user.email
            email["Subject"] = "Bienvenido a CorteLazer"
            email.set_content("Recientemente se ha incrito una cuenta a nombre de este correo, si no ha sido usted, porfavor, responda este correo")
            await self.__emailClient.send(email)
            await self.__cmrService.addNewCustomer(user)
            return True
        except HTTPException as e:
            raise
        except UniqueViolationError as e:
            raise HTTPException(status_code=409, detail=ExceptionsEnum.DUPLICATED_USER.value)
        except Exception as e:
            self.__logger.info(str(e))
            raise
    
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
            if len(rows) == 0:
                raise HTTPException(404, "No se ha detectado un usuario valido")
            return User.model_validate(rows[0])
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
    async def getUserByEmail(self, email: str)->User:
        try:
            rows = await self.__postgress.query(UserSql.getUSerByEmail.value, [email])
            if len(rows) == 0:
                raise HTTPException(404, "No se ha detectado un usuario valido")
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
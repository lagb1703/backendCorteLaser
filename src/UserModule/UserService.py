from fastapi import HTTPException
from src.utils.PostgresClient import PostgresClient, get_postgres_client
from src.UserModule.dtos import User, UserToken, IdentificationType
from hashlib import sha256
from src.UserModule.enums import UserSql, ExceptionsEnum
from src.utils.EmailClient import EmailClient, get_email_client
from src.CmrModule.CmrService import CmrService, get_cmr_service
from email.message import EmailMessage
from asyncpg.exceptions import UniqueViolationError  # type: ignore
import logging

class UserService:
    
    def __init__(
        self,
        postgres: PostgresClient,
        email_client: EmailClient,
        cmr_service: CmrService
    ):
        self.__postgres = postgres
        self.__logger = logging.getLogger("UserService")
        self.__emailClient = email_client
        self.__cmrService = cmr_service
        
    async def login(self, userName: str, password: str) -> UserToken:
        try:
            passSha256: str = sha256(password.encode('utf-8')).hexdigest()
            user = await self.__postgres.query(UserSql.login.value, [userName.lower(), passSha256])
            if len(user) == 0:
                raise HTTPException(status_code=401, detail="Usuario o contraseña inválidos")
            return UserToken.model_validate(user[0])
        except HTTPException as e:
            self.__logger.info(str(e))
            raise
        except Exception as e:
            self.__logger.info(str(e))
            raise HTTPException(status_code=500, detail="Algo falló al procesar el inicio de sesión; por favor contacte al administrador.")

    async def register(self, user: User) -> bool:
        try:
            user.password = sha256(user.password.encode('utf-8')).hexdigest()
            user.email = user.email.lower()
            id: int | str | None = (await self.__postgres.save(UserSql.register.value, user.model_dump()))["p_id"]
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
    
    async def getAllUser(self) -> list[User]:
        try:
            rows = await self.__postgres.query(UserSql.getAllUser.value, [])
            users: list[User] = [User.model_validate(r) for r in rows]
            return users
        except Exception as e:
            self.__logger.info(str(e))
            raise 
    
    async def getUserById(self, id: str | int) -> User:
        try:
            rows = await self.__postgres.query(UserSql.getUserById.value, [int(id)])
            if len(rows) == 0:
                raise HTTPException(404, "No se ha detectado un usuario valido")
            return User.model_validate(rows[0])
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
    async def getUserByEmail(self, email: str) -> User:
        try:
            rows = await self.__postgres.query(UserSql.getUserByEmail.value, [email])
            if len(rows) == 0:
                raise HTTPException(404, "No se ha detectado un usuario valido")
            return User.model_validate(rows[0])
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
        
    async def changeAddress(self, address: str, user: UserToken) -> None:
        try:
            await self.__postgres.update(UserSql.changeAddress.value, {
                "address": address
            }, user.id)
        except Exception as e:
            self.__logger.info(str(e))
            raise
        
    async def getAllIdentificationTypes(self) -> list[IdentificationType]:
        try:
            rows = await self.__postgres.query(UserSql.getAllIdentificationTypes.value, [])
            identificationTypes: list[IdentificationType] = [IdentificationType.model_validate(r) for r in rows]
            return identificationTypes
        except Exception as e:
            self.__logger.info(str(e))
            raise 

def get_user_service() -> UserService:
    return UserService(
        postgres=get_postgres_client(),
        email_client=get_email_client(),
        cmr_service=get_cmr_service()
    )

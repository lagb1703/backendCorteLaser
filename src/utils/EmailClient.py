from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from email.message import EmailMessage
import aiosmtplib

class EmailClient:
    
    def __init__(self):
        e: Enviroment = Enviroment.getInstance()
        self.__fromEmail: str = e.get(EnviromentsEnum.GOOGLE_MAIL_USER.value)
        self.__hostName: str = e.get(EnviromentsEnum.GOOGLE_MAIL_HOST.value)
        self.__port: int = int(e.get(EnviromentsEnum.GOOGLE_MAIL_PORT.value))
        self.__secure: bool = bool(e.get(EnviromentsEnum.GOOGLE_MAIL_SECURE.value))
        self.__password: str = e.get(EnviromentsEnum.GOOGLE_MAIL_PASS.value)
    
    async def send(self, message: EmailMessage)->None:
        await aiosmtplib.send(message, hostname=self.__hostName, port=self.__port, username=self.__fromEmail, password=self.__password)
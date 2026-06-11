from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from email.message import EmailMessage
import aiosmtplib

class EmailClient:
    
    def __init__(self, from_email: str, host_name: str, port: int, secure: bool, password: str):
        self.__fromEmail: str = from_email
        self.__hostName: str = host_name
        self.__port: int = port
        self.__secure: bool = secure
        self.__password: str = password
    
    async def send(self, message: EmailMessage)->None:
        message["From"] = self.__fromEmail
        await aiosmtplib.send(message, hostname=self.__hostName, port=self.__port, username=self.__fromEmail, password=self.__password)

def get_email_client() -> EmailClient:
    e: Enviroment = Enviroment.getInstance()
    return EmailClient(
        from_email=e.get(EnviromentsEnum.GOOGLE_MAIL_USER.value),
        host_name=e.get(EnviromentsEnum.GOOGLE_MAIL_HOST.value),
        port=int(e.get(EnviromentsEnum.GOOGLE_MAIL_PORT.value)),
        secure=bool(e.get(EnviromentsEnum.GOOGLE_MAIL_SECURE.value)),
        password=e.get(EnviromentsEnum.GOOGLE_MAIL_PASS.value)
    )

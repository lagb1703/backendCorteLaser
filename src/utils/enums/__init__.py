from enum import Enum

class EnviromentsEnum(Enum):
    DB_USER = "DB_USER"
    DB_PASSWORD = "DB_PASSWORD"
    DB_HOST = "DB_HOST"
    DB_PORT = "DB_PORT"
    DB_NAME = "DB_NAME"
    JWT_KEY = "JWT_KEY"
    GOOGLE_CLIENT = "TU_CLIENT_ID.apps.googleusercontent.com"
    
class ExceptionsEnum(Enum):
    NOT_ENVIROMENT_VARIABLE_AVABLE = "No se encontro la variable de entorno :variable"
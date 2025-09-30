from enum import Enum

class ExceptionsEnum(Enum):
    NO_KEY = "No se ha suministrado una clave"
    NO_TOKEN = "No se ha encontrado el token en la petición"
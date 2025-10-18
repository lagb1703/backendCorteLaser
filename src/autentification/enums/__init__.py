from enum import Enum

class ExceptionsEnum(Enum):
    NO_KEY = "No se ha suministrado una clave"
    NO_TOKEN = "No se ha encontrado el token en la petición"
    EXPIRED_TOKEN = "El token enviado ha expirado"
    NO_ROLL = "El usuario no tiene permisos para acceder"
    GOOGLE_AUTH_ERROR = "Error autenticando con Google: :Error"
    SSL_ERROR = "Error de certificado SSL. Verifica la configuración de red. :error"
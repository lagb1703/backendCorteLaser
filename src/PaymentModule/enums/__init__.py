from enum import Enum

class ExceptionsEnum(Enum):
    NO_CARD_INFO="No hay información sobre la tarjeta a utilizar"
    NO_NEQUI_PHONE_NUMBER="NO se envio el numero de telefono para utilizar nequi"
    NO_VALID_COLOMBIAN_PHONE_NUMBER="El numero de telefono no es valido"
    WOMPI_TIME_OUT="Bancolombia esta caido por el momento"
    WOMPI_BAD_STATUS="Bancolombia ha respondido con un error :Error"
    
class PaymentStatus(Enum):
    APPROVED="APPROVED"
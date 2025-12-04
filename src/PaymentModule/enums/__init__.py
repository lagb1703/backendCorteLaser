from enum import Enum

class ExceptionsEnum(Enum):
    NO_CARD_INFO="No hay información sobre la tarjeta a utilizar"
    NO_NEQUI_PHONE_NUMBER="NO se envio el numero de telefono para utilizar nequi"
    NO_VALID_COLOMBIAN_PHONE_NUMBER="El numero de telefono no es valido"
    WOMPI_TIME_OUT="Bancolombia esta caido por el momento"
    WOMPI_BAD_STATUS="Bancolombia ha respondido con un error :Error"
    
class PaymentStatus(Enum):
    APPROVED="APPROVED"
    
class PaymentSql(Enum):
    getAllPaymentMethods="""
        SELECT 
            ptppm."paymentMethodId" as "id",
            ptppm."paymentMethod" as "name"
        FROM "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" ptppm
    """
    getPaymentsByUserId="""
        SELECT 
            ptpp."paymentId" as "id",
            ptpp."p_id" as "p_id",
            ptpp.status as "status",
            ptpp.reference as "reference",
            ptpp."createdAt"::TEXT as "created_at",
            ptpp."paymentMethodId" as "paymentMethodId",
            ptppm."paymentMethod" as "paymentMethod"
        FROM "PAYMENT"."TB_PAYMENT_PAYMENTS" ptpp
        LEFT JOIN "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" ptppm
            ON ptppm."paymentMethodId" = ptpp."paymentMethodId"
        WHERE SPLIT_PART(ptpp."reference", '@', 3) = $1
    """
    savePayment="""
        call "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARPAYMENT"($1, $2)
    """
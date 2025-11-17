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
            ptpp."createdAt" as "createdAt",
            ptpp."paymentMethodId" as "paymentMethodId",
            ptppm."paymentMethod" as "paymentMethod"
        FROM "PAYMENT"."TB_PAYMENT_MTPAYMENT" ptpmp
        LEFT JOIN "PAYMENT"."TB_PAYMENT_PAYMENTS" ptpp
            ON ptpp."paymentId" = ptpmp."paymentId"
        LEFT JOIN "PAYMENT"."TB_PAYMENT_PAYMENTSMETHODS" ptppm
            ON ptppm."paymentMethodId" = ptpp."paymentMethodId"
        LEFT JOIN "FILE"."TB_FILE_MTFILES" mtfmt
            ON mtfmt."mtId" = ptpmp."mtId"
        LEFT JOIN "FILE"."TB_FILE_FILES" ftff
            ON ftff."fileId" = mtfmt."fileId"
        WHERE ftff."userId" = $1
    """
    savePayment="""
        call "PAYMENT"."SP_PA_PAYMENTPKG_AGREGARPAYMENT"($1, $2)
    """
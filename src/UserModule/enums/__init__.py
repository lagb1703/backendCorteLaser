from enum import Enum

class UserSql(Enum):
    login="""
        SELECT 
            utuu."userId" as "id",
            utuu.email as "email",
            utuu."isAdmin" as "isAdmin"
        FROM "USER"."TB_USU_USERS" utuu
        WHERE utuu.email = $1 and utuu.password = $2
    """
    register= """
        call "USER"."SP_USU_USERPKG_AGREGARUSUARIO"($1, $2)
    """
    getAllUser= """
        SELECT 
            utuu.names as "names",
            utuu."lastNames" as "lastNames",
            utuu.email as "email",
            utuu.address as "address",
            utuu.password as "password",
            utuu.phone as "phone",
            utuu."isAdmin" as "isAdmin"
        FROM "USER"."TB_USU_USERS" utuu
    """
    getUSerById= """
        SELECT 
            utuu.names as "names",
            utuu."lastNames" as "lastNames",
            utuu.email as "email",
            utuu.address as "address",
            utuu.password as "password",
            utuu.phone as "phone",
            utuu."isAdmin" as "isAdmin"
        FROM "USER"."TB_USU_USERS" utuu
        WHERE utuu."userId" = $1
    """
    changeAddress = """
        call "USER"."SP_USU_USERPKG_EDITARADDRESSUSUARIO"($1,$2)
    """
    
from enum import Enum

class ExceptionsEnum(Enum):
    BAD_FILE = "El archivo :file no es aceptable por ':description'"
    FILE_NOT_FOUND = "El archivo :file no fue encontrado"
    
class FolderName(Enum):
    ORIGINAL = "original"
    WKB = "WKB"
    
class FileSql(Enum):
    getFileById="""
        SELECT 
            ftff.name as "name",
            ftff.md5 as "md5",
            ftff.bucket as "bucket",
            ftff.date as "date",
            ftff."userId" as "userId"
        FROM "FILE"."TB_FILE_FILES" ftff
        WHERE ftff."fileId" = $1
    """
    getAllUserFiles="""
        SELECT 
            ftff."fileId" as "fileId",
            ftff.name as "name",
            ftff.md5 as "md5",
            ftff.bucket as "bucket",
            ftff.date as "date"
        FROM "FILE"."TB_FILE_FILES" ftff
        WHERE ftff."userId" = $1
    """
    saveFile="""
        call "FILE"."SP_FI_FILEPKG_AGREGARARCHIVO"($1, $2)
    """
    deleteFile="""
        call "FILE"."SP_FI_FILEPKG_ELIMINARARCHIVO"($1)
    """
    saveQuote="""
        call "FILE"."SP_FI_FILEPKG_AGREGARMTFILE"($1, $2)
    """
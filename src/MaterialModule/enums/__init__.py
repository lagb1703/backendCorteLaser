from enum import Enum

class ExceptionsEnum(Enum):
    BAD_FILE = "El archivo :file no es aceptable por ':description'"
    FILE_NOT_FOUND = "El archivo :file no fue encontrado"
    
class FolderName(Enum):
    ORIGINAL = "original"
    WKB = "WKB"
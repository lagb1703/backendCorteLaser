from enum import Enum

class ExceptionsEnum(Enum):
    BAD_FILE = "El archivo :file no es aceptable por ':description'"
    
class FolderName(Enum):
    ORIGINAL = "original"
    WKB = "WKB"
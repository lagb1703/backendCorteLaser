from os import environ
from dotenv import load_dotenv
from .enums import ExceptionsEnum
class Enviroment:
    
    __instance: 'Enviroment | None' = None
    
    @staticmethod
    def getInstance()->'Enviroment':
        if Enviroment.__instance is None:
            Enviroment.__instance = Enviroment()
        return Enviroment.__instance
    
    def __init__(self):
        load_dotenv()
        
    def get(self, name: str)->str:
        variable: str | None = environ.get(name)
        if variable is None:
            raise Exception(ExceptionsEnum.NOT_ENVIROMENT_VARIABLE_AVABLE.value.replace(":variable", name))
        return variable
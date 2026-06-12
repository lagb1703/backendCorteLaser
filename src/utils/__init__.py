from os import environ
from dotenv import load_dotenv
from .enums import ExceptionsEnum
class Environment:
    
    __instance: 'Environment | None' = None
    
    @staticmethod
    def getInstance()->'Environment':
        if Environment.__instance is None:
            Environment.__instance = Environment()
        return Environment.__instance
    
    def __init__(self):
        load_dotenv()
        
    def get(self, name: str)->str:
        variable: str | None = environ.get(name)
        if variable is None:
            raise Exception(ExceptionsEnum.NOT_ENVIRONMENT_VARIABLE_AVAILABLE.value.replace(":variable", name))
        return variable

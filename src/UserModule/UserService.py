from src.utils.PostgressClient import PostgressClient
from UserModule.dtos import User

class UserService:
    
    def __init__(self):
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        
    def login(self, userName: str, password: str)->bool:
        return True
    
    def register(self, user: User):
        pass
    
    def getAllUser(self):
        pass
    
    def getUSerById(self, id: str | int):
        pass
from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import User, UserToken

class UserService:
    
    __instance: 'UserService | None' = None
    
    @staticmethod
    def getInstance():
        if UserService.__instance == None:
            UserService.__instance = UserService()
        return UserService.__instance
    
    def __init__(self):
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        
    def login(self, userName: str, password: str)->UserToken:
        return UserToken(
            id=0, 
            email="ejemplo@gmail.com"
        )
    
    def register(self, user: User):
        pass
    
    def getAllUser(self):
        pass
    
    def getUSerById(self, id: str | int):
        pass
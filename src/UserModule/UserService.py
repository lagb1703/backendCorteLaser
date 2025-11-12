from src.utils.PostgressClient import PostgressClient
from src.UserModule.dtos import User, UserToken
from typing import List
class UserService:
    
    __instance: 'UserService | None' = None
    
    @staticmethod
    def getInstance():
        if UserService.__instance == None:
            UserService.__instance = UserService()
        return UserService.__instance
    
    def __init__(self):
        self.__postgress: PostgressClient = PostgressClient.getInstance()
        
    async def login(self, userName: str, password: str)->UserToken:
        return UserToken(
            id=0, 
            email="ejemplo@gmail.com"
        )
    
    async def register(self, user: User)->bool:
        return True
    
    async def getAllUser(self)->List[User]:
        return []
    
    async def getUSerById(self, id: str | int)->User:
        return User(
            names="pepe el mago",
            lastNames="no se",
            email="constantemente@gmail.com",
            password="contraseña",
            address="aca",
            phone="3017222568",
            isAdmin=True
        )
        
    async def changeAddress(self, address: str, user: UserToken)->None:
        return
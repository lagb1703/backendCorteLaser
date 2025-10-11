from fastapi import APIRouter
from src.UserModule.dtos import User, UserLogin
from src.UserModule.UserService import UserService

router = APIRouter(prefix="/user", tags=["User"])

userService = UserService.getInstance()

@router.post("/register")
async def register(user: User):
    return userService.register(user)

@router.post("/login")
async def login(user: UserLogin):
    return userService.login(user.email, user.password)

@router.get("/all")
async def getAllUser():
    return userService.getAllUser()

@router.get("/")
async def getUserById(id: str):
    return userService.getUSerById(id)
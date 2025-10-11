from fastapi import APIRouter
from src.UserModule.dtos import User
from src.UserModule.UserService import UserService

router = APIRouter(prefix="/user", tags=["User"])

userService = UserService.getInstance()

@router.post("/register")
async def register(user: User):
    return userService.register(user)

@router.get("/all")
async def getAllUser():
    return userService.getAllUser()

@router.get("/")
async def getUserById(id: str):
    return userService.getUSerById(id)
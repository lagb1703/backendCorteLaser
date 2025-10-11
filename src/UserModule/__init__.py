from fastapi import APIRouter
from src.UserModule.dtos import User
from src.UserModule.UserService import UserService

router = APIRouter(prefix="/user")



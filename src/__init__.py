from fastapi import APIRouter
from src.autentification import router as AuthRouter
from src.UserModule import router as UserRouter

routers = APIRouter(prefix="/api")

routers.include_router(AuthRouter)
routers.include_router(UserRouter)
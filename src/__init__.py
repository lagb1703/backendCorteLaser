from fastapi import APIRouter
from src.autentification import router as AuthRouter
from src.UserModule import router as UserRouter
from src.FileModule import router as FileRouter
from src.PaymentModule import router as PaymentRouter

routers = APIRouter(prefix="/api")

routers.include_router(AuthRouter)
routers.include_router(UserRouter)
routers.include_router(FileRouter)
routers.include_router(PaymentRouter)
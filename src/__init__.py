from fastapi import APIRouter
from src.autentification import router as AuthRouter

routers = APIRouter(prefix="/api")

routers.include_router(AuthRouter)
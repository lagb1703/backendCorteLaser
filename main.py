from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src import routers
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:3001",  
]

e = Enviroment.getInstance()

app.add_middleware(
    SessionMiddleware, 
    secret_key=e.get(EnviromentsEnum.JWT_KEY.value),
    same_site="lax",
    https_only=False
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers)
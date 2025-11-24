from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from src import routers
from src.utils import Enviroment
from src.utils.enums import EnviromentsEnum
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title="Backend Corte Laser API",
    description="API para el sistema de corte laser",
    version="1.0.0",
    swagger_ui_parameters={
        "persistAuthorization": True,
    }
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Backend Corte Laser API",
        version="1.0.0",
        description="API para el sistema de corte laser",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Ingresa tu token JWT"
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

origins = [
    "http://localhost",
    "http://localhost:3000", 
    "http://localhost:3001",  
    "https://solid-orbit-wrrq9pvpvrjf9p44-5173.app.github.dev",
]

e = Enviroment.getInstance()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware, 
    secret_key=e.get(EnviromentsEnum.JWT_KEY.value),
    same_site="lax",
    https_only=False
)

app.include_router(routers)
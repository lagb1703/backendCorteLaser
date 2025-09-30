from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src import routers

app = FastAPI()


app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(routers)

for router in routers:
    print("agregado router")
    app.include_router(router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
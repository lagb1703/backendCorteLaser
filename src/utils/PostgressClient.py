from asyncpg import Pool, create_pool  # type: ignore
from typing import Any
from types import TracebackType
from json import dumps
import asyncio
import sys
from . import Enviroment
from .enums import EnviromentsEnum
from functools import lru_cache

class PostgressClient:
    
    def __init__(self) -> None:
        self.pool: Pool | None = None  # type: ignore
        
    async def connect(self) -> None:
        try:
            if self.pool is None:
                print("Conectando a la base de datos...")
                envarioment: Enviroment = Enviroment.getInstance()
                user: str = envarioment.get(EnviromentsEnum.DB_USER.value)
                password: str = envarioment.get(EnviromentsEnum.DB_PASSWORD.value)
                host: str = envarioment.get(EnviromentsEnum.DB_HOST.value)
                port: str = envarioment.get(EnviromentsEnum.DB_PORT.value)
                db: str = envarioment.get(EnviromentsEnum.DB_NAME.value)
                self.pool = await create_pool(  # type: ignore
                    dsn=f"postgres://{user}:{password}@{host}:{port}/{db}",
                    min_size=1,
                    max_size=10,
                    max_inactive_connection_lifetime=300,
                )
                print("Conexión a la base de datos establecida.")
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            self.pool = None
        
    async def query(self, sql: str, data: list[Any] = []) -> list[dict[str, Any]]:
        if self.pool is None:
            await self.connect()
        
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                rows = await conn.fetch(sql, *data)  # type: ignore
                return [dict(row) for row in rows] if rows else []  # type: ignore
        return []
        
    async def save(self, sql: str, data: dict[str, Any]) -> dict[str, Any]:
        if self.pool is None:
            await self.connect()
            
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                row = await conn.fetchrow(sql, dumps(data), "0")  # type: ignore
                return dict(row) if row else {}  # type: ignore
        return {}
        
    async def update(self, sql: str, data: dict[str, Any], id: int | str) -> dict[str, Any]:
        if self.pool is None:
            await self.connect()
            
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                row = await conn.fetchrow(sql, dumps(data), id)  # type: ignore
                return dict(row) if row else {}  # type: ignore
        return {}
    
    async def delete(self, sql: str, id: str | int) -> list[dict[str, Any]]:
        if self.pool is None:
            await self.connect()
        
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                rows = await conn.fetch(sql, id)  # type: ignore
                return [dict(row) for row in rows] if rows else []  # type: ignore
        return []
        
    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()  # type: ignore
            self.pool = None

    def __del__(self):
        if self.pool is None:
            return
        if sys.is_finalizing():
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.pool.close())
            else:
                loop.run_until_complete(self.pool.close())
        except Exception:
            pass
        finally:
            self.pool = None
            
    async def __aenter__(self) -> 'PostgressClient':
        return get_postgress_client()
        
    async def __aexit__(
        self, 
        exc_type: type[BaseException] | None, 
        exc_val: BaseException | None, 
        exc_tb: TracebackType | None
    ) -> None:
        pass

@lru_cache()
def get_postgress_client() -> PostgressClient:
    return PostgressClient()

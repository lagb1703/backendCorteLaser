from asyncpg import Pool, create_pool  # type: ignore
from typing import Any, Optional, Dict, Union, Type, List
from types import TracebackType
from json import dumps
import asyncio
import sys
from . import Enviroment
from .enums import EnviromentsEnum

class PostgressClient:
    
    __instance: 'PostgressClient | None' = None; 
    
    @staticmethod
    def getInstance()->'PostgressClient':
        if PostgressClient.__instance is None:
            PostgressClient.__instance = PostgressClient()
        return PostgressClient.__instance
    
    def __init__(self) -> None:
        self.pool: Optional[Pool] = None  # type: ignore
        
    async def connect(self) -> None:
        """Inicializa el pool de conexiones de forma asíncrona"""
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
        
    async def query(self, sql: str, data: List[Any] = []) -> list[Dict[str, Any]]:
        """Ejecuta una consulta y retorna múltiples registros"""
        if self.pool is None:
            await self.connect()
        
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                rows = await conn.fetch(sql, *data)  # type: ignore
                return [dict(row) for row in rows] if rows else []  # type: ignore
        return []
        
    async def save(self, sql: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Guarda un registro y retorna el resultado"""
        if self.pool is None:
            await self.connect()
            
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                row = await conn.fetchrow(sql, dumps(data), "0")  # type: ignore
                return dict(row) if row else {}  # type: ignore
        return {}
        
    async def update(self, sql: str, data: Dict[str, Any], id: Union[int, str]) -> Dict[str, Any]:
        """Actualiza un registro usando el ID proporcionado"""
        if self.pool is None:
            await self.connect()
            
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                # Incluir el ID en los parámetros
                row = await conn.fetchrow(sql, dumps(data), id)  # type: ignore
                return dict(row) if row else {}  # type: ignore
        return {}
    
    async def delete(self, sql: str, id: str | int) -> list[Dict[str, Any]]:
        """Ejecuta una consulta y retorna múltiples registros"""
        if self.pool is None:
            await self.connect()
        
        if self.pool is not None:
            async with self.pool.acquire() as conn:  # type: ignore
                rows = await conn.fetch(sql, id)  # type: ignore
                return [dict(row) for row in rows] if rows else []  # type: ignore
        return []
        
    async def close(self) -> None:
        """Cierra el pool de conexiones"""
        if self.pool is not None:
            await self.pool.close()  # type: ignore
            self.pool = None
    def __del__(self):
        # Avoid running async operations during interpreter shutdown
        if self.pool is None:
            return
        # If Python is finalizing, don't try to create or use event loop
        if sys.is_finalizing():
            return
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # schedule close; it will run on the running loop
                loop.create_task(self.pool.close())
            else:
                # run until complete on the current thread loop
                loop.run_until_complete(self.pool.close())
        except Exception:
            # best effort; don't raise in destructor
            pass
        finally:
            self.pool = None
            
    async def __aenter__(self) -> 'PostgressClient':
        """Soporte para async context manager"""
        return PostgressClient.getInstance()
        
    async def __aexit__(
        self, 
        exc_type: Optional[Type[BaseException]], 
        exc_val: Optional[BaseException], 
        exc_tb: Optional[TracebackType]
    ) -> None:
        """Cierra las conexiones al salir del context manager"""
        pass
            
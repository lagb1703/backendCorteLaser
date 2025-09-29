"""
Ejemplo de uso de PostgressClient

Este archivo muestra cómo usar la clase PostgressClient de forma correcta
con manejo adecuado de conexiones asíncronas.
"""
import asyncio
from src.utils.PostgressClient import PostgressClient

async def main():
    # Crear instancia del cliente
    db_client = PostgressClient.getInstance()
    
    try:
        
        # Ejemplo de consulta
        result = await db_client.query(
            'SELECT * FROM curriculum."TB_HV_BANCOS" WHERE "IDBANCO" = $1', 
            [63]
        )
        print("Resultado de consulta:", result)
        
        # # Ejemplo de guardado
        # new_user = await db_client.save(
        #     "INSERT INTO users (data) VALUES ($1) RETURNING *",
        #     {"name": "Juan", "email": "juan@example.com"}
        # )
        # print("Nuevo usuario:", new_user)
        
        # # Ejemplo de actualización
        # updated_user = await db_client.update(
        #     "UPDATE users SET data = $1 WHERE id = $2 RETURNING *",
        #     {"name": "Juan Actualizado", "email": "juan.nuevo@example.com"},
        #     1
        # )
        # print("Usuario actualizado:", updated_user)
        
    finally:
        await db_client.close()

async def main_with_context_manager():
    # Opción 2: Uso con context manager (recomendado)
    async with PostgressClient() as db_client:
        result = await db_client.query(
            'SELECT * FROM curriculum."TB_HV_BANCOS" WHERE "IDBANCO" = $1', 
            [63]
        )
        print("Resultado con context manager:", result)
        # La conexión se cierra automáticamente

if __name__ == "__main__":
    # Ejecutar ejemplo
    asyncio.run(main_with_context_manager())
    # O con context manager
    # asyncio.run(main_with_context_manager())
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils.PostgresClient import PostgresClient


class TestPostgresClient:
    @pytest.fixture
    def postgres_client(self):
        return PostgresClient()

    @pytest.mark.asyncio
    async def test_connect_success(self, postgres_client):
        with patch("src.utils.PostgresClient.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            with patch("src.utils.PostgresClient.Environment.getInstance") as mock_env:
                mock_env.return_value.get.return_value = "test_value"
                
                await postgres_client.connect()
                assert postgres_client.pool is not None
                mock_create_pool.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, postgres_client):
        with patch("src.utils.PostgresClient.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_create_pool.side_effect = Exception("Connection failed")
            
            with patch("src.utils.PostgresClient.Environment.getInstance") as mock_env:
                mock_env.return_value.get.return_value = "test_value"
                
                await postgres_client.connect()
                assert postgres_client.pool is None

    @pytest.mark.asyncio
    async def test_query_success(self, postgres_client):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"id": 1, "name": "test"}])
        
        # Create a proper async context manager
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = AsyncContextManager()
        postgres_client.pool = mock_pool
        
        result = await postgres_client.query("SELECT * FROM test", [])
        assert len(result) == 1
        assert result[0]["id"] == 1

    @pytest.mark.asyncio
    async def test_query_empty_result(self, postgres_client):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[])
        
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = AsyncContextManager()
        postgres_client.pool = mock_pool
        
        result = await postgres_client.query("SELECT * FROM test", [])
        assert result == []

    @pytest.mark.asyncio
    async def test_query_no_pool(self, postgres_client):
        with patch("src.utils.PostgresClient.create_pool", new_callable=AsyncMock) as mock_create_pool:
            mock_pool = MagicMock()
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[{"id": 1}])
            
            class AsyncContextManager:
                async def __aenter__(self):
                    return mock_conn
                async def __aexit__(self, *args):
                    pass
            
            mock_pool.acquire.return_value = AsyncContextManager()
            mock_create_pool.return_value = mock_pool
            
            with patch("src.utils.PostgresClient.Environment.getInstance") as mock_env:
                mock_env.return_value.get.return_value = "test_value"
                
                result = await postgres_client.query("SELECT * FROM test", [])
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_save_success(self, postgres_client):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"p_id": 1})
        
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = AsyncContextManager()
        postgres_client.pool = mock_pool
        
        result = await postgres_client.save("INSERT INTO test", {"name": "test"})
        assert result["p_id"] == 1

    @pytest.mark.asyncio
    async def test_update_success(self, postgres_client):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetchrow = AsyncMock(return_value={"p_id": 1})
        
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = AsyncContextManager()
        postgres_client.pool = mock_pool
        
        result = await postgres_client.update("UPDATE test", {"name": "test"}, 1)
        assert result["p_id"] == 1

    @pytest.mark.asyncio
    async def test_delete_success(self, postgres_client):
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_conn.fetch = AsyncMock(return_value=[{"deleted": True}])
        
        class AsyncContextManager:
            async def __aenter__(self):
                return mock_conn
            async def __aexit__(self, *args):
                pass
        
        mock_pool.acquire.return_value = AsyncContextManager()
        postgres_client.pool = mock_pool
        
        result = await postgres_client.delete("DELETE FROM test", 1)
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_close(self, postgres_client):
        mock_pool = AsyncMock()
        postgres_client.pool = mock_pool
        
        await postgres_client.close()
        mock_pool.close.assert_called_once()
        assert postgres_client.pool is None

    @pytest.mark.asyncio
    async def test_context_manager(self, postgres_client):
        with patch("src.utils.PostgresClient.get_postgres_client") as mock_get_client:
            mock_get_client.return_value = postgres_client
            
            async with postgres_client as client:
                assert client is postgres_client

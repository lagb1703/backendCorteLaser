import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from src.UserModule.dtos import UserToken
from src.FileModule.fileService import get_file_service
from src.autentification.Security import get_security
from src.UserModule.UserService import get_user_service
from src.FileModule.dtos import FileDb


class TestFileRouter:
    @pytest.fixture
    def mock_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.fixture
    def mock_admin_token(self):
        return UserToken(id=1, email="admin@example.com", isAdmin=True)

    @pytest.fixture
    def mock_file_service(self):
        service = AsyncMock()
        service.getAllUserInfoFiles = AsyncMock(return_value=[
            FileDb(id=1, name="test.dxf", date="2024-01-01", md5="abc123", bucket="original", userId=1)
        ])
        service.saveFile = AsyncMock(return_value=1)
        service.getFileInfo = AsyncMock(return_value=FileDb(id=1, name="test.dxf", date="2024-01-01", md5="abc123", bucket="original", userId=1))
        service.getFile = AsyncMock()
        service.getImage = AsyncMock()
        service.deleteFile = AsyncMock()
        service.getPrice = AsyncMock(return_value=MagicMock(price=1500.0))
        service.setPriceCalculator = AsyncMock()
        service.getPriceEstimate = AsyncMock(return_value="price + 100")
        return service

    @pytest.fixture
    def mock_security(self, mock_user_token):
        security = MagicMock()
        security.setUser = MagicMock(return_value=mock_user_token)
        return security

    @pytest.fixture
    def mock_admin_security(self, mock_admin_token):
        security = MagicMock()
        security.setUser = MagicMock(return_value=mock_admin_token)
        return security

    @pytest.fixture
    def mock_user_service(self, mock_admin_token):
        service = AsyncMock()
        service.getUserById = AsyncMock(return_value=MagicMock(isAdmin=True))
        return service

    @pytest.mark.asyncio
    async def test_get_all_user_files(self, mock_file_service, mock_security):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_file_metadata(self, mock_file_service, mock_security):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file/metadata?id=1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_file_download(self, mock_file_service, mock_security):
        from fastapi.responses import StreamingResponse
        from io import BytesIO
        mock_file_service.getFile = AsyncMock(return_value=StreamingResponse(
            BytesIO(b"file_content"),
            media_type="application/octet-stream"
        ))
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file/donwload?id=1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_image(self, mock_file_service, mock_security):
        from fastapi.responses import StreamingResponse
        from io import BytesIO
        mock_file_service.getImage = AsyncMock(return_value=StreamingResponse(
            BytesIO(b"image_data"),
            media_type="image/png"
        ))
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file/image?id=1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_file(self, mock_file_service, mock_security):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    "/api/file?id=1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_price(self, mock_file_service, mock_security):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file/price?id=1&materialId=1&thicknessId=1&amount=1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_set_price_calculator(self, mock_file_service, mock_admin_security, mock_user_service):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_admin_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/file/price?exp=price+100",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_price_estimate(self, mock_file_service, mock_admin_security, mock_user_service):
        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_admin_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/file/price/estimate",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/file")
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_admin_endpoint_without_admin_role(self, mock_file_service, mock_security, mock_user_service):
        non_admin_token = UserToken(id=2, email="user@example.com", isAdmin=False)
        mock_security.setUser = MagicMock(return_value=non_admin_token)
        mock_user_service.getUserById = AsyncMock(return_value=MagicMock(isAdmin=False))

        app.dependency_overrides[get_file_service] = lambda: mock_file_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/file/price?exp=price+100",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
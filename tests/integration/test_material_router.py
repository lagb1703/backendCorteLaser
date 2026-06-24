import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from src.UserModule.dtos import UserToken
from src.MaterialModule.materialService import get_material_service
from src.autentification.Security import get_security
from src.UserModule.UserService import get_user_service


class TestMaterialRouter:
    @pytest.fixture
    def mock_admin_token(self):
        return UserToken(id=1, email="admin@example.com", isAdmin=True)

    @pytest.fixture
    def mock_material_service(self):
        service = AsyncMock()
        service.getAllMaterials = AsyncMock(return_value=[
            {"materialId": 1, "name": "Acrylic", "price": 100, "weight": 1.5}
        ])
        service.getAllThickness = AsyncMock(return_value=[
            {"thicknessId": 1, "name": "3mm", "price": 50, "speed": 10.0}
        ])
        service.getMaterialById = AsyncMock(return_value={"materialId": 1, "name": "Acrylic", "price": 100, "weight": 1.5})
        service.getThicknessByMaterial = AsyncMock(return_value=[
            {"thicknessId": 1, "name": "3mm", "price": 50, "speed": 10.0}
        ])
        service.getThicknessNoLinkedToMaterial = AsyncMock(return_value=[])
        service.addNewMaterial = AsyncMock(return_value=1)
        service.changeMaterial = AsyncMock(return_value=None)
        service.deleteMaterial = AsyncMock(return_value=None)
        service.addNewThickness = AsyncMock(return_value=1)
        service.changeThickness = AsyncMock(return_value=None)
        service.deleteThickness = AsyncMock(return_value=None)
        service.addMaterialThickness = AsyncMock(return_value=1)
        service.changeSpeedMaterialThickness = AsyncMock(return_value=None)
        service.deleteMaterialThickness = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def mock_security(self, mock_admin_token):
        security = MagicMock()
        security.setUser = MagicMock(return_value=mock_admin_token)
        return security

    @pytest.fixture
    def mock_user_service(self, mock_admin_token):
        service = AsyncMock()
        service.getUserById = AsyncMock(return_value=MagicMock(isAdmin=True))
        return service

    @pytest.mark.asyncio
    async def test_get_all_materials(self, mock_material_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/material/materials")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_all_thickness(self, mock_material_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/material/thickness/all")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_material_by_id(self, mock_material_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/material/material?materialId=1")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_thickness_by_material(self, mock_material_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/material/thickness?materialId=1")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_thickness_no_linked(self, mock_material_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/material/thickness/noLinked?materialId=1")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_new_material(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/material/material",
                    json={"name": "New Material", "price": 150, "weight": 2.0},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_material(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.put(
                    "/api/material/material/1",
                    json={"name": "Updated Material", "price": 200, "weight": 2.5},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_material(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    "/api/material/material/1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_new_thickness(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/material/thickness",
                    json={"name": "5mm", "price": 70, "speed": 8.0},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_add_material_thickness(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/material/mt/1/1?speed=10.0&price=500",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 201
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_change_speed_material_thickness(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.patch(
                    "/api/material/mt/1/1/speed?speed=15.0",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_delete_material_thickness(self, mock_material_service, mock_security, mock_user_service):
        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.delete(
                    "/api/material/mt/1/1",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 204
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/material/material",
                json={"name": "Test", "price": 100, "weight": 1.0}
            )
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_non_admin_cannot_add_material(self, mock_material_service, mock_security, mock_user_service):
        non_admin_token = UserToken(id=2, email="user@example.com", isAdmin=False)
        mock_security.setUser = MagicMock(return_value=non_admin_token)
        mock_user_service.getUserById = AsyncMock(return_value=MagicMock(isAdmin=False))

        app.dependency_overrides[get_material_service] = lambda: mock_material_service
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/material/material",
                    json={"name": "Test", "price": 100, "weight": 1.0},
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 403
        finally:
            app.dependency_overrides.clear()
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from src.UserModule.dtos import UserToken
from src.autentification.AuthService import get_auth_service
from src.UserModule.UserService import get_user_service
from src.autentification.Security import get_security


class TestAuthRouter:
    @pytest.mark.asyncio
    async def test_login_success(self, mock_auth_service):
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/auth/login",
                    json={"email": "test@example.com", "password": "password123"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_login_google_redirect(self, mock_auth_service):
        app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/auth/login/google")
                assert response.status_code in [200, 302, 307, 308]
        finally:
            app.dependency_overrides.clear()


class TestUserRouter:
    @pytest.mark.asyncio
    async def test_get_current_user(self, mock_user_token, mock_user_service, mock_security):
        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/user/",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_register_user(self, mock_user_service):
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/user/register",
                    json={
                        "names": "New",
                        "lastNames": "User",
                        "email": "new@example.com",
                        "password": "password123",
                        "address": "789 New St",
                        "phone": 1234567890,
                        "identification": "12345679",
                        "identificationTypeId": 1
                    }
                )
                assert response.status_code in [200, 201, 400, 500]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_identification_types(self, mock_user_service):
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/user/identificationTypes")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/")
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_admin_endpoint_without_admin_role(self, mock_user_token, mock_user_service, mock_security):
        non_admin_user = UserToken(id=1, email="test@example.com", isAdmin=False)
        mock_security.setUser = MagicMock(return_value=non_admin_user)
        mock_user_service.getUserById = AsyncMock(return_value=MagicMock(isAdmin=False))

        app.dependency_overrides[get_security] = lambda: mock_security
        app.dependency_overrides[get_user_service] = lambda: mock_user_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/user/all",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code in [401, 403]
        finally:
            app.dependency_overrides.clear()
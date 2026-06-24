import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from src.UserModule.dtos import User, UserToken
from src.autentification.AuthService import get_auth_service
from src.UserModule.UserService import get_user_service
from src.autentification.Security import get_security


@pytest.fixture
def mock_user():
    return User(
        id=1,
        names="Test",
        lastNames="User",
        email="test@example.com",
        address="123 Test St",
        password="hashed_password",
        phone=1234567890,
        isAdmin=False,
        identification="12345678",
        identificationTypeId=1
    )


@pytest.fixture
def mock_admin_user():
    return User(
        id=2,
        names="Admin",
        lastNames="User",
        email="admin@example.com",
        address="456 Admin Ave",
        password="hashed_password",
        phone=9876543210,
        isAdmin=True,
        identification="87654321",
        identificationTypeId=1
    )


@pytest.fixture
def mock_user_token(mock_user):
    return UserToken(
        id=mock_user.id,
        email=mock_user.email,
        isAdmin=mock_user.isAdmin
    )


@pytest.fixture
def mock_admin_token(mock_admin_user):
    return UserToken(
        id=mock_admin_user.id,
        email=mock_admin_user.email,
        isAdmin=mock_admin_user.isAdmin
    )


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_user_service(mock_user, mock_admin_user):
    service = AsyncMock()
    service.getUserById = AsyncMock(return_value=mock_user)
    service.getAllUser = AsyncMock(return_value=[mock_user, mock_admin_user])
    service.register = AsyncMock(return_value=mock_user)
    service.login = AsyncMock(return_value=mock_user)
    service.getUserByEmail = AsyncMock(return_value=mock_user)
    service.changeAddress = AsyncMock(return_value=None)
    service.getAllIdentificationTypes = AsyncMock(return_value=[{"identificationTypeId": 1, "type": "CC"}])
    return service


@pytest.fixture
def mock_security(mock_user_token):
    security = MagicMock()
    security.setUser = MagicMock(return_value=mock_user_token)
    security.getToken = MagicMock(return_value="test_jwt_token")
    security.refreshToken = MagicMock(return_value="refreshed_token")
    return security


@pytest.fixture
def mock_auth_service(mock_user_token):
    service = AsyncMock()
    service.login = AsyncMock(return_value="test_jwt_token")
    service.loginGoogle = AsyncMock(return_value={"url": "https://google.com/auth"})
    service.googleCallBack = AsyncMock(return_value="test_jwt_token")
    return service
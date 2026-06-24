import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from src.autentification.AuthService import AuthService
from src.UserModule.dtos import UserToken


class TestAuthService:
    @pytest.fixture
    def mock_security(self):
        security = MagicMock()
        security.getToken = MagicMock(return_value="test_jwt_token")
        security.refreshToken = MagicMock(return_value="refreshed_token")
        return security

    @pytest.fixture
    def mock_user_service(self):
        service = AsyncMock()
        service.login = AsyncMock(return_value=UserToken(id=1, email="test@example.com", isAdmin=False))
        service.getUserByEmail = AsyncMock(return_value=UserToken(id=1, email="test@example.com", isAdmin=False))
        return service

    @pytest.fixture
    def mock_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.fixture
    def auth_service(self, mock_security, mock_user_service):
        with patch("src.autentification.AuthService.OAuth"):
            return AuthService(mock_security, mock_user_service)

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_security, mock_user_service, mock_user_token):
        mock_user_service.login = AsyncMock(return_value=mock_user_token)
        result = await auth_service.login("test@example.com", "password123")
        assert result == "test_jwt_token"
        mock_security.getToken.assert_called_once_with(mock_user_token)

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, mock_user_service):
        from fastapi import HTTPException
        mock_user_service.login = AsyncMock(side_effect=HTTPException(401, "Invalid credentials"))
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login("test@example.com", "wrong_password")
        assert exc_info.value.status_code == 401

    def test_refresh_token(self, auth_service, mock_security):
        result = auth_service.refreshToken("old_token")
        assert result == "refreshed_token"
        mock_security.refreshToken.assert_called_once_with("old_token")

    @pytest.mark.asyncio
    async def test_google_callback_no_userinfo(self, auth_service):
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        mock_oauth = MagicMock()
        mock_oauth.google = MagicMock()
        mock_oauth.google.authorize_access_token = AsyncMock(return_value={})
        auth_service._AuthService__oauth = mock_oauth
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.googleCallBack(mock_request)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_google_callback_no_email(self, auth_service):
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        mock_request = MagicMock()
        mock_oauth = MagicMock()
        mock_oauth.google = MagicMock()
        mock_oauth.google.authorize_access_token = AsyncMock(return_value={"userinfo": {}})
        auth_service._AuthService__oauth = mock_oauth
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.googleCallBack(mock_request)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_google_callback_user_not_found(self, auth_service, mock_user_service):
        from fastapi import HTTPException
        from unittest.mock import MagicMock
        from src.UserModule.dtos import User
        mock_request = MagicMock()
        mock_oauth = MagicMock()
        mock_oauth.google = MagicMock()
        mock_oauth.google.authorize_access_token = AsyncMock(return_value={"userinfo": {"email": "notfound@example.com"}})
        auth_service._AuthService__oauth = mock_oauth
        mock_user = User(
            id=None,
            names="Not",
            lastNames="Found",
            email="notfound@example.com",
            address="",
            password="",
            phone=0,
            isAdmin=False,
            identification="",
            identificationTypeId=""
        )
        mock_user_service.getUserByEmail = AsyncMock(return_value=mock_user)
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.googleCallBack(mock_request)
        assert exc_info.value.status_code == 400
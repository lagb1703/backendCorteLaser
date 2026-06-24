import pytest
from unittest.mock import patch, MagicMock
from src.autentification.Security import Security
from authlib.jose.errors import ExpiredTokenError


class TestSecurity:
    def test_set_user_valid_token(self, mock_user_token):
        with patch("src.autentification.Security.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_jwt_key"
            security = Security(jwt_key="test_jwt_key")
            with patch("src.autentification.JWTWarpper.JWTWarpper.decode") as mock_decode:
                mock_decode.return_value = {
                    "email": "test@example.com",
                    "id": 1,
                    "isAdmin": False
                }
                result = security.setUser("valid_token")
                assert result.id == 1
                assert result.email == "test@example.com"

    def test_set_user_expired_token(self):
        with patch("src.autentification.Security.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_jwt_key"
            security = Security(jwt_key="test_jwt_key")
            with patch("src.autentification.JWTWarpper.JWTWarpper.decode") as mock_decode:
                mock_decode.side_effect = ExpiredTokenError()
                with pytest.raises(ExpiredTokenError):
                    security.setUser("expired_token")

    def test_get_token(self, mock_user_token):
        with patch("src.autentification.Security.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_jwt_key"
            security = Security(jwt_key="test_jwt_key")
            token = security.getToken(mock_user_token)
            assert token is not None


class TestUserToken:
    def test_user_token_creation(self, mock_user_token):
        assert mock_user_token.id == 1
        assert mock_user_token.email == "test@example.com"
        assert mock_user_token.isAdmin is False

    def test_user_token_admin(self, mock_admin_token):
        assert mock_admin_token.id == 2
        assert mock_admin_token.isAdmin is True
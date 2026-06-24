import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.UserModule.UserService import UserService
from src.UserModule.dtos import User, UserToken, IdentificationType
from fastapi import HTTPException
from hashlib import sha256


class TestUserService:
    @pytest.fixture
    def mock_postgres(self):
        return AsyncMock()

    @pytest.fixture
    def mock_email_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cmr_service(self):
        return AsyncMock()

    @pytest.fixture
    def user_service(self, mock_postgres, mock_email_client, mock_cmr_service):
        return UserService(mock_postgres, mock_email_client, mock_cmr_service)

    @pytest.fixture
    def sample_user(self):
        return User(
            id=1,
            names="Test",
            lastNames="User",
            email="test@example.com",
            address="123 Test St",
            password="password123",
            phone=1234567890,
            isAdmin=False,
            identification="12345678",
            identificationTypeId=1
        )

    @pytest.fixture
    def sample_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.mark.asyncio
    async def test_login_success(self, user_service, mock_postgres, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "email": "test@example.com",
            "isAdmin": False
        }])
        result = await user_service.login("test@example.com", "password123")
        assert result.id == 1
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[])
        with pytest.raises(HTTPException) as exc_info:
            await user_service.login("test@example.com", "wrong_password")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_register_success(self, user_service, mock_postgres, mock_email_client, mock_cmr_service, sample_user):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        result = await user_service.register(sample_user)
        assert result is True
        mock_email_client.send.assert_called_once()
        mock_cmr_service.addNewCustomer.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_duplicate_user(self, user_service, mock_postgres, sample_user):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.save = AsyncMock(side_effect=UniqueViolationError())
        with pytest.raises(HTTPException) as exc_info:
            await user_service.register(sample_user)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_get_all_users(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {
                "names": "Test",
                "lastNames": "User",
                "email": "test@example.com",
                "address": "123 Test St",
                "password": "hashed",
                "phone": 1234567890,
                "isAdmin": False,
                "identification": "12345678",
                "identificationTypeId": 1
            }
        ])
        result = await user_service.getAllUser()
        assert len(result) == 1
        assert result[0].email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_success(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{
            "names": "Test",
            "lastNames": "User",
            "email": "test@example.com",
            "address": "123 Test St",
            "password": "hashed",
            "phone": 1234567890,
            "isAdmin": False,
            "identification": "12345678",
            "identificationTypeId": 1
        }])
        result = await user_service.getUserById(1)
        assert result.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_get_user_by_id_not_found(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[])
        with pytest.raises(HTTPException) as exc_info:
            await user_service.getUserById(999)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_user_by_email_success(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "names": "Test",
            "lastNames": "User",
            "email": "test@example.com",
            "address": "123 Test St",
            "password": "hashed",
            "phone": 1234567890,
            "isAdmin": False,
            "identification": "12345678",
            "identificationTypeId": 1
        }])
        result = await user_service.getUserByEmail("test@example.com")
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[])
        with pytest.raises(HTTPException) as exc_info:
            await user_service.getUserByEmail("nonexistent@example.com")
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_change_address(self, user_service, mock_postgres, sample_user_token):
        mock_postgres.update = AsyncMock()
        await user_service.changeAddress("New Address", sample_user_token)
        mock_postgres.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_identification_types(self, user_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"identificationTypeId": 1, "type": "CC"},
            {"identificationTypeId": 2, "type": "CE"}
        ])
        result = await user_service.getAllIdentificationTypes()
        assert len(result) == 2
        assert result[0].type == "CC"
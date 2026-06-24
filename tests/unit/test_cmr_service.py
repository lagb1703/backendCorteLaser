import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.CmrModule.CmrService import CmrService
from src.CmrModule.CmrApi import Bitrix24
from src.UserModule.dtos import User


class TestCmrService:
    @pytest.fixture
    def mock_cmr_api(self):
        return AsyncMock()

    @pytest.fixture
    def cmr_service(self, mock_cmr_api):
        return CmrService(mock_cmr_api)

    @pytest.fixture
    def sample_user(self):
        return User(
            id=1,
            names="Test",
            lastNames="User",
            email="test@example.com",
            address="123 Test St",
            password="hashed",
            phone=1234567890,
            isAdmin=False,
            identification="12345678",
            identificationTypeId=1
        )

    @pytest.mark.asyncio
    async def test_add_new_customer_success(self, cmr_service, mock_cmr_api, sample_user):
        mock_cmr_api.searchCustomerByDocument = AsyncMock(return_value=None)
        mock_cmr_api.createNewCustomer = AsyncMock(return_value="customer_id_123")
        result = await cmr_service.addNewCustomer(sample_user)
        assert result == "customer_id_123"

    @pytest.mark.asyncio
    async def test_add_new_customer_already_exists(self, cmr_service, mock_cmr_api, sample_user):
        mock_cmr_api.searchCustomerByDocument = AsyncMock(return_value=sample_user)
        result = await cmr_service.addNewCustomer(sample_user)
        assert result == ""

    @pytest.mark.asyncio
    async def test_update_customer(self, cmr_service, mock_cmr_api, sample_user):
        mock_cmr_api.updateCustomer = AsyncMock()
        await cmr_service.updateCustomer(sample_user, "12345678")
        mock_cmr_api.updateCustomer.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_task(self, cmr_service, mock_cmr_api):
        mock_cmr_api.addTask = AsyncMock()
        payments = {
            "user": [{"identification": "12345678", "address": "123 Test St"}],
            "items": [{"name": "file.dxf", "fileId": 1, "materialName": "Acrylic", "thicknessName": "3mm", "amount": 1}],
            "amount_in_cents": 10000,
            "reference": "ref_123"
        }
        await cmr_service.addTask(payments)
        mock_cmr_api.addTask.assert_called_once()


class TestBitrix24:
    @pytest.fixture
    def bitrix24(self):
        return Bitrix24(base_url="https://test.bitrix24.com/rest/1/", custom_id_field="UF_CRM_CUSTOM_ID")

    @pytest.fixture
    def sample_user(self):
        return User(
            id=1,
            names="Test",
            lastNames="User",
            email="test@example.com",
            address="123 Test St",
            password="hashed",
            phone=1234567890,
            isAdmin=False,
            identification="12345678",
            identificationTypeId=1
        )

    @pytest.mark.asyncio
    async def test_create_new_customer_success(self, bitrix24, sample_user):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"result": "123"})
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await bitrix24.createNewCustomer(sample_user)
            assert result == "123"

    @pytest.mark.asyncio
    async def test_create_new_customer_failure(self, bitrix24, sample_user):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await bitrix24.createNewCustomer(sample_user)
            assert result == ""

    @pytest.mark.asyncio
    async def test_search_customer_by_document_found(self, bitrix24):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={
                "result": [{
                    "ID": "1",
                    "NAME": "Test",
                    "LAST_NAME": "User",
                    "PHONE": [{"VALUE": 1234567890}],
                    "EMAIL": [{"VALUE": "test@example.com"}]
                }]
            })
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await bitrix24.searchCustomerByDocument("12345678")
            assert result is not None
            assert result.identification == "12345678"

    @pytest.mark.asyncio
    async def test_search_customer_by_document_not_found(self, bitrix24):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json = MagicMock(return_value={"result": []})
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            result = await bitrix24.searchCustomerByDocument("99999999")
            assert result is None

    @pytest.mark.asyncio
    async def test_update_customer(self, bitrix24, sample_user):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            await bitrix24.updateCustomer(sample_user, "12345678")

    @pytest.mark.asyncio
    async def test_add_task(self, bitrix24):
        with patch("src.CmrModule.CmrApi.httpx.AsyncClient") as mock_client:
            mock_search_response = MagicMock()
            mock_search_response.status_code = 200
            mock_search_response.json = MagicMock(return_value={
                "result": [{
                    "ID": "1",
                    "NAME": "Test",
                    "LAST_NAME": "User",
                    "PHONE": [{"VALUE": 1234567890}],
                    "EMAIL": [{"VALUE": "test@example.com"}]
                }]
            })
            mock_task_response = MagicMock()
            mock_task_response.status_code = 200
            mock_task_response.json = MagicMock(return_value={"result": "deal_123"})

            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=[mock_search_response, mock_task_response])
            mock_client.return_value.__aenter__.return_value = mock_client_instance

            payments = {
                "user": [{"identification": "12345678", "address": "123 Test St"}],
                "items": [{"name": "file.dxf", "fileId": 1, "materialName": "Acrylic", "thicknessName": "3mm", "amount": 1}],
                "amount_in_cents": 10000,
                "reference": "ref_123",
                "billing": {"name": "Test User", "email": "test@example.com", "identification": "12345678"},
                "address": "123 Test St"
            }
            await bitrix24.addTask(payments)
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.PaymentModule.paymentService import PaymentService
from src.PaymentModule.dto import PaymentType, PaymentMethodWompi, ReferenceType, AcceptanceTokens, AcceptanceTokenType, DbPaymentType, BilingType, WompiTokenizerType
from src.UserModule.dtos import UserToken
from fastapi import HTTPException


class TestPaymentService:
    @pytest.fixture
    def mock_postgres(self):
        return AsyncMock()

    @pytest.fixture
    def mock_file_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_wompi_wrapper(self):
        return AsyncMock()

    @pytest.fixture
    def mock_email_client(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cmr_service(self):
        return AsyncMock()

    @pytest.fixture
    def payment_service(self, mock_postgres, mock_file_service, mock_wompi_wrapper, mock_email_client, mock_cmr_service):
        return PaymentService(
            postgres=mock_postgres,
            file_service=mock_file_service,
            wompi_wrapper=mock_wompi_wrapper,
            email_client=mock_email_client,
            cmr_service=mock_cmr_service,
            business_email="business@example.com"
        )

    @pytest.fixture
    def sample_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.fixture
    def sample_payment(self):
        return PaymentType(
            acceptance_token="test_acceptance_token",
            accept_personal_auth="test_personal_auth",
            payment_method=PaymentMethodWompi(type="CARD", token="test_token"),
            card=WompiTokenizerType(
                number="4242424242424242",
                cvc="789",
                exp_month="12",
                exp_year="29",
                card_holder="Test User"
            ),
            items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
            amount_in_cents=10000,
            billing=BilingType(
                name="Test User",
                email="test@example.com",
                identification="12345678"
            )
        )

    @pytest.mark.asyncio
    async def test_get_payment_methods(self, payment_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"id": 1, "name": "Credit Card"},
            {"id": 2, "name": "PSE"}
        ])
        result = await payment_service.getPaymentMethods()
        assert len(result) == 2
        assert result[0].name == "Credit Card"

    @pytest.mark.asyncio
    async def test_get_acceptance_tokens(self, payment_service, mock_wompi_wrapper):
        mock_wompi_wrapper.getAcceptanceTokens = AsyncMock(return_value=AcceptanceTokens(
            presigned_acceptance=AcceptanceTokenType(acceptance_token="token1", permalink="link1", type="type1"),
            presigned_personal_data_auth=AcceptanceTokenType(acceptance_token="token2", permalink="link2", type="type2")
        ))
        result = await payment_service.getAcceptanceTokens()
        assert result.presigned_acceptance.acceptance_token == "token1"

    @pytest.mark.asyncio
    async def test_verify_payment(self, payment_service, mock_wompi_wrapper):
        mock_wompi_wrapper.verifyPayment = AsyncMock(return_value={"status": "APPROVED"})
        result = await payment_service.verifyPayment("payment_123")
        assert result == "APPROVED"

    @pytest.mark.asyncio
    async def test_get_payments(self, payment_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"id": 1, "p_id": "pay_123", "status": "APPROVED", "reference": "ref_123", "created_at": "2024-01-01", "paymentMethod": "CARD"}
        ])
        result = await payment_service.getPayments(1)
        assert len(result) == 1
        assert result[0].status == "APPROVED"

    @pytest.mark.asyncio
    async def test_make_payment(self, payment_service, mock_file_service, mock_wompi_wrapper, mock_postgres, sample_payment, sample_user_token):
        mock_file_service.getPrice = AsyncMock(return_value=MagicMock(price=100.0))
        mock_wompi_wrapper.makePayment = AsyncMock(return_value=MagicMock(id="pay_123"))
        mock_wompi_wrapper.verifyPayment = AsyncMock(return_value={"status": "APPROVED"})
        mock_postgres.save = AsyncMock(return_value={"p_id": "db_pay_123"})

        result = await payment_service.makePayment(sample_payment, sample_user_token)
        assert result == "pay_123"

    @pytest.mark.asyncio
    async def test_until_not_get_pending_approved(self, payment_service, mock_wompi_wrapper):
        mock_wompi_wrapper.verifyPayment = AsyncMock(return_value={"status": "APPROVED"})
        result = await payment_service.untilNotGetPending("pay_123")
        assert result == "APPROVED"

    @pytest.mark.asyncio
    async def test_get_payment_info_by_reference(self, payment_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{
            "FU_PA_PAYMENTPKG_GETPAYMENTINFOBYREFERENCE": '{"items": [], "user": []}'
        }])
        result = await payment_service._PaymentService__getPaymentInfoByReference("ref_123")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_get_payment_info_by_reference_not_found(self, payment_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[])
        result = await payment_service._PaymentService__getPaymentInfoByReference("nonexistent")
        assert result == {}

    @pytest.mark.asyncio
    async def test_webhook_approved(self, payment_service, mock_postgres, mock_email_client, mock_cmr_service):
        from starlette.requests import Request
        from starlette.responses import Response
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=json.dumps({
            "data": {
                "transaction": {
                    "status": "APPROVED",
                    "reference": "ref_123",
                    "customer_email": "customer@example.com",
                    "amount_in_cents": 10000
                }
            }
        }).encode())

        mock_response = MagicMock(spec=Response)
        mock_postgres.query = AsyncMock(return_value=[{
            "FU_PA_PAYMENTPKG_GETPAYMENTINFOBYREFERENCE": json.dumps({
                "items": [{"name": "file.dxf", "fileId": 1, "materialName": "Acrylic", "thicknessName": "3mm", "amount": 1}],
                "user": [{"email": "customer@example.com"}]
            })
        }])

        await payment_service.webhook(mock_request, mock_response)
        mock_email_client.send.assert_called_once()
        mock_cmr_service.addTask.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_rejected(self, payment_service, mock_email_client):
        from starlette.requests import Request
        from starlette.responses import Response
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=json.dumps({
            "data": {
                "transaction": {
                    "status": "REJECTED",
                    "reference": "ref_123",
                    "customer_email": "customer@example.com",
                    "amount_in_cents": 10000
                }
            }
        }).encode())

        mock_response = MagicMock(spec=Response)
        await payment_service.webhook(mock_request, mock_response)
        mock_email_client.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_webhook_no_data(self, payment_service):
        from starlette.requests import Request
        from starlette.responses import Response
        import json

        mock_request = MagicMock(spec=Request)
        mock_request.body = AsyncMock(return_value=json.dumps({"data": None}).encode())
        mock_response = MagicMock(spec=Response)

        await payment_service.webhook(mock_request, mock_response)

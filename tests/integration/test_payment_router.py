import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from main import app
from src.UserModule.dtos import UserToken
from src.PaymentModule.paymentService import get_payment_service
from src.autentification.Security import get_security
from src.PaymentModule.dto import AcceptanceTokens, AcceptanceTokenType


class TestPaymentRouter:
    @pytest.fixture
    def mock_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.fixture
    def mock_payment_service(self):
        service = AsyncMock()
        service.getAcceptanceTokens = AsyncMock(return_value=AcceptanceTokens(
            presigned_acceptance=AcceptanceTokenType(acceptance_token="token1", permalink="link1", type="type1"),
            presigned_personal_data_auth=AcceptanceTokenType(acceptance_token="token2", permalink="link2", type="type2")
        ))
        service.getPaymentMethods = AsyncMock(return_value=[{"id": 1, "name": "Credit Card"}])
        service.makePayment = AsyncMock(return_value="pay_123")
        service.getPayments = AsyncMock(return_value=[])
        service.verifyPayment = AsyncMock(return_value="APPROVED")
        service.untilNotGetPending = AsyncMock(return_value="APPROVED")
        service.webhook = AsyncMock(return_value=None)
        return service

    @pytest.fixture
    def mock_security(self, mock_user_token):
        security = MagicMock()
        security.setUser = MagicMock(return_value=mock_user_token)
        return security

    @pytest.mark.asyncio
    async def test_get_acceptance_tokens(self, mock_payment_service):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/payment/acceptancesTokens")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_payment_methods(self, mock_payment_service):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/payment/paymentsMethods")
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_payments(self, mock_payment_service, mock_security):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/payment/",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_verify_payment(self, mock_payment_service, mock_security):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/payment/verify?id=pay_123",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_until_not_get_pending(self, mock_payment_service, mock_security):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get(
                    "/api/payment/verify/APROVED?id=pay_123",
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_webhook(self, mock_payment_service):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/payment/webhook",
                    json={"data": {"transaction": {"status": "APPROVED"}}}
                )
                assert response.status_code in [200, 201]
        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_protected_endpoint_without_auth(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/payment/")
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_make_payment(self, mock_payment_service, mock_security):
        app.dependency_overrides[get_payment_service] = lambda: mock_payment_service
        app.dependency_overrides[get_security] = lambda: mock_security
        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post(
                    "/api/payment/",
                    json={
                        "acceptance_token": "test_token",
                        "accept_personal_auth": "test_auth",
                        "payment_method": {"type": "CARD", "token": "card_token"},
                        "card": {
                            "number": "4242424242424242",
                            "cvc": "789",
                            "exp_month": "12",
                            "exp_year": "29",
                            "card_holder": "Test User"
                        },
                        "items": [{"materialId": "1", "thicknessId": "1", "fileId": "1", "amount": 1}],
                        "billing": {
                            "name": "Test User",
                            "email": "test@example.com",
                            "identification": "12345678"
                        }
                    },
                    headers={"Authorization": "Bearer test_token"}
                )
                assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()
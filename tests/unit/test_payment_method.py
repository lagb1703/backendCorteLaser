import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.PaymentModule.paymentMethod import CardMethod, NequiMethod
from src.PaymentModule.dto import PaymentType, PaymentMethodWompi, WompiTokenizerType, ReferenceType, BilingType
from fastapi import HTTPException


class TestCardMethod:
    @pytest.fixture
    def card_method(self):
        with patch("src.PaymentModule.paymentMethod.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_value"
            return CardMethod()

    @pytest.mark.asyncio
    async def test_tokenizer_success(self, card_method):
        with patch("src.PaymentModule.paymentMethod.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"id": "token_123"}}
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await card_method.tokenizer({"number": "4242424242424242"})
            assert result == "token_123"

    @pytest.mark.asyncio
    async def test_tokenizer_timeout(self, card_method):
        with patch("src.PaymentModule.paymentMethod.httpx.AsyncClient") as mock_client:
            import httpx
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await card_method.tokenizer({"number": "4242424242424242"})
            assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_generate_payment_no_card(self, card_method):
        # The validation happens at DTO level, so we test that the DTO raises
        with pytest.raises(HTTPException) as exc_info:
            PaymentType(
                acceptance_token="test_token",
                accept_personal_auth="test_auth",
                payment_method=PaymentMethodWompi(type="CARD", token="test_token"),
                card=None,
                items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
                amount_in_cents=10000,
                billing=BilingType(
                    name="Test User",
                    email="test@example.com",
                    identification="12345678"
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_payment_success(self, card_method):
        card = WompiTokenizerType(
            number="4242424242424242",
            cvc="123",
            exp_month="12",
            exp_year="25",
            card_holder="Test User"
        )
        payment = PaymentType(
            acceptance_token="test_token",
            accept_personal_auth="test_auth",
            payment_method=PaymentMethodWompi(type="CARD", token="test_token", installments=1),
            card=card,
            items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
            amount_in_cents=10000,
            reference="ref_123",
            billing=BilingType(
                name="Test User",
                email="test@example.com",
                identification="12345678"
            )
        )
        
        with patch.object(card_method, "tokenizer", new_callable=AsyncMock) as mock_tokenizer:
            mock_tokenizer.return_value = "token_123"
            with patch.object(card_method, "_getPaymentSourceId", new_callable=AsyncMock) as mock_source:
                mock_source.return_value = 456
                with patch.object(card_method, "_send", new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = MagicMock()
                    
                    result = await card_method.generatePayment(payment, "test@example.com")
                    assert result is not None


class TestNequiMethod:
    @pytest.fixture
    def nequi_method(self):
        with patch("src.PaymentModule.paymentMethod.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_value"
            return NequiMethod()

    @pytest.mark.asyncio
    async def test_tokenizer_success(self, nequi_method):
        with patch("src.PaymentModule.paymentMethod.httpx.AsyncClient") as mock_client:
            mock_response_post = MagicMock()
            mock_response_post.json.return_value = {"data": {"id": "nequi_123"}}
            mock_response_post.raise_for_status = MagicMock()
            
            mock_response_get = MagicMock()
            mock_response_get.json.return_value = {"data": {"status": "APPROVED"}}
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response_post)
            mock_client_instance.get = AsyncMock(return_value=mock_response_get)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await nequi_method.tokenizer({"phone_number": "3001234567"})
            assert result == "nequi_123"

    @pytest.mark.asyncio
    async def test_tokenizer_not_approved(self, nequi_method):
        with patch("src.PaymentModule.paymentMethod.httpx.AsyncClient") as mock_client:
            mock_response_post = MagicMock()
            mock_response_post.json.return_value = {"data": {"id": "nequi_123"}}
            mock_response_post.raise_for_status = MagicMock()
            
            mock_response_get = MagicMock()
            mock_response_get.json.return_value = {"data": {"status": "PENDING"}}
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response_post)
            mock_client_instance.get = AsyncMock(return_value=mock_response_get)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(Exception):
                await nequi_method.tokenizer({"phone_number": "3001234567"})

    @pytest.mark.asyncio
    async def test_generate_payment_no_phone(self, nequi_method):
        # The validation happens at DTO level, so we test that the DTO raises
        with pytest.raises(HTTPException) as exc_info:
            PaymentType(
                acceptance_token="test_token",
                accept_personal_auth="test_auth",
                payment_method=PaymentMethodWompi(type="NEQUI"),
                card=None,
                items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
                amount_in_cents=10000,
                billing=BilingType(
                    name="Test User",
                    email="test@example.com",
                    identification="12345678"
                )
            )
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_generate_payment_success(self, nequi_method):
        payment = PaymentType(
            acceptance_token="test_token",
            accept_personal_auth="test_auth",
            payment_method=PaymentMethodWompi(type="NEQUI", phone_number="3001234567"),
            card=None,
            items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
            amount_in_cents=10000,
            reference="ref_123",
            billing=BilingType(
                name="Test User",
                email="test@example.com",
                identification="12345678"
            )
        )
        
        with patch.object(nequi_method, "tokenizer", new_callable=AsyncMock) as mock_tokenizer:
            mock_tokenizer.return_value = "nequi_token_123"
            with patch.object(nequi_method, "_getPaymentSourceId", new_callable=AsyncMock) as mock_source:
                mock_source.return_value = 789
                with patch.object(nequi_method, "_send", new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = MagicMock()
                    
                    result = await nequi_method.generatePayment(payment, "test@example.com")
                    assert result is not None

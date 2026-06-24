import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.PaymentModule.wompiWrapper import WompiWrapper
from src.PaymentModule.dto import PaymentType, PaymentMethodWompi, ReferenceType, BilingType, WompiTokenizerType
from fastapi import HTTPException


class TestWompiWrapper:
    @pytest.fixture
    def wompi_wrapper(self):
        with patch("src.PaymentModule.wompiWrapper.Environment.getInstance") as mock_env:
            mock_env.return_value.get.return_value = "test_value"
            with patch("src.PaymentModule.wompiWrapper.NequiMethod"):
                with patch("src.PaymentModule.wompiWrapper.CardMethod"):
                    return WompiWrapper()

    @pytest.mark.asyncio
    async def test_get_acceptance_tokens_success(self, wompi_wrapper):
        with patch("src.PaymentModule.wompiWrapper.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {
                    "presigned_acceptance": {
                        "acceptance_token": "token1",
                        "permalink": "link1",
                        "type": "type1"
                    },
                    "presigned_personal_data_auth": {
                        "acceptance_token": "token2",
                        "permalink": "link2",
                        "type": "type2"
                    }
                }
            }
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await wompi_wrapper.getAcceptanceTokens()
            assert result.presigned_acceptance.acceptance_token == "token1"

    @pytest.mark.asyncio
    async def test_get_acceptance_tokens_timeout(self, wompi_wrapper):
        with patch("src.PaymentModule.wompiWrapper.httpx.AsyncClient") as mock_client:
            import httpx
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await wompi_wrapper.getAcceptanceTokens()
            assert exc_info.value.status_code == 504

    @pytest.mark.asyncio
    async def test_get_acceptance_tokens_invalid_response(self, wompi_wrapper):
        with patch("src.PaymentModule.wompiWrapper.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"invalid": "data"}}
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await wompi_wrapper.getAcceptanceTokens()
            assert exc_info.value.status_code == 502

    @pytest.mark.asyncio
    async def test_make_payment_card(self, wompi_wrapper):
        payment = PaymentType(
            acceptance_token="test_token",
            accept_personal_auth="test_auth",
            payment_method=PaymentMethodWompi(type="CARD", token="test_token"),
            card=WompiTokenizerType(
                number="4242424242424242",
                cvc="123",
                exp_month="12",
                exp_year="25",
                card_holder="Test User"
            ),
            items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
            amount_in_cents=10000,
            reference="ref_123",
            billing=BilingType(
                name="Test User",
                email="test@example.com",
                identification="12345678"
            )
        )
        
        mock_card_method = AsyncMock()
        mock_card_method.generatePayment = AsyncMock(return_value=MagicMock())
        wompi_wrapper._WompiWrapper__paymentMethods["CARD"] = mock_card_method
        
        result = await wompi_wrapper.makePayment(payment, "test@example.com")
        assert result is not None
        mock_card_method.generatePayment.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_payment_unknown_method(self, wompi_wrapper):
        # The DTO validates the type, so we test with a valid type but remove it from the dict
        payment = PaymentType(
            acceptance_token="test_token",
            accept_personal_auth="test_auth",
            payment_method=PaymentMethodWompi(type="PSE", token="test_token"),
            card=None,
            items=[ReferenceType(materialId="1", thicknessId="1", fileId="1", amount=1)],
            amount_in_cents=10000,
            billing=BilingType(
                name="Test User",
                email="test@example.com",
                identification="12345678"
            )
        )
        
        # Remove PSE from the payment methods to simulate unknown method
        if "PSE" in wompi_wrapper._WompiWrapper__paymentMethods:
            del wompi_wrapper._WompiWrapper__paymentMethods["PSE"]
        
        with pytest.raises(Exception):
            await wompi_wrapper.makePayment(payment, "test@example.com")

    @pytest.mark.asyncio
    async def test_verify_payment_success(self, wompi_wrapper):
        with patch("src.PaymentModule.wompiWrapper.httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {"status": "APPROVED"}}
            mock_response.raise_for_status = MagicMock()
            
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            result = await wompi_wrapper.verifyPayment("payment_123")
            assert result["status"] == "APPROVED"

    @pytest.mark.asyncio
    async def test_verify_payment_timeout(self, wompi_wrapper):
        with patch("src.PaymentModule.wompiWrapper.httpx.AsyncClient") as mock_client:
            import httpx
            mock_client_instance = AsyncMock()
            mock_client_instance.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            
            with pytest.raises(HTTPException) as exc_info:
                await wompi_wrapper.verifyPayment("payment_123")
            assert exc_info.value.status_code == 504

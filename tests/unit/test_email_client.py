import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.utils.EmailClient import EmailClient
from email.message import EmailMessage


class TestEmailClient:
    @pytest.fixture
    def email_client(self):
        return EmailClient(
            from_email="test@example.com",
            host_name="smtp.example.com",
            port=587,
            secure=True,
            password="test_password"
        )

    @pytest.mark.asyncio
    async def test_send_success(self, email_client):
        message = EmailMessage()
        message["To"] = "recipient@example.com"
        message["Subject"] = "Test Subject"
        message.set_content("Test content")
        
        with patch("src.utils.EmailClient.aiosmtplib.send") as mock_send:
            mock_send.return_value = None
            await email_client.send(message)
            mock_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_sets_from_email(self, email_client):
        message = EmailMessage()
        message["To"] = "recipient@example.com"
        message["Subject"] = "Test Subject"
        message.set_content("Test content")
        
        with patch("src.utils.EmailClient.aiosmtplib.send") as mock_send:
            mock_send.return_value = None
            await email_client.send(message)
            assert message["From"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_send_with_correct_parameters(self, email_client):
        message = EmailMessage()
        message["To"] = "recipient@example.com"
        message["Subject"] = "Test Subject"
        message.set_content("Test content")
        
        with patch("src.utils.EmailClient.aiosmtplib.send") as mock_send:
            mock_send.return_value = None
            await email_client.send(message)
            
            call_args = mock_send.call_args
            assert call_args[1]["hostname"] == "smtp.example.com"
            assert call_args[1]["port"] == 587
            assert call_args[1]["username"] == "test@example.com"
            assert call_args[1]["password"] == "test_password"

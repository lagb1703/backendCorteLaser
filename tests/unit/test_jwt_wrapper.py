import pytest
from datetime import timedelta
from src.autentification.JWTWarpper import JWTWarpper
from authlib.jose.errors import ExpiredTokenError


class TestJWTWarpper:
    @pytest.fixture
    def jwt_wrapper(self):
        return JWTWarpper(key="test_secret_key", exp=timedelta(hours=1))

    @pytest.fixture
    def sample_payload(self):
        return {
            "email": "test@example.com",
            "id": 1,
            "isAdmin": False
        }

    def test_encode_with_default_key(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload)
        assert token is not None
        assert isinstance(token, bytes)
        assert len(token) > 0

    def test_encode_with_custom_key(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload, key="custom_key")
        assert token is not None

    def test_encode_without_key_raises(self):
        wrapper = JWTWarpper()
        with pytest.raises(Exception):
            wrapper.encode({"test": "data"})

    def test_encode_with_custom_expiration(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload, exp=timedelta(minutes=30))
        assert token is not None

    def test_decode_valid_token(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload)
        decoded = jwt_wrapper.decode(token)
        assert decoded["email"] == "test@example.com"
        assert decoded["id"] == 1
        assert decoded["isAdmin"] is False

    def test_decode_with_custom_key(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload, key="custom_key")
        decoded = jwt_wrapper.decode(token, key="custom_key")
        assert decoded["email"] == "test@example.com"

    def test_decode_without_key_raises(self, jwt_wrapper, sample_payload):
        wrapper = JWTWarpper()
        token = jwt_wrapper.encode(sample_payload)
        with pytest.raises(ValueError):
            wrapper.decode(token)

    def test_decode_expired_token(self, jwt_wrapper, sample_payload):
        wrapper = JWTWarpper(key="test_secret_key", exp=timedelta(seconds=-1))
        token = wrapper.encode(sample_payload)
        with pytest.raises(ExpiredTokenError):
            wrapper.decode(token)

    def test_refresh_token(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload)
        refreshed = jwt_wrapper.refresh(token)
        assert refreshed is not None
        decoded = jwt_wrapper.decode(refreshed)
        assert decoded["email"] == "test@example.com"

    def test_refresh_with_custom_key(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload, key="custom_key")
        refreshed = jwt_wrapper.refresh(token, key="custom_key")
        assert refreshed is not None

    def test_refresh_without_key_raises(self, jwt_wrapper, sample_payload):
        wrapper = JWTWarpper()
        token = jwt_wrapper.encode(sample_payload)
        with pytest.raises(ValueError):
            wrapper.refresh(token)

    def test_encode_decode_roundtrip(self, jwt_wrapper, sample_payload):
        token = jwt_wrapper.encode(sample_payload)
        decoded = jwt_wrapper.decode(token)
        for key, value in sample_payload.items():
            assert decoded[key] == value
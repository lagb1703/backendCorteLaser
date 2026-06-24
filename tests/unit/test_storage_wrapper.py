import pytest
from unittest.mock import MagicMock, patch
from src.FileModule.storageWrapper import StorageWrapper


class TestStorageWrapper:
    @pytest.fixture
    def mock_storage_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_bucket(self):
        return MagicMock()

    @pytest.fixture
    def storage_wrapper(self, mock_storage_client, mock_bucket):
        with patch("src.FileModule.storageWrapper.storage.Client.from_service_account_json") as mock_from_json:
            mock_from_json.return_value = mock_storage_client
            mock_storage_client.bucket.return_value = mock_bucket
            wrapper = StorageWrapper(credentials_url="fake_creds.json", bucket_name="test-bucket")
            return wrapper

    def test_upload_without_content_type(self, storage_wrapper, mock_bucket):
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        
        storage_wrapper.upload(b"test data", "test.txt")
        
        mock_bucket.blob.assert_called_once_with("test.txt")
        mock_blob.upload_from_string.assert_called_once_with(b"test data")

    def test_upload_with_content_type(self, storage_wrapper, mock_bucket):
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        
        storage_wrapper.upload(b"test data", "test.txt", "text/plain")
        
        mock_bucket.blob.assert_called_once_with("test.txt")
        mock_blob.upload_from_string.assert_called_once_with(b"test data", content_type="text/plain")

    def test_download(self, storage_wrapper, mock_bucket):
        mock_blob = MagicMock()
        mock_blob.download_as_bytes.return_value = b"file content"
        mock_bucket.blob.return_value = mock_blob
        
        result = storage_wrapper.download("test.txt")
        
        assert result == b"file content"
        mock_bucket.blob.assert_called_once_with("test.txt")
        mock_blob.download_as_bytes.assert_called_once()

    def test_delete(self, storage_wrapper, mock_bucket):
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        
        storage_wrapper.delete("test.txt")
        
        mock_bucket.blob.assert_called_once_with("test.txt")
        mock_blob.delete.assert_called_once()

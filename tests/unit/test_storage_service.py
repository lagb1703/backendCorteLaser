import pytest
from unittest.mock import MagicMock
from src.FileModule.storageService import StorageService
from fastapi import HTTPException


class TestStorageService:
    @pytest.fixture
    def mock_storage_wrapper(self):
        return MagicMock()

    @pytest.fixture
    def storage_service(self, mock_storage_wrapper):
        return StorageService(storage=mock_storage_wrapper)

    def test_upload_without_content_type(self, storage_service, mock_storage_wrapper):
        storage_service.upload(b"test data", "test.txt", "folder")
        mock_storage_wrapper.upload.assert_called_once_with(b"test data", "folder/test.txt", content_type=None)

    def test_upload_with_content_type(self, storage_service, mock_storage_wrapper):
        storage_service.upload(b"test data", "test.txt", "folder", "text/plain")
        mock_storage_wrapper.upload.assert_called_once_with(b"test data", "folder/test.txt", content_type="text/plain")

    def test_download_success(self, storage_service, mock_storage_wrapper):
        mock_storage_wrapper.download.return_value = b"file content"
        result = storage_service.download("test.txt", "folder")
        assert result == b"file content"
        mock_storage_wrapper.download.assert_called_once_with("folder/test.txt")

    def test_download_not_found(self, storage_service, mock_storage_wrapper):
        mock_storage_wrapper.download.side_effect = Exception("Not found")
        with pytest.raises(HTTPException) as exc_info:
            storage_service.download("test.txt", "folder")
        assert exc_info.value.status_code == 404

    def test_delete(self, storage_service, mock_storage_wrapper):
        storage_service.delete("test.txt", "folder")
        mock_storage_wrapper.delete.assert_called_once_with("folder/test.txt")

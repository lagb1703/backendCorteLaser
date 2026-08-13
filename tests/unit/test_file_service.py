import pytest
from unittest.mock import AsyncMock, MagicMock
from src.FileModule.fileService import FileService
from src.FileModule.storageService import StorageService
from src.FileModule.dtos import FileDb, PriceResponse
from src.UserModule.dtos import UserToken
from fastapi import HTTPException, UploadFile
from io import BytesIO


class TestFileService:
    @pytest.fixture
    def mock_storage(self):
        return MagicMock()

    @pytest.fixture
    def mock_creator(self):
        return MagicMock()

    @pytest.fixture
    def mock_postgres(self):
        return AsyncMock()

    @pytest.fixture
    def mock_material_service(self):
        return AsyncMock()

    @pytest.fixture
    def mock_cost_service(self):
        return AsyncMock()

    @pytest.fixture
    def file_service(self, mock_storage, mock_creator, mock_postgres, mock_material_service, mock_cost_service):
        return FileService(
            storage=mock_storage,
            creator=mock_creator,
            postgres=mock_postgres,
            material_service=mock_material_service,
            cost_service=mock_cost_service
        )

    @pytest.fixture
    def sample_user_token(self):
        return UserToken(id=1, email="test@example.com", isAdmin=False)

    @pytest.fixture
    def sample_file_db(self):
        return FileDb(
            id=1,
            name="test.dxf",
            date="2024-01-01",
            md5="abc123",
            bucket="original",
            userId=1
        )

    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_service, mock_postgres, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        result = await file_service.getFileInfo("1", sample_user_token)
        assert result.id == 1
        assert result.name == "test.dxf"

    @pytest.mark.asyncio
    async def test_get_file_info_not_found(self, file_service, mock_postgres, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[])
        with pytest.raises(HTTPException) as exc_info:
            await file_service.getFileInfo("999", sample_user_token)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_save_file_success(self, file_service, mock_postgres, mock_storage, mock_creator, sample_user_token):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        mock_creator.createGeometry = MagicMock()
        mock_creator.createGeometry.return_value.save = MagicMock(return_value=b"wkb_data")
        mock_storage.upload = MagicMock()

        file = MagicMock(spec=UploadFile)
        file.filename = "test.dxf"
        file.read = AsyncMock(return_value=b"file_content")

        result = await file_service.saveFile(file, sample_user_token)
        assert result == 1
        assert mock_storage.upload.call_count == 2

    @pytest.mark.asyncio
    async def test_save_file_no_filename(self, file_service, sample_user_token):
        file = MagicMock(spec=UploadFile)
        file.filename = None
        with pytest.raises(HTTPException) as exc_info:
            await file_service.saveFile(file, sample_user_token)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_save_file_duplicate(self, file_service, mock_postgres, mock_creator, sample_user_token):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.save = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        mock_creator.createGeometry = MagicMock()
        mock_creator.createGeometry.return_value.save = MagicMock(return_value=b"wkb_data")

        file = MagicMock(spec=UploadFile)
        file.filename = "test.dxf"
        file.read = AsyncMock(return_value=b"file_content")

        with pytest.raises(HTTPException) as exc_info:
            await file_service.saveFile(file, sample_user_token)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_get_file(self, file_service, mock_postgres, mock_storage, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        mock_storage.download = MagicMock(return_value=b"file_content")

        result = await file_service.getFile("1", sample_user_token)
        assert result is not None

    @pytest.mark.asyncio
    async def test_delete_file(self, file_service, mock_postgres, mock_storage, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        mock_postgres.delete = AsyncMock()
        mock_storage.delete = MagicMock()

        await file_service.deleteFile("1", sample_user_token)
        mock_postgres.delete.assert_called_once()
        assert mock_storage.delete.call_count == 2

    @pytest.mark.asyncio
    async def test_get_image(self, file_service, mock_postgres, mock_storage, mock_creator, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        mock_storage.download = MagicMock(return_value=b"wkb_data")
        mock_creator.createGeometry = MagicMock()
        mock_creator.createGeometry.return_value.export = MagicMock(return_value=b"image_data")

        result = await file_service.getImage("1", sample_user_token)
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_glb_rigged(self, file_service, mock_postgres, mock_storage, mock_creator, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        mock_storage.download = MagicMock(return_value=b"wkb_data")
        mock_creator.createGeometry = MagicMock()
        mock_creator.createGeometry.return_value.export = MagicMock(return_value=b"glb_data")

        result = await file_service.getGlbRigged("1", sample_user_token)

        assert result is not None
        mock_creator.createGeometry.return_value.export.assert_called_once_with(
            "glb-rigged"
        )

    @pytest.mark.asyncio
    async def test_get_all_user_info_files(self, file_service, mock_postgres, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[
            {"id": 1, "name": "test1.dxf", "date": "2024-01-01", "md5": "abc123", "bucket": "original", "userId": 1},
            {"id": 2, "name": "test2.dxf", "date": "2024-01-02", "md5": "def456", "bucket": "original", "userId": 1}
        ])
        result = await file_service.getAllUserInfoFiles(sample_user_token)
        assert len(result) == 2
        assert result[0].name == "test1.dxf"

    @pytest.mark.asyncio
    async def test_get_price(self, file_service, mock_postgres, mock_storage, mock_creator, mock_material_service, mock_cost_service, sample_user_token):
        mock_postgres.query = AsyncMock(return_value=[{
            "id": 1,
            "name": "test.dxf",
            "date": "2024-01-01",
            "md5": "abc123",
            "bucket": "original",
            "userId": 1
        }])
        mock_storage.download = MagicMock(return_value=b"wkb_data")
        mock_creator.createGeometry = MagicMock()
        mock_creator.createGeometry.return_value.getPerimeter = MagicMock(return_value=100.0)
        mock_creator.createGeometry.return_value.getMinimumRectangle = MagicMock(return_value=(0, 0, 10, 10))
        mock_material_service.getMtIdByMaterialIdThicknessId = AsyncMock(return_value=1)
        mock_material_service.getMaterialById = AsyncMock(return_value=MagicMock(price=100, weight=1.5))
        mock_material_service.getThicknessById = AsyncMock(return_value=MagicMock(price=50, speed=10.0))
        mock_cost_service.getPrice = AsyncMock(return_value=1000.0)

        result = await file_service.getPrice("1", "1", "1", 1, sample_user_token)
        assert result.price >= 1500

    @pytest.mark.asyncio
    async def test_set_price_calculator(self, file_service, mock_cost_service):
        mock_cost_service.setPriceCalculator = AsyncMock()
        await file_service.setPriceCalculator("price + 100")
        mock_cost_service.setPriceCalculator.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_price_estimate(self, file_service, mock_cost_service):
        mock_cost_service.getPriceEstimate = AsyncMock(return_value="price + 100")
        result = await file_service.getPriceEstimate()
        assert result == "price + 100"

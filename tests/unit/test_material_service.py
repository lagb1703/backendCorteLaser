import pytest
from unittest.mock import AsyncMock
from src.MaterialModule.materialService import MaterialService
from src.MaterialModule.dtos import Material, Thickness
from fastapi import HTTPException


class TestMaterialService:
    @pytest.fixture
    def mock_postgres(self):
        return AsyncMock()

    @pytest.fixture
    def material_service(self, mock_postgres):
        return MaterialService(mock_postgres)

    @pytest.fixture
    def sample_material(self):
        return Material(
            materialId=1,
            name="Acrylic",
            price=100,
            weight=1.5
        )

    @pytest.fixture
    def sample_thickness(self):
        return Thickness(
            thicknessId=1,
            name="3mm",
            price=50,
            speed=10.0
        )

    @pytest.mark.asyncio
    async def test_get_all_materials(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"materialId": 1, "name": "Acrylic", "price": 100, "weight": 1.5},
            {"materialId": 2, "name": "Wood", "price": 80, "weight": 0.8}
        ])
        result = await material_service.getAllMaterials()
        assert len(result) == 2
        assert result[0].name == "Acrylic"

    @pytest.mark.asyncio
    async def test_get_all_thickness(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"thicknessId": 1, "name": "3mm", "price": 50, "speed": 10.0},
            {"thicknessId": 2, "name": "5mm", "price": 70, "speed": 8.0}
        ])
        result = await material_service.getAllThickness()
        assert len(result) == 2
        assert result[0].name == "3mm"

    @pytest.mark.asyncio
    async def test_get_material_by_id(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"materialId": 1, "name": "Acrylic", "price": 100, "weight": 1.5}
        ])
        result = await material_service.getMaterialById(1)
        assert result.materialId == 1
        assert result.name == "Acrylic"

    @pytest.mark.asyncio
    async def test_get_thickness_by_id(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"thicknessId": 1, "name": "3mm", "price": 50, "speed": 10.0}
        ])
        result = await material_service.getThicknessById(1)
        assert result.thicknessId == 1
        assert result.name == "3mm"

    @pytest.mark.asyncio
    async def test_get_thickness_by_material(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"thicknessId": 1, "name": "3mm", "price": 50, "speed": 10.0}
        ])
        result = await material_service.getThicknessByMaterial("1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_get_thickness_no_linked_to_material(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[
            {"thicknessId": 2, "name": "5mm", "price": 70, "speed": 8.0}
        ])
        result = await material_service.getThicknessNoLinkedToMaterial("1")
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_add_new_material(self, material_service, mock_postgres, sample_material):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        result = await material_service.addNewMaterial(sample_material)
        assert result == 1
        mock_postgres.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_new_material_duplicate(self, material_service, mock_postgres, sample_material):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.save = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        with pytest.raises(HTTPException) as exc_info:
            await material_service.addNewMaterial(sample_material)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_add_new_thickness(self, material_service, mock_postgres, sample_thickness):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        result = await material_service.addNewThickness(sample_thickness)
        assert result == 1

    @pytest.mark.asyncio
    async def test_add_new_thickness_duplicate(self, material_service, mock_postgres, sample_thickness):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.save = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        with pytest.raises(HTTPException) as exc_info:
            await material_service.addNewThickness(sample_thickness)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_change_material(self, material_service, mock_postgres, sample_material):
        mock_postgres.update = AsyncMock()
        await material_service.changeMaterial("1", sample_material)
        mock_postgres.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_material_duplicate(self, material_service, mock_postgres, sample_material):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.update = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        with pytest.raises(HTTPException) as exc_info:
            await material_service.changeMaterial("1", sample_material)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_change_thickness(self, material_service, mock_postgres, sample_thickness):
        mock_postgres.update = AsyncMock()
        await material_service.changeThickness("1", sample_thickness)
        mock_postgres.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_thickness_duplicate(self, material_service, mock_postgres, sample_thickness):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.update = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        with pytest.raises(HTTPException) as exc_info:
            await material_service.changeThickness("1", sample_thickness)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_add_material_thickness(self, material_service, mock_postgres):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        result = await material_service.addMaterialThickness("1", "1", 10.0, 500)
        assert result == 1

    @pytest.mark.asyncio
    async def test_add_material_thickness_duplicate(self, material_service, mock_postgres):
        from asyncpg.exceptions import UniqueViolationError
        mock_postgres.save = AsyncMock(side_effect=UniqueViolationError("duplicate key"))
        with pytest.raises(HTTPException) as exc_info:
            await material_service.addMaterialThickness("1", "1", 10.0, 500)
        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_change_speed_material_thickness_success(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID": 1}])
        mock_postgres.update = AsyncMock()
        await material_service.changeSpeedMaterialThickness("1", "1", 15.0)
        mock_postgres.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_speed_material_thickness_invalid_speed(self, material_service, mock_postgres):
        with pytest.raises(HTTPException) as exc_info:
            await material_service.changeSpeedMaterialThickness("1", "1", 0)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_change_speed_material_thickness_not_found(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID": None}])
        with pytest.raises(HTTPException) as exc_info:
            await material_service.changeSpeedMaterialThickness("1", "1", 15.0)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_material_thickness(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID": 1}])
        mock_postgres.delete = AsyncMock()
        await material_service.deleteMaterialThickness("1", "1")
        mock_postgres.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_material_thickness_not_found(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID": None}])
        await material_service.deleteMaterialThickness("1", "1")

    @pytest.mark.asyncio
    async def test_delete_material(self, material_service, mock_postgres):
        mock_postgres.delete = AsyncMock()
        await material_service.deleteMaterial("1")
        mock_postgres.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_thickness(self, material_service, mock_postgres):
        mock_postgres.delete = AsyncMock()
        await material_service.deleteThickness("1")
        mock_postgres.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_mt_id_by_material_id_thickness_id(self, material_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"FU_MA_MATERIALPKG_GETMTBYUSERIDMATERIALIDTHICKNESSID": 42}])
        result = await material_service.getMtIdByMaterialIdThicknessId("1", "1")
        assert result == 42
import pytest
from unittest.mock import AsyncMock, MagicMock
from src.FileModule.costService import CostService
from src.FileModule.interfaces import PriceElements


class TestCostService:
    @pytest.fixture
    def mock_postgres(self):
        return AsyncMock()

    @pytest.fixture
    def cost_service(self, mock_postgres):
        return CostService(postgres_client=mock_postgres)

    @pytest.mark.asyncio
    async def test_get_price_estimate(self, cost_service, mock_postgres):
        mock_postgres.query = AsyncMock(return_value=[{"estimatic": '"materialPrice + thicknessPrice"'}])
        result = await cost_service.getPriceEstimate()
        assert result == "materialPrice + thicknessPrice"

    @pytest.mark.asyncio
    async def test_set_price_calculator(self, cost_service, mock_postgres):
        mock_postgres.save = AsyncMock(return_value={"p_id": 1})
        await cost_service.setPriceCalculator("materialPrice * 2")
        mock_postgres.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_price_with_cached_tree(self, cost_service, mock_postgres):
        cost_service.tree = MagicMock()
        cost_service.tree.body = MagicMock()
        
        mock_evaluator = MagicMock()
        mock_evaluator.visit = MagicMock(return_value=100.0)
        
        price_elements = PriceElements(
            materialPrice=100.0,
            thicknessPrice=50.0,
            area=2.0,
            weight=1.5,
            perimeter=10.0,
            speed=10.0,
            amount=1,
            mtPrice=500,
            blends=0
        )
        
        with pytest.MonkeyPatch.context() as m:
            m.setattr("src.FileModule.costService.AstEval", lambda x: mock_evaluator)
            result = await cost_service.getPrice(price_elements)
            assert result == 100.0

    @pytest.mark.asyncio
    async def test_get_price_without_cached_tree(self, cost_service, mock_postgres):
        cost_service.tree = None
        mock_postgres.query = AsyncMock(return_value=[{"estimatic": '"materialPrice + thicknessPrice"'}])
        
        price_elements = PriceElements(
            materialPrice=100.0,
            thicknessPrice=50.0,
            area=2.0,
            weight=1.5,
            perimeter=10.0,
            speed=10.0,
            amount=1,
            mtPrice=500,
            blends=0
        )
        
        result = await cost_service.getPrice(price_elements)
        assert result == 150.0

import pytest
from src.FileModule.costCalculator import CostCalculator


class TestCostCalculator:
    def test_simple_calculation(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=10000.0,
            thicknessPrice=5000.0,
            area=20.0,
            perimeter=100.0,
            amount=1
        )
        # (10000 * 20) + (100 * 5000) = 200000 + 500000 = 700000
        assert result == 700000.0

    def test_minimum_price(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=10.0,
            thicknessPrice=5.0,
            area=0.1,
            perimeter=1.0,
            amount=1
        )
        # (10 * 0.1) + (1 * 5) = 1 + 5 = 6, but minimum is 150000
        assert result == 150000.0

    def test_with_multiple_amount(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=10000.0,
            thicknessPrice=5000.0,
            area=20.0,
            perimeter=100.0,
            amount=3
        )
        # ((10000 * 20) + (100 * 5000)) * 3 = 700000 * 3 = 2100000
        assert result == 2100000.0

    def test_zero_area(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=100.0,
            thicknessPrice=50.0,
            area=0.0,
            perimeter=10.0,
            amount=1
        )
        # (100 * 0) + (10 * 50) = 0 + 500 = 500, but minimum is 150000
        assert result == 150000.0

    def test_zero_perimeter(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=100.0,
            thicknessPrice=50.0,
            area=2.0,
            perimeter=0.0,
            amount=1
        )
        # (100 * 2) + (0 * 50) = 200 + 0 = 200, but minimum is 150000
        assert result == 150000.0

    def test_large_values(self):
        calculator = CostCalculator()
        result = calculator.getPrice(
            materialPrice=1000.0,
            thicknessPrice=500.0,
            area=100.0,
            perimeter=1000.0,
            amount=10
        )
        # ((1000 * 100) + (1000 * 500)) * 10 = (100000 + 500000) * 10 = 6000000
        assert result == 6000000.0

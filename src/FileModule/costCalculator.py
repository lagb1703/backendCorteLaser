
class CostCalculator:
    
    def getPrice(self, materialPrice: float, thicknessPrice: float, area: float, perimeter: float)->float:
        print(materialPrice, thicknessPrice, area, perimeter)
        return max((materialPrice*area) + (perimeter*thicknessPrice), 150000)
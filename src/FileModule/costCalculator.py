
class CostCalculator:
    
    def getPrice(self, materialPrice: float, thicknessPrice: float, area: float, perimeter: float)->float:
        return max((materialPrice*area) + (perimeter*thicknessPrice), 150000)
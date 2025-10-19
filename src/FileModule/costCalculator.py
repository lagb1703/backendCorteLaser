
class CostCalculator:
    
    def getPrice(self, materialPrice: float, thicknessPrice: float, area: float, perimeter: float)->float:
        return (materialPrice*area) + (perimeter*thicknessPrice)
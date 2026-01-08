from src.FileModule.astEval import AstEval
from src.utils.PostgressClient import PostgressClient
from src.FileModule.enums import CostSql
from typing import Dict
import ast

class CostService:
    
    __instance: 'CostService | None' = None
    
    tree: ast.Expression | None = None
    
    @staticmethod
    def getInstance()->'CostService':
        if CostService.__instance is None:
            CostService.__instance = CostService()
        return CostService.__instance
    
    def __init__(self) -> None:
        self.__postgressClient = PostgressClient.getInstance()
    
    async def __setEstimate(self, exp: str) -> None:
        data: Dict[str, str] = {
            'estimatec': exp
        }
        await self.__postgressClient.save(CostSql.newEstimate.value, data)
    
    async def getPriceEstimate(self) -> str:
        return (await self.__postgressClient.query(CostSql.getPrice.value, []))[0]['estimatec']
    
    async def getPrice(self, materialPrice: float, thicknessPrice: float, area: float, weight: float, perimeter: float, amount: int) -> float:
        if self.tree is None:
            exp = await self.getPriceEstimate()
            self.tree = ast.parse(exp, mode='eval')
        try:
            names: Dict[str, float | int] = {
                "materialPrice": materialPrice,
                "thicknessPrice": thicknessPrice,
                "area": area,
                "weight": weight,
                "perimeter": perimeter,
                "amount": amount
            }
            evaluator = AstEval(names)
            return evaluator.visit(self.tree)
        except Exception:
            raise
    
    async def setPriceCalculator(self, exp: str) -> None:
        self.tree = ast.parse(exp, mode='eval')
        await self.__setEstimate(exp)
    
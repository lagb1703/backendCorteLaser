from src.FileModule.astEval import AstEval
from src.utils.PostgressClient import PostgressClient, get_postgress_client
from src.FileModule.enums import CostSql
import ast
from src.FileModule.interfaces import PriceElements

class CostService:

    tree: ast.Expression | None = None

    def __init__(self, postgress_client: PostgressClient) -> None:
        self.__postgressClient = postgress_client

    async def __setEstimate(self, exp: str) -> None:
        data: dict[str, str] = {"estimatic": exp}
        print(data)
        await self.__postgressClient.save(CostSql.newEstimate.value, data)

    async def getPriceEstimate(self) -> str:
        return (await self.__postgressClient.query(CostSql.getPrice.value, []))[0][
            "estimatic"
        ].replace('"', "")

    async def getPrice(self, priceElemnets: PriceElements) -> float:
        if self.tree is None:
            exp = await self.getPriceEstimate()
            self.tree = ast.parse(exp, mode="eval")
        try:
            names: dict[str, float | int] = priceElemnets.model_dump()
            evaluator = AstEval(names)
            result = evaluator.visit(self.tree.body)
            return result
        except Exception:
            raise

    async def setPriceCalculator(self, exp: str) -> None:
        self.tree = ast.parse(exp, mode="eval")
        await self.__setEstimate(exp)

def get_cost_service() -> CostService:
    return CostService(postgress_client=get_postgress_client())

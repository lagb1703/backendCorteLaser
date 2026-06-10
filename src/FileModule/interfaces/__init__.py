from pydantic import BaseModel

class PriceElements(BaseModel):
    matrialPrice: float
    thicknessPrice: float
    area: float
    weight: float
    perimeter: float
    speed: float
    amount: int
    blends: int

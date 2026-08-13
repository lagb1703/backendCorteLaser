from abc import ABC, abstractmethod


class GeometriesAnalyzer(ABC):

    @abstractmethod
    def checkGeometries(self) -> bool:
        pass

    @abstractmethod
    def getMinimumRectangle(self) -> tuple[float, float, float, float]:
        pass

    @abstractmethod
    def getPerimeter(self) -> float:
        pass

    @abstractmethod
    def export(self, format: str) -> bytes:
        pass

    @abstractmethod
    def save(self) -> bytes:
        pass

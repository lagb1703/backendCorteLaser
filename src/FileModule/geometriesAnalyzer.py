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
    def createImage(self) -> bytes:
        pass

    @abstractmethod
    def createOBJ(self, thickness: float) -> bytes:
        pass

    @abstractmethod
    def save(self) -> bytes:
        pass

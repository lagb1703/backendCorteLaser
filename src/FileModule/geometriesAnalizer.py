from abc import ABC, abstractmethod
from typing import Tuple

class GeometriesAnaliser(ABC):
    
    @abstractmethod
    def checkGeometries(self)->bool:
        pass
    
    @abstractmethod
    def getMinimunRectangle(self)->Tuple[float, float, float, float]:
        pass
    
    @abstractmethod
    def getPerimeter(self)->int:
        pass
    
    @abstractmethod
    def createImage(self)->bytes:
        pass
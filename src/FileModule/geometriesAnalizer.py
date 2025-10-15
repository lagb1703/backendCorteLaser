from abc import ABC, abstractmethod
from typing import Tuple, Any

class GeometriesAnaliser(ABC):
    
    @abstractmethod
    def checkGeometries(self)->bool:
        pass
    
    @abstractmethod
    def getMinimunRectangle(self)->Tuple[int, ...]:
        pass
    
    @abstractmethod
    def getPerimeter(self)->int:
        pass
    
    @abstractmethod
    def createImage(self)->Any:
        pass
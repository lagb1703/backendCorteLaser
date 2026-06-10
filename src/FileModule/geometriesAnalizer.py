from abc import ABC, abstractmethod

class GeometriesAnaliser(ABC):
    
    @abstractmethod
    def checkGeometries(self)->bool:
        pass
    
    @abstractmethod
    def getMinimunRectangle(self)->tuple[float, float, float, float]:
        pass
    
    @abstractmethod
    def getPerimeter(self)->int:
        pass
    
    @abstractmethod
    def createImage(self)->bytes:
        pass
    
    @abstractmethod
    def save(self)->bytes:
        pass
from abc import ABC, abstractmethod
from typing import List
from typing import TypeVar, Generic

T = TypeVar('T')

class GeometriesAdapter(ABC, Generic[T]):
    
    def __init__(self):
        pass
    
    @abstractmethod
    def makeGeometries(self, data: bytes)-> List[T]:
        pass
from abc import ABC, abstractmethod

import geopandas as gpd


class GeometryExporter(ABC):

    @abstractmethod
    def export(self, geometries: gpd.GeoSeries) -> bytes:
        pass

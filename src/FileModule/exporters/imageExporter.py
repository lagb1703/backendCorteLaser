from io import BytesIO

import geopandas as gpd
import matplotlib.pyplot as plt

from src.FileModule.exporters.geometryExporter import GeometryExporter


class ImageExporter(GeometryExporter):

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        fig, ax = plt.subplots(figsize=(6, 6))  # type: ignore
        geometries[geometries.geom_type == "Polygon"].plot(  # type: ignore
            ax=ax, facecolor="none", edgecolor="black"
        )
        geometries[geometries.geom_type == "MultiLineString"].plot(  # type: ignore
            ax=ax, facecolor="none", edgecolor="red"
        )
        ax.set_aspect("equal")
        ax.axis("off")
        buffer = BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0)  # type: ignore
        plt.close(fig)
        imageBytes = buffer.getvalue()
        buffer.close()
        return imageBytes

import geopandas as gpd
import pytest
from shapely.geometry import LineString, MultiLineString, Polygon

from src.FileModule.exporters import (
    GeometryExporter,
    GlbExporter,
    ImageExporter,
    ObjExporter,
)
from src.FileModule.implements import ShapelyAnalyzer


def test_image_exporter_returns_png():
    geometries = gpd.GeoSeries(
        [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
    )

    result = ImageExporter().export(geometries)

    assert result.startswith(b"\x89PNG\r\n\x1a\n")


def test_obj_exporter_returns_obj_data():
    geometries = gpd.GeoSeries(
        [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
    )

    result = ObjExporter().export(geometries)

    assert b"v " in result
    assert b"f " in result


def test_glb_exporter_returns_glb_data():
    geometries = gpd.GeoSeries(
        [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
    )

    result = GlbExporter().export(geometries)

    assert result[:4] == b"glTF"


def test_glb_exporter_includes_bend_line_geometry():
    geometries = gpd.GeoSeries(
        [
            Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
            MultiLineString([LineString([(0, 0.5), (1, 0.5)])]),
        ]
    )

    result = GlbExporter().export(geometries)

    assert result[:4] == b"glTF"


class RecordingExporter(GeometryExporter):

    def __init__(self):
        self.geometries = None

    def export(self, geometries: gpd.GeoSeries) -> bytes:
        self.geometries = geometries
        return b"exported"


def test_analyzer_delegates_to_selected_exporter():
    exporter = RecordingExporter()
    analyzer = ShapelyAnalyzer(
        [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
        exporters={"custom": exporter},
    )

    result = analyzer.export("custom")

    assert result == b"exported"
    assert exporter.geometries is not None


def test_analyzer_rejects_unsupported_export_format():
    analyzer = ShapelyAnalyzer([])

    with pytest.raises(ValueError, match="Unsupported export format: xyz"):
        analyzer.export("xyz")

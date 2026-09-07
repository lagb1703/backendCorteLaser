import geopandas as gpd
import numpy as np
import pytest
import trimesh  # type: ignore
from io import BytesIO
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


def loadFoldedPlate() -> trimesh.Scene:
    """A 30x10 plate cut by two bend lines, so pieces chain father -> son -> son."""
    geometries = gpd.GeoSeries(
        [
            Polygon([(0, 0), (30, 0), (30, 10), (0, 10)]),
            MultiLineString([LineString([(10, 0), (10, 10)])]),
            MultiLineString([LineString([(20, 0), (20, 10)])]),
        ]
    )
    return trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")


def test_glb_exporter_chains_sons_through_the_bend_lines():
    scene = loadFoldedPlate()
    parents = scene.graph.transforms.parents

    assert parents["father"] == scene.graph.base_frame
    assert parents["son0"] == "father"
    assert parents["son1"] == "son0"


def test_glb_exporter_gives_each_son_a_pivot_on_its_bend_line():
    scene = loadFoldedPlate()

    matrix = np.asarray(scene.graph.transforms.edge_data[("father", "son0")]["matrix"])
    assert not np.allclose(matrix, np.eye(4))
    # the pivot sits on the bend line (x=10, mid span y=5) at half the sheet thickness
    assert np.allclose(matrix[:3, 3], [10.0, 5.0, 0.005])


def test_glb_exporter_bakes_son_geometry_into_its_pivot_frame():
    scene = loadFoldedPlate()

    bounds = scene.geometry["son0_mesh"].bounds
    # the bend line runs through the son's local origin, so x straddles zero
    assert bounds[0][0] == pytest.approx(-5.0)
    assert bounds[1][0] == pytest.approx(5.0)
    # and the piece hangs on the local +Y side, so a positive angle always folds
    # the same way regardless of how the DXF drew the line
    assert bounds[0][1] == pytest.approx(0.0)
    assert bounds[1][1] == pytest.approx(10.0)


def test_glb_exporter_exposes_bend_metadata_on_every_son():
    scene = loadFoldedPlate()

    rootExtras = scene.graph.transforms.edge_data[
        (scene.graph.base_frame, "father")
    ]["metadata"]
    assert rootExtras["type"] == "part-root"
    assert rootExtras["nodeId"] == "father"

    extras = scene.graph.transforms.edge_data[("father", "son0")]["metadata"]
    assert extras["type"] == "bend-node"
    assert extras["nodeId"] == "son0"
    assert extras["parentId"] == "father"
    assert extras["bendLineIndex"] == 0
    assert extras["start"] == [10.0, 0.0, 0.005]
    assert extras["end"] == [10.0, 10.0, 0.005]
    assert len(extras["axis"]) == 3


def test_glb_exporter_son_folds_around_its_bend_line():
    scene = loadFoldedPlate()
    local = np.asarray(scene.graph.transforms.edge_data[("father", "son0")]["matrix"])

    rotateX90 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    # far edge of the flap, in the son's own frame
    farEdge = np.asarray([0.0, 10.0, 0.0, 1.0])
    folded = local @ rotateX90 @ farEdge

    # folded 90 degrees it stands straight up over the bend line
    assert np.allclose(folded[:3], [10.0, 5.0, 10.005], atol=1e-6)


def test_glb_exporter_without_bend_lines_has_no_sons():
    geometries = gpd.GeoSeries([Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])])

    scene = trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")

    assert "father" in scene.graph.nodes
    assert not [node for node in scene.graph.nodes if node.startswith("son")]


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

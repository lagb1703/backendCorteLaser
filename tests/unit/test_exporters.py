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
    # and the node's local X is the bend line itself, which is what pins the
    # fold: its father keeps the identity, so local X still reads as the axis
    extras = scene.graph.transforms.edge_data[("father", "son0")]["metadata"]
    assert np.allclose(matrix[:3, 0], extras["axis"])


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
    # the pivot sits mid thickness, so folding does not push the pieces apart
    assert bounds[0][2] == pytest.approx(-0.005)
    assert bounds[1][2] == pytest.approx(0.005)


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
    assert extras["pivot"] == pytest.approx([10.0, 5.0, 0.005])
    # the axis runs along the bend line, oriented so a positive angle folds up
    assert extras["axis"] == pytest.approx([0.0, -1.0, 0.0])
    # the front end labels each control from the bend line it hangs from
    assert extras["bendLineIndex"] == 0
    assert extras["occurrence"] == 0
    assert extras["start"] == pytest.approx([10.0, 0.0, 0.005])
    assert extras["end"] == pytest.approx([10.0, 10.0, 0.005])


def test_glb_exporter_son_folds_around_its_bend_line():
    scene = loadFoldedPlate()
    local = np.asarray(scene.graph.transforms.edge_data[("father", "son0")]["matrix"])

    rotateX90 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    # far edge of the flap, in the son's own frame
    farEdge = np.asarray([0.0, 10.0, 0.0, 1.0])
    folded = local @ rotateX90 @ farEdge

    # folded 90 degrees it stands straight up over the bend line
    assert np.allclose(folded[:3], [10.0, 5.0, 10.005], atol=1e-6)


def test_glb_exporter_grandson_follows_the_piece_it_hangs_from():
    scene = loadFoldedPlate()
    edges = scene.graph.transforms.edge_data
    local0 = np.asarray(edges[("father", "son0")]["matrix"])
    local1 = np.asarray(edges[("son0", "son1")]["matrix"])

    rotateX90 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    farEdge = np.asarray([0.0, 10.0, 0.0, 1.0])

    # flat, the last piece ends at the far end of the plate
    assert np.allclose((local0 @ local1 @ farEdge)[:3], [30.0, 5.0, 0.005], atol=1e-6)
    # folding its parent carries it up without folding it on its own
    assert np.allclose(
        (local0 @ rotateX90 @ local1 @ farEdge)[:3], [10.0, 5.0, 20.005], atol=1e-6
    )


def test_glb_exporter_folds_a_diagonal_bend_on_its_own_line():
    geometries = gpd.GeoSeries(
        [
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
            MultiLineString([LineString([(0, 0), (10, 10)])]),
        ]
    )

    scene = trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")
    local = np.asarray(scene.graph.transforms.edge_data[("father", "son0")]["matrix"])

    # local X follows the 45 degree bend, not the world axes
    assert np.allclose(local[:3, 0], [np.sqrt(0.5), np.sqrt(0.5), 0.0])

    rotateX90 = trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])
    # every point of the bend line itself stays put while the flap folds
    for distance in (-3.0, 0.0, 4.0):
        onTheBend = np.asarray([distance, 0.0, 0.0, 1.0])
        assert np.allclose(local @ rotateX90 @ onTheBend, local @ onTheBend, atol=1e-9)


def test_glb_exporter_ignores_the_bend_zone_lines():
    """Only the first line of a group is the bend; the rest mark its extent."""
    geometries = gpd.GeoSeries(
        [
            Polygon([(0, 0), (20, 0), (20, 10), (0, 10)]),
            MultiLineString(
                [
                    LineString([(10, 0), (10, 10)]),
                    LineString([(9.2, 0), (9.2, 10)]),
                    LineString([(10.8, 0), (10.8, 10)]),
                ]
            ),
        ]
    )

    scene = trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")

    sons = [node for node in scene.graph.nodes if node.startswith("son")]
    assert sons == ["son0"]
    extras = scene.graph.transforms.edge_data[("father", "son0")]["metadata"]
    assert extras["pivot"] == pytest.approx([10.0, 5.0, 0.005])


def test_glb_exporter_numbers_both_hinges_of_one_bend_line():
    """A notch splits one bend line into two flaps that share its number."""
    geometries = gpd.GeoSeries(
        [
            Polygon(
                [(0, 0), (30, 0), (30, 20), (20, 20), (20, 10), (10, 10), (10, 20), (0, 20)]
            ),
            MultiLineString([LineString([(0, 15), (30, 15)])]),
        ]
    )

    scene = trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")
    edges = scene.graph.transforms.edge_data
    sons = [
        edges[("father", node)]["metadata"]
        for node in ("son0", "son1")
    ]

    assert [extras["bendLineIndex"] for extras in sons] == [0, 0]
    assert sorted(extras["occurrence"] for extras in sons) == [0, 1]
    # both report the whole bend line, but each pivots on its own arm
    for extras in sons:
        assert extras["start"] == pytest.approx([0.0, 15.0, 0.005])
        assert extras["end"] == pytest.approx([30.0, 15.0, 0.005])
    assert sorted(extras["pivot"][0] for extras in sons) == pytest.approx([5.0, 25.0])


def test_glb_exporter_closes_a_piece_with_a_repeated_vertex():
    """Flattened DXF curves repeat a point, which used to crack the mesh.

    The repeat is rarely exact: a last bit difference makes the triangulation
    emit a sliver, and the extrusion then raises a wall on it.
    """
    geometries = gpd.GeoSeries(
        [Polygon([(0, 0), (1e-17, 0), (10, 0), (4, 8)])]
    )

    scene = trimesh.load(BytesIO(GlbExporter().export(geometries)), file_type="glb")

    mesh = scene.geometry["father_mesh"]
    assert mesh.is_watertight
    assert len(trimesh.repair.broken_faces(mesh)) == 0


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

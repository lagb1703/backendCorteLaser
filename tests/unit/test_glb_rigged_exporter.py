import geopandas as gpd
import numpy as np
from pygltflib import GLTF2
from shapely.geometry import LineString, MultiLineString, Point, Polygon

from src.FileModule.exporters import GlbRiggedExporter
from src.FileModule.implements import ShapelyAnalyzer


def readAccessor(gltf: GLTF2, accessorIndex: int, dtype, components: int):
    accessor = gltf.accessors[accessorIndex]
    view = gltf.bufferViews[accessor.bufferView]
    byteOffset = (view.byteOffset or 0) + (accessor.byteOffset or 0)
    byteLength = view.byteLength
    data = gltf.binary_blob()[byteOffset : byteOffset + byteLength]
    values = np.frombuffer(data, dtype=dtype, count=accessor.count * components)
    return values.reshape(accessor.count, components)


def matrixFromNode(node) -> np.ndarray:
    return np.asarray(node.matrix, dtype=np.float64).reshape((4, 4), order="F")


def worldMatrices(gltf: GLTF2) -> dict[int, np.ndarray]:
    parents: dict[int, int] = {}
    for parentIndex, node in enumerate(gltf.nodes):
        for childIndex in node.children or []:
            parents[childIndex] = parentIndex

    result: dict[int, np.ndarray] = {}

    def calculate(index: int) -> np.ndarray:
        if index in result:
            return result[index]
        parent = parents.get(index)
        local = matrixFromNode(gltf.nodes[index])
        result[index] = local if parent is None else calculate(parent) @ local
        return result[index]

    for index in range(len(gltf.nodes)):
        calculate(index)
    return result


def test_rigged_glb_contains_bend_joint_and_valid_skinning():
    geometries = gpd.GeoSeries(
        [
            Polygon([(0, 0), (10, 0), (10, 10), (0, 10)]),
            MultiLineString([LineString([(5, 0), (5, 10)])]),
        ]
    )

    data = GlbRiggedExporter().export(geometries)
    gltf = GLTF2().load_from_bytes(data)

    assert data[:4] == b"glTF"
    assert len(gltf.skins) == 1
    jointNames = [gltf.nodes[index].name for index in gltf.skins[0].joints]
    assert "rig_root" in jointNames
    assert "part_0_root" in jointNames
    assert "bend_line_0" in jointNames
    bendNode = next(node for node in gltf.nodes if node.name == "bend_line_0")
    assert bendNode.extras["start"] == [5.0, 0.0, 0.005]
    assert bendNode.extras["end"] == [5.0, 10.0, 0.005]
    assert bendNode.extras["axis"] == [0.0, 1.0, 0.0]

    assert any(node.skin == 0 for node in gltf.nodes)
    for primitive in gltf.meshes[0].primitives:
        assert primitive.attributes.JOINTS_0 is not None
        assert primitive.attributes.WEIGHTS_0 is not None
        joints = readAccessor(
            gltf, primitive.attributes.JOINTS_0, np.uint8, components=4
        )
        weights = readAccessor(
            gltf, primitive.attributes.WEIGHTS_0, np.float32, components=4
        )
        assert np.all(joints[:, 0] < len(gltf.skins[0].joints))
        assert np.all(joints[:, 1:] == 0)
        np.testing.assert_allclose(weights[:, 0], 1.0)
        np.testing.assert_allclose(weights[:, 1:], 0.0)

    inverseBindAccessor = gltf.skins[0].inverseBindMatrices
    inverseBinds = readAccessor(
        gltf, inverseBindAccessor, np.float32, components=16
    ).reshape((-1, 4, 4)).transpose((0, 2, 1))
    worlds = worldMatrices(gltf)
    for jointIndex, nodeIndex in enumerate(gltf.skins[0].joints):
        np.testing.assert_allclose(
            worlds[nodeIndex] @ inverseBinds[jointIndex],
            np.eye(4),
            atol=1e-5,
        )


def test_rigged_glb_preserves_polygon_holes():
    hole = Polygon([(2, 2), (8, 2), (8, 8), (2, 8)])
    polygon = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)])
    bendLine = MultiLineString([LineString([(5, 0), (5, 10)])])

    data = GlbRiggedExporter().export(gpd.GeoSeries([polygon, hole, bendLine]))
    gltf = GLTF2().load_from_bytes(data)

    platePrimitives = [
        primitive for primitive in gltf.meshes[0].primitives if primitive.material == 0
    ]
    assert len(platePrimitives) == 2
    for primitive in platePrimitives:
        positions = readAccessor(
            gltf, primitive.attributes.POSITION, np.float32, components=3
        )
        indices = readAccessor(gltf, primitive.indices, np.uint32, components=1)
        for triangle in indices.reshape(-1, 3):
            center = positions[triangle].mean(axis=0)
            assert not hole.contains(Point(float(center[0]), float(center[1])))


def test_analyzer_registers_rigged_glb_strategy():
    polygon = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

    data = ShapelyAnalyzer([polygon]).export("glb-rigged")

    assert data[:4] == b"glTF"

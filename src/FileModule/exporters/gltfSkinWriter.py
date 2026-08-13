from dataclasses import dataclass
from typing import Any

import numpy as np
from pygltflib import (
    ARRAY_BUFFER,
    ELEMENT_ARRAY_BUFFER,
    FLOAT,
    MAT4,
    SCALAR,
    TRIANGLES,
    UNSIGNED_BYTE,
    UNSIGNED_INT,
    Accessor,
    Asset,
    Attributes,
    Buffer,
    BufferView,
    GLTF2,
    Material,
    Mesh,
    Node,
    PbrMetallicRoughness,
    Primitive,
    Scene,
    Skin,
    VEC3,
    VEC4,
)


@dataclass
class RigNode:
    name: str
    localMatrix: np.ndarray
    parent: int | None
    isJoint: bool = False
    extras: dict[str, Any] | None = None


@dataclass
class RigPrimitive:
    vertices: np.ndarray
    normals: np.ndarray
    faces: np.ndarray
    jointIndices: np.ndarray
    material: int


class GltfSkinWriter:

    def write(
        self,
        nodes: list[RigNode],
        inverseBindMatrices: list[np.ndarray],
        primitives: list[RigPrimitive],
    ) -> bytes:
        if not nodes:
            raise ValueError("A rigged GLB requires at least one node")

        rootNodeIndices = [
            index for index, node in enumerate(nodes) if node.parent is None
        ]
        if len(rootNodeIndices) != 1:
            raise ValueError("A rigged GLB requires exactly one root node")

        jointNodeIndices = [
            index for index, node in enumerate(nodes) if node.isJoint
        ]
        if not jointNodeIndices:
            raise ValueError("A rigged GLB requires at least one joint")
        if len(jointNodeIndices) > 255:
            raise ValueError("A rigged GLB supports at most 255 joints")
        if len(inverseBindMatrices) != len(jointNodeIndices):
            raise ValueError("Each joint must have an inverse bind matrix")

        jointSlots = {
            nodeIndex: jointIndex
            for jointIndex, nodeIndex in enumerate(jointNodeIndices)
        }
        gltf = GLTF2(
            asset=Asset(
                version="2.0",
                generator="backendCorteLaser rigged GLB exporter",
            )
        )
        binary = bytearray()

        gltf.materials = [
            Material(
                name="sheet-metal",
                pbrMetallicRoughness=PbrMetallicRoughness(
                    baseColorFactor=[0.0, 0.0, 1.0, 1.0],
                    metallicFactor=0.0,
                    roughnessFactor=0.7,
                ),
                doubleSided=True,
            ),
            Material(
                name="bend-line",
                pbrMetallicRoughness=PbrMetallicRoughness(
                    baseColorFactor=[1.0, 0.0, 0.0, 1.0],
                    metallicFactor=0.0,
                    roughnessFactor=0.7,
                ),
                doubleSided=True,
            ),
        ]

        inverseBindArray = np.asarray(inverseBindMatrices, dtype=np.float32)
        if inverseBindArray.shape != (len(jointNodeIndices), 4, 4):
            raise ValueError("Inverse bind matrices must have shape (joints, 4, 4)")
        inverseBindData = np.ascontiguousarray(
            np.transpose(inverseBindArray, (0, 2, 1))
        )
        inverseBindView = self.__appendBufferView(
            gltf, binary, inverseBindData, None
        )
        inverseBindAccessor = self.__appendAccessor(
            gltf,
            inverseBindView,
            componentType=FLOAT,
            count=len(jointNodeIndices),
            accessorType=MAT4,
        )

        primitiveDefinitions: list[Primitive] = []
        for primitive in primitives:
            primitiveDefinition = self.__createPrimitive(
                gltf, binary, primitive, len(jointNodeIndices)
            )
            if primitiveDefinition is not None:
                primitiveDefinitions.append(primitiveDefinition)

        if primitiveDefinitions:
            gltf.meshes = [
                Mesh(
                    name="rigged-sheet-metal",
                    primitives=primitiveDefinitions,
                )
            ]
        else:
            gltf.meshes = []

        gltf.nodes = []
        for node in nodes:
            matrix = np.asarray(node.localMatrix, dtype=np.float32)
            if matrix.shape != (4, 4):
                raise ValueError("Rig node matrices must have shape (4, 4)")
            gltf.nodes.append(
                Node(
                    name=node.name,
                    matrix=matrix.flatten(order="F").tolist(),
                    children=[],
                    extras=node.extras,
                )
            )

        for index, node in enumerate(nodes):
            if node.parent is None:
                continue
            if node.parent < 0 or node.parent >= len(nodes):
                raise ValueError(f"Invalid parent for rig node {node.name}")
            gltf.nodes[node.parent].children.append(index)

        rootNodeIndex = rootNodeIndices[0]
        if primitiveDefinitions:
            meshNodeIndex = len(gltf.nodes)
            gltf.nodes.append(
                Node(
                    name="rigged_plate",
                    mesh=0,
                    skin=0,
                    matrix=np.eye(4, dtype=np.float32).flatten(order="F").tolist(),
                    children=[],
                )
            )
            gltf.nodes[rootNodeIndex].children.append(meshNodeIndex)

        gltf.buffers = [Buffer(byteLength=len(binary))]
        gltf.skins = [
            Skin(
                name="bend-line-rig",
                inverseBindMatrices=inverseBindAccessor,
                skeleton=rootNodeIndex,
                joints=jointNodeIndices,
            )
        ]
        gltf.scenes = [Scene(name="rigged-scene", nodes=[rootNodeIndex])]
        gltf.scene = 0
        gltf.set_binary_blob(bytes(binary))
        return b"".join(gltf.save_to_bytes())

    def __createPrimitive(
        self,
        gltf: GLTF2,
        binary: bytearray,
        primitive: RigPrimitive,
        jointCount: int,
    ) -> Primitive | None:
        vertices = np.asarray(primitive.vertices, dtype=np.float32).reshape(-1, 3)
        normals = np.asarray(primitive.normals, dtype=np.float32).reshape(-1, 3)
        faces = np.asarray(primitive.faces, dtype=np.uint32).reshape(-1)
        jointIndices = np.asarray(primitive.jointIndices, dtype=np.int64).reshape(-1)
        if len(vertices) == 0 or len(faces) == 0:
            return None
        if len(normals) != len(vertices) or len(jointIndices) != len(vertices):
            raise ValueError("Primitive attributes must have the same vertex count")
        if np.any(jointIndices < 0) or np.any(jointIndices >= jointCount):
            raise ValueError("Primitive references an invalid joint")

        joints = np.zeros((len(vertices), 4), dtype=np.uint8)
        joints[:, 0] = jointIndices.astype(np.uint8)
        weights = np.zeros((len(vertices), 4), dtype=np.float32)
        weights[:, 0] = 1.0

        positionView = self.__appendBufferView(
            gltf, binary, vertices, ARRAY_BUFFER
        )
        normalView = self.__appendBufferView(gltf, binary, normals, ARRAY_BUFFER)
        jointsView = self.__appendBufferView(gltf, binary, joints, ARRAY_BUFFER)
        weightsView = self.__appendBufferView(gltf, binary, weights, ARRAY_BUFFER)
        indexView = self.__appendBufferView(
            gltf, binary, faces, ELEMENT_ARRAY_BUFFER
        )

        positionAccessor = self.__appendAccessor(
            gltf,
            positionView,
            componentType=FLOAT,
            count=len(vertices),
            accessorType=VEC3,
            minimum=vertices.min(axis=0).tolist(),
            maximum=vertices.max(axis=0).tolist(),
        )
        normalAccessor = self.__appendAccessor(
            gltf,
            normalView,
            componentType=FLOAT,
            count=len(normals),
            accessorType=VEC3,
        )
        jointsAccessor = self.__appendAccessor(
            gltf,
            jointsView,
            componentType=UNSIGNED_BYTE,
            count=len(joints),
            accessorType=VEC4,
        )
        weightsAccessor = self.__appendAccessor(
            gltf,
            weightsView,
            componentType=FLOAT,
            count=len(weights),
            accessorType=VEC4,
        )
        indexAccessor = self.__appendAccessor(
            gltf,
            indexView,
            componentType=UNSIGNED_INT,
            count=len(faces),
            accessorType=SCALAR,
        )
        return Primitive(
            attributes=Attributes(
                POSITION=positionAccessor,
                NORMAL=normalAccessor,
                JOINTS_0=jointsAccessor,
                WEIGHTS_0=weightsAccessor,
            ),
            indices=indexAccessor,
            material=primitive.material,
            mode=TRIANGLES,
        )

    def __appendBufferView(
        self,
        gltf: GLTF2,
        binary: bytearray,
        data: np.ndarray,
        target: int | None,
    ) -> int:
        alignment = (-len(binary)) % 4
        if alignment:
            binary.extend(b"\0" * alignment)
        rawData = np.ascontiguousarray(data).tobytes(order="C")
        viewIndex = len(gltf.bufferViews)
        gltf.bufferViews.append(
            BufferView(
                buffer=0,
                byteOffset=len(binary),
                byteLength=len(rawData),
                target=target,
            )
        )
        binary.extend(rawData)
        return viewIndex

    def __appendAccessor(
        self,
        gltf: GLTF2,
        bufferView: int,
        componentType: int,
        count: int,
        accessorType: str,
        minimum: list[float] | None = None,
        maximum: list[float] | None = None,
    ) -> int:
        accessorIndex = len(gltf.accessors)
        gltf.accessors.append(
            Accessor(
                bufferView=bufferView,
                byteOffset=0,
                componentType=componentType,
                count=count,
                type=accessorType,
                min=minimum,
                max=maximum,
            )
        )
        return accessorIndex

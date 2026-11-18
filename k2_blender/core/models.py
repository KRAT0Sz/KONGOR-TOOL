"""
Intermediate Representation (IR) Dataclasses for K2 Engine Models and Animations.
Zero external dependencies, purely serializable and inspectable.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional

@dataclass
class VertexAttributes:
    position: Tuple[float, float, float]
    normal: Tuple[float, float, float]
    uvs: List[Tuple[float, float]] = field(default_factory=list)
    tangents: List[Tuple[float, float, float]] = field(default_factory=list)
    signs: List[int] = field(default_factory=list)
    colors: List[Tuple[int, int, int, int]] = field(default_factory=list)
    weights: List[Tuple[int, float]] = field(default_factory=list)

@dataclass
class K2ModelHeader:
    version: int = 3
    num_meshes: int = 0
    num_sprites: int = 0
    num_surfs: int = 0
    num_bones: int = 0
    bmin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bmax: Tuple[float, float, float] = (0.0, 0.0, 0.0)

@dataclass
class K2Bone:
    index: int
    name: str
    parent_index: int = -1
    inv_base: Tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)
    base: Tuple[float, ...] = (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0)

@dataclass
class K2BlendedLink:
    weights: List[float] = field(default_factory=list)
    indexes: List[int] = field(default_factory=list)

@dataclass
class K2Mesh:
    mesh_index: int
    name: str
    shader_name: str
    mode: int = 1
    bonelink: int = -1
    bmin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bmax: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    vertices: List[Tuple[float, float, float]] = field(default_factory=list)
    faces: List[Tuple[int, int, int]] = field(default_factory=list)
    normals: List[Tuple[float, float, float]] = field(default_factory=list)
    uv_channels: List[List[Tuple[float, float]]] = field(default_factory=list)
    tangent_channels: List[List[Tuple[float, float, float]]] = field(default_factory=list)
    sign_channels: List[List[int]] = field(default_factory=list)
    color_channels: List[List[Tuple[int, int, int, int]]] = field(default_factory=list)
    single_links: List[int] = field(default_factory=list)
    blended_links: List[K2BlendedLink] = field(default_factory=list)

@dataclass
class K2Plane:
    normal: Tuple[float, float, float]
    dist: float

@dataclass
class K2Edge:
    normal: Tuple[float, float, float]
    point: Tuple[float, float, float]

@dataclass
class K2Surface:
    surf_index: int
    flags: int = 0
    bmin: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bmax: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    planes: List[K2Plane] = field(default_factory=list)
    points: List[Tuple[float, float, float]] = field(default_factory=list)
    edges: List[K2Edge] = field(default_factory=list)
    tris: List[Tuple[int, int, int]] = field(default_factory=list)

@dataclass
class K2ModelData:
    header: K2ModelHeader = field(default_factory=K2ModelHeader)
    bones: List[K2Bone] = field(default_factory=list)
    meshes: List[K2Mesh] = field(default_factory=list)
    surfaces: List[K2Surface] = field(default_factory=list)

@dataclass
class K2ClipHeader:
    version: int = 2
    num_motions: int = 0
    num_frames: int = 0

@dataclass
class K2MotionChannel:
    key_type: int
    float_keys: List[float] = field(default_factory=list)
    byte_keys: List[int] = field(default_factory=list)

@dataclass
class K2BoneMotion:
    bone_index: int
    bone_name: str
    channels: List[K2MotionChannel] = field(default_factory=list)

@dataclass
class K2ClipData:
    header: K2ClipHeader = field(default_factory=K2ClipHeader)
    motions: List[K2BoneMotion] = field(default_factory=list)

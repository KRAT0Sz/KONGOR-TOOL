"""
K2 Blender Clean Architecture Core Package.
Pure Python package for K2 Model, Animation, and XML companion serialization.
Zero bpy dependencies.
"""

from .constants import (
    SMDL_SIGNATURE,
    CLIP_SIGNATURE,
    CURRENT_MODEL_VERSION,
    CURRENT_CLIP_VERSION,
    MeshMode,
    MotionKeyType,
)
from .models import (
    K2ModelData,
    K2ModelHeader,
    K2Bone,
    K2Mesh,
    K2Surface,
    K2ClipData,
    K2ClipHeader,
    K2BoneMotion,
    K2MotionChannel,
)
from .chunk_io import K2ChunkReader, K2ChunkWriter, ChunkIOError
from .math_k2 import Matrix43, euler_yxz_to_quat, quat_to_euler_yxz, calculate_tangent_sign, BoundingBox
from .smdl_reader import read_smdl
from .smdl_writer import write_smdl, split_and_remap_vertices
from .clip_reader import read_clip
from .clip_writer import write_clip
from .xml_companion import (
    K2Material,
    K2MaterialPhase,
    K2Sampler,
    K2ModelDefinition,
    K2AnimationDef,
    read_material_xml,
    write_material_xml,
    read_mdf_xml,
    write_mdf_xml,
)

__all__ = [
    "SMDL_SIGNATURE",
    "CLIP_SIGNATURE",
    "CURRENT_MODEL_VERSION",
    "CURRENT_CLIP_VERSION",
    "MeshMode",
    "MotionKeyType",
    "K2ModelData",
    "K2ModelHeader",
    "K2Bone",
    "K2Mesh",
    "K2Surface",
    "K2ClipData",
    "K2ClipHeader",
    "K2BoneMotion",
    "K2MotionChannel",
    "K2ChunkReader",
    "K2ChunkWriter",
    "ChunkIOError",
    "Matrix43",
    "euler_yxz_to_quat",
    "quat_to_euler_yxz",
    "calculate_tangent_sign",
    "BoundingBox",
    "read_smdl",
    "write_smdl",
    "split_and_remap_vertices",
    "read_clip",
    "write_clip",
    "K2Material",
    "K2MaterialPhase",
    "K2Sampler",
    "K2ModelDefinition",
    "K2AnimationDef",
    "read_material_xml",
    "write_material_xml",
    "read_mdf_xml",
    "write_mdf_xml",
]

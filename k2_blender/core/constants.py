"""
K2 Engine Binary Constants and FourCC Signatures.
Directly mapped from I:\\hon\\hon\\src\\k2 C++ headers.
"""

from enum import IntEnum

# Signatures
SMDL_SIGNATURE = b"SMDL"
CLIP_SIGNATURE = b"CLIP"

# Versions
CURRENT_MODEL_VERSION = 3
CURRENT_CLIP_VERSION = 2

# Mesh Modes (c_mesh.h:25-30)
class MeshMode(IntEnum):
    SKINNED_BLENDED = 1
    SKINNED_NONBLENDED = 2

# Mesh and Surface Flags (c_mesh.h:32-35, c_k2model.h)
MESH_GPU_DEFORM = 1 << 0
MESH_INVIS = 1 << 1
MESH_NORMALS = 1 << 2

SURF_FOLIAGE = 1 << 0
SURF_NOT_SOLID = 1 << 1

# Clip Motion Key Types (c_clip.h:69-82)
class MotionKeyType(IntEnum):
    X = 0
    Y = 1
    Z = 2
    PITCH = 3
    ROLL = 4
    YAW = 5
    VISIBILITY = 6
    SCALEX = 7
    SCALEY = 8
    SCALEZ = 9

NUM_MKEY_TYPES = 10

# Limits
MAX_UV_CHANNELS = 8
MAX_VERTEX_COLOR_CHANNELS = 4
INVALID_BONE = -1

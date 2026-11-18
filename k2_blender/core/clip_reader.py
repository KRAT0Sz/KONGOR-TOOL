"""
CLIP (Animation) Binary Reader.
Parses CLIP v1/v2 binary streams into K2ClipData IR.
Zero bpy dependencies.
"""

import struct
from typing import BinaryIO, Dict
from .chunk_io import K2ChunkReader
from .models import K2ClipData, K2ClipHeader, K2BoneMotion, K2MotionChannel

def read_clip(stream: BinaryIO) -> K2ClipData:
    reader = K2ChunkReader(stream, expected_signature=b"CLIP")
    clip = K2ClipData()
    motions_by_bone: Dict[int, K2BoneMotion] = {}

    for chunk in reader.iter_chunks():
        name, data = chunk.name, chunk.data

        if name == b"head":
            ver, num_motions, num_frames = struct.unpack_from("<3i", data, 0)
            clip.header = K2ClipHeader(
                version=ver,
                num_motions=num_motions,
                num_frames=num_frames,
            )

        elif name == b"bmtn":
            bone_idx, key_type, num_keys, name_len = struct.unpack_from("<3iB", data, 0)
            bone_name_bytes = data[13 : 13 + name_len]
            bone_name = bone_name_bytes.decode("latin1", errors="replace").rstrip("\x00")

            key_offset = 13 + name_len + 1

            if key_type == 6: # MKEY_VISIBILITY (byte keys)
                byte_keys = list(data[key_offset : key_offset + num_keys])
                channel = K2MotionChannel(key_type=key_type, byte_keys=byte_keys)
            else: # float keys
                float_keys = list(struct.unpack_from(f"<{num_keys}f", data, key_offset))
                channel = K2MotionChannel(key_type=key_type, float_keys=float_keys)

            if bone_idx not in motions_by_bone:
                motion = K2BoneMotion(bone_index=bone_idx, bone_name=bone_name)
                motions_by_bone[bone_idx] = motion
                clip.motions.append(motion)

            motions_by_bone[bone_idx].channels.append(channel)

    return clip

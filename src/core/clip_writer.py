"""
CLIP (Animation) Binary Writer.
Serializes K2ClipData IR into CLIP v2 binary format.
Includes constant keyframe compression (c_outclip.cpp:125-169).
"""

import struct
from typing import BinaryIO
from .chunk_io import K2ChunkWriter
from .models import K2ClipData

def write_clip(stream: BinaryIO, clip: K2ClipData) -> None:
    writer = K2ChunkWriter(stream, signature=b"CLIP")

    # 1. 'head' chunk
    h = clip.header
    head_payload = struct.pack("<3i", 2, len(clip.motions), h.num_frames)
    writer.write_chunk(b"head", head_payload)

    # 2. 'bmtn' chunks
    for motion in clip.motions:
        bone_name_bytes = motion.bone_name.encode("latin1", errors="replace")
        name_len = min(len(bone_name_bytes), 255)

        for channel in motion.channels:
            bmtn_payload = bytearray()
            key_type = channel.key_type

            if key_type == 6: # MKEY_VISIBILITY (byte keys)
                keys = channel.byte_keys
                # Constant compression
                if keys and all(k == keys[0] for k in keys):
                    keys_to_write = [keys[0]]
                else:
                    keys_to_write = keys

                num_keys = len(keys_to_write)
                bmtn_payload.extend(struct.pack("<3iB", motion.bone_index, key_type, num_keys, name_len))
                bmtn_payload.extend(bone_name_bytes[:name_len] + b"\x00")
                bmtn_payload.extend(bytes(keys_to_write))

            else: # float keys
                keys = channel.float_keys
                # Constant compression
                if keys and all(abs(k - keys[0]) < 1e-6 for k in keys):
                    keys_to_write = [keys[0]]
                else:
                    keys_to_write = keys

                num_keys = len(keys_to_write)
                bmtn_payload.extend(struct.pack("<3iB", motion.bone_index, key_type, num_keys, name_len))
                bmtn_payload.extend(bone_name_bytes[:name_len] + b"\x00")
                bmtn_payload.extend(struct.pack(f"<{num_keys}f", *keys_to_write))

            writer.write_chunk(b"bmtn", bytes(bmtn_payload))

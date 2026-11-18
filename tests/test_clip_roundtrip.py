import io
import pytest
from src.core.clip_reader import read_clip
from src.core.clip_writer import write_clip

def test_clip_read_synthetic(sample_clip_bytes):
    clip = read_clip(io.BytesIO(sample_clip_bytes))
    
    assert clip.header.version == 2
    assert clip.header.num_motions == 1
    assert clip.header.num_frames == 5
    assert len(clip.motions) == 1
    
    motion = clip.motions[0]
    assert motion.bone_name == "root"
    assert motion.bone_index == 0
    
    # Check all 10 channels
    assert len(motion.channels) == 10
    # Visibility channel (index 6) has byte keys
    assert motion.channels[6].key_type == 6
    assert motion.channels[6].byte_keys == [1]

def test_clip_write_and_read_roundtrip(sample_clip_bytes):
    # 1. Read synthetic clip
    clip1 = read_clip(io.BytesIO(sample_clip_bytes))
    
    # 2. Write to binary stream
    out_stream = io.BytesIO()
    write_clip(out_stream, clip1)
    written_bytes = out_stream.getvalue()
    
    # 3. Read back
    clip2 = read_clip(io.BytesIO(written_bytes))
    
    # 4. Compare
    assert clip2.header.version == clip1.header.version
    assert clip2.header.num_motions == clip1.header.num_motions
    assert clip2.header.num_frames == clip1.header.num_frames
    assert len(clip2.motions) == len(clip1.motions)
    
    m1, m2 = clip1.motions[0], clip2.motions[0]
    assert m1.bone_name == m2.bone_name
    assert m1.bone_index == m2.bone_index
    assert len(m1.channels) == len(m2.channels)
    
    for c1, c2 in zip(m1.channels, m2.channels):
        assert c1.key_type == c2.key_type
        if c1.key_type == 6: # visibility
            assert c1.byte_keys == c2.byte_keys
        else:
            assert len(c1.float_keys) == len(c2.float_keys)
            for k1, k2 in zip(c1.float_keys, c2.float_keys):
                assert pytest.approx(k1, abs=1e-5) == k2

def test_clip_constant_keyframe_compression():
    # If all frames have identical value, writer should compress to 1 key
    from src.core.models import K2ClipData, K2ClipHeader, K2BoneMotion, K2MotionChannel
    
    clip = K2ClipData(
        header=K2ClipHeader(version=2, num_motions=1, num_frames=100),
        motions=[
            K2BoneMotion(
                bone_index=0,
                bone_name="root",
                channels=[
                    K2MotionChannel(key_type=0, float_keys=[5.0] * 100), # constant 5.0 across 100 frames
                    K2MotionChannel(key_type=1, float_keys=[float(i) for i in range(100)]), # varying keys
                ]
            )
        ]
    )
    
    out_stream = io.BytesIO()
    write_clip(out_stream, clip)
    
    # Read back and verify compression
    read_back = read_clip(io.BytesIO(out_stream.getvalue()))
    ch0 = read_back.motions[0].channels[0]
    ch1 = read_back.motions[0].channels[1]
    
    assert len(ch0.float_keys) == 1
    assert ch0.float_keys[0] == 5.0
    assert len(ch1.float_keys) == 100

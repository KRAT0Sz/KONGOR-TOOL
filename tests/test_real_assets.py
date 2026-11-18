"""
Phase 4 Outsider Verification: Integration test against real Heroes of Newerth game assets.
Skips automatically if game build directory is not present on the current runner.
"""

import io
import os
import pytest
from src.core import read_smdl, write_smdl, read_clip, write_clip

HON_DIR = r"I:\hon\hon\build\bin\Debug"

@pytest.fixture
def has_hon_assets():
    return os.path.exists(HON_DIR)

def test_real_model_loading_and_roundtrip(has_hon_assets):
    if not has_hon_assets:
        pytest.skip("Heroes of Newerth assets directory not found")

    model_path = os.path.join(HON_DIR, "game", "buildings", "ascension", "repeater0", "high.model")
    with open(model_path, "rb") as f:
        orig = read_smdl(f)

    assert orig.header.version == 3
    assert len(orig.meshes) >= 1
    assert len(orig.bones) >= 1

    buf = io.BytesIO()
    write_smdl(buf, orig)
    buf.seek(0)
    rt = read_smdl(buf)

    assert rt.header.version == orig.header.version
    assert len(rt.meshes) == len(orig.meshes)
    assert len(rt.bones) == len(orig.bones)
    assert len(rt.meshes[0].vertices) == len(orig.meshes[0].vertices)
    assert len(rt.meshes[0].faces) == len(orig.meshes[0].faces)
    assert len(rt.meshes[0].normals) == len(orig.meshes[0].normals)

def test_real_collision_surface_roundtrip(has_hon_assets):
    if not has_hon_assets:
        pytest.skip("Heroes of Newerth assets directory not found")

    collider_path = os.path.join(
        HON_DIR, "game", "buildings", "colliders", "cylinder_collider", "cylinder_collider.model"
    )
    with open(collider_path, "rb") as f:
        orig = read_smdl(f)

    assert len(orig.surfaces) == 1
    surf = orig.surfaces[0]
    assert len(surf.planes) > 0
    assert len(surf.points) > 0
    assert len(surf.edges) > 0
    assert len(surf.tris) > 0

    buf = io.BytesIO()
    write_smdl(buf, orig)
    buf.seek(0)
    rt = read_smdl(buf)

    assert len(rt.surfaces) == 1
    rt_surf = rt.surfaces[0]
    assert len(rt_surf.planes) == len(surf.planes)
    assert len(rt_surf.points) == len(surf.points)
    assert len(rt_surf.edges) == len(surf.edges)
    assert len(rt_surf.tris) == len(surf.tris)

def test_real_clip_loading_and_roundtrip(has_hon_assets):
    if not has_hon_assets:
        pytest.skip("Heroes of Newerth assets directory not found")

    clip_path = os.path.join(HON_DIR, "game", "buildings", "ascension", "repeater0", "default_1.clip")
    with open(clip_path, "rb") as f:
        orig = read_clip(f)

    assert orig.header.version == 2
    assert orig.header.num_frames > 0
    assert len(orig.motions) > 0

    buf = io.BytesIO()
    write_clip(buf, orig)
    buf.seek(0)
    rt = read_clip(buf)

    assert rt.header.version == orig.header.version
    assert rt.header.num_frames == orig.header.num_frames
    assert len(rt.motions) == len(orig.motions)
    for orig_m, rt_m in zip(orig.motions, rt.motions):
        assert orig_m.bone_name == rt_m.bone_name
        assert len(orig_m.channels) == len(rt_m.channels)

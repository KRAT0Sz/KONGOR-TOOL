import pytest
from src.core.models import VertexAttributes
from src.core.smdl_writer import split_and_remap_vertices

def test_identical_vertices_are_deduplicated():
    # Two vertices with identical pos, normal, uv, color, weights
    verts = [
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            uvs=[(0.5, 0.5)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            uvs=[(0.5, 0.5)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
    ]
    faces = [(0, 1, 0)]
    
    unique_verts, new_faces = split_and_remap_vertices(verts, faces)
    assert len(unique_verts) == 1
    assert new_faces == [(0, 0, 0)]

def test_uv_seam_splits_vertices():
    # Two vertices with same position and normal, but different UVs (UV seam)
    verts = [
        VertexAttributes(
            position=(1.0, 2.0, 3.0),
            normal=(0.0, 1.0, 0.0),
            uvs=[(0.0, 0.0)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
        VertexAttributes(
            position=(1.0, 2.0, 3.0),
            normal=(0.0, 1.0, 0.0),
            uvs=[(1.0, 0.0)], # different UV coordinate!
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
    ]
    faces = [(0, 1, 0)]
    
    unique_verts, new_faces = split_and_remap_vertices(verts, faces)
    # Must NOT merge them!
    assert len(unique_verts) == 2
    assert new_faces == [(0, 1, 0)]

def test_hard_normal_splits_vertices():
    # Same pos and UV, but different normals (hard edge / crease)
    verts = [
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(1.0, 0.0, 0.0),
            uvs=[(0.5, 0.5)],
            tangents=[(0.0, 1.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(0.0, 1.0, 0.0), # different normal
            uvs=[(0.5, 0.5)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 255, 255, 255)],
            weights=[(0, 1.0)]
        ),
    ]
    faces = [(0, 1, 0)]
    unique_verts, new_faces = split_and_remap_vertices(verts, faces)
    assert len(unique_verts) == 2
    assert new_faces == [(0, 1, 0)]

def test_color_difference_splits_vertices():
    # Same pos, normal, UV, but different vertex colors
    verts = [
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            uvs=[(0.0, 0.0)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(255, 0, 0, 255)],
            weights=[(0, 1.0)]
        ),
        VertexAttributes(
            position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            uvs=[(0.0, 0.0)],
            tangents=[(1.0, 0.0, 0.0)],
            signs=[0],
            colors=[(0, 255, 0, 255)], # different color
            weights=[(0, 1.0)]
        ),
    ]
    faces = [(0, 1, 0)]
    unique_verts, new_faces = split_and_remap_vertices(verts, faces)
    assert len(unique_verts) == 2

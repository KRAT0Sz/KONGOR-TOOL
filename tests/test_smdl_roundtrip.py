import io
import pytest
from src.core.smdl_reader import read_smdl
from src.core.smdl_writer import write_smdl

def test_smdl_read_synthetic(sample_smdl_bytes):
    model = read_smdl(io.BytesIO(sample_smdl_bytes))
    
    assert model.header.version == 3
    assert model.header.num_meshes == 1
    assert model.header.num_bones == 1
    assert model.header.num_surfs == 1
    assert len(model.bones) == 1
    assert model.bones[0].name == "root"
    assert len(model.meshes) == 1
    
    mesh = model.meshes[0]
    assert mesh.name == "mesh"
    assert mesh.shader_name == "/test/mat.xml"
    assert len(mesh.vertices) == 3
    assert len(mesh.faces) == 1
    assert mesh.faces[0] == (0, 1, 2)
    assert len(mesh.normals) == 3
    assert len(mesh.uv_channels[0]) == 3
    assert len(mesh.blended_links) == 3
    
    assert len(model.surfaces) == 1
    surf = model.surfaces[0]
    assert len(surf.planes) == 1
    assert len(surf.points) == 3
    assert len(surf.edges) == 3
    assert len(surf.tris) == 1

def test_smdl_write_and_read_roundtrip(sample_smdl_bytes):
    # 1. Read original synthetic model
    model1 = read_smdl(io.BytesIO(sample_smdl_bytes))
    
    # 2. Write model to binary stream
    out_stream = io.BytesIO()
    write_smdl(out_stream, model1)
    written_bytes = out_stream.getvalue()
    
    # 3. Read back written stream
    model2 = read_smdl(io.BytesIO(written_bytes))
    
    # 4. Compare model structures
    assert model2.header.version == model1.header.version
    assert model2.header.num_meshes == model1.header.num_meshes
    assert model2.header.num_bones == model1.header.num_bones
    assert model2.header.num_surfs == model1.header.num_surfs
    
    # Compare bones
    assert len(model2.bones) == len(model1.bones)
    for b1, b2 in zip(model1.bones, model2.bones):
        assert b1.name == b2.name
        assert b1.parent_index == b2.parent_index
        for i in range(12):
            assert pytest.approx(b1.inv_base[i], abs=1e-5) == b2.inv_base[i]
            assert pytest.approx(b1.base[i], abs=1e-5) == b2.base[i]
            
    # Compare meshes
    assert len(model2.meshes) == len(model1.meshes)
    m1, m2 = model1.meshes[0], model2.meshes[0]
    assert m1.name == m2.name
    assert m1.shader_name == m2.shader_name
    assert len(m1.vertices) == len(m2.vertices)
    for v1, v2 in zip(m1.vertices, m2.vertices):
        assert pytest.approx(v1[0], abs=1e-5) == v2[0]
        assert pytest.approx(v1[1], abs=1e-5) == v2[1]
        assert pytest.approx(v1[2], abs=1e-5) == v2[2]
        
    assert m1.faces == m2.faces
    
    # Compare collision surfaces
    assert len(model2.surfaces) == len(model1.surfaces)
    s1, s2 = model1.surfaces[0], model2.surfaces[0]
    assert len(s1.planes) == len(s2.planes)
    assert len(s1.points) == len(s2.points)
    assert len(s1.edges) == len(s2.edges)
    assert s1.tris == s2.tris

def test_smdl_tangent_sign_and_lnk3_specification():
    """Verifies that SMDL v3 writes 'tang', 'sign', and 'lnk3' for skinned meshes."""
    from src.core.models import K2ModelData, K2ModelHeader, K2Mesh, K2Bone, K2BlendedLink
    from src.core.chunk_io import K2ChunkReader

    model = K2ModelData(
        header=K2ModelHeader(version=3, num_meshes=1, num_bones=1),
        bones=[K2Bone(index=0, name="root", parent_index=-1, inv_base=[0.0]*12, base=[0.0]*12)],
        meshes=[
            K2Mesh(
                mesh_index=0,
                name="test_mesh",
                shader_name="material",
                mode=1,
                vertices=[(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)],
                faces=[(0, 1, 2)],
                normals=[(0.0, 0.0, 1.0)] * 3,
                uv_channels=[[(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]],
                tangent_channels=[[(1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)]],
                sign_channels=[[0, 255, 0]],
                blended_links=[
                    K2BlendedLink(weights=[1.0], indexes=[0]),
                    K2BlendedLink(weights=[1.0], indexes=[0]),
                    K2BlendedLink(weights=[1.0], indexes=[0]),
                ]
            )
        ]
    )

    out = io.BytesIO()
    write_smdl(out, model)
    data = out.getvalue()

    # Verify chunk tags
    reader = K2ChunkReader(io.BytesIO(data), expected_signature=b"SMDL")
    chunk_names = [c.name for c in reader.iter_chunks()]
    assert b"lnk3" in chunk_names
    assert b"tang" in chunk_names
    assert b"sign" in chunk_names

    # Read back and verify values
    read_back = read_smdl(io.BytesIO(data))
    rm = read_back.meshes[0]
    assert len(rm.tangent_channels[0]) == 3
    assert rm.tangent_channels[0][0] == (1.0, 0.0, 0.0)
    assert rm.sign_channels[0] == [0, 255, 0]
    assert len(rm.blended_links) == 3

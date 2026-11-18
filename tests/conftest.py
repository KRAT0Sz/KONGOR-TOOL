import io
import struct
import pytest

@pytest.fixture
def sample_smdl_bytes():
    """Generates a minimal valid synthetic SMDL v3 binary stream based on C++ ground truth."""
    stream = io.BytesIO()
    # 4-byte Magic
    stream.write(b"SMDL")

    # 'head' chunk
    # struct modelHeader_t: version=3, numMeshes=1, num_sprites=0, num_surfs=1, numBones=1, bmin=(-10, -10, -10), bmax=(10, 10, 10)
    head_payload = struct.pack(
        "<5i6f",
        3, 1, 0, 1, 1,
        -10.0, -10.0, -10.0,
        10.0, 10.0, 10.0
    )
    stream.write(b"head")
    stream.write(struct.pack("<i", len(head_payload)))
    stream.write(head_payload)

    # 'bone' chunk
    # parentIndex=-1, invBase (12 floats), base (12 floats), cNameLen=4, szBoneName="root\0"
    bone_payload = bytearray()
    bone_payload.extend(struct.pack("<i", -1)) # parentIndex
    inv_base = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 0.0
    )
    base = (
        1.0, 0.0, 0.0,
        0.0, 1.0, 0.0,
        0.0, 0.0, 1.0,
        0.0, 0.0, 0.0
    )
    bone_payload.extend(struct.pack("<12f", *inv_base))
    bone_payload.extend(struct.pack("<12f", *base))
    bone_name = b"root"
    bone_payload.extend(struct.pack("<B", len(bone_name)))
    bone_payload.extend(bone_name + b"\x00")

    stream.write(b"bone")
    stream.write(struct.pack("<i", len(bone_payload)))
    stream.write(bone_payload)

    # 'mesh' chunk
    # mesh_index=0, mode=1 (BLENDED), num_verts=3, bmin=(-5, -5, -5), bmax=(5, 5, 5), bonelink=-1
    # cNameLen=4, cShaderNameLen=13, "mesh\0/test/mat.xml\0"
    mesh_payload = bytearray()
    mesh_name = b"mesh"
    shader_name = b"/test/mat.xml"
    mesh_payload.extend(struct.pack(
        "<3i6fi2B",
        0, 1, 3,
        -5.0, -5.0, -5.0,
        5.0, 5.0, 5.0,
        -1,
        len(mesh_name),
        len(shader_name)
    ))
    mesh_payload.extend(mesh_name + b"\x00")
    mesh_payload.extend(shader_name + b"\x00")

    stream.write(b"mesh")
    stream.write(struct.pack("<i", len(mesh_payload)))
    stream.write(mesh_payload)

    # 'vrts' chunk
    vrts_payload = bytearray()
    vrts_payload.extend(struct.pack("<i", 0)) # mesh_index
    vrts_payload.extend(struct.pack("<3f", 0.0, 0.0, 0.0))
    vrts_payload.extend(struct.pack("<3f", 1.0, 0.0, 0.0))
    vrts_payload.extend(struct.pack("<3f", 0.0, 1.0, 0.0))

    stream.write(b"vrts")
    stream.write(struct.pack("<i", len(vrts_payload)))
    stream.write(vrts_payload)

    # 'face' chunk: mesh_index=0, numFaces=1, faceIndexSize=1
    face_payload = bytearray()
    face_payload.extend(struct.pack("<2ib", 0, 1, 1))
    face_payload.extend(struct.pack("<3B", 0, 1, 2))

    stream.write(b"face")
    stream.write(struct.pack("<i", len(face_payload)))
    stream.write(face_payload)

    # 'texc' chunk: mesh_index=0, channel=0
    texc_payload = bytearray()
    texc_payload.extend(struct.pack("<2i", 0, 0))
    texc_payload.extend(struct.pack("<2f", 0.0, 0.0))
    texc_payload.extend(struct.pack("<2f", 1.0, 0.0))
    texc_payload.extend(struct.pack("<2f", 0.0, 1.0))

    stream.write(b"texc")
    stream.write(struct.pack("<i", len(texc_payload)))
    stream.write(texc_payload)

    # 'nrml' chunk: mesh_index=0
    nrml_payload = bytearray()
    nrml_payload.extend(struct.pack("<i", 0))
    nrml_payload.extend(struct.pack("<3f", 0.0, 0.0, 1.0))
    nrml_payload.extend(struct.pack("<3f", 0.0, 0.0, 1.0))
    nrml_payload.extend(struct.pack("<3f", 0.0, 0.0, 1.0))

    stream.write(b"nrml")
    stream.write(struct.pack("<i", len(nrml_payload)))
    stream.write(nrml_payload)

    # 'lnk1' chunk: mesh_index=0, num_verts=3
    lnk1_payload = bytearray()
    lnk1_payload.extend(struct.pack("<2i", 0, 3))
    for _ in range(3):
        lnk1_payload.extend(struct.pack("<i", 1)) # num_weights
        lnk1_payload.extend(struct.pack("<f", 1.0)) # weight
        lnk1_payload.extend(struct.pack("<i", 0)) # bone index

    stream.write(b"lnk1")
    stream.write(struct.pack("<i", len(lnk1_payload)))
    stream.write(lnk1_payload)

    # 'surf' chunk: 1 plane, 3 points, 3 edges, 1 tri
    surf_payload = bytearray()
    surf_payload.extend(struct.pack(
        "<5i6fi",
        0, 1, 3, 3, 1,
        -5.0, -5.0, -5.0,
        5.0, 5.0, 5.0,
        0
    ))
    # 1 Plane (Ax + By + Cz = D)
    surf_payload.extend(struct.pack("<4f", 0.0, 0.0, 1.0, 0.0))
    # 3 Points
    surf_payload.extend(struct.pack("<3f", 0.0, 0.0, 0.0))
    surf_payload.extend(struct.pack("<3f", 1.0, 0.0, 0.0))
    surf_payload.extend(struct.pack("<3f", 0.0, 1.0, 0.0))
    # 3 Edges (normal 3f, point 3f)
    for _ in range(3):
        surf_payload.extend(struct.pack("<6f", 0.0, 1.0, 0.0, 0.0, 0.0, 0.0))
    # 1 Tri (3 uint indices)
    surf_payload.extend(struct.pack("<3I", 0, 1, 2))

    stream.write(b"surf")
    stream.write(struct.pack("<i", len(surf_payload)))
    stream.write(surf_payload)

    return stream.getvalue()

@pytest.fixture
def sample_clip_bytes():
    """Generates a minimal valid synthetic CLIP v2 binary stream based on C++ ground truth."""
    stream = io.BytesIO()
    stream.write(b"CLIP")

    # 'head' chunk: version=2, numMotions=1, numFrames=5
    head_payload = struct.pack("<3i", 2, 1, 5)
    stream.write(b"head")
    stream.write(struct.pack("<i", len(head_payload)))
    stream.write(head_payload)

    # 10 'bmtn' channels for bone index 0 ("root")
    bone_name = b"root"
    for key_type in range(10):
        bmtn_payload = bytearray()
        if key_type == 6: # MKEY_VISIBILITY
            num_keys = 1 # constant visibility = 1
            bmtn_payload.extend(struct.pack("<3iB", 0, key_type, num_keys, len(bone_name)))
            bmtn_payload.extend(bone_name + b"\x00")
            bmtn_payload.extend(b"\x01")
        else: # float keys
            num_keys = 1 # constant key
            val = 1.0 if key_type in (7, 8, 9) else 0.0 # scale = 1.0, others = 0.0
            bmtn_payload.extend(struct.pack("<3iB", 0, key_type, num_keys, len(bone_name)))
            bmtn_payload.extend(bone_name + b"\x00")
            bmtn_payload.extend(struct.pack("<f", val))

        stream.write(b"bmtn")
        stream.write(struct.pack("<i", len(bmtn_payload)))
        stream.write(bmtn_payload)

    return stream.getvalue()

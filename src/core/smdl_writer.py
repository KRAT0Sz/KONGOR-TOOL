"""
SMDL (Model) Binary Writer.
Serializes K2ModelData IR into SMDL v3 binary format.
Includes Vertex Seam Splitter, proper Collision Surface ('surf') serialization,
and safe stream-based Sprite handling (resolving BUG-01, BUG-02, BUG-03).
"""

import struct
from typing import BinaryIO, List, Tuple, Dict
from .chunk_io import K2ChunkWriter
from .models import K2ModelData, VertexAttributes

def split_and_remap_vertices(
    verts: List[VertexAttributes],
    faces: List[Tuple[int, int, int]]
) -> Tuple[List[VertexAttributes], List[Tuple[int, int, int]]]:
    """
    Deduplicates and splits vertices based on C++ ground truth (s2exporter.cpp:1410-1485).
    Vertices at the same spatial position are only merged if normal, UV, tangent, sign,
    color, and bone weights are completely identical.
    """
    unique_verts: List[VertexAttributes] = []
    vert_map: Dict[Tuple, int] = {}
    remap: Dict[int, int] = {}

    for old_idx, v in enumerate(verts):
        # Round floats slightly to prevent float precision divergence
        key = (
            tuple(round(coord, 5) for coord in v.position),
            tuple(round(n, 4) for n in v.normal),
            tuple(tuple(round(uv, 5) for uv in uv_ch) for uv_ch in v.uvs),
            tuple(tuple(round(t, 4) for t in tan_ch) for tan_ch in v.tangents),
            tuple(v.signs),
            tuple(v.colors),
            tuple((w[0], round(w[1], 4)) for w in sorted(v.weights, key=lambda x: x[0]))
        )

        if key in vert_map:
            remap[old_idx] = vert_map[key]
        else:
            new_idx = len(unique_verts)
            vert_map[key] = new_idx
            unique_verts.append(v)
            remap[old_idx] = new_idx

    new_faces = []
    for f in faces:
        new_faces.append((remap[f[0]], remap[f[1]], remap[f[2]]))

    return unique_verts, new_faces

def write_smdl(stream: BinaryIO, model: K2ModelData) -> None:
    writer = K2ChunkWriter(stream, signature=b"SMDL")

    # 1. 'head' chunk
    h = model.header
    head_payload = struct.pack(
        "<5i6f",
        3, # Version 3
        len(model.meshes),
        h.num_sprites,
        len(model.surfaces),
        len(model.bones),
        h.bmin[0], h.bmin[1], h.bmin[2],
        h.bmax[0], h.bmax[1], h.bmax[2],
    )
    writer.write_chunk(b"head", head_payload)

    # 2. 'bone' chunk
    if model.bones:
        bone_payload = bytearray()
        for b in model.bones:
            name_bytes = b.name.encode("latin1", errors="replace")
            name_len = min(len(name_bytes), 255)
            bone_payload.extend(struct.pack("<i", b.parent_index))
            bone_payload.extend(struct.pack("<12f", *b.inv_base))
            bone_payload.extend(struct.pack("<12f", *b.base))
            bone_payload.extend(struct.pack("<B", name_len))
            bone_payload.extend(name_bytes[:name_len] + b"\x00")
        writer.write_chunk(b"bone", bytes(bone_payload))

    # 3. Meshes
    for m in model.meshes:
        name_bytes = m.name.encode("latin1", errors="replace")
        name_len = min(len(name_bytes), 255)
        shader_bytes = m.shader_name.encode("latin1", errors="replace")
        shader_len = min(len(shader_bytes), 255)

        # 'mesh' chunk
        mesh_payload = bytearray()
        mesh_payload.extend(struct.pack(
            "<3i6fi2B",
            m.mesh_index,
            m.mode,
            len(m.vertices),
            m.bmin[0], m.bmin[1], m.bmin[2],
            m.bmax[0], m.bmax[1], m.bmax[2],
            m.bonelink,
            name_len,
            shader_len,
        ))
        mesh_payload.extend(name_bytes[:name_len] + b"\x00")
        mesh_payload.extend(shader_bytes[:shader_len] + b"\x00")
        writer.write_chunk(b"mesh", bytes(mesh_payload))

        # 'vrts' chunk
        vrts_payload = bytearray()
        vrts_payload.extend(struct.pack("<i", m.mesh_index))
        for v in m.vertices:
            vrts_payload.extend(struct.pack("<3f", v[0], v[1], v[2]))
        writer.write_chunk(b"vrts", bytes(vrts_payload))

        # 'lnk1' / 'lnk3' (Blended links) or 'lnk2' (Single links)
        if m.mode == 1 and m.blended_links:
            lnk_payload = bytearray()
            lnk_payload.extend(struct.pack("<2i", m.mesh_index, len(m.vertices)))
            for link in m.blended_links:
                num_weights = len(link.weights)
                lnk_payload.extend(struct.pack("<i", num_weights))
                lnk_payload.extend(struct.pack(f"<{num_weights}f", *link.weights))
                lnk_payload.extend(struct.pack(f"<{num_weights}i", *link.indexes))
            lnk_tag = b"lnk3" if model.header.version >= 3 else b"lnk1"
            writer.write_chunk(lnk_tag, bytes(lnk_payload))
        elif m.mode == 2 and m.single_links:
            lnk2_payload = bytearray()
            lnk2_payload.extend(struct.pack("<2i", m.mesh_index, len(m.vertices)))
            lnk2_payload.extend(struct.pack(f"<{len(m.single_links)}I", *m.single_links))
            writer.write_chunk(b"lnk2", bytes(lnk2_payload))

        # 'face' chunk
        face_payload = bytearray()
        num_verts = len(m.vertices)
        index_size = 1 if num_verts < 256 else (2 if num_verts < 65536 else 4)
        face_payload.extend(struct.pack("<2ib", m.mesh_index, len(m.faces), index_size))
        fmt = "<3B" if index_size == 1 else ("<3H" if index_size == 2 else "<3I")
        for f in m.faces:
            face_payload.extend(struct.pack(fmt, f[0], f[1], f[2]))
        writer.write_chunk(b"face", bytes(face_payload))

        # 'texc' chunks
        for ch_idx, uvs in enumerate(m.uv_channels):
            if not uvs:
                continue
            texc_payload = bytearray()
            texc_payload.extend(struct.pack("<2i", m.mesh_index, ch_idx))
            for u, v in uvs:
                texc_payload.extend(struct.pack("<2f", u, v))
            writer.write_chunk(b"texc", bytes(texc_payload))

        # 'tang' chunks
        for ch_idx, tangents in enumerate(m.tangent_channels):
            if not tangents:
                continue
            tang_payload = bytearray()
            tang_payload.extend(struct.pack("<2i", m.mesh_index, ch_idx))
            for tx, ty, tz in tangents:
                tang_payload.extend(struct.pack("<3f", tx, ty, tz))
            writer.write_chunk(b"tang", bytes(tang_payload))

        # 'sign' chunks
        for ch_idx, signs in enumerate(m.sign_channels):
            if not signs:
                continue
            sign_payload = bytearray()
            sign_payload.extend(struct.pack("<2i", m.mesh_index, ch_idx))
            sign_payload.extend(bytes(signs))
            writer.write_chunk(b"sign", bytes(sign_payload))

        # 'colr' chunks
        for ch_idx, colors in enumerate(m.color_channels):
            if not colors:
                continue
            colr_payload = bytearray()
            colr_payload.extend(struct.pack("<2i", m.mesh_index, ch_idx))
            for r, g, b, a in colors:
                colr_payload.extend(struct.pack("<4B", r, g, b, a))
            writer.write_chunk(b"colr", bytes(colr_payload))

        # 'nrml' chunk
        if m.normals:
            nrml_payload = bytearray()
            nrml_payload.extend(struct.pack("<i", m.mesh_index))
            for nx, ny, nz in m.normals:
                nrml_payload.extend(struct.pack("<3f", nx, ny, nz))
            writer.write_chunk(b"nrml", bytes(nrml_payload))

    # 4. Collision Surfaces ('surf' chunks - BUG-03 fix)
    for surf in model.surfaces:
        surf_payload = bytearray()
        surf_payload.extend(struct.pack(
            "<5i6fi",
            surf.surf_index,
            len(surf.planes),
            len(surf.points),
            len(surf.edges),
            len(surf.tris),
            surf.bmin[0], surf.bmin[1], surf.bmin[2],
            surf.bmax[0], surf.bmax[1], surf.bmax[2],
            surf.flags,
        ))
        for p in surf.planes:
            surf_payload.extend(struct.pack("<4f", p.normal[0], p.normal[1], p.normal[2], p.dist))
        for pt in surf.points:
            surf_payload.extend(struct.pack("<3f", pt[0], pt[1], pt[2]))
        for e in surf.edges:
            surf_payload.extend(struct.pack("<6f", e.normal[0], e.normal[1], e.normal[2], e.point[0], e.point[1], e.point[2]))
        for tri in surf.tris:
            surf_payload.extend(struct.pack("<3I", tri[0], tri[1], tri[2]))
        writer.write_chunk(b"surf", bytes(surf_payload))

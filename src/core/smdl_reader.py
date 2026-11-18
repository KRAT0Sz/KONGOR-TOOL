"""
SMDL (Model) Binary Reader.
Parses SMDL v1/v3 binary streams into K2ModelData IR.
Zero bpy dependencies.
"""

import io
import struct
from typing import BinaryIO
from .chunk_io import K2ChunkReader
from .models import (
    K2ModelData,
    K2ModelHeader,
    K2Bone,
    K2Mesh,
    K2BlendedLink,
    K2Surface,
    K2Plane,
    K2Edge
)

def read_smdl(stream: BinaryIO) -> K2ModelData:
    reader = K2ChunkReader(stream, expected_signature=b"SMDL")
    model = K2ModelData()
    
    current_mesh = None

    for chunk in reader.iter_chunks():
        name, data = chunk.name, chunk.data
        chunk_stream = io.BytesIO(data)

        if name == b"head":
            # struct modelHeader_t: version, numMeshes, num_sprites, num_surfs, numBones, bmin[3], bmax[3]
            ver, num_meshes, num_sprites, num_surfs, num_bones, min_x, min_y, min_z, max_x, max_y, max_z = struct.unpack(
                "<5i6f", data[:44]
            )
            model.header = K2ModelHeader(
                version=ver,
                num_meshes=num_meshes,
                num_sprites=num_sprites,
                num_surfs=num_surfs,
                num_bones=num_bones,
                bmin=(min_x, min_y, min_z),
                bmax=(max_x, max_y, max_z),
            )

        elif name == b"bone":
            # boneBlock_t: parentIndex (4), invBase (48), base (48), cNameLen (1), szBoneName (cNameLen + 1)
            pos = 0
            bone_idx = len(model.bones)
            while pos < len(data):
                parent_idx, = struct.unpack_from("<i", data, pos)
                inv_base = struct.unpack_from("<12f", data, pos + 4)
                base = struct.unpack_from("<12f", data, pos + 52)
                name_len, = struct.unpack_from("<B", data, pos + 100)
                bone_name_bytes = data[pos + 101 : pos + 101 + name_len]
                bone_name = bone_name_bytes.decode("latin1", errors="replace").rstrip("\x00")
                
                model.bones.append(
                    K2Bone(
                        index=bone_idx,
                        name=bone_name,
                        parent_index=parent_idx,
                        inv_base=inv_base,
                        base=base,
                    )
                )
                bone_idx += 1
                pos += 100 + 1 + name_len + 1

        elif name == b"mesh":
            # SMeshBlock: mesh_index (4), mode (4), num_verts (4), bmin (12), bmax (12), bonelink (4), cNameLen (1), cShaderNameLen (1)
            mesh_idx, mode, num_verts, min_x, min_y, min_z, max_x, max_y, max_z, bonelink, name_len, shader_len = struct.unpack_from(
                "<3i6fi2B", data, 0
            )
            offset = 42
            name_bytes = data[offset : offset + name_len]
            mesh_name = name_bytes.decode("latin1", errors="replace").rstrip("\x00")
            offset += name_len + 1
            shader_bytes = data[offset : offset + shader_len]
            shader_name = shader_bytes.decode("latin1", errors="replace").rstrip("\x00")

            mesh = K2Mesh(
                mesh_index=mesh_idx,
                name=mesh_name,
                shader_name=shader_name,
                mode=mode,
                bonelink=bonelink,
                bmin=(min_x, min_y, min_z),
                bmax=(max_x, max_y, max_z),
            )
            model.meshes.append(mesh)
            current_mesh = mesh

        elif name == b"vrts":
            mesh_idx, = struct.unpack_from("<i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            num_verts = (len(data) - 4) // 12
            verts = []
            for i in range(num_verts):
                vx, vy, vz = struct.unpack_from("<3f", data, 4 + i * 12)
                verts.append((vx, vy, vz))
            target_mesh.vertices = verts

        elif name == b"face":
            mesh_idx, num_faces, index_size = struct.unpack_from("<2ib", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            faces = []
            offset = 9
            fmt = "<3B" if index_size == 1 else ("<3H" if index_size == 2 else "<3I")
            for _ in range(num_faces):
                i0, i1, i2 = struct.unpack_from(fmt, data, offset)
                faces.append((i0, i1, i2))
                offset += index_size * 3
            target_mesh.faces = faces

        elif name == b"texc":
            mesh_idx, channel = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            num_coords = (len(data) - 8) // 8
            uvs = []
            for i in range(num_coords):
                u, v = struct.unpack_from("<2f", data, 8 + i * 8)
                uvs.append((u, v))
            while len(target_mesh.uv_channels) <= channel:
                target_mesh.uv_channels.append([])
            target_mesh.uv_channels[channel] = uvs

        elif name == b"tang":
            mesh_idx, channel = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            num_tangents = (len(data) - 8) // 12
            tangents = []
            for i in range(num_tangents):
                tx, ty, tz = struct.unpack_from("<3f", data, 8 + i * 12)
                tangents.append((tx, ty, tz))
            while len(target_mesh.tangent_channels) <= channel:
                target_mesh.tangent_channels.append([])
            target_mesh.tangent_channels[channel] = tangents

        elif name == b"sign":
            mesh_idx, channel = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            signs = list(data[8:])
            while len(target_mesh.sign_channels) <= channel:
                target_mesh.sign_channels.append([])
            target_mesh.sign_channels[channel] = signs

        elif name == b"colr":
            mesh_idx, channel = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            num_colors = (len(data) - 8) // 4
            colors = []
            for i in range(num_colors):
                r, g, b, a = struct.unpack_from("<4B", data, 8 + i * 4)
                colors.append((r, g, b, a))
            while len(target_mesh.color_channels) <= channel:
                target_mesh.color_channels.append([])
            target_mesh.color_channels[channel] = colors

        elif name == b"nrml":
            mesh_idx, = struct.unpack_from("<i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            num_normals = (len(data) - 4) // 12
            normals = []
            for i in range(num_normals):
                nx, ny, nz = struct.unpack_from("<3f", data, 4 + i * 12)
                normals.append((nx, ny, nz))
            target_mesh.normals = normals

        elif name in (b"lnk1", b"lnk3"):
            mesh_idx, num_verts = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            blended = []
            pos = 8
            for _ in range(num_verts):
                num_weights, = struct.unpack_from("<i", data, pos)
                pos += 4
                weights = list(struct.unpack_from(f"<{num_weights}f", data, pos))
                pos += num_weights * 4
                indexes = list(struct.unpack_from(f"<{num_weights}i", data, pos))
                pos += num_weights * 4
                blended.append(K2BlendedLink(weights=weights, indexes=indexes))
            target_mesh.blended_links = blended

        elif name == b"lnk2":
            mesh_idx, num_verts = struct.unpack_from("<2i", data, 0)
            target_mesh = model.meshes[mesh_idx] if mesh_idx < len(model.meshes) else current_mesh
            single_links = list(struct.unpack_from(f"<{num_verts}I", data, 8))
            target_mesh.single_links = single_links

        elif name == b"surf":
            # surfBlock_t: surf_index, num_planes, num_points, num_edges, num_tris, bmin[3], bmax[3], flags
            surf_idx, num_planes, num_points, num_edges, num_tris, min_x, min_y, min_z, max_x, max_y, max_z, flags = struct.unpack_from(
                "<5i6fi", data, 0
            )
            pos = 48
            planes = []
            for _ in range(num_planes):
                nx, ny, nz, dist = struct.unpack_from("<4f", data, pos)
                planes.append(K2Plane(normal=(nx, ny, nz), dist=dist))
                pos += 16
            
            points = []
            for _ in range(num_points):
                px, py, pz = struct.unpack_from("<3f", data, pos)
                points.append((px, py, pz))
                pos += 12
                
            edges = []
            for _ in range(num_edges):
                nx, ny, nz, px, py, pz = struct.unpack_from("<6f", data, pos)
                edges.append(K2Edge(normal=(nx, ny, nz), point=(px, py, pz)))
                pos += 24
                
            tris = []
            for _ in range(num_tris):
                i0, i1, i2 = struct.unpack_from("<3I", data, pos)
                tris.append((i0, i1, i2))
                pos += 12
                
            model.surfaces.append(
                K2Surface(
                    surf_index=surf_idx,
                    flags=flags,
                    bmin=(min_x, min_y, min_z),
                    bmax=(max_x, max_y, max_z),
                    planes=planes,
                    points=points,
                    edges=edges,
                    tris=tris,
                )
            )

    return model

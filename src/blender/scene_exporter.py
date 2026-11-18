"""
Scene Exporter Adapter for KONGOR TOOL.
Extracts Blender Armatures, Meshes, and Animation into K2ModelData and K2ClipData IR.
"""

import math
import os
from typing import Dict, List, Tuple
import bpy
import bmesh
from mathutils import Matrix, Vector

from ..core import (
    write_smdl,
    write_clip,
    split_and_remap_vertices,
    K2ModelData,
    K2ModelHeader,
    K2Bone,
    K2Mesh,
    K2BlendedLink,
    K2Surface,
    K2Plane,
    K2Edge,
    VertexAttributes,
    K2ClipData,
    K2ClipHeader,
    K2BoneMotion,
    K2MotionChannel,
    BoundingBox,
    calculate_tangent_sign,
    write_material_xml,
    write_mdf_xml,
    K2Material,
    K2MaterialPhase,
    K2Sampler,
    K2ModelDefinition,
    K2AnimationDef,
)

def export_scene_to_k2_model(filepath: str, settings) -> Tuple[bool, str]:
    """Exports Blender scene objects to K2 .model format via Core IR."""
    context = bpy.context
    depsgraph = context.evaluated_depsgraph_get()

    model_dir = os.path.dirname(filepath)
    model_name = os.path.splitext(os.path.basename(filepath))[0]

    # Find primary Armature
    armature_obj = None
    for obj in context.scene.objects:
        if obj.type == "ARMATURE" and not obj.hide_get():
            armature_obj = obj
            break

    # 1. Extract Bones
    bones: List[K2Bone] = []
    bone_index_map: Dict[str, int] = {}

    if armature_obj and getattr(settings, "export_mode", "ANIMATED") == "ANIMATED" and not getattr(settings, "force_static", False):
        arm_data = armature_obj.data
        flatten = getattr(settings, "remove_hierarchy", False)

        for idx, pb in enumerate(arm_data.bones):
            bone_index_map[pb.name] = idx

        for idx, pb in enumerate(arm_data.bones):
            p_idx = -1
            if pb.parent and not flatten and pb.parent.name in bone_index_map:
                p_idx = bone_index_map[pb.parent.name]

            # In K2 Engine: base matrix is bone world rest matrix
            # invBase is its inverse
            mat_world = pb.matrix_local
            mat_inv = mat_world.inverted()

            # Convert 4x4 matrix to K2 3x4 layout (axis[3][3] + pos[3])
            base_tuple = (
                mat_world[0][0], mat_world[0][1], mat_world[0][2],
                mat_world[1][0], mat_world[1][1], mat_world[1][2],
                mat_world[2][0], mat_world[2][1], mat_world[2][2],
                mat_world[0][3], mat_world[1][3], mat_world[2][3],
            )
            inv_base_tuple = (
                mat_inv[0][0], mat_inv[0][1], mat_inv[0][2],
                mat_inv[1][0], mat_inv[1][1], mat_inv[1][2],
                mat_inv[2][0], mat_inv[2][1], mat_inv[2][2],
                mat_inv[0][3], mat_inv[1][3], mat_inv[2][3],
            )

            bones.append(
                K2Bone(
                    index=idx,
                    name=pb.name,
                    parent_index=p_idx,
                    inv_base=inv_base_tuple,
                    base=base_tuple,
                )
            )

    # 2. Extract Meshes and Collision Surfaces
    k2_meshes: List[K2Mesh] = []
    k2_surfaces: List[K2Surface] = []
    overall_bbox = BoundingBox()

    mesh_objects = [
        obj for obj in context.scene.objects
        if obj.type == "MESH" and not obj.hide_get()
    ]

    surf_idx_counter = 0

    for obj in mesh_objects:
        is_collision = (
            getattr(obj.k2_mesh_settings, "is_collision_surface", False)
            or "_surf" in obj.name.lower()
            or "collision" in obj.name.lower()
        )

        eval_obj = obj.evaluated_get(depsgraph)
        temp_mesh = eval_obj.to_mesh()
        
        # Triangulate mesh using BMesh
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(temp_mesh)
        bm.free()

        temp_mesh.calc_normals_split()

        # Handle Collision Surface (BUG-03 fix)
        if is_collision:
            points = [tuple(v.co) for v in temp_mesh.vertices]
            tris = [(p.vertices[0], p.vertices[1], p.vertices[2]) for p in temp_mesh.polygons]

            surf_bbox = BoundingBox()
            for p in points:
                surf_bbox.add_point(p)
                overall_bbox.add_point(p)

            # Generate convex planes from polygon normals
            planes = []
            for poly in temp_mesh.polygons:
                n = tuple(poly.normal)
                p0 = temp_mesh.vertices[poly.vertices[0]].co
                d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
                planes.append(K2Plane(normal=n, dist=d))

            # Generate edges
            edges = []
            for e in temp_mesh.edges:
                v0 = temp_mesh.vertices[e.vertices[0]].co
                v1 = temp_mesh.vertices[e.vertices[1]].co
                edge_dir = (v1 - v0).normalized()
                edges.append(K2Edge(normal=tuple(edge_dir), point=tuple(v0)))

            k2_surfaces.append(
                K2Surface(
                    surf_index=surf_idx_counter,
                    flags=0,
                    bmin=surf_bbox.bmin,
                    bmax=surf_bbox.bmax,
                    planes=planes,
                    points=points,
                    edges=edges,
                    tris=tris,
                )
            )
            surf_idx_counter += 1
            eval_obj.to_mesh_clear()
            continue

        # Handle Visual Mesh
        mesh_bbox = BoundingBox()
        raw_verts: List[VertexAttributes] = []
        raw_faces: List[Tuple[int, int, int]] = []

        uv_layer = temp_mesh.uv_layers.active.data if temp_mesh.uv_layers.active else None
        col_layer = temp_mesh.color_attributes.active.data if temp_mesh.color_attributes.active else None

        # Build vertex attributes per loop
        loop_counter = 0
        for poly in temp_mesh.polygons:
            poly_loops = []
            for loop_idx in poly.loop_indices:
                v_idx = temp_mesh.loops[loop_idx].vertex_index
                v = temp_mesh.vertices[v_idx]
                pos = tuple(v.co)
                normal = tuple(temp_mesh.loops[loop_idx].normal)
                
                mesh_bbox.add_point(pos)
                overall_bbox.add_point(pos)

                uvs = []
                if uv_layer:
                    u, v_coord = uv_layer[loop_idx].uv
                    # Default: invert V for K2
                    uvs.append((u, 1.0 - v_coord))

                colors = []
                if col_layer:
                    c = col_layer[loop_idx].color
                    colors.append((int(c[0] * 255), int(c[1] * 255), int(c[2] * 255), int(c[3] * 255)))

                # Weights
                weights = []
                for g in v.groups:
                    if g.group < len(obj.vertex_groups):
                        vg_name = obj.vertex_groups[g.group].name
                        if vg_name in bone_index_map:
                            weights.append((bone_index_map[vg_name], g.weight))

                # Normalize weights
                total_w = sum(w[1] for w in weights)
                if total_w > 0.0:
                    weights = [(w[0], w[1] / total_w) for w in weights]

                raw_verts.append(
                    VertexAttributes(
                        position=pos,
                        normal=normal,
                        uvs=uvs,
                        tangents=[],
                        signs=[0],
                        colors=colors,
                        weights=weights,
                    )
                )
                poly_loops.append(loop_counter)
                loop_counter += 1

            if len(poly_loops) == 3:
                raw_faces.append((poly_loops[0], poly_loops[1], poly_loops[2]))

        # Apply Vertex Seam Splitting (BUG-02 fix)
        unique_verts, clean_faces = split_and_remap_vertices(raw_verts, raw_faces)

        # Build K2Mesh
        shader_name = f"/materials/{obj.name}.material"
        if obj.data.materials and obj.data.materials[0]:
            shader_name = f"/materials/{obj.data.materials[0].name}.material"

        is_skinned = bool(bones and any(v.weights for v in unique_verts))
        mode = 1 if is_skinned else 2

        k2_mesh = K2Mesh(
            mesh_index=len(k2_meshes),
            name=obj.name,
            shader_name=shader_name,
            mode=mode,
            bonelink=-1,
            bmin=mesh_bbox.bmin,
            bmax=mesh_bbox.bmax,
            vertices=[v.position for v in unique_verts],
            faces=clean_faces,
            normals=[v.normal for v in unique_verts],
            uv_channels=[[v.uvs[0] for v in unique_verts]] if (unique_verts and unique_verts[0].uvs) else [],
            color_channels=[[v.colors[0] for v in unique_verts]] if (unique_verts and unique_verts[0].colors) else [],
        )

        if mode == 1:
            k2_mesh.blended_links = [
                K2BlendedLink(
                    weights=[w[1] for w in v.weights],
                    indexes=[w[0] for w in v.weights]
                )
                for v in unique_verts
            ]
        else:
            k2_mesh.single_links = [
                (v.weights[0][0] if v.weights else 0) for v in unique_verts
            ]

        k2_meshes.append(k2_mesh)
        eval_obj.to_mesh_clear()

    # 3. Assemble Model Data and Write
    model_data = K2ModelData(
        header=K2ModelHeader(
            version=3,
            num_meshes=len(k2_meshes),
            num_sprites=0,
            num_surfs=len(k2_surfaces),
            num_bones=len(bones),
            bmin=overall_bbox.bmin if not overall_bbox.is_empty() else (-1.0, -1.0, -1.0),
            bmax=overall_bbox.bmax if not overall_bbox.is_empty() else (1.0, 1.0, 1.0),
        ),
        bones=bones,
        meshes=k2_meshes,
        surfaces=k2_surfaces,
    )

    with open(filepath, "wb") as f:
        write_smdl(f, model_data)

    # 4. Optional Companion Files (.material and .mdf)
    if getattr(settings, "export_materials", True):
        for mesh in k2_meshes:
            mat_filename = os.path.join(model_dir, f"{mesh.name}.material")
            mat = K2Material(
                name=mesh.name,
                phases=[
                    K2MaterialPhase(
                        name="color",
                        lighting_spec="default",
                        samplers=[
                            K2Sampler(name="diffuse", texture_path=f"{mesh.name}_color.dds"),
                            K2Sampler(name="normalmap", texture_path=f"{mesh.name}_norm.dds"),
                        ]
                    )
                ]
            )
            with open(mat_filename, "w", encoding="utf-8") as f:
                f.write(write_material_xml(mat))

    if getattr(settings, "export_model_def", True):
        mdf_filename = os.path.join(model_dir, f"{model_name}.mdf")
        mdf = K2ModelDefinition(
            model_file=f"{model_name}.model",
            default_skin="default",
            anims=[K2AnimationDef(name="idle", clip_file=f"{model_name}_idle.clip", loop=True, fps=30.0)]
        )
        with open(mdf_filename, "w", encoding="utf-8") as f:
            f.write(write_mdf_xml(mdf))

    return True, f"Successfully exported {len(k2_meshes)} meshes and {len(bones)} bones."

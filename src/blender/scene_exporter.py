"""
KONGOR TOOL - Clean Scene Exporter
Exports Blender Armatures, Meshes, Collision Surfaces, and Animations to K2 Engine format.
Uses Pure Python Core IR and Ground Truth C++ specs. Zero legacy dependencies.
"""

import math
import os
from typing import Dict, List, Optional, Tuple
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
    Matrix43,
    quat_to_euler_yxz,
    write_material_xml,
    write_mdf_xml,
    K2Material,
    K2MaterialPhase,
    K2Sampler,
    K2ModelDefinition,
    K2AnimationDef,
)

def export_k2_model_file(
    filepath: str,
    context: bpy.types.Context,
    settings=None,
) -> Tuple[bool, str]:
    """Exports Blender scene objects to K2 .model format (SMDL v3)."""
    depsgraph = context.evaluated_depsgraph_get()
    model_dir = os.path.dirname(filepath)
    model_name = os.path.splitext(os.path.basename(filepath))[0]

    flip_v = getattr(settings, "flip_v", True) if settings else True
    apply_modifiers = getattr(settings, "apply_modifiers", True) if settings else True
    export_materials = getattr(settings, "export_materials", True) if settings else True
    export_mdf = getattr(settings, "export_mdf", True) if settings else True

    # 1. Locate Primary Armature
    armature_obj = None
    if context.active_object and context.active_object.type == "ARMATURE":
        armature_obj = context.active_object
    else:
        for obj in context.scene.objects:
            if obj.type == "ARMATURE" and not obj.hide_get():
                armature_obj = obj
                break

    bones: List[K2Bone] = []
    bone_name_to_index: Dict[str, int] = {}

    if armature_obj:
        arm_bones = armature_obj.data.bones
        for idx, b in enumerate(arm_bones):
            bone_name_to_index[b.name] = idx

        for idx, b in enumerate(arm_bones):
            parent_idx = -1
            if b.parent and b.parent.name in bone_name_to_index:
                parent_idx = bone_name_to_index[b.parent.name]

            # In K2 Engine: base is bone world rest matrix (3x4), inv_base is its inverse
            m = b.matrix_local
            axis_x = (m[0][0], m[1][0], m[2][0])
            axis_y = (m[0][1], m[1][1], m[2][1])
            axis_z = (m[0][2], m[1][2], m[2][2])
            pos = (m[0][3], m[1][3], m[2][3])

            mat43 = Matrix43(axis_x=axis_x, axis_y=axis_y, axis_z=axis_z, pos=pos)
            inv_mat43 = mat43.inverse()

            bones.append(
                K2Bone(
                    index=idx,
                    name=b.name,
                    parent_index=parent_idx,
                    inv_base=inv_mat43.to_flat_floats(),
                    base=mat43.to_flat_floats(),
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

    surf_counter = 0

    for obj in mesh_objects:
        is_collision = (
            getattr(obj.kongor, "is_collision_surface", False)
            or "_surf" in obj.name.lower()
            or "collision" in obj.name.lower()
        )

        eval_obj = obj.evaluated_get(depsgraph) if apply_modifiers else obj
        temp_mesh = eval_obj.to_mesh()

        # Ensure all polygons are triangles
        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(temp_mesh)
        bm.free()

        # Handle Collision Polyhedra (BUG-03 Ground Truth)
        if is_collision:
            points = [tuple(v.co) for v in temp_mesh.vertices]
            tris = [(p.vertices[0], p.vertices[1], p.vertices[2]) for p in temp_mesh.polygons]

            surf_bbox = BoundingBox()
            for p in points:
                surf_bbox.add_point(p)
                overall_bbox.add_point(p)

            # Generate bounding planes: n . (p - p0) = 0 => n.p - d = 0 => d = n.p0
            planes: List[K2Plane] = []
            for poly in temp_mesh.polygons:
                n = tuple(poly.normal)
                p0 = temp_mesh.vertices[poly.vertices[0]].co
                d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
                planes.append(K2Plane(normal=n, dist=d))

            # Generate bounding edges
            edges: List[K2Edge] = []
            for e in temp_mesh.edges:
                v0 = temp_mesh.vertices[e.vertices[0]].co
                v1 = temp_mesh.vertices[e.vertices[1]].co
                edge_dir = (v1 - v0).normalized() if (v1 - v0).length > 1e-6 else Vector((1.0, 0.0, 0.0))
                edges.append(K2Edge(normal=tuple(edge_dir), point=tuple(v0)))

            k2_surfaces.append(
                K2Surface(
                    surf_index=surf_counter,
                    flags=0,
                    bmin=surf_bbox.bmin,
                    bmax=surf_bbox.bmax,
                    planes=planes,
                    points=points,
                    edges=edges,
                    tris=tris,
                )
            )
            surf_counter += 1
            if apply_modifiers:
                eval_obj.to_mesh_clear()
            continue

        # Handle Visual Geometry Mesh
        mesh_bbox = BoundingBox()
        raw_verts: List[VertexAttributes] = []
        raw_faces: List[Tuple[int, int, int]] = []

        uv_layer = temp_mesh.uv_layers.active.data if temp_mesh.uv_layers.active else None
        col_layer = temp_mesh.color_attributes.active.data if temp_mesh.color_attributes.active else None

        loop_counter = 0
        for poly in temp_mesh.polygons:
            poly_loops: List[int] = []
            for loop_idx in poly.loop_indices:
                v_idx = temp_mesh.loops[loop_idx].vertex_index
                v = temp_mesh.vertices[v_idx]
                pos = tuple(v.co)
                normal = tuple(temp_mesh.loops[loop_idx].normal)

                mesh_bbox.add_point(pos)
                overall_bbox.add_point(pos)

                uvs: List[Tuple[float, float]] = []
                if uv_layer:
                    u, v_coord = uv_layer[loop_idx].uv
                    uvs.append((u, (1.0 - v_coord) if flip_v else v_coord))

                colors: List[Tuple[int, int, int, int]] = []
                if col_layer:
                    c = col_layer[loop_idx].color
                    colors.append((
                        int(c[0] * 255),
                        int(c[1] * 255),
                        int(c[2] * 255),
                        int(c[3] * 255) if len(c) > 3 else 255
                    ))

                # Extract bone weights
                weights: List[Tuple[int, float]] = []
                for g in v.groups:
                    if g.group < len(obj.vertex_groups):
                        vg_name = obj.vertex_groups[g.group].name
                        if vg_name in bone_name_to_index:
                            weights.append((bone_name_to_index[vg_name], g.weight))

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

        # Apply C++ Ground Truth Vertex Seam Splitting (BUG-02 fix)
        unique_verts, clean_faces = split_and_remap_vertices(raw_verts, raw_faces)

        # Shader Name
        shader_name = f"/materials/{obj.name}.material"
        if obj.data.materials and obj.data.materials[0]:
            shader_name = f"/materials/{obj.data.materials[0].name}.material"

        rigid_link = getattr(obj.kongor, "bonelink", -1)
        has_skin_weights = bool(bones and any(v.weights for v in unique_verts))
        mode = 1 if has_skin_weights else (2 if rigid_link >= 0 else 0)

        k2_mesh = K2Mesh(
            mesh_index=len(k2_meshes),
            name=obj.name,
            shader_name=shader_name,
            mode=mode,
            bonelink=rigid_link,
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
        elif mode == 2:
            k2_mesh.single_links = [
                (v.weights[0][0] if v.weights else rigid_link) for v in unique_verts
            ]

        k2_meshes.append(k2_mesh)
        if apply_modifiers:
            eval_obj.to_mesh_clear()

    # 3. Assemble and Write K2ModelData
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

    # 4. Optional XML Companions (.material and .mdf)
    if export_materials:
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

    if export_mdf:
        mdf_filename = os.path.join(model_dir, f"{model_name}.mdf")
        mdf = K2ModelDefinition(
            model_file=f"{model_name}.model",
            default_skin="default",
            anims=[K2AnimationDef(name="idle", clip_file=f"{model_name}_idle.clip", loop=True, fps=30.0)]
        )
        with open(mdf_filename, "w", encoding="utf-8") as f:
            f.write(write_mdf_xml(mdf))

    return True, f"Successfully exported {len(k2_meshes)} meshes, {len(k2_surfaces)} collision surfaces, and {len(bones)} bones."

def export_k2_clip_file(
    filepath: str,
    context: bpy.types.Context,
    armature_obj: bpy.types.Object,
    settings=None,
) -> Tuple[bool, str]:
    """Exports animation from a Blender Armature into K2 .clip format (CLIP v2)."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        return False, "An active Armature object is required for exporting .clip animation."

    frame_start = getattr(settings, "frame_start", context.scene.frame_start) if settings else context.scene.frame_start
    frame_end = getattr(settings, "frame_end", context.scene.frame_end) if settings else context.scene.frame_end
    num_frames = max(1, frame_end - frame_start + 1)

    arm_bones = armature_obj.data.bones
    if not arm_bones:
        return False, "Armature contains no bones to animate."

    # Backup current frame
    orig_frame = context.scene.frame_current

    # Collect per-bone channel frames
    bone_channels: Dict[str, Dict[int, List[float]]] = {
        b.name: {i: [] for i in (0, 1, 2, 3, 4, 5, 7, 8, 9)}
        for b in arm_bones
    }

    try:
        for f in range(frame_start, frame_end + 1):
            context.scene.frame_set(f)
            for b in arm_bones:
                pb = armature_obj.pose.bones.get(b.name)
                if not pb:
                    continue

                # Relative pose matrix to parent
                if pb.parent:
                    rel_mat = pb.parent.matrix.inverted() @ pb.matrix
                else:
                    rel_mat = pb.matrix

                loc = rel_mat.to_translation()
                rot_q = rel_mat.to_quaternion()
                pitch_deg, roll_deg, yaw_deg = quat_to_euler_yxz(rot_q.x, rot_q.y, rot_q.z, rot_q.w)
                scale = rel_mat.to_scale()

                ch = bone_channels[b.name]
                ch[0].append(loc.x)
                ch[1].append(loc.y)
                ch[2].append(loc.z)
                ch[3].append(pitch_deg)
                ch[4].append(roll_deg)
                ch[5].append(yaw_deg)
                ch[7].append(scale.x)
                ch[8].append(scale.y)
                ch[9].append(scale.z)

    finally:
        context.scene.frame_set(orig_frame)

    # Build K2BoneMotion blocks
    motions: List[K2BoneMotion] = []
    for idx, b in enumerate(arm_bones):
        ch_dict = bone_channels[b.name]
        channels = [
            K2MotionChannel(key_type=kt, float_keys=ch_dict[kt])
            for kt in (0, 1, 2, 3, 4, 5, 7, 8, 9)
        ]
        motions.append(
            K2BoneMotion(
                bone_index=idx,
                bone_name=b.name,
                channels=channels,
            )
        )

    clip_data = K2ClipData(
        header=K2ClipHeader(
            version=2,
            num_motions=len(motions),
            num_frames=num_frames,
        ),
        motions=motions,
    )

    with open(filepath, "wb") as f:
        write_clip(f, clip_data)

    return True, f"Successfully exported clip with {num_frames} frames across {len(motions)} bones."

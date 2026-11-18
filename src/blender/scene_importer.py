"""
KONGOR TOOL - Scene Importer
Builds Blender Armature, Meshes, and Actions from K2ModelData and K2ClipData IR.
"""

import math
import os
from typing import Dict, List, Optional
import bpy
from mathutils import Matrix, Vector, Quaternion

from ..core import read_smdl, read_clip, K2ModelData, K2ClipData, Matrix43, euler_yxz_to_quat
from .texture_manager import build_k2_shader_material

def import_k2_model_file(
    filepath: str,
    flip_v: bool = True,
    build_materials: bool = True,
    bones_in_front: bool = True,
    show_bone_names: bool = False,
) -> bpy.types.Object:
    """Reads a K2 .model file into Blender scene objects."""
    with open(filepath, "rb") as stream:
        model = read_smdl(stream)

    base_dir = os.path.dirname(filepath)
    model_name = os.path.splitext(os.path.basename(filepath))[0]

    armature_obj = None
    bone_name_by_index: Dict[int, str] = {}

    # 1. Armature & Skeleton Construction
    if model.bones:
        armature_data = bpy.data.armatures.new(name=f"{model_name}_Skeleton")
        armature_data.show_names = show_bone_names
        armature_obj = bpy.data.objects.new(name=f"{model_name}_Skeleton", object_data=armature_data)
        armature_obj.show_in_front = bones_in_front
        bpy.context.collection.objects.link(armature_obj)

        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = armature_data.edit_bones

        # Determine reference bone scale from model dimensions
        bmin = model.header.bmin
        bmax = model.header.bmax
        model_dim = max(
            abs(bmax[0] - bmin[0]),
            abs(bmax[1] - bmin[1]),
            abs(bmax[2] - bmin[2]),
            1.0,
        )
        default_bone_len = max(model_dim * 0.05, 2.0)

        # Precompute positions and hierarchy for intelligent bone length calculation
        positions: Dict[int, Vector] = {}
        children_map: Dict[int, List[int]] = {b.index: [] for b in model.bones}
        for bone in model.bones:
            mat = Matrix43.from_flat_floats(bone.base)
            positions[bone.index] = Vector(mat.pos)
            if bone.parent_index >= 0 and bone.parent_index in children_map:
                children_map[bone.parent_index].append(bone.index)

        for bone in model.bones:
            bone_name_by_index[bone.index] = bone.name
            eb = edit_bones.new(bone.name)
            eb.use_deform = True

            mat = Matrix43.from_flat_floats(bone.base)
            m4 = Matrix((
                (mat.axis_x[0], mat.axis_y[0], mat.axis_z[0], mat.pos[0]),
                (mat.axis_x[1], mat.axis_y[1], mat.axis_z[1], mat.pos[1]),
                (mat.axis_x[2], mat.axis_y[2], mat.axis_z[2], mat.pos[2]),
                (0.0, 0.0, 0.0, 1.0),
            ))

            head_pos = positions[bone.index]
            child_dists = [
                (positions[c_idx] - head_pos).length
                for c_idx in children_map.get(bone.index, [])
                if (positions[c_idx] - head_pos).length > 0.05
            ]
            if child_dists:
                bone_len = min(child_dists)
            elif bone.parent_index >= 0 and bone.parent_index in positions:
                p_dist = (head_pos - positions[bone.parent_index]).length
                bone_len = max(p_dist * 0.7, default_bone_len * 0.5) if p_dist > 0.05 else default_bone_len
            else:
                bone_len = default_bone_len

            bone_len = max(bone_len, 0.5)

            eb.head = head_pos
            tail_dir = Vector(mat.axis_y)
            if tail_dir.length < 1e-4:
                tail_dir = Vector((0.0, 1.0, 0.0))
            eb.tail = eb.head + tail_dir.normalized() * bone_len
            eb.matrix = m4
            eb.length = bone_len

        for bone in model.bones:
            if bone.parent_index >= 0 and bone.parent_index in bone_name_by_index:
                parent_name = bone_name_by_index[bone.parent_index]
                if parent_name in edit_bones and bone.name in edit_bones:
                    edit_bones[bone.name].parent = edit_bones[parent_name]

        bpy.ops.object.mode_set(mode="OBJECT")

    # 2. Geometry Meshes
    for mesh in model.meshes:
        mesh_data = bpy.data.meshes.new(name=mesh.name)
        mesh_obj = bpy.data.objects.new(name=mesh.name, object_data=mesh_data)
        bpy.context.collection.objects.link(mesh_obj)

        verts = [Vector(v) for v in mesh.vertices]
        mesh_data.from_pydata(verts, [], mesh.faces)
        mesh_data.update()

        # UV Coordinates
        if mesh.uv_channels and mesh.uv_channels[0]:
            uv_layer = mesh_data.uv_layers.new(name="UVMap")
            uvs = mesh.uv_channels[0]
            for poly in mesh_data.polygons:
                for loop_idx in poly.loop_indices:
                    v_idx = mesh_data.loops[loop_idx].vertex_index
                    if v_idx < len(uvs):
                        u, v_coord = uvs[v_idx]
                        uv_layer.data[loop_idx].uv = (u, (1.0 - v_coord) if flip_v else v_coord)

        # Normals
        if mesh.normals and len(mesh.normals) == len(mesh.vertices):
            mesh_data.normals_split_custom_set_from_vertices([Vector(n) for n in mesh.normals])

        # Colors
        if mesh.color_channels and mesh.color_channels[0]:
            color_layer = mesh_data.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
            colors = mesh.color_channels[0]
            for poly in mesh_data.polygons:
                for loop_idx in poly.loop_indices:
                    v_idx = mesh_data.loops[loop_idx].vertex_index
                    if v_idx < len(colors):
                        r, g, b, a = colors[v_idx]
                        color_layer.data[loop_idx].color = (r / 255.0, g / 255.0, b / 255.0, a / 255.0)

        # Materials
        if build_materials and mesh.shader_name:
            mat_stem = os.path.splitext(os.path.basename(mesh.shader_name))[0] or mesh.name
            mat = build_k2_shader_material(mat_stem, base_dir, mesh.shader_name)
            mesh_data.materials.append(mat)

        # Skinning & Vertex Groups
        if armature_obj:
            mesh_obj.parent = armature_obj
            mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
            mod.object = armature_obj

            if mesh.mode == 1 and mesh.blended_links:
                for v_idx, link in enumerate(mesh.blended_links):
                    for b_idx, weight in zip(link.indexes, link.weights):
                        if weight > 0.0 and b_idx in bone_name_by_index:
                            b_name = bone_name_by_index[b_idx]
                            vg = mesh_obj.vertex_groups.get(b_name) or mesh_obj.vertex_groups.new(name=b_name)
                            vg.add([v_idx], weight, "ADD")
            elif mesh.mode == 2 and mesh.single_links:
                for v_idx, b_idx in enumerate(mesh.single_links):
                    if b_idx in bone_name_by_index:
                        b_name = bone_name_by_index[b_idx]
                        vg = mesh_obj.vertex_groups.get(b_name) or mesh_obj.vertex_groups.new(name=b_name)
                        vg.add([v_idx], 1.0, "ADD")
            elif mesh.bonelink >= 0 and mesh.bonelink in bone_name_by_index:
                b_name = bone_name_by_index[mesh.bonelink]
                vg = mesh_obj.vertex_groups.new(name=b_name)
                vg.add(list(range(len(mesh.vertices))), 1.0, "ADD")

    # 3. Collision Polyhedra
    for surf in model.surfaces:
        surf_mesh = bpy.data.meshes.new(name=f"{model_name}_Collision_{surf.surf_index}")
        surf_obj = bpy.data.objects.new(name=f"{model_name}_Collision_{surf.surf_index}", object_data=surf_mesh)
        bpy.context.collection.objects.link(surf_obj)

        surf_mesh.from_pydata([Vector(p) for p in surf.points], [], surf.tris)
        surf_mesh.update()
        surf_obj.kongor.is_collision_surface = True

        if armature_obj:
            surf_obj.parent = armature_obj

    return armature_obj or (mesh_obj if model.meshes else None)

def _get_or_create_fcurve(
    action: bpy.types.Action,
    datablock: bpy.types.ID,
    data_path: str,
    index: int,
    group_name: str = "",
) -> bpy.types.FCurve:
    """Creates or ensures an FCurve in both modern Blender 5.0+ (Slotted Actions) and legacy Blender 4.x."""
    if hasattr(action, "fcurve_ensure_for_datablock"):
        return action.fcurve_ensure_for_datablock(datablock, data_path, index=index, group_name=group_name)
    elif hasattr(action, "fcurves"):
        fc = action.fcurves.find(data_path=data_path, index=index)
        if fc is None:
            fc = action.fcurves.new(data_path=data_path, index=index, action_group=group_name)
        return fc
    else:
        layer = action.layers[0] if action.layers else action.layers.new(name="Layer")
        strip = layer.strips[0] if layer.strips else layer.strips.new(type="KEYFRAME")
        slot = action.slots[0] if action.slots else action.slots.new(target_id_type="OBJECT")
        cb = strip.channelbag(slot)
        fc = cb.fcurves.find(data_path=data_path, index=index)
        if fc is None:
            fc = cb.fcurves.new(data_path=data_path, index=index)
        return fc

def import_k2_clip_file(filepath: str, armature_obj: bpy.types.Object) -> Optional[bpy.types.Action]:
    """Reads a K2 .clip file into a Blender Action with exact relative-to-rest pose transformations."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        raise ValueError("An active Armature object is required to import animation clips.")

    with open(filepath, "rb") as stream:
        clip = read_clip(stream)

    clip_name = os.path.splitext(os.path.basename(filepath))[0]
    action = bpy.data.actions.new(name=clip_name)

    if not armature_obj.animation_data:
        armature_obj.animation_data_create()
    armature_obj.animation_data.action = action

    arm_bones = armature_obj.data.bones
    num_frames = clip.header.num_frames

    # Precompute B_rel_rest inverse for each bone to transform from parent-space to pose bone matrix_basis
    inv_rel_rest_map: Dict[str, Matrix] = {}
    for b in arm_bones:
        if b.parent:
            b_rel_rest = b.parent.matrix_local.inverted() @ b.matrix_local
        else:
            b_rel_rest = b.matrix_local.copy()
        inv_rel_rest_map[b.name] = b_rel_rest.inverted()

    for motion in clip.motions:
        bone_name = motion.bone_name
        if bone_name not in arm_bones:
            continue

        inv_b_rel = inv_rel_rest_map[bone_name]

        # Map channel key types: 0,1,2 = pos, 3,4,5 = pitch,roll,yaw, 7,8,9 = scale
        ch_map = {ch.key_type: ch.float_keys for ch in motion.channels}
        kx = ch_map.get(0, [0.0])
        ky = ch_map.get(1, [0.0])
        kz = ch_map.get(2, [0.0])
        k_pitch = ch_map.get(3, [0.0])
        k_roll = ch_map.get(4, [0.0])
        k_yaw = ch_map.get(5, [0.0])
        k_sx = ch_map.get(7, [1.0])
        k_sy = ch_map.get(8, [1.0])
        k_sz = ch_map.get(9, [1.0])

        len_x = len(kx)
        len_y = len(ky)
        len_z = len(kz)
        len_p = len(k_pitch)
        len_r = len(k_roll)
        len_yw = len(k_yaw)
        len_sx = len(k_sx)
        len_sy = len(k_sy)
        len_sz = len(k_sz)

        pb = armature_obj.pose.bones.get(bone_name)
        if pb:
            pb.rotation_mode = "QUATERNION"

        loc_keys: List[List[float]] = [[], [], []]
        rot_keys: List[List[float]] = [[], [], [], []]
        scale_keys: List[List[float]] = [[], [], []]

        for f in range(num_frames):
            pos = (kx[f % len_x], ky[f % len_y], kz[f % len_z])
            pitch = k_pitch[f % len_p]
            roll = k_roll[f % len_r]
            yaw = k_yaw[f % len_yw]
            sx = k_sx[f % len_sx]
            sy = k_sy[f % len_sy]
            sz = k_sz[f % len_sz]

            qx, qy, qz, qw = euler_yxz_to_quat(pitch, roll, yaw)
            quat_k2 = Quaternion((qw, qx, qy, qz))

            T = Matrix.Translation(Vector(pos))
            R = quat_k2.to_matrix().to_4x4()
            S = Matrix.Diagonal(Vector((sx, sy, sz, 1.0)))
            M_k2 = T @ R @ S

            # matrix_basis = inv(B_rel_rest) * M_k2
            matrix_basis = inv_b_rel @ M_k2
            b_loc, b_rot, b_scale = matrix_basis.decompose()

            frame_num = float(f + 1)
            loc_keys[0].extend([frame_num, b_loc.x])
            loc_keys[1].extend([frame_num, b_loc.y])
            loc_keys[2].extend([frame_num, b_loc.z])

            rot_keys[0].extend([frame_num, b_rot.w])
            rot_keys[1].extend([frame_num, b_rot.x])
            rot_keys[2].extend([frame_num, b_rot.y])
            rot_keys[3].extend([frame_num, b_rot.z])

            scale_keys[0].extend([frame_num, b_scale.x])
            scale_keys[1].extend([frame_num, b_scale.y])
            scale_keys[2].extend([frame_num, b_scale.z])

        path_loc = f'pose.bones["{bone_name}"].location'
        path_rot = f'pose.bones["{bone_name}"].rotation_quaternion'
        path_scale = f'pose.bones["{bone_name}"].scale'

        for i in range(3):
            fc = _get_or_create_fcurve(action, armature_obj, path_loc, i, group_name=bone_name)
            fc.keyframe_points.add(num_frames)
            fc.keyframe_points.foreach_set("co", loc_keys[i])
            fc.update()

        for i in range(4):
            fc = _get_or_create_fcurve(action, armature_obj, path_rot, i, group_name=bone_name)
            fc.keyframe_points.add(num_frames)
            fc.keyframe_points.foreach_set("co", rot_keys[i])
            fc.update()

        for i in range(3):
            fc = _get_or_create_fcurve(action, armature_obj, path_scale, i, group_name=bone_name)
            fc.keyframe_points.add(num_frames)
            fc.keyframe_points.foreach_set("co", scale_keys[i])
            fc.update()

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = num_frames
    return action

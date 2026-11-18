"""
KONGOR TOOL - Scene Importer
Builds Blender Armature, Meshes, and Actions from K2ModelData and K2ClipData IR.
"""

import math
import os
from typing import Dict, Optional
import bpy
from mathutils import Vector

from ..core import read_smdl, read_clip, K2ModelData, K2ClipData, Matrix43
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

        for bone in model.bones:
            bone_name_by_index[bone.index] = bone.name
            eb = edit_bones.new(bone.name)
            eb.use_deform = True

            mat = Matrix43.from_flat_floats(bone.base)
            eb.head = Vector(mat.pos)
            tail_dir = Vector(mat.axis_y)
            if tail_dir.length < 1e-4:
                tail_dir = Vector((0.0, 1.0, 0.0))
            eb.tail = eb.head + tail_dir.normalized() * 0.1

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

def import_k2_clip_file(filepath: str, armature_obj: bpy.types.Object) -> Optional[bpy.types.Action]:
    """Reads a K2 .clip file into a Blender Action assigned to the specified armature."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        raise ValueError("An active Armature object is required to import animation clips.")

    with open(filepath, "rb") as stream:
        clip = read_clip(stream)

    clip_name = os.path.splitext(os.path.basename(filepath))[0]
    action = bpy.data.actions.new(name=clip_name)

    if not armature_obj.animation_data:
        armature_obj.animation_data_create()
    armature_obj.animation_data.action = action

    for motion in clip.motions:
        bone_name = motion.bone_name
        path_loc = f'pose.bones["{bone_name}"].location'
        path_rot = f'pose.bones["{bone_name}"].rotation_euler'
        path_scale = f'pose.bones["{bone_name}"].scale'

        for channel in motion.channels:
            kt = channel.key_type
            keys = channel.float_keys

            if kt in (0, 1, 2):
                fc = action.fcurves.new(data_path=path_loc, index=kt)
                if len(keys) == 1:
                    fc.keyframe_points.insert(1, keys[0])
                else:
                    for idx, val in enumerate(keys):
                        fc.keyframe_points.insert(idx + 1, val)

            elif kt in (3, 4, 5):
                axis_idx = 0 if kt == 3 else (1 if kt == 4 else 2)
                fc = action.fcurves.new(data_path=path_rot, index=axis_idx)
                if len(keys) == 1:
                    fc.keyframe_points.insert(1, math.radians(keys[0]))
                else:
                    for idx, val in enumerate(keys):
                        fc.keyframe_points.insert(idx + 1, math.radians(val))

            elif kt in (7, 8, 9):
                fc = action.fcurves.new(data_path=path_scale, index=kt - 7)
                if len(keys) == 1:
                    fc.keyframe_points.insert(1, keys[0])
                else:
                    for idx, val in enumerate(keys):
                        fc.keyframe_points.insert(idx + 1, val)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = clip.header.num_frames
    return action

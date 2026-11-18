"""
Scene Importer Adapter for KONGOR TOOL.
Converts K2ModelData and K2ClipData IR into Blender Armatures, Meshes, and Actions.
"""

import os
from typing import Dict, List, Optional
import bpy
from mathutils import Matrix, Vector

from ..core import read_smdl, read_clip, K2ModelData, K2ClipData, Matrix43
from .texture_manager import create_k2_material

def import_k2_model_to_scene(filepath: str, settings) -> bpy.types.Object:
    """Reads a .model file and reconstructs the Armature, Meshes, and Collision objects in Blender."""
    with open(filepath, "rb") as f:
        model = read_smdl(f)

    base_dir = os.path.dirname(filepath)
    model_name = os.path.splitext(os.path.basename(filepath))[0]

    armature_obj = None
    bone_name_by_index: Dict[int, str] = {}

    # 1. Reconstruct Armature if bones exist
    if model.bones:
        armature_data = bpy.data.armatures.new(name=f"{model_name}_Armature")
        armature_obj = bpy.data.objects.new(name=f"{model_name}_Armature", object_data=armature_data)
        bpy.context.collection.objects.link(armature_obj)

        bpy.context.view_layer.objects.active = armature_obj
        bpy.ops.object.mode_set(mode="EDIT")

        edit_bones = armature_data.edit_bones

        for bone in model.bones:
            bone_name_by_index[bone.index] = bone.name
            eb = edit_bones.new(bone.name)
            eb.use_deform = True

            # Extract base matrix
            mat43 = Matrix43.from_flat_floats(bone.base)
            # In K2 Engine: X right, Y forward, Z up
            pos = mat43.pos
            eb.head = Vector((pos[0], pos[1], pos[2]))
            # Extrude tail along bone forward/axis
            tail_dir = Vector((mat43.axis_y[0], mat43.axis_y[1], mat43.axis_y[2]))
            if tail_dir.length < 1e-4:
                tail_dir = Vector((0.0, 1.0, 0.0))
            eb.tail = eb.head + tail_dir.normalized() * 0.1

        # Establish hierarchy
        for bone in model.bones:
            if bone.parent_index >= 0 and bone.parent_index in bone_name_by_index:
                parent_name = bone_name_by_index[bone.parent_index]
                if parent_name in edit_bones and bone.name in edit_bones:
                    edit_bones[bone.name].parent = edit_bones[parent_name]

        bpy.ops.object.mode_set(mode="OBJECT")

    # 2. Reconstruct Visual Meshes
    for mesh in model.meshes:
        mesh_data = bpy.data.meshes.new(name=mesh.name)
        mesh_obj = bpy.data.objects.new(name=mesh.name, object_data=mesh_data)
        bpy.context.collection.objects.link(mesh_obj)

        # Vertices and Faces
        verts = [Vector((v[0], v[1], v[2])) for v in mesh.vertices]
        mesh_data.from_pydata(verts, [], mesh.faces)
        mesh_data.update()

        # UV Coordinates
        if mesh.uv_channels and mesh.uv_channels[0]:
            uv_layer = mesh_data.uv_layers.new(name="UVMap")
            uvs = mesh.uv_channels[0]
            flip = getattr(settings, "flip_uv", True)
            for poly in mesh_data.polygons:
                for loop_idx in poly.loop_indices:
                    vert_idx = mesh_data.loops[loop_idx].vertex_index
                    if vert_idx < len(uvs):
                        u, v = uvs[vert_idx]
                        uv_layer.data[loop_idx].uv = (u, (1.0 - v) if flip else v)

        # Vertex Colors
        if mesh.color_channels and mesh.color_channels[0]:
            color_layer = mesh_data.color_attributes.new(
                name="Col", type="BYTE_COLOR", domain="CORNER"
            )
            cols = mesh.color_channels[0]
            for poly in mesh_data.polygons:
                for loop_idx in poly.loop_indices:
                    vert_idx = mesh_data.loops[loop_idx].vertex_index
                    if vert_idx < len(cols):
                        r, g, b, a = cols[vert_idx]
                        color_layer.data[loop_idx].color = (r / 255.0, g / 255.0, b / 255.0, a / 255.0)

        # Normals
        if mesh.normals and len(mesh.normals) == len(mesh.vertices):
            mesh_data.use_auto_smooth = True if hasattr(mesh_data, "use_auto_smooth") else None
            custom_normals = [Vector((n[0], n[1], n[2])) for n in mesh.normals]
            mesh_data.normals_split_custom_set_from_vertices(custom_normals)

        # Material & Shader
        if getattr(settings, "import_materials", True) and mesh.shader_name:
            mat_name = os.path.splitext(os.path.basename(mesh.shader_name))[0] or mesh.name
            mat = create_k2_material(mat_name, base_dir, settings, mesh.shader_name)
            mesh_data.materials.append(mat)

        # Vertex Groups & Skinning
        if armature_obj:
            mesh_obj.parent = armature_obj
            mod = mesh_obj.modifiers.new(name="Armature", type="ARMATURE")
            mod.object = armature_obj

            # Mode 1: Blended Links
            if mesh.mode == 1 and mesh.blended_links:
                for v_idx, link in enumerate(mesh.blended_links):
                    for b_idx, weight in zip(link.indexes, link.weights):
                        if weight > 0.0 and b_idx in bone_name_by_index:
                            b_name = bone_name_by_index[b_idx]
                            vg = mesh_obj.vertex_groups.get(b_name)
                            if not vg:
                                vg = mesh_obj.vertex_groups.new(name=b_name)
                            vg.add([v_idx], weight, "ADD")

            # Mode 2: Single Links
            elif mesh.mode == 2 and mesh.single_links:
                for v_idx, b_idx in enumerate(mesh.single_links):
                    if b_idx in bone_name_by_index:
                        b_name = bone_name_by_index[b_idx]
                        vg = mesh_obj.vertex_groups.get(b_name)
                        if not vg:
                            vg = mesh_obj.vertex_groups.new(name=b_name)
                        vg.add([v_idx], 1.0, "ADD")

            # Rigid Bone Link
            elif mesh.bonelink >= 0 and mesh.bonelink in bone_name_by_index:
                b_name = bone_name_by_index[mesh.bonelink]
                vg = mesh_obj.vertex_groups.new(name=b_name)
                vg.add(list(range(len(mesh.vertices))), 1.0, "ADD")

    # 3. Reconstruct Collision Surfaces
    for surf in model.surfaces:
        surf_mesh = bpy.data.meshes.new(name=f"{model_name}_surf_{surf.surf_index}")
        surf_obj = bpy.data.objects.new(name=f"{model_name}_surf_{surf.surf_index}", object_data=surf_mesh)
        bpy.context.collection.objects.link(surf_obj)

        surf_verts = [Vector((p[0], p[1], p[2])) for p in surf.points]
        surf_mesh.from_pydata(surf_verts, [], surf.tris)
        surf_mesh.update()

        surf_obj.k2_mesh_settings.is_collision_surface = True
        if armature_obj:
            surf_obj.parent = armature_obj

    return armature_obj or (mesh_obj if model.meshes else None)

def import_k2_clip_to_scene(filepath: str, armature_obj: bpy.types.Object) -> Optional[bpy.types.Action]:
    """Reads a .clip file and applies keyframes to the given Armature object."""
    if not armature_obj or armature_obj.type != "ARMATURE":
        raise ValueError("Must specify an active Armature object to import animation into.")

    with open(filepath, "rb") as f:
        clip = read_clip(f)

    clip_name = os.path.splitext(os.path.basename(filepath))[0]
    action = bpy.data.actions.new(name=clip_name)

    if not armature_obj.animation_data:
        armature_obj.animation_data_create()
    armature_obj.animation_data.action = action

    num_frames = clip.header.num_frames

    for motion in clip.motions:
        bone_name = motion.bone_name
        data_path_loc = f'pose.bones["{bone_name}"].location'
        data_path_rot = f'pose.bones["{bone_name}"].rotation_euler'
        data_path_scale = f'pose.bones["{bone_name}"].scale'

        for channel in motion.channels:
            kt = channel.key_type
            keys = channel.float_keys

            if kt in (0, 1, 2): # X, Y, Z translation
                fcurve = action.fcurves.new(data_path=data_path_loc, index=kt)
                if len(keys) == 1:
                    fcurve.keyframe_points.insert(1, keys[0])
                else:
                    for frame_idx, val in enumerate(keys):
                        fcurve.keyframe_points.insert(frame_idx + 1, val)

            elif kt in (3, 4, 5): # Pitch, Roll, Yaw
                rot_idx = 0 if kt == 3 else (1 if kt == 4 else 2)
                fcurve = action.fcurves.new(data_path=data_path_rot, index=rot_idx)
                if len(keys) == 1:
                    fcurve.keyframe_points.insert(1, math.radians(keys[0]))
                else:
                    for frame_idx, val in enumerate(keys):
                        fcurve.keyframe_points.insert(frame_idx + 1, math.radians(val))

            elif kt in (7, 8, 9): # Scale X, Y, Z
                scale_idx = kt - 7
                fcurve = action.fcurves.new(data_path=data_path_scale, index=scale_idx)
                if len(keys) == 1:
                    fcurve.keyframe_points.insert(1, keys[0])
                else:
                    for frame_idx, val in enumerate(keys):
                        fcurve.keyframe_points.insert(frame_idx + 1, val)

    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = num_frames
    return action

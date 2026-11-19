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
    K2SkinReference,
    K2ModelDefinition,
    K2AnimationDef,
)

def _is_character_mesh(obj: bpy.types.Object) -> bool:
    """Returns True if object is a valid character geometry mesh (excludes widgets/helpers/surfaces)."""
    if not obj or obj.type != "MESH" or obj.hide_get():
        return False
    if getattr(obj.kongor, "is_collision_surface", False):
        return False
    name_lower = obj.name.lower()
    if name_lower.startswith(("_surf", "collision")):
        return False
    # Exclude bone helpers, widget shapes, and rig creator widgets
    if obj.name.startswith(("_bone", "Materiales_RIG_CREATOR", "WGT-", "rig_widget", "cs_", "ctrl_")):
        return False
    # Exclude objects in helper/widget collections
    for coll in obj.users_collection:
        cname = coll.name.lower()
        if any(w in cname for w in ("rig_creator", "widget", "wgt", "controls", "helpers")):
            return False
    return True

def _is_collision_surface(obj: bpy.types.Object) -> bool:
    """Returns True if object represents a K2 collision surface polyhedron."""
    if not obj or obj.type != "MESH" or obj.hide_get():
        return False
    return (
        getattr(obj.kongor, "is_collision_surface", False)
        or "_surf" in obj.name.lower()
        or "collision" in obj.name.lower()
    )

def _node_image_path(node) -> Optional[str]:
    if not node or node.type != 'TEX_IMAGE' or not node.image:
        return None
    image_path = bpy.path.abspath(node.image.filepath_raw or node.image.filepath)
    if not image_path:
        return None
    return image_path.replace("\\", "/")

def _looks_like_tex_type(text: str, tex_type: str) -> bool:
    text = (text or "").lower()
    if tex_type == 'color':
        return any(k in text for k in ('color', 'diff', 'diffuse', 'albedo', 'base'))
    if tex_type == 'normal':
        return any(k in text for k in ('normal', 'norm', 'nrm', 'bump'))
    if tex_type == 'specular':
        return any(k in text for k in ('spec', 'specular', 'spec_color'))
    if tex_type == 'team':
        return 'team' in text
    if tex_type == 'lightmap':
        return any(k in text for k in ('glow', 'lightmap', 'emissive', 'emis', 'self'))
    if tex_type == 'mrao':
        return any(k in text for k in ('mrao', 'orm', 'rough', 'metal', 'gloss'))
    return False

def _resolve_material_textures(mat: Optional[bpy.types.Material], export_dir: str = "") -> Dict[str, str]:
    textures: Dict[str, str] = {}
    if not mat or not mat.use_nodes or not mat.node_tree:
        return textures

    for node in mat.node_tree.nodes:
        if node.type != 'TEX_IMAGE':
            continue
        image_path = _node_image_path(node)
        if not image_path:
            continue
        filename = os.path.basename(image_path).lower()
        label = (node.label or node.name or "").lower()
        search_text = f"{label} {filename}"
        for tex_type in ('color', 'normal', 'specular', 'team', 'lightmap', 'mrao'):
            if tex_type in textures:
                continue
            if _looks_like_tex_type(search_text, tex_type):
                if export_dir:
                    try:
                        rel = os.path.relpath(image_path, export_dir).replace("\\", "/")
                        if not rel.startswith(".."):
                            textures[tex_type] = rel
                            break
                    except ValueError:
                        pass
                textures[tex_type] = f"textures/{os.path.basename(image_path)}"
                break
    return textures

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
    target_engine = getattr(settings, "target_engine", "HON_PBT") if settings else "HON_PBT"

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
        export_deform_only = getattr(settings, "export_deform_only", True) if settings else True
        has_non_deform = any(not b.use_deform for b in armature_obj.data.bones)

        if export_deform_only and has_non_deform:
            arm_bones = [b for b in armature_obj.data.bones if b.use_deform]
        else:
            arm_bones = list(armature_obj.data.bones)

        for idx, b in enumerate(arm_bones):
            bone_name_to_index[b.name] = idx

        for idx, b in enumerate(arm_bones):
            parent_idx = -1
            p = b.parent
            while p:
                if p.name in bone_name_to_index:
                    parent_idx = bone_name_to_index[p.name]
                    break
                p = p.parent

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

    # Determine character meshes to export (prefer selected character meshes if any)
    selected_char = [obj for obj in context.selected_objects if _is_character_mesh(obj)]
    char_objects = selected_char if selected_char else [obj for obj in context.scene.objects if _is_character_mesh(obj)]

    # Determine collision surfaces (prefer selected surfaces if any)
    selected_surfs = [obj for obj in context.selected_objects if _is_collision_surface(obj)]
    surf_objects = selected_surfs if selected_surfs else [obj for obj in context.scene.objects if _is_collision_surface(obj)]

    # Collect materials in first-seen order from character meshes
    unique_materials: List[bpy.types.Material] = []
    material_to_stem: Dict[str, str] = {}
    seen_mat_keys = set()

    for obj in char_objects:
        for slot in obj.material_slots:
            mat = slot.material
            if mat and mat.name_full not in seen_mat_keys:
                seen_mat_keys.add(mat.name_full)
                unique_materials.append(mat)

    for idx, mat in enumerate(unique_materials):
        mat_lower = mat.name.lower()
        if mat_lower.startswith(("material", "mat")) or mat.name.startswith("Material"):
            stem = "material" if idx == 0 else f"material{idx + 1}"
        else:
            stem = mat.name
        material_to_stem[mat.name_full] = stem

    # 2a. Export Collision Surfaces
    for surf_idx, obj in enumerate(surf_objects):
        eval_obj = obj.evaluated_get(depsgraph) if apply_modifiers else obj
        temp_mesh = eval_obj.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(temp_mesh)
        bm.free()

        points = [tuple(v.co) for v in temp_mesh.vertices]
        tris = [(p.vertices[0], p.vertices[1], p.vertices[2]) for p in temp_mesh.polygons]

        surf_bbox = BoundingBox()
        for p in points:
            surf_bbox.add_point(p)
            overall_bbox.add_point(p)

        planes: List[K2Plane] = []
        for poly in temp_mesh.polygons:
            n = tuple(poly.normal)
            p0 = temp_mesh.vertices[poly.vertices[0]].co
            d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
            planes.append(K2Plane(normal=n, dist=d))

        edges: List[K2Edge] = []
        for e in temp_mesh.edges:
            v0 = temp_mesh.vertices[e.vertices[0]].co
            v1 = temp_mesh.vertices[e.vertices[1]].co
            edge_dir = (v1 - v0).normalized() if (v1 - v0).length > 1e-6 else Vector((1.0, 0.0, 0.0))
            edges.append(K2Edge(normal=tuple(edge_dir), point=tuple(v0)))

        k2_surfaces.append(
            K2Surface(
                surf_index=surf_idx,
                flags=0,
                bmin=surf_bbox.bmin,
                bmax=surf_bbox.bmax,
                planes=planes,
                points=points,
                edges=edges,
                tris=tris,
            )
        )
        if apply_modifiers:
            eval_obj.to_mesh_clear()

    # 2b. Export Character Geometry Meshes
    for obj in char_objects:
        eval_obj = obj.evaluated_get(depsgraph) if apply_modifiers else obj
        temp_mesh = eval_obj.to_mesh()

        bm = bmesh.new()
        bm.from_mesh(temp_mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        bm.to_mesh(temp_mesh)
        bm.free()

        mesh_bbox = BoundingBox()
        raw_verts: List[VertexAttributes] = []
        raw_faces: List[Tuple[int, int, int]] = []

        uv_layer = temp_mesh.uv_layers.active.data if temp_mesh.uv_layers.active else None
        col_attr = temp_mesh.color_attributes.active if temp_mesh.color_attributes else None
        col_domain = col_attr.domain if col_attr else None
        col_layer = col_attr.data if col_attr else None

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
                if uv_layer and loop_idx < len(uv_layer):
                    u, v_coord = uv_layer[loop_idx].uv
                    uvs.append((u, (1.0 - v_coord) if flip_v else v_coord))

                colors: List[Tuple[int, int, int, int]] = []
                if col_layer:
                    c_idx = loop_idx if col_domain == "CORNER" else v_idx
                    if c_idx < len(col_layer):
                        elem = col_layer[c_idx]
                        c = getattr(elem, "color", None) or getattr(elem, "vector", (1.0, 1.0, 1.0, 1.0))
                        colors.append((
                            int(c[0] * 255),
                            int(c[1] * 255),
                            int(c[2] * 255),
                            int(c[3] * 255) if len(c) > 3 else 255
                        ))

                weights: List[Tuple[int, float]] = []
                for g in v.groups:
                    if g.group < len(obj.vertex_groups):
                        vg_name = obj.vertex_groups[g.group].name
                        if vg_name in bone_name_to_index:
                            weights.append((bone_name_to_index[vg_name], g.weight))

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

        unique_verts, clean_faces = split_and_remap_vertices(raw_verts, raw_faces)

        # Resolve S2-compliant shader_name (e.g. "material", "material2")
        mat = obj.data.materials[0] if (obj.data.materials and obj.data.materials[0]) else None
        if mat and mat.name_full in material_to_stem:
            mat_stem = material_to_stem[mat.name_full]
        elif mat:
            mat_stem = mat.name
        else:
            mat_stem = "material"

        shader_name = mat_stem

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

    # 4. Optional S2Exporter Companion Files (.material and .mdf)
    if export_materials:
        exported_stems = set()
        for mat in unique_materials:
            stem = material_to_stem[mat.name_full]
            if stem in exported_stems:
                continue
            exported_stems.add(stem)

            resolved_tex = _resolve_material_textures(mat, model_dir)
            idx_suffix = "" if stem == "material" else stem.replace("material", "")

            if target_engine == "HON_PBT":
                def_diffuse = f"color{idx_suffix}.tga" if stem.startswith("material") else f"{stem}_color.tga"
                def_normal = f"normal{idx_suffix}.tga" if stem.startswith("material") else f"{stem}_normal.tga"
                def_specular = f"spec_color{idx_suffix}.tga" if stem.startswith("material") else f"{stem}_spec.tga"

                k2_mat = K2Material(
                    name="",
                    target_engine="HON_PBT",
                    vDiffuseColor="1.0000 1.0000 1.0000",
                    fSpecularLevel="1.0000",
                    fGlossiness="56",
                    fOpacity="1.0000",
                    fReflect="1.0000",
                    diffuse_texture=resolved_tex.get("color") or def_diffuse,
                    normal_texture=resolved_tex.get("normal") or def_normal,
                    specular_texture=resolved_tex.get("specular") or def_specular,
                    team_texture=resolved_tex.get("team") or "team.tga",
                    lightmap_texture=resolved_tex.get("lightmap") or "glow.tga",
                )
            else:
                def_diffuse = f"textures/color{idx_suffix}.tga" if stem.startswith("material") else f"textures/{stem}_color.tga"
                def_normal = f"textures/normal{idx_suffix}.tga" if stem.startswith("material") else f"textures/{stem}_normal.tga"
                def_mrao = f"textures/mrao{idx_suffix}.tga" if stem.startswith("material") else f"textures/{stem}_mrao.tga"

                k2_mat = K2Material(
                    name="",
                    target_engine="HON_REBORN",
                    shader="/shared/shaders/heroes/hero_diffuse_normal_mrao_team_envmap_tinted.shader",
                    vDiffuseColor="1 1 1",
                    fSpecularLevel="1.5",
                    fGlossiness="32",
                    fOpacity="1.0",
                    diffuse_texture=resolved_tex.get("color") or def_diffuse,
                    normal_texture=resolved_tex.get("normal") or def_normal,
                    mrao_texture=resolved_tex.get("mrao") or def_mrao,
                    cube_texture="/world/sky/panorama/1.tga",
                )

            mat_filepath = os.path.join(model_dir, f"{stem}.material")
            with open(mat_filepath, "w", encoding="utf-8") as f:
                f.write(write_material_xml(k2_mat, target_engine=target_engine))

        if not unique_materials and k2_meshes:
            if target_engine == "HON_PBT":
                k2_mat = K2Material(
                    name="",
                    target_engine="HON_PBT",
                    diffuse_texture="color.tga",
                    normal_texture="normal.tga",
                    specular_texture="spec_color.tga",
                    team_texture="team.tga",
                    lightmap_texture="glow.tga",
                )
            else:
                k2_mat = K2Material(
                    name="",
                    target_engine="HON_REBORN",
                    shader="/shared/shaders/heroes/hero_diffuse_normal_mrao_team_envmap_tinted.shader",
                    diffuse_texture="textures/color.tga",
                    normal_texture="textures/normal.tga",
                    mrao_texture="textures/mrao.tga",
                    cube_texture="/world/sky/panorama/1.tga",
                )
            mat_filepath = os.path.join(model_dir, "material.material")
            with open(mat_filepath, "w", encoding="utf-8") as f:
                f.write(write_material_xml(k2_mat, target_engine=target_engine))

    if export_mdf:
        skin_refs: List[K2SkinReference] = []
        for mesh in k2_meshes:
            mat_stem = mesh.shader_name or "material"
            skin_refs.append(
                K2SkinReference(
                    mesh_name=mesh.name,
                    material_path=f"{mat_stem}.material",
                )
            )

        mdf_filename = os.path.join(model_dir, f"{model_name}.mdf")
        model_rel = f"{model_name}.model"
        mdf = K2ModelDefinition(
            model_file=model_rel,
            model_name=f"{model_name}.model",
            default_skin="default",
            model_type="K2",
            skin_refs=skin_refs,
            anims=[
                K2AnimationDef(
                    name="idle",
                    clip_file=f"clips/{model_name}_idle.clip",
                    loop=True,
                    fps=30.0,
                )
            ],
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

    export_deform_only = getattr(settings, "export_deform_only", True) if settings else True
    has_non_deform = any(not b.use_deform for b in armature_obj.data.bones)

    if export_deform_only and has_non_deform:
        arm_bones = [b for b in armature_obj.data.bones if b.use_deform]
    else:
        arm_bones = list(armature_obj.data.bones)

    if not arm_bones:
        return False, "Armature contains no bones to animate."

    # Precompute exported parent for each bone (bypassing non-deform control bones)
    exported_names = {b.name for b in arm_bones}
    bone_to_exported_parent: Dict[str, Optional[bpy.types.Bone]] = {}
    for b in arm_bones:
        p = b.parent
        while p and p.name not in exported_names:
            p = p.parent
        bone_to_exported_parent[b.name] = p

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

                # Relative pose matrix to exported parent (bakes evaluated IK, drivers, and constraints)
                exp_parent = bone_to_exported_parent.get(b.name)
                if exp_parent:
                    pb_parent = armature_obj.pose.bones.get(exp_parent.name)
                    if pb_parent:
                        rel_mat = pb_parent.matrix.inverted() @ pb.matrix
                    else:
                        rel_mat = pb.matrix
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

"""
KONGOR TOOL - Modern Blender Operators
Clean operator definitions conforming to Blender >= 4.2 / 5.0 standards.
Zero legacy code or legacy naming conventions.
"""

import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .scene_importer import import_k2_model_file, import_k2_clip_file
from .scene_exporter import export_k2_model_file, export_k2_clip_file

class KONGOR_OT_import_model(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Model (.model / SMDL)"""
    bl_idname = "kongor.import_model"
    bl_label = "Import K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kongor_import
        box = layout.box()
        box.label(text="Import Options", icon="IMPORT")
        box.prop(settings, "flip_v")
        box.prop(settings, "build_materials")
        box.prop(settings, "bones_in_front")
        box.prop(settings, "show_bone_names")

    def execute(self, context):
        settings = context.scene.kongor_import
        try:
            import_k2_model_file(
                self.filepath,
                flip_v=settings.flip_v,
                build_materials=settings.build_materials,
                bones_in_front=getattr(settings, "bones_in_front", True),
                show_bone_names=getattr(settings, "show_bone_names", False),
            )
            self.report({"INFO"}, f"Successfully imported K2 Model: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to import K2 Model: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_export_model(bpy.types.Operator, ExportHelper):
    """Export scene to K2 Engine Model (.model / SMDL v3)"""
    bl_idname = "kongor.export_model"
    bl_label = "Export K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kongor_export
        box = layout.box()
        box.label(text="Export Options", icon="EXPORT")
        box.prop(settings, "prop_preset")
        box.prop(settings, "force_static")
        box.prop(settings, "apply_modifiers")
        box.prop(settings, "export_deform_only")
        box.prop(settings, "export_materials")
        box.prop(settings, "export_mdf")

    def execute(self, context):
        settings = context.scene.kongor_export
        try:
            success, msg = export_k2_model_file(self.filepath, context, settings)
            if success:
                self.report({"INFO"}, msg)
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export K2 Model: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_import_clip(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Animation Clip (.clip) onto active Armature"""
    bl_idname = "kongor.import_clip"
    bl_label = "Import K2 Clip"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".clip"
    filter_glob: StringProperty(default="*.clip", options={"HIDDEN"})

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Please select an active Armature object before importing a .clip file.")
            return {"CANCELLED"}

        try:
            import_k2_clip_file(self.filepath, armature)
            self.report({"INFO"}, f"Successfully imported K2 Clip: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to import K2 Clip: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_export_clip(bpy.types.Operator, ExportHelper):
    """Export Armature animation to K2 Engine Clip (.clip)"""
    bl_idname = "kongor.export_clip"
    bl_label = "Export K2 Clip"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".clip"
    filter_glob: StringProperty(default="*.clip", options={"HIDDEN"})

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            for obj in context.scene.objects:
                if obj.type == "ARMATURE" and not obj.hide_get():
                    armature = obj
                    break

        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "An active Armature object is required to export a .clip file.")
            return {"CANCELLED"}

        settings = context.scene.kongor_clip
        try:
            success, msg = export_k2_clip_file(self.filepath, context, armature, settings)
            if success:
                self.report({"INFO"}, msg)
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export K2 Clip: {str(e)}")
            return {"CANCELLED"}

def get_target_armatures(context):
    """Find armatures relevant to the current selection or context."""
    armatures = []
    # 1. Active object if armature
    if getattr(context, "active_object", None) and context.active_object.type == "ARMATURE":
        armatures.append(context.active_object)

    # 2. Selected armatures
    for obj in getattr(context, "selected_objects", []):
        if obj.type == "ARMATURE" and obj not in armatures:
            armatures.append(obj)

    # 3. If active object is a mesh, check parent or armature modifiers
    if not armatures and getattr(context, "active_object", None) and context.active_object.type == "MESH":
        parent = context.active_object.parent
        if parent and parent.type == "ARMATURE" and parent not in armatures:
            armatures.append(parent)
        for mod in context.active_object.modifiers:
            if mod.type == "ARMATURE" and mod.object and mod.object not in armatures:
                armatures.append(mod.object)

    # 4. Fallback: all armatures in current scene
    if not armatures and getattr(context, "scene", None):
        for obj in context.scene.objects:
            if obj.type == "ARMATURE" and obj not in armatures:
                armatures.append(obj)

    return armatures

class KONGOR_OT_toggle_bones(bpy.types.Operator):
    """Toggle visibility of Armature skeleton bones (Show/Hide)"""
    bl_idname = "kongor.toggle_bones"
    bl_label = "Toggle Bones"
    bl_description = "Show or hide skeleton bones in the 3D Viewport"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armatures = get_target_armatures(context)
        if armatures:
            any_hidden = any(arm.hide_get() or arm.hide_viewport for arm in armatures)
            if any_hidden:
                for arm in armatures:
                    arm.hide_viewport = False
                    arm.hide_set(False)
                if hasattr(context, "space_data") and getattr(context.space_data, "type", None) == "VIEW_3D":
                    if hasattr(context.space_data, "overlay") and hasattr(context.space_data.overlay, "show_bones"):
                        context.space_data.overlay.show_bones = True
                self.report({"INFO"}, f"Bones: Shown ({len(armatures)} armature(s))")
            else:
                for arm in armatures:
                    arm.hide_viewport = True
                    arm.hide_set(True)
                self.report({"INFO"}, f"Bones: Hidden ({len(armatures)} armature(s))")
            return {"FINISHED"}

        if hasattr(context, "space_data") and getattr(context.space_data, "type", None) == "VIEW_3D":
            if hasattr(context.space_data, "overlay") and hasattr(context.space_data.overlay, "show_bones"):
                overlay = context.space_data.overlay
                overlay.show_bones = not overlay.show_bones
                state = "Shown" if overlay.show_bones else "Hidden"
                self.report({"INFO"}, f"Bones Overlay: {state}")
                return {"FINISHED"}

        self.report({"WARNING"}, "No Armature found in scene.")
        return {"CANCELLED"}

class KONGOR_OT_toggle_bone_names(bpy.types.Operator):
    """Toggle display of bone names on Armature skeleton"""
    bl_idname = "kongor.toggle_bone_names"
    bl_label = "Toggle Bone Names"
    bl_description = "Show or hide bone names in the 3D Viewport"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armatures = get_target_armatures(context)
        if not armatures:
            self.report({"WARNING"}, "No Armature found in scene.")
            return {"CANCELLED"}

        all_showing = all(arm.data.show_names for arm in armatures if arm.data)
        new_state = not all_showing

        count = 0
        for arm in armatures:
            if arm.data:
                arm.data.show_names = new_state
                count += 1

        state_str = "Shown" if new_state else "Hidden"
        self.report({"INFO"}, f"Bone Names: {state_str} ({count} armature(s))")
        return {"FINISHED"}

class KONGOR_OT_toggle_bone_xray(bpy.types.Operator):
    """Toggle In Front (X-Ray) display for Armature skeleton"""
    bl_idname = "kongor.toggle_bone_xray"
    bl_label = "Toggle Bones In Front"
    bl_description = "Display skeleton bones in front of meshes (X-Ray mode)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armatures = get_target_armatures(context)
        if not armatures:
            self.report({"WARNING"}, "No Armature found in scene.")
            return {"CANCELLED"}

        all_in_front = all(arm.show_in_front for arm in armatures)
        new_state = not all_in_front

        for arm in armatures:
            arm.show_in_front = new_state

        state_str = "ON" if new_state else "OFF"
        self.report({"INFO"}, f"Bones In Front (X-Ray): {state_str} ({len(armatures)} armature(s))")
        return {"FINISHED"}

class KONGOR_OT_fit_bone_size(bpy.types.Operator):
    """Automatically adjust bone lengths on Armature to match character proportions"""
    bl_idname = "kongor.fit_bone_size"
    bl_label = "Fit Bone Size"
    bl_description = "Automatically resize Armature bones to match character proportions and joints"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        armatures = get_target_armatures(context)
        if not armatures:
            self.report({"WARNING"}, "No Armature found in scene.")
            return {"CANCELLED"}

        count = 0
        for arm_obj in armatures:
            if not arm_obj.data:
                continue

            dim = max(arm_obj.dimensions) if any(arm_obj.dimensions) else 0.0
            if dim < 1.0:
                meshes = [o for o in context.scene.objects if o.type == "MESH" and o.parent == arm_obj]
                if meshes:
                    dim = max(max(m.dimensions) for m in meshes)
            default_bone_len = max(dim * 0.05, 3.0) if dim > 1.0 else 5.0

            orig_active = context.view_layer.objects.active
            context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode="EDIT")
            edit_bones = arm_obj.data.edit_bones

            for eb in edit_bones:
                child_dists = [
                    (c.head - eb.head).length
                    for c in eb.children
                    if (c.head - eb.head).length > 0.05
                ]
                if child_dists:
                    target_len = min(child_dists)
                elif eb.parent:
                    target_len = max(eb.parent.length * 0.7, default_bone_len * 0.5)
                else:
                    target_len = default_bone_len

                target_len = max(target_len, 0.5)
                eb.length = target_len

            bpy.ops.object.mode_set(mode="OBJECT")
            if orig_active:
                context.view_layer.objects.active = orig_active

            count += len(arm_obj.data.bones)

        self.report({"INFO"}, f"Successfully resized {count} bones across {len(armatures)} armature(s).")
        return {"FINISHED"}

class KONGOR_OT_inspect_scene(bpy.types.Operator):
    """Display information and statistics about K2 Engine objects in scene"""
    bl_idname = "kongor.inspect_scene"
    bl_label = "Inspect Scene"

    def execute(self, context):
        meshes = [o for o in context.scene.objects if o.type == "MESH"]
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        surfaces = [
            o for o in meshes
            if getattr(o.kongor, "is_collision_surface", False) or "_surf" in o.name.lower()
        ]
        visual_meshes = len(meshes) - len(surfaces)

        msg = f"K2 Scene: {visual_meshes} Visual Meshes, {len(surfaces)} Collision Surfaces, {len(armatures)} Armatures."
        self.report({"INFO"}, msg)
        return {"FINISHED"}

class KONGOR_OT_dialog(bpy.types.Operator):
    """Open floating dialog window for KONGOR TOOL"""
    bl_idname = "kongor.dialog"
    bl_label = "KONGOR TOOL (v5.0.0)"
    bl_description = "Open independent floating control window for KONGOR TOOL"
    bl_options = {"REGISTER"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=440)

    def execute(self, context):
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout

        # 1. Header Box
        header_box = layout.box()
        col = header_box.column(align=True)
        col.label(text="Heroes of Newerth K2 Engine Pipeline", icon="TOOL_SETTINGS")
        col.operator("kongor.inspect_scene", text="Inspect Scene Objects", icon="INFO")

        # 2. Model Section
        model_box = layout.box()
        model_box.label(text="K2 Model (.model / SMDL v3):", icon="OBJECT_DATA")
        row = model_box.row(align=True)
        row.operator("kongor.import_model", text="Import Model", icon="IMPORT")
        row.operator("kongor.export_model", text="Export Model", icon="EXPORT")

        settings_imp = context.scene.kongor_import
        settings_exp = context.scene.kongor_export
        col = model_box.column(align=True)
        col.prop(settings_exp, "prop_preset")
        col.prop(settings_exp, "force_static")
        col.prop(settings_exp, "apply_modifiers")
        col.prop(settings_exp, "export_materials")
        col.prop(settings_exp, "standardize_material_names")
        col.prop(settings_exp, "export_mdf")
        col.prop(settings_exp, "export_deform_only")
        col.operator("kongor.standardize_materials", text="Standardize Materials to K2", icon="MATERIAL")
        col.separator()
        col.prop(settings_imp, "flip_v")
        col.prop(settings_imp, "bones_in_front")
        col.prop(settings_imp, "show_bone_names")

        # Active Mesh Object Settings (matches S2Exporter Mesh Info)
        act = context.active_object
        if act and act.type == "MESH":
            mesh_box = layout.box()
            mesh_box.label(text=f"Selected Mesh: {act.name}", icon="MESH_DATA")
            mesh_box.prop(act.kongor, "mesh_type")
            if act.kongor.mesh_type == "NORMAL":
                mesh_box.prop(act.kongor, "bonelink")

        # 3. KONGOR Rig & K2 Skeleton Tools
        rig_k2_box = layout.box()
        rig_k2_box.label(text="KONGOR Rig & K2 Skeleton Tools:", icon="ARMATURE_DATA")
        row_spawn = rig_k2_box.row(align=True)
        row_spawn.operator("kongor.add_k2_rig", text="Add Character Rig...", icon="OUTLINER_OB_ARMATURE")
        row_spawn.operator("kongor.generate_k2_skeleton", text="Generate K2 Armature", icon="ARMATURE_DATA")

        row_k2 = rig_k2_box.row(align=True)
        row_k2.operator("kongor.conform_k2_hierarchy", text="Conform K2 Hierarchy", icon="CON_CHILDOF")
        row_k2.operator("kongor.add_k2_sockets", text="Add K2 Sockets", icon="PLUS")

        row_remap = rig_k2_box.row(align=True)
        row_remap.operator("kongor.remap_to_k2_universal", text="Remap to K2 (Bip01)", icon="SYNTAX_ON").reverse = False
        row_remap.operator("kongor.isolate_k2_deform", text="Isolate Deform", icon="CHECKMARK")

        # 4. KONGOR Rig Pipeline Section
        arp_box = layout.box()
        arp_box.label(text="KONGOR Rig Pipeline:", icon="POSE_HLT")
        if hasattr(context.scene, "kongor_arp"):
            arp_settings = context.scene.kongor_arp
            col_arp = arp_box.column(align=True)
            col_arp.prop(arp_settings, "target_arp_rig", text="Target KONGOR Rig")
            col_arp.prop(arp_settings, "source_k2_rig", text="Source K2 Armature")
            row_arp_range = col_arp.row(align=True)
            row_arp_range.prop(arp_settings, "bake_frame_start", text="Start")
            row_arp_range.prop(arp_settings, "bake_frame_end", text="End")
            col_arp.prop(arp_settings, "preserve_socket_bones")

            row_arp_ops = arp_box.row(align=True)
            row_arp_ops.operator("kongor.arp_apply_k2_preset", text="Load K2 Preset (.bmap)", icon="PRESET")
            row_arp_ops.operator("kongor.arp_bind", text="Bind K2 to Rig", icon="CONSTRAINT_BONE")
            row_arp_ops.operator("kongor.arp_unbind", text="Unbind", icon="X")

            arp_box.operator("kongor.arp_bake", text="Bake KONGOR Rig to K2 Skeleton", icon="ACTION")

        # 5. Skeleton & Bones Display Section
        rig_box = layout.box()
        rig_box.label(text="Skeleton & Bones Display:", icon="BONE_DATA")
        target_arms = get_target_armatures(context)

        bones_vis = any(not a.hide_get() and not a.hide_viewport for a in target_arms) if target_arms else False
        names_vis = any(a.data.show_names for a in target_arms if a.data) if target_arms else False
        xray_vis = any(a.show_in_front for a in target_arms) if target_arms else False

        row = rig_box.row(align=True)
        row.operator("kongor.toggle_bones", text="Toggle Bones", icon="BONE_DATA", depress=bones_vis)
        row.operator("kongor.toggle_bone_names", text="Toggle Names", icon="SYNTAX_ON", depress=names_vis)
        row.operator("kongor.toggle_bone_xray", text="In Front (X-Ray)", icon="XRAY", depress=xray_vis)

        row_fit = rig_box.row(align=True)
        row_fit.operator("kongor.fit_bone_size", text="Auto-Fit Bone Sizes", icon="ARROW_LEFTRIGHT")

        if target_arms and target_arms[0].data:
            arm_obj = target_arms[0]
            col = rig_box.column(align=True)
            col.label(text=f"Active Rig: {arm_obj.name}", icon="OUTLINER_OB_ARMATURE")
            col.prop(arm_obj.data, "show_names", text="Show Bone Names")
            col.prop(arm_obj, "show_in_front", text="In Front (X-Ray)")
            col.prop(arm_obj.data, "show_axes", text="Show Bone Axes")
            col.prop(arm_obj.data, "display_type", text="Display Type")

        # 5. Animation Clip Section
        clip_box = layout.box()
        clip_box.label(text="K2 Animation Clip (.clip / CLIP v2):", icon="ANIM")
        row = clip_box.row(align=True)
        row.operator("kongor.import_clip", text="Import Clip", icon="IMPORT")
        row.operator("kongor.export_clip", text="Export Clip", icon="EXPORT")

        settings_clip = context.scene.kongor_clip
        col = clip_box.column(align=True)
        row = col.row(align=True)
        row.prop(settings_clip, "frame_start")
        row.prop(settings_clip, "frame_end")
        col.prop(settings_clip, "fps")
        col.prop(settings_clip, "export_deform_only")

        # 4. Active Mesh Object Properties
        if context.active_object and context.active_object.type == "MESH":
            obj_box = layout.box()
            obj_box.label(text=f"Active Mesh: {context.active_object.name}", icon="MESH_DATA")
            settings_obj = context.active_object.kongor
            obj_box.prop(settings_obj, "is_collision_surface")
            if not settings_obj.is_collision_surface:
                obj_box.prop(settings_obj, "bonelink")

        # 5. Extension Management
        maint_box = layout.box()
        maint_box.label(text="Extension:", icon="PREFERENCES")
        row = maint_box.row()
        row.operator("kongor.uninstall", text="Manage Extension in Preferences", icon="PREFERENCES")

class KONGOR_OT_uninstall(bpy.types.Operator):
    """Safely open Blender Preferences to manage or uninstall KONGOR TOOL"""
    bl_idname = "kongor.uninstall"
    bl_label = "Manage / Uninstall KONGOR TOOL"
    bl_options = {"REGISTER", "INTERNAL"}

    def execute(self, context):
        try:
            bpy.ops.screen.userpref_show('INVOKE_DEFAULT')
            if hasattr(context.preferences, "active_section"):
                context.preferences.active_section = "EXTENSIONS"
        except Exception:
            pass
        self.report({"INFO"}, "Preferences opened: Manage or uninstall KONGOR TOOL from Extensions.")
        return {"FINISHED"}

# ---------------------------------------------------------------------------
# K2 & Rig Creator Bone Mapping & Integration
# ---------------------------------------------------------------------------

RGC_TO_K2_BONE_MAP = {
    # Torso / Spine
    "root_rotation": "Root",
    "def_spine.001": "Bip01 Pelvis",
    "def_spine.002": "Bip01 Spine",
    "def_spine.003": "Bip01 Spine1",
    "def_spine.004": "Bip01 Spine2",
    "def_head.001": "Bip01 Neck",
    "def_head.002": "Bip01 Head",

    # Left Arm
    "def_shoulder_L.001": "Bip01 L Clavicle",
    "def_shoulder_L.002": "Bip01 L Clavicle1",
    "def_arm_UP_L.001": "Bip01 L UpperArm",
    "def_arm_UP_L.002": "Bip01 L UpperArmRoll",
    "def_arm_DOWN_L.001": "Bip01 L Forearm",
    "def_arm_DOWN_L.002": "Bip01 L ForearmRoll",
    "def_hand_L": "Bip01 L Hand",

    # Right Arm
    "def_shoulder_R.001": "Bip01 R Clavicle",
    "def_shoulder_R.002": "Bip01 R Clavicle1",
    "def_arm_UP_R.001": "Bip01 R UpperArm",
    "def_arm_UP_R.002": "Bip01 R UpperArmRoll",
    "def_arm_DOWN_R.001": "Bip01 R Forearm",
    "def_arm_DOWN_R.002": "Bip01 R ForearmRoll",
    "def_hand_R": "Bip01 R Hand",

    # Left Leg
    "def_hip_L.001": "Bip01 L Thigh",
    "def_hip_L.002": "Bip01 L ThighRoll",
    "def_leg_L.001": "Bip01 L Calf",
    "def_leg_L.002": "Bip01 L CalfRoll",
    "def_feet_L.001": "Bip01 L Foot",
    "def_feet_L.002": "Bip01 L Toe0",

    # Right Leg
    "def_hip_R.001": "Bip01 R Thigh",
    "def_hip_R.002": "Bip01 R ThighRoll",
    "def_leg_R.001": "Bip01 R Calf",
    "def_leg_R.002": "Bip01 R CalfRoll",
    "def_feet_R.001": "Bip01 R Foot",
    "def_feet_R.002": "Bip01 R Toe0",

    # Left Fingers
    "def_thumb_L.001": "Bip01 L Finger0",
    "def_thumb_L.002": "Bip01 L Finger01",
    "def_thumb_L.003": "Bip01 L Finger02",
    "def_index_L.001": "Bip01 L Finger1",
    "def_index_L.002": "Bip01 L Finger11",
    "def_index_L.003": "Bip01 L Finger12",
    "def_middle_L.001": "Bip01 L Finger2",
    "def_middle_L.002": "Bip01 L Finger21",
    "def_middle_L.003": "Bip01 L Finger22",
    "def_ring_L.001": "Bip01 L Finger3",
    "def_ring_L.002": "Bip01 L Finger31",
    "def_ring_L.003": "Bip01 L Finger32",
    "def_pinky_L.001": "Bip01 L Finger4",
    "def_pinky_L.002": "Bip01 L Finger41",
    "def_pinky_L.003": "Bip01 L Finger42",

    # Right Fingers
    "def_thumb_R.001": "Bip01 R Finger0",
    "def_thumb_R.002": "Bip01 R Finger01",
    "def_thumb_R.003": "Bip01 R Finger02",
    "def_index_R.001": "Bip01 R Finger1",
    "def_index_R.002": "Bip01 R Finger11",
    "def_index_R.003": "Bip01 R Finger12",
    "def_middle_R.001": "Bip01 R Finger2",
    "def_middle_R.002": "Bip01 R Finger21",
    "def_middle_R.003": "Bip01 R Finger22",
    "def_ring_R.001": "Bip01 R Finger3",
    "def_ring_R.002": "Bip01 R Finger31",
    "def_ring_R.003": "Bip01 R Finger32",
    "def_pinky_R.001": "Bip01 R Finger4",
    "def_pinky_R.002": "Bip01 R Finger41",
    "def_pinky_R.003": "Bip01 R Finger42",
}

class KONGOR_OT_remap_to_k2(bpy.types.Operator):
    """Remap Rig Creator deform bones to standard K2 Engine (Bip01) names or reverse"""
    bl_idname = "kongor.remap_to_k2"
    bl_label = "Remap Bones to K2 Standard"
    bl_options = {"REGISTER", "UNDO"}

    reverse: bpy.props.BoolProperty(
        name="Reverse (K2 to Rig Creator)",
        description="Convert K2 standard Bip01 names back to Rig Creator def_ names",
        default=False,
    )

    def execute(self, context):
        target_arms = get_target_armatures(context)
        if not target_arms:
            self.report({"WARNING"}, "No armature found in selection or scene.")
            return {"CANCELLED"}

        mapping = {v: k for k, v in RGC_TO_K2_BONE_MAP.items()} if self.reverse else RGC_TO_K2_BONE_MAP
        renamed_count = 0

        for arm in target_arms:
            for old_name, new_name in mapping.items():
                b = arm.data.bones.get(old_name)
                if b:
                    b.name = new_name
                    renamed_count += 1

            # Also rename vertex groups on child / skinned meshes
            for obj in bpy.data.objects:
                if obj.type == "MESH" and (obj.parent == arm or any(m.type == "ARMATURE" and m.object == arm for m in obj.modifiers)):
                    for old_name, new_name in mapping.items():
                        vg = obj.vertex_groups.get(old_name)
                        if vg:
                            vg.name = new_name

        direction = "Rig Creator -> K2 Bip01" if not self.reverse else "K2 Bip01 -> Rig Creator"
        self.report({"INFO"}, f"Remapped {renamed_count} bones ({direction}).")
        return {"FINISHED"}

class KONGOR_OT_setup_k2_deform(bpy.types.Operator):
    """Configure bone deform flags for K2 export (deform bones ON, controls/widgets OFF)"""
    bl_idname = "kongor.setup_k2_deform"
    bl_label = "Prepare Rig for K2 Export"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        target_arms = get_target_armatures(context)
        if not target_arms:
            self.report({"WARNING"}, "No armature found in selection or scene.")
            return {"CANCELLED"}

        deform_count = 0
        non_deform_count = 0

        for arm in target_arms:
            for b in arm.data.bones:
                name_lower = b.name.lower()
                is_control = any(name_lower.startswith(prefix) for prefix in ("ik_", "pole", "cont_", "root_", "widget", "mch_", "org_"))
                is_deform_named = any(name_lower.startswith(prefix) for prefix in ("def_", "bip01", "bone_", "root")) and not is_control

                if is_control:
                    b.use_deform = False
                    non_deform_count += 1
                elif is_deform_named:
                    b.use_deform = True
                    deform_count += 1
                elif b.use_deform:
                    deform_count += 1
                else:
                    non_deform_count += 1

        self.report({"INFO"}, f"Prepared for K2: {deform_count} deform bones, {non_deform_count} control bones.")
        return {"FINISHED"}

class KONGOR_OT_add_k2_rig(bpy.types.Operator):
    """Add a professional character armature preset from KONGOR Rig (Human, Quadruped, etc.)"""
    bl_idname = "kongor.add_k2_rig"
    bl_label = "Add KONGOR Rig Character"
    bl_description = "Add professional character armature preset from KONGOR Rig"
    bl_options = {"REGISTER", "UNDO"}

    preset: bpy.props.EnumProperty(
        name="Character Preset",
        description="Character preset to append from KONGOR Rig",
        items=[
            ("human", "Human (Biped)", "Full biped humanoid character with IK/FK controls and facial setup"),
            ("dog", "Dog (Quadruped)", "Quadruped canine character rig"),
            ("horse", "Horse (Quadruped)", "Quadruped equine character rig"),
            ("bird", "Bird (Avian)", "Avian flying creature rig with wings"),
            ("free", "Empty / Free Rig", "Blank template rig with root controller"),
        ],
        default="human",
    )

    def execute(self, context):
        if hasattr(bpy.ops, "arp") and hasattr(bpy.ops.arp, "append_arp"):
            try:
                bpy.ops.arp.append_arp(rig_preset=self.preset)
                self.report({"INFO"}, f"Successfully added KONGOR Rig ({self.preset.capitalize()})")
                return {"FINISHED"}
            except Exception as e:
                self.report({"ERROR"}, f"Failed to spawn KONGOR Rig preset: {e}")
                return {"CANCELLED"}
        else:
            self.report({"ERROR"}, "KONGOR Rig module is not loaded.")
            return {"CANCELLED"}

class KONGOR_OT_standardize_materials(bpy.types.Operator):
    """Standardize scene/character material names to K2 standard (material, material2, material3...)"""
    bl_idname = "kongor.standardize_materials"
    bl_label = "Standardize Materials to K2"
    bl_description = "Rename materials to canonical K2 Engine naming convention: material, material2, material3..."
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        char_objects = [
            obj for obj in context.scene.objects
            if obj.type == "MESH" and not obj.hide_viewport and not obj.name.startswith(
                ("_bone", "Materiales_RIG_CREATOR", "WGT-", "rig_widget", "cs_", "ctrl_")
            )
        ]
        if not char_objects:
            char_objects = [
                obj for obj in context.scene.objects
                if obj.type == "MESH" and not obj.name.startswith(
                    ("_bone", "Materiales_RIG_CREATOR", "WGT-", "rig_widget", "cs_", "ctrl_")
                )
            ]

        unique_mats = []
        seen = set()
        for obj in char_objects:
            for slot in obj.material_slots:
                mat = slot.material
                if mat and mat not in seen:
                    seen.add(mat)
                    unique_mats.append(mat)

        if not unique_mats:
            self.report({"WARNING"}, "No materials found on character meshes.")
            return {"CANCELLED"}

        renamed_count = 0
        for idx, mat in enumerate(unique_mats):
            target_name = "material" if idx == 0 else f"material{idx + 1}"
            if mat.name != target_name:
                existing = bpy.data.materials.get(target_name)
                if existing and existing != mat:
                    existing.name = f"{target_name}_temp"
                mat.name = target_name
                renamed_count += 1

        self.report({"INFO"}, f"Standardized {len(unique_mats)} material(s) to K2 convention ({renamed_count} renamed).")
        return {"FINISHED"}

classes = (
    KONGOR_OT_standardize_materials,
    KONGOR_OT_import_model,
    KONGOR_OT_export_model,
    KONGOR_OT_import_clip,
    KONGOR_OT_export_clip,
    KONGOR_OT_toggle_bones,
    KONGOR_OT_toggle_bone_names,
    KONGOR_OT_toggle_bone_xray,
    KONGOR_OT_fit_bone_size,
    KONGOR_OT_inspect_scene,
    KONGOR_OT_remap_to_k2,
    KONGOR_OT_setup_k2_deform,
    KONGOR_OT_add_k2_rig,
    KONGOR_OT_dialog,
    KONGOR_OT_uninstall,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

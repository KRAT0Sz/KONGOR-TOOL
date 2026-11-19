"""
KONGOR TOOL - Auto-Rig Pro (ARP) Bridge Module
Seamless integration between K2 Engine skeletons/clips and Auto-Rig Pro (v3.71.25).
Provides 1-click binding, K2 biped retargeting, and animation baking to K2 deform skeleton.
"""

import os
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, PointerProperty

_arp_registered = False

def is_arp_available() -> bool:
    """Check if Auto-Rig Pro is loaded (either internally or globally)."""
    return bool(
        hasattr(bpy.types, "ARP_OT_retarget")
        or hasattr(bpy.types, "ARP_OT_build_bones")
        or hasattr(bpy.types, "ARP_OT_export")
        or _arp_registered
    )

def try_register_internal_arp() -> bool:
    """Attempt to register the internal AutoRigPro package bundled with KONGOR Tool."""
    global _arp_registered
    if _arp_registered:
        return True

    if hasattr(bpy.types, "ARP_OT_build_bones") or hasattr(bpy.types, "ARP_OT_retarget"):
        print("[KONGOR TOOL] Auto-Rig Pro is already loaded in Blender environment.")
        return True

    try:
        from .. import auto_rig_pro
        auto_rig_pro.register()
        _arp_registered = True
        return True
    except Exception as e:
        print(f"[KONGOR TOOL] Notice: Auto-Rig Pro internal registration: {e}")
        return False

def try_unregister_internal_arp():
    """Unregister internal AutoRigPro module if loaded."""
    global _arp_registered
    if not _arp_registered:
        return

    try:
        from .. import auto_rig_pro
        auto_rig_pro.unregister()
        _arp_registered = False
    except Exception as e:
        print(f"[KONGOR TOOL] Error unregistering Auto-Rig Pro: {e}")

def is_k2_armature(obj: bpy.types.Object) -> bool:
    """Detect if an object is a K2 game armature."""
    if not obj or obj.type != "ARMATURE":
        return False
    bone_names = {b.name for b in obj.data.bones}
    k2_indicators = {"Root", "Bip01", "Bip01 Pelvis", "Bip01 Spine", "Bip01 Head"}
    return bool(bone_names & k2_indicators) or any(name.startswith("_bone") for name in bone_names)

class KongorARPBridgeSettings(PropertyGroup):
    target_arp_rig: PointerProperty(
        name="KONGOR Rig",
        type=bpy.types.Object,
        description="Target KONGOR Rig control armature",
        poll=lambda self, obj: obj.type == "ARMATURE" and not is_k2_armature(obj),
    )
    source_k2_rig: PointerProperty(
        name="K2 Armature",
        type=bpy.types.Object,
        description="Source K2 game armature",
        poll=lambda self, obj: is_k2_armature(obj),
    )
    bake_frame_start: IntProperty(
        name="Start Frame",
        default=0,
    )
    bake_frame_end: IntProperty(
        name="End Frame",
        default=250,
    )
    preserve_socket_bones: BoolProperty(
        name="Preserve Sockets",
        description="Preserve _bone_* sockets and effects attachment points during retargeting/baking",
        default=True,
    )

class KONGOR_OT_arp_bind(Operator):
    """Constrain K2 Deform Armature to KONGOR Rig controls for live animation"""
    bl_idname = "kongor.arp_bind"
    bl_label = "Bind K2 to KONGOR Rig"
    bl_description = "Add Copy Transforms constraints linking K2 deform bones to KONGOR Rig controllers"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "kongor_arp", None)
        return bool(settings and settings.source_k2_rig and settings.target_arp_rig)

    def execute(self, context):
        settings = context.scene.kongor_arp
        k2_arm = settings.source_k2_rig
        arp_arm = settings.target_arp_rig

        preset_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "auto_rig_pro",
            "remap_presets",
            "k2_biped.bmap",
        )
        bone_mapping = {}
        if os.path.exists(preset_file):
            with open(preset_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f]
                i = 0
                while i < len(lines):
                    if lines[i] and i + 1 < len(lines):
                        arp_bone = lines[i]
                        k2_bone = lines[i + 1]
                        if k2_bone and k2_bone != "None" and arp_bone and arp_bone != "None":
                            bone_mapping[k2_bone] = arp_bone
                        i += 5
                    else:
                        i += 1

        arp_pose_bones = arp_arm.pose.bones
        k2_pose_bones = k2_arm.pose.bones

        bound_count = 0
        for k2_name, pbone in k2_pose_bones.items():
            target_name = None
            def_cand = f"def_{k2_name.lower().replace('bip01 ', '').replace(' ', '_')}"
            if def_cand in arp_pose_bones:
                target_name = def_cand
            elif k2_name in bone_mapping and bone_mapping[k2_name] in arp_pose_bones:
                target_name = bone_mapping[k2_name]
            elif k2_name in arp_pose_bones:
                target_name = k2_name

            if target_name:
                cname = "K2_ARP_Follow"
                c = pbone.constraints.get(cname)
                if not c:
                    c = pbone.constraints.new(type="COPY_TRANSFORMS")
                    c.name = cname
                c.target = arp_arm
                c.subtarget = target_name
                c.mix_mode = "REPLACE"
                c.owner_space = "WORLD"
                c.target_space = "WORLD"
                bound_count += 1

        self.report({"INFO"}, f"Bound {bound_count} K2 bone(s) to KONGOR Rig '{arp_arm.name}'")
        return {"FINISHED"}

class KONGOR_OT_arp_unbind(Operator):
    """Remove live follow constraints from K2 Deform Armature"""
    bl_idname = "kongor.arp_unbind"
    bl_label = "Unbind K2 Armature"
    bl_description = "Remove all follow constraints from K2 deform bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "kongor_arp", None)
        return bool(settings and settings.source_k2_rig)

    def execute(self, context):
        settings = context.scene.kongor_arp
        k2_arm = settings.source_k2_rig
        count = 0
        for pbone in k2_arm.pose.bones:
            c = pbone.constraints.get("K2_ARP_Follow")
            if c:
                pbone.constraints.remove(c)
                count += 1
        self.report({"INFO"}, f"Removed KONGOR Rig constraints from {count} bone(s)")
        return {"FINISHED"}

class KONGOR_OT_arp_bake(Operator):
    """Bake animation from KONGOR Rig directly onto K2 Armature for game-ready export"""
    bl_idname = "kongor.arp_bake"
    bl_label = "Bake KONGOR Rig to K2 Skeleton"
    bl_description = "Bake visual transforms from KONGOR Rig into K2 game skeleton keyframes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        settings = getattr(context.scene, "kongor_arp", None)
        return bool(settings and settings.source_k2_rig and settings.target_arp_rig)

    def execute(self, context):
        settings = context.scene.kongor_arp
        k2_arm = settings.source_k2_rig
        arp_arm = settings.target_arp_rig

        # 1. Ensure K2 is bound
        bpy.ops.kongor.arp_bind()

        # 2. Select K2 Armature for baking
        bpy.ops.object.select_all(action="DESELECT")
        k2_arm.select_set(True)
        context.view_layer.objects.active = k2_arm

        start = settings.bake_frame_start
        end = settings.bake_frame_end

        action_name = "K2_Baked_Action"
        if arp_arm.animation_data and arp_arm.animation_data.action:
            action_name = f"{arp_arm.animation_data.action.name}_K2Bake"

        # 3. Bake visual transform
        bpy.ops.nla.bake(
            frame_start=start,
            frame_end=end,
            only_selected=False,
            visual_keying=True,
            clear_constraints=True,
            use_current_action=False,
            clean_curves=True,
            bake_types={"POSE"},
        )

        if k2_arm.animation_data and k2_arm.animation_data.action:
            k2_arm.animation_data.action.name = action_name

        self.report({"INFO"}, f"Successfully baked animation frames {start}-{end} to '{k2_arm.name}' ({action_name})")
        return {"FINISHED"}

class KONGOR_OT_arp_apply_k2_preset(Operator):
    """Set Auto-Rig Pro remap preset to K2 Biped (k2_biped.bmap)"""
    bl_idname = "kongor.arp_apply_k2_preset"
    bl_label = "Load K2 Biped Preset (.bmap)"
    bl_description = "Configure Auto-Rig Pro Remap tool with the official K2 Biped bone mapping"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        preset_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "auto_rig_pro",
            "remap_presets",
            "k2_biped.bmap",
        )
        if not os.path.exists(preset_file):
            self.report({"ERROR"}, f"K2 Preset file not found: {preset_file}")
            return {"CANCELLED"}

        loaded = False
        if hasattr(bpy.ops, "arp"):
            if hasattr(bpy.ops.arp, "import_config"):
                try:
                    bpy.ops.arp.import_config(filepath=preset_file, clear_current=True)
                    loaded = True
                except Exception as e:
                    print(f"[KONGOR TOOL] Notice invoking arp.import_config: {e}")
            if not loaded and hasattr(bpy.ops.arp, "import_config_preset"):
                try:
                    bpy.ops.arp.import_config_preset(preset_name="k2_biped", clear_current=True)
                    loaded = True
                except Exception as e:
                    print(f"[KONGOR TOOL] Notice invoking arp.import_config_preset: {e}")

        if hasattr(context.scene, "arp_bmap_path"):
            context.scene.arp_bmap_path = preset_file

        self.report({"INFO"}, f"Loaded K2 Biped Remap Preset: {preset_file}")
        return {"FINISHED"}

classes = (
    KongorARPBridgeSettings,
    KONGOR_OT_arp_bind,
    KONGOR_OT_arp_unbind,
    KONGOR_OT_arp_bake,
    KONGOR_OT_arp_apply_k2_preset,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kongor_arp = PointerProperty(type=KongorARPBridgeSettings)
    try_register_internal_arp()

def unregister():
    try_unregister_internal_arp()
    if hasattr(bpy.types.Scene, "kongor_arp"):
        del bpy.types.Scene.kongor_arp
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

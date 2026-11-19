"""
KONGOR TOOL - KONGOR Rig Bridge & K2 Engine Skeleton Pipeline
Seamless integration between K2 Engine skeletons/clips and KONGOR Rig.
Provides 1-click binding, K2 biped retargeting, DAG hierarchy conforming,
standard K2 leaf socket generation, and animation baking to K2 deform skeleton.
"""

import os
import bpy
from bpy.types import Operator, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, PointerProperty

try:
    from mathutils import Vector
except ImportError:
    class Vector(tuple):
        def __new__(cls, coords):
            return super().__new__(cls, coords)
        def __add__(self, other):
            return Vector((self[0] + other[0], self[1] + other[1], self[2] + other[2]))

_arp_registered = False

# Standard K2 Engine parent-child DAG hierarchy
K2_PARENT_RULES = {
    "Bip01": "Root",
    "Bip01 Pelvis": "Bip01",
    "Bip01 Spine": "Bip01 Pelvis",
    "Bip01 Spine1": "Bip01 Spine",
    "Bip01 Spine2": "Bip01 Spine1",
    "Bip01 Spine3": "Bip01 Spine2",
    "Bip01 Neck": "Bip01 Spine1",
    "Bip01 Head": "Bip01 Neck",
    "Bip01 L Clavicle": "Bip01 Spine1",
    "Bip01 R Clavicle": "Bip01 Spine1",
    "Bip01 L UpperArm": "Bip01 L Clavicle",
    "Bip01 R UpperArm": "Bip01 R Clavicle",
    "Bip01 L Forearm": "Bip01 L UpperArm",
    "Bip01 R Forearm": "Bip01 R UpperArm",
    "Bip01 L Hand": "Bip01 L Forearm",
    "Bip01 R Hand": "Bip01 R Forearm",
    "Bip01 L Thigh": "Bip01 Pelvis",
    "Bip01 R Thigh": "Bip01 Pelvis",
    "Bip01 L Calf": "Bip01 L Thigh",
    "Bip01 R Calf": "Bip01 R Thigh",
    "Bip01 L Foot": "Bip01 L Calf",
    "Bip01 R Foot": "Bip01 R Calf",
    "Bip01 L Toe0": "Bip01 L Foot",
    "Bip01 R Toe0": "Bip01 R Foot",
    "_bone_weapon01": "Bip01 R Hand",
    "_bone_weapon02": "Bip01 L Hand",
    "_bone_overhead": "Bip01 Head",
    "_bone_chest": "Bip01 Spine1",
    "_bone_lefteye": "Bip01 Head",
    "_bone_righteye": "Bip01 Head",
}

# Standard K2 Leaf Sockets Definition: (socket_name, parent_name, offset_xyz)
K2_SOCKETS_DEF = [
    ("_bone_weapon01", "Bip01 R Hand", (0.0, 0.05, 0.0)),
    ("_bone_weapon02", "Bip01 L Hand", (0.0, 0.05, 0.0)),
    ("_bone_overhead", "Bip01 Head", (0.0, 0.0, 0.35)),
    ("_bone_chest", "Bip01 Spine1", (0.0, 0.15, 0.0)),
    ("_bone_lefteye", "Bip01 Head", (0.035, 0.08, 0.05)),
    ("_bone_righteye", "Bip01 Head", (-0.035, 0.08, 0.05)),
]

# Universal KONGOR Rig / ARP / Mixamo deform names -> K2 standard Bip01 mapping
KONGOR_RIG_DEFORM_TO_K2 = {
    # Root & Pelvis
    "c_traj": "Root",
    "traj": "Root",
    "root_master": "Root",
    "root_rotation": "Root",
    "root.x": "Bip01",
    "c_root.x": "Bip01",
    "c_pos": "Bip01",
    "bip01": "Bip01",
    "hips.x": "Bip01 Pelvis",
    "def_hips.x": "Bip01 Pelvis",
    "c_hips_plate.x": "Bip01 Pelvis",
    "hips": "Bip01 Pelvis",
    "pelvis": "Bip01 Pelvis",

    # Spine chain
    "spine_01.x": "Bip01 Spine",
    "def_spine_01.x": "Bip01 Spine",
    "c_spine_01.x": "Bip01 Spine",
    "spine.001": "Bip01 Spine",
    "spine_02.x": "Bip01 Spine1",
    "def_spine_02.x": "Bip01 Spine1",
    "c_spine_02.x": "Bip01 Spine1",
    "spine.002": "Bip01 Spine1",
    "spine_03.x": "Bip01 Spine2",
    "def_spine_03.x": "Bip01 Spine2",
    "c_spine_03.x": "Bip01 Spine2",
    "spine.003": "Bip01 Spine2",

    # Neck & Head
    "neck.x": "Bip01 Neck",
    "def_neck.x": "Bip01 Neck",
    "c_neck.x": "Bip01 Neck",
    "neck": "Bip01 Neck",
    "neck.001": "Bip01 Neck",
    "head.x": "Bip01 Head",
    "def_head.x": "Bip01 Head",
    "c_head.x": "Bip01 Head",
    "head": "Bip01 Head",

    # Left Arm
    "shoulder.l": "Bip01 L Clavicle",
    "def_shoulder.l": "Bip01 L Clavicle",
    "c_shoulder.l": "Bip01 L Clavicle",
    "clavicle_l": "Bip01 L Clavicle",
    "clavicle.l": "Bip01 L Clavicle",
    "arm.l": "Bip01 L UpperArm",
    "def_arm.l": "Bip01 L UpperArm",
    "arm_stretch.l": "Bip01 L UpperArm",
    "c_arm_fk.l": "Bip01 L UpperArm",
    "upperarm_l": "Bip01 L UpperArm",
    "forearm.l": "Bip01 L Forearm",
    "def_forearm.l": "Bip01 L Forearm",
    "forearm_stretch.l": "Bip01 L Forearm",
    "c_forearm_fk.l": "Bip01 L Forearm",
    "lowerarm_l": "Bip01 L Forearm",
    "hand.l": "Bip01 L Hand",
    "def_hand.l": "Bip01 L Hand",
    "c_hand_fk.l": "Bip01 L Hand",
    "hand_l": "Bip01 L Hand",

    # Right Arm
    "shoulder.r": "Bip01 R Clavicle",
    "def_shoulder.r": "Bip01 R Clavicle",
    "c_shoulder.r": "Bip01 R Clavicle",
    "clavicle_r": "Bip01 R Clavicle",
    "clavicle.r": "Bip01 R Clavicle",
    "arm.r": "Bip01 R UpperArm",
    "def_arm.r": "Bip01 R UpperArm",
    "arm_stretch.r": "Bip01 R UpperArm",
    "c_arm_fk.r": "Bip01 R UpperArm",
    "upperarm_r": "Bip01 R UpperArm",
    "forearm.r": "Bip01 R Forearm",
    "def_forearm.r": "Bip01 R Forearm",
    "forearm_stretch.r": "Bip01 R Forearm",
    "c_forearm_fk.r": "Bip01 R Forearm",
    "lowerarm_r": "Bip01 R Forearm",
    "hand.r": "Bip01 R Hand",
    "def_hand.r": "Bip01 R Hand",
    "c_hand_fk.r": "Bip01 R Hand",
    "hand_r": "Bip01 R Hand",

    # Dota / Source Engine Biped Mappings
    "spine_0": "Bip01 Spine",
    "spine_1": "Bip01 Spine1",
    "spine_2": "Bip01 Spine2",
    "spine_3": "Bip01 Spine3",
    "neck_0": "Bip01 Neck",
    "clavicle_L": "Bip01 L Clavicle",
    "clavicle_R": "Bip01 R Clavicle",
    "arm_upper_L": "Bip01 L UpperArm",
    "arm_upper_R": "Bip01 R UpperArm",
    "arm_lower_L": "Bip01 L Forearm",
    "arm_lower_R": "Bip01 R Forearm",
    "hand_L": "Bip01 L Hand",
    "hand_R": "Bip01 R Hand",
    "leg_upper_L": "Bip01 L Thigh",
    "leg_upper_R": "Bip01 R Thigh",
    "leg_lower_L": "Bip01 L Calf",
    "leg_lower_R": "Bip01 R Calf",
    "ankle_L": "Bip01 L Foot",
    "ankle_R": "Bip01 R Foot",
    "ball_L": "Bip01 L Toe0",
    "ball_R": "Bip01 R Toe0",
    "weapon_0_R": "_bone_weapon01",
    "weapon_0_L": "_bone_weapon02",

    # Left Leg
    "thigh.l": "Bip01 L Thigh",
    "def_thigh.l": "Bip01 L Thigh",
    "thigh_stretch.l": "Bip01 L Thigh",
    "c_thigh_fk.l": "Bip01 L Thigh",
    "thigh_l": "Bip01 L Thigh",
    "leg.l": "Bip01 L Calf",
    "def_leg.l": "Bip01 L Calf",
    "leg_stretch.l": "Bip01 L Calf",
    "c_leg_fk.l": "Bip01 L Calf",
    "calf_l": "Bip01 L Calf",
    "shin_l": "Bip01 L Calf",
    "foot.l": "Bip01 L Foot",
    "def_foot.l": "Bip01 L Foot",
    "c_foot_fk.l": "Bip01 L Foot",
    "foot_l": "Bip01 L Foot",
    "toes.l": "Bip01 L Toe0",
    "toes_01.l": "Bip01 L Toe0",
    "def_toes.l": "Bip01 L Toe0",
    "c_toes_fk.l": "Bip01 L Toe0",
    "toe_l": "Bip01 L Toe0",

    # Right Leg
    "thigh.r": "Bip01 R Thigh",
    "def_thigh.r": "Bip01 R Thigh",
    "thigh_stretch.r": "Bip01 R Thigh",
    "c_thigh_fk.r": "Bip01 R Thigh",
    "thigh_r": "Bip01 R Thigh",
    "leg.r": "Bip01 R Calf",
    "def_leg.r": "Bip01 R Calf",
    "leg_stretch.r": "Bip01 R Calf",
    "c_leg_fk.r": "Bip01 R Calf",
    "calf_r": "Bip01 R Calf",
    "shin_r": "Bip01 R Calf",
    "foot.r": "Bip01 R Foot",
    "def_foot.r": "Bip01 R Foot",
    "c_foot_fk.r": "Bip01 R Foot",
    "foot_r": "Bip01 R Foot",
    "toes.r": "Bip01 R Toe0",
    "toes_01.r": "Bip01 R Toe0",
    "def_toes.r": "Bip01 R Toe0",
    "c_toes_fk.r": "Bip01 R Toe0",
    "toe_r": "Bip01 R Toe0",
}

# Left & Right Fingers
for side, s_char, k2_side in [("l", "L", "L"), ("r", "R", "R")]:
    for f_idx, f_name in enumerate(["thumb", "index", "middle", "ring", "pinky"]):
        for p_idx in [1, 2, 3]:
            k2_finger_num = f"{f_idx}" if p_idx == 1 else f"{f_idx}{p_idx - 1}"
            k2_target = f"Bip01 {k2_side} Finger{k2_finger_num}"
            candidates = [
                f"{f_name}{p_idx}.{side}",
                f"def_{f_name}{p_idx}.{side}",
                f"c_{f_name}{p_idx}.{side}",
                f"c_{f_name}{p_idx}1.{side}",
            ]
            for c in candidates:
                KONGOR_RIG_DEFORM_TO_K2[c] = k2_target

# Dota / Source style fingers
for side, s_char, k2_side in [("L", "L", "L"), ("R", "R", "R"), ("l", "L", "L"), ("r", "R", "R")]:
    for f_idx, f_name in enumerate(["thumb", "index", "middle", "ring", "pinky"]):
        for p_idx in [0, 1, 2]:
            k2_finger_num = f"{f_idx}" if p_idx == 0 else f"{f_idx}{p_idx}"
            k2_target = f"Bip01 {k2_side} Finger{k2_finger_num}"
            candidates = [
                f"finger_{f_name}_{p_idx}_{side}",
                f"{f_name}_{p_idx}_{side}",
            ]
            for c in candidates:
                KONGOR_RIG_DEFORM_TO_K2[c] = k2_target

def is_arp_available() -> bool:
    """Check if KONGOR Rig is loaded (either internally or globally)."""
    return bool(
        hasattr(bpy.types, "ARP_OT_retarget")
        or hasattr(bpy.types, "ARP_OT_build_bones")
        or hasattr(bpy.types, "ARP_OT_export")
        or _arp_registered
    )

def try_register_internal_arp() -> bool:
    """Attempt to register the internal KONGOR Rig package bundled with KONGOR Tool."""
    global _arp_registered
    if _arp_registered:
        return True

    if hasattr(bpy.types, "ARP_OT_build_bones") or hasattr(bpy.types, "ARP_OT_retarget"):
        print("[KONGOR TOOL] KONGOR Rig is already loaded in Blender environment.")
        return True

    try:
        from .. import kongor_rig
        kongor_rig.register()
        _arp_registered = True
        return True
    except Exception as e:
        print(f"[KONGOR TOOL] Notice: KONGOR Rig internal registration: {e}")
        return False

def try_unregister_internal_arp():
    """Unregister internal KONGOR Rig module if loaded."""
    global _arp_registered
    if not _arp_registered:
        return

    try:
        from .. import kongor_rig
        kongor_rig.unregister()
        _arp_registered = False
    except Exception as e:
        print(f"[KONGOR TOOL] Error unregistering KONGOR Rig: {e}")

def is_k2_armature(obj: bpy.types.Object) -> bool:
    """Detect if an object is a K2 game armature."""
    if not obj or obj.type != "ARMATURE":
        return False
    bone_names = {b.name for b in obj.data.bones}
    k2_indicators = {"Root", "Bip01", "Bip01 Pelvis", "Bip01 Spine", "Bip01 Head"}
    return bool(bone_names & k2_indicators) or any(name.startswith("_bone") for name in bone_names)

def get_target_armature(context):
    """Retrieve the primary target armature from active selection or scene."""
    act = context.active_object
    if act and act.type == "ARMATURE":
        return act
    for obj in context.selected_objects:
        if obj.type == "ARMATURE":
            return obj
    if hasattr(context.scene, "kongor_arp"):
        if context.scene.kongor_arp.source_k2_rig:
            return context.scene.kongor_arp.source_k2_rig
        if context.scene.kongor_arp.target_arp_rig:
            return context.scene.kongor_arp.target_arp_rig
    return None

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

class KONGOR_OT_conform_k2_hierarchy(Operator):
    """Enforce strict K2 Engine single-root DAG hierarchy (Root -> Bip01 -> Pelvis)"""
    bl_idname = "kongor.conform_k2_hierarchy"
    bl_label = "Conform Hierarchy to K2 Standard"
    bl_description = "Enforce strict K2 DAG parent hierarchy (Root at 0,0,0, Bip01, Pelvis, Spines, Limbs, Sockets)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm_obj = get_target_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "No armature selected or found in scene.")
            return {"CANCELLED"}

        orig_active = context.view_layer.objects.active
        orig_mode = context.mode

        try:
            context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='EDIT')
            ebones = arm_obj.data.edit_bones

            # 1. Root bone at (0, 0, 0)
            root_b = ebones.get("Root")
            if not root_b:
                root_b = ebones.new("Root")
                root_b.head = (0.0, 0.0, 0.0)
                root_b.tail = (0.0, 0.1, 0.0)
                root_b.use_deform = True
            root_b.parent = None

            # 2. Bip01 (Center-of-mass)
            pelvis_b = ebones.get("Bip01 Pelvis")
            bip_b = ebones.get("Bip01")
            if not bip_b:
                bip_b = ebones.new("Bip01")
                if pelvis_b:
                    bip_b.head = pelvis_b.head.copy()
                    tail_offset = 5.0 if pelvis_b.head.length > 50 else 0.1
                    bip_b.tail = bip_b.head + Vector((0.0, 0.0, tail_offset))
                else:
                    bip_b.head = (0.0, 0.0, 1.0)
                    bip_b.tail = (0.0, 0.0, 1.1)
                bip_b.use_deform = True
            bip_b.parent = root_b

            # 3. Pelvis
            if pelvis_b:
                pelvis_b.parent = bip_b
                pelvis_b.use_deform = True

            # 4. Spine Chain
            spine_b = ebones.get("Bip01 Spine")
            if spine_b:
                spine_b.parent = pelvis_b if pelvis_b else (bip_b if bip_b else root_b)
                spine_b.use_deform = True

            spine1_b = ebones.get("Bip01 Spine1")
            if spine1_b:
                spine1_b.parent = spine_b if spine_b else (pelvis_b if pelvis_b else root_b)
                spine1_b.use_deform = True

            spine2_b = ebones.get("Bip01 Spine2")
            if spine2_b:
                spine2_b.parent = spine1_b if spine1_b else (spine_b if spine_b else root_b)
                spine2_b.use_deform = True

            spine3_b = ebones.get("Bip01 Spine3")
            if spine3_b:
                spine3_b.parent = spine2_b if spine2_b else spine1_b
                spine3_b.use_deform = True

            chest_b = spine3_b or spine2_b or spine1_b or spine_b or pelvis_b or root_b

            # 5. Neck & Head
            neck_b = ebones.get("Bip01 Neck")
            if neck_b:
                neck_b.parent = chest_b
                neck_b.use_deform = True

            head_b = ebones.get("Bip01 Head")
            if head_b:
                head_b.parent = neck_b if neck_b else chest_b
                head_b.use_deform = True

            # 6. Limbs & Fingers
            for s in ("L", "R"):
                clav = ebones.get(f"Bip01 {s} Clavicle")
                if clav:
                    clav.parent = chest_b
                    clav.use_deform = True
                uarm = ebones.get(f"Bip01 {s} UpperArm")
                if uarm:
                    uarm.parent = clav if clav else chest_b
                    uarm.use_deform = True
                farm = ebones.get(f"Bip01 {s} Forearm")
                if farm:
                    farm.parent = uarm if uarm else chest_b
                    farm.use_deform = True
                hand = ebones.get(f"Bip01 {s} Hand")
                if hand:
                    hand.parent = farm if farm else chest_b
                    hand.use_deform = True

                # Fingers
                for f_idx in range(5):
                    f_root = ebones.get(f"Bip01 {s} Finger{f_idx}")
                    if f_root:
                        f_root.parent = hand if hand else chest_b
                        f_root.use_deform = True
                    f_mid = ebones.get(f"Bip01 {s} Finger{f_idx}1")
                    if f_mid:
                        f_mid.parent = f_root if f_root else (hand if hand else chest_b)
                        f_mid.use_deform = True
                    f_tip = ebones.get(f"Bip01 {s} Finger{f_idx}2")
                    if f_tip:
                        f_tip.parent = f_mid if f_mid else (f_root if f_root else hand)
                        f_tip.use_deform = True

                # Legs
                thigh = ebones.get(f"Bip01 {s} Thigh")
                if thigh:
                    thigh.parent = pelvis_b if pelvis_b else root_b
                    thigh.use_deform = True
                calf = ebones.get(f"Bip01 {s} Calf")
                if calf:
                    calf.parent = thigh if thigh else pelvis_b
                    calf.use_deform = True
                foot = ebones.get(f"Bip01 {s} Foot")
                if foot:
                    foot.parent = calf if calf else thigh
                    foot.use_deform = True
                toe = ebones.get(f"Bip01 {s} Toe0")
                if toe:
                    toe.parent = foot if foot else calf
                    toe.use_deform = True

            # 7. Sockets
            w1 = ebones.get("_bone_weapon01")
            if w1:
                w1.parent = ebones.get("Bip01 R Hand") or chest_b
                w1.use_deform = True
            w2 = ebones.get("_bone_weapon02")
            if w2:
                w2.parent = ebones.get("Bip01 L Hand") or chest_b
                w2.use_deform = True
            oh = ebones.get("_bone_overhead")
            if oh:
                oh.parent = head_b or neck_b or chest_b
                oh.use_deform = True
            ch = ebones.get("_bone_chest")
            if ch:
                ch.parent = chest_b
                ch.use_deform = True
            el = ebones.get("_bone_lefteye")
            if el:
                el.parent = head_b or chest_b
                el.use_deform = True
            er = ebones.get("_bone_righteye")
            if er:
                er.parent = head_b or chest_b
                er.use_deform = True

            # 8. Single-Root DAG Integrity (No multiple roots)
            reparented_orphans = 0
            for eb in ebones:
                if eb.parent is None and eb.name != "Root":
                    eb.parent = root_b
                    reparented_orphans += 1

            bpy.ops.object.mode_set(mode='OBJECT')
            if orig_active:
                context.view_layer.objects.active = orig_active

            self.report({"INFO"}, f"Conformed K2 DAG hierarchy on '{arm_obj.name}'. ({reparented_orphans} orphan(s) parented to Root)")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error conforming K2 hierarchy: {e}")
            return {"CANCELLED"}

class KONGOR_OT_add_k2_sockets(Operator):
    """Add standard K2 Engine leaf sockets (_bone_weapon01, _bone_overhead, etc.)"""
    bl_idname = "kongor.add_k2_sockets"
    bl_label = "Add Standard K2 Sockets"
    bl_description = "Add standard K2 leaf socket bones (_bone_weapon01/02, _bone_overhead, _bone_chest, _bone_lefteye/righteye)"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm_obj = get_target_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "No armature selected or found in scene.")
            return {"CANCELLED"}

        orig_active = context.view_layer.objects.active
        try:
            context.view_layer.objects.active = arm_obj
            bpy.ops.object.mode_set(mode='EDIT')
            ebones = arm_obj.data.edit_bones

            # Calculate biped frame for orientation-invariant, properly scaled socket placement
            pelvis_b = ebones.get("Bip01 Pelvis") or ebones.get("pelvis")
            head_b = ebones.get("Bip01 Head") or ebones.get("head")
            r_thigh = ebones.get("Bip01 R Thigh") or ebones.get("thigh.r")
            l_thigh = ebones.get("Bip01 L Thigh") or ebones.get("thigh.l")

            if pelvis_b and head_b:
                spine_vec = head_b.head - pelvis_b.head
                spine_len = max(spine_vec.length, 1.0)
                up_dir = spine_vec.normalized()
                lat_vec = (r_thigh.head - l_thigh.head) if (r_thigh and l_thigh) else Vector((-1.0, 0.0, 0.0))
                right_dir = lat_vec.normalized()
                fwd_dir = right_dir.cross(up_dir).normalized()
            else:
                spine_len = 50.0
                up_dir = Vector((0.0, 1.0, 0.0))
                right_dir = Vector((-1.0, 0.0, 0.0))
                fwd_dir = Vector((0.0, 0.0, -1.0))

            added_count = 0
            for s_name, parent_name, offset in K2_SOCKETS_DEF:
                s_bone = ebones.get(s_name)
                parent_bone = ebones.get(parent_name)

                # Fallback parent if specific bone not found
                if not parent_bone:
                    if "Hand" in parent_name:
                        parent_bone = ebones.get("Bip01 Spine1") or ebones.get("Bip01 Pelvis")
                    elif "Head" in parent_name:
                        parent_bone = ebones.get("Bip01 Neck") or ebones.get("Bip01 Spine1")

                # Compute standard, human-visible socket coordinates
                if s_name == "_bone_overhead" and head_b:
                    target_head = head_b.head + up_dir * (spine_len * 0.75)
                    target_tail = target_head + up_dir * (spine_len * 0.3)
                elif s_name == "_bone_chest" and parent_bone:
                    target_head = parent_bone.head + fwd_dir * (spine_len * 0.25)
                    target_tail = target_head + fwd_dir * (spine_len * 0.2)
                elif s_name == "_bone_lefteye" and head_b:
                    target_head = head_b.head + fwd_dir * (spine_len * 0.18) - right_dir * (spine_len * 0.07) + up_dir * (spine_len * 0.08)
                    target_tail = target_head + fwd_dir * (spine_len * 0.1)
                elif s_name == "_bone_righteye" and head_b:
                    target_head = head_b.head + fwd_dir * (spine_len * 0.18) + right_dir * (spine_len * 0.07) + up_dir * (spine_len * 0.08)
                    target_tail = target_head + fwd_dir * (spine_len * 0.1)
                elif parent_bone:
                    if s_bone and s_bone.length >= 1.0:
                        target_head = s_bone.head
                        target_tail = s_bone.tail
                    else:
                        hand_dir = (parent_bone.tail - parent_bone.head).normalized() if parent_bone.length > 0 else up_dir
                        target_head = parent_bone.tail
                        target_tail = target_head + hand_dir * (spine_len * 0.25)
                else:
                    target_head = Vector((0.0, 0.0, 0.0))
                    target_tail = Vector((0.0, 1.0, 0.0))

                if not s_bone:
                    if parent_bone:
                        s_bone = ebones.new(s_name)
                        s_bone.head = target_head
                        s_bone.tail = target_tail
                        s_bone.parent = parent_bone
                        s_bone.use_deform = True
                        s_bone.use_connect = False
                        added_count += 1
                else:
                    if parent_bone and s_bone.parent != parent_bone:
                        s_bone.parent = parent_bone
                    if s_bone.length < 1.0 or s_name in ("_bone_overhead", "_bone_chest", "_bone_lefteye", "_bone_righteye"):
                        s_bone.head = target_head
                        s_bone.tail = target_tail
                    s_bone.use_deform = True

            bpy.ops.object.mode_set(mode='OBJECT')
            # Enable visible in-front display and names
            arm_obj.show_in_front = True
            arm_obj.data.show_names = True
            arm_obj.data.display_type = 'OCTAHEDRAL'

            if orig_active:
                context.view_layer.objects.active = orig_active

            self.report({"INFO"}, f"Added / verified {len(K2_SOCKETS_DEF)} K2 sockets on '{arm_obj.name}' ({added_count} newly created).")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Error adding K2 sockets: {e}")
            return {"CANCELLED"}

class KONGOR_OT_generate_k2_skeleton(Operator):
    """Generate a clean K2 Game Armature from active KONGOR Rig with live follow constraints"""
    bl_idname = "kongor.generate_k2_skeleton"
    bl_label = "Generate K2 Game Armature"
    bl_description = "Create a clean, game-ready K2 skeleton following KONGOR Rig controls live"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        src_arm = get_target_armature(context)
        if not src_arm:
            self.report({"WARNING"}, "No active armature found to generate K2 skeleton from.")
            return {"CANCELLED"}

        try:
            # 1. Create new armature data & object
            new_name = f"{src_arm.name}_K2"
            k2_arm_data = bpy.data.armatures.new(name=f"{new_name}_Data")
            k2_arm_obj = bpy.data.objects.new(name=new_name, object_data=k2_arm_data)
            context.collection.objects.link(k2_arm_obj)
            k2_arm_obj.matrix_world = src_arm.matrix_world.copy()

            # 2. Enter EDIT mode to build bones
            context.view_layer.objects.active = k2_arm_obj
            bpy.ops.object.mode_set(mode='EDIT')
            new_ebones = k2_arm_data.edit_bones

            # Gather bones from source rig
            bone_map_pairs = []
            for b in src_arm.data.bones:
                k2_name = None
                if b.name in KONGOR_RIG_DEFORM_TO_K2:
                    k2_name = KONGOR_RIG_DEFORM_TO_K2[b.name]
                elif b.name.startswith("Bip01") or b.name.startswith("_bone_") or b.name == "Root":
                    k2_name = b.name
                elif b.use_deform and not any(b.name.lower().startswith(p) for p in ("c_", "ik_", "pole_", "root_", "mch_", "org_")):
                    k2_name = b.name

                if k2_name:
                    bone_map_pairs.append((b.name, k2_name, b.head_local, b.tail_local, b.roll))

            # Create edit bones in new skeleton
            for src_name, k2_name, head, tail, roll in bone_map_pairs:
                if k2_name not in new_ebones:
                    nb = new_ebones.new(k2_name)
                    nb.head = head
                    nb.tail = tail
                    nb.roll = roll
                    nb.use_deform = True

            # 3. Conform hierarchy & add sockets
            bpy.ops.object.mode_set(mode='OBJECT')
            context.view_layer.objects.active = k2_arm_obj
            bpy.ops.kongor.conform_k2_hierarchy()
            bpy.ops.kongor.add_k2_sockets()

            # 4. Bind with Copy Transforms constraints
            context.view_layer.objects.active = k2_arm_obj
            bpy.ops.object.mode_set(mode='POSE')
            bound_count = 0
            for pb in k2_arm_obj.pose.bones:
                # Find matching target in source rig
                matching_src = None
                for src_name, k2_name, _, _, _ in bone_map_pairs:
                    if k2_name == pb.name and src_name in src_arm.pose.bones:
                        matching_src = src_name
                        break
                if not matching_src and pb.name in src_arm.pose.bones:
                    matching_src = pb.name

                if matching_src:
                    c = pb.constraints.new(type="COPY_TRANSFORMS")
                    c.name = "K2_ARP_Follow"
                    c.target = src_arm
                    c.subtarget = matching_src
                    c.owner_space = "WORLD"
                    c.target_space = "WORLD"
                    bound_count += 1

            bpy.ops.object.mode_set(mode='OBJECT')

            # 5. Store in settings
            if hasattr(context.scene, "kongor_arp"):
                context.scene.kongor_arp.source_k2_rig = k2_arm_obj
                context.scene.kongor_arp.target_arp_rig = src_arm

            k2_arm_obj.show_in_front = True
            k2_arm_data.display_type = 'OCTAHEDRAL'

            self.report({"INFO"}, f"Generated K2 Game Skeleton '{k2_arm_obj.name}' ({bound_count} bones bound live to '{src_arm.name}').")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to generate K2 skeleton: {e}")
            return {"CANCELLED"}

class KONGOR_OT_isolate_k2_deform(Operator):
    """Enforce strict K2 deform bone flags (Bip01 and sockets ON, controls OFF)"""
    bl_idname = "kongor.isolate_k2_deform"
    bl_label = "Isolate K2 Deform Bones"
    bl_description = "Ensure only actual K2 deform bones and sockets have deform flag enabled for export"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        arm_obj = get_target_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "No armature found.")
            return {"CANCELLED"}

        deform_count = 0
        non_deform_count = 0

        for b in arm_obj.data.bones:
            name_lower = b.name.lower()
            is_socket = b.name.startswith("_bone_")
            is_bip = b.name.startswith("Bip01") or b.name == "Root"
            is_control = any(name_lower.startswith(p) for p in ("c_", "ik_", "pole", "cont_", "root_", "widget", "mch_", "org_"))

            if is_socket or is_bip:
                b.use_deform = True
                deform_count += 1
            elif is_control:
                b.use_deform = False
                non_deform_count += 1
            elif b.use_deform:
                deform_count += 1
            else:
                non_deform_count += 1

        self.report({"INFO"}, f"K2 Deform Isolation: {deform_count} deform bones ON, {non_deform_count} controls OFF.")
        return {"FINISHED"}

class KONGOR_OT_remap_to_k2_universal(Operator):
    """Universal bone and vertex group remapper for KONGOR Rig and K2 Engine"""
    bl_idname = "kongor.remap_to_k2_universal"
    bl_label = "Universal Remap to K2 (Bip01)"
    bl_description = "Remap KONGOR Rig / Rig Creator / Mixamo bones and vertex groups to official K2 Bip01"
    bl_options = {"REGISTER", "UNDO"}

    reverse: BoolProperty(
        name="Reverse Mapping",
        description="Convert K2 standard Bip01 names back to deform (def_) names",
        default=False,
    )

    def execute(self, context):
        arm_obj = get_target_armature(context)
        if not arm_obj:
            self.report({"WARNING"}, "No armature found.")
            return {"CANCELLED"}

        mapping = {v: k for k, v in KONGOR_RIG_DEFORM_TO_K2.items()} if self.reverse else KONGOR_RIG_DEFORM_TO_K2
        renamed_bones = 0

        for old_name, new_name in mapping.items():
            b = arm_obj.data.bones.get(old_name)
            if b:
                b.name = new_name
                renamed_bones += 1

        # Also rename vertex groups on child meshes
        renamed_vgs = 0
        for obj in bpy.data.objects:
            if obj.type == "MESH" and (obj.parent == arm_obj or any(m.type == "ARMATURE" and m.object == arm_obj for m in obj.modifiers)):
                for old_name, new_name in mapping.items():
                    vg = obj.vertex_groups.get(old_name)
                    if vg:
                        vg.name = new_name
                        renamed_vgs += 1

        direction = "To K2 Bip01" if not self.reverse else "To Def Names"
        self.report({"INFO"}, f"Universal Remap ({direction}): {renamed_bones} bones, {renamed_vgs} vertex groups renamed.")
        return {"FINISHED"}

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
            "kongor_rig",
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
    """Set KONGOR Rig remap preset to K2 Biped (k2_biped.bmap)"""
    bl_idname = "kongor.arp_apply_k2_preset"
    bl_label = "Load K2 Biped Preset (.bmap)"
    bl_description = "Configure KONGOR Rig Remap tool with the official K2 Biped bone mapping"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        preset_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "kongor_rig",
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
    KONGOR_OT_conform_k2_hierarchy,
    KONGOR_OT_add_k2_sockets,
    KONGOR_OT_generate_k2_skeleton,
    KONGOR_OT_isolate_k2_deform,
    KONGOR_OT_remap_to_k2_universal,
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

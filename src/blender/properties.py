"""
KONGOR TOOL - Modern Blender Property Definitions
Designed for Blender >= 4.2 / 5.0.
Clean Architecture without legacy baggage.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
)

class KongorModelImportSettings(bpy.types.PropertyGroup):
    flip_v: BoolProperty(
        name="Flip UV (V-Axis)",
        description="Invert V texture coordinate (1.0 - V) for standard DirectX / Blender UV mapping",
        default=True,
    )
    build_materials: BoolProperty(
        name="Build Materials",
        description="Generate Principled BSDF shader materials from K2 material specifications",
        default=True,
    )
    bones_in_front: BoolProperty(
        name="Bones In Front (X-Ray)",
        description="Display skeleton bones in front of character mesh geometry",
        default=True,
    )
    show_bone_names: BoolProperty(
        name="Show Bone Names",
        description="Display bone names next to skeleton joints in 3D Viewport",
        default=False,
    )

class KongorModelExportSettings(bpy.types.PropertyGroup):
    target_engine: EnumProperty(
        name="Project KONGOR",
        description="Select HoN engine target and material shader format",
        items=[
            ("HON_PBT", "HoN x64 PBT (Classic S2)", "Heroes of Newerth x64 PBT (Project Bradley) native classic shaders"),
            ("HON_REBORN", "HoN Reborn (PBR)", "Heroes of Newerth Reborn modern PBR shaders"),
        ],
        default="Project KONGOR",
    )
    flip_v: BoolProperty(
        name="Flip UV (V-Axis)",
        description="Invert V texture coordinate (1.0 - V) for K2 Engine standard",
        default=True,
    )
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply object modifiers during export",
        default=True,
    )
    export_materials: BoolProperty(
        name="Generate .material",
        description="Write companion K2 XML .material files for each exported mesh",
        default=True,
    )
    export_mdf: BoolProperty(
        name="Generate .mdf",
        description="Write companion K2 Model Definition File (.mdf)",
        default=True,
    )
    export_deform_only: BoolProperty(
        name="Export Deform Bones Only",
        description="Export only deforming bones (skips IK controls, helpers, and widgets). Essential for Rig Creator and game rigs",
        default=True,
    )

class KongorClipSettings(bpy.types.PropertyGroup):
    frame_start: IntProperty(
        name="Start Frame",
        description="Initial animation frame to export",
        default=1,
    )
    frame_end: IntProperty(
        name="End Frame",
        description="Final animation frame to export",
        default=250,
    )
    fps: IntProperty(
        name="Frames Per Second",
        description="Target framerate for animation playback",
        default=30,
        min=1,
    )
    export_deform_only: BoolProperty(
        name="Export Deform Bones Only",
        description="Export only deforming bones (skips IK controls). Bakes evaluated constraint motions into K2 clip channels",
        default=True,
    )

class KongorObjectSettings(bpy.types.PropertyGroup):
    is_collision_surface: BoolProperty(
        name="Collision Surface",
        description="Export this mesh as a K2 'surf' collision convex polyhedron instead of a visual mesh",
        default=False,
    )
    bonelink: IntProperty(
        name="Rigid Bone Link Index",
        description="Attach all mesh vertices rigidly to a single bone (-1 for blended vertex skinning)",
        default=-1,
    )

root_pkg = __package__.rsplit(".blender", 1)[0] if ".blender" in __package__ else __package__

class KONGOR_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = root_pkg

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        box.label(text="KONGOR TOOL v5.0.0", icon="TOOL_SETTINGS")
        box.label(text="Heroes of Newerth K2 Engine Model & Animation (.model / .clip) Tool")
        box.separator()
        row = box.row()
        row.alert = True
        row.operator("kongor.uninstall", text="Uninstall", icon="TRASH")

classes = (
    KongorModelImportSettings,
    KongorModelExportSettings,
    KongorClipSettings,
    KongorObjectSettings,
    KONGOR_AddonPreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.kongor_import = PointerProperty(type=KongorModelImportSettings)
    bpy.types.Scene.kongor_export = PointerProperty(type=KongorModelExportSettings)
    bpy.types.Scene.kongor_clip = PointerProperty(type=KongorClipSettings)
    bpy.types.Object.kongor = PointerProperty(type=KongorObjectSettings)

def unregister():
    if hasattr(bpy.types.Object, "kongor"):
        del bpy.types.Object.kongor
    if hasattr(bpy.types.Scene, "kongor_clip"):
        del bpy.types.Scene.kongor_clip
    if hasattr(bpy.types.Scene, "kongor_export"):
        del bpy.types.Scene.kongor_export
    if hasattr(bpy.types.Scene, "kongor_import"):
        del bpy.types.Scene.kongor_import
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

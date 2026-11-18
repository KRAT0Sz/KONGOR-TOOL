"""
Blender PropertyGroups for KONGOR TOOL.
Settings for Import, Export, and Mesh configuration.
"""

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)

class K2ImportSettings(bpy.types.PropertyGroup):
    flip_uv: BoolProperty(
        name="Flip UV (V-Axis)",
        description="Invert V coordinate (1.0 - V) for standard DirectX / Blender UV mapping",
        default=True,
    )
    import_textures: BoolProperty(
        name="Import Textures",
        description="Search for and load matching DDS/PNG/TGA texture files",
        default=True,
    )
    import_materials: BoolProperty(
        name="Import Materials",
        description="Create Principled BSDF shader materials for each mesh",
        default=True,
    )
    tex_color: BoolProperty(
        name="Color / Diffuse",
        description="Load diffuse / albedo texture (_color, _albedo)",
        default=True,
    )
    tex_normal: BoolProperty(
        name="Normal Map",
        description="Load normal map texture (_norm, _normal)",
        default=True,
    )
    tex_mrao: BoolProperty(
        name="MRAO / Specular",
        description="Load metallic, roughness, AO texture (_mrao, _spec)",
        default=True,
    )
    tex_emissive: BoolProperty(
        name="Emissive / Glow",
        description="Load emissive texture (_glow, _emissive)",
        default=True,
    )

class K2ExportSettings(bpy.types.PropertyGroup):
    export_mode: EnumProperty(
        name="Export Mode",
        items=[
            ("ANIMATED", "Animated Mesh", "Export with armature and vertex bone skinning"),
            ("STATIC", "Static Mesh", "Export as static unskinned mesh without armature"),
        ],
        default="ANIMATED",
    )
    force_static: BoolProperty(
        name="Force Static",
        description="Strip all armature links and export purely static geometry",
        default=False,
    )
    remove_hierarchy: BoolProperty(
        name="Flatten Hierarchy",
        description="Flatten bone hierarchy on export (all bones parented to root)",
        default=False,
    )
    copy_textures: BoolProperty(
        name="Copy Textures",
        description="Copy linked textures next to the exported .model file",
        default=False,
    )
    export_geometry: BoolProperty(
        name="Export Geometry",
        description="Write .model binary geometry file",
        default=True,
    )
    export_materials: BoolProperty(
        name="Export Materials",
        description="Generate K2 XML companion .material files",
        default=True,
    )
    export_model_def: BoolProperty(
        name="Export MDF",
        description="Generate K2 XML companion .mdf (Model Definition) file",
        default=True,
    )
    export_animation: BoolProperty(
        name="Export Animation",
        description="Export active action to .clip animation file alongside model",
        default=False,
    )
    frame_start: IntProperty(
        name="Start Frame",
        description="First frame of animation to export",
        default=1,
    )
    frame_end: IntProperty(
        name="End Frame",
        description="Last frame of animation to export",
        default=250,
    )

class K2MeshSettings(bpy.types.PropertyGroup):
    is_collision_surface: BoolProperty(
        name="Collision Surface",
        description="Export this mesh as a K2 'surf' collision hull instead of a visual mesh",
        default=False,
    )
    bonelink: IntProperty(
        name="Rigid Bone Link",
        description="Rigidly attach entire mesh to this bone index (-1 for skinned vertex weights)",
        default=-1,
    )

classes = (
    K2ImportSettings,
    K2ExportSettings,
    K2MeshSettings,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.k2_import_settings = PointerProperty(type=K2ImportSettings)
    bpy.types.Scene.k2_export_settings = PointerProperty(type=K2ExportSettings)
    bpy.types.Object.k2_mesh_settings = PointerProperty(type=K2MeshSettings)

def unregister():
    del bpy.types.Object.k2_mesh_settings
    del bpy.types.Scene.k2_export_settings
    del bpy.types.Scene.k2_import_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

"""
KONGOR TOOL - Modern Blender UI Panels
Professional 3D Viewport Sidebar N-Panel and File Menu integrations.
Designed for Blender >= 4.2 / 5.0 with zero legacy structure.
"""

import bpy

class KONGOR_PT_main_panel(bpy.types.Panel):
    """Primary N-Panel in 3D Viewport for KONGOR TOOL"""
    bl_label = "KONGOR TOOL (v5.0.0)"
    bl_idname = "KONGOR_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Heroes of Newerth K2 Engine Tool", icon="TOOL_SETTINGS")
        col.operator("kongor.inspect_scene", text="Inspect Scene Objects", icon="INFO")

class KONGOR_PT_import_panel(bpy.types.Panel):
    """Import subpanel for K2 Models and Clips"""
    bl_label = "Import K2 Assets"
    bl_idname = "KONGOR_PT_import_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "KONGOR_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kongor_import

        row = layout.row(align=True)
        row.operator("kongor.import_model", text="Import Model", icon="IMPORT")
        row.operator("kongor.import_clip", text="Import Clip", icon="ANIM")

        box = layout.box()
        box.label(text="Import Options:")
        col = box.column(align=True)
        col.prop(settings, "flip_v")
        col.prop(settings, "build_materials")

class KONGOR_PT_export_model_panel(bpy.types.Panel):
    """Export subpanel for K2 Models"""
    bl_label = "Export K2 Model"
    bl_idname = "KONGOR_PT_export_model_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "KONGOR_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kongor_export

        layout.operator("kongor.export_model", text="Export .model", icon="EXPORT")

        box = layout.box()
        box.label(text="Model Export Options:")
        col = box.column(align=True)
        col.prop(settings, "flip_v")
        col.prop(settings, "apply_modifiers")
        col.prop(settings, "export_materials")
        col.prop(settings, "export_mdf")

class KONGOR_PT_export_clip_panel(bpy.types.Panel):
    """Export subpanel for K2 Animation Clips"""
    bl_label = "Export K2 Clip"
    bl_idname = "KONGOR_PT_export_clip_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "KONGOR_PT_main_panel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.kongor_clip

        layout.operator("kongor.export_clip", text="Export .clip", icon="RENDER_ANIMATION")

        box = layout.box()
        box.label(text="Clip Animation Options:")
        col = box.column(align=True)
        col.prop(settings, "frame_start")
        col.prop(settings, "frame_end")
        col.prop(settings, "fps")

class KONGOR_PT_object_panel(bpy.types.Panel):
    """Per-object K2 Settings (Collision Surface, Rigid Bone Link)"""
    bl_label = "Active Object K2 Properties"
    bl_idname = "KONGOR_PT_object_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "KONGOR_PT_main_panel"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = obj.kongor

        box = layout.box()
        box.prop(settings, "is_collision_surface")
        if not settings.is_collision_surface:
            box.prop(settings, "bonelink")

def menu_func_import(self, context):
    self.layout.operator("kongor.import_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.import_clip", text="Heroes of Newerth Clip (.clip)")

def menu_func_export(self, context):
    self.layout.operator("kongor.export_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.export_clip", text="Heroes of Newerth Clip (.clip)")

classes = (
    KONGOR_PT_main_panel,
    KONGOR_PT_import_panel,
    KONGOR_PT_export_model_panel,
    KONGOR_PT_export_clip_panel,
    KONGOR_PT_object_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

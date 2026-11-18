"""
Blender 3D Viewport N-Panel and Topbar File Menu integrations for KONGOR TOOL.
"""

import bpy

class K2_PT_MainPanel(bpy.types.Panel):
    bl_label = "KONGOR TOOL (v5.0.0)"
    bl_idname = "K2_PT_MainPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="K2 Engine Clean Architecture Tool", icon="TOOL_SETTINGS")
        col.operator("k2.scene_info", text="Scene Info", icon="INFO")

class K2_PT_ImportPanel(bpy.types.Panel):
    bl_label = "Import (.model / .clip)"
    bl_idname = "K2_PT_ImportPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "K2_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.k2_import_settings

        row = layout.row(align=True)
        row.operator("import_mesh.k2", text="Import Model", icon="IMPORT")
        row.operator("import_clip.k2", text="Import Clip", icon="ANIM")

        layout.separator()
        layout.prop(settings, "flip_uv")
        layout.prop(settings, "import_materials")
        layout.prop(settings, "import_textures")

        if settings.import_textures:
            box = layout.box()
            box.label(text="Texture Channels:")
            col = box.column(align=True)
            col.prop(settings, "tex_color")
            col.prop(settings, "tex_normal")
            col.prop(settings, "tex_mrao")
            col.prop(settings, "tex_emissive")

class K2_PT_ExportPanel(bpy.types.Panel):
    bl_label = "Export (.model / .clip)"
    bl_idname = "K2_PT_ExportPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "K2_PT_MainPanel"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.k2_export_settings

        layout.label(text="Export Mode:")
        layout.prop(settings, "export_mode", expand=True)

        box = layout.box()
        box.label(text="Options:")
        col = box.column(align=True)
        col.prop(settings, "force_static")
        col.prop(settings, "remove_hierarchy")
        col.prop(settings, "export_geometry")
        col.prop(settings, "export_materials")
        col.prop(settings, "export_model_def")

        layout.separator()
        row = layout.row(align=True)
        row.operator("export_mesh.k2", text="Export Model", icon="EXPORT")

class K2_PT_MeshSettingsPanel(bpy.types.Panel):
    bl_label = "K2 Mesh & Collision Settings"
    bl_idname = "K2_PT_MeshSettingsPanel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "KONGOR Tool"
    bl_parent_id = "K2_PT_MainPanel"

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == "MESH"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object
        settings = obj.k2_mesh_settings

        layout.prop(settings, "is_collision_surface")
        if not settings.is_collision_surface:
            layout.prop(settings, "bonelink")

def menu_func_import(self, context):
    self.layout.operator("import_mesh.k2", text="K2 Model (.model)")
    self.layout.operator("import_clip.k2", text="K2 Clip (.clip)")

def menu_func_export(self, context):
    self.layout.operator("export_mesh.k2", text="K2 Model (.model)")

classes = (
    K2_PT_MainPanel,
    K2_PT_ImportPanel,
    K2_PT_ExportPanel,
    K2_PT_MeshSettingsPanel,
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

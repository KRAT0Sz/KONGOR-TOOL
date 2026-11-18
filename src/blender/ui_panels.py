"""
KONGOR TOOL - Modern Blender Menus & Bottom Navbar Integration
Provides a horizontal navbar right above the Timeline / bottom of 3D Viewport,
plus an independent Floating Dialog and 3D Viewport Header Menu.
Zero N-Panel clutter.
"""

import bpy

class KONGOR_MT_main_menu(bpy.types.Menu):
    """Top header dropdown menu in 3D Viewport"""
    bl_label = "KONGOR Tool"
    bl_idname = "KONGOR_MT_main_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.dialog", text="Open KONGOR Tool Window...", icon="WINDOW")
        layout.separator()
        layout.operator("kongor.import_model", text="Import K2 Model (.model)", icon="IMPORT")
        layout.operator("kongor.export_model", text="Export K2 Model (.model)", icon="EXPORT")
        layout.separator()
        layout.operator("kongor.import_clip", text="Import K2 Clip (.clip)", icon="ANIM")
        layout.operator("kongor.export_clip", text="Export K2 Clip (.clip)", icon="RENDER_ANIMATION")
        layout.separator()
        layout.operator("kongor.inspect_scene", text="Inspect Scene Objects", icon="INFO")
        layout.separator()
        layout.operator("kongor.uninstall", text="Uninstall Extension...", icon="TRASH")

def draw_viewport_header_menu(self, context):
    self.layout.menu("KONGOR_MT_main_menu")

def draw_bottom_navbar(self, context):
    """Draws a horizontal navigation bar at the bottom boundary above the Timeline"""
    layout = self.layout
    layout.separator()
    sub = layout.row(align=True)
    sub.operator("kongor.dialog", text="KONGOR Tool", icon="TOOL_SETTINGS")
    sub.operator("kongor.import_model", text="Import Model", icon="IMPORT")
    sub.operator("kongor.export_model", text="Export Model", icon="EXPORT")
    sub.operator("kongor.import_clip", text="Import Clip", icon="ANIM")
    sub.operator("kongor.export_clip", text="Export Clip", icon="RENDER_ANIMATION")

def menu_func_import(self, context):
    self.layout.operator("kongor.import_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.import_clip", text="Heroes of Newerth Clip (.clip)")

def menu_func_export(self, context):
    self.layout.operator("kongor.export_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.export_clip", text="Heroes of Newerth Clip (.clip)")

classes = (
    KONGOR_MT_main_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_editor_menus.append(draw_viewport_header_menu)
    bpy.types.DOPESHEET_HT_header.append(draw_bottom_navbar)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.DOPESHEET_HT_header.remove(draw_bottom_navbar)
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_viewport_header_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

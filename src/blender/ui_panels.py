"""
KONGOR TOOL - Modern Blender Menus & Header Integration
Provides a 3D Viewport Header Menu and triggers the Floating Navbar above the Timeline.
Zero N-Panel clutter and zero Timeline header clutter.
"""

import bpy

class KONGOR_MT_main_menu(bpy.types.Menu):
    """Top header dropdown menu in 3D Viewport"""
    bl_label = "KONGOR Tool"
    bl_idname = "KONGOR_MT_main_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.floating_bar", text="Toggle Floating Navbar", icon="VIEW_PAN")
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

def menu_func_import(self, context):
    self.layout.operator("kongor.import_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.import_clip", text="Heroes of Newerth Clip (.clip)")

def menu_func_export(self, context):
    self.layout.operator("kongor.export_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.export_clip", text="Heroes of Newerth Clip (.clip)")

def _auto_start_floating_bar():
    try:
        # Check if 3D Viewport is ready and start floating navbar
        for window in bpy.context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    for region in area.regions:
                        if region.type == "WINDOW":
                            with bpy.context.temp_override(window=window, screen=screen, area=area, region=region):
                                bpy.ops.kongor.floating_bar("INVOKE_DEFAULT")
                            return None
    except Exception:
        pass
    return None

classes = (
    KONGOR_MT_main_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_editor_menus.append(draw_viewport_header_menu)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)
    bpy.app.timers.register(_auto_start_floating_bar, first_interval=0.5)

def unregister():
    if bpy.app.timers.is_registered(_auto_start_floating_bar):
        bpy.app.timers.unregister(_auto_start_floating_bar)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_viewport_header_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

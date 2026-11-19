"""
KONGOR TOOL - Modern Blender Menus & Header Integration
Provides a 3D Viewport Header Menu and Native Floating Dialog.
Zero N-Panel and zero Viewport clutter.
"""

import bpy
from .operators import get_target_armatures

class KONGOR_MT_arp_menu(bpy.types.Menu):
    """Auto-Rig Pro & K2 Bridge Menu"""
    bl_label = "Auto-Rig Pro Bridge"
    bl_idname = "KONGOR_MT_arp_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.arp_apply_k2_preset", text="Load K2 Biped Preset (.bmap)", icon="PRESET")
        layout.separator()
        layout.operator("kongor.arp_bind", text="Bind K2 Armature to ARP Rig", icon="CONSTRAINT_BONE")
        layout.operator("kongor.arp_unbind", text="Unbind K2 Armature", icon="X")
        layout.separator()
        layout.operator("kongor.arp_bake", text="Bake ARP Animation to K2 Skeleton", icon="ACTION")

class KONGOR_MT_rigging_menu(bpy.types.Menu):
    """Rig Creator & K2 Rigging Tools Menu"""
    bl_label = "K2 Rig Creator"
    bl_idname = "KONGOR_MT_rigging_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.add_k2_rig", text="Add K2 Game Human Rig", icon="OUTLINER_OB_ARMATURE")
        layout.separator()
        layout.operator("kongor.remap_to_k2", text="Remap Bones to K2 Standard (Bip01)", icon="SYNTAX_ON").reverse = False
        layout.operator("kongor.remap_to_k2", text="Remap Bones to Rig Creator (def_)", icon="SYNTAX_OFF").reverse = True
        layout.operator("kongor.setup_k2_deform", text="Prepare Rig for K2 Export", icon="CHECKMARK")
        layout.separator()
        layout.operator("kongor.fit_bone_size", text="Auto-Fit Bone Sizes", icon="ARROW_LEFTRIGHT")
        layout.separator()
        layout.menu("rgc.add_armature", text="All Rig Creator Presets...", icon="FILE_BLEND")
        layout.separator()
        layout.menu("KONGOR_MT_arp_menu", text="Auto-Rig Pro Bridge...", icon="POSE_HLT")

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
        layout.menu("KONGOR_MT_rigging_menu", text="K2 Rig Creator Tools", icon="ARMATURE_DATA")
        layout.menu("KONGOR_MT_arp_menu", text="Auto-Rig Pro Tools", icon="POSE_HLT")
        layout.separator()
        layout.operator("kongor.toggle_bones", text="Toggle Bones (Show/Hide)", icon="BONE_DATA")
        layout.operator("kongor.toggle_bone_names", text="Toggle Bone Names", icon="SYNTAX_ON")
        layout.operator("kongor.toggle_bone_xray", text="Toggle Bones In Front (X-Ray)", icon="XRAY")
        layout.operator("kongor.fit_bone_size", text="Auto-Fit Bone Sizes", icon="ARROW_LEFTRIGHT")
        layout.separator()
        layout.operator("kongor.inspect_scene", text="Inspect Scene Objects", icon="INFO")
        layout.separator()
        layout.operator("kongor.uninstall", text="Manage Extension...", icon="PREFERENCES")

def draw_viewport_header_menu(self, context):
    layout = self.layout
    layout.menu("KONGOR_MT_main_menu")

    target_arms = get_target_armatures(context)
    bones_vis = any(not a.hide_get() and not a.hide_viewport for a in target_arms) if target_arms else False
    names_vis = any(a.data.show_names for a in target_arms if a.data) if target_arms else False
    xray_vis = any(a.show_in_front for a in target_arms) if target_arms else False

    row = layout.row(align=True)
    row.operator("kongor.toggle_bones", text="", icon="BONE_DATA", depress=bones_vis)
    row.operator("kongor.toggle_bone_names", text="", icon="SYNTAX_ON", depress=names_vis)
    row.operator("kongor.toggle_bone_xray", text="", icon="XRAY", depress=xray_vis)

def menu_func_import(self, context):
    self.layout.operator("kongor.import_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.import_clip", text="Heroes of Newerth Clip (.clip)")

def menu_func_export(self, context):
    self.layout.operator("kongor.export_model", text="Heroes of Newerth Model (.model)")
    self.layout.operator("kongor.export_clip", text="Heroes of Newerth Clip (.clip)")

class KONGOR_PT_object_panel(bpy.types.Panel):
    """K2 Mesh Info & Object Settings (matches S2Exporter Mesh Info)"""
    bl_label = "K2 Mesh Info"
    bl_idname = "KONGOR_PT_object_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'

    @classmethod
    def poll(cls, context):
        return bool(context.object and context.object.type == "MESH")

    def draw(self, context):
        layout = self.layout
        obj = context.object
        box = layout.box()
        box.label(text="K2 Object Settings", icon="OBJECT_DATA")
        box.prop(obj.kongor, "mesh_type")
        if obj.kongor.mesh_type == "NORMAL":
            box.prop(obj.kongor, "bonelink")
        elif obj.kongor.mesh_type == "SURF":
            box.label(text="Exports as collision surface (_surf polyhedron)", icon="INFO")

classes = (
    KONGOR_MT_arp_menu,
    KONGOR_MT_rigging_menu,
    KONGOR_MT_main_menu,
    KONGOR_PT_object_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_editor_menus.append(draw_viewport_header_menu)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_viewport_header_menu)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

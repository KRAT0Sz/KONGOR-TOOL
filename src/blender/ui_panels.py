"""
KONGOR TOOL - Modern Blender Menus & Header Integration
Provides a 3D Viewport Header Menu and Native Floating Dialog.
Zero N-Panel and zero Viewport clutter.
"""

import bpy
from .operators import get_target_armatures

class KONGOR_MT_rigging_menu(bpy.types.Menu):
    """KONGOR Rig - Unified Rigging, Auto-Rig and K2 Skeleton Bridge Menu"""
    bl_label = "KONGOR Rig"
    bl_idname = "KONGOR_MT_rigging_menu"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.generate_k2_skeleton", text="Generate K2 Game Armature from KONGOR Rig", icon="ARMATURE_DATA")
        layout.operator("kongor.conform_k2_hierarchy", text="Conform Hierarchy to K2 Standard (Root -> Bip01)", icon="CON_CHILDOF")
        layout.operator("kongor.add_k2_sockets", text="Add Standard K2 Sockets (_bone_*)", icon="PLUS")
        layout.operator("kongor.isolate_k2_deform", text="Isolate K2 Deform Bones", icon="CHECKMARK")
        layout.separator()
        layout.operator("kongor.arp_apply_k2_preset", text="Load K2 Biped Preset (.bmap)", icon="PRESET")
        layout.operator("kongor.arp_bind", text="Bind K2 Armature to KONGOR Rig", icon="CONSTRAINT_BONE")
        layout.operator("kongor.arp_unbind", text="Unbind K2 Armature", icon="X")
        layout.operator("kongor.arp_bake", text="Bake KONGOR Rig to K2 Skeleton", icon="ACTION")
        layout.separator()
        layout.operator("kongor.remap_to_k2_universal", text="Universal Remap to K2 (Bip01)", icon="SYNTAX_ON").reverse = False
        layout.operator("kongor.remap_to_k2_universal", text="Universal Remap to Def (def_)", icon="SYNTAX_OFF").reverse = True
        layout.separator()
        layout.operator("kongor.add_k2_rig", text="Add KONGOR Rig Character...", icon="OUTLINER_OB_ARMATURE")
        layout.operator("kongor.fit_bone_size", text="Auto-Fit Bone Sizes", icon="ARROW_LEFTRIGHT")

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
        layout.operator("kongor.standardize_materials", text="Standardize Materials to K2 (material, material2...)", icon="MATERIAL")
        layout.separator()
        layout.operator("kongor.import_clip", text="Import K2 Clip (.clip)", icon="ANIM")
        layout.operator("kongor.export_clip", text="Export K2 Clip (.clip)", icon="RENDER_ANIMATION")
        layout.separator()
        layout.menu("KONGOR_MT_rigging_menu", text="KONGOR Rig Tools", icon="ARMATURE_DATA")
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
        box.label(text="Mesh Info", icon="OBJECT_DATA")
        
        col_mesh = box.column(align=True)
        col_mesh.prop(obj, "name", text="Mesh")
        
        row_opts = box.row()
        row_opts.prop(obj.kongor, "exclude_normals")
        row_opts.prop(obj.kongor, "is_roof")

        col_radio = box.column(align=True)
        col_radio.prop(obj.kongor, "mesh_type", expand=True)

        if obj.kongor.mesh_type == "NORMAL":
            box.prop(obj.kongor, "bonelink")
        elif obj.kongor.mesh_type == "SURF":
            box.label(text="Exports as collision surface (_surf polyhedron)", icon="INFO")

        # Material Slots (matches S2Exporter Mesh Info material slots)
        mat_box = box.box()
        mat_box.label(text="Material", icon="MATERIAL")
        if obj.material_slots:
            for slot in obj.material_slots:
                mat_box.prop(slot, "material", text="")
        else:
            mat_box.label(text="No materials assigned", icon="INFO")

classes = (
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

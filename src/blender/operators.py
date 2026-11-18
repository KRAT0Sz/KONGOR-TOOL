"""
Blender Operators for KONGOR TOOL.
Handles File dialogs, invocation, and execution of Import/Export tasks.
"""

import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .scene_importer import import_k2_model_to_scene, import_k2_clip_to_scene
from .scene_exporter import export_scene_to_k2_model

class IMPORT_OT_k2_model(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Model (.model)"""
    bl_idname = "import_mesh.k2"
    bl_label = "Import K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.k2_import_settings
        try:
            import_k2_model_to_scene(self.filepath, settings)
            self.report({"INFO"}, f"Successfully imported: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Import error: {str(e)}")
            return {"CANCELLED"}

class EXPORT_OT_k2_model(bpy.types.Operator, ExportHelper):
    """Export K2 Engine Model (.model)"""
    bl_idname = "export_mesh.k2"
    bl_label = "Export K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.k2_export_settings
        try:
            success, msg = export_scene_to_k2_model(self.filepath, settings)
            if success:
                self.report({"INFO"}, msg)
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Export error: {str(e)}")
            return {"CANCELLED"}

class IMPORT_OT_k2_clip(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Animation Clip (.clip)"""
    bl_idname = "import_clip.k2"
    bl_label = "Import K2 Clip"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".clip"
    filter_glob: StringProperty(default="*.clip", options={"HIDDEN"})

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Please select an active Armature before importing a .clip file.")
            return {"CANCELLED"}

        try:
            import_k2_clip_to_scene(self.filepath, armature)
            self.report({"INFO"}, f"Successfully imported clip: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Clip import error: {str(e)}")
            return {"CANCELLED"}

class K2_OT_scene_info(bpy.types.Operator):
    """Display information about active K2 scene objects"""
    bl_idname = "k2.scene_info"
    bl_label = "Scene Info"

    def execute(self, context):
        meshes = [o for o in context.scene.objects if o.type == "MESH"]
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        surfs = [
            o for o in meshes
            if getattr(o.k2_mesh_settings, "is_collision_surface", False) or "_surf" in o.name.lower()
        ]

        msg = f"K2 Scene: {len(meshes)} Meshes, {len(armatures)} Armatures, {len(surfs)} Collision Surfaces."
        self.report({"INFO"}, msg)
        return {"FINISHED"}

classes = (
    IMPORT_OT_k2_model,
    EXPORT_OT_k2_model,
    IMPORT_OT_k2_clip,
    K2_OT_scene_info,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

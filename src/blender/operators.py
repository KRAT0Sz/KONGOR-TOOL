"""
KONGOR TOOL - Modern Blender Operators
Clean operator definitions conforming to Blender >= 4.2 / 5.0 standards.
Zero legacy code or legacy naming conventions.
"""

import os
import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper

from .scene_importer import import_k2_model_file, import_k2_clip_file
from .scene_exporter import export_k2_model_file, export_k2_clip_file

class KONGOR_OT_import_model(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Model (.model / SMDL)"""
    bl_idname = "kongor.import_model"
    bl_label = "Import K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.kongor_import
        try:
            import_k2_model_file(
                self.filepath,
                flip_v=settings.flip_v,
                build_materials=settings.build_materials,
            )
            self.report({"INFO"}, f"Successfully imported K2 Model: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to import K2 Model: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_export_model(bpy.types.Operator, ExportHelper):
    """Export scene to K2 Engine Model (.model / SMDL v3)"""
    bl_idname = "kongor.export_model"
    bl_label = "Export K2 Model"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".model"
    filter_glob: StringProperty(default="*.model", options={"HIDDEN"})

    def execute(self, context):
        settings = context.scene.kongor_export
        try:
            success, msg = export_k2_model_file(self.filepath, context, settings)
            if success:
                self.report({"INFO"}, msg)
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export K2 Model: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_import_clip(bpy.types.Operator, ImportHelper):
    """Import K2 Engine Animation Clip (.clip) onto active Armature"""
    bl_idname = "kongor.import_clip"
    bl_label = "Import K2 Clip"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".clip"
    filter_glob: StringProperty(default="*.clip", options={"HIDDEN"})

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "Please select an active Armature object before importing a .clip file.")
            return {"CANCELLED"}

        try:
            import_k2_clip_file(self.filepath, armature)
            self.report({"INFO"}, f"Successfully imported K2 Clip: {os.path.basename(self.filepath)}")
            return {"FINISHED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to import K2 Clip: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_export_clip(bpy.types.Operator, ExportHelper):
    """Export Armature animation to K2 Engine Clip (.clip)"""
    bl_idname = "kongor.export_clip"
    bl_label = "Export K2 Clip"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".clip"
    filter_glob: StringProperty(default="*.clip", options={"HIDDEN"})

    def execute(self, context):
        armature = context.active_object
        if not armature or armature.type != "ARMATURE":
            for obj in context.scene.objects:
                if obj.type == "ARMATURE" and not obj.hide_get():
                    armature = obj
                    break

        if not armature or armature.type != "ARMATURE":
            self.report({"ERROR"}, "An active Armature object is required to export a .clip file.")
            return {"CANCELLED"}

        settings = context.scene.kongor_clip
        try:
            success, msg = export_k2_clip_file(self.filepath, context, armature, settings)
            if success:
                self.report({"INFO"}, msg)
                return {"FINISHED"}
            else:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
        except Exception as e:
            self.report({"ERROR"}, f"Failed to export K2 Clip: {str(e)}")
            return {"CANCELLED"}

class KONGOR_OT_inspect_scene(bpy.types.Operator):
    """Display information and statistics about K2 Engine objects in scene"""
    bl_idname = "kongor.inspect_scene"
    bl_label = "Inspect Scene"

    def execute(self, context):
        meshes = [o for o in context.scene.objects if o.type == "MESH"]
        armatures = [o for o in context.scene.objects if o.type == "ARMATURE"]
        surfaces = [
            o for o in meshes
            if getattr(o.kongor, "is_collision_surface", False) or "_surf" in o.name.lower()
        ]
        visual_meshes = len(meshes) - len(surfaces)

        msg = f"K2 Scene: {visual_meshes} Visual Meshes, {len(surfaces)} Collision Surfaces, {len(armatures)} Armatures."
        self.report({"INFO"}, msg)
        return {"FINISHED"}

class KONGOR_OT_uninstall(bpy.types.Operator):
    """Uninstall KONGOR TOOL extension and remove files from Blender"""
    bl_idname = "kongor.uninstall"
    bl_label = "Uninstall KONGOR TOOL"
    bl_options = {"REGISTER", "INTERNAL"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        import shutil
        import pathlib

        root_pkg = __package__.rsplit(".blender", 1)[0] if ".blender" in __package__ else __package__
        uninstalled = False

        # 1. Blender 4.2+ Extension Uninstaller
        if hasattr(bpy.ops, "extensions") and hasattr(bpy.ops.extensions, "package_uninstall"):
            try:
                bpy.ops.extensions.package_uninstall(pkg_id="kongor_tool")
                uninstalled = True
            except Exception:
                pass

        # 2. Legacy Add-on Remove operator
        if not uninstalled and hasattr(bpy.ops, "preferences") and hasattr(bpy.ops.preferences, "addon_remove"):
            try:
                bpy.ops.preferences.addon_remove(module=root_pkg)
                uninstalled = True
            except Exception:
                pass

        # 3. Direct disk cleanup fallback
        try:
            current_file = pathlib.Path(__file__).resolve()
            addon_dir = current_file.parent.parent
            if addon_dir.exists() and (addon_dir / "blender_manifest.toml").exists():
                shutil.rmtree(addon_dir, ignore_errors=True)
                uninstalled = True
        except Exception:
            pass

        self.report({"INFO"}, "KONGOR TOOL has been uninstalled. Restart Blender to finish.")
        return {"FINISHED"}

classes = (
    KONGOR_OT_import_model,
    KONGOR_OT_export_model,
    KONGOR_OT_import_clip,
    KONGOR_OT_export_clip,
    KONGOR_OT_inspect_scene,
    KONGOR_OT_uninstall,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

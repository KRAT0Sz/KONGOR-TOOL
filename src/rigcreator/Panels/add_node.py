import bpy
from .general import *

def RGC_Menu_Add_Nodes(self, context):
    layout = self.layout
    if context.space_data.tree_type == "GeometryNodeTree" : 
        layout.separator()
        layout.menu("rgc.add_nodes", text="Sub Target")

SelectObj = None

class RGC_add_nodes(bpy.types.Menu):
    bl_idname = "rgc.add_nodes"
    bl_label = "Sub Target"

    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        tree = context.space_data.node_tree
        objs = (
                o for o in bpy.data.objects
                if any(mod.type == 'NODES' and mod.node_group == tree for mod in o.modifiers)
            )
        
        
        objs = [
            o for o in bpy.data.objects
            if any(mod.type == 'NODES' and mod.node_group == tree for mod in o.modifiers)
        ]

        if not objs:
            layout.label(text="No objects linked", icon="ERROR")
            return

        for obj in objs:
            op = layout.operator("rgc.select_obj_target", text=obj.name)
            op.obj_name = obj.name

class RGC_OT_select_obj_target(bpy.types.Operator):
    bl_idname = "rgc.select_obj_target"
    bl_label = "Select Object Target"
    bl_description = "Selecciona el objeto y muestra los subtargets"

    obj_name: bpy.props.StringProperty()

    def execute(self, context):
        global SelectObj
        SelectObj = bpy.data.objects.get(self.obj_name)
        bpy.ops.wm.call_menu(name="rgc.objt_target")
        return {'FINISHED'}


class RGC_objt_target(bpy.types.Menu):
    bl_idname = "rgc.objt_target"
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return True
    
    def draw(self, context):
        layout = self.layout
        obj = SelectObj
        if obj :
            subtargets = obj.RGC_Constraint_GrupsProps.targets_grups
            for i, tgt in enumerate(subtargets):
                op = layout.operator("rgc.add_nodes", text=tgt.name, icon='OBJECT_ORIGIN')
                op.index = i
                op.type = "ADDNODE"
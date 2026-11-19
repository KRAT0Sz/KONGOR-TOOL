
import bpy
from ..generaldata import *
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    StringProperty,
    EnumProperty,
    PointerProperty,
    CollectionProperty,
    FloatVectorProperty,
    IntVectorProperty,
    BoolVectorProperty,
)

Texts = []

class RGC_OperatorMenuInfo(bpy.types.Operator):
    bl_idname = "rgc.cmenu_info"
    bl_label = ""

    text : StringProperty()

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        global Texts
        Texts.clear()
        text : str = self.text
        ltext = text.split("\n")
        for t in ltext :
            Texts.append(t)
        bpy.ops.wm.call_menu(name="rgc.menu_info")
        return {"FINISHED"}


class RGC_Menu_InfoMenu(bpy.types.Menu):
    bl_idname = "rgc.menu_info"
    bl_label = "Info"

    def draw(self, context):
        layout = self.layout
        global Texts
        col = layout.column(align=True)
        for i, l in enumerate(Texts) :
            if i == 0 : 
                col.label(text=l, icon="INFO")
            else :
                col.label(text=l)
        
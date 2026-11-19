import bpy
from .general import *
from ..generaldata import GeneralArmatureData


class RGC_Panel_EdiArmature(GN_RigCreatorViewPort, bpy.types.Panel):
    bl_idname = "RGC_Panel_EdiArmature"
    bl_label = "Edit Armature"
    
    
    @classmethod
    def poll(cls, context):  
        Self = GeneralArmatureData()
        return Self.GetArmature() and Self.PanelType([{"ALL"}, {"RIG"}]) and Self.GetObjMode() == "POSE"
    

    
    def draw(self, context):
        
        layout = self.layout
        props = self.Props()
        objprops = self.PropsToObject()
        
        layout.prop(objprops, "bbone_segments", text="Segments")
        layout.prop(objprops, "use_rot_brow", text="Rotation Brow", toggle=1)
        
        if self.Panel(layout, "StretchTo", "StretchTo", "") :
            grid = layout.grid_flow(
            row_major=False, columns=2, 
            even_columns=True, even_rows=False, 
            align=True
            )
            for dir in ["R", "L"] :
                grid.prop(objprops, f"vl_arm_{dir}", text = f"Arm {dir}")
                grid.prop(objprops, f"vl_leg_{dir}", text = f"Leg {dir}")
        
        if self.Panel(layout, "Face", "Face", "") :
            layout.prop(objprops, "f_brow", text = "Brow")
            row = layout.row(align = True)
            row.prop(objprops, "f_brow_R", text = "Brow R")
            row.prop(objprops, "f_brow_L", text = "Brow L")
            layout.prop(objprops, "f_mouth_up", text = "Mouth UP")
            layout.prop(objprops, "f_mouth_down", text = "Mouth DOWN")
            
            grid = layout.grid_flow(
            row_major=False, columns=2, 
            even_columns=True, even_rows=False, 
            align=True
            )
            for dir in ["R", "L"]:
                grid.prop(objprops, f"ac_eyelip_up_{dir}", text=f"Eyelip UP {dir}")
                grid.prop(objprops, f"ac_eyelip_down_{dir}", text=f"Eyelip DOWN {dir}")
            
import bpy
from .general import *
from ..generaldata import GeneralArmatureData


class RGC_Panel_Proxy_Low(GeneralArmatureData, bpy.types.Panel):
    bl_idname = "RGC_Panel_Proxy_Low"
    bl_label = "Proxy Low"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Create Proxy"
    
    @classmethod
    def poll(cls, context):        
        return True

    def draw(self, context):
        layout = self.layout
        props = self.Props()
        
        layout.prop(props, "pl_enum", text="")
        if props.pl_enum == "COLLECTION":
            layout.prop(props, "pl_collection_to_create_proxy", text="Collection")
        
        layout.prop(props, "pl_enum_type", text="")
        layout.prop(props, "pl_collection_name", text="")
        
        if props.pl_enum_type == "DECIMATE" :
            
            layout.prop(props, "pl_decimate_ratio", text="Dicimete Radio")
            layout.prop(props, "pl_decimate_ratio_vert", text="Dicimete Radio Vert")
            layout.prop(props, "pl_angle_limit", text="Face Angle Limite")
            layout.prop(props, "pl_delectmaterial", text="Delect Matarial")
            
            if props.pl_enum == "COLLECTION":
                colc = props.pl_collection_to_create_proxy
                col = self.layoutEnabled(layout, bool(colc != None and len(colc.children) == 0) )
                if colc and len(colc.children) != 0 :
                    layout.label(text="He collection has daughters collection", icon="ERROR")
            elif props.pl_enum == "OBJECT":
                col = self.layoutEnabled(layout, bool(len(self.GetSelectableObjects()) != 0))
            else :
                col = layout
                
            col.operator("rgc.proxy_low", text="Proxy Low")
                    
        else :
            layout.prop(props, "pl_armature", text="", icon="OUTLINER_OB_ARMATURE")
            layout.prop(props, "ol_detail", text="Detail")
        
            col = self.layoutEnabled(layout, bool(props.pl_armature != None) )
            col.operator("rgc.proxy_low", text="Proxy Low")
        
        

from .general import *
from ..generaldata import GeneralArmatureData
import bmesh
from .generators import *
## sss
    #bm = bmesh.from_edit_mesh(obj.data)
    #view : bool = False
    #select_objects = self.GetSelectableObjects()
    #have_armature = False
    #for o in select_objects:
    #    if o != obj : 
    #        if o.type == "ARMATURE" : 
    #            have_armature = True
    #            break
    #layout.label(text="Set To Armature" if have_armature else "Add Armature",)
    #for v in bm.verts:
    #    if v.select : view = True
    #if view == False :
    #    layout.label(text="Select Vertex", icon="ERROR")
    #    return
    #
    #layout = layout.column(align=True)
    #layout.scale_y = 1.2
    #layout.prop(props, "mesh_bone_name", text="Bone Name")
    #
    ## bone Reference
    #row = layout.row(align=True)
    #row.prop(props, "mesh_use_bone_reference", text="Bone Reference", expand=False, slider=False, toggle=1)
    #rrow = row.row(align=True)
    #rrow.enabled = props.mesh_use_bone_reference
    #rrow.prop(props, "mesh_bone_reference_name", text="")
    #
    #layout.separator()
    #layout.prop(props, "mesh_use_aling_roll_normal", text="Aling Roll Normal", expand=False, slider=False, toggle=1)
    #layout.prop(props, "mesh_keep_object", text="Keep Object", expand=False, slider=False, toggle=1)
    #layout.separator()
    #
    ## weights
    #row = layout.row(align=True)
    #row.prop(props, "mesh_with_automatic_weights", text="With Automatic Weights", expand=False, slider=False, toggle=1)
    #rrow = row.row(align=True)
    #rrow.enabled = props.mesh_with_automatic_weights
    #rrow.prop(props, "mesh_with_by_distance_of_vertex", text="With By Distance Of Vertex", expand=False, slider=False, toggle=1)
    #
    #layout.separator()
    #
    #
    #if self.GetMeshSelectMode("EDGE") or self.GetMeshSelectMode("VERT"):
    #    
    #    clayout = layout.column(align = True)
    #    clayout.enabled = self.GetMeshSelectMode("VERT")
    #    clayout.prop(props, "mesh_use_vertcurve", text="Vert Curve", expand=False, slider=False, toggle=1)
    #    clayout = layout.column(align = True)
    #    clayout.enabled = props.mesh_use_vertcurve
    #    clayout.prop(props, "mesh_vertcurve_power", text="Curve Power", expand=False, slider=False, toggle=1)
    #
    #    clayout = layout.column(align = True)
    #    if self.GetMeshSelectMode("VERT"):
    #        clayout.enabled = not props.mesh_use_vertcurve
    #        
    #    clayout.prop(props, "mesh_use_tail", text="Use Tail", expand=False, slider=False, toggle=1)
    #    col = clayout.column(align=True)
    #    col.enabled = props.mesh_use_tail
    #    
    #    col = clayout.column(align=True)
    #    col.enabled = not props.mesh_use_tail
    #    col.prop(props, "mesh_normal_global", text="")
    #    if props.mesh_normal_global  == "GLOBAL":
    #        row = col.row(align=True)
    #        row.prop(props, "mesh_direction", text="X")
    #else :
    #    layout.prop(props, "mesh_normal_global", text="")
    #    if props.mesh_normal_global  == "GLOBAL":
    #        row = layout.row(align=True)
    #        row.prop(props, "mesh_direction", text="X")
    #    
    #text = ""
    #if self.GetMeshSelectMode("VERT"):
    #    text = "Set Bone To Selected Vert"
    #elif self.GetMeshSelectMode("EDGE"):
    #    text = "Set Bone To Selected Edge"
    #elif self.GetMeshSelectMode("FACE"):
    #    text = "Set Bone To Selected Face"
    #    
    #layout.separator()
    #layout.prop(props, "mesh_use_curve", text="Use Curve Grip",expand=False, slider=False, toggle=1)
    #
    #if props.mesh_use_curve :
    #    DrawGenerators().Curve(layout, props, use_run=False)
    #    
    #layout.separator()   
    #
    #
    #layout.operator("rgc.mesh_to_bone", 
    #    text=text, 
    #    icon="BONE_DATA"
    #)

class Draw(DrawGenerators) : 
    
    
    def CheckVerts(self, obj, how_much : int = 1) -> bool :
        
        vs = self.GetVertexSelect(obj, self.GetMeshMode())
        return bool(len(vs) >= how_much)
    
    
    def DrawButtonRun(self, layout, type : str, text : str, label_text: str, obj : object, how_much : int, value = True) :
        value = self.CheckVerts(obj, how_much) and value
        L = self.layoutEnabled(layout, value, True)
        if not value :
            L.label(text=label_text, icon="ERROR")
        L.operator("rgc.mesh_to_bone", 
            text=text, icon="PLAY"
        ).type = type
    
    def OnlyBone(self, Layout, props, obj) :

        Layout.prop(props, "ob_length", text="Length")
        Layout.prop(props, "ob_normal_global", text="")
        
        row = self.layoutActive(Layout, bool(props.ob_normal_global == "GLOBAL")).row()
        row.prop(props, "ob_direction", text="xyz")
        
        self.DrawButtonRun(
            Layout, "ONLY_BONE", "Only Bone", "Select 1 Vertex", obj, 1
        )
    
    def HeadTailBone(self, Layout, props, obj):
        
        
        Layout.prop(props, "headtail_use_parent", text="Parent", expand=False, slider=False, toggle=1)
        Layout.prop(props, "headtail_use_connected", text="Connected", expand=False, slider=False, toggle=1)
        Layout.prop(props, "headtail_use_loop", text="Loop", expand=False, slider=False, toggle=1)
        Layout.prop(props, "headtail_enum_const", text="How Control")
        
        match props.headtail_enum_const :
            case "FINGERS" :
                self.Fingers(Layout, props, False)
            case "GRIP" :
                self.CurveGrip(Layout, props, False)
            case "CURVE" :
                self.Curve(Layout, props, False)

        self.DrawButtonRun(
            Layout, "HEADTAIL_BONE", "Head/Tail", "Select 2 Vertex", obj, 2
        )
    
    def EyeBone(self, layout, props, obj):
        
        layout.prop(props, "eye_point_center", text="Point Center")        
        layout.prop(props,  "use_deform_bone", text="Deform Bone", expand=False, slider=False, toggle=1)
        layout.prop(props,  "use_eye_root", text="Root", expand=False, slider=False, toggle=1)
        layout.prop(props,  "use_eye_bbone", text="Bbone", expand=False, slider=False, toggle=1)
        
        
        col = layout.column(align=True)
        col.active = props.use_eye_bbone
        col.prop(props,  "use_eye_semetal_bbone", text="Semetal BBone", expand=False, slider=False, toggle=1)
        col.prop(props,  "eye_bbone_segments", text="BBone Segments")
        col.prop(props,  "eye_use_loop", text="Loop", expand=False, slider=False, toggle=1)
        
        layout.separator()
        
        how_much = 1 if not props.use_eye_bbone else 2 if not props.use_eye_semetal_bbone else 4
        self.DrawButtonRun(
            layout, "EYE_BONE", "Generate Eye", 
            f"Select {how_much} Vertex" if props.eye_point_center else "Not Have Point Center", 
            obj, how_much, bool(props.eye_point_center != None)
        )


class RGC_Panel_MeshToBone(Draw,  bpy.types.Panel):
    bl_idname = "RGC_Panel_MeshToBone"
    bl_label = "Mesh To Bone"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mesh To Bone"
    
    @classmethod
    def poll(cls, context):        
        Self = GeneralArmatureData()
        return Self.GetActiveObject() and Self.GetActiveObject().type == "MESH" and Self.GetObjMode() == "EDIT"

    def draw(self, context):
        layout = self.layout
        props = self.Props()
        obj = self.GetActiveObject()
        
        row = layout.row(align = True)
        row.prop(props, "mesh_armature_select", text="Armature")
        info  = "The bones will turn into armature"
        if not props.mesh_armature_select :
            objs = self.GetSelectableObjects()
            armature_select = False
            for o in objs:
                if o.type == "ARMATURE" :
                    armature_select = True
                    break
            if armature_select :
                info = f"The bones will prostrate themselves \n in the selected armorture"
            else :
                info = f"An armorture will be created and the bones \n will be placed there."
        
        self.InfoButton(row, info)

        col = layout.column(align = True)
        col.prop(props, "mesh_bone_name", text="Bone Name")
        col.prop(props, "mesh_keep_object", text="Keep Object", expand=False, slider=False, toggle=1)
        col.prop(props, "mesh_with_automatic_weights", text="With Automatic Weights", expand=False, slider=False, toggle=1)
        col.prop(props,  "mesh_shape_size", text="Shape Size")
        
        layout.prop(props, "mesh_browser", text="", icon="VIEWZOOM")
        
        list_button = [
            ["VERT", "VERTEXSEL", "Vert"],
            ["EDGE", "EDGESEL", "Edge"],
            ["FACE", "FACESEL", "Face"],
        ]
        row = layout.row(align = True)
        for b in list_button :
            op = row.operator('mesh.select_mode', text=b[2], icon=b[1], emboss=True, depress=self.GetMeshSelectMode(
                b[0]
            ))
            op.type = b[0]
        self.InfoButton(row, text=
            "If it is in a value different from Vert, \n it takes an average of the selected vertices \n and there is an addition in bone"
        )
        
        list = [
            ["Only Bone", self.OnlyBone],
            ["Head/Tail Bone", self.HeadTailBone],
            ["Eye Bone", self.EyeBone],
            
        ]
        
        for gn in list :
            if props.mesh_browser.lower() in gn[0].lower() or props.mesh_browser == "" :
                box = layout.box()
                Layout = box.column(align=True)
                if self.Panel(Layout, gn[0], gn[0], "", True) :
                    gn[1](Layout, props, obj)


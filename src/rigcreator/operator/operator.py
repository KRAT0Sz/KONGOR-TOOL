
import bpy 
from ..generaldata import *
from .general import *
from .classes import *

import bpy.utils.previews
import os
import time




class RGC_OperatorGeneral(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.general"
    bl_label = ""
   
    type : bpy.props.StringProperty()
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        list_Op = {
            "INPORT" : self.SetProperties,
            "GET_CONST_ARMATURE" : self.GetConstraintArmatureToIK,
            "SET_CONT_BENDYBONE" : self.SetContBendyBone,
        }
        
        
        if self.type in list_Op:
            list_Op[self.type]()
        
        
        return {"FINISHED"}


# Generadores 
GE_OP_list = {}
Operators_list = GeneralArmatureData().ListGenerators()

def Execute(op):
    def execute(self, context):
        list = {
            "Physics" : self.GN_Fisicas, 
            "Fingers" : self.GN_Fingers,
            "Ik" : self.GN_Ik,
            "Fk" : self.GN_Fk,
            "Bones" : self.GN_Bones,
            "Curve" : self.GN_Curve,
            "Auto_Root" : self.GN_Auto_Root,
            "Add_Collection_Of_Material" : self.AddCollection,
        }
        if op in list:
            list[op]()
        return {"FINISHED"}
    return execute


for op in Operators_list:
    class_name = f"RGC_{op}"
    bl_idname = f"rgc.{op.lower()}"
    bl_label = f"{op}"
    
    class_opertor = type(class_name, (GeneratorsBones, bpy.types.Operator,), {
        "bl_idname": bl_idname,
        "bl_label": bl_label,
        "execute": Execute(op)
    })
    
    GE_OP_list[class_name] = class_opertor



    
class RGC_Operator_GeneratorsBones(GeneratorsBones, bpy.types.Operator):
    bl_idname = "rgc.generatorsbones"
    bl_label = ""
  
    type : bpy.props.StringProperty()


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        list = {
            "Physics" : self.GN_Fisicas, 
            "Fingers" : self.GN_Fingers,
            "Ik" : self.GN_Ik,
            "Fk" : self.GN_Fk,
            "Bones" : self.GN_Bones,
            "Curve" : self.GN_Curve,
            "Auto_Root" : self.GN_Auto_Root,
            "Add_Collection_Of_Material" : self.AddCollection,
            "AddBone":self.AddBone,
            "UnionBase":self.GN_UnionBone,
            "UnionActiveBone" : self.GN_UnionActiveBone,
            "ParentBendyBones": self.GN_ParentBendyBone,
            "ParentActiveBendyBones": self.GN_ParentActiveBendyBone,
            "ParentOffSet" : self.GN_ParentOffset,
            "ParentConnected" : self.GN_ParentConnected,
            "Curve_Grip" : self.GN_CurveGrip,            
            "DampedTrackParent" : self.GN_DampedTrackParent,
            "DampedTrackControlParent" : self.GN_DampedTrackControlParent,
            "Annotate_Bone" : self.GN_AnnotateBone,
            "AddBoneHead" : self.GN_AddBoneHead,
            "AddBoneTail" : self.GN_AddBoneTail,
            "AddBoneHeadTail" : self.GN_AddBoneHeadTail,
            "EditProperty" : self.EditProperty,
            "ARMS" : self.GN_Arms, 
            "LEGS" : self.GN_Legs,
            "TORSO" : self.GN_Torso,
            "TAIL" : self.GN_Tail,
        }
        
        
        if self.type in list :
            list[self.type]()
            
        
            self.report({'INFO'}, f"Set {self.type}")
        
        return {"FINISHED"}

class RGC_SetMode(GeneralArmatureData, bpy.types.Operator):
    bl_idname = "rgc.setmode"
    bl_label = ""
  
    mode : bpy.props.StringProperty()


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        self.SetMode(self.mode)
        return {"FINISHED"}

class RGC_OperatorCollections(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.collections"
    bl_label = ""
  
    type : bpy.props.StringProperty()
    col_name : bpy.props.StringProperty()
    col_name_parent : bpy.props.StringProperty()
    

    @classmethod
    def poll(cls, context):
        return True
    

    def execute(self, context):
        props = self.Props()
        if self.type in {"SELECT", "DESELECT"}: 
            self.SelectBoneToCollection(
                self.col_name, self.GetObjMode(), 
                value = True if self.type == "SELECT" else False
                )
        
        elif self.type == "ALL_DESELECT" :
            self.OnlySelectBonesInThesCollection(self.col_name)
            
        elif self.type == "MENU":
            props.how_collection_select = self.col_name_parent
            bpy.ops.wm.call_menu(name="RGC_Menu_Collections")
        elif self.type in {"UP", "DOWN"} :
            self.EditIndexCollections(self.col_name, self.type)
        elif self.type == "ADD_COLLECTION":
            self.AddCollectionToArmature()
        
        elif self.type == "ACTIVE":
            active = self.GetActiveObject().data.collections.active_name
            col = self.GetActiveObject().data.collections_all.get(self.col_name)
            if active == self.col_name or col.is_solo: 
                col.is_solo = not col.is_solo
            self.GetActiveObject().data.collections.active_name = self.col_name
        
        return {"FINISHED"}



class RGC_OperatorProperties(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.properties"
    bl_label = ""
  
    type : bpy.props.StringProperty()

    

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        props = self.PropsToArmature()
        
        if self.type == "ADD" :
            self.AddPropertiesRigCreator()
            self.SetDriveToOldRigCreator()
        
        if self.type == "SET" :
            self.SetDriveToOldRigCreator()
        
        for type in ["R", "L"] : 
            if self.type == f"ARMS_IKAFK_{type}" : 
                self.FkaIkoIkaFk(type, "arm", getattr(props[0], f"arm_invert_ik_fk_{type}"))
            elif self.type == f"LEGS_IKAFK_{type}" : 
                self.FkaIkoIkaFk(type, "leg", getattr(props[0], f"leg_invert_ik_fk_{type}"))
                
        return {"FINISHED"}



class RGC_OperatorResetArmature(ResetArmature, bpy.types.Operator):
    bl_idname = "rgc.rstarmature"
    bl_label = ""
  
    type : bpy.props.StringProperty()

    

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        # General
        operator_genral = {
            "RESET_ALL" : self.ResetAllArmature,
            "RESET_FACE" : self.ResetFace,
            "RESET_CARTOON_FACE" : self.ResetCartoonFace,
            "RESET_SPINE" : self.ResetSpine,
            "RESET_ALLSTRETCH_TO" : self.ResetALLBoneStretchTo,
            "RESET_STRETCH_TO" : self.ResetSelectBoneStretchTo,
            "RESET_ROOT" : self.ResetRoot,
            "RESET_CAR" : self.ResetCar,
        }
        if self.type in operator_genral:
            operator_genral[self.type]()

        # Arm and Leg
        operator_arm_leg = {}
        for type in ["R", "L"] : 
            operator_arm_leg[f"RESET_ARM_{type}"] = (self.ResetArm, type)
            operator_arm_leg[f"RESET_LEG_{type}"] = (self.ResetLeg, type)
            
        if self.type in operator_arm_leg : 
            value = operator_arm_leg[self.type]
            value[0](value[1])
        
        # Fingers 
        operator_fingers = {}
        for type in ["R", "L"]:
            for finger in self.ListFinger():
                operator_fingers[f"RESET_{finger.upper()}_{type}"] = (
                    self.ResetFingers, 
                    finger.lower().replace(" ", "_").lower(), type
                )
        if self.type in operator_fingers:
            value = operator_fingers[self.type]
            value[0](value[1],value[2])

        return {"FINISHED"}

class RGC_OperatorAddArmature(bpy.types.Operator):
    bl_idname = "rgc.add_armature"
    bl_label = "Add Armature"
    bl_description = "Add an armature from the Rig Creator file"
    bl_options = {"REGISTER", "UNDO"}
    
    type: bpy.props.StringProperty(name="Type", description="The type of armature to append", default="")

    @classmethod
    def poll(cls, context):
        if bpy.app.version >= (3, 0, 0) and True:
            cls.poll_message_set('')
        return not False

    def execute(self, context):
        before_data = list(bpy.data.collections)
        parent_file = os.path.dirname(os.path.dirname(__file__))
        bpy.ops.wm.append(directory=os.path.join(parent_file, 'assets', 'Rig_Creator.blend') + r'\Collection', filename=self.type, link=False)
        new_data = list(filter(lambda d: not d in before_data, list(bpy.data.collections)))
        appended_691BE = None if not new_data else new_data[0]
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)

# Animation 

class RGC_OperatorAnimation(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.animation"
    bl_label = ""
    
    type: bpy.props.StringProperty(name="Type", description="The type of armature to append", default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        operator_list = {
            "COPY" : self.CopyXformRelationShip,
            "PASTE" : self.PasteXformRelationShip,
            "BAKE_FOR_FRAME" : self.BakeByFrameXformRelationShip,
        }
        
        operator_list[self.type]()
        #self.CopyXformRelationShip()
        
        return {"FINISHED"}



# Node Tree

class RGC_OperatorAddNode(bpy.types.Operator):
    bl_idname = "rgc.addnode"
    bl_label = "Add Node"
    
    type: bpy.props.StringProperty(name="Type", description="The type of armature to append", default="")

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        bpy.ops.node.add_node(use_transform=True, type=self.type)
        return {"FINISHED"}

    def invoke(self, context, event):
        return self.execute(context)


from bpy.types import (
    Operator,
)
from bpy.props import (
    IntProperty,
)

# Constraint

    
class RGC_OperatorBoneConstraint(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.boneconstraint"
    bl_label = ""
    
    
    type: bpy.props.StringProperty(name="Type")

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        self.ListFunctionToConstraint(self.type, True)
        
        return {'FINISHED'}

class RGC_OperatorObjectConstraint(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.objconstraint"
    bl_label = ""
    
    
    type: bpy.props.StringProperty(name="Type")

    @classmethod
    def poll(cls, context):
        return not False

    def execute(self, context):
        
        
        self.ListFunctionToConstraint(self.type, False)
        
        return {'FINISHED'}


class CONSTRAINT_OT_add_target(GeneralArmatureData, bpy.types.Operator):
    """Add a target to the constraint"""
    bl_idname = "constraint.add_target"
    bl_label = "Add Target"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        constraint = GeneralArmatureData().get_constraint(context)
        return constraint

    def execute(self, context):
        if self.get_constraint(context):
            self.get_constraint(context).targets.new()
        return {'FINISHED'}

class CONSTRAINT_OT_remove_target(GeneralArmatureData, bpy.types.Operator):
    """Remove the target from the constraint"""
    bl_idname = "constraint.remove_target"
    bl_label = "Remove Target"
    bl_options = {'UNDO', 'INTERNAL'}

    index: bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return GeneralArmatureData().get_constraint(context)

    def execute(self, context):
        if self.get_constraint(context):
            tgts = self.get_constraint(context).targets
            tgts.remove(tgts[self.index])
        return {'FINISHED'}

class CONSTRAINT_OT_normalize_target_weights(GeneralArmatureData, bpy.types.Operator):
    """Normalize weights of all target bones"""
    bl_idname = "constraint.normalize_target_weights"
    bl_label = "Normalize Weights"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return GeneralArmatureData().get_constraint(context)

    def execute(self, context):
        if self.get_constraint(context):
            tgts = self.get_constraint(context).targets
            total = sum(t.weight for t in tgts)

            if total > 0:
                for t in tgts:
                    t.weight = t.weight / total

        return {'FINISHED'}

class CONSTRAINT_OT_disable_keep_transform(GeneralArmatureData, bpy.types.Operator):
    """Set the influence of this constraint to zero while """ \
        """trying to maintain the object's transformation. Other active """ \
        """constraints can still influence the final transformation"""

    bl_idname = "constraint.disable_keep_transform"
    bl_label = "Disable and Keep Transform"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return GeneralArmatureData().get_constraint(context) and GeneralArmatureData().get_constraint(context).influence > 0.0

    def execute(self, context):
        if self.get_constraint(context):
            self.get_constraint(context).influence = 0.0
        return {'FINISHED'}
        

# Piker
class RGC_OperatorPiker(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.piker"
    bl_label = ""
    
    type: bpy.props.StringProperty(name="Type", description="The type of armature to append", default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        active_bone = self.GetBone(self.type, "POSE")
        for bone in self.GetActiveObject().pose.bones:
            bone.bone.select = False
        active_bone.bone.select = True
        self.GetActiveObject().data.bones.active = active_bone.bone
        
        return {"FINISHED"}


class RGc_OperatorAplicarScale(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.aplicarscale"
    bl_label = ""
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        self.AplicarScale()
        
        return {"FINISHED"}


class RGC_Operator_Only_ViewChildBone(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.only_view_child_bone"
    bl_label = ""
    
    type : bpy.props.StringProperty(name="Type", description="", default="")
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        if not self.IsArmatureExists() and not self.GetObjMode() == "POSE":
            self.report({'WARNING'}, "No armature found")
            return {'CANCELLED'}
        bpy.ops.pose.hide(unselected=True)
        for bone in self.GetSelectBones(mode="POSE"):
            
            bone = self.GetBone(bone.name, "OBJECT")
            if bone :
                bone.hide = False
                # Mostrar todos los hijos recursivamente
                def show_children_recursive(b):
                    for child in b.children:
                        child.hide = False
                        if child.children:
                            show_children_recursive(child)

                show_children_recursive(bone)
            self.report({'INFO'}, f"Hiden {bone.name} and Show children")
        
        return {"FINISHED"}

def RegisterCallMenu():
    # Crear un keymap personalizado
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Window", space_type='EMPTY')
    
    kmi = km.keymap_items.new("wm.call_panel", "V", "PRESS", alt=True)
    kmi.properties.name = "RGC_Panel_Call_Proterties_RigCreator"
    
    kmi = km.keymap_items.new("wm.call_panel", "P", "PRESS", alt=True, ctrl=True)
    kmi.properties.name = "RGC_Panel_Picker"
    
    kc = bpy.context.window_manager.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new('wm.call_menu', 'A', 'PRESS',
        ctrl=False, alt=False, shift=True, repeat=False)
    kmi.properties.name = 'rgc.addbone'
    
    #kc = bpy.context.window_manager.keyconfigs.addon
    #km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    #kmi = km.keymap_items.new('wm.call_menu', 'B', 'PRESS',
    #    ctrl=True, alt=False, shift=False, repeat=False)
    #kmi.properties.name = 'rgc.editbone'
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
    kmi = km.keymap_items.new("rgc.only_view_child_bone", 'H', 'PRESS',
            ctrl=True, alt=False, shift=True)
        

def UnregisterCallMenu():

    # Limpiar el keymap cuando se desregistre el addon
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.get("Window")
    if km:
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu' and kmi.properties.name == "MY_MT_custom_menu":
                km.keymap_items.remove(kmi)


# MESH
class RGC_OperatorMeshToBone(MeshToBone, bpy.types.Operator):
    bl_idname = "rgc.mesh_to_bone"
    bl_label = ""
  
    type : bpy.props.StringProperty()


    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        list = {
            "ONLY_BONE" : self.Only_Bone,
            "CURVE_BONE" : self.Curve_Bone,
            "EYE_BONE" : self.Eye_Bone,
            "HEADTAIL_BONE" : self.HeadTail_Bone,
        }
        if self.type in list :
            list[self.type]()
            self.report({'INFO'}, f"Mesh Set {self.type}")
        
        return {"FINISHED"}
    
class RGC_OperatorCurveToBone(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.curve_to_bone"
    bl_label = ""
    
    type: bpy.props.StringProperty(name="Type", description="The type of armature to append", default="")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        self.CurveToBone()
        
        return {"FINISHED"}   
    
class RGC_Operador_childof_clear_inverse(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.clear_inverse"
    bl_label = "Clear Inverse"
    
    constraint: bpy.props.StringProperty(name="Type", description="", default="")
    type : bpy.props.StringProperty(name="Type", description="", default="")
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        bpy.ops.constraint.childof_clear_inverse(constraint=self.constraint, owner=self.type)
        
        return {"FINISHED"}

class RGC_Operador_childof_set_inverse(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.set_inverse"
    bl_label = "Set Inverse"
    
    constraint: bpy.props.StringProperty(name="Type", description="", default="")
    type : bpy.props.StringProperty(name="Type", description="", default="")
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):

        bpy.ops.constraint.childof_set_inverse(constraint=self.constraint, owner=self.type)
        
        return {"FINISHED"}
    
class RGC_Operator_ViewSelect(GeneralArmatureData, bpy.types.Operator):
    bl_idname = "rgc.view_select"
    bl_label = ""
    
    type : bpy.props.StringProperty(name="Type", description="", default="")
    

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        props = self.PoseBoneProps()
        aprops = self.GetActiveObject()
        if self.type == "ADD":
            
            
            if props : 
                if len(props.view_select) < 1:
                    bone = aprops.save_bone_have_select_view.add()
                    bone.bone = self.GetActiveBone(mode="POSE").name
                props.view_select.add()
                props.view_select_index = len(props.view_select)-1
            

        elif self.type == "REMOVE":
            if 0 <= props.view_select_index < len(props.view_select):
                if len(props.view_select) == 1:
                    bone_name = self.GetActiveBone(mode="POSE").name
                    if bone_name in [b.bone for b in aprops.save_bone_have_select_view]:
                        for i, b in enumerate(aprops.save_bone_have_select_view):
                            if b.bone == bone_name:
                                aprops.save_bone_have_select_view.remove(i)
                                break
                props.view_select.remove(props.view_select_index)
                props.view_select_index = props.view_select_index-1
            else:
                self.report({'WARNING'}, "Índice inválido para remover")
                return {'CANCELLED'}
        return {"FINISHED"}

class RGC_Operator_ModifiersProps(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.modifier_view"
    bl_label = ""
    
    type : bpy.props.StringProperty(name="Type", description="", default="")
    index : bpy.props.IntProperty(name="Index", description="Index of the modifier to remove", default=0, min=0)
    
    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        props = self.PropsToObject()
        if props : 
            if self.type == "ADD" : 
                print("Adding modifier view")
                props.modifer_view.add()
            elif self.type == "REMOVE" : 
                print("hola")
                props.modifer_view.remove(self.index)
            
        
        return {"FINISHED"}
    
class RGC_Operator_Proxy_Low(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.proxy_low"
    bl_label = ""

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        
        self.ProxyLow()
        
        return {"FINISHED"}

class RGC_Operator_Constraint(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.constraint"
    bl_label = ""
    
    index : bpy.props.IntProperty(name="Index", description="Index of the modifier to remove", default=0, min=0)
    type : bpy.props.StringProperty(name="Type", description="", default="")

    @classmethod
    def poll(cls, context):
        return GeneralArmatureData().get_constraint(context)

    def execute(self, context):
    
        arm = self.GetActiveObject()
        con = self.get_constraint(context)
        if not con : return {'CANCELLED'}
        props = con.target.RGC_Constraint_GrupsProps
        
        if self.type == "ADD":
            new = props.targets_grups.add()
            self.SetMode("OBJECT")
            bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            col = self.CreateCollection("RGC_Constraint_Targets")
            empty = self.GetActiveObject()
            self.LinktoCollectin(col, empty)
            empty.name = f"Target"
            c = empty.constraints.new(type='COPY_TRANSFORMS')
            new.object = empty
            new.name = empty.name
            self.ActiveObj(arm)
            if arm.type == "ARMATURE" :
                self.SetMode("POSE")
                
        elif self.type == "ADDSELECT":
            mode = self.GetObjMode()
            objs = self.GetSelectBones("POSE", only_select= True) if mode == "POSE" else self.GetSelectableObjects()
            for t in objs :
                if not t : continue
                t = t.name
                new = props.targets_grups.add()
                self.SetMode("OBJECT")
                bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
                col = self.CreateCollection("RGC_Constraint_Targets")
                empty = self.GetActiveObject()
                self.LinktoCollectin(col, empty)
                empty.name = t
                c = empty.constraints.new(type='COPY_TRANSFORMS')
                c.target = arm
                c.subtarget = t
                new.object = empty
                new.name = empty.name
                self.ActiveObj(arm)
                if arm.type == "ARMATURE" :
                    self.SetMode(mode)
                    
        elif self.type == "REMOVE":
            self.SetMode("OBJECT")
            grups = props.targets_grups[self.index]
            if grups.object:
                bpy.data.objects.remove(grups.object, do_unlink=True)
                grups.object = None
            props.targets_grups.remove(self.index)
            self.ActiveObj(arm)
            if arm.type == "ARMATURE" :
                self.SetMode("POSE")
                
        elif self.type == "DUPLICATE" : 
            obj = con.target 
            copy_obj = obj.copy()
            con.target = copy_obj
            col = self.CreateCollection("RGC_Constraint_Targets")
            self.LinktoCollectin(col, copy_obj)
        
        return {"FINISHED"}

class RGC_Operator_AddNode(OperatorGeneral, bpy.types.Operator):
    bl_idname = "rgc.add_nodes"
    bl_label = ""
    
    index : bpy.props.IntProperty(name="Index", description="Index of the modifier to remove", default=0, min=0)
    type : bpy.props.StringProperty(name="Type", description="", default="")

    def execute(self, context):
        
        if self.type == "ADDNODE": 
            tree = context.space_data.node_tree
            obj = next(
                (
                    o for o in bpy.data.objects
                    if any(mod.type == 'NODES' and mod.node_group == tree for mod in o.modifiers)
                ),
                None
            )
            subtargets = obj.RGC_Constraint_GrupsProps.targets_grups
            target = subtargets[self.index]
            if target.object:
                bpy.ops.node.add_node(use_transform=True, type='GeometryNodeObjectInfo')
                node = context.active_node
                node.inputs['Object'].default_value = target.object
                node.transform_space = 'RELATIVE'
                for ip in node.inputs:
                    ip.hide = True
                node.outputs[-1].hide = True
                node.use_custom_color = True
                node.color = (0.464343, 0.531639, 0.397047)
                node.label = target.name
                
        elif self.type == "OPENCONSTRAINTNODE" :
            
            con = self.get_constraint(context)
            obj = con.target
            mod = obj.modifiers[0]
            nt = mod.node_group

            wm = context.window_manager

            # --- 1. Buscar Node Editor existente en ventana actual ---
            current_window = context.window
            found = False

            for area in current_window.screen.areas:
                if area.type == 'NODE_EDITOR':
                    for space in area.spaces:
                        if space.type == 'NODE_EDITOR':
                            space.pin = True
                            space.tree_type = 'GeometryNodeTree'
                            space.node_tree = nt
                            found = True
                            break
                if found:
                    break

            # --- 2. Si NO existía, crear nueva ventana ---
            if not found:
                bpy.ops.wm.window_new()
                new_window = wm.windows[-1]

                for area in new_window.screen.areas:
                    if area.type != 'NODE_EDITOR':
                        area.type = 'NODE_EDITOR'

                    if area.type == 'NODE_EDITOR':
                        for space in area.spaces:
                            if space.type == 'NODE_EDITOR':
                                space.pin = True
                                space.tree_type = 'GeometryNodeTree'
                                space.node_tree = nt
                                found = True
                                break
                    if found:
                        break
        
        elif self.type == "ADDCONSTRAINTNODE":
            
            arm = self.GetActiveObject()
            con = self.get_constraint(context)
            if not con : return {'CANCELLED'}
            if arm.type == "ARMATURE" :
                bone = self.GetActiveBone(mode="POSE")
                name = f"{arm.name}_{con.name}_{bone.name}"
            name = f"{arm.name}_{con.name}"
            obj = None
            self.SetMode("OBJECT")
            
            import bmesh

            # Crear un nuevo mesh
            mesh = bpy.data.meshes.new("SingleVertexMesh")

            # Crear un objeto que use ese mesh
            col = self.CreateCollection("RGC_Constraint_Targets")
            obj = bpy.data.objects.new("SingleVertexObject", mesh)
            self.LinktoCollectin(col, obj)
            obj.name = name
            obj = obj
            # Añadir el objeto a la escena activa
            bpy.context.collection.objects.link(obj)

            # Crear un bmesh para añadir vértices
            bm = bmesh.new()
            bm.verts.new((0, 0, 0))  # Vértice en el origen
            bm.to_mesh(mesh)
            bm.free()
            
            self.ActiveObj(obj)
            
            # Añadir modifier Geometry Nodes
            obj.modifiers.new(name = obj.name, type='NODES')
            mod = obj.modifiers[-1]  # Último añadido
            mod.name = obj.name
            
            # Crear un Node Group custom con nombre igual al objeto
            ng = bpy.data.node_groups.new(name=obj.name, type='GeometryNodeTree')
            mod.node_group = ng
            ng.is_modifier = True

            socket = ng.interface.new_socket(name = "POINT", in_out = "OUTPUT")
            socket.socket_type = "NodeSocketGeometry"

            socket = ng.interface.new_socket(name = "POINT", in_out = "INPUT")
            socket.socket_type = "NodeSocketGeometry"

            
            # Crear nodo Group Input
            input_node = ng.nodes.new(type='NodeGroupInput')
            input_node.location = (-300, 0)

            # Crear nodo Group Output
            output_node = ng.nodes.new(type='NodeGroupOutput')
            output_node.location = (300, 0)

            # Conectar el output de Input al input de Output
            # Por defecto, el primer socket de cada nodo es Geometry
            ng.links.new(input_node.outputs[0], output_node.inputs[0])
            
            # Añadir socket de salida al Node Group
            socket = ng.interface.new_socket(name = "TARGET", in_out = "OUTPUT")
            socket.socket_type = "NodeSocketMatrix"


            # Configurar nombre de atributo
            socket.default_attribute_name = "TARGET"

            # Asignar al modifier

            mod["Socket_0_attribute_name"] = "TARGET"

            # Configurar el modifier para apuntar al atributo
            mod["Socket_2_attribute_name"] = "TARGET"
            
            self.ActiveObj(arm)
            if arm.type == "ARMATURE" :
                self.SetMode("POSE")
            
            
            con = self.get_constraint(context)
            con.target = obj
            con.attribute_name = "TARGET"
            con.data_type = 'FLOAT4X4'

   
            

        
        return {"FINISHED"}

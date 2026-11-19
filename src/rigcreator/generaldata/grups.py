
import bpy
from ..generaldata import GeneralArmatureData
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

ListFinger = [
            "Thumb",
            "Index Finger",
            "Middle Finger",
            "Ring Finger",
            "Pinky",
        ]

def set_annotate(self, context, value : str):
    if getattr(self, value) is True:
        # Cambiar herramienta directamente sin override
        bpy.ops.wm.tool_set_by_id(name="builtin.annotate")
    else:
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")

enum_list = {
    'EMPTY': -1,
    'ROOT_MOVE': 0,
    'ROOT_HIP': 1,
    'SHOULDERS': 2,
    'SHOULDER': 3,
    'ROOT_ARM': 4,
    'HAND': 5,
}

index_list = {
    -1: 'EMPTY',
    0: 'ROOT_MOVE',
    1: 'ROOT_HIP',
    2: 'SHOULDERS',
    3: 'SHOULDER',
    4: 'ROOT_ARM',
    5: 'HAND',
}

leg_enum_list = {
    'EMPTY': -1,
    'ROOT_MOVE': 0,
    'ROOT_HIP': 1,
    'ROOT_LEG': 2,
    
}

leg_index_list = {
    -1: 'EMPTY',
    0: 'ROOT_MOVE',
    1: 'ROOT_HIP',
    2: 'ROOT_LEG',
    
}

# Variable global para evitar recursión infinita
is_updating = False

def Index(self, context, self_property, other_property):
    global index_list, is_updating
    if is_updating:
        return  # Evita la recursión infinita
    try:
        prop = GeneralArmatureData().PropsToArmature()[0]
        value = getattr(prop, self_property)
        # Activamos la bandera antes de la actualización
        is_updating = True
        setattr(prop, other_property, index_list[value])
        # Desactivamos la bandera después de la actualización
        is_updating = False
    except (KeyError, AttributeError, IndexError) as e:
        print(f"Index Error: {e}")
        is_updating = False

def Enum(self, context, self_property, other_property):
    global enum_list, is_updating
    if is_updating:
        return  # Evita la recursión infinita
    try:
        prop = GeneralArmatureData().PropsToArmature()[0]
        # Activamos la bandera antes de la actualización
        is_updating = True
        setattr(prop, other_property, enum_list[getattr(prop, self_property)])
        # Desactivamos la bandera después de la actualización
        is_updating = False
    except (KeyError, AttributeError, IndexError) as e:
        print(f"Enum Error: {e}")
        is_updating = False

def Leg_Index(self, context, self_property, other_property):
    global leg_index_list, is_updating
    if is_updating:
        return  # Evita la recursión infinita
    try:
        prop = GeneralArmatureData().PropsToArmature()[0]
        value = getattr(prop, self_property)
        # Activamos la bandera antes de la actualización
        is_updating = True
        setattr(prop, other_property, leg_index_list[value])
        # Desactivamos la bandera después de la actualización
        is_updating = False
    except (KeyError, AttributeError, IndexError) as e:
        print(f"Index Error: {e}")
        is_updating = False

def Leg_Enum(self, context, self_property, other_property):
    global leg_enum_list, is_updating
    if is_updating:
        return  # Evita la recursión infinita
    try:
        prop = GeneralArmatureData().PropsToArmature()[0]
        # Activamos la bandera antes de la actualización
        is_updating = True
        setattr(prop, other_property, leg_enum_list[getattr(prop, self_property)])
        # Desactivamos la bandera después de la actualización
        is_updating = False
    except (KeyError, AttributeError, IndexError) as e:
        print(f"Enum Error: {e}")
        is_updating = False

def all_finger_enum(self, context, self_property):
    global enum_list, is_updating
    if is_updating:
        return  # Evita la recursión infinita
    try:
        fingers = GeneralArmatureData().ListFinger()
        for finger in fingers:
            prop = GeneralArmatureData().PropsToArmature()[0]
            name = finger.replace(" ", "").lower()
            name_property = self_property
            if 'fingers_stretch_to' in self_property:
                name_property = name_property.replace('fingers_stretch_to', 'fingers_stretch_t')
            other_property = f"{name}{name_property.replace('fingers', '')}"
            value = getattr(prop, self_property )
            setattr(prop, other_property, value)
        is_updating = False
        
    except (KeyError, AttributeError, IndexError) as e:
        print(f"Enum Error: {e}")
        is_updating = False

def polecheck(self, constex, self_property : str, data_path : str) :
    RGC = GeneralArmatureData()
    
    obj_active = RGC.GetActiveObject()
    get_mode = RGC.GetObjMode()
    if not obj_active : return 
    
    
    def SetParentPole(bone_name : str) :
        bones_name = [bone_name]
        
        if f"sub" in bone_name :
            return
        
        root_parent_name = f"ROOT_{bone_name.upper()}"
        subroot_parent_name_1 = f"ROOT_{bone_name.upper()}_1"
        subroot_parent_name_2 = f"ROOT_{bone_name.upper()}_2"
        parent_root_pole_name = ""
        root_chenge_ik_name = ""
        look_pole = ""
        
                

        RGC.SetMode("POSE")
        
        def getchange(bone) :
            if not bone:
                return None
            
            # Revisa si este hueso tiene un constraint tipo ARMATURE
            for c in bone.constraints:
                if c.type == "ARMATURE":
                    return bone  # devolvemos el hueso inmediatamente

            # Si no lo tiene y existe padre, sube recursivamente
            if bone.parent:
                return getchange(bone.parent)
            
            # Si no hay constraint y no hay más padres
            return None
        
        for b in obj_active.pose.bones :
            if b.constraints :
                for cot in b.constraints :
                    if cot.type == "IK" :
                        if cot.pole_subtarget == bone_name :
                            parent_root_pole_name = b.parent.name 
                            change_ik = RGC.GetBone(cot.subtarget, "POSE")
                            look_pole = cot.subtarget
                            root_chenge_ik_name = getchange(change_ik).name if getchange(change_ik) else ""


        if parent_root_pole_name == "" or root_chenge_ik_name == "" : 
            RGC.SetMode(get_mode)
            return
        
        RGC.SetMode("EDIT")
        
        if not bones_name : return            
        
        bones = RGC.GetBones(bones_name, mode="EDIT")
        root_ik_bones = RGC.GetBone(parent_root_pole_name, mode="EDIT")
        root_chenge_ik = RGC.GetBone(root_chenge_ik_name, mode="EDIT")
        root_bones = RGC.CreateBones([root_parent_name, subroot_parent_name_1, subroot_parent_name_2])
        RGC.SetDeform(root_bones, False)
        for b in root_bones :
            RGC.SetTransform(b, bones[0])
        
        RGC.SetTransform(root_bones[1], root_ik_bones)
        root_bones[1].parent = root_ik_bones.parent 
        root_bones[1].tail  = RGC.GetBone(look_pole, mode="EDIT").head
        
        root_bones[0].parent = root_bones[1]
        root_bones[2].parent = root_chenge_ik
        
        for b in bones :
            b.parent = root_bones[0]
        
        for b in root_bones :
            RGC.BoneCollectionUnassing(b)
            RGC.BoneCollectionAssing("Control_Bone", b)
        
        RGC.SetMode("POSE")
        
        root_bones = RGC.GetBones([root_parent_name, subroot_parent_name_1, subroot_parent_name_2], mode="POSE")
        root_chenge_ik = RGC.GetBone(root_chenge_ik_name, mode="POSE")
        
        if root_bones[1] and root_chenge_ik:
            c = root_bones[1].constraints.new(type='DAMPED_TRACK')
            c.target = RGC.GetActiveObject()
            c.subtarget = look_pole
        
        if root_bones[0] :
            c = root_bones[0].constraints.new(type='COPY_TRANSFORMS')
            c.target = RGC.GetActiveObject()
            c.subtarget = root_bones[2].name
            
            # Agregar driver a la influencia del constraint
            fcurve = c.driver_add("influence")
            drv = fcurve.driver
            drv.type = 'AVERAGE'

            # Crea una variable que apunte a la propiedad que quieres usar como controlador
            var = drv.variables.new()
            var.name = "ctrl"           # nombre interno
            var.targets[0].id = RGC.GetActiveObject()  # el objeto que tiene la propiedad
            var.targets[0].data_path = f'RGC_Armature_GrupsProps[0].{data_path}'  # ruta de la propiedad BoolProperty

            
        
        bones = RGC.GetBones(bones_name, mode="POSE")
        for b in bones :
            for constraint in b.constraints:
                b.constraints.remove(constraint)
        RGC.SetMode(get_mode)
    def Check(name : str ) :
        root = f"ROOT_{name.upper()}"
        if RGC.GetBone(root) : return
        for i in range(10000) :
            if i == 0 :
                bone = RGC.GetBone(name)
                if not bone : continue
                SetParentPole(name)                        
            else :
                bone_name = f"{name}.{i:003}"
                bone = RGC.GetBone(bone_name)
                if not bone : break
                SetParentPole(bone_name)
    
    match self_property :
        case "ARM_L" :
            Check("polearm_L")
        case "ARM_R" :
            Check("polearm_R")
        case "LEG_L" :
            Check("poleleg_L")
        case "LEG_R" :
            Check("poleleg_R")

    
    
class RGC_Save_Bones_Have_Select_View(bpy.types.PropertyGroup):
    bone : StringProperty(default="")



def get_modifiers(self, context):
    items = []
    obj = self.object
    if obj:
        for mod in obj.modifiers:
            items.append((mod.name, mod.name, ""))
    return items if items else [("None", "None", "No modifiers found")]


def update_object(self, context):
    # Esto solo fuerza que Blender reconozca un cambio
    self["modifier"] = ""  # limpia selección anterior para evitar errores


class RGC_Modifier_ViewProps(bpy.types.PropertyGroup):
    object: PointerProperty(
        name="Target Object",
        type=bpy.types.Object,
        update=update_object
    )

    modifier: EnumProperty(
        name="Modifier",
        description="Choose a modifier",
        items=get_modifiers
    )
    use_key: BoolProperty(default= True, subtype = "FACTOR")
    key : StringProperty(default="View_")


## Edit Armature
def StretchTo(self, context, type : str, bone : str) :
    RGC = GeneralArmatureData()
    
    bones = RGC.GetBonesToRange(bone, 10, mode="POSE")
    Cbones = RGC.GetBonesToRange(f"C_{bone}", 10, mode="POSE")
    for listb in [bones, Cbones] :
        for b in listb :
            if not b : continue
            for c in b.constraints :
                if c.type == "STRETCH_TO" :
                    c.bulge = self[type]

def EditTransform(self, context, type : str, bones=[]) :
    RGC = GeneralArmatureData()
    bones = RGC.GetBones(bones, mode="POSE")
    for b in bones :
        if not b : continue
        for c in b.constraints :
            if c.type == "TRANSFORM" :
                c.influence = self[type]

def EditSegments(self, context, type : str) :
    RGC = GeneralArmatureData()
    arm = RGC.GetActiveObject()
    for bone in arm.data.bones :
        if bone.use_deform :
            if bone.bbone_segments != 1 :
                bone.bbone_segments = self[type]

def UseRotBrow(self, context, type : str) :
    RGC = GeneralArmatureData()
    for dir in ["R", "L"] :
        def_bone = RGC.GetBonesToRange(f"def_eyebrows_{dir}", 4, mode="OBJECT")
        cont_bone = RGC.GetBonesToRange(f"cont_eyebrows_{dir}", 5, mode="OBJECT")
        if self[type] == True :
            for i, bone in enumerate(def_bone) :
                bone.bbone_handle_type_start = 'TANGENT'
                bone.bbone_custom_handle_start = cont_bone[i]
                RGC.SetColorBone(cont_bone[i], 'THEME03')

                bone.bbone_handle_type_end = 'TANGENT'
                bone.bbone_custom_handle_end = cont_bone[i+1]
                RGC.SetColorBone(cont_bone[i+1], 'THEME03')

        else :
            for i, bone in enumerate(def_bone) :
                bone.bbone_handle_type_start = 'AUTO'
                bone.bbone_custom_handle_start = None
                RGC.SetColorBone(cont_bone[i], 'THEME09')
                bone.bbone_handle_type_end = 'AUTO'
                bone.bbone_custom_handle_end = None
                RGC.SetColorBone(cont_bone[i+1], 'THEME09')

def EditAllConstraint(self, context, type : str, bones = []) :
    
    RGC = GeneralArmatureData()
    bones = RGC.GetBones(bones, mode="POSE")
    for bone in bones:
        if not bone : continue
        for c in bone.constraints :
            c.influence = self[type]

class RGC_Object_GrupsProps(bpy.types.PropertyGroup):
    
     # Modifier View
    modifer_view: CollectionProperty(type=RGC_Modifier_ViewProps)
    
    # Car rig Cuerpos
    use_object_reference : BoolProperty()
    object_body : PointerProperty(type = bpy.types.Object)
    object_wheel_front_L : PointerProperty(type = bpy.types.Object)
    object_wheel_front_R : PointerProperty(type = bpy.types.Object)
    object_wheel_back_L : PointerProperty(type = bpy.types.Object)
    object_wheel_back_R : PointerProperty(type = bpy.types.Object)
    
    # Edit Armature
    
  
    
    
    bbone_segments : IntProperty(
        default = 32, min = 2, max = 32, update = lambda self, context : EditSegments(self, context, "bbone_segments")
    )
    use_rot_brow : BoolProperty(
        default = False, update = lambda self, context : UseRotBrow(self, context, "use_rot_brow")
    )
    
    # arco 
    ac_eyelip_up_L : FloatProperty(default=0.8, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context : EditAllConstraint(self, context, type = "ac_eyelip_up_L", bones = ["rot_eye_UP_L.002"]))
    ac_eyelip_up_R : FloatProperty(default=0.8, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context : EditAllConstraint(self, context, type = "ac_eyelip_up_R", bones = ["rot_eye_UP_R.002"]))
   
    ac_eyelip_down_L : FloatProperty(default=0.7, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context : EditAllConstraint(self, context, type = "ac_eyelip_down_L", bones = ["rot_eye_DOWN_L.002"]))
    ac_eyelip_down_R : FloatProperty(default=0.7, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context : EditAllConstraint(self, context, type = "ac_eyelip_down_R", bones = [ "rot_eye_DOWN_R.002"]))

    #volimen 
    vl_arm_L : FloatProperty(default=1.0, min = 0.0, max=100.0, 
    update = lambda self, context : StretchTo(self, context, "vl_arm_L", "subarm_L"),options={'HIDDEN'})
    vl_arm_R : FloatProperty(default=1.0, min = 0.0, max=100.0, 
    update = lambda self, context : StretchTo(self, context, "vl_arm_R", "subarm_R"),options={'HIDDEN'})
    vl_leg_L : FloatProperty(default=1.0, min = 0.0, max=100.0, 
    update = lambda self, context : StretchTo(self, context, "vl_leg_L", "subleg_L"),options={'HIDDEN'})
    vl_leg_R : FloatProperty(default=1.0, min = 0.0, max=100.0, 
    update = lambda self, context : StretchTo(self, context, "vl_leg_R", "subleg_R"),options={'HIDDEN'})

    # Face
    f_brow : FloatProperty(default=0.05, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context :EditTransform(self, context, "f_brow", bones = ["mov_eyebrows_L","mov_eyebrows_R"]))
    
    
    f_brow_L : FloatProperty(default=0.5, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context :EditAllConstraint(self, context, "f_brow_L", bones = ["mov_subeyebrows_L"]))
    f_brow_R : FloatProperty(default=0.5, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context :EditAllConstraint(self, context, "f_brow_R", bones = ["mov_subeyebrows_R"]))
    
    
    f_mouth_up : FloatProperty(default=0.05, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context :EditTransform(self, context, "f_mouth_up", bones = ["rot_mouth_UP"]))
    
    f_mouth_down : FloatProperty(default=0.05, min=0, max=1.0, subtype = "FACTOR", options={'HIDDEN'}, 
     update = lambda self, context :EditTransform(self, context, "f_mouth_down", bones = ["rot_mouth_DOWN"]))
    
    
class RGC_Armature_GrupsProps(bpy.types.PropertyGroup):

    #save_Bone
    
    # View properties 

    view_head : BoolProperty(default=True)
    view_face : BoolProperty(default=True)
    view_arm_L : BoolProperty(default=True)
    view_arm_R : BoolProperty(default=True)
    view_fingers_L : BoolProperty(default=True)
    view_fingers_R : BoolProperty(default=True)
    view_leg_L : BoolProperty(default=True)
    view_leg_R : BoolProperty(default=True)
    
    #Global Local
    head : FloatProperty(default=1,min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_items = [
        ('EMPTY', "Empty", ""),
        ('ROOT_MOVE', "Root Move", ""),
        ('ROOT_HIP', "Root Hip", ""),
        ('SHOULDERS', "Shoulders", ""),
        ('SHOULDER', "Shoulder", ""),
        ('ROOT_ARM', "Root Arm", ""),
    ]
    eyes : FloatProperty(default=2,min=0.0, max=2.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    # Boca
    corner_mouth_L : FloatProperty(default=1,min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    corner_mouth_R : FloatProperty(default=1,min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arc_L : FloatProperty(default=0.5,min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arc_R : FloatProperty(default=0.5,min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    tongue_ik_fk : FloatProperty(default=1, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    tongue_stretch_to : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    # ARMS
    arm_ik_fk_L : FloatProperty(default=1, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_ik_fk_R : FloatProperty(default=1, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_stretch_to_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_stretch_to_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    elbow_cartoon_L : FloatProperty(default=0, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    elbow_cartoon_R : FloatProperty(default=0, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    arm_pole_followed_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"},
        update=lambda self, context: polecheck(self, context, "ARM_L", "arm_pole_followed_L"))
    arm_pole_followed_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"},
        update=lambda self, context: polecheck(self, context, "ARM_R", "arm_pole_followed_R"))
    
    
    
    arm_followed_L : IntProperty(
        default=4,
        min=-1, max=4,
        update=lambda self, context: Index(self, context, "arm_followed_L", "arm_followed_enum_L"),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"}
    )
    arm_followed_R : IntProperty(
        default=4,
        min=-1, max=4,
        update=lambda self, context: Index(self, context, "arm_followed_R", "arm_followed_enum_R"),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    arm_items = [
        ('EMPTY', "Empty", ""),
        ('ROOT_MOVE', "Root Move", ""),
        ('ROOT_HIP', "Root Hip", ""),
        ('SHOULDERS', "Shoulders", ""),
        ('SHOULDER', "Shoulder", ""),
        ('ROOT_ARM', "Root Arm", ""),
    ]

    arm_followed_enum_L: EnumProperty(
        items=arm_items,
        name='Followed L',
        default='ROOT_ARM',
        update=lambda self, context: Enum(self,context,"arm_followed_enum_L", "arm_followed_L"),
        options={'LIBRARY_EDITABLE'},override={"LIBRARY_OVERRIDABLE"}
    )
    arm_followed_enum_R: EnumProperty(
        items=arm_items,
        name='Followed R',
        default='ROOT_ARM',
        update=lambda self, context: Enum(self, context, "arm_followed_enum_R", "arm_followed_R"),
        options={'LIBRARY_EDITABLE'},override={"LIBRARY_OVERRIDABLE"}
    )
    
    arm_invert_ik_fk_L : BoolProperty(options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    arm_invert_ik_fk_R : BoolProperty(options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})


    # FINGERS
    
    """
    for type in ["R", "L"]:
        for prop in ListFinger():
            clean_name = prop.replace(" ", "").lower()
            FK_a_IK = f"{clean_name}_fk_a_ik_{type}"
            Stretch_To = f"{clean_name}_stretch_t_{type}"
            Rot = f"{clean_name}_rot_{type}"
            Followed = f"{clean_name}_followed_{type}"
            Enum = f"{clean_name}_enum_{type}"
            
            print(f"    {FK_a_IK} : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR')")
            print(f"    {Stretch_To} : BoolProperty(default=True)")
            print(f"    {Rot} : BoolProperty(default=True)")
            print(f"    {Followed} : IntProperty(default=4,min=0, max=5, update=lambda self, context: Index(self, context, '{Followed}', '{Enum}'),)")
            print(f"    {Enum} : EnumProperty(items=arm_items,name='Followed_{type}',default='HAND',update=lambda self, context: Enum(self, context, '{Enum}', '{Followed}'),options="+"{'HIDDEN'})")
    """
    
    
    arm_items = [
        ('ROOT_MOVE', "Root Move", ""),
        ('ROOT_HIP', "Root Hip", ""),
        ('SHOULDERS', "Shoulders", ""),
        ('SHOULDER', "Shoulder", ""),
        ('ROOT_ARM', "Root Arm", ""),
        ('HAND', "Hand", ""),
    ]
    
    fingers_fk_a_ik_L : FloatProperty(
        default=1.0, min=0.0, max=1.0, subtype='FACTOR',
        update=lambda self, context: all_finger_enum(self, context, 'fingers_fk_a_ik_L'),
        options={'LIBRARY_EDITABLE',},override={"LIBRARY_OVERRIDABLE"}
        )
    fingers_fk_a_ik_R : FloatProperty(
        default=1.0, min=0.0, max=1.0, subtype='FACTOR',
        update=lambda self, context: all_finger_enum(self, context, 'fingers_fk_a_ik_R'),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"}
        )
    fingers_stretch_to_L : BoolProperty(
        default=True,
        update=lambda self, context: all_finger_enum(self, context, 'fingers_stretch_to_L'),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"}
        )
    fingers_stretch_to_R : BoolProperty(
        default=True,
        update=lambda self, context: all_finger_enum(self, context, 'fingers_stretch_to_R'),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"}
        )
    fingers_followed_L : IntProperty(default=4,min=0, max=5, 
    update=lambda self, context: all_finger_enum(self, context, 'fingers_followed_L'),
    options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    fingers_followed_R : IntProperty(default=4,min=0, max=5, 
    update=lambda self, context: all_finger_enum(self, context, 'fingers_followed_R'),
    options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    fingers_enum_L : EnumProperty(items=arm_items,name='Followed_R',
    default='HAND',update=lambda self, context: all_finger_enum(self, context, 'fingers_enum_L'),
    options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    fingers_enum_R : EnumProperty(items=arm_items,name='Followed_R',
    default='HAND',update=lambda self, context: all_finger_enum(self, context, 'fingers_enum_R'),
    options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})

    thumb_fk_a_ik_R : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_stretch_t_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_followed_R : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'thumb_followed_R', 'thumb_enum_R'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_enum_R : EnumProperty(items=arm_items,name='Followed_R',default='HAND',update=lambda self, context: Enum(self, context, 'thumb_enum_R', 'thumb_followed_R'),options={'LIBRARY_EDITABLE'})
    
    indexfinger_fk_a_ik_R : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_stretch_t_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_followed_R : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'indexfinger_followed_R', 'indexfinger_enum_R'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_enum_R : EnumProperty(items=arm_items,name='Followed_R',default='HAND',update=lambda self, context: Enum(self, context, 'indexfinger_enum_R', 'indexfinger_followed_R'),options={'LIBRARY_EDITABLE'})
    
    middlefinger_fk_a_ik_R : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_stretch_t_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_followed_R : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'middlefinger_followed_R', 'middlefinger_enum_R'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_enum_R : EnumProperty(items=arm_items,name='Followed_R',default='HAND',update=lambda self, context: Enum(self, context, 'middlefinger_enum_R', 'middlefinger_followed_R'),options={'LIBRARY_EDITABLE'})
    
    ringfinger_fk_a_ik_R : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_stretch_t_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_followed_R : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'ringfinger_followed_R', 'ringfinger_enum_R'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_enum_R : EnumProperty(items=arm_items,name='Followed_R',default='HAND',update=lambda self, context: Enum(self, context, 'ringfinger_enum_R', 'ringfinger_followed_R'),options={'LIBRARY_EDITABLE'})
    
    pinky_fk_a_ik_R : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_stretch_t_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_rot_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_followed_R : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'pinky_followed_R', 'pinky_enum_R'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_enum_R : EnumProperty(items=arm_items,name='Followed_R',default='HAND',update=lambda self, context: Enum(self, context, 'pinky_enum_R', 'pinky_followed_R'),options={'LIBRARY_EDITABLE'})
    
    thumb_fk_a_ik_L : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_stretch_t_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_followed_L : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'thumb_followed_L', 'thumb_enum_L'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    thumb_enum_L : EnumProperty(items=arm_items,name='Followed_L',default='HAND',update=lambda self, context: Enum(self, context, 'thumb_enum_L', 'thumb_followed_L'),options={'LIBRARY_EDITABLE'})
    
    indexfinger_fk_a_ik_L : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_stretch_t_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_followed_L : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'indexfinger_followed_L', 'indexfinger_enum_L'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    indexfinger_enum_L : EnumProperty(items=arm_items,name='Followed_L',default='HAND',update=lambda self, context: Enum(self, context, 'indexfinger_enum_L', 'indexfinger_followed_L'),options={'LIBRARY_EDITABLE'})
    
    middlefinger_fk_a_ik_L : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_stretch_t_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_followed_L : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'middlefinger_followed_L', 'middlefinger_enum_L'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    middlefinger_enum_L : EnumProperty(items=arm_items,name='Followed_L',default='HAND',update=lambda self, context: Enum(self, context, 'middlefinger_enum_L', 'middlefinger_followed_L'),options={'LIBRARY_EDITABLE'})
    
    ringfinger_fk_a_ik_L : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_stretch_t_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_followed_L : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'ringfinger_followed_L', 'ringfinger_enum_L'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    ringfinger_enum_L : EnumProperty(items=arm_items,name='Followed_L',default='HAND',update=lambda self, context: Enum(self, context, 'ringfinger_enum_L', 'ringfinger_followed_L'),options={'LIBRARY_EDITABLE'})
    
    pinky_fk_a_ik_L : FloatProperty(default=1.0, min=0.0, max=1.0, subtype='FACTOR',options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_stretch_t_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_rot_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_followed_L : IntProperty(default=4,min=-1, max=5, update=lambda self, context: Index(self, context, 'pinky_followed_L', 'pinky_enum_L'),options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    pinky_enum_L : EnumProperty(items=arm_items,name='Followed_L',default='HAND',update=lambda self, context: Enum(self, context, 'pinky_enum_L', 'pinky_followed_L'),options={'LIBRARY_EDITABLE'})
    
    # LEGS
    leg_ik_fk_L : FloatProperty(default=1, min=0.0, max=1.0,subtype = "FACTOR",
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_ik_fk_R : FloatProperty(default=1, min=0.0, max=1.0,subtype = "FACTOR",
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_stretch_to_L : BoolProperty(default=True,
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_stretch_to_R : BoolProperty(default=True,
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_rot_L : BoolProperty(default=True,
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_rot_R : BoolProperty(default=True,
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_invert_ik_fk_L : BoolProperty(
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_invert_ik_fk_R : BoolProperty(
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    
    leg_pole_followed_L : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"},
        update=lambda self, context: polecheck(self, context, "LEG_L", "leg_pole_followed_L"))
    leg_pole_followed_R : BoolProperty(default=True,options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"},
        update=lambda self, context: polecheck(self, context, "LEG_R", "leg_pole_followed_R"))

    leg_items = [
        ('EMPTY', "Empty", ""),
        ('ROOT_MOVE', "Root Move", ""),
        ('ROOT_HIP', "Root Hip", ""),
        ('ROOT_LEG', "Root Leg", ""),
    ]
    
    leg_followed_L : IntProperty(
        default=0,min=-1, max=2, 
        update=lambda self, context: Leg_Index(self, context, 'leg_followed_L', 'leg_followed_enum_L'),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_followed_enum_L : EnumProperty(
        items=leg_items,name='Followed_L',default='ROOT_MOVE',
        update=lambda self, context: Leg_Enum(self, context, 'leg_followed_enum_L', 'leg_followed_L'),
        options={'LIBRARY_EDITABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_followed_R : IntProperty(
        default=0,min=-1, max=2, 
        update=lambda self, context: Leg_Index(self, context, 'leg_followed_R', 'leg_followed_enum_R'),
        options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_followed_enum_R : EnumProperty(
        items=leg_items,name='Followed_L',default='ROOT_MOVE',
        update=lambda self, context: Leg_Enum(self, context, 'leg_followed_enum_R', 'leg_followed_R'),
        options={'LIBRARY_EDITABLE'},override={"LIBRARY_OVERRIDABLE"})
    
    leg_elbow_cartoon_L : FloatProperty(default=0, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    leg_elbow_cartoon_R : FloatProperty(default=0, min=0.0, max=1.0,subtype = "FACTOR",options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    

def UpdateType(self, context):
    GN = GeneralArmatureData()
    prop = GN.Props()
    prop.annotate_auto_bone = False

class RGC_GrupsProps(GeneralArmatureData, bpy.types.PropertyGroup):
    
    
    
    # RESET 
    use_delect_bones : BoolProperty(default=False, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    
    # Proxy Low
    
    pl_enum: EnumProperty(items=[
        ('OBJECT', "Select Objects", ""),
        ('COLLECTION', "Collection", ""),
        ('SCENE', "Scene Objects", ""),
        ], 
        name='Type', 
        default='OBJECT', 
    )
    
    pl_enum_type: EnumProperty(items=[
        ('DECIMATE', "Decimete", ""),
        ('PRIMITIVE', "Primitive", ""),
        ], 
        name='how form', 
        default='DECIMATE', 
    )
    
    pl_collection_to_create_proxy : PointerProperty(
    name="Colección",
    type=bpy.types.Collection,
    description="Selecciona la colección de origen"
    )
    pl_collection_name : StringProperty(default="ProxyLow")
    pl_decimate_ratio : FloatProperty(default = 0.4, min=0, max=1.0,subtype = "FACTOR",)
    pl_decimate_ratio_vert : IntProperty(default = 1000, min=200,)
    pl_delectmaterial : BoolProperty(default=True)
    pl_angle_limit : FloatProperty(default = 0.0872665, min=0, max=3.13985,subtype = "ANGLE",)

    pl_armature : PointerProperty(type = bpy.types.Object, poll=lambda self, obj: obj.type == 'ARMATURE')
    ol_detail : IntProperty(default=1, min=0, max=3)
    
    # GN 
    panel_type : EnumProperty(
        items=[
            ('ALL', "All", ""),
            ('ANIMATION', "Animation", ""),
            ('RIG', "Rigging", ""),
            
        ],
        name='Panel Type',
        default={'ANIMATION'}, 
        options={'ENUM_FLAG'},
        update=UpdateType
    ) 
    
    use_sub_divide_bones : BoolProperty()
    sub_divide_bone_segments : IntProperty(
        default=4, min=2,
    )
    
    # Add Bone Pose
    use_add_bone_deform : BoolProperty(default=True, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    use_add_bone_parent_to_select : BoolProperty(default=True, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    use_add_bone_invert_parent : BoolProperty(default=False, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    use_add_bone_parent : BoolProperty(default=False, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    use_add_bone_connected : BoolProperty(default=False, options={'LIBRARY_EDITABLE', 'ANIMATABLE'})
    ### Generators
    #Generators_List : CollectionProperty(type=RGC_Generators_GrupsProps)
    #Generators_index : IntProperty(options={'HIDDEN'})
    
    #browser 
    generators_browser : StringProperty()
    
    # Fisicas Props Groups
    use_stretch_to : BoolProperty()
    power_stretch : FloatProperty(min=0, max=10.0,subtype = "FACTOR",)
    power_overlapping : FloatProperty(min = 0, max = 0.8, subtype = "FACTOR")
    frame_start : IntProperty(default=1)
    frame_end : IntProperty( default=240)
    frame_step : IntProperty(default=1, min=1)
    
    # Fingers Props Groups
    use_fk : BoolProperty(default=True)
    use_def : BoolProperty(default=True)
    use_fingers : BoolProperty(default=True)
    use_fingers_rot : BoolProperty()
    use_segments : BoolProperty(default=True)
    use_parent : BoolProperty(default=True)
    name_fk : StringProperty(default="fk_")
    name_def : StringProperty(default="def_")
    name_fingers : StringProperty(default="fingers_")
    int_segments : IntProperty(min=1, max=32, default=32)
    use_limit_rot_fingers : BoolProperty()
    limit_rot_fingers : IntProperty(min=1, default=1)
    limit_rot_fingers_invert : BoolProperty()
    
    # Fk Props Groups
    use_view_object : BoolProperty(default=(True))
    use_copy_transforms_fk : BoolProperty(default=(True))
    name_fk1 : StringProperty(default="FK")
    
    # Ik Props Groups
    use_stretch_to_ik : BoolProperty(default=(True))
    use_pole_target : BoolProperty(default=(True))
    use_ik_as: EnumProperty(items=[
        ('POLE', "Pole", ""),
        ('ROT', "Rotation", ""),
        ], 
        name='Rotation IK As', 
        default='POLE', 
    )
    use_track_to : BoolProperty(default=(True))
    use_copy_transforms_ik : BoolProperty(default=(True))
    distance_pole_target : FloatProperty(subtype = "DISTANCE", default=1)
    pole_angle : FloatProperty(subtype = "ANGLE", default=-1.5708)
    name_ik : StringProperty(default="ik_")

    # Bones Props Groups
    look_bone: EnumProperty(items=[
        ('X', "X", ""),
        ('Y', "Y", ""),
        ('Z', "Z", ""),
        ('-X', "-X", ""),
        ('-Y', "-Y", ""),
        ('-Z', "-Z", ""),
        ], 
        name='LooK Bone', 
        default={'Z'}, 
        options={'ENUM_FLAG'}
        )
    add_orientation: EnumProperty(items=[
        ('GLOBAL', "Global", ""),
        ('NORMAL', "Normal", ""),
        ], 
        name='How Orientation', 
        default='GLOBAL', 
        )
    viewport_display_type: EnumProperty(items=[
        ('SINGLE_ARROW', "Arrow", "EMPTY_SINGLE_ARROW"),
        ('CIRCLE', "Circle", "MESH_CIRCLE"),
        ('CUBE', "Cube", "CUBE"),
        ('SPHERE', "Sphere", "SPHERE"),
        ], 
        name='Type', 
        default='SPHERE', 
        )
    use_parent_bone: BoolProperty(default=(True))
    use_bone_in_tail : BoolProperty(default=(True))
    use_viewport_display: BoolProperty(default=(True))
    use_stretch_to_bone : BoolProperty(default=(True))
    name_bone: StringProperty(default="bone_")

    # Curve Props Groups
    use_curve_root: bpy.props.BoolProperty(default=(False))
    use_curve_drive: bpy.props.BoolProperty(default=(False))
    use_curve_subbone: bpy.props.BoolProperty(default=(False))
    
    curve_subbone_howmuch: bpy.props.IntProperty(default=32, min=2,)
    name_curve_def: bpy.props.StringProperty(default="def_")
    name_curve_free: bpy.props.StringProperty(default="free_")
    name_curve_cont: bpy.props.StringProperty(default="cont_")
    name_curve_root: bpy.props.StringProperty(default="root_")
    curve_int_segments: bpy.props.IntProperty(default=32, min=1, max=32)
    
    # Curve Grip Props
    grip_use_target : bpy.props.BoolProperty(default=(True))
    grip_align_to_normal : bpy.props.BoolProperty(default=(False))
    grip_align_target : bpy.props.BoolProperty(default=(False))
    grip_use_target_scale : bpy.props.BoolProperty(default=(False))
    name_grip_target: bpy.props.StringProperty(default="target_")
    name_grip_target_scale: bpy.props.StringProperty(default="scale_")
    name_grip_root: bpy.props.StringProperty(default="root_")
    grip_bulge : FloatProperty( default=1, min=0, max=100)
    grip_proximity_join : FloatProperty(default=0.0001,precision=6)
    grip_use_segments : bpy.props.BoolProperty(default=(True))
    grip_segments : IntProperty(default=32, min=1, max=32)
    
    # Auto Root 
    use_active_bone : BoolProperty(default=True)
    bones_parent : IntProperty(default=2, min=1, max=4)
    name_auto_root : StringProperty(default="root_")
    
    #Collections 
    columns_value : IntProperty(default=2, min=1, max=4)
    even_columns : BoolProperty(default=True)
    how_collection_select : StringProperty()
    edit_collection : BoolProperty()
    search_collection : StringProperty()
    
    #Properties
    use_old_prop : BoolProperty(default=False)
    
    # Bone
    edit_bone : BoolProperty(default=False)
    bone_column : IntProperty(default=1, min=1, max=4)
    bone_subcolumn : IntProperty(default=1, min=1, max=4)
    bone_use_specific_name : BoolProperty(default=False)
    bone_key : StringProperty(default="View")
    search_bone : StringProperty()
    
    # Armature
    edit_armature : BoolProperty(default=False)
    armature_column : IntProperty(default=2, min=1, max=4)
    armature_use_specific_name : BoolProperty(default=True)
    armature_key : StringProperty(default="View")
    search_armature : StringProperty()
    
    # Copy Xform ReationShip
    use_local_space : BoolProperty(default=True)
    is_save : BoolProperty(default=True)
    use_rotation : BoolProperty(default=True)
    use_scale : BoolProperty(default=True)
    
    save_matrix : FloatVectorProperty(
        default=(
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0,
            ),
        size = 16,
    )
    is_save_matrix : BoolProperty(default=False)
    
    rot_to_cursor : BoolProperty(default=False)
    
    # PIKER
    piker: EnumProperty(items=[
        ('GENERAL', "General", ""),
        ('FK', "Fk", ""),
        ('IK', "Ik", ""),
        ('DEF', "Def", ""),
        ], 
        name='How Piker', 
        default={'GENERAL'}, 
        options={'ENUM_FLAG'}
        )


    #Mesh 
    
    mesh_browser : StringProperty(default="")
    
    mesh_armature_select : PointerProperty(type = bpy.types.Object, poll=lambda self, obj: obj.type == 'ARMATURE')
    mesh_keep_object : BoolProperty(default=True)
    mesh_shape_size : FloatProperty(default=0.1, min=0.01, max=10.0,subtype = "FACTOR",)
    
    
    
    mesh_bone_name : StringProperty(default="bone")
    
    mesh_use_curve : BoolProperty(default=True)
    mesh_use_aling_roll_normal : BoolProperty(default=True)
    mesh_bone_subdivisions : IntProperty(default=1, min=1)
    mesh_use_bone_reference : BoolProperty(default=True)
    mesh_bone_reference_name : StringProperty(default="")
    mesh_use_tail : BoolProperty(default=True)
    mesh_use_parent : BoolProperty(default=True)
    mesh_with_automatic_weights : BoolProperty(default=False)
    mesh_with_by_distance_of_vertex : BoolProperty(default=False)
    
    
    mesh_use_vertcurve : BoolProperty(default=False)
    mesh_vertcurve_power : FloatProperty(default=0.1)
    
    
    # Only Bone
    ob_normal_global: EnumProperty(items=[
        ('GLOBAL', "Global", ""),
        ('NORMAL', "Normal", ""),
        ], 
        name='How Orientation', 
        default='GLOBAL', 
        )
    
    ob_direction: EnumProperty(items=[
        ('X', "X", ""),
        ('Y', "Y", ""),
        ('Z', "Z", ""),
        ('-X', "-X", ""),
        ('-Y', "-Y", ""),
        ('-Z', "-Z", ""),
        ], 
        name='LooK Bone', 
        default={'Z'}, 
        options={'ENUM_FLAG'}
    )
    
    ob_length : FloatProperty(default=0.1, min=0, max=10.0,)
    
    ## HeadTail
    headtail_use_loop : BoolProperty(default=True)
    headtail_use_parent : BoolProperty()
    headtail_use_connected : BoolProperty()
    headtail_use_bbone : BoolProperty(default=True)
    headtail_enum_const : EnumProperty(items=[
        ('FINGERS', "Fingers", ""),
        ('GRIP', "Grip Curve", ""),
        ('CURVE', "Curve", ""),
        ('NONE', "None", ""),
        ], 
        name='', 
        default='NONE', 
    )
    
    ## EYE GENERATOR 
    eye_point_center : PointerProperty(type = bpy.types.Object)
    eye_base_name : StringProperty(default="eye_")
    use_deform_bone : BoolProperty(default=False)
    use_eye_root : BoolProperty()
    use_eye_bbone : BoolProperty()
    use_eye_semetal_bbone : BoolProperty()
    eye_bbone_segments : IntProperty(default=4, min=1, max=32)
    eye_use_loop : BoolProperty(default=True)
    
    #Curve
    curve_bone_name : StringProperty(default="bone")
    curve_use_reference_bone : BoolProperty(default=False)
    curve_reference_bone_name : StringProperty(default="")
    curve_use_control : BoolProperty(default=True)
    
    #BendyBone 
    bendy_bone_invest: BoolProperty(default=False)
    bendybone_type: EnumProperty(items=[
        ('SCALE', "Scale", ""),
        ('ROTATION', "Rotation", ""),
        #('PARENT', "Parent", ""),
        
        ], 
        name='BendyBone Type', 
        default={'ROTATION'}, 
        options={'ENUM_FLAG'}
        )
    
    
    # Node Picker
    #copy propertie
    picker_object_name: bpy.props.StringProperty()
    picker_object_type: bpy.props.StringProperty()
    picker_active_object: bpy.props.StringProperty()
    picker_active_bone: bpy.props.StringProperty()
    picker_active_constraint: bpy.props.StringProperty()
    picker_propertie: bpy.props.StringProperty()
    
    #edit bone
    def set_value(self, context):
        select_bones = self.GetSelectBones(mode="EDIT")
        for bone in select_bones:
            self.AlignBboneToLocalAxis(bone, influence=self.ebone_curve_in_out)
        
        # Reiniciar el valor a 0 después de usarlo
        self["ebone_curve_in_out"] = 0.0  # No dispara el update otra vez

        
    ebone_curve_in_out : FloatProperty(default=0,  update=set_value)
    
    
    
        
    #Annotate_Bone
    annotate_name : StringProperty(default="def-")
    annotate_type_mode: EnumProperty(items=[
        ('MOVE', "Move Active", ""),
        ('ADD', "Add Bone", ""),
        ('REMOVE', "Remove Bone", ""),
        ], 
        name='', 
        default='ADD', 
    )
    
    annotate_use_deform : BoolProperty(default=True)
    annotate_use_vertbone : BoolProperty(default=False)
    annotate_name_vertbone : StringProperty(default="vertex_")
    annotate_use_vertbone_deform : BoolProperty(default=True)

    annotate_segments : IntProperty(default=32, min=1, max=32)
    annotate_use_align_mirror_x: BoolProperty(default=False)
    annotate_use_align_mirror_y: BoolProperty(default=False)
    annotate_use_align_mirror_z: BoolProperty(default=False)
    annotate_use_align_mirror_negative_x: BoolProperty(default=False)
    annotate_use_align_mirror_negative_y: BoolProperty(default=False)
    annotate_use_align_mirror_negative_z: BoolProperty(default=False)
    
    annotate_use_join_bones : BoolProperty(default=True)
    annotate_join_same_name : BoolProperty(default=False)
    annotate_proximity_join : FloatProperty(default=0.01,precision=3)
    
    annotate_global_normal : BoolProperty(default=False)
    annotate_aling_roll_normal : BoolProperty(default=True)
    annotate_size_bbone : FloatProperty(default=0.001,precision=6)
    annotate_auto_bone : BoolProperty(default=False, update= lambda self, context: set_annotate(self, context, "annotate_auto_bone"))
    annotate_use_select_target : BoolProperty(default=False)
    def only_mesh_objects(self, obj) -> bool:
        return obj.type == 'MESH'
    annotate_target : PointerProperty(type=bpy.types.Object, poll=only_mesh_objects)
    annotate_direction: EnumProperty(items=[
        ('X', "X", ""),
        ('Y', "Y", ""),
        ('Z', "Z", ""),
        ('-X', "-X", ""),
        ('-Y', "-Y", ""),
        ('-Z', "-Z", ""),
        ], 
        name='LooK roll Bone', 
        default={'Z'}, 
        options={'ENUM_FLAG'}
    )
    annotate_use_curve : BoolProperty(default=True)
    annotate_curve_power : FloatProperty(default=1,precision=3)
    annotate_use_parent : BoolProperty(default=False)
    annotate_use_connect : BoolProperty(default=False)
    
    #Annotate_Animation
    annotate_posebone : BoolProperty(default=False,  update= lambda self, context: set_annotate(self, context, "annotate_posebone") ) 
    
    #BodyParts
    
      
    bp_enum_props : EnumProperty(
        items=[
            ('ARM_L', "Arm Left", ""),
            ('ARM_R', "Arm Right", ""),
            ('LEG_L', "Leg Left", ""),
            ('LEG_R', "Leg Right", ""),

        ],
        name='Body Parts Driver Take',
        default='ARM_L',
        options={'LIBRARY_EDITABLE'},
    )
    
    bp_body_type : EnumProperty(
        items=[
            ('ARM', "Arm", ""),
            #('LEG', "Arm Right", ""),
            #('TORSO', "Leg Left", ""),
            ('TAIL', "Tail", ""),

        ],
        name='How Body Parts',
        default='ARM',
        options={'LIBRARY_EDITABLE'},
    )
    
    
    bp_use_select_to_deform : BoolProperty(default=True, options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})
    bp_sub_divide_bone_segments : IntProperty( min = 1, max = 32, default = 2)
    bp_bendy_bone_segments : IntProperty( min = 1, max = 32, default = 2)
    bp_use_drive : BoolProperty(default=True, options={'LIBRARY_EDITABLE', 'ANIMATABLE'},override={"LIBRARY_OVERRIDABLE"})

class RGC_ViewSelect_Grups(GeneralArmatureData, bpy.types.PropertyGroup):
    bone : bpy.props.StringProperty()
    
class RGC_PoseBone_GrupsProps(GeneralArmatureData, bpy.types.PropertyGroup):
    view_select : bpy.props.CollectionProperty(type=RGC_ViewSelect_Grups)
    view_select_index : IntProperty(min=0,options={'HIDDEN'},)
    

def change_name(self, context) : 
    self["object"].name = self["name"]

class RGC_Targets_GrupsProps(GeneralArmatureData, bpy.types.PropertyGroup):
    name : StringProperty(default="Target", update=change_name)
    object : PointerProperty(type=bpy.types.Object)
class RGC_Constraint_GrupsProps(GeneralArmatureData, bpy.types.PropertyGroup):
    
    
    targets_grups : bpy.props.CollectionProperty(type=RGC_Targets_GrupsProps)
    targets_grups_index : IntProperty(min=0,options={'HIDDEN'},)
    
    enum_rgc_constraint : EnumProperty(items=[
        ("ATRTIBUTE", "Attribute", ""),
        ("RGC_CONSTRAINT", "RGC Constraint", ""),
    ], name='Type', default='ATRTIBUTE',)

class RGC_List_ConstraintTarget(GeneralArmatureData, bpy.types.UIList):
    
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            
            layout.prop(item, "name", text="")
            
            return
          
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text="", icon=item.icon)

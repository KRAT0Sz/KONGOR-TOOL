import bpy
from ...generaldata import *
from types import SimpleNamespace
import bmesh
from mathutils import Vector



class GeneratorsBones(GeneralArmatureData):


    def GN_Name(self, new_name , bone_name : str) -> str : 
        get_name = bone_name[-4:]
        list_name = (f".{i:003}" for i in range(10000))
        t_name : str = bone_name
        if get_name in list_name:
            t_name = bone_name[:-4]
        return new_name + t_name

    def AddBone(self):
        self.SetMode("EDIT")
        bpy.ops.armature.bone_primitive_add()
        self.SetMode("POSE")
    
    def EditProperty(self):
        bpy.ops.wm.call_panel(name="rgc.call_editaddbone")
    
    def GN_DampedTrackControlParent(self) : 
        self.GN_DTP(use_viewport_display=True)
    
    def GN_DampedTrackParent(self):
        self.GN_DTP(use_viewport_display=False)
    
    def GN_DTP(self, use_viewport_display : bool = False, use_cont : bool =  False) :
        select_bone_name = self.GetNameToBones(self.GetSelectBones(mode="POSE", only_select=True))
        active_bone_name = self.GetNameToBones([self.GetActiveBone()])
        self.AddCollection()
        self.SetMode("EDIT")
        self.UseMirror(False)
        select_bone = self.GetBones(select_bone_name, mode="EDIT")
        active_bone = self.GetBone(active_bone_name[0], mode="EDIT")
        rot_bones = []
        cont_bones = []
        if select_bone:
            for bone in select_bone : 
                parent_bone = bone.parent
                
                rot_bone = self.CreateBonesRange(self.GN_Name("DT_", bone.name), 1)[0]
                rot_bones.append(rot_bone.name)
                if use_cont :
                    cont_bone = self.CreateBonesRange(self.GN_Name("DT_", bone.name), 1)[0]
                    cont_bones.append(cont_bone.name)
                    self.SetTransform(cont_bone, bone, length_value=1.2)
                    self.SetDeform([rot_bone, cont_bone], False)
                    self.SetColorBone(cont_bone, "THEME09")
                    self.SetDisplaySize(cont_bone, bone)
                else :
                    self.SetDeform([rot_bone], False)
                    self.SetColorBone(rot_bone, "THEME09")
                    
                self.SetDisplaySize(rot_bone, bone)
    
                rot_bone.head = bone.head
                rot_bone.tail = active_bone.head
                bone.parent = rot_bone
                rot_bone.parent = parent_bone
                rot_bone.align_roll(self.GetWorldNormal())
        self.UseMirror(True)
        self.SetMode("POSE")
        select_bone = self.GetBones(select_bone_name, mode="POSE")
        active_bone = self.GetBone(active_bone_name[0], mode="POSE")
        rot_bones = self.GetBones(rot_bones, mode="POSE")
        if use_cont : 
            cont_bones = self.GetBones(cont_bones, mode="POSE")
            for i, rbone in enumerate(rot_bones):
                contraint = rbone.constraints.new(type='DAMPED_TRACK')
                contraint.target = self.GetActiveObject()
                contraint.subtarget = active_bone.name
                
                if use_viewport_display :
                    rbone.custom_shape = self.EMPTY_Sphere
                    rbone.custom_shape_scale_xyz = (0.2, 0.2, 0.2)
        else :
        
            for i, rbone in enumerate(rot_bones):
                contraint = rbone.constraints.new(type='DAMPED_TRACK')
                contraint.target = self.GetActiveObject()
                contraint.subtarget = active_bone.name
                
                if use_viewport_display :
                    rbone.custom_shape = self.EMPTY_Sphere
                    rbone.custom_shape_scale_xyz = (0.2, 0.2, 0.2)
  
        
    def GN_AddBoneHead(self) : self.GN_AddBoneHeadAndTail("HEAD")
    def GN_AddBoneTail(self) : self.GN_AddBoneHeadAndTail("TAIL")
    def GN_AddBoneHeadTail(self) : self.GN_AddBoneHeadAndTail("HEAD_TAIL")
    
    def GN_AddBoneHeadAndTail(self, type = "HEAD"):
        self.SetMode("EDIT")
        props = self.Props()
        select_bones = self.GetSelectBones(mode="EDIT")
        if select_bones: 
            for bone in select_bones:

                new_bone = self.CreateBonesRange("Bone", 1)[0]
                if type == "HEAD":
                    new_bone.head = bone.head
                    new_bone.tail = bone.head + self.GetWorldNormal()
                elif type == "TAIL":
                    new_bone.head = bone.tail + self.GetWorldNormal()
                    new_bone.tail = bone.tail
                elif type == "HEAD_TAIL":
                    new_bone.head = bone.head
                    new_bone.tail = bone.tail
                
                if props.use_add_bone_deform:
                    self.SetDeform([new_bone], True)
                
                if props.use_add_bone_parent_to_select:
                    new_bone.parent = bone.parent
                    
                if props.use_add_bone_parent:
                    if not props.use_add_bone_invert_parent:
                        new_bone.parent = bone 
                    else:
                        if props.use_add_bone_parent_to_select:
                            new_bone.parent = bone.parent
                        bone.parent = new_bone
                    new_bone.use_connect = props.use_add_bone_connected
                new_bone.roll = bone.roll
                new_bone.length = bone.length

        else : 
            self.AddBone()

        self.SetMode("POSE")
    def GN_Parent(self, use_connect : bool = False):
        select_bone : list = self.GetNameToBones(self.GetSelectBones(mode="POSE", only_select=True))
        active_bone = self.GetNameToBones([self.GetActiveBone()])
        if not self.GetActiveBone() : return
        self.SetMode(mode="EDIT")
        select_bone = self.GetBones(select_bone, mode="EDIT")
        active_bone= self.GetBone(active_bone[0], mode="EDIT")
        if select_bone and active_bone:
            for bone in select_bone:
                bone.parent = active_bone
                if use_connect:
                    bone.use_connect = True
        self.SetMode(mode="POSE")
    def GN_ParentOffset(self):
        self.GN_Parent()
    def GN_ParentConnected(self):
        self.GN_Parent(use_connect=True) 
    def GN_ParentBendyBone(self):
        
        def SetParent(select_bone, active_bone):
            select_bone : list = self.GetBones(select_bone, mode="POSE")
            active_bone = self.GetBone(active_bone[0], mode="POSE")
            for bone in select_bone:
                for const in bone.parent.constraints:
                    if const.type == "ARMATURE" :
                        constraint = const
                        constraint.targets.new()
                        for i, tgt in enumerate(constraint.targets):
                            if tgt.target is None:
                                constraint.targets[i].target = self.GetActiveObject()
                                constraint.targets[i].subtarget = active_bone.name
                            constraint.targets[i].weight = 1.0 / len(constraint.targets)
            
        def SetNewBone(select_bone, active_bone):
            self.SetMode(mode="EDIT")
            select_bone : list = self.GetBones(select_bone, mode="EDIT")
            active_bone = self.GetBone(active_bone[0], mode="EDIT")
            
            if select_bone :
                names = []
                for bone in select_bone:
                    names.append(f"RGC_PARENT_{bone.name}")
                new_bone = self.CreateBones(names)
                if new_bone :
                    self.SetTransformToBones(new_bone, select_bone, length_value=0.5)
                    for i, bone in enumerate(select_bone):
                        self.SetDisplaySize(new_bone[i], bone)
                        bone.parent = new_bone[i]
                    self.SetDeform(new_bone, False)

            select_bone = self.GetNameToBones(select_bone)
            active_bone = self.GetNameToBones([active_bone])
            new_bone  = self.GetNameToBones(new_bone)
            self.SetMode(mode="POSE")
            select_bone : list = self.GetBones(select_bone, mode="POSE")
            active_bone = self.GetBone(active_bone[0], mode="POSE")
            new_bone = self.GetBones(new_bone, mode="POSE")
            
            if new_bone : 
                for bone in new_bone :
                    constraint = bone.constraints.new(type='ARMATURE')
                    constraint.targets.new()
                    for i, tgt in enumerate(constraint.targets):
                        if tgt.target is None:
                            constraint.targets[i].target = self.GetActiveObject()
                            constraint.targets[i].subtarget = active_bone.name
                            constraint.targets[i].weight = 1.0
        
        parent = []
        new_bone = []
        active_bone = self.GetActiveBone(mode="POSE")
        for bone in self.GetSelectBones(mode="POSE", only_select=True) :
            if bone.name != active_bone.name:
                if bone.parent :
                    if "RGC_PARENT_".lower() in bone.parent.name.lower():
                        parent.append(bone.name)
                    else:
                        new_bone.append(bone.name)
                else:
                    new_bone.append(bone.name)
   
        if parent:
            SetParent(parent[:], [active_bone.name])
        if new_bone:
            SetNewBone(new_bone[:], [active_bone.name])
    
    def GN_ParentActiveBendyBone(self):
        
        def SetParent(select_bone, active_bone):
            select_bone : list = self.GetBones(select_bone, mode="POSE")
            active_bone = self.GetBone(active_bone[0], mode="POSE")
            if new_bone : 
                constraint = new_bone.constraints.new(type='ARMATURE')
                for bone in select_bone:
                    constraint.targets.new()
                    for i, tgt in enumerate(constraint.targets):
                        if tgt.target is None:
                            constraint.targets[i].target = self.GetActiveObject()
                            constraint.targets[i].subtarget = bone.name
                        constraint.targets[i].weight = 1 / len(select_bone)
    
    
        def SetNewBone(select_bone, active_bone):
            self.SetMode(mode="EDIT")
            select_bone : list = self.GetBones(select_bone, mode="EDIT")
            active_bone = self.GetBone(active_bone[0], mode="EDIT")
            
            if active_bone:
                new_bone = self.CreateBonesRange(f"RGC_PARENT_{active_bone.name}", 1)
                self.SetTransform(new_bone[0], active_bone, length_value=0.5)
                self.SetDisplaySize(new_bone[0], active_bone)
                self.SetDeform(new_bone, False)
                active_bone.parent = new_bone[0]
                

            select_bone = self.GetNameToBones(select_bone)
            active_bone = self.GetNameToBones([active_bone])
            new_bone  = self.GetNameToBones(new_bone)
            self.SetMode(mode="POSE")
            select_bone : list = self.GetBones(select_bone, mode="POSE")
            active_bone = self.GetBone(active_bone[0], mode="POSE")
            new_bone = self.GetBone(new_bone[0], mode="POSE")
            
            if new_bone : 
                constraint = new_bone.constraints.new(type='ARMATURE')
                for bone in select_bone:
                    constraint.targets.new()
                    for i, tgt in enumerate(constraint.targets):
                        if tgt.target is None:
                            constraint.targets[i].target = self.GetActiveObject()
                            constraint.targets[i].subtarget = bone.name
                        constraint.targets[i].weight = 1 / len(select_bone)
        
        parent = []
        new_bone = []
        active_bone = self.GetActiveBone(mode="POSE")
        for bone in self.GetSelectBones(mode="POSE") :
            if bone.name != active_bone.name:
                if bone.parent :
                    if "RGC_PARENT_".lower() in bone.parent.name.lower():
                        parent.append(bone.name)
                    else:
                        new_bone.append(bone.name)
                else:
                    new_bone.append(bone.name)
   
        if parent:
            SetParent(parent[:], [active_bone.name])
        if new_bone:
            SetNewBone(new_bone[:], [active_bone.name])
    
    # BodyParts
    
    def GN_Driver(self,cost, prop_name, path) : 
        
        # crear driver
        fcurve = cost.driver_add(prop_name)
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        
        # añadir variable
        var = driver.variables.new()
        var.name = prop_name
        var.targets[0].id_type = 'OBJECT'
        var.targets[0].id = self.GetActiveObject()
        var.targets[0].data_path = path
        
        # expresión
        driver.expression = var.name
            
    def GN_Arms(self):
        
        props = self.Props()
        if len(self.PropsToArmature()) == 0 : 
            self.PropsToArmature().add()
        self.SetMode("EDIT")
        select_bones = self.GetSelectBones("EDIT")
        self.SetDeform(select_bones, False)
        
        if select_bones : 
            
            ROOT = self.CreateBone(f"ROOT-{select_bones[0].name}")
            self.SetTransform(ROOT, select_bones[0], length_value=0.2)
            self.SetColorBone(ROOT)
            select_bones[0].parent = ROOT
            SUBROOT = self.CreateBone(f"SUBROOT-{select_bones[0].name}")
            self.SetTransform(SUBROOT, select_bones[0], length_value=0.2)
            self.SetDeform([ROOT, SUBROOT], False)
            SUBROOT.parent = ROOT
            
            ARM_UP = select_bones[0]
            BONES_UP = self.DuplicateBone(ARM_UP, props.bp_sub_divide_bone_segments)
            for bone in BONES_UP:
                if props.bp_use_select_to_deform :
                    bone.name = "UP-"+bone.name
                    bone.bbone_segments = props.bp_bendy_bone_segments
                    if bone.bbone_segments != 1 :
                        bone.display_type = 'BBONE'
                        size = bone.length / 6
                        bone.bbone_x = size
                        bone.bbone_z = size


            ARM_DOWN = select_bones[1]
            BONES_DOWN = self.DuplicateBone(ARM_DOWN, props.bp_sub_divide_bone_segments)
            for bone in BONES_DOWN:
                bone.name = "DOWN-"+bone.name
                bone.bbone_segments = props.bp_bendy_bone_segments
                if bone.bbone_segments != 1 :
                    bone.display_type = 'BBONE'
                    size = bone.length / 6
                    bone.bbone_x = size
                    bone.bbone_z = size
                
            HANDS = select_bones[-1]
            DEF_HANDS = self.CreateBone(HANDS.name)
            DEF_HANDS.name = "HANDS-"+DEF_HANDS.name
            self.SetTransform(DEF_HANDS, HANDS)

            SUBCONTNORMAL = self.CreateBonesRange(f"CONT-{select_bones[0].name}", 2)
            self.SetTransformToBones(SUBCONTNORMAL, [select_bones[0], select_bones[1]])
            self.SetDeform(SUBCONTNORMAL, False)
            self.SetRelationsOnlyOneList(SUBCONTNORMAL, True)
            
            
        
        select_bones = self.GetNameToBones(select_bones)
        bones_up = self.GetNameToBones(BONES_UP)
        bones_down = self.GetNameToBones(BONES_DOWN)
        hands = self.GetNameToBones([DEF_HANDS])
        root = self.GetNameToBones([ROOT])
        subroot = self.GetNameToBones([SUBROOT])
        subcontnormal = self.GetNameToBones(SUBCONTNORMAL)
        ik = []
        cont_ik = []
        
        self.SelectBones(SUBCONTNORMAL, mode="EDIT")
        props.use_fingers = False
        props.use_fk = False
        props.name_def = "SUBCONT-"
        self.GN_Fingers()
        self.SetMode("EDIT")
        cont_bones = self.GetBonesToRange(f"SUBCONT-{subcontnormal[0][:-4]}",3, mode="EDIT",)
        subselect_bones = self.GetBones(select_bones, mode="EDIT")
        for i, bone in enumerate(cont_bones):
            bone.parent = subselect_bones[i if i < len(select_bones) else -1]
        cont_bone_sub = self.GetNameToBones(cont_bones)
        ## FK
        self.SelectBones(self.GetBones(select_bones, mode="EDIT"))
        self.Props().name_fk1 = "FK-"
        BONES_NAMES = self.GN_Fk(use_return=True)
        
        self.SetMode("EDIT")
        PARENT_FK = self.GetBone(BONES_NAMES[1][0], mode="EDIT")
        if PARENT_FK : PARENT_FK.parent = self.GetBone(root[0], mode="EDIT")
        
        ## IK
        self.SelectBones(self.GetBones(select_bones, mode="EDIT"))
        self.Props().name_ik = "IK-"
        BONES_NAMES = self.GN_Ik(use_return=True)
        ik = BONES_NAMES[1]
        cont_ik = BONES_NAMES[2]
        self.SetMode("EDIT")
        PARENT_IK_1 = self.GetBone(BONES_NAMES[-1][0], mode="EDIT")
        PARENT_IK_2 = self.GetBone(BONES_NAMES[-1][1], mode="EDIT")
        for bone in [PARENT_IK_1, PARENT_IK_2] : 
            if not bone : continue 
            bone.parent = self.GetBone(root[0], mode="EDIT")
        self.SetRelations(self.GetBone(cont_ik[-2], mode="EDIT"), self.GetBone(root[0], mode="EDIT"))
        
        def SetParentDeFBone(bones : list, index : int, set_constraint : bool = True) : 
            self.SetMode("EDIT")
            self.SelectBones(self.GetBones(bones, mode="EDIT"))
            props.use_fingers = False
            props.use_fk = False
            props.name_def = "CONT-"
            props.int_segments = props.bp_bendy_bone_segments

            self.GN_Fingers()
  
            self.SetMode("EDIT")
            if not set_constraint :
                get_parentbone = self.GetBones(select_bones, mode="EDIT")[index]
                name = f"CONT-{bones[0][:-4]}"
                get_bones = self.GetBonesToRange(name, len(bones)+1, mode="EDIT")
                if get_bones and get_parentbone: 
                    for i, bone in enumerate(get_bones):
                        self.SetRelations(bone, get_parentbone)
                    
                

                subcontnormals = self.GetBone(cont_bone_sub[-1], mode="EDIT")
                get_bones[0].parent = subcontnormals
            else :
                subcontnormals = self.GetBones(subcontnormal, mode="EDIT")[index]
                name = f"CONT-{bones[0][:-4]}"
                get_bones = self.GetBonesToRange(name, len(bones)+1, mode="EDIT")
                if get_bones and subcontnormals: 
                    for bone in get_bones:
                        self.SetRelations(bone, subcontnormals)
            
                bone = self.GetBone(bones[-1], mode="EDIT")
                bone.bbone_handle_type_end = 'TANGENT'
                bone.bbone_custom_handle_end = get_bones[-1]
            
            self.SetMode("POSE")
            if not set_constraint : return
            #root_pose = self.GetBone(root[0], mode="POSE")
            get_bones = self.GetBonesToRange(name, len(bones)+1, mode="POSE")
            if get_bones :
                for bone in get_bones :
                    const = bone.constraints.new(type='COPY_SCALE')
                    const.target = self.GetActiveObject()
                    const.subtarget = root[0]
            
            
            get_bones.reverse()
            n = len(get_bones)
            if index == 0 :
                for i, bone in enumerate(get_bones) :
                    const = bone.constraints.new(type='COPY_ROTATION')
                    const.target = self.GetActiveObject()
                    const.subtarget = subroot[0]
                    if n > 1:
                        t = i / (n - 1)   # va de 0 a 1
                        ease_out = 1 - (t ** 0.5)  # curva ease out
                        const.influence = ease_out
                    else:
                        const.influence = 1.0
            if index == 1 :
                for i, bone in enumerate(get_bones) :
                    const = bone.constraints.new(type='COPY_ROTATION')
                    const.target = self.GetActiveObject()
                    const.subtarget = select_bones[-1]
                    if n > 1:
                        t = i / (n - 1)   # va de 0 a 1
                        ease_out = 1 - (t ** 0.5)  # curva ease out
                        const.influence = ease_out
                    else:
                        const.influence = 1.0
                    const.target_space = 'LOCAL_OWNER_ORIENT'
                    const.owner_space = 'LOCAL'
                    const.use_x = False
                    const.use_z = False

                    
                        

        SetParentDeFBone(bones_up, 0)
        SetParentDeFBone(bones_down, 1)
        SetParentDeFBone(hands, 2, False)
                
        self.SetMode("POSE")
        
        def GetPropsPath() -> list :
            path = "RGC_Armature_GrupsProps[0]"
            paths = {}
            if props.bp_enum_props == "ARM_L":
                paths["fkik"] = (f"{path}.arm_ik_fk_L")
                paths["stretch"] = (f"{path}.arm_stretch_to_R")
                paths["rot"] = (f"{path}.arm_rot_R")
                paths["pole"] = (f"{path}.arm_pole_followed_L")
            elif props.bp_enum_props == "ARM_R":
                paths["fkik"] = (f"{path}.arm_ik_fk_R")
                paths["stretch"] = (f"{path}.arm_stretch_to_L")
                paths["rot"] = (f"{path}.arm_rot_L")
                paths["pole"] = (f"{path}.arm_pole_followed_R")
            elif props.bp_enum_props == "LEG_L":
                paths["fkik"] = (f"{path}.leg_ik_fk_L")
                paths["stretch"] = (f"{path}.leg_stretch_to_L")
                paths["rot"] = (f"{path}.leg_rot_L")
                paths["pole"] = (f"{path}.leg_pole_followed_L")
            elif props.bp_enum_props == "LEG_R":
                paths["fkik"] = (f"{path}.leg_ik_fk_L")
                paths["stretch"] = (f"{path}.leg_stretch_to_R")
                paths["rot"] = (f"{path}.leg_rot_R")
                paths["pole"] = (f"{path}.leg_pole_followed_L")
            return paths
        
        
        rot_bones = self.GetBones(select_bones, mode="POSE")
        for bone in rot_bones :
            c = bone.constraints[-1]
            if props.bp_use_drive :
                if props.bp_use_drive : self.GN_Driver(c,"influence", GetPropsPath()["fkik"])
        iks = self.GetBones(ik, mode="POSE")
        if iks[1] :
            bone = iks[1]
            c = bone.constraints[-1]
            if c : 
                if props.bp_use_drive :self.GN_Driver(c,"influence", GetPropsPath()["rot"])
                if props.bp_use_drive :self.GN_Driver(c,"use_stretch", GetPropsPath()["stretch"])
            new_c = bone.constraints.new(type='IK')
            new_c.target = self.GetActiveObject()
            new_c.subtarget = c.subtarget
            new_c.pole_target = None
            new_c.pole_subtarget = ""
            if new_c : 
                if props.bp_use_drive : self.GN_Driver(new_c,"use_stretch", GetPropsPath()["stretch"])
                
        cont_iks = self.GetBones(cont_ik, mode="POSE")
        bone = cont_iks[1]
        if bone :
            c = bone.constraints.new(type='STRETCH_TO')
            c.target = self.GetActiveObject()
            c.subtarget = cont_iks[-2].name
            c.bulge = 0
            if props.bp_use_drive : self.GN_Driver(c,"influence", GetPropsPath()["pole"])
            
        bone = cont_iks[-1]
        if bone :
            const = bone.constraints.new(type='COPY_SCALE')
            const.target = self.GetActiveObject()
            const.subtarget = root[0]
            
        root = self.GetBone(root[0], mode="POSE")
        if root :
            root.custom_shape = self.EMPTY_Cube
            root.custom_shape_scale_xyz = (3, 3, 3)
        subroot = self.GetBone(subroot[0], mode="POSE")
        if subroot :
            c = subroot.constraints.new(type='DAMPED_TRACK')
            c.target = self.GetActiveObject()
            c.subtarget = cont_bone_sub[1]
            
    def GN_Legs(self):...
    
    def GN_Torso(self):...
    
    def GN_Tail(self):
        props = self.Props()
        if len(self.PropsToArmature()) == 0 : 
            self.PropsToArmature().add()
        self.SetMode("EDIT")
        select_bones = self.GetSelectBones("EDIT")
        self.SetDeform(select_bones, False)
        
        def_bone_name = []
        root_name = ""
        if select_bones : 
            ROOT = self.CreateBone(f"root_{select_bones[0].name}")
            self.SetTransform(ROOT, select_bones[0], length_value=0.2)
            self.SetColorBone(ROOT)
            root_name = ROOT.name
            for bone in select_bones:
                DEFBONE = self.DuplicateBone(bone, props.bp_sub_divide_bone_segments)
                self.SetRelationsOnlyOneList(DEFBONE, True)
                def_bone_name.append(self.GetNameToBones(DEFBONE))
            
        select_bones_bane = self.GetNameToBones(select_bones)
        root_fk_name = ""
        fks_name = []
        ## FK
        self.SelectBones(self.GetBones(select_bones, mode="EDIT"))
        self.Props().name_fk1 = "fk-"
        BONES_NAMES = self.GN_Fk(use_return=True)
        fks_name = BONES_NAMES
        self.SetMode("EDIT")
        ROOT_FK = self.CreateBone(self.GN_Name("root_", BONES_NAMES[0]))
        if ROOT_FK : 
            self.SetTransform(ROOT_FK, ROOT, length_value=0.2)
            ROOT.parent = self.GetBone(root_name, mode="EDIT")
            self.SetDeform([ROOT_FK], False)
            self.SetColorBone(ROOT_FK, "THEME02")
            root_fk_name = ROOT_FK.name
            self.GetBone(BONES_NAMES[1][0], mode="EDIT").parent = ROOT_FK
        self.SetMode("POSE")
        FK = self.GetBones(fks_name, mode="POSE")
        ROOT_FK = self.GetBone(root_fk_name, mode="POSE")
        if ROOT_FK and FK :
            ROOT_FK.custom_shape = self.EMPTY_Circle
            ROOT_FK.custom_shape_transform = bpy.data.objects["Armature"].pose.bones["Bone"]

        
    def GN_UnionBone(self):
        select_bone = self.GetSelectBones(mode="POSE")
        name_select_bone = self.GetNameToBones(select_bone)
        self.SetMode("EDIT")
        select_bone = self.GetBones(name_select_bone, mode="EDIT")
        root = self.CreateBones([f"Root_{name_select_bone[0]}"])
        
        if root : 
            head = self.CreateVector(0,0,0)
            length = 0
            for bone in select_bone:
                bone.parent = root[0]
                head += bone.head
                length += bone.length
            head /= len(select_bone)
            length /= len(select_bone)
            root[0].head = head
            root[0].tail = head + self.GetWorldNormal()
            root[0].length = length * 1.5
            root[0].color.palette = select_bone[0].color.palette

            self.SetDisplaySize(root[0], select_bone[0])
            
        name_select_bone = self.GetNameToBones(select_bone)
        name_root = self.GetNameToBones(root)
        self.SetMode("POSE")
        pose_select_bone = self.GetBones(name_select_bone, mode="POSE")
        pose_root = self.GetBones(name_root, mode="POSE")
        if pose_select_bone :
            pose_root[0].custom_shape = pose_select_bone[0].custom_shape
            pose_root[0].custom_shape_scale_xyz = pose_select_bone[0].custom_shape_scale_xyz
            pose_root[0].custom_shape_translation = pose_select_bone[0].custom_shape_translation
            pose_root[0].custom_shape_rotation_euler = pose_select_bone[0].custom_shape_rotation_euler

    def GN_UnionActiveBone(self):
        
        select_bone = self.GetNameToBones(self.GetSelectBones(mode="POSE"))
        active_bone = self.GetNameToBones([self.GetActiveBone()])
        
        self.SetMode(mode="EDIT") 
        select_bone = self.GetBones(select_bone, mode="EDIT")
        active_bone = self.GetBone(active_bone[0], mode="EDIT")
        if select_bone and active_bone:
            for bone in select_bone :
                bone.parent = active_bone
        self.SetMode("POSE")
    
    def AddCollection(self):
        return super().AddCollection()

    def GN_Fisicas(self) : 

        props = self.Props()
 
        if self.GetObjMode() == {"OBJECT", "EDIT"} : return
        
        selects = self.SplitBonesForParent(self.GetSelectBones(mode=self.GetObjMode())).copy()
        
        
        for PB in selects:
            
            
            PBN = self.GetNameToBones(PB)
            
            self.SetMode(mode="EDIT")
            self.UseMirror(use=False)

            select_edit_bones = self.GetBones(PBN, self.GetObjMode()) 
            if not select_edit_bones : return
            
            Names_Bones = [f"FS_{bone.name}" for bone in select_edit_bones]
            Names_Bones.append(f"FS_{select_edit_bones[-1].name}")

            FBones = self.CreateBones(Names_Bones)
            
            if FBones :
                for i in range(len(select_edit_bones)) : 
                    self.SetTransform(FBones[i], select_edit_bones[i])
                
                self.SetTransform(FBones[-1], select_edit_bones[-1], only_tail=True)
                
                for bone in FBones:
                    bone.use_deform = False
                
                FBones[0].parent = select_edit_bones[0].parent
                
                for i in range(len(FBones)-1):
                    FBones[i+1].parent = FBones[i]
                    FBones[i+1].use_connect = True
            
            FBones_Name = self.GetNameToBones(FBones)
            select_edit_bones_Name = self.GetNameToBones(select_edit_bones)
            self.SetMode(mode="POSE")
            FBones_Pose = self.GetBones(FBones_Name, self.GetObjMode())
            Selecte_Bones_Pose = self.GetBones(select_edit_bones_Name, self.GetObjMode())
            obj = self.GetActiveObject()
            
            if FBones_Pose:
                
                save_frame = bpy.context.scene.frame_current
                bpy.context.scene.frame_set(1)
                
                for i, bone in enumerate(FBones_Pose) : 
                    if i < len(FBones_Pose)-1:
                        constraint = bone.constraints.new(type='COPY_TRANSFORMS')
                        constraint.name = "RIG_CREATOR_FISICAS"
                        constraint.target = self.GetActiveObject()
                        constraint.subtarget = Selecte_Bones_Pose[i].name
                        bone.select = True

                bpy.ops.nla.bake(
                    frame_start=props.frame_start, 
                    frame_end=props.frame_end,
                    step=props.frame_step, 
                    only_selected=True, 
                    visual_keying=True, 
                    clear_constraints=False, 
                    clear_parents=False, 
                    use_current_action=True, 
                    clean_curves=False, 
                    bake_types={'POSE'},
                    channel_types={'LOCATION', 'ROTATION', 'SCALE'}
                )
                
                for bone in FBones_Pose:
                    bone.select = True
                    for constraint in bone.constraints:
                        if constraint.type == 'COPY_TRANSFORMS':
                            if constraint.name == "RIG_CREATOR_FISICAS":
                                bone.constraints.remove(constraint)
                                
                
                for i in range(len(Selecte_Bones_Pose)):
                    
                    if not props.use_stretch_to :
                        constraint = FBones_Pose[i].constraints.new(type='DAMPED_TRACK')
                        constraint.target = self.GetActiveObject()
                        constraint.subtarget = FBones_Pose[i+1].name
                        constraint.influence = props.power_overlapping
                    else:
                        constraint = FBones_Pose[i].constraints.new(type='STRETCH_TO')
                        constraint.target = self.GetActiveObject()
                        constraint.subtarget = FBones_Pose[i+1].name
                        constraint.bulge = props.power_stretch
                        constraint.influence = props.power_overlapping
                        
                for i in range(len(Selecte_Bones_Pose)):
                    constraint = Selecte_Bones_Pose[i].constraints.new(type='COPY_TRANSFORMS')
                    constraint.name = "RIG_CREATOR_FISICAS"
                    constraint.target = self.GetActiveObject()
                    constraint.subtarget = FBones_Pose[i].name
                    Selecte_Bones_Pose[i].select = True
                    
                bpy.ops.nla.bake(
                    frame_start=props.frame_start, 
                    frame_end=props.frame_end,
                    step=props.frame_step, 
                    only_selected=True, 
                    visual_keying=True, 
                    clear_constraints=False, 
                    clear_parents=False, 
                    use_current_action=True, 
                    clean_curves=False, 
                    bake_types={'POSE'},
                    channel_types={'LOCATION', 'ROTATION', 'SCALE'}
                )
                
                for bone in Selecte_Bones_Pose:
                    bone.select = True
                    for constraint in bone.constraints:
                        if constraint.type == 'COPY_TRANSFORMS':
                            if constraint.name == "RIG_CREATOR_FISICAS":
                                bone.constraints.remove(constraint)
                    
                for bone in FBones_Pose:
                    for i in range(props.frame_start, props.frame_end+1, props.frame_step):
                        bone.keyframe_delete(data_path="location", frame=i)
                        if bone.rotation_mode != 'QUATERNION' :
                            bone.keyframe_delete(data_path="rotation_euler", frame=i)
                        else:
                            bone.keyframe_delete(data_path="rotation_quaternion", frame=i)
                            
                        bone.keyframe_delete(data_path="scale", frame=i)
                    
                    self.UpdateViewLayer()
                    
                FBones_Pose_Name = self.GetNameToBones(FBones_Pose)
                self.SetMode("EDIT")
                self.RemoveBones(FBones_Pose_Name)
                self.SetMode("POSE")
                bpy.context.scene.frame_set(save_frame)

    def SubdivideBones(self, select_bones : list[object]) -> list[object]:
        """
        Subdivide the bones in the list of select_bones.
        Returns a list of new bones created.
        """
        
        props = self.Props()
        if props.use_sub_divide_bones : 
            for bone in select_bones :
                new_bones = self.CreateBonesRange(
                    bone.name, props.sub_divide_bone_segments-1
                )
                head_base = bone.head
                tail_base = bone.tail
                roll_base = bone.roll
                bone.length /= len(new_bones)
                fist_head = bone.head
                
                for i, new_bone in enumerate(new_bones) :
                    
                    pass
        
    def GN_Fingers(self) : 
        
        self.AddCollection()
        
        props = self.Props()
        
        use_fk = props.use_fk
        use_def = props.use_def
        use_dedos = props.use_fingers
        use_Segments = props.use_segments
        use_Parent = props.use_parent

        if use_fk == False:
            use_dedos = False

        Armature = self.GetActiveObject()
        self.SetMode(mode="EDIT")
        self.UseMirror(use=False)
        selected_bones = self.GetSelectBones(mode="EDIT")

        to_select_bone_parent = selected_bones[0].parent

        if use_def == True:
            CONTROL = self.GN_Name(props.name_def, selected_bones[0].name)
        if use_fk == True: 
            FK = self.GN_Name(props.name_fk, selected_bones[0].name)
        if use_dedos == True:
            DEDOS = self.GN_Name(props.name_fingers, selected_bones[0].name)

        if not Armature and not Armature.type == 'ARMATURE' and not selected_bones : return

        NEWBONECANTIDA : int = len(selected_bones)
        DEDOSBONES = []
        FKBONE = []
        DEFBONE = []
        
        if use_Segments :
            for bone in selected_bones:
                bone.bbone_segments = props.int_segments
        
        
        # Set Dedos
        if use_dedos :
            DEDOSBONES = self.CreateBonesRange(DEDOS, 2)
            if DEDOSBONES :
                for bone in DEDOSBONES:
                    self.SetTransform(bone, selected_bones[0], length_value=0.5)
                    self.SetDisplaySize(bone, selected_bones[0], Display_size_x=1.2, Display_size_y=1.2)

                L : float = 0
                for bone in selected_bones: L += bone.length
                DEDOSBONES[-1].length = L
                DEDOSBONES[-1].parent = DEDOSBONES[0]
                if use_Parent : 
                    DEDOSBONES[0].parent = to_select_bone_parent
                    selected_bones[0].parent = DEDOSBONES[0]
                
                DEDOSBONES[0].color.palette = 'THEME01'
                DEDOSBONES[1].color.palette = 'THEME04'
            self.SetDeform(DEDOSBONES, False)
                
        # Set Fk
        if use_fk :
            FKBONE = self.CreateBonesRange(FK,NEWBONECANTIDA)
            if FKBONE :
                for i in range(NEWBONECANTIDA):
                    self.SetTransform(FKBONE[i], selected_bones[i])
                    self.SetDisplaySize(FKBONE[i], selected_bones[i])

                self.SetRelationsOnlyOneList(FKBONE, Use_connect=True)    
          
                for bone in FKBONE : 
                    bone.use_deform = False
                    bone.color.palette = 'THEME03'
                    if use_Segments : bone= 32
                    
                if use_Parent and not use_dedos :
                    FKBONE[0].parent = to_select_bone_parent
                else:
                    FKBONE[0].use_connect = False
                    FKBONE[0].parent = DEDOSBONES[-1]
        # Set Def
        if use_def :
            DEFBONE = self.CreateBonesRange(CONTROL, NEWBONECANTIDA+1)
            if DEFBONE :
                for i in range(NEWBONECANTIDA):
                    self.SetTransform(
                        DEFBONE[i], selected_bones[i], 
                        length_value=0.2
                    )
                    self.SetDisplaySize(DEFBONE[i], selected_bones[i], Display_size_x=0.8, Display_size_y=0.8)
                
                self.SetTransform(
                    DEFBONE[-1], selected_bones[-1], 
                    only_tail=True, length_value=0.2
                )
                self.SetDisplaySize(DEFBONE[-1], selected_bones[-1], Display_size_x=0.8, Display_size_y=0.8)
                
                for bone in DEFBONE:
                    bone.use_deform = False
                    self.SetColorBone(bone, 'THEME09')
                    
                if use_Parent and use_fk == False:
                    DEFBONE[0].parent = to_select_bone_parent
                    selected_bones[0].parent = DEFBONE[0]
                else:
                    for i, bone in enumerate(DEFBONE):
                        bone.parent = FKBONE[self.NIndexList(i, FKBONE)]
                    selected_bones[0].parent = DEFBONE[0]
                    DEFBONE[-1].parent = FKBONE[-1]
        
        SELECTBONES_NAME = self.GetNameToBones(selected_bones)
        DEDOSBONES_NAME = self.GetNameToBones(DEDOSBONES)  
        FKBONE_NAME = self.GetNameToBones(FKBONE)
        DEFBONE_NAME = self.GetNameToBones(DEFBONE)
        self.SetMode("POSE")
        DEDOSBONES_POSE = self.GetBones(DEDOSBONES_NAME, "POSE")
        FKBONE_POSE = self.GetBones(FKBONE_NAME, "POSE")
        DEFBONE_POSE = self.GetBones(DEFBONE_NAME, "POSE")
        SELECTBONES_POSE = self.GetBones(SELECTBONES_NAME, "POSE")
        
        if DEDOSBONES_POSE :
            for i in range(3):
                if i in {0, 2}:
                    DEDOSBONES_POSE[-1].lock_scale[i] = True
            DEDOSBONES_POSE[0].custom_shape = self.EMPTY_Cube
            DEDOSBONES_POSE[-1].custom_shape = self.EMPTY_Arrow
            DEDOSBONES_POSE[-1].custom_shape_rotation_euler[0] = -1.5708
            DEDOSBONES_POSE[-1].custom_shape_scale_xyz[1] = 0
            DEDOSBONES_POSE[-1].custom_shape_scale_xyz[0] = 4

        if FKBONE_POSE :
            
            def set_transforms_bone(bone, target_bone):
                const = bone.constraints.new(type='TRANSFORM')
                const.target = Armature
                const.subtarget = target_bone.name
                const.target_space = 'LOCAL'
                const.owner_space = 'LOCAL'
                const.map_from = 'SCALE'
                const.from_min_y_scale = 0.2
                const.from_max_y_scale = 1.8
                const.map_to = 'ROTATION'
                const.map_to_x_from = 'Y'
                const.to_min_x_rot = 3.141592653589793
                const.to_max_x_rot = -3.141592653589793
            
                 
            for bone in FKBONE_POSE:
                
                bone.custom_shape = self.EMPTY_Circle
                bone.custom_shape_translation[1] = bone.length/2
                    
                if use_dedos :

                    if props.use_limit_rot_fingers == False: 
                        set_transforms_bone(bone, DEDOSBONES_POSE[-1])
            
            if props.use_limit_rot_fingers : 
                value = props.limit_rot_fingers
                value = value if value <= len(FKBONE_POSE) else len(FKBONE_POSE)
                list_bones = FKBONE_POSE
                if props.limit_rot_fingers_invert : list_bones.reverse()
                for i in range(value) : 
                    set_transforms_bone(list_bones[i], DEDOSBONES_POSE[-1])
            
            if use_dedos :
                for bone in FKBONE_POSE:       
                    const = bone.constraints.new(type='COPY_SCALE')
                    const.target = Armature
                    const.subtarget = DEDOSBONES_POSE[0].name

        if DEFBONE_POSE :
            for bone in DEFBONE_POSE:
                bone.custom_shape = self.EMPTY_Sphere

        if SELECTBONES_POSE :
            for i, bone in enumerate(SELECTBONES_POSE):

                const = bone.constraints.new(type='COPY_TRANSFORMS')
                const.target = Armature
                const.subtarget = DEFBONE_POSE[i].name
                
                const = bone.constraints.new(type='STRETCH_TO')
                const.target = Armature
                const.subtarget = DEFBONE_POSE[i+1].name
                
    def GN_Ik(self, use_return = False) : 
        
        self.AddCollection()
        if not self.GetActiveObject() : return
        props = self.Props()
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        Select_Bone = self.GetSelectBones("EDIT")
        if not Select_Bone : return
        
        NSB =  len(Select_Bone)
        
        if NSB == 1 : return
        
        IK_NAME = self.GN_Name(props.name_ik, Select_Bone[0].name)
        IK = self.CreateBonesRange(IK_NAME, NSB if NSB > 2 else 3)
        if NSB == 2 : 
            for i in range(NSB):
                self.SetTransform(IK[i], Select_Bone[i])
            self.SetTransform(IK[-1], Select_Bone[-1], only_tail=True)
        else:
            self.SetTransformToBones(IK, Select_Bone)
        self.SetRelationsOnlyOneList(IK, Use_connect=True)
        self.SetDeform(IK, False)
        self.SetColorBone(IK[0], "THEME04")
        
        CONTROL_IK = self.CreateBonesRange(f"cont_{IK_NAME}", 4)
        self.SetDeform(CONTROL_IK, False)
        
        self.SetTransform(CONTROL_IK[0], Select_Bone[0], length_value=0.8)
        self.SetTransform(CONTROL_IK[1], Select_Bone[0], length_value=0.4)
        DSB = [Select_Bone[-1].head, Select_Bone[-1].roll, Select_Bone[0].length * 0.4]
        [CONTROL_IK[0].tail, CONTROL_IK[0].roll, CONTROL_IK[0].length] = DSB
        [CONTROL_IK[1].tail, CONTROL_IK[1].roll, CONTROL_IK[1].length] = DSB
        
        self.SetTransform(CONTROL_IK[2], IK[-1], length_value=0.5)
        Save_List = Select_Bone[:]
        Save_List.pop()
        self.SetPoleTransform(CONTROL_IK[3], Save_List if NSB > 2 else Select_Bone , props.distance_pole_target)
        CONTROL_IK[3].length /= 2
        
        self.SetColorBone(CONTROL_IK[0])
        self.SetColorBone(CONTROL_IK[2])
        self.SetColorBone(CONTROL_IK[3], 'THEME04')
        
        self.SetRelations(CONTROL_IK[-1], CONTROL_IK[1])
        self.SetRelations(IK[0], CONTROL_IK[0])
        

        SELECT_BONE_NAME = self.GetNameToBones(Select_Bone)  
        IK_NAME = self.GetNameToBones(IK)
        CONTROL_IK_NAME = self.GetNameToBones(CONTROL_IK)
        self.SetMode("POSE")
        SELECT_BONE_POSE = self.GetBones(SELECT_BONE_NAME, "POSE")
        IK_POSE = self.GetBones(IK_NAME, "POSE")
        CONTROL_IK_POSE= self.GetBones(CONTROL_IK_NAME, "POSE")
                
        if IK_POSE and CONTROL_IK_POSE :

            IK_POSE[0].custom_shape = self.EMPTY_Cube
            IK_POSE[0].rotation_mode = 'XYZ'
            IK_POSE[0].lock_rotation[2] = True
            IK_POSE[0].lock_rotation[0] = True
            IK_POSE[0].custom_shape_scale_xyz[0] = 0.5
            IK_POSE[0].custom_shape_scale_xyz[1] = 0
            IK_POSE[0].custom_shape_scale_xyz[2] = 0.5
            IK_POSE[0].custom_shape_translation[1] = IK_POSE[0].length
            
            for bone in IK_POSE : 
                bone.ik_stretch = 0.1
            
            CONTROL_IK_POSE[0].custom_shape = self.EMPTY_Cube
            CONTROL_IK_POSE[2].custom_shape = self.EMPTY_Cube
            CONTROL_IK_POSE[2].custom_shape_translation[1] = CONTROL_IK_POSE[2].length
            
            CONTROL_IK_POSE[3].custom_shape = self.EMPTY_Sphere
            for i in range(3) :
                CONTROL_IK_POSE[3].custom_shape_scale_xyz[i] /= 2
            
            const = IK_POSE[-1].constraints.new(type='COPY_TRANSFORMS')
            const.target = self.GetActiveObject()
            const.subtarget = CONTROL_IK_POSE[2].name

            const = IK_POSE[-2].constraints.new(type='IK')
            const.target = self.GetActiveObject()
            const.subtarget = CONTROL_IK_POSE[2].name
            const.chain_count = len(SELECT_BONE_POSE)-1 if NSB > 2 else len(SELECT_BONE_POSE)
            
            if props.use_ik_as == "POLE" : 
                const.pole_target = self.GetActiveObject()
                const.pole_subtarget = CONTROL_IK_POSE[-1].name
                const.pole_angle = props.pole_angle
            
            #elif props.use_ik_as == "AllROT" : 
            #    const.use_rotation = True

            const.use_stretch = props.use_stretch_to_ik
            
            if props.use_copy_transforms_ik : 
                for i in range(len(SELECT_BONE_POSE)):
                    const = SELECT_BONE_POSE[i].constraints.new(type='COPY_TRANSFORMS')
                    const.target = self.GetActiveObject()
                    const.subtarget = IK_POSE[i].name
                            

        if use_return : 
            
            return [SELECT_BONE_NAME, IK_NAME, CONTROL_IK_NAME]
        
    def GN_Fk(self, use_return = False) : 
        
        self.AddCollection()
        if not self.GetActiveObject() : return
        props = self.Props()
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        Select_Bone = self.GetSelectBones("EDIT")
        if not Select_Bone : return
        
        props = self.Props()
        
        FK = self.CreateBonesRange(self.GN_Name(props.name_fk1, Select_Bone[0].name), len(Select_Bone))
        if FK : 
            self.SetTransformToBones(FK, Select_Bone)
            self.SetRelationsOnlyOneList(FK, Use_connect=True)
            self.SetDeform(FK, False)
            for fk in FK : 
                self.SetColorBone(fk, "THEME03")
            
            for i, fk in enumerate(FK) : 
                self.SetDisplaySize(fk, Select_Bone[i])
            
        
        SELECT_BONE_NAME = self.GetNameToBones(Select_Bone)
        FK_NAME = self.GetNameToBones(FK)
        self.SetMode("POSE")
        SELECT_BONE_POSE = self.GetBones(SELECT_BONE_NAME, "POSE")
        FK_POSE = self.GetBones(FK_NAME, "POSE")
        
        if FK_POSE :
            for i, fk in enumerate(FK_POSE) :
                if props.use_copy_transforms_fk :
                    const = SELECT_BONE_POSE[i].constraints.new(type='COPY_TRANSFORMS')
                    const.target = self.GetActiveObject()
                    const.subtarget = fk.name
                
                if props.use_view_object : 
                    fk.custom_shape = self.EMPTY_Circle
                    fk.custom_shape_translation[1] = fk.length/2
        if use_return : return [SELECT_BONE_NAME, FK_NAME]  
             
    def GN_Bones(self) : 
        self.AddCollection()
        if not self.GetActiveObject() : return
        props = self.Props()
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        Select_Bone = self.GetSelectBones("EDIT")
        if not Select_Bone : return
        
        props = self.Props()
        
        BONE = self.CreateBonesRange(
            self.GN_Name(props.name_bone, Select_Bone[0].name), 
            len(Select_Bone)+1 if props.use_bone_in_tail else len(Select_Bone)
        )
        self.SetDeform(BONE, False)
        for bone in BONE :
            self.SetColorBone(bone, "THEME09")
            self.SetDisplaySize(bone, Select_Bone[0])
        
        
        look_bone = str(props.look_bone).lower().replace("{", "").replace("}", "").replace("'", "")
        
        if props.add_orientation == "GLOBAL" : 
            for i in range(len(Select_Bone)) : 
                bone = BONE[i]
                bone.head = Select_Bone[i].head
                bone.tail = Select_Bone[i].head + self.GetWorldNormal(Eje=look_bone)
                world_normal = self.GetWorldNormal(Eje=look_bone)
                print(f"GetWorldNormal result for {look_bone}: {world_normal}")
                bone.roll = 0 
                bone.length = Select_Bone[i].length
                
            if props.use_bone_in_tail :
                bone = BONE[-1]
                bone.head = Select_Bone[-1].tail
                bone.tail = Select_Bone[-1].tail + self.GetWorldNormal(Eje=look_bone)
                bone.roll = 0
                bone.length = Select_Bone[-1].length
        
        elif props.add_orientation == "NORMAL" :
            
            def get_axis(bone, look_bone) :
                axis = None
                if look_bone in {"x", "y", "z"} :
                   axis = getattr(bone, f"{look_bone}_axis") 
                else :
                    name = f"{look_bone}_axis".replace("-", "")
                    axis = getattr(bone, f"{name}")*-1
                    print(axis)
                return axis
            
            for i in range(len(Select_Bone)) : 
                bone = BONE[i]
                bone.head = Select_Bone[i].head
                
                bone.tail = Select_Bone[i].head + get_axis(Select_Bone[i], look_bone)
                bone.roll = 0
                bone.length = Select_Bone[i].length
                
            if i == len(Select_Bone)-1 and props.use_bone_in_tail :
                bone = BONE[-1]
                bone.head = Select_Bone[-1].tail
                bone.tail = Select_Bone[-1].tail + get_axis(Select_Bone[-1], look_bone)
                bone.roll = 0
                bone.length = Select_Bone[-1].length
        
        if props.use_parent_bone :
            for i in range(len(Select_Bone)) : 
                Select_Bone[i].parent = BONE[i]
        
        NAME_SELECT = self.GetNameToBones(Select_Bone)
        NAME_BONE = self.GetNameToBones(BONE)
        self.SetMode("POSE")
        SELECT_BONE_POSE = self.GetBones(NAME_SELECT, "POSE")
        BONE_POSE = self.GetBones(NAME_BONE, "POSE")
        
        if BONE_POSE :
            
            list_empty = {
                "SINGLE_ARROW": self.EMPTY_Arrow,
                "CIRCLE": self.EMPTY_Circle,
                "CUBE": self.EMPTY_Cube,
                "SPHERE": self.EMPTY_Sphere,
            }
            if props.use_viewport_display :
                for bone in BONE_POSE : 
                    bone.custom_shape = list_empty[props.viewport_display_type]
                    if props.viewport_display_type == "SINGLE_ARROW" :
                        bone.custom_shape_rotation_euler[0] = -1.5708
            
            if props.use_stretch_to_bone :
                for i in range(len(SELECT_BONE_POSE)) :
                    const = SELECT_BONE_POSE[i].constraints.new(type='STRETCH_TO')
                    const.target = self.GetActiveObject()
                    const.subtarget = BONE_POSE[i+1].name
               
    def GN_Curve(self) : 
    
        self.AddCollection()
        if not self.GetActiveObject() : return
        props = self.Props()
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        Select_Bone = self.GetSelectBones("EDIT")
        if not Select_Bone : return

        if props.use_curve_root :
            ROOT_BONE_CURVE = self.CreateBonesRange(self.GN_Name(props.name_curve_root, Select_Bone[0].name), 1)
            self.SetDeform(ROOT_BONE_CURVE, False)
            self.SetColorBone(ROOT_BONE_CURVE[0], "THEME01")
            self.SetTransform(ROOT_BONE_CURVE[0], Select_Bone[0])
            self.SetDisplaySize(ROOT_BONE_CURVE[0], Select_Bone[0])
            
        CURVE_CONT = self.CreateBonesRange(self.GN_Name(props.name_curve_cont, Select_Bone[0].name), len(Select_Bone)+1)
        self.SetDeform(CURVE_CONT, False)
        for i, bone in enumerate(CURVE_CONT) :
            self.SetColorBone(bone, "THEME04")
            self.SetDisplaySize(bone, Select_Bone[0])
            if i < len(Select_Bone) :
                self.SetTransform(bone, Select_Bone[i], length_value=0.5)
            else:
                self.SetTransform(bone, Select_Bone[-1], length_value=0.5, only_tail=True)

            if props.use_curve_root :
                bone.parent = ROOT_BONE_CURVE[0]
                
        CURVE_FREE = self.CreateBonesRange(self.GN_Name(props.name_curve_free, Select_Bone[0].name), len(Select_Bone)*2)
        self.SetDeform(CURVE_FREE, False)
        for i, bone in enumerate(CURVE_FREE) :
            self.SetColorBone(bone, "THEME03")
            self.SetDisplaySize(bone, Select_Bone[0])
            if i < len(Select_Bone) :
                self.SetTransform(bone, Select_Bone[i], length_value=0.5)
                bone.parent = CURVE_CONT[i]
            else:
                self.SetTransform(bone, Select_Bone[i-len(Select_Bone)], length_value=0.5, only_tail=True)
                bone.parent = CURVE_CONT[i-len(Select_Bone)+1]
            
        for i, bone in enumerate(Select_Bone) :
            bone.use_connect = False
            bone.parent = CURVE_CONT[i]
        
        LIST_DEF_BONE = [] 
        if props.use_curve_subbone : 
            for s in range(len(Select_Bone)) : 
                LIST_DEF_BONE.append(
                    self.CreateBonesRange(
                    self.GN_Name(props.name_curve_def, Select_Bone[s].name), 
                    props.curve_subbone_howmuch)
                )

            save_head = None
            for i, list_bone in enumerate(LIST_DEF_BONE) :
                for x, bone in enumerate(list_bone) :
                    self.SetColorBone(bone, "THEME09")
                    if save_head == None: 
                        bone.head = Select_Bone[i].head
                    else : 
                        bone.head = save_head
                    bone.tail = Select_Bone[i].tail
                    bone.roll = Select_Bone[i].roll
                    bone.length /= len(list_bone)-x
                    save_head = bone.tail.copy()

        SELECT_BONE_NAME = self.GetNameToBones(Select_Bone)
        CURVE_FREE_NAME = self.GetNameToBones(CURVE_FREE)
        CURVE_CONT_NAME = self.GetNameToBones(CURVE_CONT)
        SUB_LIST_DEF_BONE = []
        for list_bone in LIST_DEF_BONE : 
            SUB_LIST_DEF_BONE.append(self.GetNameToBones(list_bone))
            
        if props.use_curve_root :
            ROOT_BONE_CURVE_NAME = self.GetNameToBones(ROOT_BONE_CURVE)
        self.SetMode("POSE")
        SELECT_BONE_POSE = self.GetBones(SELECT_BONE_NAME, "POSE")
        CURVE_FREE_POSE = self.GetBones(CURVE_FREE_NAME, "POSE")
        CURVE_CONT_POSE = self.GetBones(CURVE_CONT_NAME, "POSE")
        LIST_DEF_BONE_POSE = []
        for list_bone in SUB_LIST_DEF_BONE : 
            LIST_DEF_BONE_POSE.append(self.GetBones(list_bone, "POSE"))
        
        if props.use_curve_root :
            ROOT_BONE_CURVE_POSE = self.GetBones(ROOT_BONE_CURVE_NAME, "POSE")
        
        if CURVE_FREE_POSE and SELECT_BONE_POSE and CURVE_CONT_POSE :
            for i, bone in enumerate(self.GetBones(SELECT_BONE_NAME, "OBJECT")) :
                bone.bbone_handle_type_start = 'TANGENT'
                bone.bbone_handle_type_end = 'TANGENT'
                bone.bbone_segments = props.curve_int_segments
                bone.bbone_custom_handle_start = self.GetBone(CURVE_FREE_POSE[i].name)
                bone.bbone_custom_handle_end = self.GetBone(CURVE_FREE_POSE[i+len(SELECT_BONE_POSE)].name)
                bone.bbone_handle_use_ease_start = True
                bone.bbone_handle_use_ease_end = True

            
            for i, bone in enumerate(SELECT_BONE_POSE) :
                conts = bone.constraints.new(type='STRETCH_TO')
                conts.target = self.GetActiveObject()
                conts.subtarget = CURVE_FREE_POSE[i+len(SELECT_BONE_POSE)].name

            for i, f in enumerate(CURVE_FREE_POSE) :
                f.custom_shape = self.EMPTY_Arrow
                if i < len(SELECT_BONE_POSE) :
                    f.custom_shape_rotation_euler[0] = -1.5708
                else :
                    f.custom_shape_rotation_euler[0] = 1.5708
                
                f.custom_shape_scale_xyz[0] = 10
                f.custom_shape_scale_xyz[1] = 0
                f.custom_shape_scale_xyz[2] = 1
                
                for i in range(3):
                    if i != 1 :
                        f.lock_scale[i] = True
                    f.lock_location[i] = True
            
            for c in CURVE_CONT_POSE :
                c.custom_shape = self.EMPTY_Sphere
                c.custom_shape_scale_xyz *= 0.5
                
            if props.use_curve_root :
                ROOT_BONE_CURVE_POSE[0].custom_shape = self.EMPTY_Cube
            
            def add_drive(bone, Donde, control_bone, cual, use_menos_1 = False):
                # Añadir un controlador a la propiedad de ubicación X del cubo
                
                driver = bone.driver_add(Donde).driver

                # Configurar el controlador
                driver.type = 'SCRIPTED'
                var = driver.variables.new()
                var.name = "var"
                var.targets[0].id_type = 'OBJECT'
                var.targets[0].id = self.GetActiveObject()
                #var.targets[0].bone_target = control_bone.name
                var.targets[0].data_path=f'pose.bones["{control_bone.name}"].{cual}'
                
                # Escribir la expresión del controlador
                if use_menos_1 == False:
                    driver.expression = "var-1"
                else:
                    driver.expression = "var"
                    
            if props.use_curve_drive:
                for i in range(len(CURVE_FREE_POSE)):
                    if i < len(SELECT_BONE_POSE):
                        add_drive(
                            SELECT_BONE_POSE[i],
                            "bbone_easein",
                            CURVE_FREE_POSE[i],
                            "scale[1]"
                            )
                    else : 
                        add_drive(
                            SELECT_BONE_POSE[i-len(SELECT_BONE_POSE)],
                            "bbone_easeout",
                            CURVE_FREE_POSE[i],
                            "scale[1]"
                        )
            
            if props.use_curve_subbone : 
                for i, list_bone in enumerate(LIST_DEF_BONE_POSE) :
                    for x, bone in enumerate(list_bone) :
                        
                        
                        conts = bone.constraints.new(type='ARMATURE')
                        conts.targets.new()
                        for h, tgt in enumerate(conts.targets):
                            conts.targets[h].target = self.GetActiveObject()
                            conts.targets[h].subtarget = SELECT_BONE_POSE[i].name

                        if x > 0 and x < len(list_bone)-1 : 
                            conts = bone.constraints.new(type='STRETCH_TO')
                            conts.target = self.GetActiveObject()
                            conts.subtarget = list_bone[x+1].name
    
    def GN_AnnotateBone(self):
        
        props = self.Props()
        
        obj = self.GetActiveObject()
        if not obj or obj.type != 'ARMATURE':
            return
        
        grease = bpy.data.grease_pencils
        if not grease:
            return

        gp = grease[0]  # Ajusta si es necesario
        if not gp : return 
        
        if not bpy.ops.gpencil.annotation_active_frame_delete.poll(): return
        self.SetMode(mode="EDIT")
        
        
        name_bone : str = props.annotate_name
        type_mode = props.annotate_type_mode
        align_bone = props.annotate_use_join_bones
        proximity_join = props.annotate_proximity_join
        aling_roll_normal = props.annotate_aling_roll_normal
        use_curve = props.annotate_use_curve 
        curve_power = props.annotate_curve_power
        target = props.annotate_target
        use_select_target = props.annotate_use_select_target
        size_bbone = props.annotate_size_bbone
        direction : str = props.annotate_direction
        use_align_mirror_x = props.annotate_use_align_mirror_x
        use_align_mirror_y = props.annotate_use_align_mirror_y
        use_align_mirror_z = props.annotate_use_align_mirror_z
        use_align_mirror_negative_x = props.annotate_use_align_mirror_negative_x
        use_align_mirror_negative_y = props.annotate_use_align_mirror_negative_y
        use_align_mirror_negative_z = props.annotate_use_align_mirror_negative_z
        global_normal = props.annotate_global_normal
        use_parent = props.annotate_use_parent
        use_connect = props.annotate_use_connect
        segments = props.annotate_segments
        use_deform = props.annotate_use_deform
        use_vertbone = props.annotate_use_vertbone
        name_vertbone = props.annotate_name_vertbone
        use_vertbone_deform = props.annotate_use_vertbone_deform
        join_same_name = props.annotate_join_same_name
        
        new_bone = self.CreateBonesRange(name_bone, 1)[0] if type_mode == "ADD" else self.GetActiveBone("EDIT") if type_mode == "MOVE" else None

        def get_normal_from_surface(obj, world_pos):
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)

            ray_origin = world_pos + mathutils.Vector((0, 0, 0.1))  # Ligeramente por encima
            ray_dir = -mathutils.Vector((0, 0, 1))  # Dirección hacia abajo

            # Transformar el rayo al espacio local del objeto evaluado
            ray_origin_local = obj_eval.matrix_world.inverted() @ ray_origin
            ray_dir_local = obj_eval.matrix_world.inverted().to_3x3() @ ray_dir

            # Usamos ray_cast directamente sobre el objeto evaluado
            result, location, normal, face_index = obj_eval.ray_cast(ray_origin_local, ray_dir_local)

            if result:
                # Devolvemos la normal en espacio mundial
                return obj_eval.matrix_world.to_3x3() @ normal
            return None
        
        vert_bone = []
        
        def get_create_bone_from_vert_object(obj, arm, points):
            
            for v in obj.data.vertices:
                for p in points:
                    vert = obj.matrix_world.inverted() @ v.co
                    point = arm.matrix_world.inverted() @ p.co
                    if self.GetDistancia3d(vert, point) < proximity_join:
                        new = self.CreateBonesRange(name_vertbone, 1)[0]
                        if use_vertbone_deform:
                            new.use_deform = True
                        new.head = vert
                        new.tail = vert + self.GetWorldNormal("z")
                        new.roll = 0
                        new.length = new_bone.length * 0.2
                        vert_bone.append(new)

        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    points = stroke.points
                    if len(points) < 2:
                        if bpy.ops.gpencil.annotation_active_frame_delete.poll():    
                            bpy.ops.gpencil.annotation_active_frame_delete()    
                        self.SetMode(mode='POSE')
                        return # Necesitamos al menos 2 puntos para crear un hueso                    
                    # Un solo hueso por stroke
                    head = obj.matrix_world.inverted() @ points[0].co
                    tail = obj.matrix_world.inverted() @ points[-1].co
                      # usar punto inicial
                      
                    if type_mode == "REMOVE":
                        for p in points:
                            for bone in obj.data.edit_bones:
                                
                                if name_bone.lower() not in bone.name.lower():
                                    continue
                                point = obj.matrix_world.inverted() @ p.co
                                head_dis = self.GetDistancia3d(point, bone.head.copy())
                                tail_dis = self.GetDistancia3d(point, bone.tail.copy())
                                if head_dis < proximity_join or tail_dis < proximity_join :
                                    self.RemoveBones([bone.name])
                        if bpy.ops.gpencil.annotation_active_frame_delete.poll():    
                            bpy.ops.gpencil.annotation_active_frame_delete()
                        self.SetMode(mode='POSE')
                        return
                    
                    if not new_bone : 
                        if bpy.ops.gpencil.annotation_active_frame_delete.poll():    
                            bpy.ops.gpencil.annotation_active_frame_delete()
                        self.SetMode(mode='POSE')
                        return
                    
                    def use_align_mirror(value, type, is_negative = False):
                        if value :
                            if is_negative:
                                if getattr(head, type) > 0 :
                                    setattr(head, type, 0)
                                if getattr(tail, type) > 0:
                                    setattr(tail, type, 0)
                            else:
                                if getattr(head, type) < 0 :
                                    setattr(head, type, 0)
                                if getattr(tail, type) < 0:
                                    setattr(tail, type, 0)
                    
                    use_align_mirror(use_align_mirror_x, "x")
                    use_align_mirror(use_align_mirror_y, "y")
                    use_align_mirror(use_align_mirror_z, "z")
                    use_align_mirror(use_align_mirror_negative_x, "x", is_negative=True)
                    use_align_mirror(use_align_mirror_negative_y, "y", is_negative=True)
                    use_align_mirror(use_align_mirror_negative_z, "z", is_negative=True)
                    
                    new_bone.head = head
                    new_bone.tail = tail
                    if use_select_target :
                        objs = self.GetSelectableObjects()
                        for sobj in objs:
                            if sobj != obj:
                                subtarget = obj
                            else :
                                subtarget = target
                    else:
                        subtarget = target
            
                    if subtarget and not global_normal:
                        normal = self.CreateVector(0, 0, 0)
                        for p in points:
                            n = get_normal_from_surface(subtarget, p.co)
                            if not n : continue
                            normal += get_normal_from_surface(subtarget, p.co)
                        normal /= len(points)
                        
                        if use_vertbone:
                            get_create_bone_from_vert_object(subtarget, obj, points)
                        
                    else :
                        direction = str(direction).lower().replace("{'", "").replace("'}", "")
                        normal = self.GetWorldNormal(direction if direction != "" else "z")
                    
                    if normal :
                        
                        if aling_roll_normal : 
                            new_bone.align_roll(normal)
  
                        if use_curve : 
                            # Posición local del punto medio del trazo
                            Location = obj.matrix_world.inverted() @ points[int(len(points) / 2)].co
                            curve_position = Location - ((head + tail) / 2)

                            # Transformar la curva al espacio local del hueso
                            bone_matrix = new_bone.matrix.to_3x3().inverted()
                            local_curve = bone_matrix @ curve_position

                            # Aplicar curvatura en el espacio local del hueso
                            def use_align_mirror(bone, value, type, is_negative = False):
                                if value :
                                    if is_negative:
                                        if getattr(bone, type) > 0 :
                                            setattr(bone, type, 0)
                                    else:
                                        if getattr(bone, type) < 0 :
                                            setattr(bone, type, 0)
                                        
                            new_bone.bbone_curveinx = (local_curve.x / 2) * curve_power
                            new_bone.bbone_curveoutx = (local_curve.x / 2) * curve_power
                            use_align_mirror(new_bone, use_align_mirror_x, "bbone_curveinx")
                            use_align_mirror(new_bone, use_align_mirror_negative_x, "bbone_curveinx", is_negative=True)
                            use_align_mirror(new_bone, use_align_mirror_x, "bbone_curveoutx")
                            use_align_mirror(new_bone, use_align_mirror_negative_x, "bbone_curveoutx", is_negative=True)
                            
                            
                            new_bone.bbone_curveinz = (local_curve.z / 2) * curve_power
                            new_bone.bbone_curveoutz = (local_curve.z / 2) * curve_power

                            new_bone.bbone_segments = segments
                    
                    new_bone.bbone_x = size_bbone
                    new_bone.bbone_z = size_bbone
                    new_bone.use_deform = use_deform
                    
        if align_bone : 
            head_bones = []
            tail_bones = []
            head_accum = new_bone.head.copy()
            tail_accum = new_bone.tail.copy()
                        
            parent = None
            sont = None
            
            for bone in obj.data.edit_bones or join_same_name:
                name : str = bone.name.lower()
                new_name_bone : str = name_bone.lower()
                
                if new_name_bone in name or not join_same_name:
                    
                    if self.GetDistancia3d(new_bone.head, bone.head) < proximity_join:
                        head_bones.append(("head", bone))
                        head_accum += bone.head
                    if self.GetDistancia3d(new_bone.head, bone.tail) < proximity_join:
                        head_bones.append(("tail", bone))
                        parent = bone
                        head_accum += bone.tail
                    if self.GetDistancia3d(new_bone.tail, bone.tail) < proximity_join:
                        tail_bones.append(("tail", bone))
                        tail_accum += bone.tail
                    if self.GetDistancia3d(new_bone.tail, bone.head) < proximity_join:
                        tail_bones.append(("head", bone))
                        tail_accum += bone.head
                        sont = bone

            # Calcular promedios
            new_head = head_accum / (len(head_bones) + 1)
            new_tail = tail_accum / (len(tail_bones) + 1)

            # Aplicar a todos los huesos correspondientes
            for end, bone in head_bones:
                if end == "head":
                    bone.head = new_head
                else:
                    bone.tail = new_head

            for end, bone in tail_bones:
                if end == "tail":
                    bone.tail = new_tail
                else:
                    bone.head = new_tail

            new_bone.head = new_head
            new_bone.tail = new_tail
            
            if use_parent:
                if parent:
                    new_bone.parent = parent
                    new_bone.use_connect = use_connect and (new_bone.head - parent.tail).length < 1e-6

                if sont:
                    sont.parent = new_bone
                    sont.use_connect = use_connect and (sont.head - new_bone.tail).length < 1e-6

            if not new_bone.parent :
                new_bone.use_connect = False
            
        if bpy.ops.gpencil.annotation_active_frame_delete.poll():    
            bpy.ops.gpencil.annotation_active_frame_delete()
        self.SetMode(mode='POSE')

    def GN_CurveGrip(self):
        
        self.AddCollection()
        if not self.GetActiveObject() : return
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        select_bone = self.GetSelectBones("EDIT")
        if not select_bone : return
        
        props = self.Props()
        
        use_target = props.grip_use_target
        use_target_scale = props.grip_use_target_scale
        align_to_normal = props.grip_align_to_normal
        align_target = props.grip_align_target
        root_name = props.name_grip_root
        target_name = props.name_grip_target
        target_scale_name = props.name_grip_target_scale
        proximity_join = props.grip_proximity_join
        grip_segments = props.grip_segments
        
        root_bones = []
        target_bones = []
        curve_rot_target = []
        
        damped_track_bones = []
        
        points = []
        length = 0  
        for bone in select_bone : 
            length += bone.length
        length /= len(select_bone)
        
        
        collections_name = [
            "Curve", "Curve Root", "Curve Target", "Curve Controller"
        ]
        
        collections = self.GetActiveObject().data.collections
        for c in collections_name :
            if not collections.get(c):
                collections.new(c)
            
        for bone in select_bone : 
            
            points.append(bone.head)
            points.append(bone.tail)
            
            curve_rot_target.append(
                [[bone.bbone_curveinx, bone.bbone_curveinz],
                [bone.bbone_curveoutx, bone.bbone_curveoutz]]
            )
            
            tail_in = self.CreateVector(bone.bbone_curveinx, 0, bone.bbone_curveinz)
            tail_out = self.CreateVector(bone.bbone_curveoutx, 0, bone.bbone_curveoutz)
            
            bone.bbone_curveinx = 0 
            bone.bbone_curveoutx = 0 
            bone.bbone_curveinz = 0 
            bone.bbone_curveoutz = 0
            
            self.BoneCollectionAssing("Curve", bone)
            
            # Cont_
            root_bone = self.CreateBonesRange(self.GN_Name("cont_", bone.name), 2)
            root_bones.append([root_bone[0].name, root_bone[1].name])
            self.SetTransform(root_bone[0], bone, length_value=0.25)
            self.SetTransform(root_bone[1], bone, length_value=0.25, only_tail=True)
            self.SetDeform(root_bone, False)
            for i in range(2):
                self.SetDisplaySize(root_bone[i], bone)
                self.BoneCollectionAssing("Curve Controller", root_bone[i])
                self.SetColorBone(root_bone[i], type_palette="THEME04")
                root_bone[i].length = length * 0.05
            
            bone.use_connect = False
            bone.parent = root_bone[0]
            
            if use_target :
                target_bone = self.CreateBonesRange(self.GN_Name(target_name, bone.name), 2)
                target_bones.append([target_bone[0].name, target_bone[1].name])
                self.SetTransform(target_bone[0], bone, length_value=0.5)
                self.SetTransform(target_bone[1], bone, length_value=0.5, only_tail=True)
                self.SetDeform(target_bone, False)
                # Obtener matriz del hueso base para orientación
                mat = bone.matrix.to_3x3().normalized()  # Solo rotación

                # Convertir los vectores a coordenadas locales del hueso
                local_tail_in = mat @ (tail_in * 2)
                local_tail_out = mat @ (tail_out * 2)

                # Aplicarlos en el tail de los controladores
                target_bone[0].tail += local_tail_in 
                target_bone[1].tail += -local_tail_out   # igual que * -1 pero más claro

                for i in range(2):
                    self.SetDisplaySize(target_bone[i], bone)
                    self.BoneCollectionAssing("Curve Target", target_bone[i])
                    self.SetColorBone(target_bone[i], type_palette="THEME03")
                    target_bone[i].parent = root_bone[i]

                bone.bbone_custom_handle_start = target_bone[0]
                bone.bbone_custom_handle_end = target_bone[1]
            else:
                bone.bbone_custom_handle_start = root_bone[0]
                bone.bbone_custom_handle_end = root_bone[1]
                
            bone.bbone_handle_type_start = 'TANGENT'
            bone.bbone_handle_type_end = 'TANGENT'
            bone.bbone_handle_use_ease_start = True
            bone.bbone_handle_use_ease_end = True
            bone.bbone_segments = grip_segments
            
            if align_target and use_target: 
                damped_track_bone = self.CreateBonesRange(self.GN_Name("track_", bone.name), 2)
                damped_track_bones.append([damped_track_bone[0].name, damped_track_bone[1].name])
                self.SetTransform(damped_track_bone[0], bone, length_value=0.2)
                self.SetTransform(damped_track_bone[1], bone, length_value=0.2, only_tail=True)
                self.SetDeform(damped_track_bone, False)
                for i in range(2) : 
                    target_bone[i].parent = damped_track_bone[i]
                    damped_track_bone[i].parent = root_bone[i]
                    self.BoneCollectionAssing("Curve Controller", damped_track_bone[i])
                    self.SetDisplaySize(damped_track_bone[i], bone)
 
        new_points = []

        for a in points:
            too_close = False
            for b in new_points:
                if self.GetDistancia3d(a, b) < proximity_join:
                    too_close = True
                    break
            if not too_close:
                new_points.append(a)
        
        
        
        def CreateToPoints(name, color : str = "THEME02", value_length : float = 0.2, parents = [], get_bone_ht : bool = False):
            bones = []
            
                
            for i, head in enumerate(new_points) :
                
                bone = self.CreateBonesRange(self.GN_Name(name, select_bone[0].name), 1)
                self.BoneCollectionAssing("Curve Root", bone[0])
                bone[0].head = head 
                bone[0].tail = head + self.GetWorldNormal()
                if parents : 
                    bone[0].parent = self.GetBone(parents[i], mode="EDIT")
                self.SetDeform(bone, False)
                self.SetDisplaySize(bone[0], select_bone[0])
                self.SetColorBone(bone[0], color)

                value : int = 0
                normal = self.CreateVector(0, 0, 0)
                if get_bone_ht : 
                    head_bones = []
                    tail_bones = []
                    for sbone in select_bone:
                        
                        if self.GetDistancia3d(head, sbone.head) < proximity_join: 
                            head_bones.append(sbone.name)
                        if self.GetDistancia3d(head, sbone.tail) < proximity_join: 
                            tail_bones.append(sbone.name)
                    
                for names in root_bones : 
                    bone_a = self.GetBone(names[0], mode="EDIT")
                    bone_b = self.GetBone(names[1], mode="EDIT")
                    
                    for cbone in [bone_a, bone_b] :
                        if self.GetDistancia3d(head, cbone.head) < proximity_join: 
                            if not parents : 
                                cbone.parent = bone[0]

                            normal += cbone.z_axis
                            value += 1

                if align_to_normal :
                    normal = normal/value
                    bone[0].tail = head + normal

                bone[0].length = length * value_length
                if get_bone_ht :
                    bones.append([bone[0].name, head_bones, tail_bones])
                else:
                    bones.append(bone[0].name)
            return bones
        
        roots = CreateToPoints(root_name, value_length=0.1)
        if use_target_scale :
            target_scale_bones = CreateToPoints(target_scale_name, "THEME09", 0.12, roots, True)

        select_bone = self.GetNameToBones(select_bone)
        self.SetMode(mode="POSE")
        select_bone = self.GetBones(select_bone, mode="POSE")
        if not select_bone : return
    
        for name in roots : 
            bone = self.GetBone(name, mode="POSE")
            if bone : 
                bone.custom_shape = self.EMPTY_Sphere
                for i in range(3):
                    bone.lock_scale[i] = True
                bone.custom_shape_wire_width = 2
        
        for i, names in enumerate(root_bones) : 
            
            bone_a = self.GetBone(names[0], mode="POSE")
            bone_b = self.GetBone(names[1], mode="POSE")
            
            for bone in [bone_a, bone_b] : 
                bone.custom_shape = self.EMPTY_Sphere
                for e in range(3):
                    bone.lock_rotation[e] = True
                    bone.lock_scale[e] = True
                    bone.lock_location[e] = True
                
            conts = select_bone[i].constraints.new(type='STRETCH_TO')
            conts.target = self.GetActiveObject()
            conts.subtarget = names[1]
            conts.bulge = props.grip_bulge

        
        for i, names in enumerate(target_bones):
            
            bone_a = self.GetBone(names[0], mode="POSE")
            bone_b = self.GetBone(names[1], mode="POSE")
            
            
            cont_bone_a = root_bones[i][0]
            cont_bone_b = root_bones[i][1]
            self.CreatreDrive(
                    self.GetBone(names[0], mode="OBJECT"), "hide",
                    self.GetBone(root_bones[i][0], mode="POSE"), f"rgc_select",
                    Use_Bone=True,
                )
            if bone_a and bone_b :
                for bone in [bone_a, bone_b] :
                    bone.custom_shape = self.EMPTY_Arrow
                    if bone == bone_a :
                        bone.custom_shape_rotation_euler[0] = -1.5708
                    else :
                        bone.custom_shape_rotation_euler[0] = 1.5708
                    
                    bone.custom_shape_scale_xyz[0] = 1
                    bone.custom_shape_scale_xyz[1] = 0
                    bone.custom_shape_scale_xyz[2] = 1
                    bone.custom_shape_wire_width = 2
                    
                    
                    
                    for i in range(3):
                        if i != 1 :
                            bone.lock_scale[i] = True
                        bone.lock_location[i] = True
        
        if use_target_scale : 
            for i, list in enumerate(target_scale_bones):
                head_bones = list[1]
                tail_bones = list[2]
                
                target_bone = self.GetBone(list[0], mode="POSE")
                
                

                
                target_bone.custom_shape = self.EMPTY_Arrows
                target_bone.custom_shape_wire_width = 3
                
                target_bone.custom_shape_rotation_euler[0] = -0.459737
                target_bone.custom_shape_rotation_euler[1] = 0.417614
                target_bone.custom_shape_rotation_euler[2] = 0.685448
                

                for e in range(3):
                    target_bone.lock_rotation[e] = True
                    target_bone.lock_location[e] = True
                target_bone.lock_rotation_w = True

                for name in head_bones:
                    head_bone = self.GetBone(name, mode="POSE")
                    if head_bone:
                        for e in range(3):
                            self.CreatreDrive(
                                    head_bone, "bbone_scalein",
                                    target_bone, f"scale[{e}]",
                                    Use_Bone=True,
                                    index= e
                                )
                for name in tail_bones:
                    tail_bone = self.GetBone(name, mode="POSE")
                    if tail_bone:
                        for e in range(3):
                            self.CreatreDrive(
                                tail_bone, f"bbone_scaleout",
                                target_bone, f"scale[{e}]", 
                                Use_Bone=True, 
                                index= e
                            )
        
        if align_target and use_target : 
            
            for i, names in enumerate(damped_track_bones) :
                bone_a = self.GetBone(names[0], mode="POSE")    
                bone_b = self.GetBone(names[1], mode="POSE") 
                
                cont_bone_a = root_bones[i][0]
                cont_bone_b = root_bones[i][1]
                
                c = bone_a.constraints.new(type='DAMPED_TRACK')
                c.target = self.GetActiveObject()
                c.subtarget = cont_bone_b
                
                c = bone_b.constraints.new(type='DAMPED_TRACK')
                c.target = self.GetActiveObject()
                c.subtarget = cont_bone_a
                c.track_axis = 'TRACK_NEGATIVE_Y'

    def GN_Auto_Root(self) : 
        
        self.AddCollection()
        props = self.Props()
        
        self.SetMode("EDIT")
        self.UseMirror(use=False)
        Active_Bone = self.GetActiveBone(mode="EDIT")
        
        name = self.GN_Name(props.name_auto_root, Active_Bone.name) if props.use_active_bone else props.name_auto_root
        ROOT_BONE = self.CreateBonesRange(name, props.bones_parent)
        self.SetDeform(ROOT_BONE, False)
        if props.use_active_bone :
            for bone in ROOT_BONE :
                self.SetTransform(bone, Active_Bone)
                self.SetDisplaySize(bone, Active_Bone)
            Active_Bone.parent = ROOT_BONE[0]
            for i in range(len(ROOT_BONE)-1):
                ROOT_BONE[i].parent = ROOT_BONE[i+1]
                
        else:
            for bone in ROOT_BONE : 
                bone.head = (0, 0, 0)
                bone.tail = self.GetWorldNormal("y")
                bone.roll = 0
            
        for i, bone in enumerate(ROOT_BONE) :
            self.SetColorBone(bone, f"THEME0{i+1}")
        
        self.SetRelationsOnlyOneList(ROOT_BONE, Use_connect=False)
        
        ROOT_BONE_NAME = self.GetNameToBones(ROOT_BONE)
        ACTIVE_BONE_NAME = self.GetNameToBones([Active_Bone])
        self.SetMode("POSE")
        ROOT_BONE_POSE = self.GetBones(ROOT_BONE_NAME, "POSE")
        ACTIVE_BONE_POSE = self.GetBones(ACTIVE_BONE_NAME, "POSE")
        
        if ROOT_BONE_POSE :
            for i, bone in enumerate(ROOT_BONE_POSE) :
                if not props.use_active_bone :
                    bone.custom_shape = self.EMPTY_Cube
                    bone.custom_shape_scale_xyz *= ((i+1)/2)
                    bone.custom_shape_scale_xyz[2] = 0
                else : 
                    bone.custom_shape = ACTIVE_BONE_POSE[0].custom_shape
                    bone.custom_shape_scale_xyz *= ((i+1)/2)
                    bone.custom_shape_scale_xyz[2] = 0
                    bone.custom_shape_scale_xyz += ACTIVE_BONE_POSE[0].custom_shape_scale_xyz*0.5
        
        ...
    
    def GN_ROT_CONT(
        self, point : Vector, target_point : Vector, name : str, shape : object, 
        use_def_bone : bool = True, scale : float = 0.5,  ) -> list :
        
        """
        [rot_bone, def_bone, cont_bone, Direction] is use_def_bone = True
        [rot_bone, cont_bone, Direction] is use_def_bone = False
        
        """
        
        self.SetMode("EDIT")
        import unicodedata
        def safe_name(name: str) -> str:
            # Si por error llega como bytes, conviértelo
            if isinstance(name, bytes):
                try:
                    name = name.decode("utf-8", errors="ignore")
                except Exception:
                    name = name.decode("latin1", errors="ignore")
            # Normaliza a ASCII (quita acentos, caracteres raros)
            name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
            return name
        
        name = safe_name(name)
        
        dir = "UP" 
        if target_point.z > point.z :
            dir = "DOWN"
        elif target_point.z == point.z :
            dir = "MED"
        
        rot_bone = self.CreateBone(f"rot_{name}")
        if rot_bone :
            rot_bone.head = point
            rot_bone.tail = target_point
            rot_bone.align_roll(self.GetWorldNormal("z"))
            self.SetDeform([rot_bone], False)
        
        if use_def_bone :
            def_bone = self.CreateBone(f"def_{name}")
            if def_bone :
                def_bone.head = target_point
                def_bone.tail = target_point + self.GetWorldNormal()
                def_bone.parent = rot_bone
                def_bone.length *= scale
                self.SetDeform([def_bone], True)
            
        cont_bone = self.CreateBone(f"cont_{name}")
        if cont_bone :
            cont_bone.head = target_point
            cont_bone.tail = target_point + self.GetWorldNormal()
            cont_bone.length *= scale
            self.SetColorBone(cont_bone, "THEME09")
            self.SetDeform([cont_bone], False)
        
        cont_bones_name = self.GetNameToBones([cont_bone]) if cont_bone else []
        rot_bones_name  = self.GetNameToBones([rot_bone]) if rot_bone else []
        def_bones_name  = self.GetNameToBones([def_bone]) if (use_def_bone and def_bone) else []

        self.SetMode("POSE")

        cont_bone = self.GetBones(cont_bones_name, "POSE")[0] if self.GetBones(cont_bones_name, "POSE") else None
        rot_bone  = self.GetBones(rot_bones_name, "POSE")[0] if self.GetBones(rot_bones_name, "POSE") else None
        def_bone  = self.GetBones(def_bones_name, "POSE")[0] if self.GetBones(def_bones_name, "POSE") else None

        if cont_bone and rot_bone :
            cont_bone.custom_shape = shape
            cont_bone.custom_shape_scale_xyz *= scale
        
            const = rot_bone.constraints.new(type='DAMPED_TRACK')
            const.target = self.GetActiveObject()
            const.subtarget = cont_bones_name[0]

        if cont_bone and def_bone and rot_bone:
            if use_def_bone :
                return [rot_bone.name, def_bone.name, cont_bone.name, dir]
            else :
                return [rot_bone.name, cont_bone.name, dir]
        else :
            return []
    
        


GN = GeneratorsBones()
import bpy
import mathutils

import bpy
import mathutils

def GN_AnnotatePoseBone():
    obj = bpy.context.active_object
    if not obj or obj.type != 'ARMATURE':
        return

    grease = bpy.data.grease_pencils
    if not grease:
        return

    gp = grease[0]  # Ajusta si tienes múltiples
    pose_bones = [b for b in obj.pose.bones if b.bone.select]

    for pbone in pose_bones:
        head_world = obj.matrix_world @ pbone.head
        tail_world = obj.matrix_world @ pbone.tail

        closest_head = None
        closest_tail = None
        min_head_dist = float("inf")
        min_tail_dist = float("inf")

        for layer in gp.layers:
            for frame in layer.frames:
                for stroke in frame.strokes:
                    for point in stroke.points:
                        pt = point.co
                        dist_head = (pt - head_world).length
                        dist_tail = (pt - tail_world).length

                        if dist_head < min_head_dist:
                            min_head_dist = dist_head
                            closest_head = pt
                        if dist_tail < min_tail_dist:
                            min_tail_dist = dist_tail
                            closest_tail = pt

        if closest_head and closest_tail:
            # Dirección del hueso
            direction = (closest_tail - closest_head).normalized()

            up = mathutils.Vector((0, 0, 1))
            if abs(direction.dot(up)) > 0.999:
                up = mathutils.Vector((0, 1, 0))  # Evitar degeneración

            right = direction.cross(up).normalized()
            up = right.cross(direction).normalized()

            rot_mat = mathutils.Matrix((
                right,
                direction,
                up
            )).transposed()

            new_matrix = rot_mat.to_4x4()
            new_matrix.translation = closest_head

            # Guardar la escala original
            original_scale = pbone.matrix.to_scale()

            
            # Asignar matriz sin escala
            pbone.matrix = obj.matrix_world.inverted() @ new_matrix

            # Restaurar la escala original
            pbone.scale = original_scale


    bpy.ops.gpencil.annotation_active_frame_delete()

@bpy.app.handlers.persistent
def GN_Update_AnnotateBone(dummy):
    props = GN.Props()
    obj = GN.GetActiveObject()
    if obj and obj.type == "ARMATURE" and GN.GetObjMode() == "POSE" :
        if props.annotate_auto_bone and GN.PanelType([{"RIG"}]):
            GN.GN_AnnotateBone()
        #else : 
        #    if props.annotate_posebone :
        #        GN_AnnotatePoseBone()
import bpy
from ...generaldata import *
from types import SimpleNamespace
import bmesh
from mathutils import Vector

class ResetArmature(GeneralArmatureData):
    
    def init(self):
        self.Armature = bpy.context.active_object
        if not self.IsArmatureExists() : return

        self.NE_Spine = []
        for i in range(6):
            self.NE_Spine.append(f"base_spine.{i+1:003}")

        Faces = [
            ("Mouth_UP", 3), ("Mouth_DOWN", 3), 
            ("Nose", 3), ("Jaw", 4), 
            ("Cheekbone_UP", 4), ("Cheekbone_DOWN", 3),
            ("Eyebrows", 4), ("Subeyebrows", 3),
            ("Subeyelids_UP", 4),
            ("Eyelids_UP", 4), ("Eyelids_DOWN", 4),
            ("Subeyelids_UP", 4), ("Ear", 5)
        ]
        
        MEdFaces = [
            ("Medface_UP", 4), ("Medface_DOWN", 2),
        ]
        
        for face in MEdFaces :
            face_name = face[0].lower()
            if "UP" in face[0]:
                face_name = face_name.replace("_up", "_UP")
            if "DOWN" in face[0]:
                face_name = face_name.replace("_down", "_DOWN")
            setattr(
                    self, f"NE_{face[0]}", [
                        f"base_{face_name}.{i+1:003}" for i in range(face[1])
                    ]
            )
            
        for type in ["R", "L"]:
            
            
            setattr(self, f"NE_Roteye_{type}", [f"base_rot_eye_{type}"])
            
            for face in Faces:
                face_name = face[0].lower()
                if "UP" in face[0]:
                    face_name = face_name.replace("_up", "_UP")
                if "DOWN" in face[0]:
                    face_name = face_name.replace("_down", "_DOWN")
                setattr(
                    self, f"NE_{face[0]}_{type}", [
                        f"base_{face_name}_{type}.{i+1:003}" for i in range(face[1])
                    ]
                )
            
            for body in ["Arm", "Leg", "Feet", "Shoulder", "Hip"] : 
               setattr(
                self, f"NE_{body}_{type}", [
                    f"base_{body.lower()}_{type}.{i+1:003}" for i in range(
                        3 if body == "Arm" else 2
                        )
                    ]
                )
            
            for finger in self.ListFinger() :
                setattr(
                    self, f"NE_{finger}_{type}", [f"base_{finger.lower()}_{type}.{i+1:003}" for i in range(4)]
                ) 
            
    
    def ResetAllArmature(self) : 
        
        props = self.Props()
        self.init()
        #if props.use_delect_bones : self.DelectBones()
        
        self.ResetFace()
        #self.ResetCartoonFace()
        self.ResetSpine()
        self.ResetRoot()
        self.ResetArm("R"), self.ResetArm("L")
        for finger in self.ListFinger():
            name = finger.lower().replace(" ", "_").lower()
            self.ResetFingers(name, "R")
            self.ResetFingers(name, "L")
        self.ResetLeg("R")
        self.ResetLeg("L")

    def DelectBones(self):
        self.SetMode(mode="EDIT")
        obj = self.GetActiveObject()
        bones = [bone.name for bone in obj.data.edit_bones]

        def delect_bone(keys: str, type: str):
            bone_to_remove = []
            for bone_name in bones:
                if type == "":
                    if keys in bone_name.lower():
                        bone_to_remove.append(bone_name)
                else:
                    # Verificamos si termina con ".NNN"
                    if bone_name[-4:].startswith(".") and bone_name[-3:].isdigit():
                        t_name = bone_name[:-4]
                    else:
                        t_name = bone_name
                    if keys in bone_name.lower() and type == t_name[-1]:
                        bone_to_remove.append(bone_name)
                        
            self.RemoveBones(bone_to_remove)

        def check_bone(bone_name : str, rang : int = 3, keys : str = "arm", type : str = "") :
                dbones = [f"{bone_name}.{i+1:003}" for i in range(rang)]
                if any(name in bones for name in dbones):
                    return 
                delect_bone(keys, type) 
                             
        for type in ["R", "L"] : 
            
            check_bone(f"base_arm_{type}", 3 , "arm", type)
            check_bone(f"base_leg_{type}", 2 , "leg", type)
            check_bone(f"base_feet_{type}", 2 , "feet", type)
            for f in self.ListFinger() :
                finger = f.lower().replace(" ", "_").lower()
                check_bone(f"base_{finger}_{type}", 4 if f == "Thumb" else 3, finger, type)
            check_bone(f"base_eyebrows_{type}", 4 , "eyebrows", type)
            check_bone(f"base_rot_eye_{type}", 14 , "eye", type)
            check_bone(f"base_rot_eye_{type}", 4 , "eyes","")
            for dir in ["DOWN", "UP"] :
                check_bone(f"base_eyelids_{dir}_{type}", 4 , "eyelids", type)
                check_bone(f"base_eyelids_{dir}_{type}", 4 , "eyelids", type)
                check_bone(f"base_medface_{type}", 5 , "medface","")
                check_bone(f"base_medface_{type}", 5 , "nose",type)
                check_bone(f"base_medface_{type}", 5 , "nose","")
            
        self.SetMode(mode="POSE")
        
    def ResetAllign(self) : 
        self.SetMode(mode="EDIT")
        
        #Cejas
        for type in ["R", "L"] :
            
            Brows = self.GetBonesToRange(f"base_eyebrows_{type}", 4, "EDIT")
            
            def get_axis(bones):
                vector = self.CreateVector(0, 0, 0)
                for b in bones :
                    vector += (b.tail + b.head) / 2
                vector /= (len(bones))
                return vector 
            
            if Brows :
                vector = get_axis(Brows)
                cont_brows = self.GetBone(f"mov_eyebrows_{type}", "EDIT")
                if cont_brows :
                    
                    cont_brows.align_roll(vector)
                    
            for dir in ["DOWN", "UP"] :
                Eyes = self.GetBonesToRange(f"base_eyelids_{dir}_{type}", 4, "EDIT")
                if Eyes :
                    move_eye = self.GetBone(f"mov_eyelids_{dir}_{type}", "EDIT")
                    if move_eye :
                        move_eye.align_roll(get_axis(Eyes))
                
            
            SubEyesLip = self.GetBonesToRange(f"base_subeyelids_UP_{type}", 4, "EDIT")
            if SubEyesLip :
                move_eye = self.GetBone(f"mov_subeyelids_UP_{type}", "EDIT")
                if move_eye :
                    move_eye.align_roll(get_axis(SubEyesLip))
    
        self.ResetALLBoneStretchTo()
    # Reseta los Huesos de la cara, el Armture selecionado
    def ResetFace(self) : 
        self.init()
        self.SetMode(mode="EDIT")
        for type in ["R", "L"] : 
            
            BS_RotEye = self.GetBones(
                    getattr(self, f"NE_Roteye_{type}"), mode="EDIT"
            )
            # Parpados
            for directon in ["UP", "DOWN"] : 

                BS_Eyelids = self.GetBones(
                    getattr(self, f"NE_Eyelids_{directon}_{type}"), mode="EDIT"
                )
                if self.CheckIsBonesExisted(self.GetNameToBones(BS_Eyelids)) : 

                    Df_Eyelids = self.GetBones(
                        [f"def_eyelids_{directon}_{type}.{i+1:003}" for i in range(len(BS_Eyelids))] 
                        , mode="EDIT"
                        )
                    CONT_Eyelids = self.GetBones(
                        [f"cont_eyelids_{directon}_{type}.{i+1:003}" for i in range(len(BS_Eyelids)+1)] 
                        , mode="EDIT"
                        )

                    ROT_Eye = self.GetBonesToRange(
                    f"rot_eye_{directon}_{type}", 2, "EDIT"
                    )
                    
                    if BS_RotEye and ROT_Eye:
                        for i in range(2):
                            if ROT_Eye[i] :
                                ROT_Eye[i].head = BS_RotEye[0].head
                                ROT_Eye[i].tail = BS_Eyelids[-2].head
                    
                    
                    if BS_Eyelids and Df_Eyelids and CONT_Eyelids:
                        for i, bone in enumerate(Df_Eyelids) : 
                            self.SetTransform(bone, BS_Eyelids[i])
                            self.SetDisplaySize(
                                bone, BS_Eyelids[i], 
                                Display_size_x=2,
                                Display_size_y=2
                            )
                        for i in range(len(CONT_Eyelids)-1) : 
                            self.SetTransform(CONT_Eyelids[i], BS_Eyelids[i], length_value=0.2)
                        self.SetTransform(
                            CONT_Eyelids[-1], BS_Eyelids[-1], 
                            length_value=0.2, only_tail=True
                            )
                    MV_Eyelids = self.GetBone(f"mov_eyelids_{directon}_{type}", "EDIT")
                    if BS_Eyelids and MV_Eyelids :
                        MV_Eyelids.head = BS_Eyelids[-2].head
                        MV_Eyelids.tail = BS_Eyelids[-2].head + self.GetWorldNormal()
                        MV_Eyelids.roll = 0
                        Length : float = 0 
                        for bone in BS_Eyelids:
                            Length += bone.length
                        MV_Eyelids.length = (Length/len(BS_Eyelids))/2
                    
            CONT_SubEye = self.GetBones(
                    [f"cont_subeye_{type}.{i+1:003}" for i in range(2)] 
                    , mode="EDIT"
            )
            
            BS_Eyelids = self.GetBones(
                    getattr(self, f"NE_Eyelids_UP_{type}"), mode="EDIT"
                ) 
            
            if CONT_SubEye and BS_Eyelids:
                for i in range(2):
                    local_Head = BS_Eyelids[0].head if i == 0 else BS_Eyelids[-1].tail
                    CONT_SubEye[i].head = local_Head
                    CONT_SubEye[i].tail = local_Head
                    CONT_SubEye[i].roll = 0
                    Length : float = 0 
                    for bone in BS_Eyelids:
                        Length += bone.length
                    
                    
                    CONT_SubEye[i].length = (Length/len(BS_Eyelids))/2
            
            BS_SubEyelids = self.GetBones(
                    getattr(self, f"NE_Subeyelids_UP_{type}"), mode="EDIT"
                ) 
            Df_SubEyelids = self.GetBonesToRange(
                f"def_subeyelids_UP_{type}", len(BS_SubEyelids), "EDIT"
            )
            CONT_SubEyelids = self.GetBonesToRange(
                f"cont_subeyelids_UP_{type}", len(BS_SubEyelids)+1, "EDIT"
            )
            if BS_SubEyelids and Df_SubEyelids and CONT_SubEyelids:
                for i, bone in enumerate(Df_SubEyelids) : 
                    self.SetTransform(bone, BS_SubEyelids[i])
                    self.SetDisplaySize(
                        bone, BS_SubEyelids[i], 
                        Display_size_x=2,
                        Display_size_y=2
                    )
                for i in range(len(BS_SubEyelids)) : 
                    self.SetTransform(CONT_SubEyelids[i], BS_SubEyelids[i], length_value=0.2)
                    self.SetDisplaySize(
                        CONT_SubEyelids[i], BS_SubEyelids[i], 
                        Display_size_x=2.2,
                        Display_size_y=2.2
                    )
                self.SetTransform(CONT_SubEyelids[-1], BS_SubEyelids[-1], only_tail= True, length_value=0.2)
                self.SetDisplaySize(
                        CONT_SubEyelids[-1], BS_SubEyelids[-1], 
                        Display_size_x=2.2,
                        Display_size_y=2.2
                )                

            MV_SubEyelids = self.GetBone(f"mov_subeyelids_UP_{type}", "EDIT")
            if BS_SubEyelids and MV_SubEyelids :
                MV_SubEyelids.head = BS_SubEyelids[-2].head
                MV_SubEyelids.tail = BS_SubEyelids[-2].head + self.GetWorldNormal()
                MV_SubEyelids.roll = 0
                Length : float = 0 
                for bone in BS_SubEyelids:
                    Length += bone.length
                MV_SubEyelids.length = (Length/len(BS_SubEyelids))/2

            # Rot Eye
            ROT_Eye = self.GetBone(f"rot_eye_{type}", mode="EDIT")
            if ROT_Eye : 
                self.SetTransform(ROT_Eye, BS_RotEye[0])
            
            ROT_SubEye = self.GetBone(f"rot_subeye_{type}", mode="EDIT")
            if ROT_SubEye : 
                self.SetTransform(ROT_SubEye, BS_RotEye[0], length_value=0.5)
            
            # Control Eye 
            CONT_Eye = self.GetBone(f"cont_eye_{type}", mode="EDIT")
            if CONT_Eye : 
                self.SetTransform(CONT_Eye, BS_RotEye[0])

            # Eye
            
            Eye = self.GetBone(f"eye_{type}", mode="EDIT")
            if Eye : 
                Local_Head = (
                    BS_RotEye[0].tail[0],
                    (BS_RotEye[0].tail[1] - BS_RotEye[0].length*10),
                    BS_RotEye[0].tail[2],
                    )
                Local_Tail = (
                    BS_RotEye[0].tail[0],
                    (BS_RotEye[0].tail[1] - BS_RotEye[0].length*10),
                    BS_RotEye[0].tail[2]+1,
                    )
                Eye.head = Local_Head
                Eye.tail = Local_Tail
                Eye.length = BS_RotEye[0].length/2
            
            
            # Cejas
            BS_Eyebrows = self.GetBones(
                getattr(self, f"NE_Eyebrows_{type}"), mode="EDIT"
            )
            
            
            if BS_Eyebrows :

                # Def Cejas
                DF_Eyebrows = self.GetBonesToRange(
                    f"def_eyebrows_{type}", Range=4, mode="EDIT"
                )
                if DF_Eyebrows : 
                    for i, bone in enumerate(DF_Eyebrows) :
                        self.SetTransform(bone, BS_Eyebrows[i])
                
                
                # Control Cejas
                CONT_Eyebrows = self.GetBonesToRange(
                    f"cont_eyebrows_{type}", Range=5, mode="EDIT"
                )
                
                if CONT_Eyebrows : 
                    for i in range(len(BS_Eyebrows)) : 
                        self.SetTransform(
                            CONT_Eyebrows[i], BS_Eyebrows[i],
                            length_value=0.2
                        )
                    self.SetTransform(
                        CONT_Eyebrows[-1], DF_Eyebrows[-1], 
                        length_value=0.2, only_tail=True
                    )
                
                # Move Cejas
                MV_Eyebrows = self.GetBonesToRange(
                    f"mov_eyebrows_{type}", 4, mode="EDIT"
                )
                MV_SubEyebrows = self.GetBonesToRange(
                    f"mov_subeyebrows_{type}", 4, mode="EDIT"
                )
                if MV_Eyebrows and MV_SubEyebrows :
                    Length : float = 0 
                    for bone in BS_Eyebrows:
                        Length += bone.length
                        
                    for i in range(4) : 
                        MV_Eyebrows[i].head = BS_Eyebrows[i].head
                        MV_Eyebrows[i].tail = BS_Eyebrows[i].head
                        MV_Eyebrows[i].roll = 0
                        MV_Eyebrows[i].length = (Length/len(BS_Eyebrows))/2
                        
                        MV_SubEyebrows[i].head = BS_Eyebrows[i].head
                        MV_SubEyebrows[i].tail = BS_Eyebrows[i].head
                        MV_SubEyebrows[i].roll = 0
                        MV_SubEyebrows[i].length = (Length/len(BS_Eyebrows))/2
                
                # Mov SubCejas
                MV_Eyebrows = self.GetBone(f"mov_eyebrows_{type}", mode="EDIT")
                MV_SubEyebrows = self.GetBone(f"mov_subeyebrows_{type}", mode="EDIT")
                if MV_Eyebrows and MV_SubEyelids : 
                    
                    local_Head = (BS_Eyebrows[-2].head + BS_Eyebrows[-2].tail)/2
                    Length : float = 0 
                    for bone in BS_Eyebrows:
                        Length += bone.length
                        
                    MV_Eyebrows.head = local_Head
                    MV_Eyebrows.tail = local_Head
                    MV_Eyebrows.roll = 0
                    MV_Eyebrows.length = (Length/len(BS_Eyebrows))/2
                    
                    MV_SubEyebrows.head = local_Head
                    MV_SubEyebrows.tail = local_Head
                    MV_SubEyebrows.roll = 0
                    MV_SubEyebrows.length = (Length/len(BS_Eyebrows))/2

                Eyebrows = self.GetBone(f"eyebrows", mode="EDIT")
                if Eyebrows : 
                    Length : float = 0 
                    for bone in BS_Eyebrows:
                        Length += bone.length
                    Eyebrows.head = BS_Eyebrows[-1].tail
                    Eyebrows.tail = BS_Eyebrows[-1].tail
                    Eyebrows.roll = 0
                    Eyebrows.length = (Length/len(BS_Eyebrows))/2
                
            # SubCejas
            BS_SubEyebrows = self.GetBones(
                getattr(self, f"NE_Subeyebrows_{type}"), mode="EDIT"
            )
            
            if BS_SubEyebrows : 
                
                # Def SubCejas
                Def_SubCejas = self.GetBonesToRange(
                    f"def_subeyebrows_{type}", 3, mode="EDIT"
                )

                if Def_SubCejas : 
                    for i, bone in enumerate(Def_SubCejas) : 
                        self.SetTransform(bone, BS_SubEyebrows[i])
        
        # Eyes
        Eyes = self.GetBones(["eye_L", "eye_R"], mode="EDIT")
        Eye = self.GetBones(["eyes", "subeyes", "subeyes.001", "subeyes.002"], mode="EDIT")  
        if Eyes and Eye: 
            Local_Head = (
                    (Eyes[0].head[0] + Eyes[1].head[0]) / 2,
                    (Eyes[0].head[1] + Eyes[1].head[1]) / 2,
                    Eyes[0].head[2]
                )
            Local_Tail = (
                (Eyes[0].tail[0] + Eyes[1].tail[0]) / 2,
                (Eyes[0].tail[1] + Eyes[1].tail[1]) / 2,
                Eyes[0].tail[2]
            ) 
            for bone in Eye:
                bone.head, bone.tail = Local_Head, Local_Tail
            head = Eye[0].head.copy()
            for bone in Eyes:
                head.x , head.y, head.z = bone.head.x, head.y, bone.head.z
                bone.head = head
                bone.tail = head + self.GetWorldNormal()
                bone.roll = 0
                length : float = 0
                for b in self.GetBones(["base_rot_eye_L", "base_rot_eye_R"], mode="EDIT"):
                    length += b.length
                bone.length = length / 2
        
        # MED Face
        for direction in ["UP", "DOWN"]:
            BS_MEdFace = self.GetBones(
                getattr(self, f"NE_Medface_{direction}"), mode="EDIT"
            )
            if BS_MEdFace : 
                
                # Def MEdFace
                
                Def_MedFace = self.GetBonesToRange(
                    f"def_medface_{direction}",
                    4 if direction == "UP" else 2,
                    mode="EDIT"    
                )
                if Def_MedFace : 
                    self.SetTransformToBones(Def_MedFace, BS_MEdFace)
                
                #Control MedFace
                
                Cont_MedFace = self.GetBonesToRange(
                    f"cont_medface_{direction}", 
                    5 if direction == "UP" else 3,
                    mode="EDIT"
                )
                
                if Cont_MedFace : 
                    for i in range(4 if direction == "UP" else 2):
                        self.SetTransform(Cont_MedFace[i], BS_MEdFace[i], length_value=0.2)
                    self.SetTransform(Cont_MedFace[-1], BS_MEdFace[-1], length_value=0.2, only_tail=True)

        # Nose
        
        for type in ["R", "L"] : 
            BS_Nose = self.GetBones(
                getattr(self, f"NE_Nose_{type}"), mode="EDIT"
            )
            if BS_Nose : 
                # Def
                Def_Nose = self.GetBonesToRange(
                    f"def_nose_{type}", Range=3, mode="EDIT"
                )
                if Def_Nose : 
                    self.SetTransformToBones(Def_Nose, BS_Nose)

                # Control 
                Cont_Nose = self.GetBonesToRange(
                    f"cont_nose_{type}", Range=4, mode="EDIT"
                )
                if Cont_Nose :
                    for i in range(3) : 
                        self.SetTransform(Cont_Nose[i], BS_Nose[i], length_value=0.2)
                    self.SetTransform(Cont_Nose[-1], BS_Nose[-1], length_value=0.2, only_tail=True)

                Cont_SubNose = self.GetBone(
                    f"cont_subnose_{type}", mode="EDIT"
                ) 
                if Cont_SubNose :
                    Local_Base = self.GetBone(
                            f"base_cheekbone_UP_{type}.004", mode="EDIT"
                    )
                    Cont_SubNose.head = Local_Base.tail
                    Cont_SubNose.tail = Local_Base.head
                    Cont_SubNose.roll = 0
                    Cont_SubNose.length /= 2
                
                Cont_Nose = self.GetBone(
                    f"cont_nose_{type}", mode="EDIT"
                )
                if Cont_Nose : 
                    Local_Base = self.GetBone(
                        f"base_nose_{type}.001", mode="EDIT"
                    )
                    Cont_Nose.head = Local_Base.tail
                    Cont_Nose.tail = Local_Base.tail + self.GetWorldNormal()
                    Cont_Nose.roll = 0 
                    Cont_Nose.length = Local_Base.length/2
                
        
        Nose = self.GetBones(
            ["nose", "rot_subnose", "rot_nose"], mode="EDIT"
        )        
        
        if Nose :
            local_Base = self.GetBone(f"base_medface_UP.003", mode="EDIT")
            local_head = (self.GetBone(f"cont_nose_L", mode="EDIT").head + self.GetBone(f"cont_nose_R", mode="EDIT").head ) / 2
            local_tail = local_Base.tail
            for bone in Nose :
                bone.head, bone.tail = local_head, local_tail
                bone.roll = 0
                bone.length = local_Base.length / 2
        
        Cont_Nose = self.GetBone(
            f"cont_nose", mode="EDIT"
        )
        if Cont_Nose : 
            Local_Base = self.GetBone("base_medface_UP.003", mode="EDIT")
            Cont_Nose.head = Local_Base.tail
            Cont_Nose.tail = Local_Base.tail + self.GetWorldNormal()
            Cont_Nose.roll = 0
            Cont_Nose.length = Local_Base.length / 2
                
        # Pomulos 
        
        for type in ["R", "L"] : 
            for dir in ["UP", "DOWN"] : 
                BS_Cheekbone = self.GetBonesToRange(
                    f"base_cheekbone_{dir}_{type}", Range=4 if dir == "UP" else 3, mode="EDIT"
                )
                if BS_Cheekbone : 
                    # Def
                    Def_Cheekbone = self.GetBonesToRange(
                        f"def_cheekbone_{dir}_{type}", Range=4 if dir == "UP" else 3, mode="EDIT"
                    )
                    
                    if Def_Cheekbone : 
                        self.SetTransformToBones(Def_Cheekbone, BS_Cheekbone)
                    
                    # Control 
                    Cont_Cheekbone = self.GetBonesToRange(
                        f"cont_cheekbone_{dir}_{type}", Range=5 if dir == "UP" else 4, mode="EDIT"
                    )
                    if Cont_Cheekbone : 
                        for i in range(4 if dir == "UP" else 3):
                            self.SetTransform(Cont_Cheekbone[i], BS_Cheekbone[i], length_value=0.2)
                        self.SetTransform(
                            Cont_Cheekbone[-1], BS_Cheekbone[-1], length_value=0.2, only_tail=True
                        )  
        
        # Quijada
        
        for type in ["R", "L"] : 
            BS_Jaw = self.GetBonesToRange(
                f"base_jaw_{type}", 4, mode="EDIT"
            )
            if BS_Jaw :
                
                # DEf 
                Def_Jaw = self.GetBonesToRange(
                    f"def_jaw_{type}", 4, mode="EDIT"
                )
                if Def_Jaw : 
                    self.SetTransformToBones(Def_Jaw, BS_Jaw)
                
                # Control
                Cont_Jaw = self.GetBonesToRange(
                    f"cont_jaw_{type}", 5, mode="EDIT"
                )
                if Cont_Jaw :
                    for i in range(4) :
                        self.SetTransform(
                            Cont_Jaw[i], BS_Jaw[i], length_value=0.2
                        )
                    self.SetTransform(
                            Cont_Jaw[-1], BS_Jaw[-1], length_value=0.2, only_tail=True
                    )
        
        # Orejas

        for type in ["R", "L"] : 
            BS_Ear = self.GetBonesToRange(
                f"base_ear_{type}", 5, mode="EDIT"
            )
            if BS_Ear : 
                
                # DEF
                Def_Ear = self.GetBonesToRange(
                    f"def_ear_{type}", 5, mode="EDIT"
                )
                if Def_Ear : 
                    self.SetTransformToBones(Def_Ear, BS_Ear)
                
                # Control
                Cont_Ear = self.GetBonesToRange(
                    f"cont_ear_{type}", 6, mode="EDIT"
                )
                
                if Cont_Ear : 
                    for i in range(5) : 
                        self.SetTransform(Cont_Ear[i], BS_Ear[i], length_value=0.2)
                    self.SetTransform(Cont_Ear[-1], BS_Ear[-1], length_value=0.2, only_tail=True)
                
                Ear = self.GetBone(
                    f"ear_{type}", mode="EDIT"
                )
                if Ear : 
                    Local_Head = (BS_Ear[-1].head + BS_Ear[-1].tail) / 2
                    Ear.head = Local_Head 
                    Ear.tail = Local_Head + self.GetWorldNormal()
                    Ear.length = BS_Ear[-1].length / 2
                    Ear.roll = 0
                
                Rot_Ear = self.GetBone(
                    f"rot_ear_{type}", mode="EDIT"
                )
                if Rot_Ear : 
                    Local_Head = (BS_Ear[-1].head + BS_Ear[-1].tail) / 2
                    Local_Tail = (BS_Ear[1].head + BS_Ear[1].tail) / 2
                    Rot_Ear.head = Local_Head 
                    Rot_Ear.tail = Local_Tail
                    Rot_Ear.length = BS_Ear[-1].length / 2
                    Rot_Ear.roll = 0
                
                Cont_Ear = self.GetBone(
                    f"cont_ear_{type}", mode="EDIT"
                )
                
                if Cont_Ear : 
                    Local_Head = (BS_Ear[1].head + BS_Ear[1].tail) / 2
                    Cont_Ear.head = Local_Head 
                    Cont_Ear.tail = Local_Head + self.GetWorldNormal()
                    Cont_Ear.length = BS_Ear[2].length / 2
                    Cont_Ear.roll = 0
                
        # Boca
        for dir in ["UP", "DOWN"] : 
            for type in ["R", "L"] : 
                BS_Mouth= self.GetBonesToRange(
                    f"base_mouth_{dir}_{type}", 3, mode="EDIT"
                )
                if BS_Mouth :
                    
                    # Def 
                    Def_Mouth = self.GetBonesToRange(
                        f"def_mouth_{dir}_{type}", 3, mode="EDIT"
                    )
                    
                    if Def_Mouth :
                        self.SetTransformToBones(
                            Def_Mouth, BS_Mouth
                        )
                    
                    # Control
                    Cont_Mouth = self.GetBonesToRange(
                        f"cont_mouth_{dir}_{type}", 4, mode="EDIT"
                    )
                    if Cont_Mouth : 
                        for i in range(3) :
                            self.SetTransform(Cont_Mouth[i], BS_Mouth[i], length_value=0.2)
                        self.SetTransform(Cont_Mouth[-1], BS_Mouth[-1], length_value=0.2, only_tail=True)            
                    # Control 
                    Cont_SubMouth = self.GetBonesToRange(
                        f"cont_submouth_{dir}_{type}", 3, mode="EDIT"
                    )
                    
                    if Cont_SubMouth :
                        for i in range(2) :
                            
                            Cont_SubMouth[i].head = BS_Mouth[i+1].head 
                            Cont_SubMouth[i].tail = BS_Mouth[i+1].tail + self.GetWorldNormal()
                            Cont_SubMouth[i].roll = 0
                            Cont_SubMouth[i].length = BS_Mouth[i+1].length/1.5
                        
                        Cont_SubMouth[-1].head = BS_Mouth[-1].tail
                        Cont_SubMouth[-1].tail = BS_Mouth[-1].tail + self.GetWorldNormal()
                        Cont_SubMouth[-1].roll = 0
                        Cont_SubMouth[-1].length = BS_Mouth[-1].length/1.5
                            
            BS_Mouth = self.GetBone(
                f"base_mouth_{dir}_L.001", mode="EDIT"
            )
            if BS_Mouth :
                
                # Control 
                Cont_SubMouth = self.GetBone(
                    f"cont_submouth_{dir}", mode="EDIT"
                )
                
                if Cont_SubMouth :
                    Cont_SubMouth.head = BS_Mouth.head 
                    Cont_SubMouth.tail = BS_Mouth.tail + self.GetWorldNormal()
                    Cont_SubMouth.roll = 0
                    Cont_SubMouth.length = BS_Mouth.length/1.5
            
        # Rot
        
        Rot_Mouth = self.GetBones(
            ["rot_mouth", "rot_mouth_DOWN", "rot_mouth_UP", 
             "rot_mouth_MED", "rot_submouth_MED.001", "rot_submouth_MED.002", "rot_submouth_MED"], 
            mode="EDIT"
        )
        if Rot_Mouth : 
            if self.GetBone(f"cont_cheekbone_DOWN_{type}.003", mode="EDIT"):
                Local_Head = mathutils.Vector((0, 0, 0))
                Local_Tail = mathutils.Vector((0, 0, 0))
                for type in ["R", "L"] :
                    Local_Head += self.GetBone(f"cont_cheekbone_DOWN_{type}.003", mode="EDIT").head
                    Local_Head += self.GetBone(f"cont_jaw_{type}.003", mode="EDIT").head
                    Local_Tail += self.GetBone(f"base_mouth_UP_{type}.001", mode="EDIT").head
                    Local_Tail += self.GetBone(f"base_mouth_DOWN_{type}.001", mode="EDIT").head
                
                Local_Head /= 4
                Local_Tail /= 4
                
                for bone in Rot_Mouth :
                    bone.head = Local_Head
                    bone.tail = Local_Tail
                    bone.roll = 0
            
        
        # General Boca
        Mouth = self.GetBones(
            ["mouth", "mouth_UP", "mouth_DOWN", "submouth_UP", "submouth_DOWN", ], mode="EDIT"
        )
        
        if Mouth :
            
            Local_Head = mathutils.Vector((0, 0, 0))
            Local_Head += self.GetBone(f"base_mouth_UP_L.001", mode="EDIT").head
            Local_Head += self.GetBone(f"base_mouth_DOWN_L.001", mode="EDIT").head
            for bone in Mouth :
                bone.head = (Local_Head / 2)
                bone.tail = (Local_Head / 2) + self.GetWorldNormal()
                bone.roll = 0
                bone.length = self.GetBone(f"base_mouth_DOWN_L.001", mode="EDIT").length/2
        
        # Sub Mauth
        for type in ["R", "L"] : 
            def GetLocalHead(n : str = ".001"):
                local_Head = mathutils.Vector((0, 0, 0))
                for dir in ["UP", "DOWN"] : 
                    Local_Base = self.GetBone(f"base_mouth_{dir}_{type}{n}", mode="EDIT")
                    if local_Base :
                        local_Head += Local_Base.tail
                return local_Head/2
            
            SubMouth = self.GetBonesToRange(
                f"submouth_{type}", 3, mode="EDIT"
            )
            
            if SubMouth : 
                for i in range(3):
                    SubMouth[i].head = GetLocalHead(f".00{i+1}")
                    SubMouth[i].tail = GetLocalHead(f".00{i+1}") + self.GetWorldNormal()
                    SubMouth[i].length /= 100
            
            Mouth = self.GetBone(f"mouth_{type}", mode="EDIT")
            if Mouth :
                Mouth.head = GetLocalHead(f".003")
                Mouth.tail = GetLocalHead(f".003") + self.GetWorldNormal()
                Mouth.length = self.GetBone("base_cheekbone_DOWN_L.001", mode="EDIT").length / 3
                    
        # Quijada
        Jaw = self.GetBones(
            ["cont_subjaw", "jaw", "subjaw",], mode="EDIT"
        )
        if Jaw :
            Local_Base_1 = self.GetBones(["base_jaw_L.002", "base_jaw_R.002"], mode="EDIT")
            Local_Base_2 = self.GetBones(["base_jaw_L.004", "base_jaw_R.004"], mode="EDIT")
            if Local_Base_1 and Local_Base_2:
                Local_Head = (Local_Base_1[0].head + Local_Base_1[1].head) / 2
                Local_Tail = (Local_Base_2[0].tail + Local_Base_2[1].tail) / 2
                for bone in Jaw:
                    bone.head = Local_Head
                    bone.tail = Local_Tail
                    bone.roll = 0

            
        # Dientes 
        for dir in ["UP", "DOWN"] : 
            for type in ["R", "L"] : 
                Bs_Tooth = self.GetBonesToRange(
                    f"base_tooth_{dir}_{type}", 3, mode="EDIT"
                )
                
                if Bs_Tooth :
                    
                    # Def
                    Def_Tooth = self.GetBonesToRange(
                    f"def_tooth_{dir}_{type}", 3, mode="EDIT"
                    )
                    if Def_Tooth : 
                        self.SetTransformToBones(
                            Def_Tooth, Bs_Tooth
                        )
                        
                    # Control
                    Cont_Tooth = self.GetBonesToRange(
                    f"cont_tooth_{dir}_{type}", 4, mode="EDIT"
                    )
                    if Cont_Tooth : 
                        for i in range(3):
                            self.SetTransform(
                                Cont_Tooth[i], Bs_Tooth[i], length_value=0.2
                            )
                        self.SetTransform(
                            Cont_Tooth[-1], Bs_Tooth[-1], length_value=0.2, only_tail=True
                        )

                    Cont_Tooth = self.GetBone(
                        f"cont_tooth_{dir}", mode="EDIT"
                    )
                    if Cont_Tooth :
                        
                        Cont_Tooth.head = Bs_Tooth[0].head
                        Cont_Tooth.tail = Bs_Tooth[0].head + self.GetWorldNormal()
                        Cont_Tooth.roll = 0 
                        Cont_Tooth.length = Bs_Tooth[0].length / 4
            
            
            Bs_Tooth = self.GetBones(
                    [f"base_tooth_{dir}_L.003", f"base_tooth_{dir}_R.003"], mode="EDIT"
            )
            if Bs_Tooth :
                
                Tooth = self.GetBone(
                    f"tooth_{dir}", mode="EDIT"
                )
                if Tooth :
                    Local_Head = (Bs_Tooth[0].tail + Bs_Tooth[1].tail) / 2
                    Tooth.head = Local_Head
                    Tooth.tail = Local_Head + self.GetWorldNormal()
                    Tooth.roll = 0 
                    Local_Length = self.GetDistancia3d(Bs_Tooth[0].tail, Bs_Tooth[1].tail)
                    Tooth.length = Local_Length/2

        
        Bs_Tongue = self.GetBonesToRange(
            f"base_tongue", 3, mode="EDIT"
        )
        if Bs_Tongue :
            
            # Def 
            Def_Tongue = self.GetBonesToRange(
                f"def_tongue", 3, mode="EDIT"
            )
            if Def_Tongue : 
                self.SetTransformToBones(Def_Tongue, Bs_Tongue)
            
            # Cont 
            Cont_Tongue = self.GetBonesToRange(
                f"cont_tongue", 4, mode="EDIT"
            ) 
            if Cont_Tongue:
                for i in range(3):
                    self.SetTransform(
                        Cont_Tongue[i], Bs_Tongue[i], length_value=0.2
                    )
                self.SetTransform(
                        Cont_Tongue[-1], Bs_Tongue[-1], length_value=0.2, only_tail=True
                    )
                
            # Rot
            Rot_Tongue = self.GetBonesToRange(
                f"rot_tongue", 3, mode="EDIT"
            )
            if Rot_Tongue : 
                self.SetTransformToBones(Rot_Tongue, Bs_Tongue)
            
            # Fk 
            Fk_Tongue = self.GetBonesToRange(
                f"fk_tongue", 3, mode="EDIT"
            )
            if Fk_Tongue : 
                self.SetTransformToBones(Fk_Tongue, Bs_Tongue)
            
            RotFk_Tongue = self.GetBone(
                f"rotfk_tongue", mode="EDIT"
            )
            if RotFk_Tongue :
                RotFk_Tongue.head = Bs_Tongue[0].head
                RotFk_Tongue.tail = Bs_Tongue[-1].tail
                RotFk_Tongue.roll = Bs_Tongue[0].roll
        
            #Root
            Root_Tongue = self.GetBone(
                f"root_tongue", mode="EDIT"
            )
            if Root_Tongue :
                self.SetTransform(Root_Tongue, Bs_Tongue[0], length_value=0.5)
            
            #IK
            Ik_Tongue = self.GetBonesToRange(
                f"ik_tongue", 4, mode="EDIT"
            )
            if Ik_Tongue:
                for i in range(3) : 
                    self.SetTransform(
                        Ik_Tongue[i], Bs_Tongue[i]
                    )
                self.SetTransform(
                        Ik_Tongue[-1], Bs_Tongue[-1], only_tail=True
                    )
        
        
        
        self.SetMode(mode="POSE")
        # Fk 
        Fk_Tongue = self.GetBonesToRange(
            f"fk_tongue", 3, mode="POSE"
        )
        if Fk_Tongue : 
            for bone in Fk_Tongue:
                bone.custom_shape_translation[1] = bone.length/2

        self.ResetEye()
        self.ResetALLBoneStretchTo()
        self.ResetAllign()
        self.ResetHeadDown()

    def ResetHeadDown(self) :
        self.SetMode(mode="EDIT")
        
        bs_bone = self.GetBone("base_spine.006", mode="EDIT")
        head_down_bones_names =["head_down", "cont_head_down.001", "cont_head_down.002"] 
        bone_sons = [
                "jaw", "mouth", "cont_jaw_L.002", "cont_jaw_R.002", 
                "rot_mouth", "subjaw", "rot_submouth_MED.001", 
                "rot_submouth_MED.002", 
                
            ]
        for dir in ["R", "L"] :
            bone_sons.append(f"cont_cheekbone_DOWN_{dir}.003",)
            bone_sons.append(f"cont_cheekbone_UP_{dir}.002",)
            bone_sons.append(f"cont_cheekbone_UP_{dir}.003")
            
        if bs_bone :
            head_down = self.GetBones(head_down_bones_names, mode="EDIT")
            if not head_down :
                hd = self.CreateBone(head_down_bones_names[0])
                hd_1 = self.CreateBone(head_down_bones_names[1])
                hd_2 = self.CreateBone(head_down_bones_names[2])
                head_down = [hd, hd_1, hd_2]
            
            head = (bs_bone.head + bs_bone.tail) / 2
            tail = bs_bone.head 
            
            head_down[0].head = head
            head_down[0].tail = tail
            head_down[0].roll = bs_bone.roll
            head_down[0].length = bs_bone.length
            
            self.SetTransform(head_down[1], head_down[0], length_value= 0.25)
            self.SetTransform(head_down[2], head_down[0], length_value= 0.25, only_tail=True)
            
            head_down[0].parent = head_down[1]
            for b in [head_down[1], head_down[2]] :
                b.parent = self.GetBone("def_spine.006", mode="EDIT")
                
            self.SetDeform(head_down, False)
            self.SetColorBone(head_down[2], "THEME02")
            
            self.BoneSetCollection("Head", head_down[2])
            
            self.BoneSetCollection("Control_Bone", head_down[0])
            self.BoneSetCollection("Control_Bone", head_down[1])
            
            bones_son = self.GetBones(bone_sons, mode="EDIT")

            for b in bones_son :
                b.parent = head_down[0]
                
        self.SetMode("POSE") 
        head_down = self.GetBones(head_down_bones_names, mode="POSE")
        shape = None
        shape_bone = self.GetBone("cont_spine.007", mode="POSE")
        if shape_bone : 
            shape = shape_bone.custom_shape
        cname = "STRETCH_TO_HEADDOWN"
        
        if head_down:
 
            c = head_down[0].constraints.get(cname)
            if not c :
                c = head_down[0].constraints.new(type='STRETCH_TO')
                c.name = cname
            c.target = self.GetActiveObject()
            c.subtarget = head_down[2].name
            c.use_bulge_min = True
            head_down[2].custom_shape = shape
            head_down[2].custom_shape_transform = self.GetBone("cont_medface_DOWN.002", mode="POSE")

            for i in range(3) :
                head_down[2].lock_rotation[i] = True
                head_down[2].lock_scale[i] = True
                head_down[2].custom_shape_scale_xyz[i] = 0.5

    def ResetEye(self) :
        self.SetMode(mode="EDIT")
        for t in ["R", "L"] :
            bs_eye = self.GetBone(f"base_rot_eye_{t}", "EDIT")
            if not bs_eye : return
            save_length = bs_eye.length
            rot_eye = self.GetBone(f"rot_eye_{t}", "EDIT")
            if rot_eye :
                self.SetTransform(rot_eye, bs_eye)
            cont_eye = self.GetBone(f"eye_{t}", "EDIT")
            bs_eye.length *= 10
            if cont_eye : 
                cont_eye.head = bs_eye.tail 
                cont_eye.tail = bs_eye.tail + (self.GetWorldNormal("z"))
                cont_eye.length = save_length
            bs_eye.length = save_length
            
        cont_eyes = [self.GetBone(f"eye_L", "EDIT"), self.GetBone(f"eye_R", "EDIT")]
        if cont_eyes :
            eyes = self.GetBones(["eyes","subeyes", "subeyes.001", "subeyes.002"], mode="EDIT")
            if eyes :
                head = (cont_eyes[0].head + cont_eyes[1].head) / 2
                tail = (cont_eyes[0].tail + cont_eyes[1].tail ) / 2
                for b in eyes :
                    b.head = head
                    b.tail = tail 
                    b.length = save_length
            
    def ResetCartoonFace(self) :
        
        self.SetMode(mode="EDIT")
        # Head 
        BS_Head = self.GetBone("base_head", mode="EDIT")
        if BS_Head :
            CONT_head = self.GetBonesToRange(Bone_Name="cont_def_head", Range=2, mode="EDIT")
            if CONT_head :
                self.SetTransform(CONT_head[0], BS_Head, length_value=0.2)
                self.SetTransform(CONT_head[1], BS_Head, length_value=0.2, only_tail=True)
            
            DEF_Head = self.GetBone(Bone_Name="def_head", mode="EDIT")
            if DEF_Head : 
                self.SetTransform(DEF_Head, BS_Head)
            
            HEAD = self.GetBone("head", mode="EDIT")
            if HEAD : 
                self.SetTransform(HEAD, BS_Head)
        
        # Eyes
        for type in ["R", "L"] :
            for dir in ["UP", "DOWN", "MED"] : 
                BS_Eyelid = self.GetBonesToRange(
                Bone_Name=f"base_eyelid_{dir}_{type}", Range=3 if dir != "MED" else 2, mode="EDIT"
                )
                if BS_Eyelid : 
                    DEF_Eyelid = self.GetBonesToRange(
                    Bone_Name=f"def_eyelid_{dir}_{type}", Range=3 if dir != "MED" else 2, mode="EDIT"
                    )
                    if DEF_Eyelid :
                        self.SetTransformToBones(DEF_Eyelid, BS_Eyelid)

                    if dir != "MED" :
                        CONT_Eyelid = self.GetBone(Bone_Name="cont_eyelid_{dir}_{type}", mode="EDIT")
                        if CONT_Eyelid : 
                            self.SetTransform(CONT_Eyelid, BS_Eyelid[1])
            # ROT Eye
            BASE_rot_Eye = self.GetBone(f"base_rot_eye_{type}", mode="EDIT")
            if BASE_rot_Eye :
                DEF_rot_Eye = self.GetBone(f"def_rot_eye_{type}", mode="EDIT")
                if DEF_rot_Eye :
                    self.SetTransform(DEF_rot_Eye, BASE_rot_Eye)
                    
            for dir in ["UP", "DOWN"] : 
                ROT_eyelid = self.GetBonesToRange(
                    Bone_Name=f"rot_eyelid_{dir}_{type}", Range=2, mode="EDIT"
                )
                if ROT_eyelid :
                    for i in range(2) :
                        ROT_eyelid[i].head = BASE_rot_Eye.head
                        ROT_eyelid[i].tail = self.GetBone(f"base_eyelid_{dir}_{type}.002", mode="EDIT").head
                
                # Cont Eye
                CONT_eyelid = self.GetBone(f"cont_eyelid_{dir}_{type}", mode="EDIT")
                if CONT_eyelid : 
                    self.SetTransform(CONT_eyelid, self.GetBone(f"base_eyelid_{dir}_{type}.002", mode="EDIT"), length_value=10)
        
            # Cont General Eye 

            head = self.CreateVector(0, 0, 0)
            if self.GetBone(Bone_Name="base_eyelid_UP_L.002") and self.GetBone(Bone_Name="base_eyelid_DOWN_L.002") :
                length = self.GetDistancia3d(
                    self.GetBone(Bone_Name="base_eyelid_UP_L.002").head,
                    self.GetBone(Bone_Name="base_eyelid_DOWN_L.002").head,
                )
            else :
                length = 0
            for dir in ["UP", "DOWN", "MED"] :
                BS_Eyelid = self.GetBonesToRange(
                    Bone_Name=f"base_eyelid_{dir}_{type}", Range=3 if dir != "MED" else 2, mode="EDIT"
                    )
                for bone in BS_Eyelid:
                    head += bone.head
            
            head /= 8
            CONT_Eye = self.GetBone(Bone_Name=f"cont_eye_{type}", mode="EDIT")
            if CONT_Eye : 
                CONT_Eye.head = head
                CONT_Eye.tail = head + self.GetWorldNormal()
                CONT_Eye.length = length/2
        
        for dir in ["UP", "DOWN"] : 
            #Mouth 
            BS_Mouth = self.GetBone(Bone_Name=f"base_mouth_{dir}.001", mode="EDIT")
            if BS_Mouth : 
                DEF_Mouth = self.GetBone(Bone_Name=f"def_mouth_{dir}.001", mode="EDIT")
                if DEF_Mouth : 
                    self.SetTransform(DEF_Mouth, BS_Mouth)
                    
                Mouth = self.GetBonesToRange(Bone_Name=f"mouth_{dir}", Range=2, mode="EDIT")
                print(Mouth)
                if Mouth : 
                    
                    for bone in Mouth:
                        self.SetTransform(bone, BS_Mouth, length_value=6)

            for type in ["L", "R"] : 
                BS_Mouth = self.GetBonesToRange(Bone_Name=f"base_mouth_{dir}_{type}", Range=3, mode="EDIT")
                DEF_Mouth = self.GetBonesToRange(Bone_Name=f"def_mouth_{dir}_{type}", Range=3, mode="EDIT")
                if DEF_Mouth : 
                    self.SetTransformToBones(DEF_Mouth, BS_Mouth)
                

        #Mouth MED
        for type in ["L", "R"] : 
            BS_Mouth = self.GetBone(Bone_Name=f"base_mouth_MED_{type}", mode="EDIT")
            DEF_Mouth = self.GetBone(Bone_Name=f"def_mouth_MED_{type}.001", mode="EDIT")
            if DEF_Mouth : 
                self.SetTransform(DEF_Mouth, BS_Mouth)
            Mouth = self.GetBone(Bone_Name=f"mouth_MED_{type}", mode="EDIT")
            if Mouth : 
                self.SetTransform(Mouth, BS_Mouth)
            MED_Mouth = self.GetBonesToRange(Bone_Name=f"mouth_MED_{type}", Range=3, mode="EDIT")
            if MED_Mouth : 
                Bone_UP = self.GetBonesToRange(Bone_Name=f"base_mouth_UP_{type}", Range=3, mode="EDIT")
                Bone_DOWN = self.GetBonesToRange(Bone_Name=f"base_mouth_DOWN_{type}", Range=3, mode="EDIT")
                for i in range(3):
                    head = (
                        Bone_UP[i].head +
                        Bone_DOWN[i].head
                    )/2
                    MED_Mouth[i].head = head
                    MED_Mouth[i].tail = head + self.GetWorldNormal()
                    MED_Mouth[i].length = Bone_UP[i].length
        
        head = (self.GetBone(Bone_Name="base_mouth_UP.001", mode="EDIT").head + 
                self.GetBone(Bone_Name="base_mouth_DOWN.001", mode="EDIT").head) / 2
        
        Mouth = self.GetBone(Bone_Name="mouth", mode="EDIT")
        if Mouth : 
            Mouth.head = head
            Mouth.tail = head + self.GetWorldNormal()
            Mouth.length = self.GetBone(Bone_Name="base_mouth_UP.001", mode="EDIT").length * 6
        
        BS_ROT_Mouth = self.GetBone(Bone_Name="base_rot_mouth", mode="EDIT")
        if BS_ROT_Mouth : 
            for dir in ["UP", "DOWN", "MED"] :
                ROT_Mouth = self.GetBone(Bone_Name=f"rot_mouth_{dir}", mode="EDIT")  
                if ROT_Mouth :
                    ROT_Mouth.head = BS_ROT_Mouth.head 
                    if dir != "MED" : 
                        ROT_Mouth.tail = self.GetBone(Bone_Name=f"base_mouth_{dir}.001", mode="EDIT").head 
                    else:
                        ROT_Mouth.tail = (
                            self.GetBone(Bone_Name=f"base_mouth_UP.001", mode="EDIT").head  + 
                            self.GetBone(Bone_Name=f"base_mouth_DOWN.001", mode="EDIT").head  
                        ) / 2
                    ROT_Mouth.roll = 0
        ROT_Mouth = self.GetBone(Bone_Name="rot_mouth_UP", mode="EDIT")          
        if ROT_Mouth : 
            MED_Mouth = self.GetBone(Bone_Name="rot_mouth_MED.001", mode="EDIT")
            if MED_Mouth :
                self.SetTransform(MED_Mouth, ROT_Mouth, length_value=0.5) 
        
        
        for type in ["L", "R"] : 
            BS_Rot_Eye = self.GetBone(Bone_Name=f"base_rot_eye_{type}", mode="EDIT")
            if BS_Rot_Eye :
               Eye = self.GetBone(Bone_Name=f"eye_{type}", mode="EDIT") 
               if Eye :
                   
                    head = self.CreateVector(
                        BS_Rot_Eye.tail.x, 
                        (BS_Rot_Eye.tail.y - (BS_Rot_Eye.length*3)), 
                        BS_Rot_Eye.tail.z, 
                    )
                   
                    Eye.head = head
                    Eye.tail = head + self.GetWorldNormal()
                    Eye.length = BS_Rot_Eye.length/2
        
        Eye = self.GetBone(Bone_Name="eye", mode="EDIT")
        if Eye : 
            head = (
                self.GetBone(Bone_Name=f"eye_L", mode="EDIT").head + 
                self.GetBone(Bone_Name=f"eye_R", mode="EDIT").head
            ) / 2
            tail = (
                self.GetBone(Bone_Name=f"eye_L", mode="EDIT").tail + 
                self.GetBone(Bone_Name=f"eye_R", mode="EDIT").tail
            ) / 2
            Eye.head = head 
            Eye.tail = tail
        
        #Ear
        for type in ["L", "R"] : 
        
            BS_Ear = self.GetBone(Bone_Name=f"base_ear_{type}", mode="EDIT")
            if BS_Ear : 
                DF_Ear = self.GetBone(Bone_Name=f"def_ear_{type}", mode="EDIT")
                if DF_Ear : 
                    self.SetTransform(DF_Ear, BS_Ear)
                    
            CONT_Ear = self.GetBonesToRange(Bone_Name=f"cont_ear_{type}", Range=2, mode="EDIT")
            if CONT_Ear: 
                self.SetTransform(CONT_Ear[0], BS_Ear, length_value=0.2)
                self.SetTransform(CONT_Ear[1], BS_Ear, length_value=0.2, only_tail=True)

            Ear = self.GetBone(Bone_Name=f"ear_{type}", mode="EDIT")
            if Ear :
                self.SetTransform(Ear, BS_Ear)
            
            # Tooth 
            if self.GetBone(Bone_Name="base_tooth_UP_L.001", mode="EDIT") : 
                
                for dir in ["UP", "DOWN"] : 
                    BS_Tooth = self.GetBone(Bone_Name=f"base_tooth_{dir}_L.001", mode="EDIT")
                    DF_Tooth = self.GetBone(Bone_Name=f"def_Ctooth_{dir}", mode="EDIT")
                    if DF_Tooth : 
                        DF_Tooth.head = BS_Tooth.head
                        DF_Tooth.tail = BS_Tooth.head + self.GetWorldNormal()
                        DF_Tooth.length = BS_Tooth.length
                        
                    for type in ["R", "L"] : 
                        BS_Tooth = self.GetBonesToRange(Bone_Name=f"base_tooth_{dir}_{type}", Range=3, mode="EDIT")
                        if BS_Tooth : 
                            DF_Tooth = self.GetBonesToRange(
                                Bone_Name=f"def_Ctooth_{dir}_{type}", Range=3, mode="EDIT"
                            )
                            if DF_Tooth : 
                                for i in range(3) : 
                                    
                                    DF_Tooth[i].head = BS_Tooth[i].tail
                                    DF_Tooth[i].tail = BS_Tooth[i].tail + self.GetWorldNormal()
                                    DF_Tooth[i].length = BS_Tooth[i].length
                
                    head = (
                        self.GetBone(Bone_Name=f"base_tooth_{dir}_L.003", mode="EDIT").tail + 
                        self.GetBone(Bone_Name=f"base_tooth_{dir}_R.003", mode="EDIT").tail 
                        ) / 2

                    tail = self.GetBone(Bone_Name=f"base_tooth_{dir}_L.001", mode="EDIT").head
                    
                    Tooth = self.GetBone(Bone_Name=f"tooth_{dir}", mode="EDIT")
                    if Tooth : 
                        Tooth.head, Tooth.tail = head, tail
            
            
            #Tongue
            BS_Tongue = self.GetBonesToRange(Bone_Name="base_tongue", Range=3, mode="EDIT")
            if BS_Tongue : 
                DF_Tongue = self.GetBonesToRange(Bone_Name="def_tongue", Range=4, mode="EDIT")
                if DF_Tongue : 
                    for i in range(3) : 
                        self.SetTransform(DF_Tongue[i], BS_Tongue[i], length_value=0.8)
                    self.SetTransform(DF_Tongue[-1], BS_Tongue[-1], length_value=0.8, only_tail=True)
                FK_Tongue = self.GetBonesToRange(Bone_Name="fk_tongue", Range=3, mode="EDIT")
                if FK_Tongue : 
                    self.SetTransformToBones(FK_Tongue, BS_Tongue) 
        self.ResetALLBoneStretchTo()
        
    def ResetSpine(self) : 
        
        self.SetMode(mode="EDIT")
        BS_Spine = self.GetBonesToRange(
            f"base_spine", 6, mode="EDIT"
        )

        if BS_Spine : 
            
            Root_P = self.GetBone(f"root_head_properties", mode="EDIT") 
            if Root_P : 
                self.SetTransform(Root_P, BS_Spine[-1], length_value=0.4)
                
            # DEF
            Def_Spine = self.GetBonesToRange(
                f"def_spine", 6, mode="EDIT"
            )
            
            if Def_Spine : 
                self.SetTransformToBones(Def_Spine, BS_Spine)
            
            # Rot
            Rot_Spine = self.GetBone("rot_subspine", mode="EDIT")
            if Rot_Spine : 
                Rot_Spine.head = BS_Spine[-2].head
                Rot_Spine.tail = BS_Spine[-2].head + self.GetWorldNormal()
                Rot_Spine.roll = 0 
                Rot_Spine.length = BS_Spine[-2].length / 2
                
            
            # Control
            Cont_Spine = self.GetBonesToRange(
                f"cont_spine", 5, mode="EDIT"
            )
            if Cont_Spine : 
                for i in range(4):
                    self.SetTransform(Cont_Spine[i], BS_Spine[i], length_value=0.2)
                self.SetTransform(Cont_Spine[-1], BS_Spine[3], length_value=0.2, only_tail=True)

            Cont_SubSpine = self.GetBonesToRange(
                f"cont_subspine", 2, mode="EDIT"
            )
            if Cont_SubSpine :
                for bone in Cont_SubSpine :
                    bone.head = BS_Spine[2].head
                    bone.tail = BS_Spine[2].head + self.GetWorldNormal()
                    bone.roll = 0 
                    bone.length = BS_Spine[2].length / 4
            
            #ROT
            Rot_Spine_DOWN = self.GetBonesToRange(
                f"rot_spine_DOWN", 2, mode="EDIT"
            ) 
            
            if Rot_Spine_DOWN :
                self.SetTransform(Rot_Spine_DOWN[0], BS_Spine[1], invert_head_tail=True)
                self.SetTransform(Rot_Spine_DOWN[1], BS_Spine[0], invert_head_tail=True)
                
            Rot_Spine_UP = self.GetBonesToRange(
                f"rot_spine_UP", 2, mode="EDIT"
            ) 
            
            if Rot_Spine_UP :
                self.SetTransform(Rot_Spine_UP[0], BS_Spine[2])
                self.SetTransform(Rot_Spine_UP[1], BS_Spine[3])

            # Hombros Caderas
            Shoulders = self.GetBone(f"shoulders", mode="EDIT")
            if Shoulders : 
                Shoulders.head = BS_Spine[2].head
                Shoulders.tail = BS_Spine[3].tail
                Shoulders.roll = 0
                
            hips = self.GetBone(f"hips", mode="EDIT")
            if hips : 
                hips.head = BS_Spine[1].tail
                hips.tail = BS_Spine[0].head
                hips.roll = 0
            
            

            #Head
            Cont_Spine = self.GetBones(
                ["cont_spine.006", "cont_spine.007", "cont_spine.008"], mode="EDIT"
            )
            if Cont_Spine :
                self.SetTransform(Cont_Spine[0], BS_Spine[4], length_value=0.2)
                self.SetTransform(Cont_Spine[1], BS_Spine[5], length_value=0.2)
                self.SetTransform(Cont_Spine[2], BS_Spine[5], length_value=0.2, only_tail=True)
            
            Head = self.GetBone(
                f"head", mode="EDIT"
            )
            if Head :
                self.SetTransform(Head, BS_Spine[5])
            Neck = self.GetBone(
                f"neck", mode="EDIT"
            )
            if Neck :
                self.SetTransform(Neck, BS_Spine[4])
            
            self.SetMode("POSE") 
            for dir in ["UP", "DOWN"]:
                Rot_Spine = self.GetBonesToRange(
                f"rot_spine_{dir}", 2, mode="POSE"
            ) 
                if Rot_Spine :
                    for bone in Rot_Spine:
                        bone.custom_shape_translation[1] = bone.length/2
        
            Shoulders = self.GetBone(f"shoulders", mode="POSE")
            if Shoulders :
                Shoulders.custom_shape_translation[1] = Shoulders.length/2
            hips = self.GetBone(f"hips", mode="POSE")
            if hips :
                hips.custom_shape_translation[1] = hips.length/2
            
            Head = self.GetBone(
                f"head", mode="POSE"
            )
            if Head : 
                Head.custom_shape_translation[1] = Head.length
            
            Neck = self.GetBone(
                f"neck", mode="POSE"
            )
            if Neck : 
                Neck.custom_shape_translation[1] = Neck.length/2
        
        self.SetMode(mode="EDIT")
        for type in ["R","L"]:
            BS_Shoulder = self.GetBonesToRange(
                f"base_shoulder_{type}", 2, mode="EDIT"
            )
            if BS_Spine : 
                
                # Def 
                Def_Shoulder = self.GetBonesToRange(
                    f"def_shoulder_{type}", 2 , mode="EDIT"
                )
                if Def_Shoulder :
                    self.SetTransformToBones(Def_Shoulder, BS_Shoulder)
                
                # Control 
                Cont_Shoulder = self.GetBonesToRange(
                    f"cont_shoulder_{type}", 2, "EDIT"
                )
                if Cont_Shoulder :
                    self.SetTransform(Cont_Shoulder[0], BS_Shoulder[1], length_value=0.2)
                    self.SetTransform(Cont_Shoulder[1], BS_Shoulder[1], length_value=0.2, only_tail=True)
                Shoulder = self.GetBone(
                    f"shoulder_{type}", "EDIT"
                )
                if Shoulder : 
                    self.SetTransform(Shoulder, BS_Shoulder[1])
              
            BS_Hip = self.GetBone(f"base_hip_{type}", mode="EDIT")
            #hip
            if BS_Hip : 
                
                # Def
                Def_Hip = self.GetBone(f"def_hip_{type}", mode="EDIT")
                if Def_Hip :
                    self.SetTransform(Def_Hip, BS_Hip)
                    
                # Control
                Cont_Hip = self.GetBone(f"cont_hip_{type}", mode="EDIT")
                if Cont_Hip :
                    self.SetTransform(Cont_Hip, BS_Hip, length_value=0.2, only_tail=True)
                
        self.ResetALLBoneStretchTo()
        
    def ResetArm(self, type : str = "R") : 
        
        self.SetMode("EDIT")
        BS_Arm = self.GetBonesToRange(
            f"base_arm_{type}", 3, mode="EDIT"
        )
        if not self.CheckIsBonesExisted([bone.name for bone in BS_Arm]) :
            return
        
        UPArm_1 = {
            "head" : BS_Arm[0].head,
            "tail" : (BS_Arm[0].head + BS_Arm[0].tail) / 2,
            "roll" : BS_Arm[0].roll
        }
        UPArm_2 = {
            "head" : (BS_Arm[0].head + BS_Arm[0].tail) / 2,
            "tail" : BS_Arm[0].tail,
            "roll" : BS_Arm[0].roll
        }
        
        DOWNArm_1 = {
            "head" : BS_Arm[1].head,
            "tail" : (BS_Arm[1].head + BS_Arm[1].tail) / 2,
            "roll" : BS_Arm[1].roll
        }
        DOWNArm_2 = {
            "head" : (BS_Arm[1].head + BS_Arm[1].tail) / 2,
            "tail" : BS_Arm[1].tail,
            "roll" : BS_Arm[1].roll
        }
        
        for dir in ["UP", "DOWN"] : 
            Def_Arm = self.GetBonesToRange(
                f"def_arm_{dir}_{type}", 2, mode="EDIT"
            )
            if Def_Arm :
                Def_Arm[0].head = UPArm_1["head"] if dir == "UP" else DOWNArm_1["head"]
                Def_Arm[0].tail = UPArm_1["tail"] if dir == "UP" else DOWNArm_1["tail"]
                Def_Arm[0].roll = UPArm_1["roll"] if dir == "UP" else DOWNArm_1["roll"]
        
                Def_Arm[1].head = UPArm_2["head"] if dir == "UP" else DOWNArm_2["head"]
                Def_Arm[1].tail = UPArm_2["tail"] if dir == "UP" else DOWNArm_2["tail"]
                Def_Arm[1].roll = UPArm_2["roll"] if dir == "UP" else DOWNArm_2["roll"]
        
            Cont_Arm = self.GetBonesToRange(
                f"cont_arm_{dir}_{type}", 3, mode="EDIT"
            )
            if Cont_Arm :
                for i in range(2) : 
                    self.SetTransform(Cont_Arm[i], Def_Arm[i], length_value=0.2)
                self.SetTransform(Cont_Arm[-1], Def_Arm[-1], length_value=0.2, only_tail=True)
        
        # Hand
        Hand = self.GetBone(
            f"def_hand_{type}", mode="EDIT"
        )
        if Hand : 
            self.SetTransform(Hand, BS_Arm[-1])
        
        Cont_Hand = self.GetBonesToRange(
            f"cont_hand_{type}", 2, mode="EDIT"
        )
        if Cont_Hand :
            self.SetTransform(Cont_Hand[0], BS_Arm[-1], length_value=0.2)
            self.SetTransform(Cont_Hand[-1], BS_Arm[-1], length_value=0.2, only_tail=True)
        
        # Sub Arms 
        SubArm = self.GetBonesToRange(
            f"subarm_{type}", 2 , mode="EDIT"
        )
        C_SubArm = self.GetBonesToRange(
            f"C_subarm_{type}", 2 , mode="EDIT"
        )
        if SubArm and C_SubArm :
            for i in range(2) : 
                self.SetTransform(SubArm[i], BS_Arm[i])
                self.SetTransform(C_SubArm[i], BS_Arm[i])
        
        Cont_SubArm = self.GetBonesToRange(
            f"cont_subarm_{type}", 3, mode="EDIT"
        )
        if Cont_SubArm :
            for i in range(2) : 
                self.SetTransform(
                    Cont_SubArm[i], BS_Arm[i], length_value=0.2
            )
            self.SetTransform(
                    Cont_SubArm[-1], BS_Arm[1], length_value=0.2, only_tail=True
            )
        
        Rot_Arm = self.GetBonesToRange(
            f"rot_arm_{type}", 3, mode="EDIT"
        )
        if Rot_Arm :
            self.SetTransformToBones(Rot_Arm, BS_Arm)
        
        # Fk
        Fk_Arm = self.GetBonesToRange(
            f"fk_arm_{type}", 3, mode="EDIT"
        )
        if Fk_Arm :
            self.SetTransformToBones(Fk_Arm, BS_Arm)
        
        Root_Arm = self.GetBone(
            f"root_arm_{type}", mode="EDIT"
        )
        
        if Root_Arm :
            self.SetTransform(Root_Arm, BS_Arm[0], length_value=0.4)
        
        
        # IK
        Ik_Arm = self.GetBonesToRange(
            f"ik_arm_{type}", 3, mode="EDIT"
        )
        if Ik_Arm :
            self.SetTransformToBones(Ik_Arm, BS_Arm)
            
        PoleArm = self.GetBone(
        f"polearm_{type}", mode="EDIT"
        )
        if PoleArm :
            distance = BS_Arm[0].length + BS_Arm[1].length
            self.SetPoleTransform(PoleArm, [BS_Arm[0], BS_Arm[1]], distance)
        
        IK = self.GetBones(
            [f"rot_polearm_{type}"], mode="EDIT"
        )
        if IK :
            for bone in IK :
                self.SetTransform(bone, BS_Arm[0], length_value=0.5)
        
        SubPoleArm = self.GetBone(
            f"subpolearm_{type}", mode="EDIT"
        )
        if SubPoleArm :
            Local_Head = self.GetBone(
                f"cont_subarm_{type}.002", mode="EDIT"
            ).head
            Local_Tail = self.GetBone(
                f"polearm_{type}", mode="EDIT"
            ).head
            SubPoleArm.head = Local_Head
            SubPoleArm.tail = Local_Tail
            
        Root_P = self.GetBone(f"root_arm_properties_{type}", mode="EDIT") 
        if Root_P : 
            self.SetTransform(Root_P, BS_Arm[0], length_value=0.4)
        
        Followed = self.GetBone(f"ik_arm_{type}.003.001", mode="EDIT") 
        if Followed: 
            self.SetTransform(Followed, BS_Arm[-1], length_value=0.4)
        
        self.SetMode(mode="POSE")
        Fk_Arm = self.GetBonesToRange(
            f"fk_arm_{type}", 3, mode="POSE"
        )
        if Fk_Arm :
            for bone in Fk_Arm :
                bone.custom_shape_translation[1] = bone.length / 2

        IK = self.GetBone(
                f"ik_arm_{type}.001", mode="POSE"
            )
        if IK :
            IK.custom_shape_translation[1] = IK.length/2
        
        Ik_Arm = self.GetBone(
            f"ik_arm_{type}.003", mode="POSE"
        )
        if Ik_Arm :
            Ik_Arm.custom_shape_translation[1] = Ik_Arm.length*3
        
        self.ResetControPole(type, "ARM")
        
        self.ResetALLBoneStretchTo()    
    
    def ResetFingers(self, Finger : str = "thumb", type : str = "R") : 
        
        
        self.SetMode(mode="EDIT")
        
        
        Bs_Finger = self.GetBonesToRange(
            f"base_{Finger}_{type}", 4, mode="EDIT"
        )
        index : int = len(Bs_Finger)
        if Bs_Finger and index: 
            
            # Def 
            Def_Finger = self.GetBonesToRange(
            f"def_{Finger}_{type}", index, mode="EDIT"
            )
            if Def_Finger :
                self.SetTransformToBones(Def_Finger, Bs_Finger)
            
            # Control 
            Cont_Finger = self.GetBonesToRange(
            f"cont_{Finger}_{type}", index+1, mode="EDIT"
            )
            
            if Cont_Finger : 
                for i in range(index) : 
                    self.SetTransform(
                        Cont_Finger[i], Bs_Finger[i], length_value=0.2
                    )
                self.SetTransform(
                        Cont_Finger[-1], Bs_Finger[-1], length_value=0.2, only_tail=True
                    )

            # Root
            Root_Finger = self.GetBone(
                f"root_{Finger}_{type}", mode="EDIT"
            )
            if Root_Finger :
                self.SetTransform(Root_Finger, Bs_Finger[0])
                
            
            # Fk
            Fk_Finger = self.GetBonesToRange(
                f"fk_{Finger}_{type}", index-1, mode="EDIT"
            )
            if Fk_Finger :
                for i in range(index-1):
                    self.SetTransform(Fk_Finger[i], Bs_Finger[i+1])
                self.SetRelations(Fk_Finger[0], Root_Finger)
            
            if Finger != "thumb":
                
                # Rot 
                Rot_Finger = self.GetBonesToRange(
                    f"rot_{Finger}_{type}", index-1, mode="EDIT"
                )
                if Rot_Finger :
                    for i in range(index-1):
                        self.SetTransform(Rot_Finger[i], Bs_Finger[i+1])
                
                # IK
                Ik_Finger = self.GetBonesToRange(
                    f"ik_{Finger}_{type}", index, mode="EDIT"
                )
                
                if Ik_Finger : 
                    for i in range(index-1):
                        self.SetTransform(Ik_Finger[i], Bs_Finger[i+1])
                    self.SetTransform(Ik_Finger[-1], Bs_Finger[-1], only_tail=True)

            else :
                
                # Rot 
                Rot_Finger = self.GetBonesToRange(
                    f"rot_{Finger}_{type}", index, mode="EDIT"
                )
                if Rot_Finger :
                    for i in range(index):
                        self.SetTransform(Rot_Finger[i], Bs_Finger[i])
                
                # IK
                Ik_Finger = self.GetBonesToRange(
                    f"ik_{Finger}_{type}", index+1, mode="EDIT"
                )
                
                if Ik_Finger : 
                    for i in range(index):
                        self.SetTransform(Ik_Finger[i], Bs_Finger[i])
                    self.SetTransform(Ik_Finger[-1], Bs_Finger[-1], only_tail=True)
                    
                    
            Rot_Finger = self.GetBone(
                    f"rot_{Finger}_{type}", mode="EDIT"
                )
            if Rot_Finger :
                bone = Bs_Finger[1] if Finger != "thumb" else Bs_Finger[0]
                Rot_Finger.head = bone.head
                Rot_Finger.tail = bone.tail
                Rot_Finger.roll = bone.roll
                length : float = 0 
                for bone in Bs_Finger :
                    length += bone.length
                Rot_Finger.length = length / 2 if Finger != "thumb" else length
                
                if Finger == "thumb" :
                    Rot_Finger.parent = self.GetBone(f"rot_arm_{type}.003", mode="EDIT")
                
        self.SetMode(mode="POSE")
        Fk_Finger = self.GetBonesToRange(
                f"fk_{Finger}_{type}", index-1, mode="POSE"
            )
        if Fk_Finger :
            for bone in Fk_Finger:
                bone.custom_shape_translation[1] = bone.length/2
        
        
        #def setrot(bone, bs_bone):
        #    cont = self.CreateConstraint(
        #            bone,
        #            'COPY_LOCATION', 
        #            "RGC_cont", 
        #            self.GetActiveObject(), 
        #            bs_bone, 
        #            "LOCAL", "LOCAL",
        #            )
        #    cont.use_offset = True
        #    cont = self.CreateConstraint(
        #        bone,
        #        'COPY_ROTATION', 
        #        "RGC_cont", 
        #        self.GetActiveObject(), 
        #        bs_bone,  
        #        "LOCAL", 
        #        "LOCAL", 
        #        )
        #    cont.mix_mode = 'BEFORE'
        #
        #if Finger != "thumb" : 
        #    Fk_Finger = self.GetBonesToRange(
        #            f"fk_{Finger}_{type}", index, mode="POSE"
        #        )
        #    
        #    if Fk_Finger :
        #        for cont in Fk_Finger[0].constraints:
        #            if cont.type == "COPY_SCALE": 
        #                Fk_Finger[0].constraints.remove(cont)
        #        if not Fk_Finger[0].constraints:
        #            subtarget = self.GetBone(f"rot_{Finger}_{type}", mode="POSE")
        #            setrot(Fk_Finger[0], subtarget)
        #else:    
        #    Root_Finger = self.GetBone(
        #            f"root_{Finger}_{type}", mode="POSE"
        #        )
        #    Rot_Finger = self.GetBone(
        #            f"rot_{Finger}_{type}", mode="POSE"
        #        )
        #    if Root_Finger and Rot_Finger :
        #        setrot(Root_Finger, Rot_Finger)
            
        self.ResetALLBoneStretchTo()
            
        ... 
    
    def ResetLeg(self, type : str = "R") : 
        
        
        self.SetMode(mode="EDIT")
        Bs_Leg = self.GetBonesToRange(
            f"base_leg_{type}", 2, mode="EDIT"
        )
        
        
        if Bs_Leg : 
            
            Bs_LegUp_1 = CreateFakeBone(
                Bs_Leg[0].head, (Bs_Leg[0].head+Bs_Leg[0].tail)/2,
                Bs_Leg[0].roll, Bs_Leg[0].length/2
            )
            Bs_LegUp_2 = CreateFakeBone(
                (Bs_Leg[0].head+Bs_Leg[0].tail)/2, Bs_Leg[0].tail,
                Bs_Leg[0].roll, Bs_Leg[0].length/2
            )
            Bs_LegDown_1 = CreateFakeBone(
                Bs_Leg[1].head, (Bs_Leg[1].head+Bs_Leg[1].tail)/2,
                Bs_Leg[1].roll, Bs_Leg[1].length/2
            )
            Bs_LegDown_2 = CreateFakeBone(
                (Bs_Leg[1].head+Bs_Leg[1].tail)/2, Bs_Leg[1].tail,
                Bs_Leg[1].roll, Bs_Leg[1].length/2
            )
            
            
            for dir in ["UP", "DOWN"] : 
                # Def 
                Def_Leg = self.GetBonesToRange(
                    f"def_leg_{dir}_{type}", 2, mode="EDIT"
                )
                if Def_Leg : 
                    self.SetTransform(Def_Leg[0], Bs_LegUp_1 if dir == "UP" else Bs_LegDown_1)
                    self.SetTransform(Def_Leg[1], Bs_LegUp_2 if dir == "UP" else Bs_LegDown_2)

                Cont_Leg = self.GetBonesToRange(
                    f"cont_leg_{dir}_{type}", 3, mode="EDIT"
                )
                if Cont_Leg : 
                    for i in range(2):
                        self.SetTransform(
                            Cont_Leg[i], Def_Leg[i], length_value=0.2
                        )
                    self.SetTransform(
                            Cont_Leg[-1], Def_Leg[-1], length_value=0.2, only_tail=True
                        )
            
                SubLeg = self.GetBonesToRange(
                    f"subleg_{type}", 2, mode="EDIT"
                )
                if SubLeg : 
                    self.SetTransformToBones(
                        SubLeg, Bs_Leg,
                    )
                    
                C_SubLeg = self.GetBonesToRange(
                    f"C_subleg_{type}", 2, mode="EDIT"
                )
                if C_SubLeg : 
                    self.SetTransformToBones(
                        C_SubLeg, Bs_Leg,
                    )
                
                Cont_SubLeg = self.GetBonesToRange(
                    f"cont_subleg_{type}", 3, mode="EDIT"
                )
                if Cont_SubLeg : 
                    for i in range(2):
                        self.SetTransform(Cont_SubLeg[i], Bs_Leg[i], length_value=0.2)
                    self.SetTransform(Cont_SubLeg[-1], Bs_Leg[-1], length_value=0.2, only_tail=True) 
                    
            
        Bs_Feet = self.GetBonesToRange(
            f"base_feet_{type}", 3, mode="EDIT"
        )
        
        if Bs_Feet : 
            
            # Def 
            Def_Feet = self.GetBonesToRange(
                f"def_feet_{type}", 3,  mode="EDIT"
            )
            if Def_Feet : 
                self.SetTransformToBones(Def_Feet, Bs_Feet)
            
            # Control 
            Cont_Feet = self.GetBonesToRange(
                f"cont_feet_{type}", 3,  mode="EDIT"
            )
            if Cont_Feet : 
                for i in range(2):
                    self.SetTransform(Cont_Feet[i], Bs_Feet[i], length_value=0.2)
                self.SetTransform(Cont_Feet[-1], Bs_Feet[1], length_value=0.2, only_tail=True)
        
        if Bs_Leg and Bs_Feet :
            
            # Rot 
            Rot_Leg = self.GetBonesToRange(
                f"rot_leg_{type}", 4, mode="EDIT"
            )
            if Rot_Leg : 
                for i in range(2):
                    self.SetTransform(Rot_Leg[i], Bs_Leg[i])
                for i in range(2):
                    self.SetTransform(Rot_Leg[i+2], Bs_Feet[i])
            
            # FK 
            Fk_Leg = self.GetBonesToRange(
                f"fk_leg_{type}", 4, mode="EDIT"
            )
            if Fk_Leg : 
                self.SetTransformToBones(Fk_Leg, Rot_Leg)
            
            # IK
            Ik_Leg = self.GetBonesToRange(
                f"ik_leg_{type}", 4, mode="EDIT"
            )
            if Ik_Leg : 
                self.SetTransformToBones(Ik_Leg, Rot_Leg)

            Ik_Leg = self.GetBone(
                f"ik_leg_{type}", mode="EDIT"
            )
            if Ik_Leg : 
                Ik_Leg.head = Bs_Leg[-1].tail 
                Ik_Leg.tail = (
                    Bs_Leg[-1].tail[0],
                    Bs_Feet[-2].tail[1],
                    Bs_Leg[-1].tail[2],
                    )
                Ik_Leg.roll = 0

            Ik_SubLeg = self.GetBonesToRange(
                f"ik_subleg_{type}", 2, mode="EDIT"
            )
            if Ik_SubLeg : 
                self.SetTransform(Ik_SubLeg[0], Ik_Leg, length_value=0.2)
                self.SetTransform(Ik_SubLeg[1], Bs_Feet[-2], length_value=0.5, only_tail=True)
            
            Rot_Ik_Leg = self.GetBonesToRange(
                f"rot_ik_leg_{type}", 5, mode="EDIT"
            )
            if Rot_Ik_Leg : 
                self.SetTransform(Rot_Ik_Leg[0], Bs_Feet[1], length_value=0.5)
                Local_Head_1 = Bs_Feet[-1].head
                Local_Head_2 = (Bs_Feet[-1].head + Bs_Feet[-1].tail)/ 2
                Local_Head_3 = Bs_Feet[-1].tail
                Local_Head_4 = (Bs_Feet[-1].head + Bs_Feet[-1].tail)/ 2
                Local_Head_4[1] = Bs_Feet[1].tail[1]
                
                Rot_Ik_Leg[1].head = Local_Head_1
                Rot_Ik_Leg[1].tail = Local_Head_1 + (self.GetWorldNormal("y")*-1)
                Rot_Ik_Leg[1].length = Bs_Feet[-1].length * 0.5
                
                Rot_Ik_Leg[2].head = Local_Head_2
                Rot_Ik_Leg[2].tail = Local_Head_2 + (self.GetWorldNormal("y")*-1)
                Rot_Ik_Leg[2].length = Bs_Feet[-1].length * 0.5
                
                Rot_Ik_Leg[3].head = Local_Head_3
                Rot_Ik_Leg[3].tail = Local_Head_3 + (self.GetWorldNormal("y")*-1)
                Rot_Ik_Leg[3].length = Bs_Feet[-1].length * 0.5
                
                Rot_Ik_Leg[4].head = Local_Head_4
                Rot_Ik_Leg[4].tail = Local_Head_4 + (self.GetWorldNormal("y")*-1)
                Rot_Ik_Leg[4].length = Bs_Feet[-1].length * 0.5
            
            Rot_Ik_Leg = self.GetBone(
                f"rot_ik_leg_{type}", mode="EDIT"
            )
            if Rot_Ik_Leg : 
                Local_Head_2 = (Bs_Feet[-1].head + Bs_Feet[-1].tail)/ 2
                Rot_Ik_Leg.head = Local_Head_2
                Rot_Ik_Leg.tail = Local_Head_2 + (self.GetWorldNormal("y")*-1)
                Rot_Ik_Leg.length = Bs_Feet[-1].length * 0.5
        
            # Pole
            PoleLeg = self.GetBone(
                f"poleleg_{type}", mode="EDIT"
            )
            if PoleLeg : 
                self.SetPoleTransform(PoleLeg, [Bs_Leg[0], Bs_Leg[1]],  (Bs_Leg[0].length+Bs_Leg[1].length)/1.3)
                
            SubPoleLeg_L = self.GetBone(
                f"subpoleleg_{type}", mode="EDIT"
            )
            if SubPoleLeg_L and PoleLeg : 
                SubPoleLeg_L.head = Bs_Leg[0].tail
                SubPoleLeg_L.tail = PoleLeg.head
                SubPoleLeg_L.roll = 0

            # Feet 
            Rot_Feet = self.GetBone(
                f"rot_feet_{type}", mode="EDIT"
            )
            if Rot_Feet : 
                self.SetTransform(Rot_Feet, Bs_Feet[1])
            
        #Root
        Root = self.GetBone(f"root_leg_{type}", mode="EDIT")
        if Root :
            self.SetTransform(Root, Bs_Leg[0], length_value=0.5)  
        
        Root_P = self.GetBone(f"root_leg_properties_{type}", mode="EDIT") 
        if Root_P : 
            self.SetTransform(Root_P, Bs_Leg[0], length_value=0.4)
           
           
        Ik_Leg = self.GetBone(f"ik_leg_{type}", mode="EDIT")
        Followed = self.GetBone(f"ik_leg_{type}.005", mode="EDIT")
        if Ik_Leg and Followed : 
            self.SetTransform(Followed, Ik_Leg, length_value=0.4)
        
        self.ResetControPole(type, "LEG")
        
        
        self.ResetALLBoneStretchTo()
        
        Bs_Leg = self.GetBonesToRange(
            f"base_leg_{type}", 2, mode="POSE"
        )
        Bs_Feet = self.GetBonesToRange(
            f"base_feet_{type}", 3, mode="POSE"
        )
        
        # FK 
        Fk_Leg = self.GetBonesToRange(
            f"fk_leg_{type}", 4, mode="POSE"
        )
        if Fk_Leg : 
            for bone in Fk_Leg:
                bone.custom_shape_translation[1] = bone.length/2
        
        Ik_Leg = self.GetBone(
            f"ik_leg_{type}", mode="POSE"
        )
        if Ik_Leg :
            Ik_Leg.custom_shape_translation[1] = Ik_Leg.length/2.5
            Distance = self.GetDistancia3d(Bs_Leg[-1].tail, (Bs_Feet[-1].head+Bs_Feet[-1].tail)/2)
            Ik_Leg.custom_shape_translation[2] = (Distance*-1)/1.1
        
        Ik_Leg = self.GetBone(
            f"ik_leg_{type}.001", mode="POSE"
        )
        if Ik_Leg : 
            Ik_Leg.custom_shape_translation[1] = Ik_Leg.length/2
        
        # Feet 
        Rot_Feet = self.GetBone(
                f"rot_feet_{type}", mode="POSE"
            )
        if Rot_Feet : 
            Rot_Feet.custom_shape_translation[1] = Rot_Feet.length

    def ResetRoot(self) : 
        
        self.SetMode("EDIT")
        BS_Spine = self.GetBone(f"base_spine.001", mode="EDIT")
        Root_Hip = self.GetBone(f"Root_hip", mode="EDIT")
        if BS_Spine and Root_Hip:
            Root_Hip.head = BS_Spine.head 
            Root_Hip.tail = BS_Spine.head + self.GetWorldNormal()
            Root_Hip.roll = 0
            Root_Hip.length = BS_Spine.length
        Root_Hip = self.GetBone(f"Root_move", mode="EDIT")
        if Root_Hip : 
            Root_Hip.head = (0, 0, 0)
            Root_Hip.tail = self.GetWorldNormal(Eje="y")*-1
            Root_Hip.roll = 0 
        root_rotation = self.GetBone("root_rotation", mode="EDIT")
        ng_root_rotation : bool = False
        if not root_rotation : 
            ng_root_rotation = True
            root_rotation = self.CreateBone("root_rotation")
            self.SetColorBone(root_rotation)
            root_parent = self.GetBone("Root_move", mode="EDIT")
            proot_parent = root_parent.parent
            root_rotation.parent = proot_parent
            if root_parent :
                root_parent.parent = root_rotation
            
            self.BoneCollectionUnassing(root_rotation) 
            self.BoneCollectionAssing("SubRoots", root_rotation)
            
        self.SetDeform([root_rotation], False)
            
        if BS_Spine and root_rotation:
            root_rotation.head = BS_Spine.head 
            root_rotation.tail = BS_Spine.head + (self.GetWorldNormal("y") * -1)
            root_rotation.roll = 0
            root_rotation.length = BS_Spine.length * 4
        
        
        subpole = self.GetBones(["subpolearm_L", "subpolearm_R", "subpoleleg_L", "subpoleleg_R"], mode="EDIT")
        for b in subpole:
            self.BoneCollectionAssing("SubRoots", b)
        
        root_rotation_name = root_rotation.name
        self.SetMode("POSE")
        obj_name = ""
        Root_Hip = self.GetBone(f"Root_hip", mode="POSE")
        root_parent = self.GetBone("Root_move", mode="POSE")
        root_rotation = self.GetBone(root_rotation_name, mode="POSE")
        if Root_Hip : 
            Root_Hip.custom_shape_translation[1] = Root_Hip.length
        if root_rotation :
            shape_bone = self.GetBone("cont_spine.001", mode="POSE")
            if shape_bone :
                root_rotation.custom_shape = shape_bone.custom_shape
            root_rotation.custom_shape_scale_xyz[2] = 0
            for i in range(1) :
                root_rotation.lock_scale[i] = True

            obj_name = root_rotation.custom_shape.name

        if root_parent and ng_root_rotation:
                c = root_parent.constraints.new(type='COPY_LOCATION')
                c.target = self.GetActiveObject()
                c.subtarget = root_rotation.name 
                c.invert_x = True
                c.invert_y = True
                c.invert_z = True
                c.use_offset = True
                c.target_space = 'LOCAL'
                c.owner_space = 'LOCAL'

        for col in bpy.data.collections :
            if "RIG_CREATOR_Material" in col.name :
                if bpy.data.objects.get(obj_name) :
                    self.LinktoCollectin(col, bpy.data.objects.get(obj_name))
        self.SetMode("POSE")
        
    def ResetCar(self) : 
        
        objprops = self.PropsToObject()
        dim = None
        if objprops.use_object_reference : 
            OBJ_BODY = objprops.object_body
            dim = OBJ_BODY.dimensions
            OBJ_WHEEL_FRONT_L = objprops.object_wheel_front_L
            OBJ_WHEEL_FRONT_R = objprops.object_wheel_front_R
            OBJ_WHEEL_BACK_L = objprops.object_wheel_back_L
            OBJ_WHEEL_BACK_R = objprops.object_wheel_back_R
            
           
            set_parents = []
           
            def SetTransform(obj, bone, Eje="y", parent = "") :
               if obj and bone :
                head = obj.matrix_world.decompose()[0]
                bone.head = head
                bone.tail = head + self.GetWorldNormal(Eje)*-1 if Eje == "y" else head + self.GetWorldNormal(Eje)
                bone.roll = 0 if bone.name == "base_body" else 3.14159
                set_parents.append([obj, parent])
            
            ARM = self.GetActiveObject()
  
            self.SetMode("EDIT")
            
            BASE_BODY = self.GetBone("base_body", mode="EDIT")
            BASE_WHEELS_FRONT = self.GetBones(["base_wheel_front_L", "base_wheel_front_R"], mode="EDIT")
            BASE_WHEELS_BACK = self.GetBones(["base_wheel_back_L", "base_wheel_back_R"], mode="EDIT")
            
            SetTransform(OBJ_BODY, BASE_BODY, "z","def_body")
            SetTransform(OBJ_WHEEL_FRONT_L, BASE_WHEELS_FRONT[0], parent="def_wheel_front_L")
            SetTransform(OBJ_WHEEL_FRONT_R, BASE_WHEELS_FRONT[1], parent="def_wheel_front_R")
            SetTransform(OBJ_WHEEL_BACK_L, BASE_WHEELS_BACK[0], parent="def_wheel_back_L")
            SetTransform(OBJ_WHEEL_BACK_R, BASE_WHEELS_BACK[1], parent="def_wheel_back_R")
            ARM.data.collections_all["Def_Bone"].is_visible = True

            for parent in set_parents :
                self.SetMode("POSE") 
                self.ActiveBone(parent[1], mode="POSE")
                
                self.SetMode("OBJECT")
                parent[0].select_set(True)
                self.ActiveObj(ARM, False)
                bpy.ops.object.parent_set(type='BONE_RELATIVE', keep_transform=True)
                self.ActiveObj(ARM)
                
        self.SetMode("EDIT")
        BASE_BODY = self.GetBone("base_body", mode="EDIT")
        BASE_WHEELS_FRONT = self.GetBones(["base_wheel_front_L", "base_wheel_front_R"], mode="EDIT")
        BASE_WHEELS_BACK = self.GetBones(["base_wheel_back_L", "base_wheel_back_R"], mode="EDIT")
            
        
        if BASE_BODY :
            BODY_PART = self.GetBones(["def_body", "rot_body", "root_body"], mode="EDIT")
            if BODY_PART :
                for bone in BODY_PART :
                    if bone.name != "root_body" :
                        self.SetTransform(bone, BASE_BODY)
                    else:
                        bone.head = BASE_BODY.head
                        bone.tail = BASE_BODY.head + self.GetWorldNormal("y")*-1
                        bone.roll = 0
                        bone.length = BASE_BODY.length * 0.5
            ROT_BODY = self.GetBones(["rot_body_front", "rot_body_L", "rot_body_R", "rot_body_back", "rot_wheels_front"], mode="EDIT")            
           
            if ROT_BODY :
                # Rot Front
                head = (BASE_WHEELS_FRONT[0].head + BASE_WHEELS_FRONT[1].head) / 2
                tail = head + self.GetWorldNormal()
                ROT_BODY[0].head = head
                ROT_BODY[0].tail = tail
                ROT_BODY[0].roll = 0
                ROT_BODY[-1].head = head
                ROT_BODY[-1].tail = tail
                ROT_BODY[-1].roll = 0

                # Rot Back
                head = (BASE_WHEELS_BACK[0].head + BASE_WHEELS_BACK[1].head) / 2
                tail = head + self.GetWorldNormal()
                ROT_BODY[3].head = head
                ROT_BODY[3].tail = tail
                ROT_BODY[3].roll = 0

                # Rot left
                head = (BASE_WHEELS_FRONT[0].head + BASE_WHEELS_BACK[0].head) / 2
                tail = head + self.GetWorldNormal()
                ROT_BODY[1].head = head
                ROT_BODY[1].tail = tail
                ROT_BODY[1].roll = 0
                
                # Rot Right
                head = (BASE_WHEELS_FRONT[1].head + BASE_WHEELS_BACK[1].head) / 2
                tail = head + self.GetWorldNormal()
                ROT_BODY[2].head = head
                ROT_BODY[2].tail = tail
                ROT_BODY[2].roll = 0
     
        for dir in ["front", "back"] : 
            for type in ["L", "R"] : 
                BS_Wheel = self.GetBone(f"base_wheel_{dir}_{type}", mode="EDIT")
                if BS_Wheel :
                    bones = self.GetBones(
                        [f"def_wheel_{dir}_{type}", f"rot_wheel_{dir}_{type}", f"cont_wheel_{dir}_{type}", f"cont_shock_absorber_{dir}_{type}"], mode="EDIT"
                    )
                    for b in bones :
                        self.SetTransform(b, BS_Wheel)

        self.SetMode("POSE")
        
        if dim : 
            BODY_PART = self.GetBones(["def_body", "root_body"], mode="POSE")
            if BODY_PART :
                for bone in BODY_PART :
                    bone.custom_shape_scale_xyz = dim
                    
            
            ROT_BODY = self.GetBone("rot_body", mode="POSE")
            if ROT_BODY :
                ROT_BODY.custom_shape_translation.y = dim.z
            
            ROT_WHEELS = self.GetBone("rot_wheels_front", mode="POSE")
            if ROT_WHEELS :
                ROT_WHEELS.custom_shape_translation.y = dim.z * 0.75

    def ResetControPole(self, type : str = "R", subtype : str = "ARM") : 
        bone_name = f"ROOT_POLE{subtype}_{type}"
        bone_name_1 = f"ROOT_POLE{subtype}_{type}_1"
        bone_name_2 = f"ROOT_POLE{subtype}_{type}_2"
        looK_bone_name_1 = ""
        self.SetMode("POSE")
        rot_bone = self.GetBone(bone_name_1, mode="POSE")
        if rot_bone :
            for cs in rot_bone.constraints :
                if cs.type == "DAMPED_TRACK" :
                    looK_bone_name_1 = cs.subtarget

        self.SetMode("EDIT")
        
        
        rot_bone = self.GetBone(bone_name_1, mode="EDIT")
        if rot_bone : 
            self.SetTransform(rot_bone, rot_bone.parent)
            look_bone = self.GetBone(looK_bone_name_1, mode="EDIT")
            if look_bone :
                rot_bone.tail = look_bone.tail
            
        self.SetDeform([rot_bone], False)
        
        subpoles = self.GetBones([bone_name, bone_name_2], mode="EDIT")
        for b in subpoles :
            self.SetTransform(b, subpoles[0].children[0])
        self.SetDeform(subpoles, False)
    
    def ResetALLBoneStretchTo(self) : 
        self.SetMode(mode="POSE")
        for bone in self.GetActiveObject().pose.bones :
            for cont in bone.constraints:
                if cont.type == "STRETCH_TO" : 
                    cont.rest_length = 0
                    
    def ResetSelectBoneStretchTo(self) : 
        self.SetMode(mode="POSE")
        for bone in self.GetSelectBones("POSE") :
            for cont in bone.constraints:
                if cont.type == "STRETCH_TO" : 
                    cont.rest_length = 0

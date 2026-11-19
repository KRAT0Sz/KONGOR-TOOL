import bpy
from ...generaldata import *
from .generators_bones import *
from types import SimpleNamespace
import bmesh
from mathutils import Vector

class MeshToBone(GeneratorsBones):
    
    
    def MeshToBone(self): 
        # Get the active object (assumed to be a mesh object)
        obj = self.GetActiveObject()
        select_obj = self.GetSelectableObjects()
        self.UpdateViewLayer()
        
        selected_vertex_coords = []
        selected_vertex_normal = []
        
        selected_ege_coords = []
        selected_ege_normal = []
        
        selected_face = []
        selected_face_coords = []
        selected_face_normal = []
        
        # Ensure you're in Edit Mode
        if obj.mode == 'EDIT':
            
            # Crear una representación bmesh de la malla
            bm = bmesh.from_edit_mesh(obj.data)
            
            if self.GetMeshSelectMode("VERT"):
                
                # Obtener las coordenadas de los vértices seleccionados
                selected_vertex_coords = [v.co.copy() for v in bm.verts if v.select]
                selected_vertex_normal = [v.normal.copy() for v in bm.verts if v.select]
            
            elif self.GetMeshSelectMode("EDGE"):
                
                for edge in bm.edges:
                    if edge.select:
                        
                        selected_ege_coords.append((
                            edge.verts[0].co.copy() , 
                            edge.verts[1].co.copy() ))
                        
                        selected_ege_normal.append((
                            edge.verts[0].normal.copy() , 
                            edge.verts[1].normal.copy() ))
                        
            elif self.GetMeshSelectMode("FACE"):
                
                for face in bm.faces:
                    if face.select:
                        faces = []
                        normals = []
                        for vert in face.verts:
                            faces.append(vert.co.copy())
                            normals.append(vert.normal.copy())
                        selected_face_coords.append(faces)
                        selected_face_normal.append(normals)
        armature = None
        for obj in select_obj: 
            if obj.type == "ARMATURE": 
                armature = obj
                break
        
        # Salimos del modo Edit para la malla antes de trabajar con el armature
        self.SetMode(mode="OBJECT")
        props = self.Props()
        
        
        # Función para calcular las nuevas coordenadas considerando la matriz mundial del objeto
        def n_co(co): 
            # Aplicar correctamente la matriz mundial a un Vector4 y devolver Vector3
            co_world = obj.matrix_world @ co.to_4d()  # Asegúrate de convertir a Vector4 para la multiplicación
            return co_world.to_3d()  # Convertir a Vector3 para obtener solo la parte XYZ

        
        def set_bone():
            
            
            def roll(bone, normal):
                if props.mesh_use_aling_roll_normal:
                    bone.align_roll(normal)
            
            def reference_bone(use_tail : bool = False):
                if props.mesh_use_bone_reference :
                    reference_bone = self.GetBone(props.mesh_bone_reference_name, mode="EDIT")
                    if not reference_bone : return
                    for bone in new_bones : 
                        if use_tail :
                            bone.length = reference_bone.length
                        self.SetDisplaySize(bone, reference_bone)
            
            if self.GetMeshSelectMode("VERT"):
                
                if not props.mesh_use_vertcurve or len(selected_vertex_coords) <= 1:
                    if not props.mesh_use_tail or len(selected_vertex_coords) <= 1 : 
                        new_bones = self.CreateBonesRange(props.mesh_bone_name, len(selected_vertex_coords))
                        reference_bone()
                            
                        for i, co in enumerate(selected_vertex_coords):
                            new_bones[i].head = n_co(co)
                            if props.mesh_normal_global == "GLOBAL":
                                type = str(props.mesh_direction).replace("{", "").replace("}", "").replace("'", "")
                                new_bones[i].tail = n_co(co) + self.GetWorldNormal(f"{type.lower()}")
                            else :
                                new_bones[i].tail = n_co(co) + selected_vertex_normal[i]
                            roll(new_bones[i], selected_vertex_normal[i])
                    else : 
                        new_bones = self.CreateBonesRange(props.mesh_bone_name, len(selected_vertex_coords)-1)
                        reference_bone(use_tail=True)
                        for i, bone in enumerate(new_bones):
                            bone.head =  n_co(selected_vertex_coords[i])
                            bone.tail = n_co(selected_vertex_coords[i+1])
                            roll(new_bones[i], selected_vertex_normal[i])
                else :
                    new_bones = self.CreateBonesRange(props.mesh_bone_name, 1)
                    reference_bone(use_tail=True)
                    def obtener_2_vertices_mas_lejanos(vertex_coords):
                        if len(vertex_coords) < 2:
                            return None  # Mínimo 2 vértices
                        
                        max_distance = -1
                        par_mas_lejano = (vertex_coords[0], vertex_coords[1])  # Inicialización
                        
                        # Bucle eficiente (comparación sin repeticiones)
                        for i in range(len(vertex_coords)):
                            v1 = Vector(vertex_coords[i])
                            for j in range(i + 1, len(vertex_coords)):
                                distancia = (v1 - Vector(vertex_coords[j])).length
                                if distancia > max_distance:
                                    max_distance = distancia
                                    par_mas_lejano = (vertex_coords[i], vertex_coords[j])
                        
                        return par_mas_lejano
                    verts = obtener_2_vertices_mas_lejanos(selected_vertex_coords)
                    new_bones[0].head = n_co(verts[0])
                    new_bones[0].tail = n_co(verts[-1])
                    new_bones[0].bbone_segments = 32
                    
                    normal = self.CreateVector(0, 0, 0)
                    for n in selected_vertex_normal:
                        normal += n
                    normal /= len(selected_vertex_normal)
                    roll(new_bones[0], normal)
                    influence = len(selected_vertex_coords) * props.mesh_vertcurve_power
                    self.AlingBboneToNormal(new_bones[0], normal, influence)
                    self.GetActiveObject().data.display_type = 'BBONE'
                    
                    
            
            if self.GetMeshSelectMode("EDGE") : 
                
                
                
                new_bones = self.CreateBonesRange(props.mesh_bone_name, len(selected_ege_coords))
            
                if props.mesh_use_tail : 
                    reference_bone(use_tail=True)
                    for i, co in enumerate(selected_ege_coords):
                        new_bones[i].head = n_co(co[0])
                        new_bones[i].tail = n_co(co[1])
                        normal = (selected_ege_normal[i][0] + selected_ege_normal[i][1]) / 2
                        roll(new_bones[i], normal)
                else :
                    reference_bone()
                    for i, co in enumerate(selected_ege_coords):
                        head = (n_co(co[0]) + n_co(co[1])) / 2
                        normal = (selected_ege_normal[i][0] + selected_ege_normal[i][1]) / 2
                        
                        new_bones[i].head = head
                        if props.mesh_normal_global == "GLOBAL":
                            type = str(props.mesh_direction).replace("{", "").replace("}", "").replace("'", "")
                            new_bones[i].tail = head + self.GetWorldNormal(f"{type.lower()}")
                        else :
                            new_bones[i].tail = head + normal
                        roll(new_bones[i], normal)
                            
                        if 1 > 0 : 
                            dis = self.GetDistancia3d(new_bones[i-1].tail, new_bones[i].head)
                            if dis < 0.1 :
                                bone.parent = new_bones[i-1]
                                bone.use_connect = True
                

            if self.GetMeshSelectMode("FACE") : 
                
                
                new_bones = self.CreateBonesRange(props.mesh_bone_name, len(selected_face_coords))
                reference_bone(use_tail=True)
                for i, face in enumerate(selected_face_coords):
                    
                    head = self.CreateVector(0, 0, 0)
                    for co in face : 
                        head += co
                    head = head / len(face)
                    head = n_co(head)
                    normal = self.CreateVector(0, 0, 0)
                    for n in selected_face_normal[i] : 
                        normal += n
                    normal = normal / len(selected_face_normal[i])
                    
                    new_bones[i].head = head
                    

                    if props.mesh_normal_global == "GLOBAL":
                        type = str(props.mesh_direction).replace("{", "").replace("}", "").replace("'", "")
                        new_bones[i].tail = head + self.GetWorldNormal(f"{type.lower()}")
                    else :
                        new_bones[i].tail = head + normal
                        
                    roll(new_bones[i], normal)
                    
            if props.mesh_use_curve :
                curve_bone = self.CreateBonesRange("bendy-"+props.mesh_bone_name, Range=props.mesh_bone_subdivisions)
                new_tail = self.CreateVector(0, 0, 0)
                head_cero = new_bones[0].head
                max_dist = -1  # Inicializa la distancia más grande en un valor bajo

                for bone in new_bones:
                    dis = self.GetDistancia3d(head_cero, bone.head)
                    if dis > max_dist:  # Si encontramos una distancia mayor, actualizamos
                        max_dist = dis
                        new_tail = bone.head
                
                if curve_bone :
                    for bone in curve_bone :
                        bone.head = new_bones[0].head
                        bone.tail = new_tail
                        self.SetDisplaySize(bone, new_bones[0])
                    self.SetDeform(curve_bone, False)

                self.GetActiveObject().data.display_type = 'BBONE'
                name_curve_bone = self.GetNameToBones(curve_bone)
                name_new_bones = self.GetNameToBones(new_bones)
                self.SetMode(mode="POSE")
                curve_bone_pose = self.GetBones(name_curve_bone, mode="POSE")
                new_bones_pose = self.GetBones(name_new_bones, mode="POSE")
                if curve_bone_pose and new_bones_pose :
                    self.SelectBones(curve_bone_pose, mode="POSE")
                    GeneratorsBones().GN_Curve()
                    self.SelectBones(new_bones_pose, mode="POSE")
                    self.ActiveBone(curve_bone_pose[0].name, mode="POSE")
                    props.bendybone_type = {"PARENT"}
                    self.SetContBendyBone()
                
                self.SetMode(mode="EDIT")
                
                
        # Asegurarse de que el armature esté en la capa de vista activa
        if armature:
            obj = self.GetActiveObject()
            self.ActiveObj(armature)
            self.SetMode(mode="EDIT")
            set_bone()
        else:
            obj = self.GetActiveObject()
            bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            self.SetMode(mode="EDIT")
            self.RemoveBones(["Bone"])
            set_bone()
        
        
        if props.mesh_with_automatic_weights :
            self.SetMode(mode="OBJECT")
            armature = self.GetActiveObject()
            obj.select_set(True)
            bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            if props.mesh_with_by_distance_of_vertex:
                self.WithDistanceWeights(obj, armature)
            self.ActiveObj(armature)
            self.SetMode(mode="EDIT")
            
    
    def GetObject(self) -> list :
        props = self.Props()
        
        objs = self.GetSelectableObjects()
        
        obj = None
        arm = None
        
        self.SetMode(mode="OBJECT")
        if not props.mesh_armature_select : 
            for b in objs:
                if b.type == "MESH":
                    obj = b
                elif b.type == "ARMATURE":
                    arm = b

            if obj and arm is None:
                bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
                arm = self.GetActiveObject()
                if arm:
                    for bone in list(arm.data.edit_bones):
                        arm.data.edit_bones.remove(bone)

            if obj is None or arm is None:
                return [None, None]
        
        else :
            obj = self.GetActiveObject()
            arm = props.mesh_armature_select
        
        return [obj, arm]
    
    def WithDistanceWeights(self, obj, arm):
        props = self.Props()
        if props.mesh_with_automatic_weights :
            self.SetMode(mode="OBJECT")
            obj.select_set(True)
            bpy.ops.object.parent_set(type='ARMATURE_AUTO')
            self.ActiveObj(arm)
            self.SetMode(mode="EDIT")
    
    def KeepObject(self, obj, arm):
        props = self.Props()
        if props.mesh_keep_object : 
            self.SetMode(mode="OBJECT")
            self.ActiveObj(obj)
            self.SetMode(mode="EDIT")
            arm.select_set(True)
    
    def GetCosSortGood(self, obj) -> list:
        self.SetMode("OBJECT")
        self.ActiveObj(obj)
        self.SetMode("EDIT")
        cos = self.GetVertexSelectCO(obj, self.GetMeshMode())
        self.UpdateViewLayer()
        init_point = self.GetVertexActivaCO(obj, self.GetMeshMode())
        if init_point :
            cos = self.SortCordineByDistance(cos, start_point=init_point)
        return cos
    
    def Only_Bone(self):
        obj, arm = self.GetObject()
        if not obj or not arm : return
        props = self.Props()
        
        self.SetMode("OBJECT")
        self.ActiveObj(obj)
        self.SetMode("EDIT")
        self.UpdateViewLayer()
        
        mode = "VERT"
        if self.GetMeshSelectMode("EDGE") :
            mode = "EDGE"
        elif self.GetMeshSelectMode("FACE") :
            mode = "FACE"
        
        values  = self.GetVertexSelectCoNormal(
            obj, mode
        )
        
        self.SetModeObj(arm, "EDIT")
        
        bones = self.CreateBonesRange(f"{props.mesh_bone_name}", len(values))
        for i, bone in enumerate(bones) :
            co = values[i][0]
            normal = values[i][1]
            bone.head = co
            type = str(props.ob_direction).replace("{", "").replace("}", "").replace("'", "") 
            bone.tail = co + (self.GetWorldNormal(type.lower()) if props.ob_normal_global == "GLOBAL" else normal)
            bone.length = props.ob_length
            
        self.WithDistanceWeights(obj, arm)
        self.KeepObject(obj, arm)
    
    def Curve_Bone(self):
        pass
    
    def HeadTail_Bone(self):
        obj, arm = self.GetObject()
        if not obj or not arm : return
        props = self.Props()
        
        cos = self.GetCosSortGood(obj)

        self.SetModeObj(arm, "EDIT")

        bb_bones = self.CreateBonesRange(f"bb_{props.mesh_bone_name}", len(cos)-1 if not props.headtail_use_loop else len(cos))
        for i, bone in enumerate(bb_bones):
            bone.head = cos[i]
            index = i+1
            if not props.headtail_use_loop :
                bone.tail = cos[index]
            else :
                bone.tail = cos[index] if index < len(cos) else cos[0]
                
            if props.headtail_use_bbone :
                bone.display_type = 'BBONE'
                bone.bbone_x *= props.mesh_shape_size
                bone.bbone_z *= props.mesh_shape_size
            
            bone.align_roll(cos[i])
        if props.headtail_use_parent :
            self.SetRelationsOnlyOneList(bb_bones, props.headtail_use_connected)
            
        if props.headtail_enum_const != "NONE" :
            bbones_name = self.GetNameToBones(bb_bones)
            self.SetMode("POSE")
            for bname in bbones_name :
                self.ActiveBone(bname, "POSE")
            
            if props.headtail_enum_const == "GRIP" :
                self.GN_CurveGrip()
            elif props.headtail_enum_const == "CURVE" :
                self.GN_Curve()
            elif props.headtail_enum_const == "FINGERS" :
                self.GN_Fingers()
        
        self.WithDistanceWeights(obj, arm)
        self.KeepObject(obj, arm)
    
    def Eye_Bone(self) :
        
        obj, arm = self.GetObject()
        if not obj or not arm : return

        cos = self.GetCosSortGood(obj)
        
        self.AddCollection()
        self.ActiveObj(arm)
        props = self.Props()

        name = props.mesh_bone_name
        point = props.eye_point_center.matrix_world.copy().translation if props.eye_point_center else self.CreateVector(0, 0, 0)
        
        size = (props.eye_point_center.dimensions.length / 2 if props.eye_point_center.type == "MESH" else 1) * props.mesh_shape_size
        
        center = self.CreateVector(0, 0, 0)
        for co in cos:
            center += co
        center /= max(1, len(cos))
        
        import math


        # ----- Crear hijos (rot/def/cont) de forma segura -----
        child_bones = []
        for co in cos:
            res = self.GN_ROT_CONT(point, co, name, self.EMPTY_Sphere, use_def_bone=True, scale= size / 2 )
            if isinstance(res, list) and len(res) >= 3:  # esperado: [rot, def, cont, dir]
                child_bones.append(res)

        self.SetMode("EDIT")

        # Root
        root_bone = None
        if props.use_eye_root :
            root_bone = self.CreateBone(f"root-{name}")
            if root_bone:
                root_bone.head = center
                root_bone.tail = center + self.GetWorldNormal()
                root_bone.length *= size * 4
                self.SetDeform([root_bone], False)
                self.SetColorBone(root_bone, "THEME01")
        
        
        if props.use_eye_bbone:
            bb_bones = self.CreateBonesRange(f"bb_{name}", len(cos) if not props.eye_use_loop else len(cos)-1)
            for i, bone in enumerate(bb_bones):
                bone.head = cos[i]
                index = i+1
                if props.eye_use_loop:
                    index = cos[index] if index < len(cos) else cos[0]
                bone.tail = index
                bone.display_type = 'BBONE'
                bone.bbone_segments = props.eye_bbone_segments
                bone.bbone_x *= size / 12
                bone.bbone_z *= size / 12
                bone.align_roll(center)
            
            if props.use_eye_semetal_bbone :
                part_1 = bb_bones[:int(len(bb_bones)/2)]
                part_2 = bb_bones[int(len(bb_bones)/2):]
                self.SetRelationsOnlyOneList(part_1, Use_connect=True)
                self.SetRelationsOnlyOneList(part_2, Use_connect=True)
            else :
                self.SetRelationsOnlyOneList(bb_bones, Use_connect=True)
            
        def_bones_name = []
        cont_bones_name = []
        
        for i, child in enumerate(child_bones):
            rot_bone_name = child[0]
            
            def_bone_name = child[1]
            def_bones_name.append(def_bone_name)
            cont_bone_name = child[2]  

            
            cont_bones_name.append(cont_bone_name)
            rot_bone = self.GetBone(rot_bone_name, mode="EDIT")
            cont_bone = self.GetBone(cont_bone_name, mode="EDIT")
            def_bone = self.GetBone(def_bone_name, mode="EDIT")
            rot_bone.display_type = 'STICK'

            if props.use_eye_bbone :
                if i == 0:
                    bb_bones[i].use_connect = False
                    bb_bones[i].parent = def_bone
                
                elif i == int((len(bb_bones))/2) and not props.use_eye_semetal_bbone:
                    bb_bones[i].use_connect = False
                    bb_bones[i].parent = def_bone
            
            if props.use_eye_root :
                rot_bone.parent = root_bone
                cont_bone.parent = root_bone
            
            self.SetDeform([def_bone], props.use_deform_bone)

        # ----- Pasar a POSE y aplicar constraints -----
        root_bone_name = self.GetNameToBones([root_bone]) if root_bone else []
        bb_bones_name = self.GetNameToBones(bb_bones) if props.use_eye_bbone else []
        self.SetMode("POSE")
        root_bone_p = self.GetBones(root_bone_name, "POSE")[0] if root_bone_name else None
        def_bones = self.GetBones(def_bones_name,  "POSE")
        cont_bones = self.GetBones(cont_bones_name, "POSE")
        bb_bones_p = self.GetBones(bb_bones_name, "POSE") if props.use_eye_bbone else []
        
        
        if root_bone_p:
            root_bone_p.custom_shape = self.EMPTY_Circle
            root_bone_p.custom_shape_rotation_euler[0] = 1.5708
            root_bone_p.custom_shape_scale_xyz *= size * 1.25

        if cont_bones and def_bones :
            for bone_a, bone_b in zip(cont_bones, def_bones) :
               bone_a.custom_shape_transform = bone_b

        for bone in def_bones :
            bone.custom_shape = self.EMPTY_Circle
            bone.custom_shape_rotation_euler[0] = 1.5708
            bone.custom_shape_scale_xyz *= size / 4

        if bb_bones_p :
            for i, bone in enumerate(bb_bones_p) :
                index = i+1
                sub_target = def_bones_name[index] if index < len(def_bones_name) else def_bones_name[0]
                
                const = bone.constraints.new(type='COPY_ROTATION')
                const.target = arm
                const.subtarget = def_bones_name[i]
                const.target_space = 'LOCAL'
                const.owner_space = 'LOCAL'
                
                const = bone.constraints.new(type='COPY_TRANSFORMS')
                const.target = arm
                const.subtarget = def_bones_name[i]
                
                
                const = bone.constraints.new(type='STRETCH_TO')
                const.target = arm
                const.subtarget = sub_target
                const.bulge = 0
            self.SelectBones(bb_bones_p, mode="POSE")
            bpy.ops.pose.armature_apply(selected=True)
        
        self.WithDistanceWeights(obj, arm)
        self.KeepObject(obj, arm)
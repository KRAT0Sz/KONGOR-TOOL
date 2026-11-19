
import bpy
from ..generaldata import *
from types import SimpleNamespace
import bmesh
from mathutils import Vector

"""
Operaciones Generales que utiliso en diferentes Operadores
"""

Matrix = None

class OperatorGeneral(GeneralArmatureData):
    
        

    def SetContBendyBone(self):
        
        try :
        
            if self.GetObjMode() != "POSE" : return
            act_bone = self.GetActiveBone(mode="POSE")
            select_bone = self.GetSelectBones(mode="POSE")
            prop = self.Props()
            
            if act_bone and select_bone: 
                for bone in select_bone[:]:
                    if bone == act_bone : 
                        select_bone.remove(bone)
                        
                if prop.bendybone_type != {"PARENT"} :
                    selct_bones_1 = select_bone[0] if not prop.bendy_bone_invest else select_bone[1]
                    selct_bones_2 = select_bone[1] if not prop.bendy_bone_invest else select_bone[0]
            
                if prop.bendybone_type == {"ROTATION"} :

                    act_bone = self.GetBone(act_bone.name, mode="OBJECT")
                    act_bone.bbone_handle_type_start = 'TANGENT'
                    act_bone.bbone_handle_type_end = 'TANGENT'
                    act_bone.bbone_handle_use_ease_start = True
                    act_bone.bbone_handle_use_ease_end  = True
                    act_bone.bbone_custom_handle_start = self.GetBone(selct_bones_1.name, mode="OBJECT")
                    act_bone.bbone_custom_handle_end = self.GetBone(selct_bones_2.name, mode="OBJECT")
                
                elif prop.bendybone_type == {"SCALE"} :
                    for i in range(3) : 
                        self.CreatreDrive(
                            act_bone, "bbone_scalein",
                            selct_bones_1, f"scale[{i}]",
                            Use_Bone=True,
                            index= i
                        )

                        self.CreatreDrive(
                            act_bone, f"bbone_scaleout",
                            selct_bones_2, f"scale[{i}]", 
                            Use_Bone=True, 
                            index= i
                        )
                        
                elif prop.bendybone_type == {"PARENT"} :
                    
                    def haveconstraint() -> bool:
                        for bone in select_bone :
                            if bone.parent and bone.parent.name == bone.name+"RGC_CONTROL" :
                                return True
                        return False
                    if not haveconstraint() : 
                        GetName = self.GetNameToBones(select_bone)
                        GetNameActBone = act_bone.name
                        self.SetMode(mode="EDIT")
                        select_bone_edit = self.GetBones(GetName, mode="EDIT")
                        act_bone_pose = self.GetBone(GetNameActBone, mode="POSE")
                        if select_bone_edit :
                            Names = []
                            for i in range(len(select_bone_edit)) :
                                Names.append(self.GN_Name(new_name=select_bone_edit[i].name, bone_name="RGC_CONTROL"))
                            cont_bones = self.CreateBones(Names)
                            if cont_bones :
                                self.SetTransformToBones(cont_bones, select_bone_edit, length_value=0.5)
                                for i, bone in enumerate(cont_bones) :
                                    self.SetDisplaySize(bone, select_bone_edit[i])
                                self.SetDeform(cont_bones, False)
                                for i in range(len(cont_bones)) :
                                    select_bone_edit[i].parent = cont_bones[i]
                        cont_bones_name = self.GetNameToBones(cont_bones)
                        self.SetMode(mode="POSE")
                        cont_bones_pose = self.GetBones(cont_bones_name, mode="POSE")
                        if cont_bones_pose : 
                            for bone in cont_bones_pose :
                                constraint = bone.constraints.new(type='ARMATURE')
                                constraint.targets.new()
                                for i, tgt in enumerate(constraint.targets):
                                    if tgt.target is None:
                                        constraint.targets[i].target = self.GetActiveObject()
                                        constraint.targets[i].subtarget = act_bone_pose.name
                                        constraint.targets[i].weight = 1.0
                    else :
                        parent_name = []
                        for bone in select_bone:
                            if bone.parent is not None:
                                parent_name.append(bone.parent.name)
                            
                        parent_bones = self.GetBones(parent_name, mode="POSE")
                        if parent_bones :
                            for bone in parent_bones :
                                if bone.constraints :
                                    for cont in bone.constraints :
                                        if cont.type == "ARMATURE" :
                                            cont.targets.new()
                                            for i, tgt in enumerate(cont.targets):
                                                if tgt.target is None:
                                                    cont.targets[i].target = self.GetActiveObject()
                                                    cont.targets[i].subtarget = act_bone.name
                                                cont.targets[i].weight = 1.0 / len(cont.targets)
        except : 
            print("Error")
        
               
    def GetConstraintArmatureToIK(self) : 
        
        self.SetMode(mode="EDIT") 
        
        get_constraint_to_armature = self.GetBones(
            ["ik_arm_L.003", "ik_arm_R.003", "ik_leg_L", "ik_leg_R"], mode="EDIT"
            )
        
        get_name_new_bone = []
        
        for bone in get_constraint_to_armature : 
            
            new_bone = self.CreateBonesRange(bone.name, 1)
            get_name_new_bone.append(new_bone[0].name)
            self.SetTransform(new_bone[0], bone)
            self.SetDeform(new_bone, False)
            self.SetDisplaySize(new_bone[0], bone)
            bone.parent = new_bone[0]
                
        self.SetMode(mode="POSE") 
        
        get_constraint_to_armature = self.GetBones(
            ["ik_arm_L.003", "ik_arm_R.003", "ik_leg_L", "ik_leg_R"], mode="POSE"
        )
        new_bones = self.GetBones(get_name_new_bone, mode="POSE")
        
        for i, bone in enumerate(get_constraint_to_armature) : 
            
            constraint = self.GetConstraintActive(bone)
            Select = new_bones[i]
            
            new_constraint = Select.constraints.new(type=constraint.type)
            
            for attr in dir(constraint):
                if not attr.startswith("_") and not callable(getattr(constraint, attr)):
                    try:
                        setattr(new_constraint, attr, getattr(constraint, attr))
                    except AttributeError:
                        pass
            
            # Handle targets for ARMATURE constraint type
            if constraint.type == 'ARMATURE':
                # Ensure the new constraint has the correct number of targets
                while len(new_constraint.targets) < len(constraint.targets):
                    new_constraint.targets.new()

                for i, tgt in enumerate(constraint.targets):
                    if tgt.target is not None:
                        new_constraint.targets[i].target = tgt.target
                        new_constraint.targets[i].subtarget = tgt.subtarget
                        new_constraint.targets[i].weight = tgt.weight
                        
                        # Verificar si el target tiene un driver y copiarlo
                        if tgt.id_data.animation_data and tgt.id_data.animation_data.drivers:
                            driver = None
                            for d in tgt.target.animation_data.drivers:
                                # Filtrar el driver que afecta específicamente el weight del target
                                if d.data_path == f'pose.bones["{bone.name}"].constraints["{constraint.name}"].targets[{i}].weight':
                                    driver = d
                            if not driver : continue
                            variables = driver.driver.variables
                            
                            def add_drive(
                                Obj : object, Propertie : str, Control_Obj : object, 
                                Control_Propertie : str,  Use_Bone : bool = False, 
                                Use_Expression : bool = False, Expression : str = "-1", ):
                                # Agregar un controlador (driver) a la propiedad del objeto
                                driver = Obj.driver_add(Propertie).driver
                                driver.type = 'SCRIPTED'
                                
                                # Crear una nueva variable para el driver
                                var = driver.variables.new()
                                var.name = variables[0].name
                                var.targets[0].id_type = "OBJECT"
                                var.targets[0].id = self.GetActiveObject()
                                
                                # Si se está usando un hueso, agregar la ruta correspondiente
                                if Use_Bone:
                                    var.targets[0].data_path = f'pose.bones["{Control_Obj.name}"].{Control_Propertie}'
                                else:
                                    # Si no es un hueso, asignar la propiedad directamente
                                    var.targets[0].data_path = Control_Propertie
                                

                                if Use_Expression : driver.expression = Expression
                                else : driver.expression = "var"
                            
                            add_drive(
                                new_constraint.targets[i], 
                                f"weight", 
                                driver, 
                                variables[0].targets[0].data_path, 
                                Use_Expression=True, 
                                Expression=driver.driver.expression
                                )
                            
            
            bone.constraints.remove(constraint)
            
            # Recorrer las colecciones
            for col in self.GetCollections():
                
                if Select.name in self.GetBonesNamesInCollection(col.name) : 
                    # Verificar si el hueso está en la colección actual
                    bpy.ops.armature.collection_unassign_named(
                        name=col.name, 
                        bone_name=Select.name
                    )

            Select.bone.select = True
            bpy.ops.armature.collection_assign(name="Control_Bone")


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
            
        if props.mesh_keep_object : 
            self.SetMode(mode="OBJECT")
            armature = self.GetActiveObject()
            self.ActiveObj(obj)
            self.SetMode(mode="EDIT")
            armature.select_set(True)
    
    
    def CurveToBone(self): 
        # Obtener el objeto activo (suponiendo que es una curva)
        curve = self.GetActiveObject()
        select_obj = self.GetSelectableObjects()
        selected_curve = []
        hook_bones = []
        
        # Asegurarse de estar en modo edición para la curva
        if curve.mode == 'EDIT':
            # Verificar si la curva es de tipo NURBS o Bezier
            for spline in curve.data.splines:
                if spline.type == 'BEZIER':
                    for point in spline.bezier_points:
                        selected_curve.append(point.co.copy())  # Agregar coordenadas del punto Bezier
                else:
                    for point in spline.points:
                        selected_curve.append(point.co.copy())  # Agregar coordenadas del punto NURBS

        
        armature = None
        for obj in select_obj: 
            if obj.type == "ARMATURE": 
                armature = obj
                break
        
        
        
        # Salimos del modo edición para la curva antes de trabajar con el armature
        self.SetMode(mode="OBJECT")
        props = self.Props()

        # Función para calcular las nuevas coordenadas considerando la matriz mundial del objeto
        def n_co(co, curve_obj): 
            # Aplicar correctamente la matriz mundial a un Vector4 y devolver Vector3
            co_world = curve_obj.matrix_world @ co.to_4d()  # Asegúrate de convertir a Vector4 para la multiplicación
            return co_world.to_3d()  # Convertir a Vector3 para obtener solo la parte XYZ
        
        # Función para crear los huesos
        def set_bone(curve_obj):
            
            
            index = len(selected_curve)  # Número de puntos seleccionados
            # Crear huesos basados en el rango
            bones_new = self.CreateBonesRange(Bone_Name=props.curve_bone_name, Range=index)
            r_bone = None
            if props.curve_use_reference_bone :
                r_bone = self.GetBone(props.curve_reference_bone_name, mode="EDIT")
            # Configurar deformación de los huesos
            self.SetDeform(bones_new)
            
            hook_bones = self.GetNameToBones(bones_new) 
            
            # Asignar coordenadas a los huesos
            for i in range(index):
                
                # Obtener la posición del punto transformada por la matriz mundial de la curva
                head = n_co(selected_curve[i], curve_obj)  # Calcular la posición de la cabeza del hueso
                
                bones_new[i].head = head
                bones_new[i].tail = head + self.GetWorldNormal()  # Ajustar la cola para darle longitud al hueso
                if r_bone :
                    bones_new[i].length = r_bone.length
                    self.SetDisplaySize(bones_new[i], r_bone)
                
            # Ajustes adicionales si necesitas rotación o manipular más huesos
            if props.curve_use_control == True:
                bones_rot = self.CreateBonesRange(Bone_Name="rot_" + props.curve_bone_name, Range=index - 1)
                
                self.SetDeform(bones_rot)
                for i in range(index-1):
                    bones_rot[i].head = bones_new[i].head  # Si tienes otras propiedades que configurar
                    bones_rot[i].tail = bones_new[i+1].head
                    if r_bone : self.SetDisplaySize(bones_rot[i], r_bone)
                    if i != 0 : 
                        bones_rot[i].parent = bones_rot[i-1]
                        bones_rot[i].use_connect = True
                    bones_new[i].parent = bones_rot[i]
                bones_new[-1].parent = bones_rot[-1]
                self.SelectBones(bones_rot, mode="EDIT")
                GeneratorsBones().GN_Fingers()
            
            return hook_bones
        
        # Asegurarse de que la armadura esté en la capa activa y en modo edición
        if armature:
            curve = self.GetActiveObject()  # Obtener el objeto activo actual
            self.ActiveObj(armature)  # Activar el objeto armature
            self.SetMode(mode="EDIT")
            hook_bones = set_bone(curve)	
        else:
            # Si no hay armature, crear una nueva armadura
            curve = self.GetActiveObject()
            bpy.ops.object.armature_add(enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            armature = self.GetActiveObject()
            self.SetMode(mode="EDIT")
            self.RemoveBones(["Bone"])  # Eliminar el hueso predeterminado si es necesario
            hook_bones = set_bone(curve)
        
        self.SetMode(mode="OBJECT")
        self.ActiveObj(curve)
        Modifiers = []
        for i in range(len(selected_curve)):
            M = curve.modifiers.new(name = "", type='HOOK')
            M.object = armature
            M.subtarget = hook_bones[i]
            Modifiers.append(M)
            
        self.SetMode(mode="EDIT")
        
        def set_points(points):
            
            # Asignar cada punto de la curva a su respectivo modificador Hook
            for i, point in enumerate(points):
                # Para asegurar que no superamos el número de modificadores disponibles
                for p in points:
                     p.select = False
                     
                if i < len(Modifiers):
                    mod = Modifiers[i]
                    # Deseleccionar todos los puntos de nuevo para asegurarse de que no hay selección múltiple
                    point.select = True
                    bpy.ops.object.hook_assign(modifier=mod.name)
            
            
        if curve.mode == 'EDIT':
            # Verificar si la curva es de tipo NURBS o Bezier
            for spline in curve.data.splines:
                if spline.type == 'BEZIER':
                    set_points(spline.bezier_points)
                else:
                    set_points(spline.points)
                    
        self.ActiveObj(armature, use_deselect=False)
        bpy.ops.object.parent_set(type='ARMATURE_NAME')

    def AplicarScale(self):
        save_scale = self.GetActiveObject().scale.copy()
        self.SetMode(mode="OBJECT")
        
        for obj in self.GetSelectableObjects():
            # Asegurarse de que el objeto sea el activo y que no sea un objeto vacío
            if obj.type != 'EMPTY':  
                if obj.type == 'ARMATURE':
                    # Si el objeto no tiene múltiples usuarios, simplemente aplicar las transformaciones
                    bpy.context.view_layer.objects.active = obj
                    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                    
                    self.SetMode(mode="POSE")
                    
                    for bone in obj.pose.bones:
                        for i in range(3):  # Normalizar cada componente de la escala, rotación y traslación
                            bone.custom_shape_translation[i] *= save_scale[i]

                        for cont in bone.constraints:
                            
                            if cont.type == "STRETCH_TO":
                                cont.rest_length = 0
                                
                            if cont.type == "LIMIT_LOCATION":
                                
                                if cont.min_x != 0 :
                                    cont.min_x *= save_scale[0]
                                if cont.min_y != 0 :
                                    cont.min_y *= save_scale[0]
                                if cont.min_z != 0 :
                                    cont.min_z *= save_scale[0]
                                    
                                if cont.max_x != 0 :
                                    cont.max_x *= save_scale[0]
                                if cont.max_y != 0 :
                                    cont.max_y *= save_scale[0]
                                if cont.max_z != 0 :
                                    cont.max_z *= save_scale[0]
                                    
                    self.SetMode(mode="OBJECT")
                
    def SetDriveToOldRigCreator(self):
        
        new_drive = [
            "head", "eyes", 
            
        ]
        old_drive = [
            "Cabeza_Global_Local", "Ojos_Global_Local", 
        ]
        for type in ["R", "L"] : 
            old_drive.append(f"Brazo_IK_FK_{type}")
            old_drive.append(f"Brazo_IK_Stretch_{type}")
            old_drive.append(f"Brazo_Rot_Mov_{type}")
            old_drive.append(f"Global_Local_Brazo_{type}")
            
            old_drive.append(f"Pierna_IK_Fk_{type}")
            old_drive.append(f"Pierna_IK_Stretch_{type}")
            old_drive.append(f"Pierna_Rot_Mov_{type}")
            
            new_drive.append(f"arm_ik_fk_{type}")
            
            mi_type = "L" if type == "R" else "R"
            new_drive.append(f"arm_stretch_to_{mi_type}")
            new_drive.append(f"arm_rot_{mi_type}")
            
            new_drive.append(f"arm_followed_{type}")
            
            new_drive.append(f"leg_ik_fk_{type}")
            new_drive.append(f"leg_stretch_to_{type}")
            new_drive.append(f"leg_rot_{type}")
            
        
        for i, old in enumerate(old_drive) : 

            if hasattr(self.GetActiveObject().data, f'["{old}"]') :
                self.GetActiveObject().data.driver_remove(f'["{old}"]')
                self.CreatreDrive(
                    self.GetActiveObject().data, f'["{old}"]', 
                    self.GetActiveObject(), f"RGC_Armature_GrupsProps[0].{new_drive[i]}", 
                    Use_Bone=False
                )

    def SetProperties(self):
        props = bpy.context.scene.RGC_GrupsProps
        
        # Para Crear la lista de Genradores Disponibles
        Generators = GeneralArmatureData().ListGenerators()
        for g in Generators:
            grups = props.Generators_List.get(g)
            if not grups:
                new = props.Generators_List.add()
                new.name = g

    def AddPropertiesRigCreator(self):
        self.PropsToArmature().add()
    
    def AddCollectionToArmature(self):
        for col in self.ListCollectionToArmature():
            if col not in self.GetCollectionsNames() :
                self.GetActiveObject().data.collections.new(col)
        
    def SelectBoneToCollection(self, Col_Name : str, Mode : str = "POSE", value : bool = True):
        if Mode == "OBJECT" : return
        if Mode == 'POSE':
            for bone in self.GetCollectionToName(Col_Name).bones:
                bone = self.GetBone(bone.name, "POSE")
                bone.select = value
                if bone.select :
                    self.ActiveBone(bone.name, mode=Mode)
        elif Mode == 'EDIT':
            for bone in self.GetCollectionToName(Col_Name).bones:
                bone.select = value
                if bone.select :
                    self.ActiveBone(bone.name, mode=Mode)

    def OnlySelectBonesInThesCollection(self, Col_Name : str):
        for bone in self.GetActiveObject().data.bones :
            bone.select = False
        for bone in self.GetCollectionToName(Col_Name).bones:
            bone.select = True
            
    def EditIndexCollections(self, Col_Name: str, Type: str):
        # Obtener la colección por nombre
        col = self.GetCollectionToName(Col_Name)
        collections = self.GetActiveObject().data.collections  # Obtener la colección de Armature
        
        # Encontrar el índice de la colección manualmente
        col_index = -1
        for i, c in enumerate(collections):
            if c == col:
                col_index = i
                break
        
        # Verificar si se encontró la colección
        if col_index == -1:
            print(f"Error: Colección '{Col_Name}' no encontrada.")
            return
        
        # Mover hacia arriba
        if Type == "UP":
            new_index = col_index - 1
            new_index = new_index if new_index >= 0 else 0
            collections.move(col_index, new_index)
        
        # Mover hacia abajo
        elif Type == "DOWN":
            new_index = col_index + 1
            new_index = new_index if new_index <= len(collections) - 1 else len(collections) - 1
            collections.move(col_index, new_index)

    def FkaIkoIkaFk(self, type: str = "R", body_part: str = "arm", invert: bool = False):
        index = 3 if body_part == "arm" else 4 

        IK = self.GetBonesToRange(f"ik_{body_part}_{type}", index, mode="POSE")
        FK = self.GetBonesToRange(f"fk_{body_part}_{type}", index, mode="POSE")
        POLE = self.GetBone(
            f"pole{body_part}_{type}", mode="POSE"
        )
        
        IKLEG = self.GetBone(
            f"ik_leg_{type}", mode="POSE"
        )
        ROTFEET = self.GetBone(
            f"rot_feet_{type}", mode="POSE"
        )
        
        # Verificar que tanto IK como FK existan
        if not IK or not FK and POLE:
            return

        # Aplicar transformaciones de IK a FK si invert=True
        if invert:
            for i, fk_bone in enumerate(FK):
                ik_bone = IK[i]
                
                # Aplicar la matriz de IK a FK
                fk_bone.matrix = ik_bone.matrix
                
                # Ajustar la rotación si es necesario
                if i == 1:
                    fk_bone.rotation_quaternion[2] = 0
                    fk_bone.rotation_quaternion[3] = 0
                
                # Ajustar ubicación y escala
                fk_bone.location = (0, 0, 0)
                fk_bone.scale = (1, 1, 1)
            
                # Forzar actualización de la capa de visualización
                bpy.context.view_layer.update()
            return

        # Aplicar transformaciones de FK a IK si invert=False
        for i, ik_bone in enumerate(IK):
            if i > 1 and body_part == "leg": continue
            fk_bone = FK[i]
            
            # Aplicar la matriz de FK a IK
            ik_bone.matrix = fk_bone.matrix
            
            if i == 0:
                # Ajuste cuidadoso de la rotación y transformaciones si es necesario
                ik_bone.location = (0, 0, 0)
                ik_bone.scale = (1, 1, 1)
                ik_bone.rotation_euler[0] = 0  # Ajuste rotación X si es necesario
                ik_bone.rotation_euler[2] = 0  # Ajuste rotación Z si es necesario

            if i == 1:
                # Ajuste cuidadoso para el segundo hueso
                ik_bone.location = (0, 0, 0)
                ik_bone.scale = (1, 1, 1)
                ik_bone.rotation_quaternion[0] = 1  # Solo resetea el primer componente de quaternion
                ik_bone.rotation_quaternion[1] = 0
                ik_bone.rotation_quaternion[2] = 0
                ik_bone.rotation_quaternion[3] = 0

            # Forzar actualización de la capa de visualización
            bpy.context.view_layer.update()

        if body_part == "leg" : 
            IKLEG.matrix = FK[2].matrix
            IKLEG.rotation_quaternion[0] = 1 
            IKLEG.rotation_quaternion[1] = 0 
            IKLEG.rotation_quaternion[2] = 0 
            IKLEG.rotation_quaternion[3] = 0 
            bpy.context.view_layer.update()
            ROTFEET.matrix = FK[-1].matrix
        
        position =  FK[1].z_axis*-1
        # Obtener la posición promedio de FK[0] y FK[1]
        matrix_fk0 = FK[0].matrix
        matrix_fk1 = FK[1].matrix

        # Promediar las matrices FK
        average_fk_matrix = self.MatrixMedFor(matrix_fk0, matrix_fk1)
        
        # Crear la nueva matriz (ubicación, rotación, escala)
        matrix = self.CreateMatrix(location=position, rotation_euler=(0, 0, 0), scale=(1, 1, 1))
        
        # Aplicar la transformación promedio de FK sobre la nueva matriz
        final_matrix = matrix @ average_fk_matrix
        
        # Asignar la matriz resultante a POLE
        POLE.matrix = final_matrix
        POLE.rotation_quaternion[0] = 1
        POLE.rotation_quaternion[1] = 0
        POLE.rotation_quaternion[2] = 0
        POLE.rotation_quaternion[3] = 0
    

    def CopyXformRelationShip(self):
        # Obtener el objeto activo y los objetos seleccionados
        obj = self.GetActiveObject()
        
        # Obtener el hueso activo y los huesos seleccionados
        Bone_Active = self.GetActiveBone()
        Bone_Select = self.GetSelectBones(mode="POSE")
        props = self.Props()  # Configuración de propiedades

        if not Bone_Active or not Bone_Select:
            return

        # Obtener la matriz global del objeto activo y del objeto seleccionado
        object_matrix = obj.matrix_world.copy()

        # Obtener la matriz del primer hueso seleccionado que no sea el hueso activo
        bone = None
        for b in Bone_Select:
            if b != Bone_Active:
                bone = b
                break

        if not bone:
            return

        select_object_matrix = bone.id_data.matrix_world.copy()
        
        # Obtener la matriz local del hueso seleccionado
        if bone.id_data != obj:
            select_matrix = select_object_matrix @ bone.matrix.copy()
            active_matrix = object_matrix @ Bone_Active.matrix.copy() # Matriz global del hueso seleccionado
        else:
            select_matrix = bone.matrix.copy()
            active_matrix = Bone_Active.matrix.copy() 
            
        # Descomponer la matriz del hueso seleccionado
        sloc, srot, ssca = select_matrix.decompose()

        # Obtener la localización del hueso seleccionado en el espacio del hueso activo
        temporal_matrix = active_matrix.inverted() @ select_matrix
        
        loc, rot, sca = temporal_matrix.decompose()

        # Crear una nueva matriz con las transformaciones correspondientes
        new_matrix = mathutils.Matrix.LocRotScale(
            loc , 
            rot if props.use_rotation else srot, 
            sca if props.use_scale else ssca
        )

        # Guardar la matriz descompuesta en las propiedades
        values = []
        for line in new_matrix:
            for value in line:
                values.append(value)

        for i, v in enumerate(values):
            props.save_matrix[i] = v

        props.is_save_matrix = True
        self.report({'INFO'}, f"{Bone_Active.name} Copy Relation Ship to {Bone_Select[0].name}")
        
    def PasteXformRelationShip(self):
        # Obtener el objeto activo y los objetos seleccionados
        obj = self.GetActiveObject()

        # Obtener el hueso activo y los huesos seleccionados
        Bone_Active = self.GetActiveBone()
        Bone_Select = self.GetSelectBones(mode="POSE")
        props = self.Props()  # Configuración de propiedades

        # Obtener la matriz global del objeto activo y del objeto seleccionado
        object_matrix = obj.matrix_world.copy()

        # Reconstruir la matriz a partir de los valores guardados
        values = [props.save_matrix[i] for i in range(16)]  # Suponiendo que la matriz es 4x4 (16 elementos)
        new_matrix = mathutils.Matrix()

        # Asignar los valores a la matriz
        for i in range(4):
            for j in range(4):
                new_matrix[i][j] = values[i * 4 + j]
    
        
        # Aplicar la nueva matriz a los huesos seleccionados
        for bone in Bone_Select:
            if bone != Bone_Active:
                
                loc, rot, sca = bone.matrix.copy().decompose()
                if bone.id_data != obj:
                    active_matrix = object_matrix @ Bone_Active.matrix.copy()
                else : 
                    active_matrix = Bone_Active.matrix.copy()
                new_matrix = active_matrix @ new_matrix
                nloc, nrot, nsca = new_matrix.decompose()
                new_matrix = mathutils.Matrix.LocRotScale(
                    nloc, 
                    nrot if props.use_rotation else rot, 
                    nsca if props.use_scale else sca
                )
                bone.matrix = new_matrix 

                # Insertar keyframe en la localización, rotación y escala de este hueso
                bone.keyframe_insert(data_path="location", frame=bpy.context.scene.frame_current)
                if bone.rotation_mode != 'QUATERNION' :
                    bone.keyframe_insert(data_path="rotation_euler", frame=bpy.context.scene.frame_current)
                else:
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=bpy.context.scene.frame_current)
                bone.keyframe_insert(data_path="scale", frame=bpy.context.scene.frame_current) 
        
        self.report({'INFO'}, "Paste Relation Ship")
        
    def BakeByFrameXformRelationShip(self):
        # Obtener hueso activo y huesos seleccionados
        Bone_Active = self.GetActiveBone()
        Bone_Select = self.GetSelectBones(mode="POSE")
        props = self.Props()  # Configuración de propiedades

        if not Bone_Active or not Bone_Select:
            return

        # Obtener el objeto activo
        obj = self.GetActiveObject()

        # Asegurarse de que el objeto tiene datos de animación
        if obj and obj.animation_data and obj.animation_data.action:
            # Lista de frames clave (keyframes)
            keyframes = set()

            # Recorrer los huesos seleccionados y buscar sus FCurves (Blender 4.x & 5.x compatible)
            action = obj.animation_data.action
            action_fcurves = []
            if hasattr(action, "fcurves"):
                action_fcurves = list(action.fcurves)
            elif hasattr(action, "layers"):
                for layer in action.layers:
                    for strip in getattr(layer, "strips", []):
                        action_fcurves.extend(getattr(strip, "fcurves", []))

            for bone in Bone_Select:
                for fcurve in action_fcurves:
                    if fcurve.data_path.startswith(f'pose.bones["{bone.name}"]'):
                        # Filtrar solo los keyframes seleccionados
                        selected_keyframes = [int(kf.co[0]) for kf in fcurve.keyframe_points if kf.select_control_point]
                        keyframes.update(selected_keyframes)

           # Si se encontraron keyframes, mover el cursor a esos frames
            if keyframes:
                print(f"Keyframes encontrados: {sorted(keyframes)}")
                
                # Obtener la lista ordenada de keyframes
                keyframe_list = sorted(keyframes)

                # Iterar sobre los frames seleccionados
                for i, frame in enumerate(keyframe_list):
                    print(f"Procesando frame {frame}")
                    
                    # Establecer el cursor en el frame actual
                    bpy.context.scene.frame_set(frame)

                    # Forzar una actualización completa de la interfaz
                    bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

                    # Copiar las transformaciones del hueso activo
                    self.CopyXformRelationShip()  

                    # Si hay un siguiente frame, pegar en el siguiente
                    if i < len(keyframe_list) - 1:
                        next_frame = keyframe_list[i + 1]

                        # Establecer el cursor en el siguiente frame
                        print(f"Pegar en frame {next_frame}")
                        bpy.context.scene.frame_set(next_frame)

                        # Forzar actualización antes de pegar
                        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

                        # Pegar las transformaciones en el siguiente frame
                        self.PasteXformRelationShip()

                        # Actualizar la vista para garantizar que las animaciones se vean correctamente
                        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        
                
    # Constraints 
    def ListFunctionToConstraint(self, type : str, use_bone : bool ) :
        List_Def = {
            "REMOVE" : self.RemoveConstraints,
            "DUPLICATE_CONST" : self.DuplicateConstraints,
            "APPLY_CONST" : self.ApplyConstraints,
            "DELETE_ALL" : self.RemoveAllConstraints,
            "COPY_SEL_CONST" : self.CopyConstraints,
            "COPY_SEL_CONST_INDEX" : self.CopyConstraints,
            "UP" : self.MoveConstraints,
            "DOWN" : self.MoveConstraints,
        }
        
        How_Def = List_Def[type]
        if type in {"COPY_SEL_CONST_INDEX", "COPY_SEL_CONST"}:
            How_Def(use_bone, True if type != "COPY_SEL_CONST" else False)
        elif type in {"UP", "DOWN"}:
            How_Def(use_bone, type)
        else:
            How_Def(use_bone)
         
    def RemoveConstraints(self, use_bone : bool = False):
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if X : 
            const = self.GetConstraintActive(X)
            if not const : return
            bpy.ops.constraint.delete(constraint=const.name, owner='BONE' if use_bone else 'OBJECT')
            if X.active_constraint < 1:
                X.active_constraint = 0
            else:
                X.active_constraint = X.active_constraint-1
    
    def DuplicateConstraints(self, use_bone : bool = False) : 
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if X : 
            const = self.GetConstraintActive(X)
            if not const : return
            bpy.ops.constraint.copy(constraint=const.name, owner='BONE' if use_bone else 'OBJECT')
            X.active_constraint += 1
    
    def ApplyConstraints(self, use_bone : bool = False) : 
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if X : 
            const = self.GetConstraintActive(X)
            if not const : return
            bpy.ops.constraint.apply(constraint=const.name, owner='BONE' if use_bone else 'OBJECT')
            if len(X.constraints) > 0:
                X.active_constraint -= 1    
    
    def RemoveAllConstraints(self, use_bone : bool = False):
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if X : 
            for constraint in X.constraints:
                X.constraints.remove(constraint)
    
    def MoveConstraints(self, use_bone : bool = False, type : str = "DOWN"):
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if not X : return 
        
        const = self.GetConstraintActive(X)
        if not const : return
        
        index = X.active_constraint-1 if type == "UP" else X.active_constraint+1
        
        if 0 <= index < len(X.constraints):
            if index > -1 and index < len(X.constraints):
                bpy.ops.constraint.move_to_index(
                    constraint=const.name, 
                    owner='BONE' if use_bone else 'OBJECT', 
                    index=index,
                )
                X.active_constraint = index
        
    def CopyConstraints(self, use_bone : bool = False, use_index=True):
        
        X = self.GetActiveObject() if use_bone == False else self.GetActiveBone()
        if not X : return
        constraint = self.GetConstraintActive(X)
        if not constraint : return
        
        # Get the index of the constraint
        if use_index: 
            constraint_index = X.constraints.find(constraint.name)
        
        X_Select = self.GetSelectableObjects() if use_bone == False else self.GetSelectBones(mode="POSE")
        X_Select.remove(X)
        print(X_Select)
        # Copy the constraint to the selected bones
        for Select in X_Select:
            
            if Select != X:
                new_constraint = Select.constraints.new(type=constraint.type)
                
                for attr in dir(constraint):
                    if not attr.startswith("_") and not callable(getattr(constraint, attr)):
                        try:
                            setattr(new_constraint, attr, getattr(constraint, attr))
                        except AttributeError:
                            pass
                
                # Handle targets for ARMATURE constraint type
                if constraint.type == 'ARMATURE':
                    # Ensure the new constraint has the correct number of targets
                    while len(new_constraint.targets) < len(constraint.targets):
                        new_constraint.targets.new()

                    for i, tgt in enumerate(constraint.targets):
                        if tgt.target is not None:
                            new_constraint.targets[i].target = tgt.target
                            new_constraint.targets[i].subtarget = tgt.subtarget
                            new_constraint.targets[i].weight = tgt.weight
                
                        
                if use_index:        
                    # Move the new constraint to the correct index
                    constraints = Select.constraints
                    for i in range(len(constraints) - 1, constraint_index, -1):
                        constraints.move(i, i-1)

    def ProxyLow(self) :
        self.SetMode("OBJECT")
        self.UpdateViewLayer()
        props = self.Props()
        
        collection = props.pl_collection_to_create_proxy
        collection_name = props.pl_collection_name 
        decimate_ratio = props.pl_decimate_ratio
        armature = props.pl_armature
        detail =  props.ol_detail
        
        type = props.pl_enum
        
        def getnodetree(node_tree : str) :
            import os
            import bpy

            # Guardar Node Trees existentes
            before_data = set(bpy.data.node_groups)

            # Carpeta del archivo .blend donde está el node tree
            parent_file = os.path.dirname(os.path.dirname(__file__))
            blend_file_path = os.path.join(parent_file, 'assets', 'Rig_Creator.blend')

            # Hacer append del NodeTree
            bpy.ops.wm.append(
                filepath=os.path.join(blend_file_path, "NodeTree", node_tree),
                directory=os.path.join(blend_file_path, "NodeTree") + os.sep,
                filename=node_tree,
                link=False
            )
        
        delectmesh = bpy.data.node_groups.get("DelectMesh")
        if not delectmesh : 
            getnodetree("DelectMesh")
            delectmesh = bpy.data.node_groups.get("DelectMesh")
        
        primitive = bpy.data.node_groups.get("Primitive")
        if not primitive : 
            getnodetree("Primitive")
            primitive = bpy.data.node_groups.get("Primitive")
        
        joinprimitive = bpy.data.node_groups.get("JoinPrimitive")
        if not joinprimitive : 
            getnodetree("JoinPrimitive")
            primitive = bpy.data.node_groups.get("JoinPrimitive")
        def CreateProxyCollection(parent_collection = None) :
            nueva_coleccion = bpy.data.collections.get(collection_name)
            if not nueva_coleccion:
                nueva_coleccion = bpy.data.collections.new(collection_name)

            # link solo si no está
            if parent_collection != None :
                parent_col = self.GetParentCollection(parent_collection)
                if parent_col and nueva_coleccion.name not in [c.name for c in parent_col.children]:
                    parent_col.children.link(nueva_coleccion)
            else:
                # Link a la escena principal si no hay parent
                if nueva_coleccion.name not in [c.name for c in bpy.context.scene.collection.children]:
                    bpy.context.scene.collection.children.link(nueva_coleccion)
            return nueva_coleccion
        
        def ProxyObj(obj, is_int : bool = False, nueva_coleccion = None) :
            if obj.type != "MESH":
                return

            # Activar y duplicar
            self.ActiveObj(obj)
            new_obj = obj.copy()
            new_obj.data = obj.data.copy()
            bpy.context.scene.collection.objects.link(new_obj)
            tmodifiers = []
            
            
            if props.pl_enum_type == "DECIMATE" : 
                vertex_count = len(new_obj.data.vertices)
                ratio = decimate_ratio / (vertex_count / props.pl_decimate_ratio_vert)
                ratio = min(ratio, 1.0)  
                
                # Modificador decimate
                if len(new_obj.data.polygons) > 3: 
                    dec = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
                    dec.ratio = ratio
                    tmodifiers.append(dec)
                    
                    dec = new_obj.modifiers.new(name="Decimate", type='DECIMATE')
                    dec.ratio = ratio
                    dec.decimate_type = 'DISSOLVE'
                    dec.angle_limit = props.pl_angle_limit
                    tmodifiers.append(dec)
                    
                    dec = new_obj.modifiers.new(name="Triangulate", type='TRIANGULATE')
                    tmodifiers.append(dec)

            else :
                if len(new_obj.data.polygons) > 3: 
                    
                    groups = [vg.name for vg in new_obj.vertex_groups]
                    bones = [b.name for b in armature.data.bones if b.use_deform]
                    # nombres comunes (intersección)
                    commons = set(groups) & set(bones)
                    # pasarlos a la lista modifiers
                    modifiers = list(commons)
                    
                    if delectmesh :
                        dec = new_obj.modifiers.new(name="DelectMesh", type='NODES')
                        dec.node_group = delectmesh
                        tmodifiers.append(dec)
                    
                    if primitive :
                        
                        # Crear el modificador
                        dec = new_obj.modifiers.new(name="Detail", type='NODES')
                        dec.node_group = joinprimitive

                        # Limpiar todos los nodos existentes en el node tree
                        gn_tree = dec.node_group
                        for n in gn_tree.nodes:
                            gn_tree.nodes.remove(n)

                        # Crear nodo Group Input y Group Output
                        group_input = gn_tree.nodes.new('NodeGroupInput')
                        group_output = gn_tree.nodes.new('NodeGroupOutput')
                        group_input.location = (-400, 0)
                        group_output.location = (800, 0)

                        # Crear Join Geometry
                        join_node = gn_tree.nodes.new('GeometryNodeJoinGeometry')
                        join_node.location = (400, 0)

                        # Conectar Join Geometry al output
                        gn_tree.links.new(join_node.outputs[0], group_output.inputs[0])

                        # Para cada grupo, crear un nodo dentro del Node Group
                        y_offset = 0
                        for m in modifiers:  # modifiers = lista de grupos
                            # Crear un nodo que use el input de la geometría (ej: Geometry Proximity o Custom Node)
                            prim_node = gn_tree.nodes.new("GeometryNodeGroup")
                            prim_node.node_tree = bpy.data.node_groups['Primitive']  # tu Node Group real
                            prim_node.location = (0, y_offset)
                            
                            # Asignar los valores de entrada
                            prim_node.inputs[-2].default_value = m            # primer input: nombre del grupo
                            prim_node.inputs[-1].default_value = detail       # segundo input: detalle
                            
                            # Conectar Input del modificador al nodo
                            gn_tree.links.new(group_input.outputs[0], prim_node.inputs[0])  # ajusta índice si es necesario
                            
                            # Conectar la salida del nodo Primitive al Join Geometry
                            gn_tree.links.new(prim_node.outputs[0], join_node.inputs[-1])
                            
                            y_offset -= 200  # separar nodos verticalmente
                        
                        tmodifiers.append(dec)

            
            if new_obj.data.shape_keys :
                new_obj.shape_key_clear() 
                    
            self.ActiveObj(new_obj)    
            for m in new_obj.modifiers :
                if m.type == 'SUBSURF' :
                    bpy.ops.object.modifier_remove(modifier=m.name)
                if props.pl_enum_type != "DECIMATE" : 
                    if m.type == "MIRROR" :
                        bpy.ops.object.modifier_apply(modifier=m.name)
                    
            # Comprobar si tiene UV_PROJECT
            has_uv_project = any(m.type == 'UV_PROJECT' for m in new_obj.modifiers)

            # Solo borrar materiales si NO tiene UV_PROJECT
            if not has_uv_project and props.pl_delectmaterial:
                new_obj.data.materials.clear()
            
            if len(new_obj.data.polygons) > 3: 
                # invertir lista de modificadores a aplicar                
                for dec in tmodifiers:
                    # Mover al principio
                    mod_index = new_obj.modifiers.find(dec.name)
                    while mod_index > 0:
                        new_obj.modifiers.move(mod_index, mod_index-1)
                        mod_index -= 1
                        
                tm = tmodifiers
                tm.reverse()
                for dec in tm:
                   bpy.ops.object.modifier_apply(modifier=dec.name)
                    
            bpy.ops.object.shade_flat()
            if is_int == False and nueva_coleccion:
                self.LinktoCollectin(nueva_coleccion, new_obj)
                return
            return new_obj
        
        def CreateProxyToCollection(collection) :
            # ---------- Crear colección si no existe ----------
            # Buscar o crear la nueva colección
            # Crear o buscar nueva colección
            # nombre único por colección
            nueva_coleccion = CreateProxyCollection(collection)
                       
            objs_to_proxy = []
            objs_to_inst_proxt = []
            save = set()

            for obj in collection.objects:
                if obj.instance_type == 'COLLECTION' and obj.instance_collection:
                    inst_col = obj.instance_collection
                    grup = []
                    for child_obj in inst_col.objects:
                        if child_obj.name not in save:
                            child_copy = bpy.data.objects.get(child_obj.name)
                            grup.append(child_copy)
                            save.add(child_obj.name)
                    if grup:
                        # usamos el EMPTY original
                        objs_to_inst_proxt.append([grup, obj.name, obj.matrix_world.copy()])
                else:
                    objs_to_proxy.append(obj)

            # Procesar los objetos sueltos
            for obj in objs_to_proxy:
                ProxyObj(obj, nueva_coleccion=nueva_coleccion)

            # Procesar las instancias
            for grup, name_col, matrix in objs_to_inst_proxt:
                new_collection = bpy.data.collections.new(name_col)
                nueva_coleccion.children.link(new_collection)

                for obj in grup:
                    new_obj = ProxyObj(obj, True)
                    self.LinktoCollectin(new_collection, new_obj)

                # crear instancia una sola vez
                bpy.ops.object.collection_instance_add(
                    collection=new_collection.name,
                    align='WORLD',
                    location=(0, 0, 0),
                    scale=(1, 1, 1)
                )
                inst = bpy.context.active_object
                inst.matrix_world = matrix
                # mover la instancia a la colección principal
                for col in list(inst.users_collection):
                    col.objects.unlink(inst)
                nueva_coleccion.objects.link(inst)


            # Ocultar la colección resultante
            nueva_coleccion.hide_viewport = False
            nueva_coleccion.hide_render = True

            collection.hide_viewport = True
            collection.hide_render = False
        
        if type == "COLLECTION" :
            CreateProxyToCollection(collection)
        elif props.pl_enum == "OBJECT":
            nueva_coleccion = CreateProxyCollection()
            for obj in self.GetSelectableObjects() :
                ProxyObj(obj, nueva_coleccion=nueva_coleccion)
                obj.hide_viewport = True
        else :
            nueva_coleccion = CreateProxyCollection()
            for obj in bpy.data.objects :
                if obj.type == "MESH":
                    ProxyObj(obj, nueva_coleccion=nueva_coleccion)
                    obj.hide_viewport = True
import bpy 
from .general import * 
@bpy.app.handlers.persistent
def UpdateNode(dummy) : 
    
    types = ["Get Bone"]
    
    RGC = GeneralArmatureData()
    def get_input_value(node, index=0):
        """Devuelve el valor del socket de entrada del nodo.
        Si está desconectado, devuelve el default_value.
        Si está conectado, devuelve el valor del socket origen."""
        input_socket = node.inputs[index+1]
        
        # Si está conectado
        if input_socket.is_linked:
            from_socket = input_socket.links[0].from_socket
            from_node = from_socket.node
            # Si el socket origen tiene default_value
            if hasattr(from_socket, "default_value"):
                return from_socket.default_value
            else:
                # Si el valor proviene de otro nodo que tiene salida calculable
                return from_node
        else:
            # Si no está conectado
            if hasattr(input_socket, "default_value"):
                return input_socket.default_value
            else:
                return None
            
    def SetConstrint(node) :
        obj = get_input_value(node, 0)
        name_bone = get_input_value(node, 1)
        name_constraint = get_input_value(node, 2)
        add_constraint = get_input_value(node, 3)
        
        if RGC.GetActiveObject().type != "ARMATURE" : return
        if RGC.GetObjMode() != "POSE" : return
        bone = obj.pose.bones.get(name_bone)
        
        if not bone : return
        cont = bone.constraints.get(name_constraint)
        if not cont : 
            cont = bone.constraints.new("GEOMETRY_ATTRIBUTE")
            cont.name = name_constraint
            
        cont.target = obj_target
        cont.attribute_name = f"{bone.name} {name_constraint}"
        cont.data_type = 'FLOAT4X4'


    
    # Obtener la ventana y el área activa donde haya un editor de nodos
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'NODE_EDITOR':
                space = area.spaces.active
                # Verificar que el espacio actual sea un Node Editor de tipo Geometry Nodes
                if hasattr(space, "node_tree") and space.tree_type == 'GeometryNodeTree':
                    tree = space.node_tree
                    obj_target = next(
                        (
                            o for o in bpy.data.objects
                            if any(mod.type == 'NODES' and mod.node_group == tree for mod in o.modifiers)
                        ),
                        None
                    )
                    if tree:
                        for node in tree.nodes:
                            if node.type == "GROUP" and node.node_tree.name in ["Get Bone"] :
                                SetConstrint(node)
                    
                    
                    return  # salir tras encontrar el primero
    

def UPregister() : 
    bpy.app.handlers.depsgraph_update_pre.append(UpdateNode)
def UPunregister() :
    bpy.app.handlers.depsgraph_update_pre.remove(UpdateNode)

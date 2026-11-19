import bpy, os, platform

def update_all_tab_names(self, context):
    try:
        from . import auto_rig
        auto_rig.update_arp_tab()
    except:
        pass
    
    try:
        from . import auto_rig_ge
        auto_rig_ge.update_arp_tab()
    except:
        pass
        
    try:
        from . import auto_rig_smart
        auto_rig_smart.update_arp_tab()
    except:
        pass
      
    try:
        from . import auto_rig_remap
        auto_rig_remap.update_arp_tab()
    except:
        pass
        
    try:
        from . import rig_functions
        rig_functions.update_arp_tab()
    except:
        pass
        
        
def get_documents_path(other_folder):
    home = os.path.expanduser("~")  # Obtient le chemin du répertoire de base de l'utilisateur
    documents = ""

    if platform.system() == "Windows":
        documents = os.path.join(home, "Documents")
    else:
        documents = os.path.join(home, "Documents")
    
    p = os.path.join(documents, 'KONGOR Rig')
    p = os.path.join(p, other_folder)
    
    return p
   

class ARP_MT_arp_addon_preferences(bpy.types.AddonPreferences):
    bl_idname = __package__.split('.')[0]
    arp_tab_name : bpy.props.StringProperty(name='Interface Tab', description='Name of the tab to display the interface in', default='KONGOR Rig', update=update_all_tab_names)
    arp_tools_tab_name : bpy.props.StringProperty(name='Tools Interface Tab', description='Name of the tab to display the tools (IK-FK snap...) interface in', default='Tool', update=update_all_tab_names)
    
    beginner_mode: bpy.props.BoolProperty(name='Beginner Mode', default=True)
    custom_armatures_path: bpy.props.StringProperty(name='Armatures', subtype='FILE_PATH', default=get_documents_path('Armatures Presets'), description='Path to store armature presets')
    custom_limb_path: bpy.props.StringProperty(name='Limbs', subtype='FILE_PATH', default=get_documents_path('Custom Limbs'), description='Path to store custom limb presets')
    rig_layers_path: bpy.props.StringProperty(name='Rig Layers', subtype='FILE_PATH', default=get_documents_path('Rig Layers'), description='Path to store rig layers presets')
    remap_presets_path: bpy.props.StringProperty(name='Remap Presets', subtype='FILE_PATH', default=get_documents_path('Remap Presets'), description='Path to store remap presets')
    ge_presets_path: bpy.props.StringProperty(name='Export Presets', subtype='FILE_PATH', default=get_documents_path('Game Engine Presets'), description='Path to store game engine export presets')
    
    default_ikfk_arm: bpy.props.EnumProperty(items=(('IK', 'IK', 'IK'), ('FK', 'FK', 'FK')), description='Default value for arms IK-FK switch', name='IK-FK Arms Default')
    default_ikfk_leg: bpy.props.EnumProperty(items=(('IK', 'IK', 'IK'), ('FK', 'FK', 'FK')), description='Default value for legs IK-FK switch', name='IK-FK Legs Default')
    default_head_lock: bpy.props.BoolProperty(default=True, name='Head Lock Default', description='Default value for the Head Lock switch')
    remove_existing_arm_mods: bpy.props.BoolProperty(default=True, name='Remove Armature Modifiers', description='Remove existing armature modifiers when binding')
    remove_existing_vgroups: bpy.props.BoolProperty(default=True, name='Remove Existing Vertex Groups', description='Remove existing vertex groups when binding')
    rem_arm_mods_set: bpy.props.BoolProperty(default=False, description='Toggle to be executed the first time binding, to set default prefs')
    rem_vgroups_set: bpy.props.BoolProperty(default=False, description='Toggle to be executed the first time binding, to set default prefs')
    show_export_popup: bpy.props.BoolProperty(default=True, description='Show a popup notification on export completion')
    
    
    def draw(self, context):
        col = self.layout.column(align=True)
        col.prop(self, 'beginner_mode', text='Beginner Mode (help buttons)')
        col.separator()
        
        col.label(text='Rig:')
        col.prop(self, 'remove_existing_arm_mods', text='Remove Existing Armature Modifiers when Binding')
        col.prop(self, 'remove_existing_vgroups', text='Remove Existing Vertex Groups when Binding')
        col.separator()
        col.prop(self, 'default_ikfk_arm', text='IK-FK Arms')
        col.prop(self, 'default_ikfk_leg', text='IK-FK Legs')
        col.prop(self, 'default_head_lock', text='Head Lock')
        
        col.separator()
        col.separator()
        col.label(text='Interface:')
        col.prop(self, 'arp_tab_name', text='Main ARP Tab')
        col.prop(self, 'arp_tools_tab_name', text='Tools Tab')
        col.prop(self, 'show_export_popup', text='Show Popup when Export Finished')

        col.separator()
        col.separator()
        col.label(text='Paths:')
        col.prop(self, 'custom_armatures_path')
        col.prop(self, 'custom_limb_path')
        col.prop(self, 'rig_layers_path')
        col.prop(self, 'remap_presets_path')
        col.prop(self, 'ge_presets_path')
        
        col.separator()
        col.separator()
        col.label(text='Special-Debug:', icon='ERROR')
        col.prop(context.scene, 'arp_disable_smart_fx')
        col.prop(context.scene, 'arp_debug_mode')
        col.prop(context.scene, 'arp_debug_bind')
        col.prop(context.scene, 'arp_experimental_mode')
        

def register():
    from bpy.utils import register_class

    try:
        register_class(ARP_MT_arp_addon_preferences)
    except:
        pass
    bpy.types.Scene.arp_debug_mode = bpy.props.BoolProperty(name='Debug Mode', default=False, description = 'Run the addon in debug mode for debugging purposes.\nWarning, can generate earthquakes and solar tempest. Do not enable for normal usage!', options={'HIDDEN'})
    bpy.types.Scene.arp_debug_bind = bpy.props.BoolProperty(name='Debug Bind', default=False, description='Enable Debug mode for bind functions, for debugging purposes.\nWarning, will break tools and generate earthquakes!\nDo not enable for normal usage!', options={'HIDDEN'})
    bpy.types.Scene.arp_experimental_mode = bpy.props.BoolProperty(name='Experimental Mode', default=False, description = 'Enable experimental, unstable tools. Warning, can lead to errors. Use it at your own risks.', options={'HIDDEN'})
    bpy.types.Scene.arp_disable_smart_fx = bpy.props.BoolProperty(name='Disable Smart FX', default=False, description='Disable Smart markers FX for debug purposes, such as Mac systems not supporting some graphics. Safe to use.', options={'HIDDEN'})
    
def unregister():
    from bpy.utils import unregister_class
    try:
        unregister_class(ARP_MT_arp_addon_preferences)
    except:
        pass

    for prop in ('arp_debug_mode', 'arp_debug_bind', 'arp_experimental_mode', 'arp_disable_smart_fx'):
        if hasattr(bpy.types.Scene, prop):
            try:
                delattr(bpy.types.Scene, prop)
            except:
                pass

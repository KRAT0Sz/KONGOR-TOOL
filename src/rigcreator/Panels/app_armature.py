

import bpy


def AddArmature(self, context):
    layout = self.layout
    layout.menu("rgc.add_armature")
    
    ...




class RGC_Menu_K2(bpy.types.Menu):
    bl_idname = "rgc.add_k2"
    bl_label = "K2 Engine (Heroes of Newerth)"

    def draw(self, context):
        layout = self.layout
        layout.operator("kongor.add_k2_rig", text="K2 Game Human Rig (Bip01)", icon="OUTLINER_OB_ARMATURE").rig_type = "Human For Games"
        layout.operator("kongor.add_k2_rig", text="K2 Flat Hierarchy Rig", icon="OUTLINER_OB_ARMATURE").rig_type = "Human Flat Hierarchy"
        layout.separator()
        layout.operator("kongor.remap_to_k2", text="Remap Bones to K2 Standard (Bip01)", icon="SYNTAX_ON").reverse = False
        layout.operator("kongor.remap_to_k2", text="Remap Bones to Rig Creator (def_)", icon="SYNTAX_OFF").reverse = True
        layout.operator("kongor.setup_k2_deform", text="Prepare Rig for K2 Export", icon="CHECKMARK")

class RGC_Menu_AddArmature(bpy.types.Menu):
    bl_idname = "rgc.add_armature"
    bl_label = "Rig Creator"

    def draw(self, context):
        layout = self.layout
        layout.menu("rgc.add_k2", text="K2 Engine / HoN Rigs", icon="GAME")
        layout.separator()
        layout.operator(
            "rgc.add_armature", text="Human", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Human"
        
        layout.menu("rgc.add_for_games", text="For Games")
        layout.menu("rgc.add_body_parts", text="Body Parts")
        layout.separator()
        layout.menu("rgc.add_extras", text="Extras")
        layout.menu("rgc.autos", text="Autos")

class RGC_Menu_ForGames(bpy.types.Menu):
    bl_idname = "rgc.add_for_games"
    bl_label = "For Games"

    def draw(self, context):
        layout = self.layout 
        layout.operator(
            "rgc.add_armature", text="Human For Games", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Human For Games"  
        layout.operator(
            "rgc.add_armature", text="Human Flat Hierarchy", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Human Flat Hierarchy" 

class RGC_Menu_AddExtras(bpy.types.Menu):
    bl_idname = "rgc.add_extras"
    bl_label = "Extras"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "rgc.add_armature", text="Basic Human", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Basic Human"
        layout.operator(
            "rgc.add_armature", text="Cartoon Human", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Cartoon Human"
        layout.operator(
            "rgc.add_armature", text="Reference Human", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Reference Human"
        layout.operator(
            "rgc.add_armature", text="Human Sin RigCreator", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Human Sin RigCreator"
        

class RGC_Menu_AddBodyParts(bpy.types.Menu):
    bl_idname = "rgc.add_body_parts"
    bl_label = "Body Parts"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "rgc.add_armature", text="Cartoon Face", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Cartoon Face"
        layout.operator(
            "rgc.add_armature", text="Reference Cartoon Face", 
            icon="OUTLINER_OB_ARMATURE"
        ).type = "Reference Cartoon Face"

class RGC_Menu_Autos(bpy.types.Menu):
    bl_idname = "rgc.autos"
    bl_label = "Body Parts"

    def draw(self, context):
        layout = self.layout
        layout.operator(
            "rgc.add_armature", text="Car", 
        ).type = "Car"
        layout.operator(
            "rgc.add_armature", text="Reference Car", 
        ).type = "Reference Car"
        
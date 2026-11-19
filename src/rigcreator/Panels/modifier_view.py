
import bpy
from .general import *


class DrawModifierView(GeneralArmatureData):
    def DrawModifier(self, layout, modifiers):
        for i, m in enumerate(modifiers) :
            box = layout.box()
            row = box.row(align=True)
            row.prop(m, "object", text="")
            row.prop(m, "modifier", text="")
            op = row.operator("rgc.modifier_view", text="", icon="PANEL_CLOSE")
            op.type = "REMOVE"
            op.index = i
            row = box.row(align=True)
            row.prop(m, "use_key", text="Key")
            row_ = row.row(align=True)
            row_.enabled = m.use_key
            row.prop(m, "key", text="")
            
            self.DrawModifierProps(box, m, i)
     
    def DrawModifierProps(self, layout, modifier_view, index):
        if not modifier_view:
            layout.label(text="No modifier selected.")
            return

        if modifier_view.object is None or modifier_view.modifier is None:
            layout.label(text="No modifier selected.")
            return 
        modifier = modifier_view.object.modifiers.get(modifier_view.modifier)
        if modifier is None:
            layout.label(text="Modifier not found.")
            return
        if self.Panel(layout, f"{modifier.name}_{index}", f"{modifier.name}", "") == False:
            return

        for prop in modifier.bl_rna.properties:
            identifier = prop.identifier
            
            if identifier in {"rna_type", "name", "type", "show_expanded", "show_on_cage", "show_in_editmode"}:
                continue  # Ignorar propiedades comunes

            if not prop.is_readonly:
                try:
                    
                    if modifier_view.use_key :
                        if modifier_view.key.lower() in identifier.lower() :
                            text = item.name.replace(f"{modifier_view.key}", "")
                            layout.prop(modifier, identifier, text=text)
                    else:
                        layout.prop(modifier, identifier)
                except Exception as e:
                    print(f"No se pudo dibujar {identifier}: {e}")
       
        if modifier.type == 'NODES' and modifier.node_group:
            
            for item in modifier.node_group.interface.items_tree:
                if item.in_out != 'INPUT':
                    continue
                
                identifier = item.identifier

                if modifier_view.use_key and modifier_view.key.lower() not in item.name.lower():
                    continue

                if identifier :
                    try:
                        text = item.name.replace(f"{modifier_view.key}", "")
                        layout.prop(modifier, f'["{identifier}"]', text=text)
                    except Exception as e:
                        print(f"Error mostrando '{identifier}': {e}")


class RGC_Panel_Modifier(GN_RigCreatorViewPort, DrawModifierView, bpy.types.Panel):
    bl_idname = "RGC_Panel_Modifier"
    bl_label = "Modifier View"
    
    @classmethod
    def poll(cls, context):
        Self = GeneralArmatureData()        
        return context.active_object and context.active_object.type == "ARMATURE"\
            and Self.PanelType([{"ALL"}, {"RIG"}])
    
    
    def draw(self, context):
        layout = self.layout
        props = self.PropsToObject()
        
        if props : 
            modifiers = props.modifer_view 
            self.DrawModifier(layout, modifiers)
            

            layout.operator(
                "rgc.modifier_view", 
                text="Add Modifier View",
                icon="ADD"
            ).type = "ADD"
            

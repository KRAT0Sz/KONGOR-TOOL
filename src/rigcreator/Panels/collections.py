import bpy
from .general import *
from ..generaldata import GeneralArmatureData

from ..operator import RGC_OperatorCollections

how_col = ""

class RGC_Panel_Collections(GN_RigCreatorViewPort, bpy.types.Panel):
    bl_idname = "RGC_Panel_Collections"
    bl_label = "Collections"

    
    @classmethod
    def poll(cls, context):        
        Self = GeneralArmatureData()
        return Self.GetArmature() and Self.PanelType([{"ALL"}, {"ANIMATION"}])
    
    
    def DrawCollections(self,layout, col) : 
        
        props = self.Props()
        
        icon = self.ChangeIcon(
                    "RESTRICT_VIEW_ON", "RESTRICT_VIEW_OFF", 
                    not col.is_visible
        )
        
        
        
        
        subrow = layout.row(align=True)
    
        
        if col.parent and col.parent.name.lower().find("panel") == -1 :
            new = subrow.operator("rgc.collections", 
            text="", icon="FILE_PARENT")
            new.type = "MENU"
            new.col_name_parent = col.parent.name 
        
        subrow.prop(
                col, "is_visible", text=col.name if props.edit_collection == False else "", toggle=1, icon=icon, 
        )
    
        if props.edit_collection :
            subrow.prop(
                col, "name", text="", toggle=1, 
            )
            
            new = subrow.operator(
            "rgc.collections", 
            text="", 
            icon="TRIA_UP"
            )
            new.type = "UP"
            new.col_name = col.name 
            
            new = subrow.operator(
            "rgc.collections", 
            text="", 
            icon="TRIA_DOWN"
            )
            new.type = "DOWN"
            new.col_name = col.name 
        
        if self.GetObjMode() == "POSE" : 

            bones_in_collections_set = set(self.GetBonesNamesInCollection(col.name))
            selected_bones = set(self.GetNameToBones(self.GetSelectBones("POSE")))

            # Estado 1: No hay ninguno de la colección seleccionado
            none_selected = not selected_bones & bones_in_collections_set

            # Estado 2: Hay algunos seleccionados de la colección, pero también otros huesos externos
            partial_selected = selected_bones & bones_in_collections_set and not selected_bones <= bones_in_collections_set

            # Estado 3: Solo huesos de la colección están seleccionados
            only_selected = selected_bones.issubset(bones_in_collections_set) and bool(selected_bones)

            if none_selected:
                action = "SELECT"
                icon = "RESTRICT_SELECT_ON"
            elif partial_selected:
                action = "ALL_DESELECT"
                icon = "RESTRICT_SELECT_OFF"
            elif only_selected:
                action = "DESELECT"
                icon = "INDIRECT_ONLY_ON"
            else:
                action = "DESELECT"
                icon = "RESTRICT_SELECT_ON"  # fallback


            new = subrow.operator("rgc.collections", text="", icon=icon)
            new.type = action
            new.col_name = col.name
        
        active = bpy.context.object.data.collections.active_name
        new = subrow.operator(
            "rgc.collections", 
            text="", 
            icon="SOLO_ON" if col.is_solo else "SOLO_OFF",
            depress=active == col.name
        )
        new.type = "ACTIVE"
        new.col_name = col.name 

        
        if col.children: 
            for c in col.children:
                if "panel" in col.name.lower() and col.is_visible == False : continue
                row = layout.column(align=True)
                row.active = col.is_visible
                self.DrawCollections(row, c)
            
    
    def CheckCollection(self, col) -> bool :
        value = False
        if "panel" in col.name.lower()  : value = True
        if col.parent :
            value = self.CheckCollection(col.parent)
        return value
        
    
    def draw(self, context):
        layout = self.layout
        self.Armature = self.GetArmature()
        props = self.Props()
        
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(props, "search_collection", text="", icon="VIEWZOOM")
        
        if self.Panel(col, "edit", "Edit", "GREASEPENCIL", True) :  
            row = col.row(align=True)
            if props.columns_value > 1:
                row.prop(props, "even_columns", text="", icon="ALIGN_JUSTIFY")
            row.scale_x = 1.2
            row.prop(props, "columns_value", text="Columns",)
            row = col.row(align=True)
            if self.IsCollectionToRigCreatorExists() == False:
                row.operator("rgc.collections", text="Add Collection To Rig Creator").type="ADD_COLLECTION"
            col.prop(props, "edit_collection", text="Edit Collection", icon="GREASEPENCIL", toggle=1)
       
        
        grid = layout.grid_flow(
            row_major=False, columns=props.columns_value, 
            even_columns=props.even_columns, even_rows=False, 
            align=True
            )
        
        panel_col = []

        if props.search_collection == "" :
            for col in self.GetActiveObject().data.collections:
                if self.CheckCollection(col) : 
                    if col.children :
                        panel_col.append(col)
                    continue
                if col.parent : continue
                self.DrawCollections(grid, col)
        else :
            for col in self.GetCollections():
                if not self.SearchInList(props.search_collection, col.name) : continue
                if "panel" in col.name.lower() : continue
                self.DrawCollections(grid, col)

        for pcol in panel_col :
            text = pcol.name.upper().replace("PANEL", "").strip()
            text = text.lower().capitalize() if text != "" else "Panel"
            row = layout.row()
            
            if self.Panel(row, pcol.name, text, self.ChangeIcon(
                    "HIDE_OFF", "HIDE_ON", 
                    pcol.is_visible
        ), False, pcol) :
                grid = layout.grid_flow(
                    row_major=False, columns=props.columns_value, 
                    even_columns=props.even_columns, even_rows=False, 
                    align=True
                    )
                grid.active = pcol.is_visible
                for c in pcol.children :
                    self.DrawCollections(grid, c)
            

class RGC_Menu_Collections(GN_RigCreatorViewPort, bpy.types.Menu):
    bl_idname = "RGC_Menu_Collections"
    bl_label = ""

    def draw(self, context):
        layout = self.layout
        props = self.Props()
        col = self.GetCollectionToName(props.how_collection_select)
        layout.prop(
                col, "is_visible", text=col.name, toggle=1, icon=self.ChangeIcon(
                    "RESTRICT_VIEW_ON", "RESTRICT_VIEW_OFF", 
                    not col.is_visible
                ), 
                )
        
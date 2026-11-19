"""
Blender Adapter Package for KONGOR TOOL.
Registers PropertyGroups, Operators, and UI Menus.
"""

from . import properties
from . import operators
from . import ui_panels
from . import kongor_rig_bridge

def register():
    properties.register()
    operators.register()
    ui_panels.register()
    kongor_rig_bridge.register()

def unregister():
    kongor_rig_bridge.unregister()
    ui_panels.unregister()
    operators.unregister()
    properties.unregister()

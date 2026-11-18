"""
Blender Adapter Package for KONGOR TOOL.
Registers PropertyGroups, Operators, and UI Menus.
"""

from . import properties
from . import operators
from . import ui_panels

def register():
    properties.register()
    operators.register()
    ui_panels.register()

def unregister():
    ui_panels.unregister()
    operators.unregister()
    properties.unregister()

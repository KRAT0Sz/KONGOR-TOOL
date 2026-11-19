"""
KONGOR TOOL - K2 Engine Blender Add-on / Extension
Clean Architecture implementation for Blender >=4.2 / 5.0 (Python 3.11+ / 3.13+)
Includes integrated Third-party K2 Rig Creator.
"""

bl_info = {
    "name": "KONGOR TOOL (K2 Model & Animation)",
    "author": "KONGOR TOOL Team",
    "version": (5, 0, 0),
    "blender": (4, 2, 0),
    "location": "File > Import-Export | 3D Viewport > Sidebar > KONGOR Tool",
    "description": "K2 Engine (.model / .clip) Clean Architecture Import, Export, and Rigging Tool",
    "category": "Import-Export",
}

def register():
    from . import blender
    from . import rigcreator
    blender.register()
    rigcreator.register()

def unregister():
    from . import rigcreator
    from . import blender
    try:
        rigcreator.unregister()
    except Exception:
        pass
    blender.unregister()

if __name__ == "__main__":
    register()

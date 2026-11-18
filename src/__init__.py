"""
KONGOR TOOL - K2 Engine Blender Add-on / Extension
Clean Architecture implementation for Blender >=4.2 / 5.0 (Python 3.11+ / 3.13+)
"""

bl_info = {
    "name": "KONGOR TOOL (K2 Model & Animation)",
    "author": "KONGOR TOOL Team",
    "version": (5, 0, 0),
    "blender": (4, 2, 0),
    "location": "File > Import-Export | 3D Viewport > Sidebar > KONGOR Tool",
    "description": "K2 Engine (.model / .clip) Clean Architecture Import and Export Tool",
    "category": "Import-Export",
}

def register():
    from . import blender
    blender.register()

def unregister():
    from . import blender
    blender.unregister()

if __name__ == "__main__":
    register()

"""
KONGOR TOOL - K2 Engine Blender Add-on / Extension
Clean Architecture implementation for Blender >=4.2 / 5.0 (Python 3.11+ / 3.13+)
Integrated KONGOR Rig (v3.71.25) and K2 Engine Skeleton Pipeline.
"""

bl_info = {
    "name": "KONGOR TOOL (K2 Model & Animation)",
    "author": "KONGOR TOOL Team",
    "version": (5, 0, 0),
    "blender": (4, 2, 0),
    "location": "File > Import-Export | 3D Viewport > Header > KONGOR Tool",
    "description": "K2 Engine (.model / .clip) Model & Animation pipeline with integrated KONGOR Rig",
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

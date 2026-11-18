"""
KONGOR TOOL - K2 Engine Blender Add-on
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
    # Will be connected to blender/ adapter layer in Phase 3
    pass

def unregister():
    # Will be connected to blender/ adapter layer in Phase 3
    pass

if __name__ == "__main__":
    register()

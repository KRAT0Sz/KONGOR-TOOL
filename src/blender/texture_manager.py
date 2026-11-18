"""
Texture and Shader Material Manager for KONGOR TOOL.
Constructs Principled BSDF Shader Node trees for K2 Engine assets.
"""

import os
from typing import Optional, Dict
import bpy

TEXTURE_SUFFIXES = {
    "color": ["_color", "_albedo", "_diffuse", "_d", "_c"],
    "normal": ["_norm", "_normal", "_n", "_bump"],
    "mrao": ["_mrao", "_spec", "_s", "_roughness", "_metallic"],
    "emissive": ["_glow", "_emissive", "_e", "_illum"],
}

IMAGE_EXTENSIONS = [".dds", ".tga", ".png", ".jpg", ".jpeg"]

def find_texture_file(base_dir: str, base_name: str, tex_type: str) -> Optional[str]:
    """Searches base_dir for a texture matching base_name and tex_type suffixes."""
    suffixes = TEXTURE_SUFFIXES.get(tex_type, [f"_{tex_type}"])
    
    # Check directly by base_name + suffix + extension
    for suffix in suffixes:
        for ext in IMAGE_EXTENSIONS:
            filename = f"{base_name}{suffix}{ext}"
            path = os.path.join(base_dir, filename)
            if os.path.exists(path):
                return path

    # Search directory files case-insensitively
    if os.path.isdir(base_dir):
        files_lower = {f.lower(): f for f in os.listdir(base_dir)}
        for suffix in suffixes:
            for ext in IMAGE_EXTENSIONS:
                candidate = f"{base_name}{suffix}{ext}".lower()
                if candidate in files_lower:
                    return os.path.join(base_dir, files_lower[candidate])

    return None

def create_k2_material(
    material_name: str,
    base_dir: str,
    settings,
    shader_path: str = ""
) -> bpy.types.Material:
    """Creates a Principled BSDF material in Blender configured for K2 Engine PBR shaders."""
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
    
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Create Core Nodes
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    links.new(principled.outputs["BSDF"], output_node.inputs["Surface"])

    clean_base_name = os.path.splitext(material_name)[0]

    # 1. Color / Diffuse Texture
    if getattr(settings, "tex_color", True):
        color_path = find_texture_file(base_dir, clean_base_name, "color")
        if color_path:
            img = bpy.data.images.load(color_path, check_existing=True)
            tex_node = nodes.new(type="ShaderNodeTexImage")
            tex_node.location = (-400, 200)
            tex_node.image = img
            links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
            if "Alpha" in tex_node.outputs and "Alpha" in principled.inputs:
                links.new(tex_node.outputs["Alpha"], principled.inputs["Alpha"])

    # 2. Normal Map Texture
    if getattr(settings, "tex_normal", True):
        norm_path = find_texture_file(base_dir, clean_base_name, "normal")
        if norm_path:
            img = bpy.data.images.load(norm_path, check_existing=True)
            img.colorspace_settings.name = "Non-Color"
            norm_tex_node = nodes.new(type="ShaderNodeTexImage")
            norm_tex_node.location = (-400, -100)
            norm_tex_node.image = img

            normal_map_node = nodes.new(type="ShaderNodeNormalMap")
            normal_map_node.location = (-150, -100)
            links.new(norm_tex_node.outputs["Color"], normal_map_node.inputs["Color"])
            links.new(normal_map_node.outputs["Normal"], principled.inputs["Normal"])

    # 3. Emissive / Glow Texture
    if getattr(settings, "tex_emissive", True):
        glow_path = find_texture_file(base_dir, clean_base_name, "emissive")
        if glow_path:
            img = bpy.data.images.load(glow_path, check_existing=True)
            glow_tex_node = nodes.new(type="ShaderNodeTexImage")
            glow_tex_node.location = (-400, -400)
            glow_tex_node.image = img
            if "Emission Color" in principled.inputs:
                links.new(glow_tex_node.outputs["Color"], principled.inputs["Emission Color"])
            elif "Emission" in principled.inputs:
                links.new(glow_tex_node.outputs["Color"], principled.inputs["Emission"])

    return mat

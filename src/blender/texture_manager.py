"""
KONGOR TOOL - Material & Shader Node Builder
Follows official K2 Engine material samplers (c_material.h and c_outmaterial.cpp:86-97).
Maps: diffuse, normalmap, specular, gloss, lightmap, occlusion, cube.
"""

import os
from typing import Optional, Dict
import bpy

# Official K2 Engine map samplers and their standard filename suffixes
K2_SAMPLER_PATTERNS: Dict[str, list[str]] = {
    "diffuse": ["_color", "_diffuse", "_d", "_albedo"],
    "normalmap": ["_norm", "_normal", "_n", "_bump"],
    "specular": ["_spec", "_s", "_specular"],
    "gloss": ["_gloss", "_roughness"],
    "lightmap": ["_lightmap", "_si"],
    "occlusion": ["_occlusion", "_ao"],
}

SUPPORTED_EXTENSIONS = [".dds", ".tga", ".png", ".jpg", ".jpeg"]

def locate_sampler_texture(base_dir: str, stem: str, sampler_type: str) -> Optional[str]:
    """Finds texture files in base_dir corresponding to official K2 sampler types."""
    patterns = K2_SAMPLER_PATTERNS.get(sampler_type, [f"_{sampler_type}"])
    
    for pat in patterns:
        for ext in SUPPORTED_EXTENSIONS:
            target = os.path.join(base_dir, f"{stem}{pat}{ext}")
            if os.path.exists(target):
                return target

    # Case-insensitive fallback
    if os.path.isdir(base_dir):
        disk_files = {f.lower(): f for f in os.listdir(base_dir)}
        for pat in patterns:
            for ext in SUPPORTED_EXTENSIONS:
                candidate = f"{stem}{pat}{ext}".lower()
                if candidate in disk_files:
                    return os.path.join(base_dir, disk_files[candidate])
    return None

def build_k2_shader_material(
    material_name: str,
    base_dir: str,
    shader_path: str = ""
) -> bpy.types.Material:
    """Builds a modern Blender Principled BSDF node setup reflecting K2 Engine samplers."""
    mat = bpy.data.materials.get(material_name)
    if mat is None:
        mat = bpy.data.materials.new(name=material_name)
    
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Output node
    output_node = nodes.new(type="ShaderNodeOutputMaterial")
    output_node.location = (400, 0)

    # Principled BSDF
    principled = nodes.new(type="ShaderNodeBsdfPrincipled")
    principled.location = (0, 0)
    links.new(principled.outputs["BSDF"], output_node.inputs["Surface"])

    stem = os.path.splitext(material_name)[0]

    # 1. Diffuse Sampler
    diffuse_path = locate_sampler_texture(base_dir, stem, "diffuse")
    if diffuse_path:
        img = bpy.data.images.load(diffuse_path, check_existing=True)
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.location = (-400, 200)
        tex_node.image = img
        links.new(tex_node.outputs["Color"], principled.inputs["Base Color"])
        if "Alpha" in tex_node.outputs and "Alpha" in principled.inputs:
            links.new(tex_node.outputs["Alpha"], principled.inputs["Alpha"])

    # 2. Normalmap Sampler
    normal_path = locate_sampler_texture(base_dir, stem, "normalmap")
    if normal_path:
        img = bpy.data.images.load(normal_path, check_existing=True)
        img.colorspace_settings.name = "Non-Color"
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.location = (-400, -100)
        tex_node.image = img

        norm_map = nodes.new(type="ShaderNodeNormalMap")
        norm_map.location = (-150, -100)
        links.new(tex_node.outputs["Color"], norm_map.inputs["Color"])
        links.new(norm_map.outputs["Normal"], principled.inputs["Normal"])

    # 3. Specular Sampler
    spec_path = locate_sampler_texture(base_dir, stem, "specular")
    if spec_path:
        img = bpy.data.images.load(spec_path, check_existing=True)
        img.colorspace_settings.name = "Non-Color"
        tex_node = nodes.new(type="ShaderNodeTexImage")
        tex_node.location = (-400, -350)
        tex_node.image = img
        if "Specular IOR Level" in principled.inputs:
            links.new(tex_node.outputs["Color"], principled.inputs["Specular IOR Level"])
        elif "Specular" in principled.inputs:
            links.new(tex_node.outputs["Color"], principled.inputs["Specular"])

    return mat

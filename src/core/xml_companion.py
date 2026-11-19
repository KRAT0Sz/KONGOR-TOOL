"""
XML Companion Parsers and Writers for .material and .mdf files.
Conforms strictly to K2 Engine / S2 Exporter specifications.
"""

from dataclasses import dataclass, field
import os
from typing import List, Optional
import xml.etree.ElementTree as ET

@dataclass
class K2Sampler:
    name: str
    texture_path: str
    repeat_u: bool = True
    repeat_v: bool = True

@dataclass
class K2MaterialPhase:
    name: str
    lighting_spec: str = ""
    cull: str = "back"
    blend: str = "alphatest"
    samplers: List[K2Sampler] = field(default_factory=list)

@dataclass
class K2Material:
    name: str = ""
    shader: str = "/shared/shaders/heroes/hero_diffuse_normal_mrao_team_envmap_tinted.shader"
    vDiffuseColor: str = "1 1 1"
    fSpecularLevel: str = "1.5"
    fGlossiness: str = "32"
    fOpacity: str = "1.0"
    diffuse_texture: str = ""
    normal_texture: str = ""
    mrao_texture: str = ""
    cube_texture: str = "/world/sky/panorama/1.tga"
    shaders: List[str] = field(default_factory=list)
    phases: List[K2MaterialPhase] = field(default_factory=list)

@dataclass
class K2SkinReference:
    mesh_name: str
    material_path: str

@dataclass
class K2AnimationDef:
    name: str
    clip_file: str
    loop: bool = True
    fps: float = 30.0
    num_frames: int = 0

@dataclass
class K2ModelDefinition:
    model_file: str
    model_name: str = ""
    default_skin: str = "default"
    model_type: str = "K2"
    skin_refs: List[K2SkinReference] = field(default_factory=list)
    anims: List[K2AnimationDef] = field(default_factory=list)

def read_material_xml(xml_text: str) -> K2Material:
    """Parses a K2 .material XML document."""
    root = ET.fromstring(xml_text)
    mat_name = root.attrib.get("name", "")

    param_elem = root.find("parameters")
    shader = param_elem.attrib.get("shader", "/shared/shaders/heroes/hero_diffuse_normal_mrao_team_envmap_tinted.shader") if param_elem is not None else ""
    v_diffuse = param_elem.attrib.get("vDiffuseColor", "1 1 1") if param_elem is not None else "1 1 1"
    f_spec = param_elem.attrib.get("fSpecularLevel", "1.5") if param_elem is not None else "1.5"
    f_gloss = param_elem.attrib.get("fGlossiness", "32") if param_elem is not None else "32"
    f_opac = param_elem.attrib.get("fOpacity", "1.0") if param_elem is not None else "1.0"

    diffuse = ""
    normal = ""
    mrao = ""
    cube = ""

    phases = []
    for phase_elem in root.findall("phase"):
        p_name = phase_elem.attrib.get("name", "")
        lighting = phase_elem.attrib.get("lighting", "")
        cull = phase_elem.attrib.get("cull", "back")
        blend = phase_elem.attrib.get("blend", "alphatest")
        samplers = []
        for s_elem in phase_elem.findall("sampler"):
            s_name = s_elem.attrib.get("name", "")
            s_path = s_elem.attrib.get("texture", "") or s_elem.attrib.get("file", "")
            samplers.append(
                K2Sampler(
                    name=s_name,
                    texture_path=s_path,
                    repeat_u=s_elem.attrib.get("repeat_u", "true").lower() == "true",
                    repeat_v=s_elem.attrib.get("repeat_v", "true").lower() == "true",
                )
            )
            if s_name == "diffuse" and not diffuse:
                diffuse = s_path
            elif s_name == "normalmap" and not normal:
                normal = s_path
            elif s_name == "mrao" and not mrao:
                mrao = s_path

        for c_elem in phase_elem.findall("samplercube"):
            c_name = c_elem.attrib.get("name", "")
            c_path = c_elem.attrib.get("texture", "") or c_elem.attrib.get("file", "")
            if not cube:
                cube = c_path

        phases.append(K2MaterialPhase(name=p_name, lighting_spec=lighting, cull=cull, blend=blend, samplers=samplers))

    return K2Material(
        name=mat_name,
        shader=shader,
        vDiffuseColor=v_diffuse,
        fSpecularLevel=f_spec,
        fGlossiness=f_gloss,
        fOpacity=f_opac,
        diffuse_texture=diffuse,
        normal_texture=normal,
        mrao_texture=mrao,
        cube_texture=cube or "/world/sky/panorama/1.tga",
        phases=phases,
    )

def write_material_xml(mat: K2Material) -> str:
    """Generates K2/S2 Exporter compliant .material XML."""
    mat_attr = f' name="{mat.name}"' if mat.name else ""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<material{mat_attr}>',
    ]

    # Parameters line
    shader_attr = f' shader="{mat.shader}"' if mat.shader else ""
    lines.append(
        f'\t<parameters{shader_attr} vDiffuseColor="{mat.vDiffuseColor}" '
        f'fSpecularLevel="{mat.fSpecularLevel}" fGlossiness="{mat.fGlossiness}" fOpacity="{mat.fOpacity}" />'
    )

    # If mat.phases is explicitly populated with custom phases, preserve them:
    if mat.phases and not mat.diffuse_texture:
        for phase in mat.phases:
            light_attr = f' lighting="{phase.lighting_spec}"' if phase.lighting_spec else ""
            cull_attr = f' cull="{phase.cull}"' if phase.cull else ""
            blend_attr = f' blend="{phase.blend}"' if phase.blend else ""
            lines.append(f'\t<phase name="{phase.name}"{light_attr}{cull_attr}{blend_attr}>')
            for s in phase.samplers:
                lines.append(f'\t\t<sampler name="{s.name}" texture="{s.texture_path}" repeat_u="{str(s.repeat_u).lower()}" repeat_v="{str(s.repeat_v).lower()}" />')
            lines.append('\t</phase>')
        lines.append('</material>')
        return "\n".join(lines) + "\n"

    diffuse = mat.diffuse_texture
    normal = mat.normal_texture
    mrao = mat.mrao_texture
    cube = mat.cube_texture

    if not diffuse and mat.phases:
        for p in mat.phases:
            for s in p.samplers:
                if s.name == "diffuse" and not diffuse:
                    diffuse = s.texture_path
                elif s.name == "normalmap" and not normal:
                    normal = s.texture_path
                elif s.name == "mrao" and not mrao:
                    mrao = s.texture_path

    if not diffuse:
        diffuse = "textures/color.tga"

    # 1. Shadow phase
    lines.extend([
        '\t<phase name="shadow" cull="back" blend="alphatest">',
        f'\t\t<sampler name="diffuse" texture="{diffuse}" />',
        '\t</phase>',
    ])

    # 2. Color phase
    lines.extend([
        '\t<phase name="color" cull="back" blend="alphatest">',
        f'\t\t<sampler name="diffuse" texture="{diffuse}" />',
    ])
    if normal:
        lines.append(f'\t\t<sampler name="normalmap" texture="{normal}" />')
    if mrao:
        lines.append(f'\t\t<sampler name="mrao" texture="{mrao}" />')
    if cube:
        lines.append(f'\t\t<samplercube name="cube" texture="{cube}" />')
    lines.append('\t</phase>')

    # 3. Fade phase with translucent multipass
    lines.extend([
        '\t<phase name="fade" cull="back" colorwrite="false" alphawrite="false" depthwrite="true" blend="alphatest">',
        f'\t\t<sampler name="diffuse" texture="{diffuse}" />',
        '\t\t<multipass cull="back" blend="translucent">',
        f'\t\t\t<sampler name="diffuse" texture="{diffuse}" />',
    ])
    if normal:
        lines.append(f'\t\t\t<sampler name="normalmap" texture="{normal}" />')
    if mrao:
        lines.append(f'\t\t\t<sampler name="mrao" texture="{mrao}" />')
    if cube:
        lines.append(f'\t\t\t<samplercube name="cube" texture="{cube}" />')
    lines.extend([
        '\t\t</multipass>',
        '\t</phase>',
    ])

    lines.append('</material>')
    return "\n".join(lines) + "\n"

def read_mdf_xml(xml_text: str) -> K2ModelDefinition:
    """Parses a K2 .mdf XML document."""
    root = ET.fromstring(xml_text)
    model_file = root.attrib.get("file", "")
    model_name = root.attrib.get("name", "")
    default_skin = root.attrib.get("defaultskin", "default")
    model_type = root.attrib.get("type", "K2")

    skin_refs = []
    skin_elem = root.find("skin")
    if skin_elem is not None:
        for ref_elem in skin_elem.findall("reference"):
            skin_refs.append(
                K2SkinReference(
                    mesh_name=ref_elem.attrib.get("mesh", ""),
                    material_path=ref_elem.attrib.get("material", ""),
                )
            )

    anims = []
    for anim_elem in root.findall("anim"):
        anims.append(
            K2AnimationDef(
                name=anim_elem.attrib.get("name", ""),
                clip_file=anim_elem.attrib.get("clip", ""),
                loop=anim_elem.attrib.get("loop", "true").lower() == "true",
                fps=float(anim_elem.attrib.get("fps", "30.0")),
                num_frames=int(anim_elem.attrib.get("numframes", "0")),
            )
        )

    return K2ModelDefinition(
        model_file=model_file,
        model_name=model_name,
        default_skin=default_skin,
        model_type=model_type,
        skin_refs=skin_refs,
        anims=anims,
    )

def write_mdf_xml(mdf: K2ModelDefinition) -> str:
    """Generates K2/S2 Exporter compliant .mdf XML."""
    model_name = mdf.model_name or os.path.basename(mdf.model_file)
    model_file = os.path.basename(mdf.model_file).replace("\\", "/")

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<model name="{model_name}" file="{model_file}" type="{mdf.model_type}" high="{model_file}" med="{model_file}" low="{model_file}">',
    ]

    # Skin block
    if mdf.skin_refs:
        lines.append('')
        lines.append(f'\t<skin name="{mdf.default_skin}">')
        for ref in mdf.skin_refs:
            lines.append(f'\t\t<reference mesh="{ref.mesh_name}" material="{ref.material_path}"/>')
        lines.append('\t</skin>')

    # Anims block
    if mdf.anims:
        lines.append('')
        for anim in mdf.anims:
            lines.append(f'\t<anim name="{anim.name}" clip="{anim.clip_file}" fps="{int(anim.fps)}" loop="{str(anim.loop).lower()}"/>')
    else:
        clip_name = f"clips/{os.path.splitext(model_file)[0]}_idle.clip"
        lines.append('')
        lines.append(f'\t<anim name="idle" clip="{clip_name}" fps="30" loop="true" />')

    lines.append('</model>')
    return "\n".join(lines) + "\n"

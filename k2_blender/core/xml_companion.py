"""
XML Companion Parsers and Writers for .material and .mdf files.
Conforms to K2 Engine standard XML schemas.
"""

from dataclasses import dataclass, field
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
    samplers: List[K2Sampler] = field(default_factory=list)

@dataclass
class K2Material:
    name: str
    shaders: List[str] = field(default_factory=list)
    phases: List[K2MaterialPhase] = field(default_factory=list)

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
    default_skin: str = "default"
    anims: List[K2AnimationDef] = field(default_factory=list)

def read_material_xml(xml_text: str) -> K2Material:
    root = ET.fromstring(xml_text)
    mat_name = root.attrib.get("name", "")
    
    phases = []
    for phase_elem in root.findall("phase"):
        p_name = phase_elem.attrib.get("name", "")
        lighting = phase_elem.attrib.get("lighting", "")
        samplers = []
        for s_elem in phase_elem.findall("sampler"):
            samplers.append(
                K2Sampler(
                    name=s_elem.attrib.get("name", ""),
                    texture_path=s_elem.attrib.get("file", ""),
                    repeat_u=s_elem.attrib.get("repeat_u", "true").lower() == "true",
                    repeat_v=s_elem.attrib.get("repeat_v", "true").lower() == "true",
                )
            )
        phases.append(K2MaterialPhase(name=p_name, lighting_spec=lighting, samplers=samplers))

    return K2Material(name=mat_name, phases=phases)

def write_material_xml(mat: K2Material) -> str:
    root = ET.Element("material", name=mat.name)
    for phase in mat.phases:
        p_elem = ET.SubElement(root, "phase", name=phase.name)
        if phase.lighting_spec:
            p_elem.attrib["lighting"] = phase.lighting_spec
        for sampler in phase.samplers:
            ET.SubElement(
                p_elem,
                "sampler",
                name=sampler.name,
                file=sampler.texture_path,
                repeat_u=str(sampler.repeat_u).lower(),
                repeat_v=str(sampler.repeat_v).lower(),
            )
    return ET.tostring(root, encoding="unicode")

def read_mdf_xml(xml_text: str) -> K2ModelDefinition:
    root = ET.fromstring(xml_text)
    model_file = root.attrib.get("file", "")
    default_skin = root.attrib.get("defaultskin", "default")
    
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
    return K2ModelDefinition(model_file=model_file, default_skin=default_skin, anims=anims)

def write_mdf_xml(mdf: K2ModelDefinition) -> str:
    root = ET.Element("model", file=mdf.model_file, defaultskin=mdf.default_skin)
    for anim in mdf.anims:
        ET.SubElement(
            root,
            "anim",
            name=anim.name,
            clip=anim.clip_file,
            loop=str(anim.loop).lower(),
            fps=str(anim.fps),
            numframes=str(anim.num_frames),
        )
    return ET.tostring(root, encoding="unicode")

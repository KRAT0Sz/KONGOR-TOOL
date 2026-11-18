import pytest
from src.core.xml_companion import (
    K2Material,
    K2MaterialPhase,
    K2Sampler,
    read_material_xml,
    write_material_xml,
    read_mdf_xml,
    write_mdf_xml,
    K2ModelDefinition,
    K2AnimationDef
)

def test_material_xml_roundtrip():
    mat = K2Material(
        name="hero_material",
        shaders=["mesh_color"],
        phases=[
            K2MaterialPhase(
                name="color",
                lighting_spec="hero",
                samplers=[
                    K2Sampler(name="diffuse", texture_path="hero_color.dds"),
                    K2Sampler(name="normalmap", texture_path="hero_norm.dds")
                ]
            )
        ]
    )
    xml_str = write_material_xml(mat)
    assert "<material" in xml_str
    assert "hero_color.dds" in xml_str
    
    parsed = read_material_xml(xml_str)
    assert parsed.name == "hero_material"
    assert len(parsed.phases) == 1
    assert len(parsed.phases[0].samplers) == 2
    assert parsed.phases[0].samplers[0].texture_path == "hero_color.dds"

def test_mdf_xml_roundtrip():
    mdf = K2ModelDefinition(
        model_file="model.model",
        default_skin="default",
        anims=[
            K2AnimationDef(name="idle", clip_file="idle.clip", loop=True, fps=30.0),
            K2AnimationDef(name="walk", clip_file="walk.clip", loop=True, fps=30.0)
        ]
    )
    xml_str = write_mdf_xml(mdf)
    assert "<model" in xml_str
    assert "idle.clip" in xml_str
    
    parsed = read_mdf_xml(xml_str)
    assert parsed.model_file == "model.model"
    assert len(parsed.anims) == 2
    assert parsed.anims[0].name == "idle"
    assert parsed.anims[0].loop is True
    assert parsed.anims[1].clip_file == "walk.clip"

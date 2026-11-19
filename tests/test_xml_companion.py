import pytest
from src.core.xml_companion import (
    K2Material,
    K2MaterialPhase,
    K2Sampler,
    K2SkinReference,
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

def test_hon_material_specification():
    """Verifies native Heroes of Newerth S2 material generation."""
    mat = K2Material(
        name="",
        vDiffuseColor="1.0000 1.0000 1.0000",
        fSpecularLevel="1.0000",
        fGlossiness="56",
        fOpacity="1.0000",
        fReflect="1.0000",
        diffuse_texture="color.tga",
        normal_texture="normal.tga",
        specular_texture="spec_color.tga",
        team_texture="team.tga",
        lightmap_texture="glow.tga",
    )
    xml_str = write_material_xml(mat)
    assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_str
    assert '<material>' in xml_str
    assert '<parameters vDiffuseColor="1.0000 1.0000 1.0000" fSpecularLevel="1.0000" fGlossiness="56" fOpacity="1.0000" fReflect="1.0000" />' in xml_str
    assert '<phase name="shadow" vs="mesh_shadow_opacity" ps="mesh_shadow_opacity"' in xml_str
    assert '<sampler name="opacity" texture="color.tga"' in xml_str
    assert '<phase name="depth" vs="mesh_depth_opacity" ps="mesh_depth_opacity"' in xml_str
    assert '<phase name="color" vs="mesh_color_unit" ps="mesh_color_unit_team_lightmap_spec"' in xml_str
    assert '<sampler name="diffuse" texture="color.tga"' in xml_str
    assert '<sampler name="normalmap" texture="normal.tga"' in xml_str
    assert '<sampler name="specular" texture="spec_color.tga"' in xml_str
    assert '<sampler name="team" texture="team.tga"' in xml_str
    assert '<sampler name="lightmap" texture="glow.tga"' in xml_str
    assert '<phase name="fade" vs="mesh_depth_opacity" ps="mesh_depth_opacity"' in xml_str
    assert '<multipass vs="mesh_color_unit" ps="mesh_color_unit_team_lightmap_spec"' in xml_str

    parsed = read_material_xml(xml_str)
    assert parsed.diffuse_texture == "color.tga"
    assert parsed.normal_texture == "normal.tga"
    assert len(parsed.phases) == 4

def test_s2_mdf_skin_specification():
    """Verifies S2Exporter-compliant .mdf skin and model attributes."""
    mdf = K2ModelDefinition(
        model_file="hd_high.model",
        model_name="hd_high.model",
        default_skin="default",
        model_type="K2",
        skin_refs=[
            K2SkinReference(mesh_name="mat1", material_path="material.material"),
            K2SkinReference(mesh_name="mat2", material_path="material2.material"),
            K2SkinReference(mesh_name="mat3", material_path="material3.material"),
        ],
        anims=[
            K2AnimationDef(name="idle", clip_file="clips/default_1.clip", fps=30.0, loop=True)
        ]
    )
    xml_str = write_mdf_xml(mdf)
    assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_str
    assert '<model name="hd_high.model" file="hd_high.model" type="K2" high="hd_high.model" med="hd_high.model" low="hd_high.model">' in xml_str
    assert '<skin name="default">' in xml_str
    assert '<reference mesh="mat1" material="material.material"/>' in xml_str
    assert '<reference mesh="mat2" material="material2.material"/>' in xml_str
    assert '<reference mesh="mat3" material="material3.material"/>' in xml_str
    assert '<anim name="idle" clip="clips/default_1.clip" fps="30" loop="true"/>' in xml_str

    parsed = read_mdf_xml(xml_str)
    assert parsed.model_file == "hd_high.model"
    assert len(parsed.skin_refs) == 3
    assert parsed.skin_refs[0].mesh_name == "mat1"
    assert parsed.skin_refs[0].material_path == "material.material"
    assert parsed.skin_refs[1].mesh_name == "mat2"
    assert parsed.skin_refs[2].mesh_name == "mat3"
    assert len(parsed.anims) == 1


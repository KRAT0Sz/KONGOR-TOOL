import os
import pathlib
import pytest

def test_kongor_rig_structure_and_presets():
    repo_root = pathlib.Path(__file__).parent.parent
    kongor_rig_dir = repo_root / "src" / "kongor_rig"
    assert kongor_rig_dir.exists(), "src/kongor_rig directory missing"
    
    # Check essential code modules
    src_code_dir = kongor_rig_dir / "src"
    for module_name in [
        "auto_rig.py",
        "auto_rig_remap.py",
        "auto_rig_ge.py",
        "auto_rig_smart.py",
        "auto_rig_prefs.py",
        "rig_functions.py",
    ]:
        p = src_code_dir / module_name
        assert p.exists(), f"KONGOR Rig module missing: {module_name}"

    # Check blend presets
    arm_presets = kongor_rig_dir / "armature_presets"
    assert (arm_presets / "human.blend").exists()
    assert (arm_presets / "master.blend").exists()

    # Check K2 Biped remap preset
    bmap_file = kongor_rig_dir / "remap_presets" / "k2_biped.bmap"
    assert bmap_file.exists(), "k2_biped.bmap missing from remap_presets"

    lines = [line.strip() for line in bmap_file.read_text(encoding="utf-8").splitlines()]
    assert len(lines) >= 100
    assert "Root" in lines
    assert "Bip01" in lines
    assert "Bip01 Pelvis" in lines
    assert "Bip01 Spine" in lines
    assert "Bip01 Head" in lines
    assert "Bip01 L UpperArm" in lines
    assert "Bip01 R UpperArm" in lines

def test_package_extension_includes_kongor_rig():
    from scripts.package_extension import build_package
    repo_root = pathlib.Path(__file__).parent.parent
    src_dir = repo_root / "src"
    kongor_rig_dir = src_dir / "kongor_rig"
    
    # Verify kongor_rig files glob correctly
    rig_files = [f for f in kongor_rig_dir.rglob("*") if f.is_file() and not any(p in ("__pycache__", ".vscode") for p in f.parts) and f.suffix not in (".pyc", ".pyo")]
    assert len(rig_files) > 30, f"Expected >30 KONGOR Rig files, found {len(rig_files)}"

def test_kongor_rig_branding():
    repo_root = pathlib.Path(__file__).parent.parent
    src_dir = repo_root / "src"
    
    # Check auto_rig.py
    auto_rig_text = (src_dir / "kongor_rig" / "src" / "auto_rig.py").read_text(encoding="utf-8")
    assert "bl_label = 'KONGOR Rig'" in auto_rig_text
    assert "bl_category = 'KONGOR Rig'" in auto_rig_text

    # Check auto_rig_smart.py
    smart_text = (src_dir / "kongor_rig" / "src" / "auto_rig_smart.py").read_text(encoding="utf-8")
    assert 'bl_label = "KONGOR Rig: Smart"' in smart_text
    assert 'bl_category = "KONGOR Rig"' in smart_text

    # Check auto_rig_remap.py
    remap_text = (src_dir / "kongor_rig" / "src" / "auto_rig_remap.py").read_text(encoding="utf-8")
    assert 'bl_label = "KONGOR Rig: Remap"' in remap_text
    assert 'bl_category = "KONGOR Rig"' in remap_text

    # Check auto_rig_ge.py
    ge_text = (src_dir / "kongor_rig" / "src" / "auto_rig_ge.py").read_text(encoding="utf-8")
    assert 'bl_label = "KONGOR Rig: Export"' in ge_text
    assert 'bl_category = "KONGOR Rig"' in ge_text

    # Check auto_rig_prefs.py
    prefs_text = (src_dir / "kongor_rig" / "src" / "auto_rig_prefs.py").read_text(encoding="utf-8")
    assert "default='KONGOR Rig'" in prefs_text

    # Check kongor_rig __init__.py
    init_text = (src_dir / "kongor_rig" / "__init__.py").read_text(encoding="utf-8")
    assert '"name": "KONGOR Rig"' in init_text
    assert 'text="KONGOR Rig FBX (.fbx)"' in init_text

    # Check blender ui_panels.py
    ui_text = (src_dir / "blender" / "ui_panels.py").read_text(encoding="utf-8")
    assert 'bl_label = "KONGOR Rig"' in ui_text
    assert 'text="KONGOR Rig Tools"' in ui_text

def test_k2_bone_structure_and_hierarchy_rules():
    repo_root = pathlib.Path(__file__).parent.parent
    bridge_file = repo_root / "src" / "blender" / "kongor_rig_bridge.py"
    assert bridge_file.exists(), "kongor_rig_bridge.py missing"

    text = bridge_file.read_text(encoding="utf-8")
    assert "K2_PARENT_RULES = {" in text
    assert '"Bip01": "Root"' in text
    assert '"Bip01 Pelvis": "Bip01"' in text
    assert '"Bip01 Spine": "Bip01 Pelvis"' in text
    assert '"Bip01 Spine1": "Bip01 Spine"' in text
    assert '"Bip01 Head": "Bip01 Neck"' in text
    assert '"_bone_weapon01": "Bip01 R Hand"' in text
    assert '"_bone_weapon02": "Bip01 L Hand"' in text
    assert '"_bone_overhead": "Bip01 Head"' in text
    assert '"_bone_chest": "Bip01 Spine1"' in text

    # Verify K2 bridge operators
    assert "class KONGOR_OT_conform_k2_hierarchy" in text
    assert "class KONGOR_OT_add_k2_sockets" in text
    assert "class KONGOR_OT_generate_k2_skeleton" in text
    assert "class KONGOR_OT_isolate_k2_deform" in text
    assert "class KONGOR_OT_remap_to_k2_universal" in text

def test_k2_export_pipeline_auto_rig_ge():
    repo_root = pathlib.Path(__file__).parent.parent
    ge_file = repo_root / "src" / "kongor_rig" / "src" / "auto_rig_ge.py"
    assert ge_file.exists()

    ge_text = ge_file.read_text(encoding="utf-8")
    assert "def rename_for_k2():" in ge_text
    assert "def add_k2_sockets(" in ge_text
    assert "scn.arp_engine_type == 'K2'" in ge_text
    assert "default='K2'" in ge_text
    assert "arp_rename_for_k2" in ge_text
    assert "arp_k2_add_sockets" in ge_text


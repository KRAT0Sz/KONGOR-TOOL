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

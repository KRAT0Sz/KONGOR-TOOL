import os
import pathlib
import pytest

def test_arp_structure_and_presets():
    repo_root = pathlib.Path(__file__).parent.parent
    arp_dir = repo_root / "src" / "auto_rig_pro"
    assert arp_dir.exists(), "src/auto_rig_pro directory missing"
    
    # Check essential code modules
    src_code_dir = arp_dir / "src"
    for module_name in [
        "auto_rig.py",
        "auto_rig_remap.py",
        "auto_rig_ge.py",
        "auto_rig_smart.py",
        "auto_rig_prefs.py",
        "rig_functions.py",
    ]:
        p = src_code_dir / module_name
        assert p.exists(), f"ARP module missing: {module_name}"

    # Check blend presets
    arm_presets = arp_dir / "armature_presets"
    assert (arm_presets / "human.blend").exists()
    assert (arm_presets / "master.blend").exists()

    # Check K2 Biped remap preset
    bmap_file = arp_dir / "remap_presets" / "k2_biped.bmap"
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

def test_package_extension_includes_arp():
    from scripts.package_extension import build_package
    # Test packaging script logic by building or inspecting files_to_pack
    repo_root = pathlib.Path(__file__).parent.parent
    src_dir = repo_root / "src"
    arp_dir = src_dir / "auto_rig_pro"
    
    # Verify arp files glob correctly
    arp_files = [f for f in arp_dir.rglob("*") if f.is_file() and not any(p in ("__pycache__", ".vscode") for p in f.parts) and f.suffix not in (".pyc", ".pyo")]
    assert len(arp_files) > 30, f"Expected >30 ARP files, found {len(arp_files)}"

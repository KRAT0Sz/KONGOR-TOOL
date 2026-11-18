import pathlib
import sys
import pytest

def test_core_has_zero_bpy_dependency():
    """Confirms that importing any core module never loads or requires bpy or bmesh."""
    import src.core
    import src.core.constants
    import src.core.models
    import src.core.chunk_io
    import src.core.math_k2
    import src.core.smdl_reader
    import src.core.smdl_writer
    import src.core.clip_reader
    import src.core.clip_writer
    import src.core.xml_companion
    
    assert "bpy" not in sys.modules
    assert "bmesh" not in sys.modules

def test_no_legacy_patterns_in_codebase():
    """Verify that no legacy remnants or old identifiers exist across the codebase."""
    src_dir = pathlib.Path(__file__).parent.parent / "src"
    legacy_keywords = [
        "k2_import_settings",
        "k2_export_settings",
        "k2_mesh_settings",
        "import_mesh.k2",
        "export_mesh.k2",
        "import_clip.k2",
        "k2.scene_info",
        "K2_PT_",
    ]
    for py_file in src_dir.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for kw in legacy_keywords:
            assert kw not in text, f"Found legacy pattern '{kw}' in {py_file}"

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

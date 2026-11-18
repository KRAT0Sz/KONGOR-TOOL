# KONGOR TOOL (v5.0.0)

Clean Architecture Blender add-on for importing and exporting K2 Engine assets (`.model` / `.clip` / `.material` / `.mdf`). Designed for Blender 4.2+ and Blender 5.0 (Python 3.11+ / Python 3.13+).

---

## Overview

KONGOR TOOL is a ground-up refactoring of K2 Engine modeling tools, strictly grounded in the official C++ engine implementation (`c_k2model.cpp`, `c_clip.cpp`, `s2exporter.cpp`).

### Key Features
* **Pure Python Core:** The binary serialization layer (`src/core/`) has zero external dependencies and does not import `bpy`, allowing 100% test coverage outside Blender.
* **Modern Python Ready:** Written with native `struct` handling; completely free of deprecated Python standard library modules such as `chunk` (removed in Python 3.13).
* **Automated Vertex Seam Splitting:** Accurately preserves UV seams, hard normal edges, and vertex colors following K2 C++ criteria.
* **Full Collision Surface Support:** Correctly exports collision hulls to native `surf` convex polyhedra chunks.
* **Animation Compression:** Constant keyframe reduction across all 10 K2 motion channels (`MKEY_*`).

---

## Project Structure

```
KONGOR-Tool/
├── src/
│   ├── __init__.py           # Blender add-on entry point
│   ├── core/                 # Pure Python binary I/O, models, and math
│   │   ├── chunk_io.py       # Tag/Length/Payload stream serializer
│   │   ├── constants.py      # K2 FourCC signatures and enums
│   │   ├── models.py         # Intermediate representation (IR)
│   │   ├── math_k2.py        # Matrix 3x4, Euler YXZ, Quat conversions
│   │   ├── smdl_reader.py    # SMDL v1/v3 reader
│   │   ├── smdl_writer.py    # SMDL v3 writer & vertex splitter
│   │   ├── clip_reader.py    # CLIP v1/v2 reader
│   │   ├── clip_writer.py    # CLIP v2 writer & key compression
│   │   └── xml_companion.py  # .material and .mdf companion XML
│   └── blender/              # Adapter layer for Blender API (bpy)
├── tests/                    # Pytest automated test suite
├── development_plan/         # C++ Ground Truth specifications
└── pyproject.toml            # Project configuration
```

---

## Testing

Run tests outside Blender with `pytest`:

```bash
# Run test suite
pytest

# Or via uv
uv run --python 3.13 --with pytest pytest
```

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

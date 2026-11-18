# KONGOR TOOL (v5.0.0)

Clean Architecture Blender Extension and Add-on for importing and exporting K2 Engine assets (`.model` / `.clip` / `.material` / `.mdf`). Designed for Blender >= 4.2 and Blender 5.0 (Python 3.11+ / Python 3.13+).

---

## Overview

KONGOR TOOL is an enterprise-grade, clean-room refactoring of the Heroes of Newerth K2 Engine 3D pipeline tools. Grounded strictly in the official engine C++ implementation (`c_k2model.cpp`, `c_clip.cpp`, `c_bone.h`, `s2exporter.cpp`), it completely eliminates legacy baggage, outdated APIs, and deprecated libraries.

### Key Features
* **Pure Python Core:** The binary serialization layer (`src/core/`) has zero external dependencies and zero `bpy` imports, enabling 100% test coverage outside Blender.
* **Modern Blender Ready:** Fully compatible with Python 3.11 and Python 3.13; eliminates the deprecated `chunk` module with native `struct` Little-Endian streams.
* **Blender 4.2+ Extension Format:** Bundles official `blender_manifest.toml` for the new Blender Extensions platform.
* **Automated Vertex Seam Splitting:** Accurately preserves UV seams, hard normal edges, and vertex colors following K2 C++ criteria (`s2exporter.cpp:1410-1485`).
* **Native Collision Surface (`surf`) Support:** Correctly exports collision hulls to native `surf` convex polyhedra chunks (bounding planes, points, edges, and tris).
* **Constant Animation Key Compression:** Keyframe reduction across all 10 motion channels (`MKEY_X` to `MKEY_SCALEZ`).
* **Ground Truth Matrix & Euler Math:** Accurate $3 \times 4$ bone rest matrices and right-handed Euler YXZ (Roll around Y $\rightarrow$ Pitch around X $\rightarrow$ Yaw around Z).

---

## Installation in Blender (>= 4.2 / 5.0)

### Method 1: Install as Blender Extension (Recommended)
1. Run the package build script to generate `dist/kongor_tool-5.0.0.zip`:
   ```bash
   python scripts/package_extension.py
   ```
2. In Blender, open **Edit > Preferences > Get Extensions**.
3. Click the top-right dropdown arrow $\rightarrow$ **Install from Disk...**
4. Select `dist/kongor_tool-5.0.0.zip`.

### Method 2: Manual Installation
Copy the contents of `src/` into a folder named `kongor_tool` in your Blender addons directory:
* Windows: `%APPDATA%\Blender Foundation\Blender\<version>\scripts\addons\kongor_tool`
* Linux: `~/.config/blender/<version>/scripts/addons/kongor_tool`
* macOS: `~/Library/Application Support/Blender/<version>/scripts/addons/kongor_tool`

---

## How to Use

### 1. 3D Viewport Sidebar (N-Panel)
Press **N** in the 3D Viewport and switch to the **KONGOR Tool** tab:
* **Inspect Scene:** Provides object, mesh, bone, and collision counts.
* **Import K2 Assets:** Import `.model` mesh/skeleton or `.clip` animation onto the active armature.
* **Export K2 Model:** Export visual meshes, armatures, and collision surfaces into `.model` (SMDL v3).
* **Export K2 Clip:** Export active armature animation into `.clip` (CLIP v2).
* **Active Object Properties:** Toggle **Collision Surface** or assign a **Rigid Bone Link Index**.

### 2. File Menu Integration
* `File > Import > Heroes of Newerth Model (.model)`
* `File > Import > Heroes of Newerth Clip (.clip)`
* `File > Export > Heroes of Newerth Model (.model)`
* `File > Export > Heroes of Newerth Clip (.clip)`

---

## Project Structure

```
KONGOR-Tool/
├── src/
│   ├── __init__.py           # Blender extension / add-on entry point
│   ├── core/                 # Pure Python binary I/O, models, and math (Zero BPY)
│   │   ├── chunk_io.py       # Tag/Length/Payload stream serializer
│   │   ├── constants.py      # K2 FourCC signatures and enums
│   │   ├── models.py         # Intermediate representation (IR) dataclasses
│   │   ├── math_k2.py        # Matrix43, Euler YXZ, and Quat conversions
│   │   ├── smdl_reader.py    # SMDL v1/v3 binary reader
│   │   ├── smdl_writer.py    # SMDL v3 binary writer & vertex seam splitter
│   │   ├── clip_reader.py    # CLIP v1/v2 binary reader
│   │   ├── clip_writer.py    # CLIP v2 binary writer & keyframe compressor
│   │   └── xml_companion.py  # .material and .mdf companion XML serializer
│   └── blender/              # Adapter layer for Blender API (bpy/bmesh/mathutils)
│       ├── properties.py     # Modern Blender PropertyGroups
│       ├── operators.py      # Import, Export, and Inspect operators
│       ├── scene_importer.py # K2 IR to Blender Scene converter
│       ├── scene_exporter.py # Blender Scene to K2 IR converter
│       ├── texture_manager.py# Principled BSDF & K2 sampler builder
│       └── ui_panels.py      # 3D Viewport N-Panel and File menus
├── tests/                    # 27 Automated unit & production asset tests
├── scripts/                  # Build and distribution automation
├── blender_manifest.toml     # Official Blender 4.2+ Extension Manifest
├── pyproject.toml            # Project packaging configuration
└── LICENSE                   # Apache-2.0 License
```

---

## Automated Test Suite

Run tests outside Blender with `pytest` across Python 3.11 and Python 3.13:

```bash
# Direct pytest
pytest -v

# Via uv
uv run --python 3.13 --with pytest pytest -v
uv run --python 3.11 --with pytest pytest -v
```

---

## License

This project is licensed under the Apache License 2.0. See [LICENSE](LICENSE) for details.

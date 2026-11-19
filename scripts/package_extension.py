"""
KONGOR TOOL - Packaging Script for Blender >= 4.2 / 5.0 Extension.
Creates a clean, installable .zip archive in dist/ without development files.
"""

import os
import zipfile
import pathlib

def build_package():
    repo_root = pathlib.Path(__file__).parent.parent
    dist_dir = repo_root / "dist"
    dist_dir.mkdir(exist_ok=True)

    output_zip = dist_dir / "kongor_tool-5.0.0.zip"
    if output_zip.exists():
        output_zip.unlink()

    src_dir = repo_root / "src"
    manifest = repo_root / "blender_manifest.toml"
    license_file = repo_root / "LICENSE"
    readme_file = repo_root / "README.md"

    files_to_pack = []

    # 1. Manifest and metadata
    if manifest.exists():
        files_to_pack.append((manifest, "blender_manifest.toml"))
    if license_file.exists():
        files_to_pack.append((license_file, "LICENSE"))
    if readme_file.exists():
        files_to_pack.append((readme_file, "README.md"))

    # 2. Add-on root __init__.py
    root_init = src_dir / "__init__.py"
    if root_init.exists():
        files_to_pack.append((root_init, "__init__.py"))

    # 3. Core module
    core_dir = src_dir / "core"
    for py_file in core_dir.glob("*.py"):
        files_to_pack.append((py_file, f"core/{py_file.name}"))

    # 4. Blender module
    blender_dir = src_dir / "blender"
    for py_file in blender_dir.glob("*.py"):
        files_to_pack.append((py_file, f"blender/{py_file.name}"))

    # 5. Integrated KONGOR Rig module and presets
    kongor_rig_dir = src_dir / "kongor_rig"
    if kongor_rig_dir.exists():
        for f in kongor_rig_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src_dir)
                # Skip caches, vscode configs, temporary files
                if any(part in ("__pycache__", ".vscode", "screenshots") for part in rel.parts):
                    continue
                if f.suffix in (".pyc", ".pyo"):
                    continue
                files_to_pack.append((f, str(rel).replace("\\", "/")))

    print(f"Packaging {len(files_to_pack)} files into {output_zip.name}...")
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for disk_path, arcname in sorted(files_to_pack, key=lambda x: x[1]):
            print(f"  + {arcname}")
            zf.write(disk_path, arcname)

    print(f"\n[OK] Package created successfully: {output_zip} ({output_zip.stat().st_size:,} bytes)")

if __name__ == "__main__":
    build_package()

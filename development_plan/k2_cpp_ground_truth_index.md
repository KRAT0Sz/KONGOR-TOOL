# K2 Engine C++ Ground Truth Source Index (KONGOR TOOL v5.0.0)

This document indexes all official C++ reference files from Heroes of Newerth / K2 Engine (`I:\hon\hon\src\k2` and `I:\hon\hon\lib\s2exporter`) as the single source of truth for KONGOR TOOL.

---

## 1. Core Model & Mesh Files (`I:\hon\hon\src\k2`)

| File | Size (Bytes) | Role & Key Responsibilities | Key C++ Structs / Methods |
| :--- | :--- | :--- | :--- |
| `c_k2model.h` | 8,190 | Header defining SMDL binary structures (`#pragma pack(1)`) | `modelHeader_t`, `boneBlock_t`, `SMeshBlock`, `faceBlock_t`, `surfBlock_t`, `textureCoordsBlock_t`, `tangentBlock_t`, `normalBlock_t`, `colorBlock_t` |
| `c_k2model.cpp` | 37,893 | Parser for SMDL v1/v3 model files and block dispatcher | `CK2Model::LoadModel()`, `CK2Model::ReadBlocks()`, `ParseHeader()`, `ParseBoneBlock()`, `ParseMeshBlock()`, `ParseVertexBlock()`, `ParseFaceBlock()`, `ParseSurfBlock()` |
| `c_mesh.h` | 5,885 | Mesh data structure, vertex arrays, skinning mode definitions | `CMesh`, `meshModes_enum` (`MESH_SKINNED_BLENDED=1`, `MESH_SKINNED_NONBLENDED=2`), `SVertexAttribute`, `blendedLinks`, `singleLinks`, `bonelink` |
| `c_mesh.cpp` | 2,557 | Mesh lifecycle management and vertex cleanup | `CMesh::PostLoad()`, `CMesh::Free()` |
| `c_bone.h` | 1,763 | Bone node representation, transformation matrices | `CBone`, `m_invBase`, `m_base`, `m_tmLocal`, `m_tmWorld`, `m_uiParentIndex` |
| `c_bone.cpp` | 636 | Bone constructors and initialization | `CBone::CBone()` |
| `c_skeleton.h` | 8,097 | Bone hierarchy, skeletal evaluation, poses | `CSkeleton`, `BoneStateVector`, pose types |
| `c_skeleton.cpp` | 49,732 | Animation blending, bone transformation concatenation | `CSkeleton::Pose()`, `CSkeleton::CalcBonePositions()` |
| `c_convexhull.h` | 1,453 | Collision convex polyhedron definitions | `CConvexPolyhedron`, `plane_t`, `edge_t` |
| `c_convexhull.cpp` | 4,607 | Collision convex polyhedron construction | `CConvexPolyhedron::AddPlane()`, `CConvexPolyhedron::AddPoint()` |
| `c_material.h` | 14,819 | K2 Material definition and shader parameters | `CMaterial`, `CMaterialPhase`, sampler definitions |
| `c_material.cpp` | 9,412 | XML parser for `.material` companion files | `CMaterial::Load()` |
| `c_filemanager.cpp` | ~100 KB | Binary block parser for Little-Endian 4-byte Tag + 32-bit Size | `CFileManager::BuildBlockList(pBuffer, iBufLen, vBlockList)` |

---

## 2. Animation Clip Files (`I:\hon\hon\src\k2`)

| File | Size (Bytes) | Role & Key Responsibilities | Key C++ Structs / Methods |
| :--- | :--- | :--- | :--- |
| `c_clip.h` | 3,960 | Header defining CLIP binary structures (`#pragma pack(1)`) | `SClipHeader`, `keyBlock_t`, `SBoneMotion`, `keyTypes_enum` (`MKEY_X` to `MKEY_SCALEZ`), `CLIP_VERSION=2` |
| `c_clip.cpp` | 12,605 | Parser for CLIP v1/v2 animation files | `CClip::Load()`, `CClip::ReadBlocks()`, `ParseBoneMotionBlock()`, `CalcQuatKeys()` |

---

## 3. Official 3ds Max S2 Exporter (`I:\hon\hon\lib\s2exporter\src`)

| File | Size (Bytes) | Role & Reference Value |
| :--- | :--- | :--- |
| `s2exporter.cpp` | 73,062 | Reference implementation for mesh extraction, bone hierarchy, vertex splitting at UV seams, and export flow |
| `c_outmodel.cpp` | 13,200 | Binary writer for `SMDL` container and sub-blocks (`head`, `bone`, `mesh`, `vrts`, `face`, `surf`, `sprt`) |
| `c_outmesh.cpp` | 1,696 | Extraction of mesh vertices, texture coordinates, tangent vectors, vertex colors, and bone links |
| `c_outclip.cpp` | 6,069 | Binary writer for `CLIP` container, keyframe reduction, and `bmtn` blocks |
| `c_outbone.cpp` | 660 | Bone matrix calculation (base and invBase matrix format) |
| `c_outmaterial.cpp` | 15,734 | `.material` XML companion generation |
| `c_outmdf.cpp` | 1,423 | `.mdf` (Model Definition File) XML companion generation |
| `meshtools.cpp` | 4,488 | Mesh topological tools, vertex deduplication, and seam calculation |

---

## 4. Binary Chunk Wire Format Specification

Every K2 Model (`.model`) and Clip (`.clip`) file follows the block-based container format parsed by `CFileManager::BuildBlockList`:

1. **4-Byte Magic Header:**
   - Model: `'S', 'M', 'D', 'L'` (`0x4C444D53`)
   - Clip: `'C', 'L', 'I', 'P'` (`0x50494C43`)
2. **Repeating Block Structure:**
   - `4 Bytes`: Block Name / FourCC (`head`, `bone`, `mesh`, `vrts`, `face`, `texc`, `tang`, `sign`, `colr`, `nrml`, `lnk1`, `lnk2`, `lnk3`, `surf`, `sprt`, `bmtn`)
   - `4 Bytes`: Little-Endian 32-bit Integer (`length`) = Size in bytes of block data (excluding the 8-byte header)
   - `N Bytes`: Block Payload
3. **End of File Verification:**
   - Total bytes processed must match `FileSize - 4`.

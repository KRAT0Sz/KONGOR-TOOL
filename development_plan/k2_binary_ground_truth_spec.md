# K2 Engine Binary Specification & Ground Truth Reference
**Project:** KONGOR TOOL (Version 5.0.0)  
**Author:** Agent 1 (K2 C++ Source Archaeologist)  
**Primary Source:** `I:\hon\hon\src\k2` and `I:\hon\hon\lib\s2exporter\src`  
**Status:** Approved Ground Truth Specification  

---

## 1. Container Wire Format (Chunk I/O)

Every K2 Model (`.model`) and Clip (`.clip`) file uses a chunk-based container parsed by `CFileManager::BuildBlockList` (`I:\hon\hon\src\k2\c_filemanager.cpp:1644-1682`):

```
+-------------------------------------------------------------+
| 4-Byte File Signature: "SMDL" (Model) or "CLIP" (Clip)     |
+-------------------------------------------------------------+
| Chunk 0: FourCC (4 bytes) | Length (int32, LE) | Payload... |
+-------------------------------------------------------------+
| Chunk 1: FourCC (4 bytes) | Length (int32, LE) | Payload... |
+-------------------------------------------------------------+
| ...                                                         |
+-------------------------------------------------------------+
```

* **FourCC**: 4 ASCII bytes (e.g., `'h','e','a','d'`, `'b','o','n','e'`, `'m','e','s','h'`)
* **Length**: 32-bit Little-Endian signed integer. Represents the payload byte count **excluding** the 8-byte chunk header (`name[4]` + `length[4]`).
* **Endianness**: **Little-Endian** for all integers and IEEE 754 32-bit floats.
* **Integrity Check**: Total bytes consumed across all chunks must equal `TotalFileSize - 4`.

---

## 2. SMDL (Model) Format Specification

Reference file: `I:\hon\hon\src\k2\c_k2model.h`, `c_k2model.cpp`, and `lib\s2exporter\src\c_outmodel.cpp`.  
Signature: `'S', 'M', 'D', 'L'` (`0x4C444D53`). Current version: `3` (`CURRENT_MODEL_VERSION`).

### 2.1 Chunk: `head` (Model Header)
* **C++ Struct**: `modelHeader_t` (`c_k2model.h:38-47`)
* **C++ Parser**: `CK2Model::ParseHeader` (`c_k2model.cpp:442-489`)
* **Size**: 44 bytes

| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | `version` | `int32` | 4 | File version (`3` for current SMDL) |
| `0x04` | `numMeshes` | `int32` | 4 | Number of `mesh` chunks in model |
| `0x08` | `num_sprites` | `int32` | 4 | Number of sprites (always `0` in modern K2) |
| `0x0C` | `num_surfs` | `int32` | 4 | Number of collision surface (`surf`) chunks |
| `0x10` | `numBones` | `int32` | 4 | Total number of bones in armature |
| `0x14` | `bmin` | `float[3]` | 12 | Bounding box minimum `(x, y, z)` |
| `0x20` | `bmax` | `float[3]` | 12 | Bounding box maximum `(x, y, z)` |

---

### 2.2 Chunk: `bone` (Bone Hierarchy & Rest Pose)
* **C++ Struct**: `boneBlock_t` (`c_k2model.h:49-58`)
* **C++ Parser**: `CK2Model::ParseBoneBlock` (`c_k2model.cpp:495-535`)
* **C++ Writer**: `COutModel::WriteFile` (`c_outmodel.cpp:260-275`)
* **Size per Bone**: `4 + 48 + 48 + 1 + (cNameLen + 1)` = `102 + cNameLen` bytes

| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | `parentIndex` | `int32` | 4 | Parent bone index (`-1` or `INVALID_BONE` for root bones) |
| `0x04` | `invBase` | `matrix43_t` | 48 | Inverse base transform matrix (`axis[3][3]` + `pos[3]`) |
| `0x34` | `base` | `matrix43_t` | 48 | Base transform matrix (`axis[3][3]` + `pos[3]`) |
| `0x64` | `cNameLen` | `uint8` | 1 | Length of bone name string (excluding null terminator) |
| `0x65` | `szBoneName` | `char[cNameLen + 1]` | `cNameLen + 1` | Null-terminated bone name string |

#### Matrix Structure (`matrix43_t`):
Defined in `k2_mathlib.h:165-170`:
```cpp
typedef struct matrix43_s {
    vec3_t axis[3]; // 3 vectors of 3 floats: axis[0], axis[1], axis[2] (36 bytes)
    vec3_t pos;     // translation vector: x, y, z (12 bytes)
} matrix43_t;
```
Total = 12 floats = 48 bytes.

---

### 2.3 Chunk: `mesh` (Mesh Header)
* **C++ Struct**: `SMeshBlock` (`c_k2model.h:60-73`)
* **C++ Parser**: `CK2Model::ParseMeshBlock` (`c_k2model.cpp:541-611`)
* **C++ Writer**: `COutModel::WriteFile` (`c_outmodel.cpp:285-303`)
* **Size**: `42 + (cNameLen + 1) + (cShaderNameLen + 1)` bytes

| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | `mesh_index` | `int32` | 4 | Sequential zero-based mesh index |
| `0x04` | `mode` | `int32` | 4 | Mesh skinning mode: `1 = MESH_SKINNED_BLENDED`, `2 = MESH_SKINNED_NONBLENDED` (`c_mesh.h:25-30`) |
| `0x08` | `num_verts` | `int32` | 4 | Total number of vertices in this mesh |
| `0x0C` | `bmin` | `float[3]` | 12 | Mesh local bounding box min `(x, y, z)` |
| `0x18` | `bmax` | `float[3]` | 12 | Mesh local bounding box max `(x, y, z)` |
| `0x24` | `bonelink` | `int32` | 4 | Rigid bone link index (`-1` if multiple bones or skin weights used) |
| `0x28` | `cNameLen` | `uint8` | 1 | Length of mesh name |
| `0x29` | `cShaderNameLen` | `uint8` | 1 | Length of default shader/material path |
| `0x2A` | `szNameBuffer` | `char[]` | variable | Null-terminated mesh name string, followed immediately by null-terminated shader name string |

---

### 2.4 Chunk: `vrts` (Vertex Coordinates)
* **C++ Struct**: `vertexBlock_t` (`c_k2model.h:129-134`)
* **C++ Parser**: `CK2Model::ParseVertexBlock` (`c_k2model.cpp:617-640`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `num_verts` array of `vec3_t`: each `float[3]` (`x, y, z` = 12 bytes)
* **Coordinate Note**: In K2 engine runtime loader (`c_k2model.cpp:634-636`), `x` and `y` are inverted (`-x, -y, +z`) for Yaw 180 fixup.

---

### 2.5 Chunk: `lnk1` / `lnk3` (Blended Skin Weights)
* **C++ Struct**: `blendedLinksBlock_t` (`c_k2model.h:75-79`)
* **C++ Parser**: `CK2Model::ParseBlendedLinksBlock` / `ParseBlendedLinksBlock2` (`c_k2model.cpp:659-908`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `num_verts` (`int32`, 4 bytes)
  * For each vertex $v \in [0, num\_verts - 1]$:
    * `num_weights` (`int32`, 4 bytes)
    * `weights`: array of `float[num_weights]` ($4 \times num\_weights$ bytes)
    * `indexes`: array of `uint32[num_weights]` bone indices ($4 \times num\_weights$ bytes)

---

### 2.6 Chunk: `lnk2` (Single Bone Links)
* **C++ Struct**: `singleLinksBlock_t` (`c_k2model.h:81-85`)
* **C++ Parser**: `CK2Model::ParseSingleLinksBlock` (`c_k2model.cpp:911-941`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `num_verts` (`int32`, 4 bytes)
  * `links`: array of `uint32[num_verts]` bone index per vertex ($4 \times num\_verts$ bytes)

---

### 2.7 Chunk: `face` (Polygon Triangles)
* **C++ Struct**: `faceBlock_t` (`c_k2model.h:87-92`)
* **C++ Parser**: `CK2Model::ParseFaceBlock` (`c_k2model.cpp:1091-1158`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `numFaces` (`int32`, 4 bytes)
  * `faceIndexSize` (`int8`, 1 byte):
    * `1`: 8-bit unsigned integer per index (`num_verts < 256`)
    * `2`: 16-bit Little-Endian unsigned integer per index (`num_verts < 65536`)
    * `4`: 32-bit Little-Endian unsigned integer per index (`num_verts >= 65536`)
  * `faces`: $numFaces \times 3$ indices, each of `faceIndexSize` bytes.

---

### 2.8 Chunk: `texc` (Texture UV Coordinates)
* **C++ Struct**: `textureCoordsBlock_t` (`c_k2model.h:94-98`)
* **C++ Parser**: `CK2Model::ParseTextureCoordBlock` (`c_k2model.cpp:947-974`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `channel` (`int32`, 4 bytes) - typically `0` for primary diffuse
  * `tverts`: array of `float[2]` (`u, v`) for each vertex ($8 \times num\_verts$ bytes)

---

### 2.9 Chunk: `tang` (Tangent Vectors)
* **C++ Struct**: `tangentBlock_t` (`c_k2model.h:100-104`)
* **C++ Parser**: `CK2Model::ParseTangentBlock` (`c_k2model.cpp:980-1004`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `channel` (`int32`, 4 bytes)
  * `tangents`: array of `float[3]` (`tx, ty, tz`) for each vertex ($12 \times num\_verts$ bytes)

---

### 2.10 Chunk: `sign` (Bitangent Sign)
* **C++ Struct**: `tangentBlock_t` (`c_k2model.h:100-104`)
* **C++ Parser**: `CK2Model::ParseSignBlock` (`c_k2model.cpp:1010-1030`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `channel` (`int32`, 4 bytes)
  * `signs`: array of `uint8` (`255` for negative / bitangent inversion, `0` for positive) for each vertex ($1 \times num\_verts$ bytes)

---

### 2.11 Chunk: `colr` (Vertex Colors)
* **C++ Struct**: `colorBlock_t` (`c_k2model.h:106-110`)
* **C++ Parser**: `CK2Model::ParseColorBlock` (`c_k2model.cpp:1036-1057`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `channel` (`int32`, 4 bytes)
  * `colors`: array of `uint8[4]` (`R, G, B, A`) for each vertex ($4 \times num\_verts$ bytes)

---

### 2.12 Chunk: `nrml` (Normals)
* **C++ Struct**: `normalBlock_t` (`c_k2model.h:112-115`)
* **C++ Parser**: `CK2Model::ParseNormalBlock` (`c_k2model.cpp:1062-1085`)
* **Payload**:
  * `mesh_index` (`int32`, 4 bytes)
  * `normals`: array of `float[3]` (`nx, ny, nz`) for each vertex ($12 \times num\_verts$ bytes)

---

### 2.13 Chunk: `surf` (Collision Convex Polyhedron)
* **C++ Struct**: `surfBlock_t` (`c_k2model.h:117-127`)
* **C++ Parser**: `CK2Model::ParseSurfBlock` (`c_k2model.cpp:1164-1241`)
* **C++ Writer**: `COutModel::WriteFile` (`c_outmodel.cpp:478-515`)
* **Payload Header** (48 bytes):
  * `surf_index` (`int32`, 4 bytes)
  * `num_planes` (`int32`, 4 bytes)
  * `num_points` (`int32`, 4 bytes)
  * `num_edges` (`int32`, 4 bytes)
  * `num_tris` (`int32`, 4 bytes) - number of collision triangles
  * `bmin` (`float[3]`, 12 bytes)
  * `bmax` (`float[3]`, 12 bytes)
  * `flags` (`int32`, 4 bytes)
* **Payload Data Stream**:
  1. `planes`: `num_planes` $\times$ `CPlane` (16 bytes each: `float normal[3], float dist`)
  2. `points`: `num_points` $\times$ `CVec3f` (12 bytes each: `float point[3]`)
  3. `edges`: `num_edges` $\times$ `CEdge` (24 bytes each: `float normal[3], float point[3]`)
  4. `tris`: $num\_tris \times 3$ $\times$ `uint32` (4 bytes each point index)

---

## 3. CLIP (Animation) Format Specification

Reference file: `I:\hon\hon\src\k2\c_clip.h`, `c_clip.cpp`, and `lib\s2exporter\src\c_outclip.cpp`.  
Signature: `'C', 'L', 'I', 'P'` (`0x50494C43`). Current version: `2` (`CLIP_VERSION`).

### 3.1 Chunk: `head` (Clip Header)
* **C++ Struct**: `SClipHeader` (`c_clip.h:86-91`)
* **C++ Writer**: `COutClip::WriteFile` (`c_outclip.cpp:188-198`)
* **Size**: 12 bytes

| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | `iVersion` | `int32` | 4 | Version (`2`) |
| `0x04` | `iNumMotions` | `int32` | 4 | Number of animated bones |
| `0x08` | `iNumFrames` | `int32` | 4 | Number of animation frames |

---

### 3.2 Chunk: `bmtn` (Bone Motion Block)
* **C++ Struct**: `keyBlock_t` (`c_clip.h:93-103`)
* **C++ Parser**: `CClip::ParseBoneMotionBlock` (`c_clip.cpp:223-280`)
* **C++ Writer**: `COutClip::WriteFloatKeys` / `WriteByteKeys` (`c_outclip.cpp:125-169`)

#### Header Layout:
| Offset | Field | Type | Size | Description |
| :--- | :--- | :--- | :--- | :--- |
| `0x00` | `boneIndex` | `int32` | 4 | Zero-based index of bone matching model |
| `0x04` | `key_type` | `int32` | 4 | Keyframe channel type (0 to 9) |
| `0x08` | `num_keys` | `int32` | 4 | Number of keys (`1` for constant / static value, or `iNumFrames`) |
| `0x0C` | `cNameLen` | `uint8` | 1 | Length of bone name string |
| `0x0D` | `szBoneName` | `char[cNameLen + 1]` | `cNameLen + 1` | Null-terminated bone name string |

#### Channel Types (`keyTypes_enum` `c_clip.h:69-82`):
| ID | Key Type | Data Type | Units / Notes |
| :--- | :--- | :--- | :--- |
| `0` | `MKEY_X` | `float` (4 B) | Translation X |
| `1` | `MKEY_Y` | `float` (4 B) | Translation Y |
| `2` | `MKEY_Z` | `float` (4 B) | Translation Z |
| `3` | `MKEY_PITCH` | `float` (4 B) | Euler Pitch around X axis (degrees) |
| `4` | `MKEY_ROLL` | `float` (4 B) | Euler Roll around Y axis (degrees) |
| `5` | `MKEY_YAW` | `float` (4 B) | Euler Yaw around Z axis (degrees, Bone 0 has +180 deg in runtime) |
| `6` | `MKEY_VISIBILITY` | `uint8` (1 B) | Visibility state (`1` = visible, `0` = hidden) |
| `7` | `MKEY_SCALEX` | `float` (4 B) | Scale X |
| `8` | `MKEY_SCALEY` | `float` (4 B) | Scale Y |
| `9` | `MKEY_SCALEZ` | `float` (4 B) | Scale Z |

Immediately following `szBoneName` is the payload of `num_keys` values (`float` or `uint8`).

---

## 4. Mathematics & Coordinate Space Ground Truth

### 4.1 Coordinate System
* **Engine Space**: Right-Handed Cartesian coordinate system.
  * $+X$: Right
  * $+Y$: Forward
  * $+Z$: Up
* **Euler Angle Convention**: `YXZ` order (`c_clip.cpp:200-204`, `math_inlines.h:417-437`).
  * Roll ($Y$) $\rightarrow$ Pitch ($X$) $\rightarrow$ Yaw ($Z$)
  * Quat conversion formula (`math_inlines.h:425-437`):
    $$\begin{aligned}
    q_x &= \cos(\text{yaw}/2)\sin(\text{pitch}/2)\cos(\text{roll}/2) - \sin(\text{yaw}/2)\cos(\text{pitch}/2)\sin(\text{roll}/2) \\
    q_y &= \cos(\text{yaw}/2)\cos(\text{pitch}/2)\sin(\text{roll}/2) + \sin(\text{yaw}/2)\sin(\text{pitch}/2)\cos(\text{roll}/2) \\
    q_z &= \cos(\text{yaw}/2)\sin(\text{pitch}/2)\sin(\text{roll}/2) + \sin(\text{yaw}/2)\cos(\text{pitch}/2)\cos(\text{roll}/2) \\
    q_w &= \cos(\text{yaw}/2)\cos(\text{pitch}/2)\cos(\text{roll}/2) - \sin(\text{yaw}/2)\sin(\text{pitch}/2)\sin(\text{roll}/2)
    \end{aligned}$$

---

### 4.2 Vertex Seam Splitting Rules (BUG-02 Fix)
Reference: `I:\hon\hon\lib\s2exporter\src\s2exporter.cpp:1410-1485`.

Two vertices at the same geometric position `P` can only share the same vertex index if ALL of the following criteria match:
1. **Normal**: `memcmp(normal_a, normal_b, sizeof(vec3_t)) == 0`
2. **UV Coordinates**: `memcmp(uv_a, uv_b, sizeof(vec2_t)) == 0` across all active texture channels
3. **Tangent**: `abs(tan_a - tan_b) < 0.0001` across all active tangent channels
4. **Sign**: `sign_a == sign_b` across all active channels
5. **Vertex Color**: `memcmp(col_a, col_b, sizeof(bvec4_t)) == 0` across all color channels
6. **Bone Weights**: Bone links and weight distributions match.

If ANY of these conditions fail, the vertex **must be split** into duplicate vertices with new indices.

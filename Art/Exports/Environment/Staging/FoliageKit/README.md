# Foliage & Ground Transition Asset Kit (v2 Revision)

## Asset Summary

### 1. Stylized Foliage Clumps
* **`ENV_Temple_Foliage_Clump_A.fbx`**
  - Type: Medium/Large rounded organic foliage clump
  - Polycount: 1,780 tris (1,725 verts)
  - Dimensions: 1.72 m (X) x 1.44 m (Y) x 0.88 m (Z)
  - Shading: Transferred spherical radial vertex normals + upward bias for unified painterly lighting across cloud lobes.
  - Structure: 5 organic convex cloud lobes with tangent-draped leaf shell cards and gnarled base root anchors.

* **`ENV_Temple_Foliage_Clump_B.fbx`**
  - Type: Low-spreading shrub mound for wall bases and rubble perimeters
  - Polycount: 1,472 tris (1,371 verts)
  - Dimensions: 2.28 m (X) x 1.38 m (Y) x 0.55 m (Z)
  - Shading: Transferred spherical radial vertex normals.
  - Structure: 5 low, horizontally spreading lobes with trailing ground fronds and root network.

### 2. Clinging Wall & Column Creepers
* **`ENV_Temple_Foliage_Creeper_Wall.fbx`**
  - Type: Wall-conforming clinging ivy creeper
  - Polycount: 1,248 tris (1,164 verts)
  - Dimensions: 1.49 m (X) x 0.10 m (Y) x 2.25 m (Z)
  - Placement: Back sits flush against wall plane ($Y = 0$). Sinuous climbing stems with flat-adhering 3-lobed and 5-lobed ivy leaves.
  - Shading: Soft forward-facing (+Y) normals with gentle radial spread.

* **`ENV_Temple_Foliage_Creeper_Column.fbx`**
  - Type: Column & pier conforming clinging ivy drape
  - Polycount: 1,296 tris (1,208 verts)
  - Dimensions: 0.92 m (X) x 0.29 m (Y) x 1.72 m (Z)
  - Placement: Conforms strictly to a cylindrical column surface ($R = 0.50\text{ m}$). Tendrils clasp the stone shaft with hanging drapes.
  - Shading: Radial cylindrical normals centered on column Z axis.

### 3. Ground Transition & Dirt/Rubble Patches
* **`ENV_Temple_Ground_DirtPatch_A.fbx`**
  - Type: Low-profile curved dirt & sediment drift mound
  - Polycount: 424 tris (253 verts)
  - Dimensions: 2.20 m (X) x 1.60 m (Y) x 0.074 m (Z)
  - Features: Soft dirt ripples feathered down to 0.001 m at edges, 4 embedded chipped flagstone fragments, and gravel.

* **`ENV_Temple_Ground_DirtPatch_B.fbx`**
  - Type: Linear seam wall-base dirt & crumbling mortar bank
  - Polycount: 192 tris (119 verts)
  - Dimensions: 2.40 m (X) x 0.60 m (Y) x 0.039 m (Z)
  - Placement: Snaps along wall/column bases to break the hard right-angle tile seam.

* **`ENV_Temple_Ground_CrackedMortar_C.fbx`**
  - Type: Fractured flagstone plate with recessed mortar gravel bed
  - Polycount: 30 tris (26 verts)
  - Dimensions: 1.30 m (X) x 1.10 m (Y) x 0.030 m (Z)
  - Features: Weathered stone slab split into 3 irregular pieces by an open crevice filled with dark loam and crushed mortar.

---

## PBR Texture Maps (2048 x 2048)

### Foliage Kit (`M_Temple_Foliage`)
- `ENV_Temple_Foliage_BaseColor.png`: sRGB Albedo (antique olive, sage, warm dried ochre tips, weathered umber stems; 0.000% cyan-teal).
- `ENV_Temple_Foliage_Normal.png`: Tangent-space Normal map.
- `ENV_Temple_Foliage_Mask.png`: URP Lit packed mask (R = Metallic: 0, G = Occlusion, B = 0, A = Smoothness ~0.15-0.26).

### Ground Transition Kit (`M_Temple_GroundTransition`)
- `ENV_Temple_GroundTransition_BaseColor.png`: sRGB Albedo (warm sandstone stone tone, sandy silt loam, crumbled mortar).
- `ENV_Temple_GroundTransition_Normal.png`: Tangent-space Normal map.
- `ENV_Temple_GroundTransition_Mask.png`: URP Lit packed mask (R = Metallic: 0, G = Occlusion, B = 0, A = Smoothness ~0.08-0.22).

---

## Verification
- Master Blender file: `Art/Blender/Revisions/foliage_kit_v2/TempleEnvironmentKit_foliage_v2.blend`
- Cycles preview renders: `Art/Exports/Environment/Staging/FoliageKit/Previews/`
- Production Unity scenes and scripts were untouched per workflow boundary.

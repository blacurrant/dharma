# Central Ceremonial Altar Medallion — Staging Handoff (Reworked)

Faithfully authored in Blender matching Reference 1 (ancient circular stone medallion embedded in courtyard pavers with 4 cardinal roundels, archaic rune band, 24 scalloped slab teeth, and structural fracture cracks) and Reference 2 (stepped concentric profile with recessed drainage canals and raised central altar plinth).

Unity scenes were not edited. Master `Art/Blender/TempleEnvironmentKit.blend` was not touched.

Source: `Art/Blender/Revisions/medallion/TempleEnvironmentKit_medallion.blend`

## 3D Asset

| | |
|---|---|
| FBX | `ENV_Temple_Central_Medallion.fbx` |
| Tris / verts | 5952 / 2978 |
| Diameter | 7.746 m (spec 7.5–8.0 m) |
| Overall Thickness | 0.184 m (from foundation Z = -0.10 m to altar crest Z = +0.084 m) |
| Outer Lip | local z = 0.015 m (sits flush against floor pavers) |
| Altar Crest | local z = 0.082 m (+8.2 cm raised ceremonial collar) |
| Recessed Canals | local z = 0.006–0.010 m (deep shadow/drainage grooves) |
| 4 Cardinal Roundels | centered at r = 2.03 m on +-X and +-Y, raised rim to z = 0.065 m |
| Collision | none — walkable flat surface; use the floor collider |

## Pivot / Axes
FBX is already Y-up, -Z forward, identity transform.
- Origin: disc centre, floor plane z = 0.
- Place at courtyard centre `(0, 0, 0)` in Unity.
- Walking surface sits 1.5 cm proud of courtyard floor.

## Materials (URP Lit)
`M_Temple_Central_Medallion` — 2048x2048, ~262 px/m.

| Map | Color space | Contents |
|---|---|---|
| `_BaseColor` | sRGB | Weathered sandstone matching M_UE_Ancient_Ground (measured mean RGB [78.1, 70.1, 52.3]). Warm olive moss in carved recesses. |
| `_Normal` | linear, OpenGL +Y | Authentic chiseled V-grooves: 72 archaic runes, 4 cardinal roundel spirals, 8 primary slab joints, 24 voussoir joints, 2 major fracture cracks. |
| `_Mask` | linear | R = 0 (dielectric stone), G = Ambient Occlusion, B = 0, A = Smoothness (1 - Roughness). |

## Q18 Palette Compliance
Measured **0.0000%** cyan/teal (strictly 0.0% reserved for gameplay telegraphs).

## Previews
`Previews/`:
- `medallion_game42.png`: 42 deg elevated gameplay view (Camera A2).
- `medallion_close.png`: 3/4 perspective close-up of central altar and cardinal roundel.
- `medallion_top.png`: Top-down orthographic plan view.
- `medallion_rim.png`: Scalloped outer rim meeting floor pavers.

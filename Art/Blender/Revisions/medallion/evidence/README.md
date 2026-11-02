# Central Ceremonial Altar Medallion — Staging Handoff

Blender-only authoring from CD-locked concept `courtyard_balanced.jpg`. Unity scenes were not edited. Master `Art/Blender/TempleEnvironmentKit.blend` was not touched.

Source: `Art/Blender/Revisions/medallion/TempleEnvironmentKit_medallion.blend`

## Asset

| | |
|---|---|
| FBX | `ENV_Temple_Central_Medallion.fbx` |
| Tris / verts | 2592 / 1298 |
| Diameter | 7.78 m (spec 7.5–8.0) |
| Thickness | 0.108 m (spec 0.08–0.12) |
| Lip | local z = 0.010 m (Unity Y = 0.01 when placed at origin) |
| Inner field | local z ≤ 0.018 m |
| Bottom | local z = −0.090 m |
| Collision | none — walkable flat surface; use the floor collider |

## Pivot / axes

FBX is already Y-up, −Z forward, identity transform.

- Origin: disc centre, floor plane z = 0.
- Place at courtyard centre `(0, 0, 0)` in Unity. Walking surface is ~1 cm proud of y = 0.
- Local +Y is arbitrary (radial). No facing.

The 10.8 cm slab thickness goes **below** the walking surface so the disc can sit in a floor-tile well. If centre pavers are left in place, the body clips into the 0.30 m tile volume and only the 1 cm lip shows. If centre pavers are removed, cover the 10 cm edge or the side wall reads as a curb.

Outer 0.25 m of the top is beveled down to the 1 cm lip so the step does not trip.

## Materials (URP Lit)

`M_Temple_Central_Medallion` — 2048×2048, ~262 px/m.

| Map | Color space | Contents |
|---|---|---|
| `_BaseColor` | sRGB | Weathered sandstone, Floor_A family (measured mean RGB 73.8 / 64.9 / 50.2). Warm olive moss in carved recesses. |
| `_Normal` | linear, OpenGL +Y | Concentric grooves, broken inner scroll, dentil band, cable rim, cracks, chips. |
| `_Mask` | linear | R = metallic (0), G = AO, B = 0, A = smoothness |

FBX links BaseColor + Normal. **Mask is not in the FBX** — assign it in Unity (Metallic from A, Occlusion from G).

Relief is abstract concentric masonry + a broken 3-arm scroll + a 20-unit dentil band. No sun-disc, lotus, mandala, Om, Devanagari, or other script.

## Q18

Measured **0.000%** cyan/teal (hue 160–200, sat > 0.20) on BaseColor. Greens are warm olive in the grooves only.

## Honest limits

- Cycles look-dev, not Unity URP. Raking sun in the previews is stronger than the in-game key will be; at A2 the rings still read, the inner scroll is secondary.
- Carving is 2048 normals plus 1–2 cm geo rings. It is not a hero sculpt. Close-up shows map resolution and a slightly grainy inner channel.
- Contrast vs Floor_A is modest on purpose so ground telegraphs stay readable.
- No collision mesh. No Unity placement.

## Previews

`Previews/` — `medallion_game42.png` is the 42° gameplay sheet. `medallion_rim.png` is the trip-edge check. `medallion_close.png` / `medallion_top.png` show the relief.

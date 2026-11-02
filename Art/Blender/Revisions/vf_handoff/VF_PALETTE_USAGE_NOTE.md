# VF palette & usage note (iteration 1)

Folder `Art/Blender/Revisions/vf_handoff/textures/`. Coordinates are **Unity world metres** (x, z). All maps are 8-bit PNG, authored seamless/anchored as stated. **Tested only in Blender (Cycles/EEVEE, Standard view); not tested in Unity.**

## Hue / value rules (measured on the files)
**No teal/cyan:** 0 texels with hue 145–215° and HSV saturation > 0.06 in any of the 10 colour-and-alpha maps (counted over visible texels, alpha > 0.02, and again over all texels including colour under alpha 0). Measured from the stored 8-bit sRGB bytes of the PNGs (`scripts/16_color_audit.py`, `evidence/16_color_audit.json`); HSV saturation = (max−min)/max.

**Hue of the 10 colour-and-alpha maps** (texels with saturation > 0.06): warm greys/browns 30–60° (cracks 30–60°, wear 36–48°, chipped edges 40–49°, rain 36–45°, salt 46–49°, soot 30–40°); olive moss 72.7–78.5°. This statement does **not** cover `VF_Floor_MacroTint_1024` (below) or the two grey macro-value maps (single-channel, no hue).

**HSV saturation per map** (visible texels; median / 95th percentile / max):

| Map | median | p95 | max |
|---|---|---|---|
| Cracks | 0.20 | 0.24 | 0.26 |
| Wear | 0.15 | 0.27 | 0.35 |
| Chipped edges | 0.33 | 0.35 | 0.38 |
| Rain streaks | 0.33 | 0.36 | 0.36 |
| Salt | 0.16 | 0.19 | 0.19 |
| Moss (generic / wall base / floor joints) | 0.36 | 0.39 | **0.40** |
| Soot floor / soot wall | 0.23 / 0.29 | 0.23 / 0.29 | 0.23 / 0.29 |

The palette hexes below are the true values (moss `#3A4228` has HSV saturation 0.39). These dark, near-neutral colours are low in *value*, not low in saturation, so do not describe the moss as "desaturated" in HSV terms; it is muted because it is dark and mixed 0.7 at most over stone.

**Macro tint (`VF_Floor_MacroTint_1024`)** is a multiplier (data = 0.5 neutral, applied as 2×): its range is **warm ×(1.11, 1.02, 0.89) to cool ×(0.93, 0.97, 1.11)**. The raw cool multiplier is blue-violet, hue 229° (saturation 0.16), outside the 30–78° range above and outside 145–215°; the raw data hue spans 0–300° only because most texels are near-neutral. Applied to a neutral stone card (#8A857D) at full strength: warmest texel `#918677` (hue 36°, sat 0.18), coolest `#868383` (hue 357°, sat 0.02, i.e. almost neutral), 0 texels in 145–215° with saturation > 0.06; the cool end neutralises the warm stone, it does not turn it blue.

| Role | Hex (sRGB) |
|---|---|
| crack core / stain / lit lip | `#0F0E0C` / `#1A1814` / `#B2AC98` |
| wear light smear / dark smudge / pit | `#AFA894` / `#221F19` / `#16140F` |
| chipped-edge pit / rim / arris | `#17150F` / `#BAB39F` / `#A9A38F` |
| rain streak | `#1B1812` (×0.85–1.2) |
| salt crystal / damp stain | `#D2CCB8` / `#8F8974` |
| moss dark → light (olive, low saturation) | `#3A4228` → `#5C6342` |
| soot (floor, wall) | `#0D0C0A`, `#0E0C0A` |

## Per-map usage
Overlay blend (all colour maps): `albedo = lerp(albedo, tex.rgb, tex.a * opacity * weight)` on **linear** albedo (alpha blend, not overlay/multiply; overlay-blend would shift contrast unpredictably under the telegraph). Macro maps: **multiply** `albedo *= lerp(1, 2*m, opacity)` (0.5 = neutral).

| Map | Size / world footprint | Import | Default (range) | Weight inside r<10 m | Mapping / wrap |
|---|---|---|---|---|---|
| `VF_Floor_MacroValue_2048` | 2048², whole 40×40 m | **sRGB off** (linear), 1 channel | 0.75 (0.5–1.0) | 1.0 (damping baked in: ×0.25 at r≤8, full at r≥14) | U=(x+20)/40, V=(z+20)/40, clamp |
| `VF_Floor_MacroValue_NoDamp_2048` | same | sRGB off | alt. to the above | shader-side radial weight | same; use **either** this or the damped one, never both |
| `VF_Floor_MacroTint_1024` | 1024², 40×40 m | sRGB off, RGB | 0.60 (0.3–1.0) | 1.0 (damped in map) | same as macro value |
| `VF_Floor_Cracks_2048` | 8×8 m tile | sRGB **on**, alpha straight | 0.75 (0.4–0.9) | **0.35** | u=x/8, v=z/8, repeat |
| `VF_Floor_Wear_1024` | 4×4 m tile | sRGB on | **0.50** (0.25–0.7) | 0.40 | u=x/4, v=z/4, repeat |
| `VF_Floor_ChippedEdges_1024` | 2×2 m tile on the 2 m grid (joints at even metres) | sRGB on | 0.85 (0.5–1.0; 0.6 if close-ups look busy) | 0.50 | u=x/2, v=z/2, repeat |
| `VF_Weather_MossFloorJoints_1024` | 2×2 m, same grid | sRGB on | 0.80 (0.5–1.0) | **0** | as chipped edges |
| `VF_Wall_RainStreaks_1024` | 3×3 m, streaks run along V | sRGB on | 0.65 (0.3–0.9) | n/a (walls) | u = coordinate along the wall, v = height/3 |
| `VF_Weather_Salt_1024` | 2×2 m | sRGB on | 0.55 (0.3–0.8) | 0.30 | floor planar or wall coords; gate by height |
| `VF_Weather_Moss_1024` | 2×2 m, generic | sRGB on | 0.70 (0.4–0.9) | 0 | **must be gated** (height < ~0.6 m, drains, joints) |
| `VF_Weather_MossWallBase_1024` | 3 m wall height, pre-gated | sRGB on | 0.80 (0.5–1.0) | n/a | **U repeat, V clamp** (V repeat leaves a faint line); bottom = floor line |
| `VF_Weather_SootFloorRing_1024` | 3.2×3.2 m decal (file name is historical: it is an asymmetric smudge, not a ring) | sRGB on | 0.85 (0.5–1.0) | 0 | decal near a brazier; **rotate randomly per instance** |
| `VF_Weather_SootWallPlume_512x1024` | 1.5×3.0 m decal | sRGB on | 0.80 (0.5–1.0) | n/a | wall decal, only if the brazier is within ~1 m of the wall (none of the current 4 is: nearest 1.9 m) |

Unity import (recommended, **untested**): colour maps sRGB on, *Alpha Is Transparency* on, mipmaps on; data maps sRGB off, uncompressed or high-quality (banding); keep PNG source, compress only after a visual check.

## Where NOT to use them
- **Combat circle (r < 10 m):** floor variation must stay low-contrast. Measured: tile-to-tile luminance spread inside the circle 0.020 → 0.024 (k 0.75) / 0.027 (k 1.0) against 0.077 → 0.095 / 0.107 outside. Use the weights above; do not raise them to “make it more visible”.
- **Telegraphs:** draw telegraph decals after all overlays; telegraph colour stays cyan-teal and is never used in these maps.
- **Bronze/gold and emissive zones** (inlays, pillar coil, ember): gate by `(1 - Mask.R)` and the emission map, so cracks/moss don't land on metal. *Recommended; not tested.*
- **Vertical faces:** floor-type overlays are top-down planar. Keep them to up-facing surfaces (`normal.y > ~0.55`, soft to 0.85); otherwise stair risers/platform sides streak. Wall-type maps only on walls.
- **Moss** only at wall bases, drains and joints; never on the dais top, the altar or pillar shafts.
- **Soot** near the braziers only (≤ ~1.6 m), away from the combat circle; floor smudges rotate/mirror per instance.
- **Existing sun/ring reliefs** (altar crown, wall panels, studs) are untouched here; the overlays neither remove nor repeat them.

## Known weak spots (be honest)
Wear reads boxy/procedural (lowest default, 0.50). Chipped-edge speckle can look busy at close-ups. Wall rain streaks and moss are subtle at the gameplay camera (seen only in close-ups); the floor overlays carry the visible change there. `MossWallBase` and floor-joint moss are low-contrast against the stone by design.

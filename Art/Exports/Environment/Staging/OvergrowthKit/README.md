# Overgrowth Kit v3 — Staging Handoff

Blender-only authoring. Unity scenes were not edited. Master `Art/Blender/TempleEnvironmentKit.blend` was not touched.

Source: `Art/Blender/Revisions/overgrowth_kit_v3/TempleEnvironmentKit_overgrowth_v3.blend`

## Pivot / axes (FBX already Y-up, −Z forward, identity transform)

| Asset | Pivot | Local front | Notes |
|---|---|---|---|
| `ENV_Temple_Root_Claw_Pillar` | Pillar centre, floor | n/a (radial wrap) | Inner contact ~R 0.56 m. Place on existing pillar origin. |
| `ENV_Temple_Root_Claw_Corner` | Inner wall corner, floor | +X and +Y = courtyard | Walls occupy X≤0 and Y≤0. Roots stay in +X/+Y. |
| `ENV_Temple_Vine_Curtain_A/B` | Top attachment | +Y = courtyard (away from wall) | Geometry hangs down (−Y in Unity). Place origin on cornice / lintel. |
| `ENV_Temple_Tree_Canopy_A/B` | Trunk base | +Y = courtyard lean | Sit behind perimeter walls, r ≥ 18 m. |
| `ENV_Temple_EarthBed_A/B` | Footprint centre | n/a | Stone rim top ~0.24–0.26 m. Recessed earth ~0.10–0.15 m. Place outside the 10 m combat radius. |

## Materials (URP Lit)

| Material | Maps | Notes |
|---|---|---|
| `M_Temple_Overgrowth_Wood` | Wood_{BaseColor,Normal,Mask} | Mask: R=0 metallic, G=AO, A=smoothness |
| `M_Temple_Overgrowth_Foliage` | Foliage_{BaseColor,Normal,Mask} | BaseColor is **RGBA**. Enable Alpha Clip (~0.35). A=1 on canopy volume, silhouette alpha on leaves/ivy/grass. |
| `M_Temple_Overgrowth_Ground` | Ground_{BaseColor,Normal,Mask} | Sandstone / loam / moss / gravel atlas |

Earth beds include an unused Wood slot (index 0). Foliage = 1, Ground = 2.

## Q18

Measured 0.000% cyan/teal (hue 160–200, sat > 0.20) on all three BaseColor atlases. Olive / sage / dried ochre foliage; umber bark; warm sandstone.

## Honest limits

- Canopy trees are stylized pancake-lobe masses with drooping leaf plates. Close-up still shows hull faceting; they are meant to read from camera A2 (42° / ortho 7.5), not as hero sculpts.
- Corner roots need the two wall planes; without them the piece looks like a radiating fan.
- Earth pavers are modular faceted slabs with a recessed loam basin, not sculpted flagstones. Grass tufts are nested in the earth, not on slab faces.
- Vine A is the dense curtain; Vine B is the thinner tendril variant for arches.
- No collision authored. No Unity scene placement (Unity Engineer).

## Previews

`Previews/` — Cycles look-dev, not Unity URP. `kit_overview_game42.png` is the 42° layout sheet.

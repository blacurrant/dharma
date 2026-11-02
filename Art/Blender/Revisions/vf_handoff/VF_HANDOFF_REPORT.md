# VF handoff - iteration 1 (Environment Artist)

Everything is in `Art/Blender/Revisions/vf_handoff/` (new). Production `.blend`, `Art/Exports` (Review/ unchanged), Staging, `Textures/Source`, v2_study, gate1_zones, the backup and all Unity files were not touched; nothing staged, committed, pushed, promoted; no LFS. No new models, no motif removal, no central-structure or arch decision. Continuing from: Gate 1b working copy (`gate1_zones/TempleEnvironmentKit_gate1_zones.blend`, copied to `vf_handoff/TempleEnvironmentKit_vf_working.blend`).

## For the Unity Engineer (copy these)
- `textures/` (13 PNG) + `VF_PALETTE_USAGE_NOTE.md` (hex, blend, sRGB/linear, opacity, wrap, where NOT).
- `VF_PROP_PLACEMENTS.md/.json`, `VF_PIPELINE_ANSWER.md`.
- Visual proof: `contact/VF_contact_floor.png`, `contact/VF_contact_weather.png` (each texture on a neutral card: BEFORE | AFTER | MAP) and `contact/VF_contact_courtyard.png` (real kit before/after: plan, gameplay camera, telegraph check, dais, brazier/wall close-ups). Individual renders in `renders/`.
- Coordinates everywhere: Unity world (x, z) = Blender (x, y). Macro maps: U=(x+20)/40, V=(z+20)/40.

## Status per item
| Item | Status | Evidence / caveat |
|---|---|---|
| 1a Floor macro value (2048², 40×40 m, grey) | **PASS** (Blender) | std 0.026 inside r<10 vs 0.111 outside; baked damping; no cyan. Not Unity-tested |
| 1b Macro tint (1024², RGB) | **PASS** (Blender) | multiplier warm ×(1.11,1.02,0.89) / cool ×(0.93,0.97,1.11); raw cool hue 229°; on neutral stone the result has 0 cyan texels (see corrections) |
| 1c Cracks (8 m tile, 2048²) | **PASS** | cores sized 5–10 cm so they resolve at the gameplay camera (~49 px/m); readable in the camera render |
| 1d Chipped tile edges (2 m grid, 1024²) | **PASS** | breaks the joint grid; speckle can look busy in close-ups (use 0.6) |
| 1e Wear/scuffs (4 m tile) | **PASS technically, weak visually** | boxy/procedural; default lowered to 0.50; replace in iteration 2 if kept |
| 2a Rain streaks (3 m, walls) | **PASS technically; UNVERIFIED legibility** | faint at the gameplay camera, visible only in close-ups |
| 2b Salt/mineral | **PASS technically**; subtle | gate by height |
| 2c Moss (generic, wall base, floor joints) | **PASS technically**; low contrast by design | olive, hue 72.7–78.5°, HSV saturation up to 0.40 (see corrections); generic one must be gated |
| 2d Soot floor smudge | **PASS** (after a fix, see below) | asymmetric, no ring/hole; visible on the dais brazier close-up |
| 2e Soot wall plume | **texture PASS, in-scene UNVERIFIED** | no current brazier is within 1 m of a wall (nearest 1.9 m), so the placed decals are not visible; use only with a wall-adjacent brazier/sconce |
| 3 Palette/usage note (1 page) | **PASS** | `VF_PALETTE_USAGE_NOTE.md` |
| Pipeline answer (floor parts baked + compared) | **PASS (evidence), recommendation: Unity-side world-space overlays** | all 8 floor parts: zone MD5 stable ×5 steps, FBX identical, texel agreement 100 %; 6 of the 8 floor parts (Floor_A–D, Platform_A, Stairs_A) are single-zone `StoneWarm`; the 2 border pieces carry bronze/gold inlays; the 400 floor instances share 6 baked sets |
| Prop placements (existing parts only) | **PASS (script-checked), visually UNVERIFIED** | 8 rows, all r ≥ 12.8 m; not placed/rendered in a scene |
| Before/after contact sheets | **PASS** | 3 sheets, Blender-rendered inside `vf_handoff/` |
| SHA-256 manifest | **PASS** | `VF_MANIFEST.json`, `SHA256SUMS.txt`; textures regenerated twice → identical hashes |
| Protected sets | **PASS, one expected change** | 9 of 10 identical; `Assets/Scenes` hash differs only because `ArtTest_VisualFoundation.unity` was saved at 14:06:30 by the Unity side (I never wrote under `Assets/`) |

## Measured effect (Blender EEVEE, plan view + gameplay camera; `evidence/13_courtyard*.json`)
Tile-to-tile luminance spread outside the combat circle: 0.077 → 0.095 (default) / 0.107 (k 1.0). Inside the circle: 0.020 → 0.024 / 0.027. Telegraph lift 0.157 → 0.160 and floor std under the telegraph footprint 0.0580 → 0.0581; each column was measured on its own mask (5,431 / 5,441 / 5,440 px, see corrections). Mean outside luminance −2 %.

## What went wrong on the way (kept on record)
1. Test harness bug: the radial combat-circle weight was also applied on the test cards (cracks shown at 35 %, floor-joint moss at 0 %), which made two maps look broken. Fixed (cards show the raw map).
2. First soot version was a symmetric scalloped ring that read as a sun/cog motif. Replaced by an asymmetric smudge; the file name `…SootFloorRing…` is historical.
3. First cracks were 1–2 cm wide (sub-pixel at the gameplay camera) and had colour halos from a global fill colour; rescaled and replaced by alpha-weighted colour dilation (edge halo mean 0.002).
4. Floor-type overlays stretched on stair risers/platform sides; fixed with an up-facing normal mask (the same must be done in Unity).
5. One cleanup shell command (`xargs rm` of redundant renders) hit an approval prompt that timed out; I did not retry it or re-route the deletion. The script now writes throwaway renders to the scratch folder, so nothing needed deleting.

## UNVERIFIED (summary)
Everything in Unity (shader, import settings, compression, mip filtering, cost); gating by `Mask.R`/emission; sight-line/silhouette of the proposed props; wall-plume in context; seamlessness is measured by a wrap-line rank test, not by eye on a Unity floor; the 13 PNGs come from a custom PNG writer (standard 8-bit, no colour chunks) and load correctly in Blender only.

## Disk footprint (untracked, inside `Art/`)
`vf_handoff` is 316 MB: `verify_b/` 158 MB and `bake_out_b/` 53 MB are floor-part verification intermediates (re-creatable with `scripts/04_verify_assets.py`); `renders/` 47 MB, `contact/` 31 MB, working `.blend` 18 MB, `textures/` 9.8 MB. I have not deleted anything; tell me if you want `verify_b/` and `bake_out_b/` pruned.

## Texture SHA-256
| File | Size | Bytes | SHA-256 |
|---|---|---|---|
| `textures/VF_Floor_MacroValue_2048.png` | 2048×2048×1 | 1.30 MB | `c0274ee3f672812ed8ffafa6674e614c9ee3346f33cebe0425212a6ef8169eb1` |
| `textures/VF_Floor_MacroValue_NoDamp_2048.png` | 2048×2048×1 | 1.39 MB | `62a6f41fd5c826156e70f28fdff6cd3d6043209a8247efe4f1e196fe3f15f206` |
| `textures/VF_Floor_MacroTint_1024.png` | 1024×1024×3 | 0.64 MB | `2a8b0006131e88a2b1bfd5a7bfcff776e252c9bf9a8fe98a01321efc5f004396` |
| `textures/VF_Floor_Cracks_2048.png` | 2048×2048×4 | 2.44 MB | `54e56b6da7f115469a9f4b177d601d2c8f4c77276d3a986aa8b231f5a8cf952f` |
| `textures/VF_Floor_Wear_1024.png` | 1024×1024×4 | 0.83 MB | `a60c5e6b63ddae865f2907f839d8c2be7b376307821ff45d9d25bb1a0d34ada7` |
| `textures/VF_Floor_ChippedEdges_1024.png` | 1024×1024×4 | 0.50 MB | `1aad8e5657b7fb7f91cda6afba3f2b2161f8bee10801c47fa51eac4d8a8d9746` |
| `textures/VF_Wall_RainStreaks_1024.png` | 1024×1024×4 | 0.24 MB | `2df3b96922db9badd3a7607a3a620f94c1076f2b126d27a498eac3bd54a2be4f` |
| `textures/VF_Weather_Salt_1024.png` | 1024×1024×4 | 0.65 MB | `7e54e3b8a6446083cc3491137327cd364c593d1366ef1acd69f5bc8eb55a5e4a` |
| `textures/VF_Weather_Moss_1024.png` | 1024×1024×4 | 0.69 MB | `a8d7d268a48848bb6b3fd2a57a8e21d349d345c37d916d5799a2eba6f4d3207b` |
| `textures/VF_Weather_MossWallBase_1024.png` | 1024×1024×4 | 0.47 MB | `db2f5d3cc706582e4dcc14803af2c19b10bee7e9d503b696f3dcdcceac1c1041` |
| `textures/VF_Weather_MossFloorJoints_1024.png` | 1024×1024×4 | 0.42 MB | `8efcf5dad049bdca234fe958f8560ef45a6689d4bd295795670577993a4baa23` |
| `textures/VF_Weather_SootFloorRing_1024.png` | 1024×1024×4 | 0.50 MB | `8ef890f1d538b3115b7696b926ea6530f6f5fdf9bd7a9d5a2c2bcf50db176e86` |
| `textures/VF_Weather_SootWallPlume_512x1024.png` | 512×1024×4 | 0.16 MB | `31e4c462abaae177ddbe54f2ebc48c7ed13c187fa684422e1fb7192e2834a25d` |

## Corrections after QA review (each item says what changed)
1. **Saturation figure.** The earlier "max saturation 0.21" was a **method error of mine**: `scripts/11_texture_qa.py` read Blender `image.pixels` of the sRGB PNGs, assumed they were linear and applied the sRGB transfer function again, so values were double-encoded (that also made the printed mean hexes too light, e.g. moss `#939A7D`). I re-measured from the PNG bytes (`scripts/16_color_audit.py` → `evidence/16_color_audit.json`, HSV s = (max−min)/max on the stored sRGB bytes, visible texels = alpha > 0.02). Per-map maxima: cracks 0.26, wear 0.35, chipped edges 0.38, rain streaks 0.36, salt 0.19, moss ×3 **0.40**, soot 0.23 / 0.29 (QA's 0.19–0.26 / ~0.40 / 0.37 / 0.36 reproduce). The 0.21 is removed from the palette note and replaced with these figures; the moss palette hex `#3A4228` (saturation 0.39) was always correct. `evidence/11_texture_qa.json` still contains the old saturation/hue/hex fields; they are **superseded** (I did not edit evidence files). Its cyan counts were re-checked with the new measurement and still give 0.
2. **Hue range.** "Every colour map has hue 30–77°" was false twice: (a) `VF_Floor_MacroTint_1024` is a multiplier map (raw hue 0–300° over near-neutral texels; cool multiplier 229°); (b) the moss maps reach **78.5°** (72.7–78.5°), so 77° was also wrong at the top. Corrected statement is in the palette note. The no-cyan claim (145–215°, saturation > 0.06) holds: 0 texels for every colour map and 0 for MacroTint applied to neutral stone (QA's finding about the tint confirmed, and its effect on stone is near-neutral at the cool end).
3. **Prop spacing.** The "≥ 2.2 m from every existing piece" statement holds for the **six non-banner props** only (minimum 2.24 m: Rubble_B at (−17, 3) to Pillar_A; next 2.51 m, 2.75 m, 3.35 m, 4.11 m ×2). The two Banner_A placements are wall-mounted: **1.17 m** from Wall_B / Wall_A by design, and banner #4 (−11.0, 19.4) is **2.0 m** from the existing Banner_A at (−9.0, 19.4). Also found while re-checking: the closest pair of *proposed* props is brazier R and the fallen drum, **1.8 m** apart (footprints about 1.05 m and 1.5 × 1.4 m, so tight but not overlapping); I have not changed any placement. `VF_PROP_PLACEMENTS.md` line 18 still carries the shorter wording ("banners excluded: they sit on walls"); I left that file untouched because the instruction was to edit only the two reports.
4. **Telegraph pixel counts.** "the same 5,431 px" was wrong. Each column was computed on its **own** mask (pixels where the telegraph raises luminance by > 0.004): before 5,431 px, after at default opacity 5,441 px, after at k 1.0 5,440 px. Cross-check on the fixed 5,431 px mask: lift 0.1598 (default) and 0.1608 (k 1.0), floor std 0.0581 / 0.0578 (unchanged). The lift and std figures quoted in the tables are the own-mask values.
5. **Single-zone wording.** True for **6 of 8** floor parts (Floor_A–D, Platform_A, Stairs_A: 100 % `StoneWarm`). FloorBorder_Straight_A (6,816 stone / 652 bronze / 76 gold faces) and FloorBorder_Corner_A (7,392 / 1,024 / 106) carry bronze and gold inlays. The report row and `VF_PIPELINE_ANSWER.md` now say so; the recommendation is unchanged.

**Files changed for these corrections:** `VF_HANDOFF_REPORT.md`, `VF_PALETTE_USAGE_NOTE.md`, and `VF_PIPELINE_ANSWER.md` (the last only for items 4 and 5, because the "same 5,431 px" wording and the single-zone heading live there and you asked for it to be explicit). New files: `scripts/16_color_audit.py`, `evidence/16_color_audit.json`, `evidence/16_color_audit.log`, `evidence/checksums_after_corrections.txt`. `VF_MANIFEST.json` and `SHA256SUMS.txt` were regenerated because the edited files' hashes changed. Textures were not touched (all 13 SHA-256 unchanged); no intermediates deleted.

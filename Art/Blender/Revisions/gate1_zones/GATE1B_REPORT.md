# Gate 1b — Altar_A, Pillar_C, Banner_A (zone-aware bake, independent evidence)

Same separate working copy (`TempleEnvironmentKit_gate1_zones.blend`, md5 unchanged: `875075a5…`). Method was stated **before** the runs in `GATE1B_METHOD.md`.
No motif removal, no central-structure choice, no arch change, no remodelling, no Unity, no commit/stage/promotion, no LFS. Production `.blend` NOT migrated.

## Verdicts
| Asset | Verdict | Basis |
|---|---|---|
| **Banner_A** (bronze / gold / crimson; non-lathe) | **PASS** | zone MD5 `b71abc1f…` identical at 6 points; texel-level shipped-class agreement **100 %** (1.02 M texels); re-bake vs shipped mean |Δ| ≤ 0.0014 in every zone; FBX polys + extents identical to shipped |
| **Pillar_C** (stone / bronze coil; lathe-built) | **PASS, with one unexplained residual** | MD5 `05b773f1…` identical at 6 points; texel-level **100 %** (2.78 M texels); mean |Δ| ≤ 0.0007; FBX identical. Per-face (centroid) agreement 97.5 %: 497 of the 612 disagreements are explained, **115 are not** |
| **Altar_A** (stone / bronze / gold / crimson / ember; lathe-built) | **PASS for what a texture can show; UNVERIFIED for sub-9 px² faces** | MD5 `feb8d4d1…` identical at 6 points; texel-level **100 %** (2.41 M texels, all 5 zones); mean |Δ| ≤ 0.0007 per zone and map; FBX identical. 40,249 of 79,542 faces are < 9 px², so only the texel-level result covers them |
Earlier (Gate 1): Brazier_A PASS, Arch_A_PierL PASS (bake/FBX), 21 other parts migration + reopen only.

## Evidence (all under `evidence/`)
- `05_verify_{Banner_A,Pillar_C,Altar_A}.json`: zone MD5 at **reopen → restore → bake → material swap → save → reopen**, slots, per-zone face counts, FBX file-level compare, texel-raster coverage.
- `06_compare_{…}.json`: per-zone region diffs, outlier pixel/face locations, classification from the shipped maps, texel-level agreement.
- `07_optional_checks.json`, `checksums_gate1b_{before,after}.txt`.

### Independent method (not derived from a rebuild)
Bake ran on the **saved** mesh + saved UVs. `zone_id` rasterised through those UVs by a margin-0 Cycles bake of the attribute (texel-level; each texel has exactly one owning zone), then compared with the **shipped Staging textures** and with the re-bake.

### Per-zone baked metallic means (texel raster; shipped vs re-bake)
| Asset | Zone | Faces | Texels | Metallic shipped | Metallic re-bake | Albedo R/(G+B) p50 |
|---|---|---|---|---|---|---|
| Banner_A | Bronze | 916 | 54,826 | 0.904 | 0.904 | 0.91 |
| Banner_A | Gold | 652 | 43,916 | 1.000 | 1.000 | 0.86 |
| Banner_A | Crimson | 4,206 | 917,715 | 0.000 | 0.000 | **2.00** |
| Pillar_C | Stone | 24,276 | 2,687,816 | 0.000 | 0.000 | 0.63 |
| Pillar_C | Bronze | 2,252 | 93,860 | 0.752 | 0.752 | 0.90 |
| Altar_A | Stone | 60,208 | 2,058,486 | 0.000 | 0.000 | 0.64 |
| Altar_A | Bronze | 5,024 | 108,882 | 0.741 | 0.741 | 0.89 |
| Altar_A | Gold | 2,032 | 140,383 | 1.000 | 1.000 | 0.91 |
| Altar_A | Crimson | 11,860 | 89,188 | 0.000 | 0.000 | **1.91** |
| Altar_A | Ember | 418 | 13,560 | 0.000 | 0.000 | 1.55 (emission lit) |

### Re-bake vs shipped (global mean |Δ|; texels > 0.1; max)
Banner_A: Base 0.00012 (139; 0.25), Normal 0.00066 (0), Mask 0.00030 (76; 0.45). Pillar_C: Base 0.00009 (53; 0.20), Normal 0.00091 (0), Mask 0.00058 (91; 0.50). Altar_A: Base 0.00026 (121; 0.28), Normal 0.00052 (0), Mask 0.00051 (24; 0.28), Emission 0.00000 (0; 0.004).
Outliers by zone region: Banner Mask 76/76 in Bronze; Pillar Mask 71 of 91 on island edges, Base 48 of 53 edges; Altar Base 96 of 121 edges, Gold 18, Stone 7. Pixel/face locations of the top outliers per map are in `06_compare_*.json` (`global_diff.*.top_outliers`).

### FBX (exact 05_export.py settings → `bake_out_b/Models/`)
All three: polys equal to the shipped FBX (5,774 / 26,528 / 79,542), vertex extents equal, UpAxis/UnitScale equal, identity transform, material + texture names equal, textures resolve, `zone_id` absent from FBX (by design).

## A failure in my own method (kept on record)
The classification thresholds in `GATE1B_METHOD.md` were fixed a priori, and the **crimson cut-off (R/(G+B) > 2.5) was wrong**: it came from hex-palette arithmetic, not from the loaded textures. Result with the a-priori threshold: crimson recognised 0 % on Banner_A (texel-level agreement 9.7 %) and Altar_A (96.3 %); Pillar_C unaffected (no crimson). Measured crimson regions sit at **1.85–2.02** vs stone ≤ 0.66 and metal ≤ 0.95, so any cut-off in (1.0, 1.8) gives the same result. I re-ran with 1.4 (gap midpoint) and **label it post-hoc**. The zone mapping was not at fault: region-level metallic means and diffs were already identical.

## Optional checks
1. **Non-unique-key parts (no bake, no centroid sampling):** PierR (26,304 faces), FloorBorder_Corner (8,522), Platform (25,908), Stairs (11,488) are index-aligned exactly with the rebuild (0 vertex delta); per-index `zone_id` agreement **100 %** on all four. Duplicate-key groups: 1 / 4 / 5 / 1 groups (2–10 faces); **0 groups with conflicting zones**. Also checked: Altar_A 728 groups / 9,849 faces, Span 12, Pillar_A 4 — **0 conflicts** (not index-aligned, so group-consistency only).
2. **21 "unexplained" PierL faces (definition tightened → 27):** 120 margin-10 mismatches; 93 sample a texel covered by another-zone face; the other **27 are all sub-texel faces (0.69–1.75 px²) whose centroid texel is EMPTY at margin 0**, i.e. the earlier mismatch was bake-margin dilation. Face indices, pixel and area for all 27 are in `07_optional_checks.json` (`two_PierL_probe_mismatch.unexplained_faces`). At margin 0, 891 faces sit on a texel that is not their own; 798 of those texels are empty (sub-texel faces), consistent with the same cause.
3. **Brazier re-bake outliers:** BaseColor 21 texels > 0.1 (13 on edges, 8 in Bronze; max 0.31); Mask 81 (77 Bronze, 4 edge; max 0.25); Normal/Emission none. Top locations are in `07_optional_checks.json`. Probable cause: metallic is baked at 4 samples and island edges are antialiased; **not proven**.

## UNVERIFIED / limits
- Zone assignment of faces < 9 px² (Altar_A 40,249; Pillar_C 1,941; Banner_A 492): no texture can show them; they rest on the geometry match from Gate 1 + the texel-level result.
- Pillar_C: **115 per-face disagreements unexplained** (centroid texel is the face's own zone; likely the 3×3 median reaching a neighbouring island, not tested).
- Cause of the isolated outlier texels (all four assets): sampling noise is likely, not isolated. Cross-machine / cross-GPU determinism not tested.
- The texel-level agreement is "1.0" at 5-decimal rounding (≥ 0.99999), not a literal count of every texel.
- Still never baked or exported in the working copy: Pillar_A/B/D, Arch_A_Span, Arch_A_PierR, Wall_A/B, Stairs_A, Platform_A, Floor tiles/borders, Rubble, ColumnDrum (migrated + reopen-checked only). The 13-part QA pass is QA's, not repeated here.
- Not tested: Unity; modifiers/linked libraries; remodel operators that delete or reorder faces.
- Altar_A has 728 coincident-triangle groups (9,849 faces) and Span 12; zones are consistent inside each group, but whether these are hidden duplicate faces to clean up was **not investigated** (relevant to a later remodel).
- **Production `.blend` not migrated.** Needs Nishant's explicit approval.
- **CORRECTION (Game Director/QA trace):** the two files in `Art/Exports/Environment/Review/` (`REVIEW_ortho11_offset12-18-m12_{dais_altar,player_origin}_cameraUNVERIFIED.png`, 01:31) were **written by this profile's own group-room session** (`local-f3f1bfdb…`, process `proc_acfd365f1181`, background script `rv.py`, temporary camera `tmpcam`), not by another agent. I wrongly reported them as foreign; that session had no memory of this work and never received the Game Director's stop message. They are **Blender layout renders of the production kit, not Unity camera evidence**. Rules now: `Review/` holds only `.gitkeep` until Nishant approves promotion; no further files, copies or renames there; the two PNGs are neither moved nor deleted (Nishant decides; expected destination `Art/Blender/Renders/`). The checksum tracking of 'the original 96 files' stays valid; the two PNGs are not part of that set.
- Unrelated tracked changes in `git status` (Assets/Characters/*/Materials/*.mat, ProjectSettings/…/EditorPipelineConfig.json) were not made by this task; `Art/README.md` shows modified from my Milestone-1 note.

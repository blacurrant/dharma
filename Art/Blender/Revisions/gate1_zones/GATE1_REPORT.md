# Gate 1 — Persistent material zones (M6): pipeline repair

**Scope kept:** pipeline repair only. No motif removal, no central-structure choice, no arch-dimension change, no remodelling, no bulk assets, no commit/stage/push/Review promotion, no LFS work.
**Continues from:** `Art/Blender/Revisions/v2_study/ART_DIRECTION_AUDIT.md` item **M6** (and finding 7).
**All outputs:** `Art/Blender/Revisions/gate1_zones/` (isolated; `scripts/` here are *copies* of `kitlib.py`/`assets.py` plus new gate-1 scripts).

## The defect (reproduced)
After the bake stage the saved meshes had one slot (`MI_Temple_*`) and `material_index` = 0 for 100 % of faces, e.g. Brazier_A `{0: 6082}`. The stone/bronze/gold/crimson/ember zones were gone, so no material revision could be rebaked from the saved `.blend`.

## The fix
- `kitlib.B.to_object` now writes **`zone_id`**: FACE-domain INT attribute holding the *global* zone (0 StoneWarm, 1 StoneCharcoal, 2 Bronze, 3 Gold, 4 CrimsonCloth, 5 EmberAmber), independent of slot order. Legend stored on the scene (`zone_legend`) and each object.
- `kitlib.zone_counts()` and `kitlib.restore_zone_slots()` (rebuilds SRC slots + per-face `material_index` from the attribute, same ordering as the original builder).
- `scripts/02_bake_gate1.py`: the old "not on source materials; rerun stage 1" abort is replaced by `restore_zone_slots`; asserts the zone MD5 is unchanged before bake, after bake and after the material swap; only touches `--only` parts; all output under `bake_out/`.
- `scripts/00_migrate_zones.py`: one-shot migration of the **already-saved** kit meshes in the working copy (23 parts).

## Evidence
| Check | Result | Evidence file |
|---|---|---|
| Before dump | every part: no `zone_id`; `material_index` single value | `evidence/00_migration.json` (`before`) |
| Migration | **23/23** parts transferred; 0 ambiguous faces; zone→SRC-material cross-check passed per face | `00_migration.json` (`transfer`, `after`) |
| Reopen, whole kit (fresh process) | **23/23** have `zone_id`, face sums equal polygon counts | `04_final_checks.json` (`R_*`) |
| Brazier_A (stone / bronze / ember): reopen → restore → bake → material swap → save → reopen | zone MD5 `d6c25926…` **identical at all 5 points**; counts {Stone 1296, Bronze 3488, Ember 1298} | `01_verify_Brazier_A.json` |
| Arch_A_PierL (stone / charcoal / bronze / gold) | zone MD5 `8de9b5e3…` identical at all points; counts {25760, 512, 324, 60} | `01_verify_Arch_A_PierL.json` |
| Restored slots vs a fresh builder rebuild (matched by geometry) | 6082/6082 and 26656/26656 faces agree | same |
| Bake outputs reflect the zones | Brazier: metallic mean Stone 0.00 / **Bronze 0.80** / Ember 0.00, roughness 0.73/0.50/0.70; PierL: Gold metallic 0.98, Bronze 0.48, Stone 0.00 | `C_bake.per_zone_from_baked_maps` |
| `zone_id` read inside Cycles (Attribute node → baked → compared to the array) | Brazier **6082/6082** exact; PierL 26536/26656 (120 faces differ, see below) | `C_zone_attribute_baked_through_shader`, `02_diagnostics.json` |
| Zone-aware bake script (Brazier_A) vs the **shipped** Staging textures | mean abs diff: BaseColor 0.00006, Normal 0.00025, Mask 0.00015, Emission 0.0; p99 ≤ 0.004 | `04_final_checks.json` (`T_*`) |
| FBX, exact `05_export.py` settings, from the baked result | geometry extents + 6082 polys identical to the shipped `ENV_Temple_Brazier_A.fbx`; UpAxis 1, UnitScale 100; textures resolve | `04_final_checks.json` (`X_*`) |
| Protected sets (blend, exports tree, original scripts, v2_study tree, texture sources, backup tree) | 6/6 checksums identical before/after | `evidence/checksums_{before,after}.txt` |

## Findings that matter
1. **The builders are not index-order deterministic.** The lathe-built pieces (Pillar A–D, Altar_A, Arch_A_Span) rebuild with the same vertices but a *different vertex/loop order every run* (two rebuilds in the same process differ). Therefore: (a) the migration matches faces by geometry (rounded triangle vertices), not by index; (b) **re-running stage 1 can reorder those meshes and de-sync their UV islands from existing textures.** Treat the saved `.blend` + `zone_id` as the source of truth, and always re-bake after a re-run of stage 1. For those 6 parts, the rebuilt UVs differ from the saved UVs (Pillar_D is the exception).
2. **FBX does not carry `zone_id`** (tested: not in the file, not after import). That is by design here: zones are source-side authoring data and reach Unity through the baked Mask/BaseColor maps. The shipped FBX structure is unchanged.
3. **Optional opt-in** (not enabled): zone as a CORNER colour attribute exported with `colors_type='SRGB'` round-trips exactly at histogram level on both assets; `'LINEAR'` does **not** (importer applies an sRGB→linear transform; 0.2/0.4/0.6 come back as 0.03/0.13/0.32).

## UNVERIFIED / limits
- **Bake + FBX evidence covers 2 assets (Arch_A_PierL fully through verify; Brazier_A also through the gate-1 bake script and texture comparison).** The other 21 parts were migrated and reopen-checked only; the other 4-zone/5-zone combos (Altar_A with crimson, Banner_A) were **not baked or exported**.
- Brazier re-bake vs shipped textures: tiny mean difference, but isolated pixels differ (BaseColor max 0.31, Mask max 0.25); cause not investigated (sampling noise at island edges is likely, not proven). Cycles samples/GPU nondeterminism not isolated.
- 120/26656 PierL faces read a different zone through the baked probe. 99 of them sample a texel shared with another face of that zone (median face UV area 1.4 px vs 18 px overall); the other 21 are **not individually explained** (bake margin bleed is the likely cause, unproven). The attribute itself was intact (MD5 equal), so this is a sampling limit of my probe.
- The 6 lathe-built pieces: zones were attached by geometry match to a rebuild; UVs of those saved meshes are not the same as a fresh rebuild's, so a fresh rebuild is not a drop-in replacement.
- Not tested in Unity: nothing here touches Unity. Not tested: Blender 5.x behaviour of the attribute across a *linked/appended* library workflow; modifiers; any future remodel operator that deletes/reorders faces (attribute follows face data in Blender operators, not yet exercised on these meshes).
- The migrated working copy was saved once by a script; the production `.blend` was **not** migrated (still has no `zone_id`). Promoting the fix to the production source requires an explicit go-ahead.
- Out of this gate's scope and unchanged: sun/ring motif, central structure, arch opening (4.19 m measured on the mesh vs the old 5 m note: still undecided), Unity scenes/scripts/settings, backup directory.
- Unrelated tracked changes appear in `git status` (`Assets/Characters/*/Materials/*.mat`, `ProjectSettings/...EditorPipelineConfig.json`); **not made by this task**. `Art/README.md` shows modified from my earlier Milestone-1 conventions note, not from this gate.

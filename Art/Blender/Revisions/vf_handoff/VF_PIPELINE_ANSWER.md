# Pipeline answer: can zone_id / baked maps deliver floor variation?

**Recommendation: keep variation as Unity-side, world-space overlays on top of the baked per-part maps. Do not try to carry floor variation in `zone_id` or in the bake.** Keep the zone pipeline for what it is verified to do: classify material zones (metal / emissive / stone) that survive bake, save/reopen and FBX.

## Evidence (all in `evidence/`, working copy `TempleEnvironmentKit_vf_working.blend`, production untouched)

**1. Six of the eight floor parts carry no zone information to vary; the two border pieces carry only metal inlays.** Floor_A/B/C/D are single-zone: every face is `StoneWarm` (1,824 / 1,272 / 1,760 / 1,632 faces). Platform_A (25,908) and Stairs_A (11,488) are also 100 % `StoneWarm`. Only the two border pieces have more: FloorBorder_Straight_A (6,816 stone / 652 bronze / 76 gold) and FloorBorder_Corner_A (7,392 / 1,024 / 106). `zone_id` therefore cannot express tint, wear or crack variation on the floor; it only marks the inlays.

**2. The pipeline itself is reliable on these 8 floor parts (Gate-1b bar, `05_verify_*.json`, `06_compare_*.json`).** Zone MD5 identical across reopen, restore, bake, material swap, save and reopen on all 8; saved-mesh/saved-UV bake; FBX (05_export settings) polys, extents, up-axis, unit scale, materials and texture names identical to the shipped files; `zone_id` absent from the FBX by design. Texel-level class agreement 100 % on all 8 (0.42 M – 3.0 M texels each). Re-bake vs shipped mean |Δ|: BaseColor ≤ 0.00019, Normal ≤ 0.0011, Mask ≤ 0.00091. Baked metallic means equal shipped: stone 0.000, bronze 0.784 (Corner) / 0.800 (Straight), gold 1.000. Isolated texels above 0.1: BaseColor ≤ 22 (Stairs), Mask ≤ 119 (Corner), same character as Gate 1b (island edges / bronze).

**3. Baked variation is per mesh, so it repeats identically on every instance.** The 400 floor instances use 6 baked sets: Floor_A ×102, D ×79, C ×72, B ×71, Straight border ×72, Corner ×4. The floor tile centres all sit on the odd-metre grid (324 of 324). More variants only dilute the repetition linearly (cost: one bake plus one FBX each; the full verify run for a floor part took 27–90 s, bake share not isolated), they cannot create 40 m-scale patterning. Per-instance vertex colour would need 400 unique meshes (rejected on principle; **not measured**).

**4. World-space overlays work on the real kit materials, with no UV or mesh change (Blender test, `scripts/13_courtyard_before_after.py`).** The overlay nodes (`scripts/vf_nodes.py`) were inserted into the 6 floor, 2 wall and 2 dais materials in memory; the .blend was not saved. Plan view luminance, floor only (`evidence/13_courtyard*.json`):

| | before | after, default (k value .75 / tint .60) | after, k 1.0 / 1.0 |
|---|---|---|---|
| tile-mean luminance CV, inside r < 10 m | 0.020 | 0.024 | 0.027 |
| tile-mean luminance CV, outside r > 12 m | 0.077 | 0.095 | 0.107 |
| luminance std outside (12.5–17 m) | 0.0631 | 0.0745 | 0.0774 |
| luminance std inside (r < 9.5 m) | 0.0501 | 0.0527 | 0.0531 |
| telegraph lift, gameplay camera (own mask per column: 5,431 / 5,441 / 5,440 px; on the fixed 5,431 px mask: 0.1571 / 0.1598 / 0.1608) | 0.1571 | 0.1596 | 0.1605 |
| floor luminance std under the telegraph footprint | 0.0580 | 0.0581 | 0.0578 |

So the variation adds 23 % (k .75) to 39 % (k 1.0) tile-to-tile spread outside the circle. Inside the circle the luminance std rises 5 % / 6 % and the tile-mean CV by +0.004 / +0.007 absolute (still ≤ 0.027, against 0.095–0.107 outside); the std under the telegraph footprint changes by ≤ 0.4 % and the telegraph lift by +0.002 / +0.003. One side-effect: mean outside luminance drops 2 % (0.4516 → 0.4427) because cracks/tint are darker than the base; compensate in grading if needed.

## What the pipeline should still do
Use the baked **Mask.R (metallic)** as a free zone gate: stone 0, bronze ≈ 0.78–0.80, gold 1.0 (Gate 1b + this run). Overlays multiply their opacity by `(1 - Mask.R)` so cracks/moss don't land on inlays or the bronze coil. **Recommended; not tested in Blender or Unity.**

## UNVERIFIED
- Any Unity result: shader implementation, URP/HDRP choice, sampler/compression/mip behaviour, GPU cost of 4–6 extra samples on the floor and 3 on walls, light/post-processing interaction. All numbers above are Blender (EEVEE, Standard view).
- Overlay gating by `Mask.R` and by emission (not applied in the test).
- The production `.blend` has no `zone_id` (not migrated; needs Nishant's approval). Nothing here depends on it, because the overlays are world-space.
- Platform/Stairs got value, tint, cracks and wear only (their tiles are not on the 2 m grid, so no chips/joint moss).
- Floor tiles under the platform, border pieces' metal inlays and walls beyond the left wall were not inspected close up; Wall_A/B were patched but only one wall stretch was viewed.
- The baked-variant alternative (more bakes) was reasoned, not built.

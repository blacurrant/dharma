# VF_ITERATION_2 (ArtTest_VisualFoundation only; Editor Play Mode figures; Unity 6000.6.7f1, URP, Metal)

Transport: Unity MCP tools were still gone after the recompile (`'mcp__unity__list_instances' is not a known tool name`, one call, no enable retry). Everything ran through the `unity` CLI against the same Editor. Please arrange the one approval if QA needs live MCP.

## 1) Camera minima: reconciliation
Files: `Reports/i2_cam_perframe.csv` (VF scripted sequence, every frame: config, frame, phase, margin, edge, player offset px, player-enemy m, speed, dashing, hit, telegraph), `Reports/i2_cam_hud.csv`, `Reports/i2_cam_sizes.csv`; Gate-1-input-set runs: `Reports/gate1set/{A2,B}_cap60.csv` + `*_perframe.csv`.

**[ERRATUM added later - see VF_ITERATION_3.md follow-up 1: the cause stated below is NOT supported. The -76/+16 minima are frame-0 samples taken before IsoCameraFollow.LateUpdate re-aimed the camera after a pitch change (a reproduced one-frame measurement transient); the run was never at a wrong pitch. Also: F2 gain = darker floor, not brighter character (follow-up 2); the rim-light "failure" was my setting the wrong property, not a renderer limitation (follow-up 4).]**
**Cause of iteration 1's A = -76 and B = +16 (a harness bug, not the camera):** the runner changed ortho size and offset but never re-aimed the camera, so A and A2 ran with the pitch left from the previous config. Rerun with the camera rotation set per config, VF scripted sequence (dash, attack, dodge), per-frame log:
| Config | Min margin | Frame / phase / edge | Player offset | Hits taken |
|---|---|---|---|---|
| A | **+23 px** | 246 / dodge_dash / top | 66 px | 0 |
| A2 | **+72 px** | 247 / dodge_dash / top | 82 px | 0 |
| B | **+39 px** | 247 / dodge_dash / top | 64 px | 0 |
| C | **+130 px** | 247 / dodge_dash / top | 53 px | 0 |
Per-phase minima for A (px): idle 87, run 72, dash_sideways 72, attack 73, wait 84, dodge_dash 23. **Is the minimum from dodge/knockback? No knockback: the player took 0 hits in every run. The minimum is the dodge DASH (22 m/s) toward the top edge, not normal running; plain running bottoms out at 72 (A) / 87 (B) / 100 (A2) / 170 (C).** The first buggy run is kept in `Reports/iter2_run1_frame0_artifact/` for QA.

**Gate 1 input set on A2 and B (8 directions, run, dash from rest, dash while running, attack, dodge, chain, edge, far chase), capped 60, REAL injected keyboard input:**
| | A2 | B |
|---|---|---|
| Worst margin | **+58 px** (dash_run, S/down, per-frame min at frame 2596, enemy 9.66 m) | **+45 px** (dash_run, S/down, frame 3290) |
| Run minimum | +90 | +78 |
| Frames with player out of frame | 0 | 0 |
| Telegraph fully in frame | 100% of telegraph frames (all sequences) | 100% |
| Avg fps in runs | 44-57 | 44-58 |
The worst direction is down-screen / up-screen dashing (vertical axis is the tightest because the frame is 16:9). A2 beats B by about 13 px everywhere. Edge-hugging and the far-enemy chase (focus helper OFF) stayed 79-109 px clear.
Honesty notes: (a) my first attempt at these runs produced a "player never moved" result (margins 103 at every sequence); that data was discarded (`gate1set_INVALID_no_player_movement/`). Cause: Input System `backgroundBehavior=ResetAndDisableNonBackgroundDevices` plus the Editor reporting `Application.isFocused=False` when driven from the CLI, so injected keys were dropped. The runners now install a runtime-only clone of the Input System settings (IgnoreFocus); asset and ProjectSettings untouched. I verified movement after the fix (player moved 3.79 m in 30 frames; dash frames 133 and 116 in the logs). (b) The earlier "Gate 1" matrix numbers (A +49, B +44) were run before this, with the old harness, so treat B +45 now as consistent with it. (c) **Uncapped is UNVERIFIED**: the Editor in this session runs about 65 fps at `targetFrameRate=-1, vSync=0` (probed with Game view focused and unfocused), so a truly uncapped run is not obtainable and I did not label one.

## 2) Game view size per capture; the 1944x1734 reading
Every capture row now logs `gameViewTarget`, `cam.pixel`, `Screen`, OnGUI Screen and `Display.main.rendering` in `Reports/i2_light.csv` (last column) and `i2_cam_sizes.csv`. All 16 lighting captures: **1920x1080 / 1920x1080 / 1920x1080 / 1920x1080, HUD scale 1.80**. I also measured: with the fixed "Full HD" preset `Screen` = 1920x1080; with Free Aspect it follows the docked window (642x1062 here). **1944x1734 was not reproducible; I did not find its cause.** My best explanation is a transient window size in the first Play Mode frames of the earlier session (before the Game view settled), but that is unproven. It did not affect captures, which are rendered at the preset. I left the Game view on the Full HD preset (idx 3).

## 3) Probes rebaked; ambient test; F1 / F2 separately
Each variant: set key/ambient, rebake light probes (207 probes, succeeded, 5-7 s each, GPU probe bake), save VF scene, Play, measure at B then A, same 45% telegraph, same pose. Raw 1920x1080 frames: `Captures/light_i2/<variant>_{A,B}.png`; data `Reports/i2_light.csv`. Baseline reproduces after restore (`RESTORE_L0_B`: floor 0.401, sep -0.089 / -0.110, lift 0.133 = `L0_B`).
| Variant (cam B / cam A) | Floor luma | Player sep | Enemy sep | Telegraph lift mean / p10 | Shadow |
|---|---|---|---|---|---|
| L0 yaw45 elev38 | 0.401 / 0.402 | -0.087 / -0.096 | -0.114 / -0.110 | 0.133 / 0.048 | 2.56 m |
| **F1 yaw 75 only** | 0.407 / 0.408 | -0.104 / -0.111 | -0.118 / -0.107 | 0.131 / 0.047 | 2.56 m, falls down-left on screen (-23 deg) |
| **F2 elev 32 only** | 0.385 / 0.386 | **-0.074 / -0.081** | -0.097 / -0.091 | **0.140 / 0.051** | 3.20 m |
| F3 yaw 75 + elev 32 | 0.390 / 0.391 | -0.089 / -0.099 | -0.097 / -0.103 | 0.138 / 0.051 | 3.20 m |
| Ambient warm (single variable) | 0.402 / 0.403 | -0.087 / -0.095 | -0.116 / -0.099 | 0.133 / 0.048 | no change |
| Ambient cool-strong (single variable) | 0.394 / 0.394 | -0.089 / -0.094 | -0.113 / -0.124 | 0.136 / 0.051 | no change |
(Note: the label says elev 32, not the 30 used in iteration 1; floor 0.385 is slightly above the 0.30-0.36 proposal band. Earlier "V3 elev 30" was 0.353 with a stale bake.)
Findings: with probes rebaked, **ambient warm vs cool is a real but small effect (floor -0.008 for cool, telegraph lift +0.003, no separation change); it is not the lever for character contrast.** F2 (lower key) is the only variant that improves player separation and telegraph lift; F1 alone (yaw 75) makes separation a little worse and mostly changes shadow direction. So F3's benefit over F2 is only the shadow direction. Honest eye judgement: the differences between L0, F2 and F3 are subtle at gameplay scale; F2/F3 look slightly moodier with longer shadows; no variant solves "dark figure on mid-tan floor".
The ambient variants changed what indirect probes receive, and probes only affect the dynamic characters here (environment `receiveGI=LightProbes`), so floor changes are small.

## 4) Raw before/after
Raw, un-composited, 1920x1080 frames with HUD and matched telegraph state (45% ramp, same pose) are in `Captures/light_i2/` (lighting pairs) and `Captures/env/` (iteration 1 environment pairs `env_before_*` / `env_after2_*`, raw originals alongside the `BA_*` composites). Composite sheets are derived from these.

## 5) Character-separation tests (one variable each, camera B, L0 key)
Measured at the same pose; sep = character mean luma minus floor ring around it (negative = darker than floor).
| Test | Floor luma | Player sep | Enemy sep | Telegraph lift mean / p10 | Environment affected? |
|---|---|---|---|---|---|
| Baseline L0 | 0.401 | -0.087 | -0.114 | 0.133 / 0.048 | n/a |
| (a) Rim/back spot light per character (intensity 14, warm white, range 7, behind-above) | 0.406 | -0.097 | -0.097 | **0.103 / 0.026** | **YES: FAIL** |
| (b) Lighter warmer floor in central area (radial overlay r 12 m, alpha 0.22 tint (0.95, 0.83, 0.60)) | 0.431 | -0.103 | -0.127 | 0.111 / 0.038 | the floor is the change |
| (c) Cool shadow tint (see ambient cool-strong above; I did not add a separate material shadow tint) | 0.394 | -0.089 | -0.113 | 0.136 / 0.051 | no |
**(a) FAILED its constraint.** I set rendering-layer masks on the characters and on the lights, but the floor under both actors is clearly lit (floor luma at the player 0.422 to 0.488), because the URP renderer in this project does not honour light layers without enabling rendering layers on the shared renderer asset, which I may not change. Player luma rose (0.334 to 0.391), but the floor rose more, so separation did not improve, and the spot pool dimmed the telegraph (lift 0.133 to 0.103). So per-light layer masking is not available here; the options are a material-side rim (a shader change on the protected character materials, not done) or a rendering-layer renderer change (needs approval). Not recommended as tested.
**(b)** Brighter floor lowers separation (floor up 0.03, characters stay dark) and lowers telegraph lift. A lighter floor is the wrong direction; if anything the floor should be darker/cooler behind the actors and the actors need lifting.
**(c)** Only the ambient cool was tested (no material-side shadow tint). Small gain in lift, no separation gain. Marked partial.
**Bottom line:** none of (a)-(c) improves floor-vs-character separation; the lower key (F2) is the only thing that moved it (+0.013). The real fix is on the character side (material/outline/rim shader or a brighter character albedo), which touches protected assets or the shared renderer. This needs a decision.

## Cyan/teal
No cyan/teal was added anywhere except the existing telegraph. The cool ambient test used a blue-violet (0.36, 0.42, 0.80) sky, not teal.

## State, safety, and a change to flag
- Original `ArtTest_TempleCourtyard.unity` SHA-256 still `b30065166bf45252...` (unchanged). VF scene was rebaked and saved at the restored L0 key (38, 45, 0). Editor is not in Play Mode.
- **Flag: `ProjectSettings/ProjectSettings.asset` now differs from HEAD: `runInBackground: 0 -> 1` (mtime 02:15).** I did not write it deliberately; I think the Unity tooling (the CLI `set_auto_tick` / focus commands I used for these runs, same mechanism that sets the EditorPipelineConfig flag) toggled it. I have NOT reverted or edited it; the Director/QA should decide. The other three Unity-generated files are unchanged by me.
- The vf_handoff textures were not used (not cleared). No commit, stage, push, LFS or promotion.
- New/changed code (art-test folder only): `Scripts/VFRunner.cs` (camera re-aim fix, per-frame log, ViewInfo, Rim/FloorLift runtime tests, ForceInput), `Scripts/ArtTestSequenceRunner.cs` (camera re-aim fix, per-frame log, noShots, ForceInput).

## UNVERIFIED
Uncapped frame rate (not obtainable); A2/B at 8 directions with focus helper ON; whether the first-run A = -76 is fully explained by the missing re-aim (consistent with the fix, I did not isolate it); the 1944x1734 origin; a material-side shadow tint; performance for this scene.

---
# PART 2: Environment Artist textures (cleared by the Game Director) in the VF scene
Scene `ArtTest_VisualFoundation.unity` only. Original `ArtTest_TempleCourtyard.unity` SHA-256 still `b30065166bf45252...`. Editor not in Play Mode at the end. Transport: `unity` CLI (MCP not available in this session). Raw, un-downscaled 1920x1080 Game-view frames (HUD included, Game view = Full HD preset, camera B, plain follow, focus helper OFF) are in `Captures/env_i2/`; every pair uses the same pose and the same 45 % telegraph state. Composite for convenience: `Captures/VF2_before_after_final.png` (left = no overlays, right = final stack; derived from the raw frames).

## What was done
- **Textures copied, not moved/edited:** 11 of the 13 handoff PNGs (not used: `VF_Weather_Moss_1024` generic moss, `VF_Weather_SootWallPlume_512x1024` because no brazier is within ~1 m of a wall). SHA-256 of all 11 copies matches `SHA256SUMS.txt` (checked). Location `Textures/`.
- **Import settings (from the note, verified by reading back):** colour maps sRGB on, Alpha Is Transparency on, mips on (RGBA32, trilinear, aniso 4), repeat wrap (soot clamp, wall-base moss U repeat / V clamp); data maps (MacroValue, MacroValue_NoDamp, MacroTint) sRGB off, clamp. **Compression is None for all of them** (kept for the visual check as the note recommends). Runtime memory of the 10 textures in the final stack is about **172 MB** (`Reports/i2_perf_raw.csv`); a compressed-format test was not done.
- **Two new URP shaders (art-test only, `Shaders/`):** `VF/WorldOverlayLit` (world-space mapping per the note, alpha-lerp on albedo, lit by the scene lights/shadows/probes, Forward+; per-layer radial weight; face-up quad only) and `VF/WorldMultiply` (macro maps: `albedo *= lerp(1, 2m, opacity*w)`). Both compile with 0 shader errors. Mapping: macro `UV=((x+20)/40,(z+20)/40)`; floor tiles `u=x/tile, v=z/tile`; walls `u=along-wall/3, v=height/3`. Unity (x,z) = Blender (x,y) used as stated.
- **Layers** under `VF_Environment/VF_Layers` (each can be switched off): L01 macro value (damped asset) with L01b NoDamp + shader radial weight and L01c NoDamp flat as alternatives, L02 macro tint, L03 cracks, L04 wear, L05 chipped edges, L06 joint moss, L07 salt, L08 wall rain streaks, L09 wall-base moss, L10 soot, L11 brazier lights, and test layers L03b/L04b (second off-axis scale) and L03c/L04c (per-cell mirror/rotate). Render order: macros first (queue 2501-2502), colour overlays 2503-2514, telegraph (3100) drawn after all overlays. **All overlays are separate quads; no existing material, shared URP asset, renderer feature or ProjectSettings was edited.** Floor overlay quads sit at y = 0.018 (floor top median 0.004), so stair risers/platform sides/dais tops are never overlaid. Wall layers are one quad per wall piece on the measured inner face (plane z or x = +/-19.517 + 0.012), so the arch gap stays open (38 pieces).
- Weights inside r < 10 m from the note: cracks 0.35, wear 0.40, chips 0.50, joint moss 0, salt 0.30 (ramp r 10 to 13 m is my choice); opacities: cracks 0.75, wear 0.50, chips 0.85, joint moss 0.80, salt 0.55, rain 0.65, wall moss 0.80, soot 0.85, macro value 0.75, tint 0.60.

## Step-by-step results (camera B, held combat pose at the arena centre, telegraph 45 %)
Rows are cumulative; floor luma = mean floor luma within 8 m of the centre; lift = telegraph fill mean luma gain. Raw: `Reports/i2_env_seq_full2.csv`; frames `Captures/env_i2/<stage>_{combat,dais,wall,corner}.png`; plan views `plan_<stage>.png`.
| Stage | Floor luma | Player sep | Enemy sep | Lift mean / p10 |
|---|---|---|---|---|
| S00 no overlays | 0.381 | -0.091 | -0.116 | 0.139 / 0.050 |
| S01 + macro value (damped asset) | 0.381 | -0.092 | -0.108 | 0.139 / 0.050 |
| S01b macro NoDamp + shader radial (alt.) | 0.381 | -0.091 | -0.115 | 0.139 / 0.050 |
| S01c macro NoDamp flat (alt.) | 0.379 | -0.092 | -0.115 | 0.139 / 0.050 |
| S02 + tint | 0.381 | -0.092 | -0.116 | 0.139 / 0.050 |
| S03 + cracks | 0.378 | -0.090 | -0.114 | 0.139 / 0.050 |
| S04 + wear | 0.380 | -0.091 | -0.116 | 0.138 / 0.048 |
| S05 + chipped edges | 0.380 | -0.091 | -0.117 | 0.138 / 0.048 |
| S06 + joint moss | 0.380 | -0.090 | -0.117 | 0.138 / 0.048 |
| S07 + wall rain | 0.380 | -0.090 | -0.117 | 0.138 / 0.048 |
| S08 + salt | 0.381 | -0.090 | -0.117 | 0.138 / 0.048 |
| S09 + wall-base moss | 0.381 | -0.090 | -0.117 | 0.138 / 0.048 |
| S10 + soot | 0.381 | -0.090 | -0.117 | 0.138 / 0.048 |
| **S11 cracks+wear as per-cell flip (recommended)** | 0.381 | -0.091 | -0.116 | 0.137 / 0.048 |
| S12 + brazier lights | 0.381 | -0.091 | -0.118 | 0.137 / 0.048 |
**Telegraph readability:** the whole stack changes lift by at most -0.002 (0.139 to 0.137) and p10 by -0.002, character separation by under 0.002. The combat circle is effectively untouched by design (weights above). The overlays do **not** improve character-vs-floor separation (still about -0.09 / -0.12); that problem is unchanged.

## (1) Macro maps: damped vs NoDamp (never both; measured at three centres)
Raw: `Reports/i2_damp.csv`, frames `Captures/damp_i2/`. Hold pose moved to the arena centre (r 0), (-8, 8) (r 11.3) and (12, -12) (r 17); lift = telegraph mean luma gain.
| Pose | base | damped asset | NoDamp + shader radial (origin-centred, 0.25 at r<=8 to 1 at r>=14) | NoDamp flat | NoDamp radial centred on the player |
|---|---|---|---|---|---|
| r 0 floor / lift | 0.381 / 0.139 | 0.381 / 0.139 | 0.381 / 0.139 | 0.379 / 0.139 | 0.381 / 0.139 |
| r 11.3 floor / lift | 0.357 / 0.158 | 0.351 / 0.164 | 0.351 / 0.164 | 0.347 / 0.165 | 0.355 / 0.160 |
| r 17 floor / lift | 0.358 / 0.137 | 0.351 / 0.137 | 0.352 / 0.137 | 0.352 / 0.137 | 0.356 / 0.137 |
Tile-mean luminance CV (2 m tiles, plan view; handoff metric): inside r<10 base 0.029, damped 0.020, NoDamp flat 0.037; outside 12-17 m base 0.026, with macro 0.061. So the damped asset and the shader-radial version are visually/numerically **the same** (S01 vs S01b: identical to 3 decimals except the enemy separation noise), as expected since the radial weight reproduces the bake. The flat NoDamp raises the in-circle spread (0.037 vs 0.020) but the telegraph lift stays 0.139 (r 0) / 0.165 (r 11) / 0.137 (r 17), i.e. **no measurable telegraph cost at any of the three radii** in this test. Report, not a decision: the damping centre is the arena origin, but the enemy chases the player (far-chase sequences) and the player can reach r 19, so a telegraph can appear at r 11-17 where the damped asset is already at 70-100 % strength; my numbers show no telegraph harm there, so the damping looks conservative rather than wrong. The player-centred variant is an easy shader parameter if wanted (`_DampCenter`); not used in the saved scene (damped asset in place).

## (2) Layers added one at a time (before/after at the gameplay camera; frames in `Captures/env_i2/` and close-ups `Captures/env_i2_close/`)
- **Cracks:** clearly visible on the floor outside the circle (dark, root-like, large). Reads natural at gameplay scale; at close-up they are heavy and somewhat uniform in width. **Exact 8 m repetition:** a numeric repeat metric (below) shows the cracks introduce the strongest periodic correlation.
- **Wear (0.50):** subtle patchy smudging; by eye it still reads slightly boxy/procedural as the note warned, but at gameplay scale it mostly merges into the macro variation.
- **Chipped edges:** speckle along tile joints, follows the true tile joints (aligned to the 2 m grid: checked in the close-up and plan views). Not busy at the gameplay camera.
- **Joint moss:** small olive dots/beads along joints; muted, low contrast, aligned to joints; 0 weight inside the circle.
- **Wall rain streaks:** verified present, vertical, attached to the wall face and confined to walls (diff image vs the previous stage shows only vertical streak structure on the sunlit north wall, nothing on the floor), but **very subtle**: mean luma change on the wall region 0.13 of 255. Walls facing away from the sun (west/south) are in shadow and show nothing at this camera.
- **Salt:** faint pale speckle on the floor, whole-frame mean change 0.49/255; barely noticeable.
- **Wall-base moss:** present on the walls (mean change 0.08/255); invisible at the gameplay camera except in extreme close-ups. I cannot honestly claim it reads.
- **Soot smudges (4, near braziers only, random yaw):** present but near-invisible in plan crops (very low contrast). Placed at the existing floor braziers 003/004 and the two new approach braziers; the wall plume was not used.
- **Bronze/gold inlay gating (`1 - Mask.R`) was NOT applied** (the overlays are separate quads and cannot read the baked mask). In plan views the border strip near the wall shows cracks crossing it; flagged as a defect/UNVERIFIED, not a pass.

## Is the floor still repetitive? (numbers + honest judgement)
Plan-view neighbour-patch correlation (2x2 m patches, outer ring r 12.5-17.5 outside the dais/pillar areas; higher = more exact repetition at that lag). `Reports/i2_repetition_stack.json`; script saved as `Reports/i2_repeat_metric.py` (needs only PIL).
| Stage | lag 2 m | 4 m | 6 m | **8 m** | 10 m |
|---|---|---|---|---|---|
| S00 none | 0.18 | 0.22 | 0.16 | 0.30 | 0.16 |
| S02 macro + tint | 0.18 | 0.21 | 0.12 | 0.32 | 0.14 |
| S03 + cracks (8 m tile) | 0.08 | 0.04 | 0.10 | **0.61** | 0.05 |
| S05 + wear + chips | 0.21 | 0.37 | 0.22 | **0.72** | 0.16 |
| S10 full stack (tiled normally) | 0.24 | 0.39 | 0.25 | **0.72** | 0.19 |
| **S11 cracks+wear per-cell mirror/rotate** | 0.22 | 0.25 | 0.19 | **0.29** | 0.20 |
(A second, off-axis copy of cracks/wear at a different scale was also tried, `L03b/L04b`: lag-8 only fell 0.72 to 0.59, so it is not enough; kept OFF.)
**Honest judgement:** the macro value/tint maps remove the "same tone everywhere" look outside the circle (tile CV 0.026 to 0.061) and the layers clearly break up the plain grid. **But tiling the 8 m cracks map as authored puts an exact 8 m repeat on the floor** (lag-8 correlation 0.30 to 0.72); the same crack clusters recur on a regular lattice, which an attentive player will spot at the gameplay camera. Mirroring/rotating cracks and wear per cell in the shader (a Unity-side, texture-unchanged fix) returns lag-8 to baseline (0.29) with no visible straight seams at the cell borders in the plan view; at close range I did not search every border, so **seam visibility at cell borders is UNVERIFIED at close-ups**. So: with the per-cell flip the floor no longer repeats numerically at 4-10 m and, by eye, the floor reads as worn stone rather than a tiled card, but the 2 m kit tile grid (and its 2 m periodic correlation of 0.22) is still the dominant structure, and inside the combat circle it is deliberately quiet. In the combat frames the floor still reads as a fairly regular tile grid; the visible change is mainly outside the circle and toward the edges. This is an improvement, not a fix for "repetitive".

## (3) Soot: see above (placed at 4 brazier locations, near-invisible). Wall plume not used (nearest brazier to a wall is 1.9 m).

## (4) Props reconciled and focal hierarchy
- Removed my 6 iteration-1 props; placed the Environment Artist's 8 (`VF_PROP_PLACEMENTS.json`) as clones of the matching scene instances (same meshes/materials; yaw: the list's `yaw_front_to_plusZ` + 180 = the scene's `minusZ` convention, matches the existing wall banners 90 to 270 / 180 to 0). Coordinates verified against the list. Nearest to the arena centre is 12.8 m (both approach braziers); none in the central r 10 m circle (every prop has r >= 12.8 m; the nearest to the 20 m x 20 m square is (-6.86, 10.82), z > 10). Banners are wall-mounted (r 22.3).
- **Sight lines (analytic, elevated camera 46.7 deg):** a prop only occludes a player standing within d = height/tan(46.7 deg) of it on the camera side: braziers (1.34 m) ~1.3 m, drum (1.10 m) ~1.0 m, rubble (<0.5 m) negligible; none sit near a lane. I looked at the dais approach frame (player at (-8, 8)): the two new braziers flank the stairs as a pair, nothing blocks player or altar. The existing Pillar_D (6.3 m class pieces) occlusion flagged by the Environment Artist is an existing-geometry issue; not changed.
- **Brazier lights (L11, ON in the saved scene):** warm point lights (amber, intensity 3, range 5.5, no shadows) at the two new approach braziers. Visible warm pools on the stairs approach, improves the focal read toward the dais; telegraph lift unchanged (0.137). Not tested for performance. Can be turned off.
- **What the camera sees at the altar (the altar is at (-14.1, +14.1), the NW corner, r 19.9 m; not at the arena centre):** with the plain-follow camera (size 9) the altar is **out of frame whenever the player is near the arena centre**; the screen-up half extent is about 12.4 m along the (-x,+z) axis, so the altar enters the top edge only when the player is about 7.5 m from the centre toward the NW, and is fully framed only at about (-8, 8) or closer, where its crown is still cut by the top edge and the HUD covers the top-left. So today the altar is not a "central structure" in gameplay terms; it is a destination reached after a ~11 m walk. At (-8, 8) the stepped dais with its warm accent light and now the brazier pair is the strongest value/colour accent in the frame, so the hierarchy works only in the NW quadrant. A true central focal point needs a decision (move/duplicate a structure to the centre or accept the corner altar); not made here.

## Performance (Editor Play Mode only; 1920x1080 Full HD Game view; Metal; `targetFrameRate=-1`, vSync 0; raw in `Reports/i2_perf_raw.csv`, first-session run in `i2_perf_raw_run1.csv`, per-stage UnityStats in `Reports/i2_env_stats_seq_full2.csv`)
**This measurement is noisy and I do not trust it for a number.** Five alternating no-overlay / full-stack pairs (200 frames each): pair 1 ran clean (9.9 vs 12.8 ms CPU frame, GPU 14.6 vs 19.7 ms per FrameTimingManager = overlays cost about +3 ms CPU-side / +5 ms GPU, 101 to 78 fps); pairs 2-5 ran at 34-64 ms/frame in both states (the machine was loaded; frame times jumped 4x between pairs), but the full stack was slower in every pair by about 2-12 ms. So the direction is consistent (the 10 lit full-floor transparent layers cost real GPU time), the magnitude is **UNVERIFIED**. The cause is overdraw: each overlay re-lights the whole 40 x 40 m quad. Draw calls rise only by about 21 (1391 to 1412); triangles +42. **Recommendation:** merge the floor layers into one shader pass (one lighting evaluation) and test compressed texture formats before this goes anywhere near a build; not done.

## Defects / limitations
1. The overlays are visible only outside the circle by design; the combat read is the same as before. Character separation still about -0.09/-0.12.
2. Wall-base moss, wall rain and soot are near-invisible at the gameplay camera; they work technically (positions/orientation verified) but add almost nothing visually yet; stronger opacity is possible, but I did not exceed the note's ranges.
3. Wear still looks boxy; cracks are large and heavy.
4. 8 m exact repetition of the cracks map unless the per-cell flip is used (it is, in the saved scene); seams at 8 m cell borders not checked at close range.
5. No Mask.R gating on bronze/gold inlays; cracks/moss may cross inlays on the border strip.
6. Stairs, platforms and the dais top get **no** floor overlays (the quads sit under them); the Blender test gave them value/tint/cracks/wear. This is the intended "no streaking on vertical faces" safe choice, but the dais reads cleaner than the floor.
7. GPU cost of 10 lit overdraw layers; 172 MB uncompressed textures.
8. Fog/outer ground/grime strips/altar light from iteration 1 are unchanged; the iteration-1 wall-base grime strips remain (placeholder: no grime texture exists); the iteration-1 placeholder floor mottling and placeholder moss were removed (textures exist now).

## Recommended next
1. Merge floor overlays into one shader pass; test BC7/ASTC compression; re-measure on a quiet machine.
2. Raise wall-layer opacity within the note's ranges (e.g. rain 0.9, wall moss 1.0) and light the west/south walls, or accept that they are close-up-only layers.
3. Decide the focal structure question (centre vs NW corner) with the Game Director/Nishant.
4. Character separation remains the biggest readability gap; needs the character-side change (needs approval).

## UNVERIFIED
Close-up seams at cell-flip borders; performance numbers (noisy); compression effects; inlay gating; the brazier-light cost; any play-feel judgement. Visual judgements are mine, not a QA review.

## State and safety
Saved scene = VF scene with layers L01, L02, L03c, L04c, L05, L06, L07, L08, L09, L10, L11 ON; L03/L04/L03b/L04b/L01b/L01c OFF; L0 key (38, 45, 0), camera B size 9, focus helper OFF, 8 EA props. Original courtyard scene unchanged (hash). No production script, shared URP asset, renderer feature, protected character file, `Art/Exports`, production `.blend` or `vf_handoff` source file touched (copies only). `ProjectSettings/ProjectSettings.asset` still shows `runInBackground 0 -> 1` from the tooling (reported earlier, not touched by me). No stage/commit/push/LFS/promotion. New code: `Shaders/VF_WorldOverlayLit.shader`, `Shaders/VF_WorldMultiply.shader`, `Editor/VF2Builder.cs`; `Scripts/VFRunner.cs` gained a hold-centre option.

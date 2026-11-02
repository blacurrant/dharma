# Gate 1: key light + camera matrix (ArtTest_TempleCourtyard)

Continues from `CAMERA_LIGHTING_REPORT.md` and the saved `ArtTest_TempleCourtyard.unity`. All figures are **Editor-only, Play Mode**: Unity 6000.6.7f1, URP 17.6, Metal, Apple M5. Raw data in `data/` (per-config CSVs, `char_height.csv`, `luma_lift.csv`, `perf/*.csv`, `shots/`). Harness: `Assets/ArtTest/Scripts/ArtTestSequenceRunner.cs`.

## Step 1: key light (frozen for all runs)
- Before: euler (46, 318, 0): **2.2 deg** (3D) / **3.0 deg** (horizontal) off the camera view direction, elevation 46 deg (matches the Director's and QA's figures).
- After: euler (**38, 45, 0**): **63.4 deg** (3D) / **90.0 deg** (horizontal), elevation **38 deg**. Light travels toward +X+Z; shadows fall screen-right/up.
- Same frozen pose, geometry and materials: `key_before_*.png`, `key_after_*.png`, `key_BA_gameplay.png`, `key_BA_wide.png`. Probes re-baked (207 probes, 3 s). Saved in the scene; the 45 % demo ramp cap (`endAlpha = 0.45`) is also saved.

## Step 2: camera matrix
Configs are set through the serialized `orthographicSize` and `offset` fields of the art-test scene's own `IsoCameraFollow`: A offset (12, 15.28, -12) = pitch 41.999 deg, size 8; B (12, 18, -12) = 46.686 deg, size 9; C same pitch, size 11. Applied at runtime per run and **not saved** (the saved scene is still B). `IsoCameraFollow.cs` untouched.
**Focus OFF** = pure player follow (`IsoCameraFollow.Target = Player`, `ArtTestCameraFocus` disabled). **Focus ON** = `ArtTestCameraFocus`, bias (-1, 1), enemy pull 0.35 (max 3 m).
Input: real keyboard events through the Input System (WASD, Space, Enter) into the unmodified gameplay scripts; player health raised so sequences complete. Capped = `targetFrameRate 60`; uncapped = `-1`, vsync 0 (reached about 130-366 fps).
Reference frame for every metric: 1920x1080 with the camera aspect forced to 16:9. The Game view window was not a fixed size (1689x1027 at the end); captures are rendered offscreen at 1920x1080.
Margin = smallest distance from 180 points on the projected 10 m ground circle to the frame edge, per frame (negative = clipped). Two circles: **around the player** (the protocol's measure) and the **fixed 10 m clear zone at the arena centre**. Saved frames have both drawn (red = around player, blue = fixed).
**"Visible" means inside the camera frame, not unobstructed by the HUD.** My frames are camera renders without the HUD overlay. QA's figure for the top-left HUD (about 38 % x 43 % of the frame) was not re-measured by me; anything under the HUD counts as visible here.

### Summary by config (all sequences, capped and uncapped)
| Config | Focus | Worst margin, ring around player (px) | Sequences with a negative margin | Worst margin, fixed zone at centre (px) | Frames with player/enemy outside frame | Telegraph frames fully in frame |
|---|---|---|---|---|---|---|
| A | OFF | 49 | 0/22 | -365 | 35/19175 | 1421/1421 |
| B | OFF | 44 | 0/22 | -334 | 0/17670 | 1146/1146 |
| C | OFF | 165 | 0/22 | -175 | 0/15127 | 873/873 |
| A | ON | -111 | 11/11 | -454 | 0/3571 | 218/218 |
| B | ON | -89 | 9/11 | -421 | 0/3547 | 215/215 |

### Full table (config x sequence)
| Config | Focus | FPS state (avg fps) | Sequence | Min margin, ring around player (px) | Min margin, fixed 10 m zone at centre (px) | Player/enemy outside frame (frames/total) | Telegraph fully in frame (frames) |
|---|---|---|---|---|---|---|---|
| A | OFF | cap60 (60.2) | idle | 88 | 88 | 0/106 | 0/0 |
| A | OFF | cap60 (58.9) | run | 88 | -274 | 0/922 | 0/0 |
| A | OFF | cap60 (60.2) | dash_rest | 88 | -139 | 0/467 | 0/0 |
| A | OFF | cap60 (59.9) | dash_run | 88 | -139 | 0/757 | 0/0 |
| A | OFF | cap60 (60.0) | attack | 88 | -8 | 0/263 | 0/0 |
| A | OFF | cap60 (60.2) | dodge | 78 | -88 | 0/80 | 19/19 |
| A | OFF | cap60 (40.1) | chain | 78 | 69 | 0/151 | 34/34 |
| A | OFF | cap60 (59.8) | edge_up | 81 | -365 | 0/57 | 38/38 |
| A | OFF | cap60 (60.1) | edge_down | 86 | -364 | 0/55 | 37/37 |
| A | OFF | cap60 (59.4) | far_chase_up | 88 | -47 | 7/316 | 35/35 |
| A | OFF | cap60 (59.9) | far_chase_down | 88 | -48 | 0/318 | 35/35 |
| A | OFF | uncapped (334.9) | idle | 88 | 88 | 0/583 | 0/0 |
| A | OFF | uncapped (267.0) | run | 88 | -274 | 0/4139 | 0/0 |
| A | OFF | uncapped (292.0) | dash_rest | 88 | -139 | 0/2119 | 0/0 |
| A | OFF | uncapped (293.2) | dash_run | 49 | -198 | 0/3597 | 0/0 |
| A | OFF | uncapped (290.0) | attack | 74 | -123 | 0/494 | 0/0 |
| A | OFF | uncapped (300.2) | dodge | 84 | -126 | 0/396 | 115/115 |
| A | OFF | uncapped (279.1) | chain | 74 | -117 | 0/837 | 232/232 |
| A | OFF | uncapped (296.5) | edge_up | 81 | -365 | 0/240 | 158/158 |
| A | OFF | uncapped (365.9) | edge_down | 85 | -364 | 0/302 | 202/202 |
| A | OFF | uncapped (270.9) | far_chase_up | 66 | -242 | 28/1425 | 234/234 |
| A | OFF | uncapped (293.8) | far_chase_down | 59 | -234 | 0/1551 | 282/282 |
| B | OFF | cap60 (60.0) | idle | 103 | 103 | 0/109 | 0/0 |
| B | OFF | cap60 (60.0) | run | 78 | -247 | 0/945 | 0/0 |
| B | OFF | cap60 (59.9) | dash_rest | 47 | -116 | 0/462 | 0/0 |
| B | OFF | cap60 (59.9) | dash_run | 44 | -134 | 0/763 | 0/0 |
| B | OFF | cap60 (60.0) | attack | 90 | -104 | 0/116 | 0/0 |
| B | OFF | cap60 (58.8) | dodge | 100 | -113 | 0/84 | 28/28 |
| B | OFF | cap60 (59.3) | chain | 90 | -98 | 0/184 | 57/57 |
| B | OFF | cap60 (60.0) | edge_up | 97 | -334 | 0/53 | 36/36 |
| B | OFF | cap60 (60.2) | edge_down | 101 | -334 | 0/57 | 37/37 |
| B | OFF | cap60 (45.0) | far_chase_up | 83 | -234 | 0/297 | 27/27 |
| B | OFF | cap60 (59.3) | far_chase_down | 78 | -212 | 0/312 | 46/46 |
| B | OFF | uncapped (287.9) | idle | 103 | 103 | 0/504 | 0/0 |
| B | OFF | uncapped (262.1) | run | 103 | -247 | 0/4067 | 0/0 |
| B | OFF | uncapped (263.5) | dash_rest | 103 | -116 | 0/1873 | 0/0 |
| B | OFF | uncapped (232.6) | dash_run | 103 | -116 | 0/2813 | 0/0 |
| B | OFF | uncapped (251.4) | attack | 103 | 10 | 0/1074 | 0/0 |
| B | OFF | uncapped (246.4) | dodge | 94 | -67 | 0/309 | 66/66 |
| B | OFF | uncapped (237.6) | chain | 94 | 85 | 0/712 | 194/194 |
| B | OFF | uncapped (263.5) | edge_up | 98 | -334 | 0/201 | 143/143 |
| B | OFF | uncapped (337.5) | edge_down | 101 | -334 | 0/273 | 177/177 |
| B | OFF | uncapped (224.2) | far_chase_up | 103 | -28 | 0/1170 | 147/147 |
| B | OFF | uncapped (215.7) | far_chase_down | 103 | -28 | 0/1292 | 188/188 |
| C | OFF | cap60 (60.0) | idle | 182 | 182 | 0/110 | 0/0 |
| C | OFF | cap60 (55.5) | run | 166 | -104 | 0/935 | 0/0 |
| C | OFF | cap60 (60.0) | dash_rest | 182 | 4 | 0/466 | 0/0 |
| C | OFF | cap60 (59.7) | dash_run | 182 | 4 | 0/762 | 0/0 |
| C | OFF | cap60 (60.0) | attack | 182 | 107 | 0/269 | 0/0 |
| C | OFF | cap60 (60.1) | dodge | 175 | 43 | 0/84 | 29/29 |
| C | OFF | cap60 (59.9) | chain | 175 | 167 | 0/187 | 47/47 |
| C | OFF | cap60 (60.1) | edge_up | 178 | -175 | 0/55 | 37/37 |
| C | OFF | cap60 (60.0) | edge_down | 181 | -175 | 0/55 | 37/37 |
| C | OFF | cap60 (39.3) | far_chase_up | 182 | 75 | 0/282 | 9/9 |
| C | OFF | cap60 (57.5) | far_chase_down | 165 | 75 | 0/304 | 47/47 |
| C | OFF | uncapped (221.6) | idle | 182 | 182 | 0/377 | 0/0 |
| C | OFF | uncapped (225.9) | run | 182 | -104 | 0/3509 | 0/0 |
| C | OFF | uncapped (192.3) | dash_rest | 182 | 4 | 0/1511 | 0/0 |
| C | OFF | uncapped (209.5) | dash_run | 182 | 4 | 0/2549 | 0/0 |
| C | OFF | uncapped (130.4) | attack | 174 | 82 | 0/675 | 0/0 |
| C | OFF | uncapped (186.5) | dodge | 175 | 43 | 0/259 | 106/106 |
| C | OFF | uncapped (173.0) | chain | 175 | 168 | 0/517 | 158/158 |
| C | OFF | uncapped (170.2) | edge_up | 178 | -175 | 0/121 | 65/65 |
| C | OFF | uncapped (246.3) | edge_down | 182 | -175 | 0/172 | 109/109 |
| C | OFF | uncapped (182.0) | far_chase_up | 182 | 75 | 0/947 | 118/118 |
| C | OFF | uncapped (189.2) | far_chase_down | 182 | 75 | 0/981 | 111/111 |
| A | ON | cap60 (60.0) | idle | -65 | -65 | 0/108 | 0/0 |
| A | ON | cap60 (59.9) | run | -111 | -300 | 0/943 | 0/0 |
| A | ON | cap60 (60.0) | dash_rest | -108 | -212 | 0/468 | 0/0 |
| A | ON | cap60 (60.0) | dash_run | -108 | -212 | 0/765 | 0/0 |
| A | ON | cap60 (60.0) | attack | -31 | -127 | 0/270 | 0/0 |
| A | ON | cap60 (60.0) | dodge | -12 | -170 | 0/85 | 28/28 |
| A | ON | cap60 (60.0) | chain | -45 | -45 | 0/188 | 47/47 |
| A | ON | cap60 (60.1) | edge_up | -30 | -454 | 0/54 | 37/37 |
| A | ON | cap60 (60.0) | edge_down | -88 | -327 | 0/55 | 36/36 |
| A | ON | cap60 (59.5) | far_chase_up | -111 | 25 | 0/316 | 35/35 |
| A | ON | cap60 (60.0) | far_chase_down | -7 | -143 | 0/319 | 35/35 |
| B | ON | cap60 (60.0) | idle | -45 | -45 | 0/111 | 0/0 |
| B | ON | cap60 (55.4) | run | -89 | -272 | 0/923 | 0/0 |
| B | ON | cap60 (60.0) | dash_rest | -86 | -187 | 0/466 | 0/0 |
| B | ON | cap60 (59.9) | dash_run | -86 | -187 | 0/762 | 0/0 |
| B | ON | cap60 (60.0) | attack | -12 | -105 | 0/269 | 0/0 |
| B | ON | cap60 (60.0) | dodge | 7 | -147 | 0/82 | 25/25 |
| B | ON | cap60 (60.0) | chain | -25 | -25 | 0/188 | 47/47 |
| B | ON | cap60 (60.0) | edge_up | -15 | -421 | 0/55 | 38/38 |
| B | ON | cap60 (60.0) | edge_down | -66 | -298 | 0/56 | 36/36 |
| B | ON | cap60 (60.0) | far_chase_up | -89 | 42 | 0/320 | 35/35 |
| B | ON | cap60 (60.0) | far_chase_down | 12 | -119 | 0/315 | 34/34 |

Notes: `edge_up/edge_down` put the player 10 m from the arena centre up-/down-screen. The enemy counts as "in frame" only within 10 m of the player. `far_chase_*`: enemy starts 9 m away and stays inactive for the first 1.8 s while the player chases, then attacks. The fixed-zone circle cannot stay fully in frame when the player is near the arena edge in any config, so negative values there are expected. The dodge sequence found a telegraph in every run. Min fps in the CSVs includes capture hitches (screenshot and measurement frames).

### Character height measured directly from the captures
Method: render each frame twice (player shadow-only vs normal) and diff, giving the silhouette head-top to feet in pixels (it includes the foot-plane depth of the body). Real size from mesh bounds at the idle pose: player union SMR bounds size: (1.398, 2.023, 1.416) (y=2.023); enemy union SMR bounds size: (1.517, 2.210, 1.554) (y=2.210); player CC height=2. The Director's correction holds: projected height is about height x cos(pitch); my earlier "~98 px at size 11" was an estimate and is superseded. "Standing" excludes the two dash sequences.
| Config | Frames measured | Median standing height | Range (standing) | Lowest frame |
|---|---|---|---|---|
| A | 42 | 119 px = 11.0% | 86-120 px | 86 px (8.0%) |
| A+focusON | 21 | 119 px = 11.0% | 114-120 px | 114 px (10.6%) |
| B | 42 | 103 px = 9.5% | 74-119 px | 59 px (5.5%) |
| B+focusON | 21 | 103 px = 9.5% | 98-113 px | 98 px (9.1%) |
| C | 42 | 84 px = 7.8% | 61-96 px | 61 px (5.6%) |

Low outliers occur in the low dash pose (example: `shots/B_plain_cap60_dash_rest_S(down).png`).

### Telegraph visibility (in-engine luma lift, same pixels with vs without the telegraph)
Rec.709 luma on the final tonemapped frame, over pixels that changed, fixed pose. This is photometry on a held pose, **not combat validation**. `fill+area` = fill plus the faint 10 % area tint as shown; `edge+front` = outline plus front arc. Mean over lifted pixels; p10 = weakest pixels.
| Surface | Fill alpha | Part | Mean lift | p10 lift | Max lift |
|---|---|---|---|---|---|
| lit_floor | 0.26 | fill+area | 0.133 | 0.027 | 0.593 |
| lit_floor | 0.26 | edge+front | 0.188 | 0.006 | 0.748 |
| lit_floor | 0.40 | fill+area | 0.158 | 0.017 | 0.567 |
| lit_floor | 0.40 | edge+front | 0.206 | 0.007 | 0.723 |
| lit_floor | 0.45 | fill+area | 0.172 | 0.024 | 0.618 |
| lit_floor | 0.45 | edge+front | 0.228 | 0.006 | 0.715 |
| shadowed_floor | 0.26 | fill+area | 0.204 | 0.061 | 0.529 |
| shadowed_floor | 0.26 | edge+front | 0.282 | 0.006 | 0.728 |
| shadowed_floor | 0.40 | fill+area | 0.250 | 0.086 | 0.448 |
| shadowed_floor | 0.40 | edge+front | 0.281 | 0.006 | 0.726 |
| shadowed_floor | 0.45 | fill+area | 0.264 | 0.091 | 0.469 |
| shadowed_floor | 0.45 | edge+front | 0.340 | 0.006 | 0.727 |
Lit floor = arena centre. Shadowed floor = nearest point to the centre where five sample points are all in shadow under the new key (the wall-shadow band). Images: `data/luma_*_with_45.png` / `_without_45.png`.

## Performance (Editor only)
Conditions: Editor Play Mode, Metal, Apple M5, **every row rendered to the same 1920x1080 render target**, uncapped, vsync 0, 60 warm-up frames then 300 sampled frames, same held pose (player at spawn, enemy 2 m away, windup 30 %, AI frozen), two repeats per row, rows interleaved (A8 measured last). "after" = current state (new key, post-processing, 2 actor point lights, probes). "before" = same ortho size with post-processing off, actor lights off and the old front-lit key (46, 318, 0). Raw samples: `data/perf/perf_*.csv`.
| Row | Frame ms median | Frame ms p95 | CPU main ms | Draw calls | SetPass | Triangles (M) | Shadow casters |
|---|---|---|---|---|---|---|---|
| A8_after_r1 | 5.37 | 6.64 | 1.41 | 1267 | 68 | 4.48 | 743 |
| A8_after_r2 | 5.57 | 6.83 | 1.46 | 1267 | 68 | 4.48 | 743 |
| B9_after_r1 | 4.59 | 5.95 | 1.29 | 1366 | 72 | 5.17 | 804 |
| B9_after_r2 | 4.62 | 6.11 | 1.28 | 1366 | 72 | 5.17 | 804 |
| B9_before_r1 | 4.57 | 5.74 | 1.30 | 1292 | 55 | 4.38 | 747 |
| B9_before_r2 | 4.72 | 6.11 | 1.19 | 1292 | 55 | 4.38 | 747 |
| C11_after_r1 | 5.75 | 7.97 | 1.36 | 1778 | 74 | 7.89 | 1050 |
| C11_after_r2 | 5.80 | 7.79 | 1.40 | 1778 | 74 | 7.89 | 1050 |
| C11_before_r1 | 5.69 | 7.21 | 1.38 | 1822 | 57 | 7.54 | 1111 |
| C11_before_r2 | 6.00 | 7.75 | 1.46 | 1822 | 57 | 7.54 | 1111 |
Reading: before vs after at the same size shows almost no median frame-time change in this Editor test (size 9: 4.57-4.72 vs 4.59-4.62 ms), but +17 SetPass calls and +0.8 M triangles at size 9 (+0.35 M at size 11). GPU time was **not available** (FrameTimingManager reported 0), so GPU cost is UNVERIFIED. Size 8 read slower than size 9 despite fewer draws; it was measured last, so order/thermal drift or a pitch effect cannot be separated (UNVERIFIED).

## State
- Editor was **not in Play Mode** when this was written; scene saved, not dirty, key (38, 45, 0), ramp cap 0.45, camera size 9 (B).
- Tracked changes: only the three Unity-generated files already known plus `Art/README.md`. `ProjectSettings/ProjectSettings.asset` mtime 22:18:22, content identical to HEAD (from my earlier revert). Nothing under `Assets/Scripts`, shared URP assets or the other scenes was touched.

## UNVERIFIED / not done
- GPU frame time; any player build; sustained long-run frame time.
- Colour-vision-deficiency renders (luma lift above is the greyscale measure); telegraph lift on only two surfaces (lit and shadowed floor).
- Pass thresholds (+0.10 fill, +0.25 edge) are the CD's to apply: means clear +0.10, the weakest 10 % of pixels do not.
- HUD obstruction of the ring and telegraph (HUD not in the camera captures).
- Camera lag not isolated numerically (`max_player_offset_px` is in the CSVs).
- Whether the low dash pose is intended.

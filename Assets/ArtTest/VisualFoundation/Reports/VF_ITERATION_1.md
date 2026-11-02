# VF_ITERATION_1: Visual Foundation (ArtTest_VisualFoundation)

Scene: `Assets/Scenes/ArtTest_VisualFoundation.unity` (copy of `ArtTest_TempleCourtyard`). Original scene SHA-256 before and after = `b30065166bf4...2ef724` (byte-identical). All figures are **Editor Play Mode only**: Unity 6000.6.7f1, URP 17.6, Metal, Apple M5. Nothing committed, staged, promoted or pushed; no shared URP asset, ProjectSettings, `Assets/Scripts`, Blender or `Art/Exports` file touched. The four Unity-generated tracked files were not modified or reverted by me.

## A) Real Game view baseline
- Capture: `Captures/A_gameview_B_baseline_HUD.png`. Taken with the MCP `game_view` tool, `source=screen`, so the HUD is included and there is no grid or gizmos.
- **Game view size setting:** fixed resolution **"Full HD" 1920x1080** (size index 3, an existing Editor preset, unchanged by me except that I selected it). The Editor's `Screen.width/height` reported 1944x1734 in Play Mode, which is odd; the captured frames are 1920x1080 and the HUD scale matches 1080 (GUI scale 1.8).
- Config B (46.7 deg, size 9, offset (12, 18, -12)), plain player-follow (`ArtTestCameraFocus` disabled and saved OFF in this scene, `IsoCameraFollow.Target = Player`). No production camera script changed.
- In the baseline the HUD sits top-left; player and enemy are about 90-105 px tall.

## B) Camera, moving, Game view with HUD
Runs use real keyboard input into the unmodified gameplay scripts, deterministic 60 fps (`Time.captureFramerate = 60`), same scripted sequence per config: idle, run toward the enemy, dash sideways (screen-right), attack, wait for the enemy windup, dodge by dashing across it. Frames are Game-view captures (HUD included). Gate 1 numbers (plain follow, 8-direction run/dash/edge/far-chase, capped and uncapped) are reused, not re-run: A +49 px, B +44 px, C +165 px worst ring margin.
Configs: A = 42 deg / size 8 (offset y 15.28); **A2 = 42 deg / size 8.5 (added)**; B = 46.7 deg / size 9; C = 46.7 deg / size 11.
**Why A2:** Gate 1 shows A and B both have only about 45 px of worst-case margin and A's characters are largest (11 %), so a small size increase at A's pitch buys margin while keeping most of A's height. The data confirmed it (A2 +53 px vs A -76 px in the sequence below).

### Combat area, HUD and spacing (this sequence)
| Config | Min margin, 10 m ring around player (px) | Ring visible and not under HUD, worst frame (HUD box / bars only) | Telegraph under HUD (max %) | Min wall-base visible, not under HUD (worst frame) | Player-enemy spacing when engaged (px) | Frames with player out of frame |
|---|---|---|---|---|---|---|
| A | **-76 (clipped)** | 68.9 % / 70.6 % | 0 % | 0.0 % | 89-469 | 0 |
| A2 | +53 | 81.1 % / 89.4 % | 0 % | 0.0 % | 84-432 | 0 |
| B | +16 | 80.6 % / 90.0 % | 0 % | 2.5 % | 86-417 | 0 |
| C | +130 | 82.8 % / 94.4 % | 0 % | 18.8 % | 71-343 | 0 |
Source: `Reports/vf_cam_hud.csv`. The margin minimum comes from the sideways dash (the follow camera lags the dash). It differs from Gate 1 because the stress sequence is different (a sideways screen-right dash at a deterministic 60 fps); both are valid, neither is a worst case across all inputs.
HUD obstruction: I derived the HUD rectangles from `PrototypeHud.cs` at GUI scale 1.8: bars (25, 25)-(619, 331) px = 31 % x 28 % of the frame (8.8 % of the area); the hint line's layout box extends to x = 871, y = 380 (45 % x 35 %, 14.5 % of the area, but the visible text ends near x = 664). QA's figure (38 % x 43 %) differs; I have not reconciled it. **"Visible" in this report means in frame and not under the HUD box**, so the ring loses up to about 11-17 % of its points to the HUD even when fully in frame.
Arena boundary (wall base within frame, % of the 156 m of wall-base perimeter, computed for player positions with the camera held at each config's pitch/size): centre 0 % (A, A2), 3 % (B), 25 % (C); 10 m from a wall 11-15 % (A-B), 32 % (C); corner (10,10) 22-27 %. So only C shows meaningful architecture when the player is mid-arena.

### Character size in the Game view (direct silhouette pixels; 1080 px frame height)
Silhouette = pixels that change when the character's mesh stops casting into the frame (shadow-only vs normal), head-top to feet incl. weapon and pose. Real mesh bounds: player 2.02 m, enemy 2.21 m (enemy visual scale 1.1).
| Config | Player, attack frame | Enemy, attack frame | Player, telegraph frame | Enemy, telegraph frame | Spacing at attack (px / m) |
|---|---|---|---|---|---|
| A | 110 px (10.2 %) | 149 px (13.8 %) | 103 px (9.5 %) | 126 px (11.7 %) | 104 / 1.62 |
| A2 | 103 px (9.5 %) | 141 px (13.1 %) | 98 px (9.1 %) | 121 px (11.2 %) | 98 / 1.62 |
| B | 94 px (8.7 %) | 129 px (11.9 %) | 91 px (8.4 %) | 109 px (10.1 %) | 93 / 1.62 |
| C | 76 px (7.0 %) | 106 px (9.8 %) | 72 px (6.7 %) | 89 px (8.2 %) | 76 / 1.62 |
Caveats: heights depend on pose (weapon raised during attack and windup), which is why the enemy reads taller than 1.1x the player; the idle-frame enemy value (6 m away, partly in shadow) is unreliable and omitted. Raw: `Reports/vf_cam_sizes.csv`.

### Recommendation (camera)
**A2 (42 deg, size 8.5), plain follow, focus helper OFF.** It keeps the full 10 m ring (+53 px, 81 %+ not under the HUD) with characters about 10 % larger than B, and a better ground-plane read than A, which clips (-76 px). C is the safe-margin option and the only one that shows real architecture, but characters are 7 % of frame height. This is a recommendation for the CD; nothing is adopted. UNVERIFIED across all 8-direction uncapped inputs for A2 (only the scripted sequence was run at A2).
Side-by-side same-frame sheets (same pose, same frame event per config): `Captures/strip_compare_{1_idle,3_dash,4_attack,5_telegraph,6_dodge}.png` (2x2: A, A2, B, C) and per-config sequence strips `Captures/strip_{A,A2,B,C}_sequence.png`. Individual Game-view frames: `Captures/strips/`.

## C) Lighting (camera B, 1920x1080, one variable at a time from L0; measured on a held pose: player at spawn, enemy 2.2 m away, telegraph at the 45 % test ramp)
Measures: floor luma = mean luma of floor pixels within 8 m of the arena centre excluding characters (Rec.709 on the final tonemapped frame); separation = character silhouette mean luma minus the mean luma of the floor in a ~10 px ring around it (negative = character darker than floor; larger magnitude = more contrast); telegraph lift = mean luma gain over the same pixels with vs without the telegraph (all parts). Shadow length is analytic (2.02 m / tan(elevation)), direction as it falls on screen. `Reports/vf_light.csv`.
| Variant | Change from L0 | Key vs camera (3D) | Floor luma | Player sep. | Enemy sep. | Shadow (analytic) | Telegraph lift mean / p10 |
|---|---|---|---|---|---|---|---|
| L0 | yaw 45, elev 38 | 63.4 deg | 0.384 | -0.094 | -0.115 | 2.56 m, to screen-right | 0.139 / 0.050 |
| V1 | yaw 75 | 79.8 deg | 0.392 | -0.108 | -0.106 | 2.56 m, down-right (-23 deg) | 0.136 / 0.047 |
| V2 | yaw 105 | 91.2 deg | 0.408 | -0.132 | -0.142 | 2.56 m, down-right (-52 deg) | 0.127 / 0.043 |
| V3 | elev 30 | 68.7 deg | **0.353** | -0.075 | -0.087 | 3.46 m | 0.151 / 0.055 |
| V4 | elev 50 | 56.1 deg | 0.418 | -0.118 | -0.136 | 1.68 m | 0.125 / 0.042 |
| V5 | key warmer (1.0, 0.80, 0.58) | 63.4 deg | 0.358 | -0.084 | -0.102 | 2.56 m | 0.150 / 0.058 |
| V6 | shadow strength 0.82 to 0.55 | 63.4 deg | 0.384 | -0.080 | -0.101 | 2.56 m | 0.139 / 0.050 |
| V7 | warm ambient | 63.4 deg | 0.384 | -0.092 | -0.115 | 2.56 m | 0.139 / 0.050 |
Findings: yaw 75-105 gives the three-quarter-back feel (shadows fall toward the viewer) and raises character contrast (|sep| 0.11-0.14 vs 0.09-0.12) but brightens the floor a little; lower elevation (V3) darkens the floor into the proposed 0.30-0.36 band and lengthens shadows but lowers character contrast; warmer key (V5) darkens the floor by 0.026 and saturates strongly orange; V6 only lightens shadows; **V7 changed nothing** because static geometry and probes took their ambient from the earlier probe bake (a probe rebake would be needed; not done), so the ambient warm-vs-cool test is UNVERIFIED. Material definition (by my eye, stone): visible grain/relief in all; V3 and V1 show the strongest relief; V4 flattens it. Contact sheet: `Captures/light_variants_sheet.png`; per-variant Game-view frames: `Captures/light/`.
Finalists re-shot at camera A: L0, F1 = V1, F2 = V3, **F3 = V1 + V3 combined (yaw 75, elev 32; combination, not a single-variable test)**. A: floor luma 0.382 / 0.390 / 0.352 / 0.367, player sep -0.097 / -0.114 / -0.078 / -0.100, telegraph lift 0.140 / 0.137 / 0.151 / 0.145. `Captures/light_finalists_at_A.png`.
**Recommendation (lighting):** F3 (yaw 75, elev about 32) if the CD wants the three-quarter-back look with a floor in the 0.30-0.36 range (0.367 at A, 0.37 estimated at B); F1 if the floor should stay brighter. The saved scene keeps **L0 (38, 45, 0)** as instructed; none of the variants is saved. The floor luma band is a proposal, not a requirement. Indirect probes were not rebaked for any variant, so the indirect term still comes from the L0 bake.

## D) Environment (Unity-side, reversible: everything is under `VF_Environment` plus one scene fog setting; builder `Editor/VFBuilder.cs`, `Remove()` undoes it)
No shared URP asset, renderer feature, decal feature or existing material was edited; all materials are new in `Materials/`. The sun/ring motif was not touched. The Environment Artist's weathering textures have **not landed** (`Art/Blender/Revisions/vf_handoff/` does not exist yet), so every overlay below is a **procedural placeholder tint**.
1. **Floor mottling, dark** (new overlay quad, unlit transparent, alpha up to 0.36, `VF_FloorMottle_Dark`). Before: uniform tile tone with a regular grid. After: large low-frequency darker patches. Effect is mild.
2. **Floor mottling, chalky lightening** (second overlay, alpha up to 0.13). Raises mean floor luma slightly.
3. **Wall-base darkening** (four 39 x 3.2 m gradient strips on the floor inside each wall, up to 0.85 alpha). Before: bright floor meets wall abruptly. After: a darker grounded band at each wall base.
4. **Restrained moss placeholder** (four strips, green-brown, up to 0.30 alpha, noise-masked, wall base only).
5. **Outer ground plane** (`VF_OuterGround`, 160 m, dark warm, below the floor). Before: raw near-black clear colour beyond the walls and through the arch. After: a dark brown ground reads beyond the walls; the void is less hard.
6. **Linear fog** (start 26, end 70, dark warm; scene setting). The effect on the far side is faint at gameplay scale; it is on in the saved scene, can be turned off with `RenderSettings.fog = false`.
7. **Altar accent light** (point, amber (1.0, 0.62, 0.30), intensity 6, range 10, no shadows, `VF_AltarAccent`). Before: altar and dais as lit by the key. After: a warm pool on the dais and stairs; this is the clearest focal improvement in the captures.
8. **Props from existing kit pieces only** (6: Rubble_A x3, Rubble_B x2, ColumnDrum_A x1), all at least 13 m from the arena centre (outside the central clear area), no new modelling, no collision added.
Before/after pairs (before = current scene before the pass, same camera B plain follow, same positions): `Captures/env/BA_after2_{dais,wall,arch,corner}.png`; first-pass pairs `BA_after1_*` (weaker settings); combat pose `Captures/env_combat_BA.png`.
Measured on the held combat pose (before to after2): floor luma 0.384 to 0.401; player separation -0.092 to -0.090; enemy separation -0.115 to -0.110; telegraph lift 0.139 to 0.133 (p10 0.050 to 0.048). So the environment pass is **neutral to slightly negative for telegraph visibility (-0.006)** and does not change character contrast.

## Remaining defects
- Characters are still dark on a mid-tan floor (separation about -0.09 to -0.14); rim light vs outline is deferred.
- The tile grid remains visible; overlays at this strength only mildly break it up. The Environment Artist textures should replace the placeholders.
- Overlays are unlit, so they darken sunlit and shadowed floor equally; wall faces are not darkened (only the floor at the base).
- Fog is barely visible at gameplay scale; the far architecture still reads as a hard, bright edge at the top of frame in some views.
- A clips the 10 m ring in the dash sequence; B is thin (+16 px); the HUD hides 11-17 % of the ring points at every config.
- Props sit near the edges and are rarely in frame at gameplay positions.

## Recommended next changes
1. Camera: A2 plain follow as the candidate; run A2 through the full Gate 1 eight-direction and uncapped set before any decision.
2. Lighting: apply F3 (yaw 75, elev 32) in a copy, rebake the probes, then re-measure floor luma, separation and telegraph lift and recheck the ambient warm/cool test.
3. Replace the procedural overlays with the Environment Artist's textures once the handoff manifest exists; keep the overlay structure.
4. Add a darker wall-face gradient and a small value lift behind the actors only after the character-contrast decision (rim/outline).

## UNVERIFIED
- Warm-vs-cool ambient (probes not rebaked); effect of every lighting variant on indirect light.
- A2 under the full Gate 1 input set; uncapped frame-rate lag for these runs (sequences were deterministic 60 fps).
- Telegraph under the HUD for enemy directions other than the scripted one (0 % in this run); HUD rectangle sizes versus QA's 38 % x 43 %.
- Pose dependence of the silhouette heights; the odd Editor `Screen` size (1944x1734) in Play Mode.
- Visual judgments (stone definition, mood, "reads as natural wear") are my own eye, not a QA review; no colour-vision-deficiency or greyscale renders.
- Frame time and memory for the new scene (not measured in this iteration).
- Environment Artist textures (not landed).

## State and tooling
- Saved scene: `ArtTest_VisualFoundation.unity` with L0 key (38, 45, 0), camera B (size 9), focus helper OFF, `VF_Environment` and fog on. The Editor is not in Play Mode. The camera config changes in the runs were runtime only and not saved.
- The Unity MCP tools dropped after the second script recompile, so the environment pass and the after-captures were run through the `unity` command-line tool against the same Editor (the Editor, scene and results are the same; only the transport differs). The camera and lighting measurements and the baseline capture used MCP.
- Harness: `Scripts/VFRunner.cs` (runtime measurement and captures), `Editor/VFBuilder.cs` (environment pass).

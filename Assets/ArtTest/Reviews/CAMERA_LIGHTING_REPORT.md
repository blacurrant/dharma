# Camera + lighting pass: ArtTest_TempleCourtyard

Scene: `Assets/Scenes/ArtTest_TempleCourtyard.unity` (only scene edited). Unity 6000.6.7f1, URP 17.6, Metal, Apple M5.
Nothing committed, pushed, promoted or reorganised. PrototypeArena / SampleScene / CharacterRigTest unchanged (size + mtime checked).

## Headline
- **Camera:** recommended = ortho **9**, offset unchanged (12, 18, -12), focus bias 1.4 m toward the dais, 35 % pull toward the enemy. Verified in frozen-pose Play Mode captures only.
- **Lighting:** warm Mixed key + cool tri-light ambient + baked **light probes** (207) + soft shadows. Verified.
- **Baked lightmaps: FAILED to produce a usable render.** The bake runs and writes lightmaps, but every lightmapped surface renders as blown white / black mosaic, including plain Unity primitives. Root cause not isolated. Final scene therefore uses probes only (`receiveGI = LightProbes`); there are **no lightmaps in the scene**. Details below.
- **Correction to my previous report:** finding 1 ("cyan fill almost invisible") was mostly **my bug**: the demo fill mesh had reversed triangle winding and was back-face culled, so only the edge drew. Fixed; the fill is now visible at spec opacity.

## Phase 1: camera (same pose every shot: player at spawn, enemy 2 m away, windup frozen at 70 %, 1920x1080)
Shots: `Phase1/` (pre-lighting, camera-only comparison) and `Phase2/cam_final_*` (final lighting).

| Config | px per m (1080p) | Paladin (~2 m) | Dais / arch in frame | 10 m combat radius | Verdict |
|---|---|---|---|---|---|
| 11 baseline | 49 | ~98 px | rarely | yes | actors small |
| 10 | 54 | ~108 px | stairs peek in with bias | yes, ~1.7 m margin | viable, only +10 % |
| **9 + bias (-1,1) + 35 % enemy pull** | **60** | **~120 px (+22 %)** | stairs/pillar bases at top edge as the player moves toward the dais | **yes, ~0.7 m margin** | **recommended** |
| 8 | 67.5 | ~135 px (+38 %) | architecture mostly out of frame | clipped once the focus shifts | too tight for this room |

Reasoning for 9: it is the largest size where the 10 m ground circle (7.3 m vertical on screen) stays fully visible after the dais bias (+1.0 m) and enemy pull. Size 8 gives bigger actors but loses the combat area. Constant 3.5 m dais bias (variants "b") showed the stairs but pushed the player low in frame and would be wrong when the player is elsewhere, so the bias is kept small.
Implementation: `ArtTestCameraFocus` (scene-local helper) moves the target IsoCameraFollow tracks. Gameplay camera script untouched. Camera size 9 serialized on the scene's IsoCameraFollow.

## Phase 2: lighting (as saved)
- Key: Directional, **Mixed**, colour (1.00, 0.89, 0.74), 1.3, euler (46, 318, 0), soft shadows, strength 0.82, bias 0.04 / normal bias 0.5.
- Ambient: **Trilight** sky (0.42, 0.52, 0.66), equator (0.34, 0.38, 0.45), ground (0.17, 0.15, 0.14).
- Post (scene Volume, own profile): Neutral tonemap, Bloom (threshold 1.0, 0.18), saturation -12, contrast +8. Camera background (0.075, 0.062, 0.058).
- Light probes: 207 (4 m grid, two heights, extra around dais and arch), baked.
- Actor readability lights: one soft realtime point light on player (warm white) and on enemy, no shadows.
- Fog: tested (exp², 0.016, cool). **No visible benefit** at ortho 9, left off.
- Reflection probe: tested (baked box, whole courtyard). Mean pixel change 1-3 / 255 at gameplay scale, **removed**.
- SSAO: **not configured** (needs the shared `PC_Renderer` asset edited, which would also change PrototypeArena). Baked texture AO (mask G) is in use.
- Shadow quality settings (2048 map, 4 cascades, 50 m) are in the shared URP asset and were not changed.

### Floor grout and telegraph fixes
- Dark joint lines were the 2 cm tile gaps showing the clear colour. Added `Floor_MortarUnderlay` (cube, top y = -0.02, warm stone colour) under the tiles. Joints now read as soft tone changes. Floor AO strength 0.35 and bump 0.6 on floor materials. Remaining faint tile-edge darkening is baked into the BaseColor texture.
- Cyan telegraph: `ArtTestCyanTelegraphPreview` on ArenaEnemy mirrors the real TrainingDummy windup (position, direction, range 2.15, half-angle 58, progress). Fill #27DCD1 at 26 % rising to 46 % toward the strike, edge #9BFFF6 (0.10 m), bright front arc, faint full-area tint. Original orange telegraph renderers are hidden **in this scene only**; TrainingDummy is unchanged. Two-sided unlit transparent so winding cannot hide it. Readable at 35 %, 70 % and 95 % windup (`Phase3/best_gameplay_size9_windup35/95.png`, `Phase2/cam_final_size9_RECOMMENDED.png`).

## Phase 3: baking
Final bake = light probes only: **207 probes, 4.4 s**, 0 lightmaps (GPU Progressive).
Settings: Progressive **GPU**; Mixed = Baked Indirect; bounces 2; direct/indirect/env samples 32/256/128; AO on (0.9 m); non-directional; 12 texels/m, 1024 max atlas; OpenImage denoiser; probes via `LightProbeGroup`. Static renderers: Contribute GI on, **Receive GI = Light Probes**.

### What failed (be careful before trusting any lightmap result in this project)
1. Lightmap bakes succeeded technically (2-4 atlases, 25-60 s, 460/460 renderers lightmapped) but every render with lightmaps present was blown white / black mosaic. Tried: Unity-generated UV1 (fine and very coarse charts), Blender UV0, BC6H vs uncompressed half-float, single atlas, indirect x5, Baked vs Mixed key. Image barely changed between variants.
2. **A temporary set of Unity primitives (cube, sphere, cube) with perfectly good lightmap UVs rendered the same way**, so the assets alone are not the cause. Lightmaps cleared in memory => correct image every time.
3. CPU Progressive lightmapper cannot run: Unity reports Apple Rosetta is not installed. I did not install it (system change).
4. Not isolated: whether this is a lightmap decode/encoding mismatch in this Unity/URP/Metal combination or a URP setting. I did not change PlayerSettings or shared URP assets to chase it.
5. The in-Editor Game view also showed a stale/garbled frame right after a bake (cyan async-shader placeholder first, then noise). Use `source=camera` or wait for shader compilation before trusting a capture.

### Defects that cannot be fixed in Unity without changing existing assets
- Environment pieces have no clean lightmap UV set (UV0 is a texture atlas of many small islands; Unity-generated UV1 on 30-120 k-tri relief meshes fragments badly). Needs a purpose-made non-overlapping UV1 or simplified GI proxies from the Environment Artist before any lightmap bake can be trusted.
- Tile joints are real 2 cm open gaps; the underlay is a workaround. Baked dark edge/grout detail in the BaseColor textures remains.
- Hard black void outside the walls at the oblique frame edges (no skirt/horizon geometry).
- Paladin player/enemy meshes read mid-dark against the mid-tan floor; only more light helps in Unity. A rim/outline treatment needs a material or shader change.
- Arch clear opening is 4.2 m (not 5 m) as reported before.

## Performance after the pass (Editor Play Mode, indicative)
Conditions: Unity Editor, Play Mode, Metal, Apple M5, Game view 1386x781 (Screen), vsync off, post-processing on, soft shadows (2048 / 4 cascades), 207 probes, 2 actor point lights, windup pose frozen, values are means of 4 samples from `diagnostics get_performance`, run-in-background on. Not a player build.

| Ortho size | Draw calls | SetPass | Triangles | CPU ms | GPU ms |
|---|---|---|---|---|---|
| 11 | 2,068 | 74 | 9.20 M | 4.79 | 3.92 |
| 10 | 1,797 | 74 | 7.18 M | 4.58 | 3.89 |
| **9** | **1,532** | **74** | **5.48 M** | **4.47** | **3.20** |
| 8 | 1,217 | 66 | 3.95 M | 3.80 | 2.74 |

Before this pass (size 11, no post, no actor lights): ~1,900-2,000 draws, 7.7-8.3 M tris, CPU 2.2-3.1 ms, GPU 3.8 ms (single sample). So lighting/post added roughly +1.5-2 ms CPU and ~+1.2 M triangles (shadow passes with the extra lights/post) at size 11. Smaller ortho sizes cut cost via culling.
Memory: Unity process RSS ~451 MB; runtime texture memory 628 MB, graphics driver 575 MB, Mono heap 130 MB. The Profiler's "total allocated" counter read ~18.5 GB and was falling; it does not match the process RSS and is **not trusted** (probably left over from the GPU lightmapper). No lightmap memory in the final scene.
Not measured: sustained frame time, a player build, lower-end GPUs, moving combat.

## Not verified
- Recommended camera in actual moving combat (only frozen poses).
- Cyan preview in a full encounter (unfreezing, hit/miss resolution, enemy death, restart).
- Any lightmap result. Any build.

## Decisions needed
1. Accept probes-only GI for now, or commission clean lightmap UVs / GI proxies from the Environment Artist.
2. Allow editing the shared PC_Renderer for SSAO, or keep it out.
3. Accept scene-local cyan telegraph as the reference for a later real-script change.
4. Rim/outline treatment for the Paladins, and surrounding skirt geometry.
5. OK to install Rosetta (CPU lightmapper) for further baking tests.

## Files
`Assets/ArtTest/Reviews/Phase1/` (camera comparison), `Phase2/cam_final_*` (final-lit variants), `Phase3/best_gameplay_size9_windup35.png` / `windup95.png` and `Phase2/cam_final_size9_RECOMMENDED.png` (70 % windup) = best result; `Phase3/baked_05_probes_only.png` = first probes-only frame, `Phase3/dbg_*` and `lightmap_*` (failed lightmap evidence).
Code: `Assets/ArtTest/Editor/ArtTestLighting.cs`, `ArtTestHarness.cs`; `Assets/ArtTest/Scripts/ArtTestCameraFocus.cs`, `ArtTestCyanTelegraphPreview.cs`. Lighting assets: `Assets/ArtTest/Lighting/`.

# Temple courtyard — Unity art-test validation report

Scene: `Assets/Scenes/ArtTest_TempleCourtyard.unity` (copy of PrototypeArena with the greybox `Arena` replaced by the courtyard).
Unity 6000.6.7f1, URP 17.6, Linear, Apple M5, Editor Game view 1920x1080.
Status: **review only. Nothing promoted to `Art/Exports/Environment/Review/`, nothing committed.**

## Verified in Unity
| Check | Result |
|---|---|
| Import | 21 FBX / 71 PNG copied (not moved) from `Staging/` to `Assets/ArtTest/Environment/`. Staging untouched. |
| Scale / rotation | All FBX root scale 1, rotation 0, importer scale 1. 1 unit = 1 m. Stairs 3.98x0.96x1.99, Wall_B 4.0x3.0, Pillar_A 6.39 m, Arch span 8.5 m wide / 8.83 m high. |
| Pivots | Footprint-centre / bottom-on-floor confirmed (min y ~ 0; floor tile y 0..0.30, placed at y -0.30 -> walking surface y = 0). |
| **Axis (blocking test)** | Stairs high end lands on **-Z** at yaw 0 (mean z of high verts -0.69 vs low +0.15). Wall_B relief panel (z>0.52: 7901 verts vs 1393) lands on **+Z**. => local front = **-Z** => **use `yaw_front_to_minusZ`**. |
| Yaw column check | Wall at z=+20 (yaw 180) and x=+20 (yaw 270) both show the relief to the room interior. Stairs at yaw 135 point the high end at the dais. Altar/platform/stairs seat cleanly (altar base y 0.80 = platform top 0.81). |
| Placement | 462 table rows -> 460 instances (3 arch rows share one FBX origin, merged to one). Scene tris 2,566,350 = Blender figure (2.57 M). |
| Materials | 23 external URP Lit materials in `Assets/ArtTest/Environment/Materials`, remapped on the FBX importers. Base sRGB, Normal as Normal map, Mask linear in Metallic and Occlusion slots, smoothness = Metallic alpha. Altar + Brazier emission amber, intensity 1.5, reads amber (not white/cyan) in captures. |
| Collision proxies | 57 colliders: one ground slab, wall/platform boxes, 4 stair steps, pillar/brazier/drum capsules, arch pier boxes, altar box. None for floors/banners/rubble. |
| Clear zone | No proxy except the ground within r = 10 m; nearest = Pillar_D at **11.71 m**. |
| Gameplay camera | Orthographic, size 11, offset (12, 18, -12), euler (46.69, 315, 0) read live in Play Mode. |
| Console | 0 errors / 0 warnings after the Play Mode run. Compile clean. |

## Findings / failures
1. **Cyan telegraph fill is effectively invisible on the floor** (#27DCD1 at 25 %). Only the #9BFFF6 edge reads. The existing orange/red gameplay telegraph fill reads strongly. Confirms the Blender-notes prediction. Needs a decision (fill opacity, floor value/saturation in the combat zone, or a stronger edge/inner stripe).
2. **Arch clear opening is 4.2 m** (inner pier faces at x = +/-2.10), not the 5 m stated in the kit notes. Overall 8.5 m is correct. Check whether 5 m was intended.
3. **Floor grout lines are high contrast** at gameplay-camera scale (dark grid across the whole combat floor). This competes with actors and the telegraph edge; Art Bible says the floor should be quieter than actors.
4. Player and enemy (both dark Paladin meshes) are small and low-contrast against the tan floor at ortho 11; they overlap when engaged.
5. Far-side landmarks (dais, arch) are mostly out of frame from the spawn point (as the kit notes warned). Camera/composition question.
6. Altar mesh imports at 79,340 tris vs 79,542 in Blender (-0.25 %); the notes' 8 % loss was a Blender round-trip figure and does not reproduce in Unity.
7. Stair collision is an approximation (4 steps of 0.2 m); the real step count was not measured. Not walk-tested.

## Performance (Editor, not a build; indicative only)
| Metric | Value |
|---|---|
| Draw calls (Editor stats, incl. shadows) | ~1,900-2,000 |
| SetPass calls | 55-56 (SRP Batcher on) |
| Triangles rendered per frame | ~7.7-8.3 M (incl. 4-cascade shadow passes, 1,177 shadow casters) |
| Frame time | CPU 2.2-3.1 ms, GPU 3.8 ms (one sample) on Apple M5; vsync off |
| Process memory | allocated 631 MB, reserved 1.92 GB |
| Texture memory (71 maps, runtime size reported by the Profiler) | ~415 MB (Editor figure; unverified against a player build) |
| Mesh memory | ~46.5 MB |
Not measured: sustained frame time over time, a player build, lower-end hardware. GPU number is a single sample.

## Not tested
- Player build / platform memory. Texture compression quality. Lightmap bake (nothing baked; lighting is the existing directional light + trilight ambient). Reflection probes. Walk-through of every proxy collider. Colour-vision-deficiency / greyscale telegraph test.

## Decisions needed (Creative Director)
- Telegraph fill strategy (finding 1).
- Floor contrast / grout (3) and actor contrast (4).
- Arch opening width (2).
- Texture budget (~213 MB PNG, 2.57 M tris) and Git LFS before any bulk work.
- Lighting direction (placeholder light only; Q12).

## Files
- Builder: `Assets/ArtTest/Editor/ArtTestCourtyardBuilder.cs` (re-runnable)
- Screenshots: `Assets/ArtTest/Reviews/` (`gameplay_camera_telegraph.png` is the actual gameplay camera)

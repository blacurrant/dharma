# ENV_Temple_Central_Medallion — v4 (masonry + high-poly relief bake)

Status: staged for review. Does NOT replace `Staging/Medallion/` (v3 untouched).

## What it is
- 35 separate stone blocks: centre stone + rings of 6 / 8 / 20 voussoirs, 2 cm joints over a recessed bed, chamfered and chipped arrises, per-block settling (±3 mm offset/tilt).
- Carving: basin + plinth rings, 4 emblem roundels (spiral, interlocked rings, broken labyrinth, S-scroll), 124 incised archaic glyphs in two rows, running-scroll band, 6 fractures, 10 spalled patches incl. a broken rim chunk.
- Diameter 7.80 m, top ~0.09–0.11 m, outer lip 0.015 m. Pivot at centre, base at 0.

## Pipeline
`Art/Blender/Revisions/medallion_v4/scripts/`: `v4_maps.py` (4096 planar heightfield, 1.93 mm/px) → `v4_build.py` (5,594-tri low poly; 2.55M-tri high-poly grid at 7 mm; Cycles tangent-normal bake high→low; compose; FBX; re-import check) → `v4_render.py` (look-dev).

## Files
- `Models/ENV_Temple_Central_Medallion.fbx` (Y-up, -Z forward, bake_space_transform)
- `Textures/*_BaseColor.png`, `*_Normal.png` (OpenGL/Unity), `*_Mask.png` (URP: R metallic 0, G AO, B 0, A smoothness), all 2048
- `Previews/` Cycles look-dev (Unity URP will differ)

## Limits
- 5,594 tris — above the 2–4k brief (v3 was 5,952). Decimation possible, at the cost of block bevels.
- UVs are planar top-down; wall faces sample a small joint-stone patch in the texture corner (walls are 1.5–8 cm tall, mostly hidden in joints).
- AO is heightfield cavity AO; the Cycles AO bake produced self-shadow noise and was dropped.
- Chamfer edges show slight stair-stepping in extreme close-ups (7 mm high-poly grid); not visible at gameplay camera.
- FBX links BaseColor + Normal only; assign the Mask map in the Unity material.

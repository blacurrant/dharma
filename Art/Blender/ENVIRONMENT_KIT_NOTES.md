# Temple Environment Kit — Prototype Notes (Milestone 1)

**Status:** prototype for Creative Director review. **Not approved. Nothing here has been imported into Unity.**
Exports sit in `Art/Exports/Environment/Staging/`; `Review/` is intentionally empty until the Unity import test below passes.
Authoritative direction: `Docs/ART_BIBLE.md` §0 (*Painterly Mythological Fantasy*) and §11.1/§11.3. Palette values are **provisional** (Q11 open).

## 1. Files

| What | Path |
|---|---|
| Master source | `Art/Blender/TempleEnvironmentKit.blend` (Blender 5.2.3 LTS, metric, 1 BU = 1 m) |
| Build scripts (re-run to regenerate everything) | `Art/Blender/Scripts/` — `01_build_geometry.py` → `02_bake.py` → `03_layout.py` → `04_render.py` → `05_export.py` → `06_verify_export.py` → `07_export_placement.py` (`kitlib.py`, `assets.py` = library) |
| Build reports (JSON) | `Art/Blender/Scripts/_build/` (geometry stats, texture manifest, layout/clear-zone report, export verification) |
| FBX | `Art/Exports/Environment/Staging/Models/ENV_Temple_*.fbx` (21 files, 23 mesh parts) |
| Textures (Unity-ready) | `Art/Exports/Environment/Staging/Textures/` (71 PNG) |
| Raw bakes (unfiltered colour, roughness, metallic, AO) | `Art/Blender/Textures/Source/<Part>/` |
| Placement table (Unity Engineer) | `Art/Exports/Environment/Staging/TempleCourtyard_Placement.{json,csv}` (462 instances) |
| Renders | `Art/Blender/Renders/` (`TempleCourtyard_ReviewSheet.png` is the one-page overview) |

The live Blender session was **never used**: all work ran in background Blender processes. The Cozy Desk demo is preserved at `~/BlenderProjects/CozyDeskDemo_backup.blend` (verified), and the live session still holds it unsaved.

## 2. Conventions (prototype — propose/sign off with Unity Engineer, T6/T7)

- **Units/axes:** 1 BU = 1 m; Blender +Z up. Local **front = +Y**.
- **Pivots (baked into mesh; object transforms are identity):**
  - Floor tiles / border tiles: centre of the **bottom face**. Tile top is at local z = 0.30 → place at **y = −0.30** so the walking surface is y = 0.
  - Walls, pillars, arch parts, stairs, platform, altar, props: centre of the **floor footprint**, bottom on the floor plane.
  - Arch is 3 parts sharing one origin: `Arch_A_PierL`, `Arch_A_PierR`, `Arch_A_Span` (opening along X, 5 m clear, 8.5 m overall, 8.8 m high).
- **Naming:** `ENV_Temple_<Piece>_<Variant>`; materials `MI_Temple_<Piece>_<Variant>`; textures `<Part>_{BaseColor,Normal,Mask,Emission}.png`.
- **Grid:** 2 m (tiles 2×2, wall 4×1×3, platform 4×6×0.8, stairs 4×2×0.8, arch 8 m opening width). Module dimensions are 1.98 m etc. because slabs keep a 1 cm joint inset on each side.
- **Collections:** `10_Kit_Pieces/Kit_*`, `20_Props/Kit_Prop`, `30_Test_Layouts/LAY_*` (linked duplicates sharing mesh data; `LAY_Proxies_TestOnly` is never exported).
- **Mesh hygiene:** triangulated on export, no loose geometry, UV set 0 non-overlapping, sharp edges marked, no scale/rotation on kit objects.

## 3. Materials and texture maps

Procedural node shaders (`SRC_Temple_*`, kept in the .blend with fake users) were **baked** to PNG; no node networks are exported.

| Map | Content | Import |
|---|---|---|
| `_BaseColor` | albedo with painterly (Kuwahara) pass; no baked directional light | sRGB |
| `_Normal` | tangent-space, OpenGL (+Y) from baked bump | Normal map (linear) |
| `_Mask` | **R = metallic, G = occlusion, B = 0, A = smoothness** (URP Lit friendly) | linear; assign to *Metallic map* (smoothness source: Metallic Alpha) **and** *Occlusion map* (reads G) |
| `_Emission` | Altar_A and Brazier_A only; warm amber (~22° hue), never cyan | sRGB, HDR emission colour/intensity set in Unity |

Material families inside each atlas: warm stone, charcoal stone (repairs/accents), bronze, antique gold (small accents only), crimson cloth, ember (emissive). Metal/non-metal separation lives in the Mask map. Weathering causes: edge chipping/chalking (bevel-driven), crevice grime (occlusion-driven), rising damp at piece bases (height-driven), localized cracks, sun-bleached tops. Floors are deliberately low-contrast (§3.2 rule 3).

**Texel density (prototype evidence, not a lock):** 145–460 px/m on most pieces; `Arch_A_Span` is lowest at 92 px/m. The gameplay camera shows ≈ 49 px/m on a 1080p screen (22 m visible vertically), so all pieces are ≥ ~1.9× oversampled at the current camera. Resolutions: 512–2048. Total staged textures ≈ 210 MB (PNG) — **reduce** (crunch/compression, lower floor/wall res) once Q6/Q10 settle.

## 4. Geometry budget (prototype, Q10 open)

Unique kit ≈ 516 k tris. **Composed courtyard (462 instances) ≈ 2.57 M tris**, dominated by walls (≈ 950 k) and border strips (≈ 543 k). That is heavy for a single room; see §8 for recommended reductions.

## 5. Courtyard (`30_Test_Layouts`)

Authored in Unity coordinates, then mapped to Blender as `(x, y_up, z) → (x, z, y_up)`.
Floor ±20 m (18×18 tiles + 2 m border ring), walls inner faces ±19.5 m, height 3 m. Far side = −X/+Z:
- Dais: 2× `Platform_A` + `Stairs_A` + `Altar_A` centred (−13.8, 0, 13.8), front facing the arena centre; altar focal point with ember core.
- Arch in the +Z wall at x = 4 (opening 0…8). Pillars: A (−15, 4), B (−4.5, 14.5), C (8.5, 14); **D (broken stump, 3.7 m) on the near side** (−2, −12.5).
- Braziers (4), banners (4), rubble/drum (5).
- **Clear-zone check (numeric, plan view):** 62 non-floor instances tested against the r = 10 m zone; **none inside**; nearest = `Pillar_D` at **11.46 m**; stairs 14.5 m; dais 16.5 m. Floor tiles are the only geometry inside the zone.

## 6. FBX export (verified at file level and by round-trip, **not in Unity**)

Settings: `axis_forward=-Z, axis_up=Y, apply_scale_options=FBX_SCALE_ALL, bake_space_transform=True, use_triangles, use_tspace, path_mode=RELATIVE (../Textures/), embed_textures=False`.
File-level check (`io_scene_fbx.parse_fbx`): UpAxis = Y, UnitScaleFactor = 100 (1 unit = 1 m), every Model has loc 0 / rot 0 / scale 1, bottoms at y = 0, dimensions and pivots match the source for **21/21 assets**. Triangle counts match except `Altar_A` (73,019 vs 79,542; the importer dropped ~8 % degenerate faces).
**Known export limitations:** the FBX references only BaseColor + Normal (+ Emission on Altar/Brazier). **Mask maps are not linked in the FBX** — the Unity Engineer assigns them. Blender shader nodes do not export.

## 7. Unity integration — first checks

1. **Axis/orientation test (T6, blocking):** import `ENV_Temple_Stairs_A.fbx` and `ENV_Temple_Wall_B.fbx`. Stairs' high end and the wall's relief panel define local axes (high end = Blender +Y; panel = Blender −Y). Confirm scale 1 / rotation 0 and which of Unity +Z/−Z the front lands on. The placement table gives **two yaw columns** (`yaw_front_to_plusZ`, `yaw_front_to_minusZ` = +180°); positions are identical.
2. Build URP Lit materials per §3 (Mask in both slots), emission on Altar/Brazier.
3. Floors: 400 instances → GPU instancing/static batching; consider merging per region.
4. Collision: not authored. Suggested proxies: boxes for walls/platform/stairs steps, capsules for pillars/arch piers/braziers, none for rubble/banners.
5. Occlusion: tall pieces are on the far side by design; near-side pieces are ≤ 3.7 m.
6. Do not edit `PrototypeArena`; use a separate art-test scene (T20).

## 8. Limitations / honest gaps

- **Not verified in Unity** (import, materials, lighting, collision, performance).
- Blender renders (EEVEE) are not Unity URP renders. Lighting, tonemapping and exposure are my look-dev guesses (Q12 open). No atmospheric haze/shafts yet.
- **Gameplay-camera framing:** with the player at the origin the camera sees only ≈ 15 m of the ground forward, so the far-side landmarks are mostly *out of frame* at the start position; they appear when the player moves toward them (`gameplay_dais.png`, `gameplay_arch.png`). This is a camera/composition question for Q2, not something the art can fix.
- Telegraph/player/enemy in renders are **proxies** (cyan-teal sector per §4.3.1, simple figures). In greyscale the telegraph **edge** carries the shape; its 25 % fill barely lifts luminance on the light floor (as §4.3.1 predicts).
- Player and enemy colours are undecided, so character-vs-floor contrast is only indicative.
- Weathering is subtle and the palette fairly even; structures read richer than the floor but the room still looks uniformly tan. Palette roles (Q11) should drive a second pass.
- `Platform_A`/walls/stairs use the same stone family; no trim sheets (Q3 open).
- Banner cloth is a closed thin mesh (not double-sided shader dependent). Rubble uses procedural hull stones, not sculpted.
- Heavy: 2.57 M tris courtyard; ≈ 478 MB of uncompressed `Art/` content is untracked (Q8, Git LFS undecided). Nothing is committed.
- Several pieces were found/fixed during QA (stone checkerboard on the floor, white emissive blow-out, UV fragmentation); scripts encode the fixes.
- Blender's Metal GPU baker crashes intermittently while compiling kernels; `02_bake.py` is resumable — rerun until `STAGE2_DONE`.

## 9. Decisions needing Creative Director approval

1. Is the abstract motif set (sun-disc/ring/ray relief, ring-and-ray altar) acceptable as the prototype's celestial language? (No deity/culture/script used.)
2. Floor intent: quiet low-contrast paving (current) vs. more visible worn inlay inside the combat zone.
3. Bronze/gold/crimson amounts (gold appears only on neck rings, studs, one altar band, arch intrados, keystone/relief studs; crimson only on banners and the altar runner).
4. Altar placement at the rear corner dais (current) vs another periphery position.
5. Whether to proceed to bulk production after the in-engine gameplay-camera review.

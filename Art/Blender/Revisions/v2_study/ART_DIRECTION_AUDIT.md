# Environment Kit — Art-Direction Audit and v2 Revision Plan

**Status:** audit + visual study only. **No remodeling started. Awaiting approval (section 8).**
**Scope guard:** `Art/Blender/TempleEnvironmentKit.blend` and everything under `Art/Exports/` were not modified (checksums identical before/after). The live Blender session was not used. All study output is isolated under `Art/Blender/Revisions/v2_study/`. Nothing was exported to Unity.

| Study file | Path |
|---|---|
| One-page study sheet | `Art/Blender/Revisions/v2_study/V2_StudySheet.png` |
| Renders (current / material-only / full study; gameplay + dais close-up, plus no-telegraph passes) | `Art/Blender/Revisions/v2_study/renders/` |
| Isolated working copy (study materials + lighting) | `Art/Blender/Revisions/v2_study/TempleEnvironmentKit_v2_study.blend` |
| Scripts (re-runnable, rebuild kit from deterministic builders) | `Art/Blender/Scripts/study_v2/build_and_render.py` |
| Generated reference (holding folder, **unapproved, not for commit**) | `Art/Blender/Reference/_unapproved_holding/generated_gameplay_reference_2026-10-24.png` |

Inputs used: the generated gameplay reference; the Unity art-test capture and report (`Assets/ArtTest/Reviews/`); Blender renders; placement table; geometry/texture stats.

---

## 1. What the reference teaches, and what not to take

**Take (principles):** irregular, varied-size flagstones with real cracks and height variation; a strong raking key with long cast shadows that carve form; layered depth (foreground framing at corners, steps at the edges, vegetation creeping in); clear material contrast (stone vs cloth vs metal vs fire); a lit centre with darker, richer edges; lived-in storytelling (collapse, overgrowth, debris concentrated at the perimeter).

**Do not copy:** the gold circle/star motif on the floor (a mandala/sun device; it also competes with telegraph shapes), the lion statue (figurative, needs Creative Director approval and carries real-world iconography), the orange/saffron dominance, or leaves scattered over the combat floor (high-frequency noise where the Art Bible wants calm).

## 2. Findings that change the plan

1. **The current kit leans on a sun/ring motif, which now conflicts with the direction.** About 100 instances carry it: 12 `Wall_B` panels, 4 `Pillar_B` faces, 4 arch pier panels + 2 keystone reliefs, 4 corner borders, 72 border studs, and the altar (sun-disc with 16 rays + gimbal rings, which also reads as a gear/astrolabe in Unity). **These are modelled geometry; textures cannot remove them.**
2. **The palette is sand/tan** (stone mid `#756850`, saturation ~30 %). Unity shows it as a uniformly tan room.
3. **Lighting is front-lit and flat.** My original sun travels with the camera (about 0.45 alignment with the view direction), so form is flattened and shadows fall away from the viewer. This is partly my error in the look-dev; Unity's placeholder light is also flat.
4. **The floor is a regular orthogonal 2 m grid** (324 tiles, only 4 variants, slab heights within ±4 mm). Joints are open 2 cm slots (each slab is inset 1 cm per side), 30 cm deep, so they read as a dark continuous grid. Measured in Unity: grout pixels sit 20–45 % below the slab median (p5 59–82 vs median 105); it is regular enough to compete with actors.
5. **Arch opening error (mine):** my notes said 5 m clear. Measured on the mesh: 5.01 m for the shaft, but the **impost cornice projects inward and narrows it to 4.19 m** at the spring line (z 4.3–4.7 m). Unity's report was right.
6. **Walls: 38 modules, only 2 variants**, identical 4 m runs; charcoal/light course alternation produces zebra banding rather than believable masonry.
7. **Pipeline gap (mine):** after baking I cleared mesh material slots, which reset the per-face material zones (stone/bronze/gold/cloth). Future material revisions cannot read zones from the saved `.blend`. Fix before any remodel: store zones as a persistent integer mesh attribute.
8. **Telegraph:** measured with identical pixels rendered with/without the cyan proxy (sRGB luma). Fill lift: current **0.049**, material-only **0.078**, full study **0.070**. The edge reads (+0.25 to +0.33). Darker, quieter floor helps, but the 25 % fill stays faint; this still needs a telegraph-side decision (Q21: fill opacity or an inner stripe), not just art.

## 3. Asset audit by category

Cost key (my estimates, not measured): **S** < ½ day, **M** 1–2 days, **L** 3+ days, each including UV, bake, export and verification.

### Floor (`Floor_A–D`, `FloorBorder_Straight_A`, `FloorBorder_Corner_A`; 324 + 76 instances)
- *Working:* quiet value (std 12–14 in clear patches), correct pivots, 2 m module, clear zone intact.
- *Generic/flat/noisy:* regular grid and grout; tiny variant set; no settlement, no cracks across joints, no path-driven wear, no edge encroachment; straight border = a row of 72 identical studs; corner border = ring-and-ray.
- *Material/layout fixes (no remodel):* mortar underlay (one plane under the tiles; shown in study), lower and desaturate floor, per-tile hue/value drift, damp-sheen patches, moss only in joints and edges. Per-tile 90° rotation already used.
- *Geometry changes:* irregular flagstone variants (3–6 stones per 2 m with ±1–2 cm height and slight tilt, cracks crossing joints), border redesign without studs/ring.
- *Obstruction/collision:* none; keep a single ground collider, floors are visual only.

### Walls (`Wall_A`, `Wall_B`; 38 instances)
- *Working:* strong readable perimeter, stepped top silhouette, 3 m height, collider-friendly.
- *Generic:* running-bond regularity, uniform tops, no collapse or gaps, no buttresses, zebra course banding, repeated Wall_B sun panel.
- *Material:* reduce course banding, add rain streaks, moss, base staining, per-instance value shift (all shown in study).
- *Geometry:* replace the Wall_B relief; add broken-top, buttress, niche and corner variants.
- *Collision:* box proxies are enough.

### Pillars (`A` fluted, `B` square with relief, `C` octagonal with bronze coil, `D` broken)
- *Working:* four distinct silhouettes; D's fractured top and C's coil are the strongest ideas.
- *Generic:* A is a plain Doric look; banded dark/light drums; slab capitals; all plumb and 6.3 m tall; B carries the sun relief.
- *Material:* base staining, moss, wash streaks; reduce banding.
- *Geometry:* B relief out; swap-able base/shaft/capital modules would give far more variation for little cost; add a leaning/cracked shaft.
- *Obstruction:* tall pillars must stay on the far side (as placed); near-side pieces ≤ 3.7 m.

### Stairs and platform (`Stairs_A`, `Platform_A`)
- *Working:* clear dais step-up, correct 0.2 m rises; reads in Unity.
- *Generic:* flat-top 2×3 slabs, no worn treads, no chipped corners, no collapsed edge, treads look thin in close-up.
- *Material:* wear/moss covers some of it. *Geometry:* worn/dished treads, one broken step, plinth moulding, a collapsed platform corner.
- *Collision:* stairs approximated by 4 box steps in Unity; recommend a ramp collider for gameplay smoothness.

### Arch (`Arch_A` PierL/PierR/Span)
- *Working:* monumental landmark, convincing voussoirs and keystone.
- *Generic/flawed:* impost cornice intrudes (4.19 m clear at spring line); gold intrados band + keystone/pier sun reliefs; perfectly symmetric, clean.
- *Material:* moss and streaks help. *Geometry:* fix the cornice (small), remove gold band and reliefs, add a partly collapsed variant.
- *Collision:* pier boxes; do not collide the span.

### Altar / central structure (`Altar_A`)
- *Working:* the dais + steps + flanking braziers set up a clear focal point; ember core is a good selective glow.
- *Generic/flawed:* symmetric; the radial-ray ring reads as a sun/gear; gimbal rings feel steampunk; the pad-and-steps dais is the most generic part.
- *Material cannot fix this.* Needs a redesign (section 5); asymmetric silhouette and a story (collapse, pull, fracture).

### Props (`Brazier_A`, `Banner_A`, `Rubble_A/B`, `ColumnDrum_A`)
- *Working:* braziers give light pools and warm accents; ColumnDrum and Rubble add scale/story.
- *Generic:* 4 identical braziers; 4 identical flat banners (rigid); rubble = convex hull "boulders" with no flat faces or mortar remnants; flame is an emissive mesh, not fire.
- *Obstruction/collision:* braziers 1.3 m are fine outside the zone but must not sit on the near side; banners and rubble are non-colliding. Keep all rubble ≤ 0.5 m high near the ring.

## 4. What the study shows (materials + light only; geometry untouched)

Same courtyard, same camera (ortho 11, offset 12/18/−12), three looks (see `V2_StudySheet.png`).

| | A current | B material only | C full study |
|---|---|---|---|
| Palette | tan (`#756850` mid) | desaturated warm grey (`#635E52`) | same + cool fill, warm raking key |
| Floor luma under telegraph fill | 0.38 | 0.31 | 0.35 |
| Telegraph fill lift | 0.049 | 0.078 | 0.070 |
| Telegraph edge lift | 0.25 | 0.33 | 0.27 |
| Light | front-lit sun 52° | same | key from far side 34°, long shadows toward camera, haze, mortar underlay |

**Visible gains:** moss and damp sheen in the joints, rain-wash streaks on walls and pillars, per-piece value variation, a calmer floor, depth from haze, form from the raking key. **Not fixed by this (still visible in the study):** the ring/sun reliefs, the regular grid shape of the floor, wall zebra banding in the silhouette, the symmetric altar, rigid banners.

**Honest limits of the study:**
- It is procedural shading rendered in Cycles, not baked Unity textures; the final painterly quality depends on the bake + a hand-painted pass (the Kuwahara filter is a stand-in).
- The haze is a bounded box in Cycles; Unity fog will differ (an infinite Cycles world volume black-holed the render, so I changed approach).
- The close-up haze is slightly milky and **crimson reads weakly** in the dais close-up; needs another tuning pass.
- Raking shadows pool darkly on parts of the floor; the telegraph must be validated inside shadow (not tested).
- Palette hexes are proposals, not locked (Q11).
- Moss/lichen uses olive hues (about 80°). **Verdigris is deliberately avoided: teal is reserved for telegraphs.**

## 5. Prioritized change list

### 5.1 Material and texture revisions (rebake all parts; ~20 min machine time + tuning)
| # | Change | Visual benefit | Cost |
|---|---|---|---|
| M1 | Shift stone from tan to desaturated warm grey, value-separate floor vs structure | Removes the "sand room"; floor sits behind actors | S–M |
| M2 | Joint-aware mortar/earth value (match the mortar underlay) | Kills the dark-grid look | S |
| M3 | Moss/lichen in crevices and damp lows; streaks below ledges; sheen patches on floor | Cause-driven richness | M |
| M4 | Fewer charcoal courses, per-instance value shift | Less zebra banding, less repetition | S |
| M5 | Brighter crimson cloth, muted aged brass instead of bright gold | Restrained accents that still read | S |
| M6 | Persist material zones as a mesh attribute before baking | Enables every later revision | S (pipeline) |

### 5.2 Existing mesh revisions
| # | Change | Visual benefit | Cost |
|---|---|---|---|
| G1 | Fix arch impost cornice (clear opening 5.0 m at all heights) | Correct gate silhouette and gameplay width | S |
| G2 | Remove all ring/sun reliefs (Wall_B, Pillar_B, arch piers/keystone, border studs/corner) and replace with abstract weathered fractures or blank cartouches | Meets the new direction | M |
| G3 | Remove gold intrados band; stair and platform wear (dished treads, chipped corners) | Less ornate, more lived-in | S–M |
| G4 | Pillar capital variety + leaning/cracked shaft; split base/shaft/capital modules | More silhouettes from few meshes | M |
| G5 | Altar redesign (see 5.3) | Distinct central identity | L |

### 5.3 New modular environmental assets (proposed list, nothing modelled)
| Group | Assets | Benefit | Cost |
|---|---|---|---|
| Floor | `Floor_E–H` irregular flagstone, `Floor_Cracked`, `Floor_Sunken`, `FloorEdge_Broken` (earth/moss lip), `Threshold_A` worn slab | Breaks the grid, adds history | M each pair |
| Walls | `Wall_C_Broken`, `Wall_D_Buttress`, `Wall_E_Niche` (abstract recess), `Wall_Corner_A`, `Wall_Cap_A`, `Wall_Plinth_A` | Silhouette variation along the perimeter | M |
| Pillars | `Capital_A/B`, `Shaft_A/B/C`, `Base_A/B` as swappable modules | 3×3×2 combinations | M |
| Stairs | `Stairs_B_Broken`, `Stairs_C_Wide`, `Retaining_Wall_A` | Entry/ruin variety | M |
| Arch | `Arch_B_Collapsed`, `ArchFragment_A` | A ruin landmark | M |
| Central structure | `Monolith_A_Split` (asymmetric, ember seam), `Basin_A` offering bowl, `Plinth_A` | Replaces the ring/gear with a stronger silhouette | L |
| Structure storytelling | `FallenLintel_A`, `SlabLean_A`, `Cairn_A`, `CisternRim_A` | Collapse and use, not decoration | S–M each |

**Central-structure options (needs your choice; none uses sun, mandala or figure):**
1. Split monolith with an ember seam and a basin at its foot (recommended: strongest silhouette, simplest collision).
2. Cairn of stacked slabs under a half-collapsed lintel canopy.
3. Vaulted niche or cenotaph with a crimson drape.
A figurative statue would need explicit Creative Director approval (Art Bible §11.1).

**Architectural vocabulary (proposal only, not a mythology decision):** battered (inward-leaning) walls, corbelled/stepped arches, heavy post-and-lintel, cantilevered slabs, fracture lines as the only decoration.

### 5.4 Small set-dressing props
`Rubble_C–F` (flat-faced broken blocks with mortar remnants), `Banner_B` tattered and `Banner_C` hung from a beam, `Brazier_B` (low stone), offering clusters (low), urn/jar variants, hanging chains. **Keep out of the combat zone and off the near side:** anything above 0.5 m inside the ring edge, hanging cloth on near walls, leaf/debris piles on floor. Collision: only pillars, braziers and the central structure; everything else visual only.

### 5.5 Unity-side, no Blender work
Raking key light and soft shadows; cool fill/ambient; height fog or volume haze; light shafts and dust motes (particles); falling-leaf particles away from the combat zone; real fire VFX for braziers; floor decals (cracks, damp, moss) and vegetation cards; smoothness-driven wet sheen; reflection probes; tone-mapping grade; near-side wall fade; telegraph shader. **Validate every telegraph in shadow and in greyscale after relighting.**

## 6. Reuse without changes
Material-only updates are enough for: `Floor_A–D` (as filler once the mortar underlay and variants exist), `Wall_A` (as the quiet filler run), `Pillar_C`, `Pillar_D`, `ColumnDrum_A`, `Rubble_A/B`, `Platform_A`, `Stairs_A`, `Brazier_A`, `Banner_A`. **Geometry must change:** `Wall_B`, `Pillar_B`, `Arch_A` piers + span, both border pieces, `Altar_A`.

## 7. Suggested order
1. **Before any remodel:** M6, then re-light in Unity and re-check readability (needs the Unity Engineer), because the lighting review decides whether geometry changes are needed at all.
2. M1–M5 rebake + G1 + G2 (motif removal), then re-review.
3. First asset tranche (8 pieces): `Floor_E–H`, `Wall_C_Broken`, `Wall_D_Buttress`, `Wall_Corner_A`, `Monolith_A_Split` + `Basin_A`.
4. Only then props and the remaining variants.

## 8. Decisions needed before substantial work
1. Approve removing the ring/sun motif everywhere (about 100 instances), and the neutral architectural vocabulary above.
2. Choose the central-structure option (1/2/3), or request a different direction.
3. Approve the desaturated warm-grey stone direction (and that moss stays olive, not teal).
4. Telegraph fill strategy (Q21): fill opacity, inner stripe, or darker combat-zone floor.
5. Lighting ownership: Unity Engineer to try the raking-key setup first?
6. Budget stance (still open): 2.57 M tris and ~210 MB PNG per kit; I recommend tileable trims plus decals for walls/floors instead of unique 2048 atlases once Q3/Q10 settle.

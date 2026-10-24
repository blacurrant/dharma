# MythicRoguelite — Art Bible

**Status:** Draft v0.3 — environment style **LOCKED** (§0); telegraph colour, prototype scope and asset-folder structure **resolved** (§0.9); exact palette values, texture workflow, camera parameters and prototype details remain open (§12).
**Owner:** Creative Director (Nishant) · **Maintained by:** Game Director · **Primary users:** Environment Artist, Unity Engineer

> **Precedence.** **§0 is the authoritative environment style.** If any other section of this document, `GAME_BRIEF.md`, `TECHNICAL_OVERVIEW.md`, or `Art/README.md` conflicts with §0, §0 wins and the other text must be corrected.
>
> **Tags.** **[LOCKED]** a decision made by the creative director that is final unless the creative director reopens it · **[CONFIRMED]** stated by the creative director · **[OBSERVED]** read from the current project · **[RULE]** a working rule derived directly from a confirmed pillar (changes only if the pillar changes) · **[OPEN]** undecided — do not fill in by assumption. Open items are consolidated in §12.
>
> **Placeholder warning.** All colours, materials, and meshes currently in the project are greybox/prototype stand-ins. They are **not** the art direction.

---

## 0. Authoritative environment style — Painterly Mythological Fantasy **[LOCKED]**

**The primary environment style for MythicRoguelite is _Painterly Mythological Fantasy_.** This is the authoritative environment style. All environment work is judged against this section first.

A fully 3D action roguelite with an elevated three-quarter overhead camera. The visual ambition combines the detailed 3D presentation, atmospheric environments and monumental architecture of high-quality dark-fantasy ARPGs with the responsive, readable, small-scale combat philosophy of *Hades*.

### 0.1 Architecture **[LOCKED]**
- Grounded, monumental, believable structures.
- Weathered temples, carved stone pillars, massive arches, worn stairs, altars, statues and carefully composed courtyards.
- Strong large-scale silhouettes and architectural landmarks.
- Original mythological identity. Do not copy another game's assets or distinctive designs.

### 0.2 Surface treatment **[LOCKED]**
- Rich painterly 3D materials: sculpted forms, visible material variation, nuanced roughness, carefully authored weathering.
- Stone feels ancient and substantial. Metal has convincing material separation (clearly distinct from stone, cloth and wood in colour, roughness and metallic response).
- **Avoid:** generic AI-generated surface noise · excessive grunge · uniformly smooth materials · a generic low-poly appearance.
- Ink-like details may be used **sparingly** for inscriptions, supernatural effects or decorative accents. **Ink-wash is not the primary rendering style.**

### 0.3 Colour and lighting **[LOCKED]**
- **Palette direction:** muted warm stone, charcoal shadows, antique gold, bronze, restrained crimson.
- **Lighting:** cinematic warm directional lighting, controlled contrast, atmospheric depth.
- **Selective emissive** details for sacred or supernatural elements.
- Preserve visibility and contrast for player characters, enemies, attacks and enemy telegraphs.
- **Avoid:** making every room excessively dark; saturating every material with gold.

### 0.4 Gameplay composition **[LOCKED]**
- Elevated three-quarter view of a fully 3D world.
- Distinctive foreground, midground and background.
- Clear combat spaces surrounded by dramatic architecture.
- Props and architectural silhouettes must not obscure the player or critical telegraphs.
- Reusable modular assets plus handcrafted compositions — **not** one monolithic environment mesh.

### 0.5 Production rules **[LOCKED]**
- Blender source files stay separate from Unity-imported assets.
- Environment assets are exported into the approved `Assets/Environment/` destination (structure: §0.9).
- Establish consistent scale, pivots, naming conventions, materials and collision conventions before bulk production.
- **Create and review one environment art prototype before producing a large asset library** (gate defined in §11).
- Evaluate screenshots through the **actual gameplay camera**, not only close-up renders.

### 0.6 How this section is applied (derived rules) **[RULE]**
| Locked statement | Practical consequence |
|---|---|
| Avoid generic low-poly | Silhouette, bevels, and medium-scale sculpted forms (block edges, carved relief, chips, sagging) are modelled or normal-mapped, not left as flat boxes. Budgets (Q10) must be set high enough to allow this. |
| Nuanced roughness; metal separation | Materials must carry authored roughness variation and a clear metal/non-metal distinction. A flat single-roughness material is a review failure. |
| Painterly, visible material variation | Albedo shows hand-authored colour variation and brushwork-like transitions on large forms; variation follows form and use. |
| Avoid AI-generated noise / excessive grunge | Surface detail must be traceable to a cause (use, water, soot, structural stress, repair). Random overlay noise and uniform dirt layers are rejected in review. See §3.2. |
| Ink-wash not primary | Ink-like elements are limited to inscriptions, supernatural effects and accents. No scene-wide ink/outline post-process that makes the world read as ink-wash. |
| Preserve visibility of actors and telegraphs | The readability hierarchy in §8 outranks every aesthetic rule in this section when they conflict. |
| Not every room dark; not everything gold | Vary mood and value range between rooms. Antique gold and bronze are used as accents and hierarchy, not as the base material. |
| Foreground / midground / background | Foreground framing elements sit **outside** the combat footprint or are low/transparent/cut away; the combat space is the midground. Technique for occlusion is open (Q2). |
| Modular + handcrafted | Kit pieces are reused; each arena is hand-composed from them, with unique hero pieces (statues, altars, arches) where they add landmarks. |

### 0.7 Not changed by the lock
The reference-use rule in §1 still applies (no assets copied, traced, or lifted from another game).

### 0.8 What remains open after the lock
The lock fixes the *direction*. It does **not** supply the following, which stay **[OPEN]** and must not be invented:
- Which mythology / culture / region the architecture derives from (Q1). The architectural *typology* is locked; its cultural *vocabulary* is not.
- Exact palette values (hex/linear) for each role (Q11).
- Texture workflow details: hand-painted vs PBR-authored vs hybrid, trim sheets vs unique textures, resolutions (Q3, Q10).
- Whether any outline/rim/ramp shader is used at all (Q3). If used, it must not make the world read as ink-wash.
- Camera projection, pitch, FOV/zoom (Q2).
- Post-processing and baked vs real-time lighting strategy (Q12).
- Exact colour values, including the exact telegraph cyan-teal (Q11, Q18).
- Telegraph specification details beyond the locked requirements, and how the combat-script implementation is authorised (Q18).
- Subject, iconography and ornament vocabulary of the prototype's altar/statue/arch (Q19, depends on Q1).
- Dimensions of the prototype courtyard and its minimum clear combat space (Q20).

### 0.9 Decisions resolved after the lock **[LOCKED]**
These decisions have the same authority as §0.1–§0.5 and the same precedence over conflicting text.

| Resolved | Decision | Where specified |
|---|---|---|
| **Q15 — telegraph colour** | **Bright cyan-teal** is the combat telegraph colour, chosen for strong contrast against warm stone, antique gold, bronze and crimson. Telegraphs have a clear shape, a readable fill and an animated windup progression. **Colour is never the only danger signal.** | §4.3 |
| **Q16 — environment prototype scope** | One compact, handcrafted **temple courtyard**: worn stone floor and readable open combat space; a short staircase or raised platform; four substantial pillars with deliberate variation; one monumental entrance arch; one central or rear altar/statue as the focal point; consistent painterly materials, weathering and warm cinematic lighting. Evaluated from the actual elevated three-quarter gameplay camera; must preserve player visibility, enemy visibility, telegraph readability and combat movement space. | §11.1 |
| **Q17 — environment asset folders** | `Art/Blender/` (Blender sources, outside `Assets/`), `Assets/Environment/Models/` (exported meshes), `Assets/Environment/Materials/` (Unity materials), `Assets/Environment/Textures/` (texture maps), `Assets/Environment/Prefabs/` (reusable assembled props and architectural modules). The Unity Engineer may propose extra subfolders (collision assets, decals, scene-specific prefabs) when technically necessary. | `TECHNICAL_OVERVIEW.md` §3.5, §5.4 |

**Not authorised by these decisions:** changing combat scripts, scenes, materials, meshes or project settings; creating the `Assets/Environment/` folders; starting any modelling. Each is a separate task.

---

## 1. Direction (confirmed)

- **[CONFIRMED]** Fully 3D mythological action roguelite, elevated three-quarter overhead camera, visual territory of *Path of Exile 2*.
- **[CONFIRMED]** Detailed, stylized fantasy characters and environments.
- **[CONFIRMED]** Grounded architecture, weathered surfaces, painterly material treatment, distinctive silhouettes, deliberate lighting.
- **[CONFIRMED]** Original mythological worldbuilding and visual identity; no copying of another game's assets.

**Reference-use rule [RULE]:** *Path of Exile 2* and *Hades* are references for **camera presentation, readability, and mood**. Do not reproduce their characters, props, architecture shapes, icon designs, or textures. Every environment motif must trace to the project's own mythology (§12 Q1) or to real-world historical/archaeological sources.

**Interpreting "grounded" + "stylized" [LOCKED → §0]:** the target is *Painterly Mythological Fantasy* as defined in §0 — believable, monumental structures with rich painterly 3D materials. It is not a low-poly look and not an ink-wash look. The **texture workflow details** are still open (§12 Q3); until the first environment prototype (§11) is reviewed, the Environment Artist produces blockout, shape language and prototype-scoped materials only.

---

## 2. Environment architecture

### 2.1 What is confirmed / ruled
- **[CONFIRMED]** Architecture is *grounded*: structures should look like they could be built — load paths, thresholds, steps, buttresses, drainage, wear from use — even when the culture is mythic.
- **[RULE]** Because the camera is elevated, **roofs and ceilings are mostly absent or cut away.** Interiors are expressed as open-topped courts, ruins, terraces, and cutaway halls. Vertical elements (walls, columns) must not hide the player or telegraphs (§8).
- **[RULE]** Architecture is **combat furniture first.** Every structure in a combat space is either (a) walkable floor, (b) a blocker the player can plan around, or (c) background. Mixed signals are a bug.
- **[RULE]** Design from the camera. A piece is judged in a review render from the gameplay camera angle (§11), not in a perspective hero shot.

### 2.2 Architectural language
- **[LOCKED]** Typology (§0.1): weathered temples, carved stone pillars, massive arches, worn stairs, altars, statues, carefully composed courtyards; strong large-scale silhouettes and landmarks. `TempleEnvironmentKit.blend` is consistent with this typology.
- **[OPEN]** Culture, period, ornament motifs, regional material choices, and the relationship between sacred and ordinary structures all depend on the mythological premise (§12 Q1). Statues and carvings must not depict real-world cultural or religious figures by assumption, and must not borrow another game's distinctive designs.
- **[OPEN]** Which region is built first, and its identity beyond "temple complex".
- **[RULE]** Monumental scale is expressed through landmarks, arches, and surrounding structures **around** the combat space. The combat floor itself stays sized to combat (§6.4).

### 2.3 Arena composition guidance **[RULE]**
| Concern | Rule |
|---|---|
| Combat space | One clear, continuous walkable floor plane. Floor-height changes inside active combat space are rare and always unambiguous (obvious step/ramp or full wall). |
| Cover / pillars | Used to shape movement and sightlines against dodging. Footprint must be legible as a collider at a glance. |
| Edges | Hazards, voids, and map edges are visually distinct from floor within the first glance; never hidden by shadow or occluder. |
| Dressing | Scatter/props are non-colliding and visually quieter than anything that blocks or hurts. |
| Landmarking | Each arena has at least one distinctive silhouette reading from the camera so the player orients without UI. |

### 2.4 Current state **[OBSERVED]**
`PrototypeArena`: flat 40×40 m floor, four 1.4×1.4×3 m box pillars, four 3 m perimeter walls (cubes), single directional light. No architectural content yet.

---

## 3. Material treatment

### 3.1 Locked intent
**[LOCKED]** See §0.2. Rich painterly 3D materials; sculpted forms; visible material variation; nuanced roughness; authored weathering; ancient, substantial stone; convincing metal separation. Not low-poly. Not ink-wash. Ink-like detail only sparingly.

### 3.2 Working rules **[RULE]**
1. **Wear tells the story, not noise.** Weathering concentrates where use and elements act: edges, steps, thresholds, base of walls (moisture/dirt), top surfaces (sun/soot), mortar joints. Avoid uniform grunge overlays.
2. **Large / medium / small hierarchy.** Large shapes carry the read at gameplay distance; medium detail (blocks, carving, cracks) gives structure; fine detail is subordinate and must not create high-contrast noise on the walkable floor.
3. **Floor is quieter than the actors.** Walkable-floor texture contrast, saturation, and detail frequency stay below that of characters and telegraphs.
4. **Material = function.** Each distinct material family (e.g., floor stone, wall stone, metal, wood, cloth, organic) has a consistent colour/roughness identity so players can learn surfaces.
5. **Consistent texel density** across the kit within a defined band (value **[OPEN]**, §12 Q10).
6. **Painterly treatment must survive a 3D, dynamically-lit pipeline.** Avoid baking directional lighting into albedo; baked shadow/AO is fine as subtle ambient occlusion only.
7. **No anonymous noise (LOCKED, §0.2).** Every weathering mark has a plausible cause. Reject: tiling grunge overlays used as a shortcut, over-dense scratches, uniform dirt, and uniformly smooth/plastic-looking surfaces.
8. **Material families must separate** (stone / metal / wood / cloth / gold-bronze / emissive). Metals read as metal through roughness and metallic response, not just colour.
9. **Gold is an accent.** Antique gold and bronze are used on ornament, inlay, trim and key objects, not as the base colour of whole structures.
10. **Ink-like details** (inscriptions, supernatural effects, accents) are placed deliberately and sparingly and never cover large surfaces.

### 3.3 Decisions that gate the material pipeline
The lock (§0.2) establishes the *look*. The following *production method* decisions remain **[OPEN]**:

| Question | Why it matters |
|---|---|
| Texture workflow: how painterly albedo is authored (hand-painted, procedural-plus-paintover, sculpt-baked, hybrid) while still supplying roughness/metallic/normal data. The lock requires nuanced roughness and metal separation, so the shading model must carry them. | Determines tooling, texture count, and what Blender must export |
| Outlines / rim effects / cel ramps — yes or no. If yes, they must not make the world read as ink-wash. | Needs shader work by the Unity Engineer |
| Trim sheets + tiling vs unique textures per asset | Memory and modularity |
| Vertex-colour/ AO/ edge-wear masks baked in Blender vs authored in Unity | Mesh export requirements |
| Smoothness/metallic policy for stone, metal, wet surfaces | Look and shader choice |

### 3.4 Current state **[OBSERVED]**
- These observations describe the greybox only and do not represent the locked style.
- Prototype materials in `Assets/Materials/Prototype/` (`Ground`, `Wall`, `Pillar`, `Accent`, `Dummy`, `Player`) are flat URP Lit colours, smoothness 0.5, metallic 0. They exist for blockout contrast only.
- Characters use Mixamo textures (diffuse/normal/specular) with a URP Lit, specular-workflow material. The enemy is a recoloured copy with an emission map.
- Colour space is **Linear** (`m_ActiveColorSpace: 1`). Textures that carry colour must be imported as sRGB; data textures (normal, mask) as linear.

---

## 4. Colour palette

### 4.1 Status
**[LOCKED]** Palette *direction* (§0.3): **muted warm stone, charcoal shadows, antique gold, bronze, restrained crimson**, with selective emissive accents for sacred/supernatural elements.

**[OPEN]** No exact values (hex/linear) have been chosen; none are specified here on purpose (Q11). The prototype colours below are greybox placeholders and must not be sampled as direction.

| Prototype material | Serialized `_BaseColor` (RGB) in the `.mat` | Purpose |
|---|---|---|
| Ground | 0.28 / 0.29 / 0.31 | greybox floor |
| Wall | 0.42 / 0.43 / 0.46 | greybox wall |
| Pillar | 0.52 / 0.53 / 0.56 | greybox cover |
| Accent | 0.62 / 0.58 / 0.42 | greybox accent |
| Player (greybox) | 0.35 / 0.48 / 0.62 | superseded by Paladin |
| Dummy (greybox) | 0.55 / 0.30 / 0.30 | superseded by Paladin |

### 4.2 Palette roles **[RULE]** (direction locked; values open)
The palette is defined as **roles**, each with a hue family, value range, and max saturation. The locked direction below constrains which families are in play. The director/art lead fills in the exact values (Q11).

| Locked palette element | Intended use (derived) |
|---|---|
| Muted warm stone | Dominant: floors, walls, pillars, arches, stairs — the bulk of the frame |
| Charcoal shadows | Shadow colour and depth; contrast anchor. Not pure black; must not bury combat-relevant floor |
| Antique gold | Accent: inlay, ornament, key props. Never the base of whole structures |
| Bronze | Mid-value metal accent; separates from stone and gold |
| Restrained crimson | Sparing accent (banners, cloth, ritual detail). See conflict note below |
| Selective emissive | Sacred / supernatural elements only |

| Role | Constraint (rule) | Value |
|---|---|---|
| Walkable floor | Lowest contrast and saturation in the frame; mid-low value. Family: muted warm stone | values **[OPEN]** |
| Structure / walls | Distinct from floor in *value*, not just hue (survives colour-blind and greyscale checks) | **[OPEN]** |
| Backdrop / out-of-bounds | Darker and calmer than playable space | **[OPEN]** |
| Player character | Unique, recognisable colour/value signature that no environment or enemy shares | **[OPEN]** |
| Enemy | Distinct from the player and from the floor; threat read | **[OPEN]** |
| Hostile telegraph / damage zone | A reserved colour family used for nothing else in the world (including props, torches, glow, foliage) | **[LOCKED] bright cyan-teal** (§4.3); exact value **[OPEN]** |
| Safe / interactive / reward | A second reserved family, clearly separate from the hostile one | **[OPEN]** |
| Light accents (fire, magic, divine) | Allowed to be the saturated peaks, but never in the telegraph cyan-teal family (§4.3) | **[OPEN]** (hue choices must avoid cyan-teal) |

**[RULE]** Per-region/biome palettes are variations on the same role system so readability rules transfer between regions.

**[RULE]** Validation: every palette proposal must be tested (a) in greyscale, (b) under common colour-vision-deficiency simulations, and (c) in a gameplay-camera render with player, enemy, telegraph, and floor in the same frame.

> **Q15 resolved (v0.3):** the earlier conflict between the reserved hostile colour and the locked crimson/gold/emissive palette is resolved by choosing bright cyan-teal. See §4.3.

### 4.3 Combat telegraph colour **[LOCKED]** (resolves Q15)

**The combat telegraph colour is bright cyan-teal.** It is chosen for strong contrast against the locked warm palette: warm stone, antique gold, bronze and crimson.

**Locked requirements for every telegraph:**
1. **Clear shape** — the danger area has a defined, readable boundary matching the real hit area.
2. **Readable fill** — the interior is distinguishable from the floor beneath it on every floor material.
3. **Animated windup progression** — the telegraph visibly progresses from start to strike so the player can read remaining time.
4. **Colour is not the only signal of danger** — shape, fill and motion must communicate the threat without relying on hue.

**Derived rules [RULE]** (follow from "reserved colour" in §4.2 and from §8; they add no new creative content):
- The cyan-teal family is **reserved for hostile telegraphs and danger zones.** It is not used for environment materials, props, foliage, water, light sources, sacred/supernatural emissive accents, or friendly/player VFX.
- Because sacred emissive accents may not use cyan-teal, their hue is chosen separately (Q11).
- Telegraphs must separate from the floor in **luminance as well as hue** and are validated in greyscale and under colour-vision-deficiency simulation (§4.2 validation).
- Telegraphs must remain visible under the warm key light, in shadow, and through normal VFX (§8.2).
- Crimson, gold and emissive accents may appear on architecture; combat-floor surface contrast remains limited by §3.2 rule 3 and §8.

**Still open (Q18):** the exact cyan-teal value; fill opacity and edge treatment; shape language per attack type; the windup animation style; any additional non-colour cues beyond shape/fill/motion (for example audio or enemy pose, which are design territory); and how and when the combat implementation is authorised.

**Implementation status [OBSERVED]:** the prototype still telegraphs with an **orange** tint on the enemy (`CharacterTintFeedback`, `TrainingDummy`) and uses an amber slash colour for player attacks. That is prototype behaviour and **stays unchanged**: this decision does not authorise changing combat scripts. Orange/amber is therefore a *current-behaviour* fact, not the intended final telegraph colour. A separate, explicitly authorised task will implement the cyan-teal telegraph.

---

## 5. Lighting

### 5.1 Locked intent
**[LOCKED]** (§0.3) Cinematic **warm directional** lighting, **controlled contrast**, **atmospheric depth**, **selective emissive** details for sacred/supernatural elements. Visibility and contrast of players, enemies, attacks and telegraphs are preserved. Not every room is excessively dark.

**[CONFIRMED]** Lighting is *deliberate*: a design tool for hierarchy, mood, and readability, not just illumination.

### 5.2 Working rules **[RULE]**
1. **Hierarchy of light:** (1) gameplay actors and telegraphs are always readable; (2) the intended path/arena is evenly legible; (3) mood and drama live in the periphery, backdrop, and accent lights.
2. **Shadows serve shape and grounding.** Characters and pillars cast readable contact shadows. Shadow must not obscure telegraphs, edges, or hazards.
3. **No global dark traps.** Darkness may frame an arena but not hide combat-relevant floor.
4. **Light colour supports the palette roles** (§4.2); coloured lights must not impersonate the hostile-telegraph colour.
5. **Shadow temperature is not over-specified.** The locked direction is a warm directional key with *charcoal* shadows; exact shadow hue and fill temperature are set in look-dev (Q12).
6. **Vary mood across rooms.** Rooms differ in value range, light angle, and atmosphere; none may default to uniformly dark.
7. **Atmospheric depth** (haze, light shafts, dust, value falloff to the background) is used to separate foreground/midground/background without reducing combat-floor contrast. Methods and strength are open (§5.4).
8. **Emissive is selective.** Emissive on sacred/supernatural elements only. Emissive must not compete with, or be mistaken for, hostile telegraphs, and must not use the telegraph cyan-teal family (§4.3).
9. **Budget lights deliberately.** Additional light count and shadow-casters per frame are tracked against the target platform (**[OPEN]**, §12 Q6).

### 5.3 Current state **[OBSERVED]**
- One directional light: warm white `(1, 0.96, 0.9)`, intensity 1.15, soft shadows.
- Ambient: gradient (sky 0.42/0.46/0.54, equator 0.28/0.29/0.32); fog off; default skybox; camera clear colour dark blue-grey.
- URP 17.6.0. Both `PC_RPAsset` and `Mobile_RPAsset` exist; Quality levels reference different assets (which is the shipping baseline is **[OPEN]**, §12 Q6). `PC_RPAsset`: HDR on, MSAA setting 1, main-light shadow map 2048, shadow distance 50, 4 cascades, soft shadows on. `PC_Renderer` has SSAO enabled.
- Nothing is baked: no lightmaps, probes, or volumes tuned for the game.

### 5.4 Open lighting questions **[OPEN]**
(The direction is locked; the following *method* questions are not.) Real-time vs baked vs mixed per environment; reflection/probe strategy; post-processing stack (tonemapping, bloom, colour grading, vignette) and how strong; fog/atmosphere use; time-of-day or fixed mood per region; who owns the per-region light setups (see `TECHNICAL_OVERVIEW.md` §7).

---

## 6. Scale

### 6.1 Units **[CONFIRMED by existing pipeline convention]**
1 Unity unit = 1 m. 1 Blender unit = 1 m (Blender scene units: metric, scale 1.0). Verified in both `TempleEnvironmentKit.blend` and Unity.

### 6.2 Reference measurements **[OBSERVED]**
| Reference | Value | Source |
|---|---|---|
| Player move speed | 8 m/s | `PlayerMotor` |
| Dash distance | ≈3.1 m (22 m/s × 0.14 s) | `PlayerMotor` |
| Player attack reach | 1.8 m | `PlayerCombat` |
| Enemy attack reach | 2.15 m | `TrainingDummy` |
| Prototype arena | 40 × 40 m; walls 3 m; pillars 1.4 × 1.4 × 3 m | `PrototypeArena.unity` |
| Camera view area | ≈22 m tall × ≈39 m wide visible (orthographic, size 11, 16:9) | `IsoCameraFollow` |

Character height of the Mixamo Paladin has **not** been measured in this pass. **Action for Unity Engineer:** measure it once and record it here (§10) — it becomes the master scale reference ("human unit") for the kit.

### 6.3 Observed readability concern
In the verified encounter screenshot, the two characters occupy only a very small fraction of the screen at the current camera zoom, which works against "detailed characters." Whether to tighten the camera, change FOV/projection, or both is a **[OPEN]** decision tied to Q2. Scale rules below are provisional until it is decided.

### 6.4 Scale rules **[RULE]**
- All gameplay-relevant dimensions are authored against the human unit, not by eye.
- Door/threshold, step, and cover heights are fixed system values chosen once the camera is set (**[OPEN]**) and shared between art and collision.
- Architecture may be monumental for mythic effect, but **navigable space is sized to combat** (dodge distance, attack reach), not to the architecture.

---

## 7. Modularity

### 7.1 Locked and existing conventions
**[LOCKED]** (§0.4–0.5) Reusable modular assets plus handcrafted compositions; **no monolithic environment mesh**; consistent scale, pivots, naming, materials and collision conventions established before bulk production.

**[OBSERVED, from `Art/README.md`]** One reusable piece per object/collection; apply scale/rotation before export; never overwrite existing exported assets without approval.

### 7.2 Kit structure **[OBSERVED]**
`TempleEnvironmentKit.blend` currently contains only empty top-level collections:
`00_Reference` · `10_Kit_Pieces` · `20_Props` · `30_Test_Layouts` · `90_Export_Staging`. No geometry, materials, or textures yet. The piece set for the first prototype is defined in §11.1; the production kit list and module grid remain open (Q13).

### 7.3 Open modular decisions **[OPEN]**
| Decision | Notes |
|---|---|
| Base grid / module size | Must be derived from camera, human unit, and dodge distance. Candidate sizes should be reviewed against §6; none is chosen. |
| Floor, wall, corner, doorway, stair, pillar, and trim piece set | Depends on Q1 architecture language. |
| Pivot / origin standard | Proposal by Unity Engineer + Environment Artist, signed off before first export. |
| Snap strategy (grid snapping vs sockets) | Affects Blender and Unity prefab authoring. |
| Variation strategy (damage states, material variants, decals) | Ties to §3.3. |
| Collision strategy (authored colliders vs generated) | Unity Engineer owns; Environment Artist supplies requirements. |
| Occlusion handling | Fade-out/cutaway walls vs designed-low walls; depends on Q2. |

### 7.4 Rules **[RULE]**
- Pieces must tile and snap with no visible seams at the gameplay camera.
- Props are separate from kit pieces and never required for arena function.
- Every kit piece is tested in `30_Test_Layouts` and reviewed from the gameplay camera before export.
- **Modular does not mean repetitive.** Arenas are hand-composed (§0.4): the kit supplies structure; hero pieces (statues, altars, major arches) and deliberate asymmetry supply identity and landmarks.
- **No bulk kit production** until the environment art prototype has passed review (§11).

---

## 8. Gameplay readability

This is the highest-priority section: it protects the confirmed Hades-like combat philosophy.

### 8.1 Readability hierarchy **[RULE]**
From most to least important in any combat frame:
1. Player character and hurtbox.
2. Incoming hostile telegraphs and danger zones.
3. Enemies (silhouette, facing, attack state).
4. Walkable floor and its edges / hazards.
5. Collidable cover and structure.
6. Decoration, atmosphere, background.

Art for any lower tier must never out-contrast a higher tier.

### 8.2 Specific requirements **[RULE]**
| Requirement | Detail |
|---|---|
| Foreground / midground / background | Foreground framing elements stay outside the combat footprint or are low, cut away, or faded; the combat space is the midground; the background carries scale and drama. No layer may hide the player or a telegraph (§0.4). |
| Silhouette | Player, each enemy type, and each major prop type has a distinct silhouette at gameplay-camera size, verified in a flat-silhouette test. |
| Telegraph clarity | Hostile telegraphs use the **bright cyan-teal** family (§4.3) with a clear shape, readable fill and animated windup progression; **colour is never the only signal.** They are visible on every floor material in the project and are not hidden by shadow, props, or VFX. Final timing and per-attack shape rules are owned by design (Q18). |
| Floor vs blocker | A player can distinguish floor, step, pit, wall, and cover without reading UI. |
| Occlusion | Nothing may block sight of the player or of a telegraph. Tall structures nearest the camera are cut away, faded, or kept low (technique **[OPEN]**). |
| Visual noise ceiling | Environment contrast/detail must be lower than actors in the combat area. This applies even to rich painterly materials: richness lives in form and large/medium variation, not high-frequency contrast on the combat floor. |
| Precedence | Where any style rule in §0 conflicts with this table, this table wins (§0.6). |
| Effects | VFX use readable shape language and must not hide the player hurtbox or hostile telegraphs. |
| Accessibility | Palette passes greyscale and CVD checks (§4.2); no gameplay information is carried by colour alone. |

### 8.3 Review test **[RULE]**
Every environment piece/arena passes this checklist in a gameplay-camera capture with a player, an attacking enemy with active telegraph, and normal VFX:
- Can I find the player in under a second?
- Can I see the telegraph on every floor material?
- Can I tell floor from blocker from hazard?
- Is anything important hidden by geometry?
- Does it still read in greyscale?

### 8.4 Current state **[OBSERVED]**
The greybox arena reads clearly because everything is flat and low-detail. This does not validate the final art; the checks above must be repeated with real materials.

---

## 9. Characters (scope note)

Not requested in this pass but required for context: **[OBSERVED]** player and enemy are Mixamo Paladin placeholders; enemy is a recolour. Final character art direction, pipeline, and ownership are **[OPEN]** (§12 Q4). Character silhouettes must be designed against §8.1 and the palette roles in §4.2.

---

## 10. Reference-image requirements

### 10.1 Current state **[OBSERVED]**
`Art/Blender/Reference/` is empty (only `.gitkeep`); `00_Reference` in the kit is empty. No approved references exist.

### 10.2 Rules for acceptable references **[RULE]**
- **Only approved references** go in `Art/Blender/Reference/` (per `Art/README.md`). Candidates are reviewed in a separate holding area first; nothing unapproved is committed.
- References inform *principles* (shape language, wear, light, proportion), not copying. **No screenshots of other games' assets are used as modelling or texture sources.** Screenshots of *Path of Exile 2* or *Hades* are permissible only as camera/readability study boards, clearly marked as such, and never used as texture or shape sources.
- Prefer primary sources: archaeological and architectural photography, museum collections, historical drawings, and the director's own concept work. **Verify and record licence/credit for every reference.**
- Each reference has a sidecar record (see 10.4).

### 10.3 Required reference sets (to be gathered once Q1 is decided; the style lock in §0 already defines what they must support)
| Set | Purpose | Min. content |
|---|---|---|
| Architecture | Structure types, proportions, load logic | Plans/sections/photos of the source culture's built forms |
| Materials & wear | Stone, metal, wood, cloth; weathering patterns; **painterly colour variation on large forms**; **metal-vs-stone separation** (bronze, gold, iron) | Close-up photographs showing edge wear, staining, repair; also painted/illustrative studies for brushwork-like variation, clearly marked as such |
| Ornament & symbol | Motif vocabulary | Primary-source carvings, reliefs, pottery, textiles |
| Lighting & mood | Warm directional light, controlled contrast, atmospheric depth; also rooms that are *not* dark | Photographs and director paintings; per-region |
| Camera / readability | Elevated-camera framing; foreground/midground/background layering around a clear combat space | Marked as "study only"; include the gameplay-camera framing rules |
| Silhouette & scale | Human-relative proportions | Figure-in-architecture references |
| Colour | Palette exploration | Director-approved swatches, not game screenshots |

### 10.4 Reference record (one per image or board)
Each approved reference is accompanied by an entry (filename, source URL/citation, author, licence, date added, **what principle it demonstrates**, approved-by). The index file location and format are **[OPEN]** (suggested: `Art/Blender/Reference/INDEX.md`; needs approval).

### 10.5 Review renders
Review renders go in `Art/Blender/Renders/` and must include the gameplay-camera angle. The camera setup used for review renders must match the in-game camera once Q2 is decided; until then, renders note which camera they used.

---

## 11. Review and approval process

### 11.1 Prototype-first gate **[LOCKED, §0.5]**
**One environment art prototype is created and reviewed before a large asset library is produced.** Until the Creative Director signs off the prototype, no bulk kit production, no mass texture authoring, and no mass export to `Assets/Environment/` takes place.

**Prototype scope [LOCKED]** (resolves Q16): **one compact, handcrafted temple courtyard** containing:
- worn stone floor and a readable open combat space;
- a short staircase or raised platform;
- four substantial pillars with deliberate variation;
- one monumental entrance arch;
- one central or rear altar/statue serving as the visual focal point;
- consistent painterly materials, weathering and warm cinematic lighting.

It is evaluated from the **actual elevated three-quarter gameplay camera** (the camera as configured in the project when the review is made; if the camera later changes, the prototype is re-reviewed). It must preserve **player visibility, enemy visibility, telegraph readability and combat movement space.** It is built for evaluation, not as a production asset library, and handcrafted means composed by hand rather than generated or assembled as one mesh (§0.4).

**Prototype details not yet decided [OPEN]:** the subject and ornament of the altar/statue and arch, which depend on Q1 (Q19); and the courtyard's dimensions and minimum clear combat space (Q20). Nothing in the prototype may depict a real-world deity or culture by assumption; the Creative Director picks the subject or approves an abstract placeholder form before modelling. No modelling starts until Q19 and Q20 are answered and a modelling task is assigned.

**Prototype pass criteria** (all must hold, evaluated through the real gameplay camera with the player, an enemy and an active telegraph in frame):
1. §8.3 readability checklist passes, including greyscale.
2. Materials read as the locked style (§0.2): sculpted forms, nuanced roughness, metal separation, no anonymous noise, not low-poly, not ink-wash.
3. Palette and lighting match §0.3: gold used as accent, not everywhere; the room is not excessively dark.
4. Foreground/midground/background are distinct and nothing hides the player or telegraphs.
5. Scale, pivots, naming, material and collision conventions are written down and followed (technical conventions: `TECHNICAL_OVERVIEW.md` §4.5, §5).
6. A gameplay-camera screenshot set is captured and stored with the review (§10.5, `TECHNICAL_OVERVIEW.md` §8). Close-up renders alone do not count.
7. All six scope elements above are present, and the telegraph is shown in the locked cyan-teal with shape, fill and windup progression (§4.3). How the telegraph is shown before the combat implementation task is authorised is open (Q18).
8. Player, enemy, active telegraph and combat movement space are all clearly visible in the same gameplay-camera frame.

### 11.2 Per-piece workflow **[RULE]**
1. Blockout in Blender (grey, correct scale) → gameplay-camera review render in `Renders/`.
2. Creative Director approves shape language and readability.
3. Materials/textures authored per the decided pipeline (§3.3).
4. Export to `Art/Exports/Environment/Staging/` → validate → move to `Review/`.
5. Unity Engineer imports from `Review/` into `Assets/Environment/` (`Models/`, `Materials/`, `Textures/`, `Prefabs/`; `TECHNICAL_OVERVIEW.md` §5.4).
6. In-engine gameplay-camera check against §8.3.

Detailed file/handoff conventions: `TECHNICAL_OVERVIEW.md` §5–§7.

---

## 12. Open decisions (art)

| # | Decision | Owner | Blocks |
|---|---|---|---|
| Q1 | Mythological source/premise, tone, first region. *Architectural typology is locked (§0.1); the cultural vocabulary is not.* | Creative Director | Ornament/motif language, references, hero-piece design |
| Q2 | Camera projection, pitch, FOV/zoom, rotation | Creative Director + Unity Engineer | Scale, modules, occlusion |
| Q3 | **Narrowed by the lock.** Style level is decided (§0.2). Remaining: texture workflow (how painterly albedo is authored while carrying roughness/metal/normal data); outlines/rim/ramps yes/no (must not read as ink-wash) | Creative Director + Unity Engineer | Material pipeline, shaders |
| Q4 | Final character direction vs Mixamo placeholders | Creative Director | Silhouettes, scale reference |
| Q6 | Target platform(s) and quality baseline | Creative Director | Budgets, lighting approach |
| Q10 | Texel density, texture resolution, and polygon budgets | Unity Engineer + Environment Artist after Q6 | Kit production |
| Q11 | **Narrowed by the lock.** Direction decided (§0.3). Remaining: exact values for every role in §4.2 | Creative Director | All colour work |
| Q12 | Light/post-processing strategy (baked vs real-time; post stack) | Creative Director + Unity Engineer | Look-dev |
| Q13 | **Narrowed.** The first prototype's piece set is defined (§11.1). Remaining: module grid size and the production kit piece list, to be settled after the prototype review | Environment Artist, approved by Creative Director | Production kit modelling |
| Q14 | Reference index location/format | Game Director | Reference management |
| Q15 | **RESOLVED (v0.3).** Combat telegraph colour is bright cyan-teal; shape, fill and animated windup required; colour never the only signal (§4.3, §0.9) | — | — |
| Q16 | **RESOLVED (v0.3).** First environment prototype is one compact handcrafted temple courtyard with the listed elements, evaluated from the gameplay camera (§11.1, §0.9) | — | — |
| Q17 | **RESOLVED (v0.3).** `Art/Blender/` plus `Assets/Environment/{Models, Materials, Textures, Prefabs}`; Unity Engineer may propose extra subfolders when technically necessary (§0.9; `TECHNICAL_OVERVIEW.md` §5.4). The folders are not yet created | — | — |
| Q18 | Telegraph specification details: exact cyan-teal value, fill opacity, edge treatment, per-attack shape language, windup animation style, extra non-colour cues (design territory), and how/when the combat-script implementation is authorised. Includes how the prototype review shows a cyan-teal telegraph before that authorisation | Creative Director + Game Designer + Unity Engineer | Telegraph VFX, prototype review, palette values |
| Q19 | Subject, iconography and ornament vocabulary of the prototype's altar/statue/arch (depends on Q1); or approval of an abstract placeholder form | Creative Director | Start of prototype modelling |
| Q20 | Prototype courtyard dimensions and the minimum clear combat space (to be derived with design from dash ≈3.1 m, enemy reach 2.15 m and the current camera) | Game Designer + Creative Director | Start of prototype modelling |

### Resolved by the style lock
The previous "stylisation level", "grounded vs stylised placement", "architecture family (temple-type structures)" and "palette hue direction" questions are resolved by §0. They are kept in history only as context.

### Resolved after the lock (v0.3)
Q15 (telegraph colour), Q16 (prototype scope) and Q17 (asset folders) are resolved; see §0.9. Their rows above are kept, marked resolved, for traceability.

---

## 13. Change log

| Version | Change |
|---|---|
| v0.1 | Initial framework from the confirmed direction; style left open. |
| v0.2 | Added §0 *Painterly Mythological Fantasy* as the **locked, authoritative** environment style; updated §1–§5, §7, §8, §10, §11, §12 to reference it; added prototype-first gate (§11.1); recorded Q15–Q17. No other content removed. |
| v0.3 | Resolved **Q15** (bright cyan-teal telegraph colour, §4.3), **Q16** (compact handcrafted temple courtyard prototype, §11.1) and **Q17** (asset folder structure, `TECHNICAL_OVERVIEW.md` §5.4); added §0.9; replaced the interim telegraph conflict note; opened Q18–Q20. §0 style lock and its precedence unchanged. |

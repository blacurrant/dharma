# MythicRoguelite — Game Brief

**Status:** Draft v0.3 — initial documentation pass; environment style locked (`ART_BIBLE.md` §0); telegraph colour, prototype scope and asset folders resolved (`ART_BIBLE.md` §0.9)
**Baseline:** repo `main` @ `a061e7e` (Paladin player + recoloured Paladin enemy verified in `PrototypeArena`)
**Owner:** Creative Director (Nishant) · **Maintained by:** Game Director

> **How to read this document.** Every statement is tagged:
> **[LOCKED]** = final creative-director decision · **[CONFIRMED]** = stated by the creative director · **[OBSERVED]** = read directly from the current project · **[OPEN]** = not decided; do not treat as fact. Nothing untagged should be relied on. Open items are collected in §9.

---

## 1. Vision

**[CONFIRMED]** A fully 3D mythological action roguelite.

**[CONFIRMED]** Pillars:

1. **Elevated three-quarter overhead camera**, in the visual territory of *Path of Exile 2* (a reference for camera height and presentation only — not for assets, characters, or world).
2. **Hades-like combat philosophy:** precise dodging, readable telegraphs, impactful attacks, and small, dangerous encounters rather than enormous enemy hordes.
3. **Detailed, stylized fantasy characters and environments.**
4. **Grounded architecture, weathered surfaces, painterly material treatment, distinctive silhouettes, deliberate lighting.**
5. **Original mythological worldbuilding and visual identity.** No other game's assets are copied or traced.

**[LOCKED] Environment visual style: _Painterly Mythological Fantasy_.** The authoritative definition — architecture, surface treatment, colour and lighting direction, gameplay composition and production rules — is **[`ART_BIBLE.md` §0](ART_BIBLE.md)**. In short: grounded, monumental, weathered mythological architecture; rich painterly 3D materials (not low-poly, not ink-wash); muted warm stone with antique gold, bronze and restrained crimson; cinematic warm directional light; and always-readable actors and telegraphs. Where any text in this brief appears to conflict, `ART_BIBLE.md` §0 prevails.

**[LOCKED] Decisions resolved after the style lock** (details in `ART_BIBLE.md` §0.9):
- **Combat telegraph colour (Q15):** bright cyan-teal, with a clear shape, readable fill and animated windup progression. Colour is never the only danger signal.
- **First environment prototype (Q16):** one compact, handcrafted temple courtyard — worn stone floor and open combat space, a short staircase or raised platform, four varied substantial pillars, one monumental entrance arch, one central or rear altar/statue focal point — evaluated from the real elevated three-quarter gameplay camera.
- **Environment asset folders (Q17):** `Art/Blender/` for sources; `Assets/Environment/{Models, Materials, Textures, Prefabs}` for Unity assets.

**[OPEN]** Working title is the project name `MythicRoguelite`; a shipping title has not been chosen.

## 2. Player experience goals (derived from the pillars)

These restate the confirmed pillars as testable goals; they add no new creative content.

| Goal | What it means in practice |
|---|---|
| Fair, precise combat | Every damaging attack is telegraphed long enough to react to and visually unambiguous at gameplay camera distance. Deaths should be attributable to a player mistake. |
| Small, dangerous encounters | A handful of enemies, each individually threatening, rather than crowds. Encounter size is a *design budget* (see §9 Q7). |
| Impact | Hits read through animation, VFX, camera/hit-stop feedback, and audio — not just damage numbers. |
| Readable at distance | Characters, telegraphs, hazards, and walkable space must stay legible from the elevated camera (see `ART_BIBLE.md` §8). The readability rules outrank decorative richness in the locked art style. |
| A world with its own identity | Visuals, architecture, and lore are original and cohere around one mythological premise (undecided — §9 Q1). |

## 3. Core loop

**[OPEN]** The run structure is not defined. Not yet decided: room/encounter sequencing, rewards and boons, meta-progression, run length, death/retry loop, hub or no hub, boss structure, and randomisation scope. This brief deliberately does **not** assume a Hades-style structure beyond the *combat philosophy* the director confirmed.

## 4. Camera and perspective

| Aspect | State |
|---|---|
| Intent | **[CONFIRMED]** Elevated three-quarter overhead; PoE2-like territory. |
| Current prototype | **[OBSERVED]** `IsoCameraFollow`: offset `(12, 18, −12)` ⇒ yaw 45°, pitch ≈ 46.7° below horizontal; **orthographic**, size 11 (≈22 m visible vertical, ≈39 m horizontal at 16:9); follow speed 14; clip 0.1–80. |
| Orthographic vs perspective | **[OPEN]** PoE2-style presentation is conventionally perspective with a steeper, narrow-FOV view. Whether the final game stays orthographic is undecided (§9 Q2). The prototype value is a placeholder, not a decision. |
| Fixed vs rotatable, zoom, occlusion handling | **[OPEN]** |

## 5. Combat philosophy and current prototype baseline

**[CONFIRMED]** Hades-like philosophy as in §1.

**[OBSERVED]** What the prototype currently implements (values are prototype tuning, **not** design decisions):

| Element | Current prototype value | Source |
|---|---|---|
| Player move speed | 8 m/s | `PlayerMotor` |
| Dash | 22 m/s for 0.14 s (≈3.1 m), cooldown 0.75 s | `PlayerMotor` |
| Player attack | range 1.8 m, ±58° arc, cooldown 0.35 s, 25 dmg, 4.5 knockback, hold-to-repeat | `PlayerCombat` |
| Enemy (single melee "training dummy") | approach 3.2 m/s, attack range 2.15 m, ±58° arc, **windup 0.78 s**, recovery 0.4 s, cooldown 1.9 s, 12 dmg, 150 HP, windup armour on | `TrainingDummy` |
| Telegraph (current) | Enemy tint shifts to orange + attack FX during windup. Prototype behaviour; unchanged. | `TrainingDummy`, `CharacterTintFeedback`, `CombatFx` |
| Telegraph (decided target) | **[LOCKED]** Bright cyan-teal with clear shape, readable fill and animated windup; colour is never the only signal. **Not yet implemented**; changing combat scripts requires a separate authorised task. | `ART_BIBLE.md` §4.3 |
| Encounter | One enemy in a walled arena; win/lose; `R` restarts in place | `ArenaEncounter` |
| Input | Unity Input System; WASD, Space dash, LMB/Enter attack | `PrototypeInput`, `InputSystem_Actions.inputactions` |
| Characters | Mixamo "Paladin J Nordstrom" (player) and a recoloured copy (enemy); 21 Mixamo clips; no dedicated dash clip (roll used as stand-in) | `Assets/Characters/Player/README.md` |

**[OPEN]** Weapon set, ability/boon system, enemy roster and archetypes, boss design, status effects, damage model, controller support.

## 6. Setting and mythology

**[OPEN — blocks ornament, motif and reference work.]** No mythological source, region, pantheon, tone, or story premise has been decided. The director confirmed that it must be *original* and *mythological*.

**[LOCKED]** The environment typology is weathered temples, carved stone pillars, massive arches, worn stairs, altars, statues and composed courtyards (`ART_BIBLE.md` §0.1). The *cultural vocabulary* those structures draw on is not decided. See §9 Q1.

## 7. Content scope

**[OPEN]** Number of biomes/regions, enemy count, run length, vertical-slice definition, and platform targets are undecided.

**[OBSERVED]** Existing content is a greybox: `PrototypeArena` (40×40 m floor, 3 m walls, four 1.4×1.4×3 m pillars, one enemy) and `CharacterRigTest`. `SampleScene` is the Unity template scene and the only scene currently enabled in Build Settings.

## 8. Team and responsibilities (summary)

Detailed hand-off rules are in `TECHNICAL_OVERVIEW.md` §7.

| Role | Responsibility |
|---|---|
| Creative Director (Nishant) | Final authority on direction; resolves §9. |
| Game Director | Maintains this brief, sequences work, routes tasks, keeps docs current. |
| Game Designer (`@designy`) | Combat, encounter, and progression design. |
| Unity Engineer | Unity project, scripts, import, scenes, shaders, rendering. |
| Environment Artist | Blender source, environment kit, materials/textures, review renders. |

> Unity Engineer and Environment Artist are **roles** defined here; no teammate profiles with those names exist on this install yet.

## 9. Open decisions (index)

The full list with context for the creative director is also reported alongside this document. Items are cross-referenced from the other docs.

| # | Decision | Blocks |
|---|---|---|
| Q1 | Mythological source/premise, tone, and the first region to build (architectural typology is already locked) | Reference gathering, ornament/motif language, hero-piece design |
| Q2 | Camera: stay orthographic or move to perspective; pitch, FOV/zoom, rotation | Scale rules, kit module design, occlusion, readability thresholds |
| Q3 | **Style decided** (*Painterly Mythological Fantasy*, `ART_BIBLE.md` §0). Remaining: texture-authoring workflow and whether any outline/rim shader is used | Material pipeline, shader work, texture budgets |
| Q4 | Protagonist and enemies: is the Mixamo Paladin a permanent placeholder, and who produces final character art | Character scale reference, silhouette language |
| Q5 | Run structure and vertical-slice scope (first biome/room set) | Content order, kit scope |
| Q6 | Platform and performance target (PC only? controller?) | Poly/texture/light budgets, which URP asset is the baseline |
| Q7 | Encounter size and enemy-count budget | Arena sizing, readability testing |
| Q8 | Source control for large binaries (Git LFS or not); whether `Art/` is tracked | Repo health |
| Q9 | Placeholder asset licensing review (Mixamo character/animations) | Shippability of current prototype assets |

*Further open items live in `ART_BIBLE.md` §12 and `TECHNICAL_OVERVIEW.md` §10. `ART_BIBLE.md` Q15 (telegraph colour), Q16 (environment prototype scope) and Q17 (asset folders) are **resolved**. New open items: Q18 (telegraph specification details and implementation authorisation), Q19 (subject/ornament of the prototype's altar/statue/arch) and Q20 (prototype dimensions and clear combat space).*

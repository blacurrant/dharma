# Art-Direction Review 001 — Visual Target and Integration Plan

**Status:** Decision proposal. **Not committed, not promoted.** Nothing here changes `ART_BIBLE.md` §0 (locked style) or any locked decision; where it touches a locked item (camera, Q20) it asks for approval instead.
**Tags:** [OBSERVED] measured/read in this review · [PROPOSED] needs Creative Director (CD) sign-off · [LOCKED] existing decision · [OPEN] undecided.

## 0. Inputs and limits
| Input | What was actually reviewed |
|---|---|
| Painterly reference | The generated 954×670 image `Desktop/Screenshot 2026-10-24 at 9.11.19 PM.png`, **assumed** to be the one meant. Not copied into the repo. Treated as a mood/readability study only (`ART_BIBLE.md` §10.2). Not a validated gameplay frame, and its geometry is not reliable. |
| Environment kit | `Art/Blender/ENVIRONMENT_KIT_NOTES.md`, the staged exports, `Assets/ArtTest/Reviews/ART_TEST_VALIDATION_REPORT.md` and its three captures. |
| Unity comparisons | **Not yet available.** This document defines what they must show (§5, §6). All Unity numbers in Part 1 come from **one** capture, `gameplay_camera_telegraph.png`, so treat them as indicative. **Update (revision 3):** a Unity camera and lighting pass now exists (`Assets/ArtTest/Reviews/CAMERA_LIGHTING_REPORT.md`, captures in `Phase1`–`Phase3`); Part 3 §21.1 integrates it, and where it contradicts Part 1 (for example the cyan fill, which that report shows was a demo bug, not a real invisibility) Part 3 prevails. |

## 1. Single prioritized visual target
Priority order: **(1) combat readability → (2) character presence → (3) light structure → (4) floor/material → (5) periphery density → (6) polish.** A lower item never overrides a higher one (`ART_BIBLE.md` §8.1).

> *A warm, side-lit stone courtyard seen from a closer elevated camera: quiet, mid-dark floor in the centre; denser, brighter structures at the edges; long soft shadows; small bronze/gold/crimson accents; and one cool cyan-teal element, the telegraph, that is the highest-contrast thing on the floor.*

| Area | Current (observed) | Reference (observed, indicative) | **Target [PROPOSED]** |
|---|---|---|---|
| Character screen height | ≈6–7 % (~60–75 px at 1080p); 5.6 % computed for a 1.8 m figure (Paladin height still unmeasured) | ≈10–11 % | **8–9 %**: ortho size ≈7–8 at the current pitch (size 7.5 → 8.2 %). Keep **≥ ~9 m of ground visible each way** (3 dash lengths). Size ≥ ~7.3 keeps the whole 20 m clear zone on screen |
| Pitch / projection | ortho, 46.7° | looks flatter and perspective-like (≈40°, unreliable) | Baseline 46.7°; test **42°**. Projection stays **ortho** until Q2 is decided |
| Key light direction | Travels within **≈10°** of the camera's view direction (front-lit, flat, shadows hidden behind objects) | Side/back-lit, long shadows toward the viewer | **Side to 3/4-back key, ~35–45° elevation** (current ~50°) |
| Key colour | near-neutral (1.0, 0.96, 0.90), temperature unused | strongly warm | **Warm, ~3800–4800 K equivalent**; floor R/B ≈1.6–1.9 (now 1.4) |
| Fill / shadows | cool blue-grey ambient (0.42, 0.46, 0.54) → bluish shadows | warm-brown shadows | **Neutral-warm charcoal** (§0.3). Cast shadow on the combat floor never crushed (mean luma ≥ ~0.20) |
| Floor value | mean luma **0.41**, flat (p5–p95 spread 0.10–0.16), regular 2 m lattice | mean 0.32–0.34, light/shadow pools | **0.30–0.36**, with large-scale (≥3 m) variation coming from light and shade |
| Shadow softness | URP soft shadows, 4 cascades, 2048, distance 50 | soft penumbra | Keep soft; test distance ~35, 2–3 cascades |
| Density / hierarchy | Even and sparse; near walls have loud light/dark banding; grey void outside walls | Empty centre, dense periphery, dark edges | **Centre stays empty (locked).** Edges denser and darker. No void visible outside the courtyard |
| Colour grouping | uniform tan; accents tiny | warm-dominant, small saturated accents | Three groups: quiet floor / lit structure / small accents. **Cyan-teal appears only in telegraphs** |
| Post | none in the art-test scene | grading, vignette, glow on fire | Tonemapping + gentle grade + soft vignette + low bloom (threshold above 1 so the floor and telegraph don't bloom) |

**Measurement note.** Fine-grain contrast on the Unity floor is *lower* than the reference (mean neighbour-pixel difference 0.007–0.011 vs ≈0.022). The "grout problem" is therefore **regularity and flatness, not too much contrast**; flattening the floor further would be the wrong fix. The reference's richness comes mostly from lighting, and its floor is not telegraph-validated, so don't copy its floor noise.

## 2. What the reference may and may not drive
**Adopt (principles only):** character presence, light angle and warmth, value structure (lit pool → dark edges), quiet centre / dense periphery, warm-dominant palette with small accents, large irregular flag read.
**Not adopted — illustration only, not world-design:** the lion/guardian-beast statue, the gold ring sigil on the floor, the red leaf litter, red ribbon motifs, the tower/obelisk pillar forms, the ravine/cliff backdrop, vines. The sigil and leaf litter would also break locked rules (crimson/emissive off the combat floor; a quiet floor; no telegraph look-alikes). Q19 (abstract) and Q1 (mythology open) stand.

## 3. Issues by category
**A. Unity-side fixes** (scene, lights, camera, post, material parameters, import; art-test scene only — no gameplay scene, script or `PrototypeArena` change)
| # | Fix | Solves |
|---|---|---|
| A1 | Camera comparison in the art-test scene (§5). **Needs CD approval**, because Q20 said to reuse the existing camera | Character size, far landmarks out of frame |
| A2 | Rotate/retemper the key light; neutral-warm ambient; shadow distance/cascades | Flat look, bluish shadows, floor too light for telegraphs |
| A3 | Add a global Volume: tonemap, grade, vignette, low bloom | Even tan read, missing mood |
| A4 | Material parameters on floors/walls: occlusion strength, normal scale, tint | Lattice emphasis, wall banding |
| A5 | Re-pose **existing** instances in the scene: edge clusters of banners, braziers, rubble, columns; lower or fade near-side pieces | Periphery density, occlusion |
| A6 | Treat the outside of the walls: dark ground/backdrop, depth falloff | Grey void, foreground/mid/background (§0.4) |
| A7 | Telegraph demo tuning (art-test scene only): edge width, strike ramp; hide the old red telegraph for comparison frames | Cyan fill invisible on the floor |
| A8 | Perf quick wins: stop floor/border tiles casting shadows (~400 of 1,177 casters), instancing/static batching, texture compression and resolution | Budget (§6) |

**B. Existing asset revisions** — only when the stated trigger fires after A
| # | Revision | Trigger |
|---|---|---|
| B1 | Re-bake the 4 floor BaseColor/Mask maps: break the 2 m lattice, enlarge the flag read, no new geometry | Lattice still visible after A2+A4 |
| B2 | Soften BaseColor banding on Wall A/B | Near wall still outdraws actors after A2–A4 |
| B3 | Reduce wall/border tris (~950 k + ~543 k) | Player-build measurement misses budget |
| B4 | Arch opening is **4.2 m**, but the kit notes say 5 m: correct the notes, or change geometry only if 5 m was intended | CD answer |
| B5 | Player/enemy contrast (both dark Paladins on tan) — character owner, Q4 | Still failing after A2 |

**C. New asset production** — nothing is needed for the next review. Candidates only after A/B pass, CD approval and Q8:
C1 floor wear decals (only if B1 isn't enough) · C2 neutral-tone ground-cover/overgrowth cards (no crimson, no cyan) · C3 distant backdrop silhouettes (only if A6 can't carry the background).

**D. Optional polish — wait:** painterly screen-space filter (risks the ink-wash read and blurs telegraph edges) · volumetric fog/light shafts · brazier flicker lights · leaf/dust VFX · baked lightmaps and probes · extra props · HUD colour check (the Dash bar is a sky-blue near the reserved cyan-teal family) · any floor emblem.

## 4. Acceptance criteria (all measured on gameplay-camera frames at 1080p)
| # | Criterion | Pass |
|---|---|---|
| AC1 | Player and enemy found in < 1 s; character height | 8–9 % of screen height; ≥ 9 m of ground visible each way from the player |
| AC2 | **Telegraph, lit floor:** greyscale luma delta of the strike-frame fill vs the surrounding floor | ≥ 0.10; edge ≥ 0.25 |
| AC3 | **Telegraph, shadowed floor:** same test inside cast shadow | ≥ 0.10 |
| AC4 | Shape reads without colour (greyscale and CVD simulation); edge width | Shape identifiable; edge ≥ ~3 px at 1080p |
| AC5 | Reservation | Cyan-teal appears nowhere in environment, lights, emissive or player VFX; crimson/emissive absent from the combat floor |
| AC6 | Combat floor | Mean luma 0.30–0.36; no visible repeating 2 m lattice; large-scale variation present; fine detail below actor contrast |
| AC7 | Light | Key direction ≥ 60° off the camera view direction; warm key; shadows not crushed in the clear zone |
| AC8 | Clear zone and occlusion | r ≈ 10 m still free; nothing near-side hides player or telegraph at any capture position |
| AC9 | Hierarchy | Player/telegraph > enemy > floor > structures > decoration (§8.1); near walls don't outdraw actors |
| AC10 | Style | Still reads as §0: painterly, weathered, not low-poly, not ink-wash, gold as accent |
| AC11 | Performance (§6) | Measured in a development **player build**, no regression versus baseline |

Arithmetic behind AC2: the fill needs about α = ΔL ÷ (0.71 − floor luma). At floor 0.33, ΔL 0.10 needs ≈26 % and ΔL 0.15 needs ≈39 %. So a darker floor makes the approved **#27DCD1 at ≈22–28 %** nearly sufficient, and a strike ramp to ≈40–45 % fits Q18's "increased intensity near the strike". Today's 0.41 floor would need 33 % / 50 %. Gamma-space arithmetic only: confirm on real frames.

## 5. Comparison matrix the Unity captures should deliver
Fixed 1080p capture positions: centre · toward dais (far −X/+Z) · toward arch · near-side edge, each with the cyan demo telegraph at start/mid/strike, plus one frame with the current red telegraph to keep "current vs target" separate.
| Axis | Options |
|---|---|
| Light | baseline · side-lit L · side-lit R · 3/4-back — at 50° and 38° elevation; warm key, neutral-warm ambient |
| Camera | ortho 11 (baseline) · 9 · 7.5 · 7.5 + 42° pitch; optional lower-third player offset via a target transform in the scene only |
| Post | off · on |
Pick one light × one camera, then tune. Don't run the full grid.

## 6. Performance constraints and validation
**Baseline [OBSERVED, Editor, Apple M5, single samples]:** 2.57 M scene tris · ~7.7–8.3 M tris/frame with shadows · ~1,900–2,000 draw calls · 55–56 SetPass · 1,177 shadow casters · CPU 2.2–3.1 ms · GPU 3.8 ms · ~415 MB texture memory.
**Constraint:** the platform target is **[OPEN] (Q6)**, so no hard budget is set. Interim rule: no regression against this baseline after the changes above, and any added light, shadow caster or post effect must be justified against it.
**Required validation [PROPOSED]:** a development player build (not the Editor); a scripted 60 s run covering all capture positions; record avg/p95/p99 frame time, draw calls, SetPass, shadow casters and texture/mesh memory; repeat on a lower-end machine once Q6 exists; verify post and shadows on/off. Check a 1,177 → ~780 shadow-caster drop (A8).

## 7. Implementation order
1. **Baseline freeze:** capture the matrix positions unchanged (A-side, no edits).
2. **Light** (A2, then A3 post): biggest gain, scene-only, no approval needed.
3. **Floor/wall material parameters** (A4).
4. **Camera comparison** (A1) — CD approval gate (D1 below).
5. **Composition:** edge density with existing pieces, outside-the-walls treatment, occlusion (A5, A6).
6. **Telegraph tuning** on the final light/floor/camera (A7), then AC2–AC5.
7. **Perf pass** (A8) and the player-build measurement.
8. **Review gate:** run the AC table. Only failures trigger **B**; only B failures plus approval trigger **C**. **D** waits.

## 8. Decisions requested from the CD
- **D1** Approve testing a tighter camera (ortho ≈7–8.5, optional 42° pitch) in the **art-test scene only**; this amends Q20's "reuse the camera". The gameplay scene and `IsoCameraFollow` stay untouched.
- **D2** Confirm the reference is a study board with the not-adopted list in §2.
- **D3** Acknowledge that the strike ramp may reach ≈40–45 % fill (inside Q18; the hue and the edge colour stay).
- **D4** Settle Q8 (Git LFS) before any commit: `Art/` and `Assets/ArtTest/` hold ~0.5 GB of untracked binaries.
- **D5** Q6 platform target, before budgets can be hard numbers.

## 9. State of the repo when this was written
This review added only this untracked file. Pre-existing uncommitted work (`Art/` tree, `Art/README.md` edit, `Assets/ArtTest/`, `Assets/Scenes/ArtTest_TempleCourtyard.unity`) is untouched. Nothing committed, pushed or promoted to `Review/`.

**Flag:** `git status` also shows modifications **not made by this review** and not present at the previous commit: `Assets/Characters/Player/Materials/Paladin_MAT.mat`, `Assets/Characters/Enemy/Materials/Paladin_Enemy_MAT.mat` and `ProjectSettings/Packages/com.unity.pipeline/EditorPipelineConfig.json`. They are character materials and a project-settings file, so they were probably touched by the Unity Editor or an earlier task. Inspect them (`git diff`) before any commit; they bear on B5 (character contrast) and must not be swept into an environment commit.

---

# Part 2 — Decision record for gates D1–D5 (supplement, review revision 2)

**Status of this part:** decisions and recommendations only. **Nothing was implemented**: no scene, script, material, project-setting or Git change, and nothing committed, pushed, staged, installed or promoted. Sections 0–9 above are unchanged; where Part 2 differs from them, Part 2 is newer. Locked decisions (`ART_BIBLE.md` §0, §0.9, Q15–Q20) are untouched.
Tags: **[APPROVED]** instructed by the Creative Director (CD) in the brief for this task · **[PROVISIONAL]** approved for testing only · **[PROPOSED]** recommendation awaiting CD approval · **[UNRESOLVED]** needs a decision · **[OBSERVED]** read or computed in this pass.

## 10. Status of D1–D5

| Gate | Status | One-line outcome |
|---|---|---|
| **D1 Camera** | **[APPROVED for testing]** 42° / size 8 vs 46.7° / size 9 vs 46.7° / size 11, art-test scene only, decided by moving captures; **no change to `IsoCameraFollow` or the production camera; Q20 not amended** | See Part 3 §22 |
| **D2 Reference** | **[APPROVED / closed]** mood and readability study; all exclusions in force | See §13 |
| **D3 Telegraph** | **[APPROVED for testing]** 40–45 % strike-phase ramp; windup carried by edge, shape and reveal; no production combat-script change until the in-engine test passes; Q21 open | See Part 3 §22 |
| **D4 Git LFS** | **[APPROVED IN PRINCIPLE, conditional]** hybrid strategy subject to file-level review; backup **done and verified**; LFS **not installed**; no configuration, history migration, commit or push authorised | See Part 3 §23 |
| **D5 Platform** | **[PROVISIONAL]** PC desktop, keyboard and mouse first, controller planned, 1080p / 60 fps; budgets are initial targets pending player-build measurements | See Part 3 §24 |
| **Naming** | **[APPROVED]** "Half Heaven" is the creative title; `MythicRoguelite` stays the internal repository and project name; nothing renamed | See Part 3 §25 |
| **Q1 direction** | **[RECORDED, partial]** distinct fantasy rooted in Hindu traditions; first prototype stays abstract (Q19 locked); research and sensitivity review required first | See Part 3 §25 |

*(This table was revised in revision 3; the earlier statuses are superseded.)*

## 11. Discrepancies between the brief and the repository (resolve before relying on the text)

| # | Brief says | Repository shows | Handling |
|---|---|---|---|
| 1 | Project is "Half Heaven" | "Half Heaven" appears nowhere in the repo or docs. The project is `MythicRoguelite`; the remote is `blacurrant/dharma` | **Not renamed.** If a rename is intended it needs its own decision record. Until then this document keeps `MythicRoguelite` |
| 2 | "Hindu mythology should inform the world's identity" | No document records this. Q1 (mythology) is **open**; Q19 (locked) makes the first prototype **abstract, depicting no specific deity or culture**; `ART_BIBLE.md` §11.1 bans real-world deities by assumption | **[PROPOSED] input to Q1, not applied.** It does not contradict Q19 (which governs the first prototype only), but it must be recorded as a CD decision before any art uses it. See the note below |
| 3 | "Existing size 9 baseline" | `ArtTest_TempleCourtyard.unity` is at orthographic size **9**; `PrototypeArena.unity` (the Q20 reference) is at **11**; the earlier validation report recorded 11, so the art-test scene was changed afterwards | The test uses **9 as the working baseline and 11 as the Q20 control**. The art-test scene's own value is the only one that may be varied |
| 4 | Character presence is a priority (§1: 8–9 % screen height) | That height is only reached at size ≤ 7.5, which fails the 10 m criterion below | A genuine trade-off; see §11.2 |
| 5 | Earlier status flagged modified character materials and a project-settings file | `git status` no longer shows them modified | Resolved on their own; no action taken. Re-check before any commit |

**Note on Hindu mythology (recommendation).** To honour "no generic mythological-game shorthand" without contradicting Q19: keep the first prototype abstract; when Q1 is decided, record it as a CD decision (including which traditions, texts and regional architectures are sources), research from primary architectural and archaeological sources, and run a sensitivity review before depicting any deity, sacred symbol or ritual object, since these belong to a living religion. Until then, no figurative or iconographic content is added.

## 12. D1 — Camera test (provisional)

### 12.1 What the test must prove
The CD's criterion: the **complete 10 m combat radius stays visible during movement and attacks, not only in a frozen pose.** Interpretation used here **[PROPOSED]**: the ellipse of radius 10 m on the ground around the **player** must stay fully inside the frame at all times. (If the intent is the arena's fixed 10 m clear zone while the player roams to its edge, no size in the matrix can satisfy it, since that needs about 14.6 m of screen half-height; please confirm the interpretation.)

### 12.2 Computed expectation **[OBSERVED arithmetic; CORRECTED in revision 3]**
**Correction.** Revision 2 used the camera's *displacement* during the dash (1.73 m) as if it were the *lag*. A frame-by-frame simulation of `IsoCameraFollow`'s filter (per frame the camera moves toward the target by 1 − e^(−14·Δt)) gives these world-space lags of the camera behind the player: **steady run ≈ 0.51 m (60 fps) to 0.54 m (144 fps); peak at the end of a dash from running ≈ 1.26 m (60 fps) to 1.36 m (144 fps)**. The lag grows with frame rate, so captures must also be taken uncapped. A world offset along the camera's forward axis appears on screen scaled by sin(pitch). The 10 m ellipse needs a screen half-height of 10 × sin(pitch). This assumes the camera is centred on the player; the art-test scene's focus bias (§21.1) takes margin away from every row below.

**Pitch 46.7° (offset (12, 18, −12)): ellipse half-height 7.28 m**

| Ortho size | Static margin | Run cost (0.37–0.40 m) | Dash cost (0.92–0.99 m) | Character height (1.8 m placeholder) |
|---|---|---|---|---|
| 7 | −0.28 m (clips) | fail | fail | 8.8 % |
| 7.5 | +0.22 m | fail | fail | 8.2 % |
| 8 | +0.72 m | pass | fail | 7.7 % |
| 8.5 | +1.22 m | pass | pass (spare 0.23–0.30 m) | 7.3 % |
| 9 | +1.72 m | pass | pass (spare 0.73–0.80 m) | 6.9 % |
| 11 | +3.72 m | pass | pass | 5.6 % |

**Pitch 42° (offset (12, 15.28, −12)): ellipse half-height 6.69 m**

| Ortho size | Static margin | Run cost (0.34–0.36 m) | Dash cost (0.84–0.91 m) | Character height |
|---|---|---|---|---|
| 7 | +0.31 m | fail | fail | 9.6 % |
| 7.5 | +0.81 m | pass | fail | 8.9 % |
| 8 | +1.31 m | pass | pass (spare 0.40–0.47 m) | 8.4 % |
| 8.5 | +1.81 m | pass | pass | 7.9 % |
| 9 | +2.31 m | pass | pass | 7.4 % |

Reading: **tighter is not automatically better.** At 46.7° the smallest size that survives a dash is about 8.2–8.3; at 42° about 7.5–7.6. **42° / size 8 is the only configuration in this set that reaches ≈8.4 % character height and keeps the radius in frame through run and dash**, with roughly 0.4 m to spare. That spare is small: any camera focus bias, a hit knockback, or low frame rate can consume it. This is a prediction; the captures decide.

### 12.3 Test protocol **[SUPERSEDED by Part 3 §22: the CD narrowed the matrix to three configurations]**
- **Matrix:** sizes 7, 7.5, 8, 8.5, 9 at 46.7° (control 11 in the original scene is read only); a separate 42° series at 7.5, 8, 8.5, 9. The 42° series runs only because the camera script already derives its rotation from the serialized `offset`; it can be set in the art-test scene's camera object **without editing the script**. If that cannot be done without touching the script, the 42° series is dropped.
- **Movement script (identical for every cell):** idle; run 8 m/s in the 8 directions for 2 s each, with emphasis on the up-screen/down-screen directions where the vertical lag cost is highest; dash in the same directions; attack with the enemy at its spawn; one full telegraph cycle with the player at the 10 m edge. Record a frame sequence, not single stills.
- **Measurements per frame:** distance in pixels from the frame edge to the nearest point of the projected 10 m ellipse (min over the run); character height as a percentage of frame height; whether player, enemy and telegraph stay on screen together.
- **Pass:** minimum edge margin ≥ 0 px on every frame (strict), player visible, telegraph visible.

### 12.4 Recommendation
Provisionally **prefer the 42° variant at size 8** (passes run and dash, ≈8.4 % character height) and **keep 46.7° at size 9 as the fallback**. Reject 7 and 7.5 at 46.7° unless the CD relaxes the criterion. This is a pre-capture prediction; the captures decide. Moving the gameplay camera, or amending Q20's "reuse the existing camera", needs a separate **decision record** after the review, and projection (Q2) stays open.

## 13. D2 — Reference image (approved)
**Decision [APPROVED]:** the generated reference is a **mood and readability study**, not a design specification. It informs light angle and warmth, value structure, character presence, a quiet centre with a dense periphery, and a warm-dominant palette with small accents. It is not traced, measured, or used as a layout, and it is not copied into the repo.
**Exclusions retained (unchanged from §2):** the lion/guardian-beast statue, the gold floor sigil, the red leaf litter, the red ribbon motifs, the tower/obelisk pillar forms, the cliff/ravine backdrop, and any other motif that breaks the locked palette or the quiet-floor rule. Added: nothing in the reference is evidence for the mythology (Q1) or for Hindu iconography; it is an AI-generated illustration with no source provenance.

## 14. D3 — Telegraph test range (provisional)

**Test range [PROVISIONAL]:** fill `#27DCD1` at its normal intensity (use 25 %, inside the locked 22–28 %) and a strike-phase ramp of ≈40–45 %; edge `#9BFFF6`. This is a test range. **Q18 stays resolved, Q21 stays open, and no production value is set.**

**Expected greyscale lift** (fill luma 0.71 minus floor luma, times opacity; gamma-space arithmetic, to be confirmed on captures):

| Floor luma | 25 % | 40 % | 45 % |
|---|---|---|---|
| 0.41 (current art-test floor) | +0.075 | +0.12 | +0.135 |
| 0.33 (target floor) | +0.095 | +0.152 | +0.171 |
| 0.20 (shadowed) | +0.128 | +0.20 | +0.23 |

Threshold from §4 (AC2/AC3): ≥ +0.10 for the fill, ≥ 0.25 for the edge. So the normal 25 % fill **does not** meet the threshold on the current lit floor (and is borderline on the target floor), while the strike ramp does. The early windup therefore has to be carried by the **edge, shape and reveal motion**, which is exactly what Q15 requires ("colour is never the only signal").

**Capture matrix:** 2 surfaces (lit, shadowed) × 3 phases (start, mid, strike) × 3 strike opacities (25 %, 40 %, 45 %) × 2 renders (colour, greyscale). Also a colour-vision-deficiency simulation (deuteranopia and protanopia) of the strike frame. Evaluate each over at least two floor materials and with the enemy standing on the telegraph. Include one frame with the existing orange telegraph to keep current behaviour and target style separate.
**Constraints:** visual-only demonstration in the art-test scene; combat scripts unchanged (T17). The cyan family appears nowhere else in the scene.

## 15. D4 — Git LFS and the untracked art

### 15.1 Findings **[OBSERVED]**
| Item | Finding |
|---|---|
| Git LFS binary | **Not installed**: `git lfs` is not a git command |
| LFS config | `~/.gitconfig` (global) already defines `filter.lfs.*` with `required = true`; the repo has **no `.gitattributes`** |
| Risk | If a `.gitattributes` with `filter=lfs` were added while `git-lfs` is missing, `required = true` would make `git add` fail |
| Remote | `git@github.com:blacurrant/dharma.git`; account plan unknown |
| Repo today | `.git` = 42 MB; largest tracked file = 9.9 MB FBX; largest committed binaries are character FBX/PNG files (no history problem) |
| Untracked art | `Art/` 471 MB + `Assets/ArtTest/` 329 MB = ≈800 MB gross, ≈540 MB unique |
| By type (gross) | PNG 359 MB (Art) + 272 MB (ArtTest); FBX 56 MB + 56 MB; `.blend` 35 MB; `.blend1` backup 17.6 MB; two `.pyc`; small `.json`, `.py`, `.mat`, `.meta` |
| Duplication | `Assets/ArtTest/Environment/` models and textures are copies of `Art/Exports/Environment/Staging/` (sampled hashes identical); Staging is, per `Art/README.md`, a transient validation area |
| Largest single file | none over 40 MB (so GitHub's 100 MB per-file block is not an issue today) |
| GitHub LFS quota (GitHub docs, retrieved this pass) | GitHub Free: **10 GiB storage, 10 GiB bandwidth/month**; each pushed version of a changed file counts in full |

### 15.2 Options
| Option | Assessment |
|---|---|
| A. Plain Git for everything | Works technically (no file > 100 MB) but permanently bloats history; the textures are regenerated by bakes, so every revision adds up to ≈20 MB per file; removing it later needs a history rewrite. **Not recommended** |
| B. Git LFS for all binary art | Standard for Unity; low ongoing cost; needs a tool install and a `.gitattributes`; re-exports consume quota. **Recommended as the base** |
| C. Commit sources and scripts only; regenerate exports | Smallest repo, but the bake pipeline needs Blender and is documented as crash-prone (Metal bake, resumable), so a fresh clone could not open the art-test scene without hours of rebuild. Good for *Staging*, not for what Unity needs |
| D. Keep art outside Git (cloud/NAS) | No repo bloat but no version link between scenes and assets. Fallback only |

### 15.3 Recommendation **[PROPOSED]** (hybrid of B and C)
1. **LFS-track** the binaries Unity or Blender need to open the project: `Assets/ArtTest/**` models and textures (`*.fbx`, `*.png`, `*.exr`, lighting data as needed) and `Art/Blender/*.blend`. Estimated LFS footprint ≈ 350 MB, i.e. about 3.5 % of the free 10 GiB storage.
2. **Do not track** `Art/Exports/Environment/Staging/**` (duplicate, transient), `*.blend1`, `__pycache__/`, `*.pyc`, and the raw bakes in `Art/Blender/Textures/Source/` (regenerable by `02_bake.py`) unless the CD wants them versioned; add them to `.gitignore` as one explicit, reviewed change.
3. **Track normally as text:** `Art/Blender/Scripts/*.py`, `Art/Blender/ENVIRONMENT_KIT_NOTES.md`, the `_build` JSON reports, `Docs/`, and all Unity `.unity`, `.mat`, `.meta` and `.asset` text files. Mark Unity YAML as text in `.gitattributes`, not LFS.
4. **No history migration** is needed: nothing large is already committed.
5. **Separate commits** later: (i) `.gitattributes` and `.gitignore` alone; (ii) docs; (iii) Blender sources; (iv) Unity art-test assets and scene. Verify `git lfs ls-files` and a dry-run size count before each commit.
6. **Interim risk:** until a commit exists, ≈0.5 GB of art lives only on this machine. A plain filesystem backup (outside Git) is advisable now.

### 15.4 Preconditions before any Git action (all need explicit CD approval)
Approve the strategy and the track/ignore lists; confirm the account's LFS quota; install `git-lfs`; confirm the first push goes to a branch, not `main`. **Not done in this pass:** install, `.gitattributes`, `.gitignore` edits, staging, commit, push, history changes.

## 16. D5 — Platform target and budgets

### 16.1 What the documents say **[OBSERVED]**
Nothing. Platform and performance target is **open (Q6)** in `GAME_BRIEF.md`, `ART_BIBLE.md` and `TECHNICAL_OVERVIEW.md` (T2). No locked decision names a platform.
Circumstantial evidence only: development is on macOS (Apple M5); input is Unity Input System with keyboard/mouse bindings; both `PC_RPAsset` and `Mobile_RPAsset` exist (the latter from the Unity template, with no design decision behind it); Build Settings lists only `SampleScene`; the camera and combat references (PoE2-style, Hades-style) are PC-first games. None of this is a target.

### 16.2 Proposed initial target **[PROPOSED, not approved]**
**PC desktop, keyboard and mouse first** (Windows as the primary shipping assumption, macOS supported since it is the development platform), with **controller support planned** for the combat (a Hades-like game benefits) but not scheduled. 1080p at **60 fps** on a mid-range consumer GPU of roughly 2019 class (about a GTX 1660 / base Apple M1). Mobile is out of scope; the `Mobile` quality level and `Mobile_RPAsset` are marked unused, not deleted (Unity Engineer decides later).

### 16.3 Proposed initial budgets for a combat room **[PROPOSED]**
Derived from the measured Editor baseline (≈7.7–8.3 M triangles per frame including shadows, ≈1,900–2,000 draw calls, 1,177 shadow casters, ≈415 MB texture memory, CPU 2.2–3.1 ms, GPU 3.8 ms on an M5) with a margin for lower hardware. **No lower-end hardware has been measured**, so these are starting points.

| Budget | Proposed limit | Basis |
|---|---|---|
| Frame time | 16.6 ms at 60 fps; target ≤ 12 ms GPU and ≤ 8 ms CPU on the minimum spec | Headroom for combat and VFX |
| Triangles per frame (incl. shadow passes) | ≤ 4 M | About half of the current baseline; walls and floor border are the cut candidates (B3) |
| Draw calls / SetPass | ≤ 1,000 / ≤ 100 | Instancing and batching for floors |
| Shadow casters in the main cascade | ≤ 500 | Floors and borders stop casting (A8) |
| Environment texture memory per room (compressed, in a player build) | ≤ 512 MB | Currently ≈415 MB in the Editor, uncompressed estimate unverified |
| Unique environment triangles in the kit | review after the first player-build measurement | Currently ≈516 k |

Validation (unchanged from §6): a development player build, a scripted 60 s run, average / p95 / p99 frame time, and a repeat on the lowest-spec machine available. **Approving this proposal is a CD decision; it closes Q6 and T2.**

## 17. Acceptance criteria for the next visual review (measurable)
Everything in §4 (AC1–AC11) still applies. Added or tightened for this round:
| # | Criterion | Pass |
|---|---|---|
| R1 | Camera matrix complete | Every cell in §12.3 captured as a movement sequence, with the edge-margin metric recorded |
| R2 | 10 m radius | Minimum margin ≥ 0 px on every frame for the chosen configuration; any clipping is listed with its size and frame |
| R3 | Character presence | Chosen configuration yields 8–9 % character height, or the CD accepts the shortfall in writing (§11 row 4) |
| R4 | Telegraph matrix complete | §14 matrix captured in colour and greyscale, lit and shadowed, plus a CVD frame |
| R5 | Telegraph threshold | Strike-phase fill ≥ +0.10 luma over its surface on every surface tested; edge ≥ +0.25; the shape identifiable in greyscale from the edge alone at the start phase |
| R6 | Reservation | Cyan-teal appears only on telegraph objects (checked by a colour-histogram or scene audit of the art-test scene) |
| R7 | Light | Key light ≥ 60° off the camera view direction; floor mean luma 0.30–0.36 in the clear zone |
| R8 | Untouched files | `git diff` confirms none of the protected files in §18 changed |
| R9 | Reference discipline | No excluded motif (§13) appears in the art-test scene |
| R10 | Performance | Player-build numbers recorded against §16.3, even if the budgets are still only proposed |

## 18. Must remain untouched
**Locked decisions:** `ART_BIBLE.md` §0 and §0.1–§0.9, Q15–Q20 (including Q20's "reuse the existing camera"), the cyan-teal reservation, the prototype scope, the abstract-subject rule. Changing any of these needs a written decision record.
**Files:**
- `Docs/ART_BIBLE.md`, `Docs/GAME_BRIEF.md`, `Docs/TECHNICAL_OVERVIEW.md` (committed; edit only through a decision update).
- `Assets/Scripts/Prototype/*.cs`, especially `IsoCameraFollow.cs`, `TrainingDummy.cs`, `CharacterTintFeedback.cs`, `CombatFx.cs`, `PlayerMotor.cs`, `PlayerCombat.cs`, `ArenaEncounter.cs`, `PrototypeHud.cs`.
- `Assets/Scenes/PrototypeArena.unity`, `CharacterRigTest.unity`, `SampleScene.unity` (and their `.meta`).
- `Assets/Characters/**` (including both Paladin materials), `Assets/Materials/Prototype/**`, `Assets/Settings/**`, `ProjectSettings/**`, `Packages/**`.
- `.gitignore`, and no `.gitattributes` until D4 is approved.
- `Art/Exports/Environment/Staging/**` contents (do not promote) and `Art/Exports/Environment/Review/` (stays empty).
**May be edited in the implementation phase (art-test only):** the camera, light, volume and material objects of `ArtTest_TempleCourtyard.unity`, the `Assets/ArtTest/` materials, `Assets/ArtTest/Reviews/` outputs, and `Art/Blender/` sources by the Environment Artist. Camera sizes and the 42° offset are set through the existing serialized fields of the art-test scene's own camera, not through a script change.

## 19. Implementation sequence (after the CD approves the open items)
**Unity Engineer**
1. Freeze a baseline capture set of the unchanged art-test scene (size 9, 46.7°).
2. Build the capture harness: the scripted movement sequence, a frame-sequence recorder, the edge-margin metric, and the greyscale/CVD converters (editor-only, in `Assets/ArtTest/Editor/`).
3. Run the D1 camera matrix (§12.3); record the results in `Assets/ArtTest/Reviews/`; recommend one configuration.
4. Set the key light, ambient, and the post volume per §1; capture; confirm the floor luma target.
5. Run the D3 telegraph matrix (§14) with the demonstration objects only.
6. Take player-build performance numbers against §16.3.
**Environment Artist (in parallel; no new assets)**
1. Measure the floor and wall BaseColor luma and the regularity (the 2 m lattice) from the captures; decide whether B1 (floor re-bake) is triggered.
2. Compose the edge density from the existing pieces for the chosen camera; no new modelling.
3. Answer the arch opening question (4.2 m built vs 5 m documented).
**Game Director**
Collect results, run the acceptance table in §17, and write the decision records: camera (D1 and any Q20 amendment), D3 values (if the CD sets them), D4 strategy, D5 target, Q1 (mythology), and the project name.

## 20. Decisions still needed from the CD **[SUPERSEDED: answered in the CD's direction; remaining items are in Part 3 §28]**
1. **D4:** approve the hybrid LFS strategy and the track/ignore lists (§15.3), or choose another option.
2. **D5:** approve, change or reject the proposed PC target and budgets (§16.2, §16.3).
3. **D1 interpretation:** confirm the 10 m radius means the ellipse around the player (§12.1), and whether a one-frame clip of a few centimetres during a dash may pass.
4. **Project name:** MythicRoguelite or "Half Heaven"?
5. **Hindu mythology:** record it as the Q1 decision, or keep Q1 open? Prototype content stays abstract either way until you do.

---

# Part 3 — Revision 3: CD directions on D1–D5, naming and Q1

**Scope of this revision:** records the Creative Director's directions, integrates the Unity Engineer's and Environment Artist's reports that now exist, corrects one error of mine (§12.2), prepares D4 and takes the verified backup. **No LFS configuration, install, `.gitattributes`/`.gitignore` edit, staging, commit, push or history change; no protected scene, script, material or setting touched.** Locked decisions (`ART_BIBLE.md` §0, §0.9, Q15–Q20) are unchanged.

## 21. Evidence integrated in this revision

### 21.1 Unity camera and lighting pass (`Assets/ArtTest/Reviews/CAMERA_LIGHTING_REPORT.md`) **[OBSERVED, read in this revision]**
| Item | Report says | Consequence here |
|---|---|---|
| Camera | Recommends ortho 9, offset unchanged, a **focus bias of 1.4 m toward the dais** and a 35 % pull toward the enemy via the scene-local helper `ArtTestCameraFocus`. Verified only in **frozen poses**. Size 8 "clipped once the focus shifts" | D1 must be decided by **moving** captures. The bias consumes the margin in §12.2, so it is a separate variable (§22) |
| Cyan telegraph | The earlier "fill invisible" finding was a **demo bug** (reversed winding, back-face culled). Fixed: fill #27DCD1 at 26 % rising to 46 % toward the strike, edge #9BFFF6 (0.10 m); the original orange renderers are hidden **in this scene only** | Part 1 and Part 2's statements that the fill is invisible are superseded. The preview already runs a 26→46 % ramp; 46 % is 1 point above the approved 40–45 % test range and should be capped at 45 % for the formal test |
| Lighting | Warm Mixed key (1.00, 0.89, 0.74) at 1.3, euler (46, 318, 0); trilight ambient; neutral tonemap and low bloom; 207 baked light probes; actor point lights; fog and reflection probe tested and removed | **Computed from the saved scene's quaternion: the key travels only ≈ 2° off the camera's view direction** (3° in the horizontal plane; it was ≈ 10° before), so the scene is still **front-lit and flat**. The warmth and softness improved, but the direction problem from §1 is not fixed and fails R7 (≥ 60°). The report calls lighting "verified" without flagging this. A side or three-quarter-back key is still required before judging floor value, form and telegraph legibility |
| Lightmaps | **Failed** (blown-white mosaic, reproduced even on Unity primitives); scene uses probes only; Rosetta not installed (CPU lightmapper unavailable) | No lightmap-dependent decision may be taken. Five open questions go to the CD (§28) |
| Performance (Editor, indicative) | Size 11: 2,068 draws, 9.2 M tris. Size 9: 1,532 draws, 5.48 M tris, CPU 4.47 ms, GPU 3.2 ms. Size 8: 1,217 draws, 3.95 M tris. Culling shrinks cost with smaller sizes | Against the provisional budgets (§24) only size 8 is near the triangle target; **no size meets 1,000 draws yet**. Not a player build |

### 21.2 Environment Artist audit (`Art/Blender/Revisions/v2_study/ART_DIRECTION_AUDIT.md`) **[OBSERVED]**
A read-only study; no remodel; `TempleEnvironmentKit.blend` and `Art/Exports/` unchanged (checksums per the audit). Its findings that matter here: the kit's **sun-disc / ring-and-ray motif** appears on about 100 instances (modelled geometry, not texture); the palette is sand/tan; the arch's impost narrows the opening to **4.19 m** (notes said 5 m); the floor is a regular 2 m grid; material zones were lost after baking (pipeline gap M6). Its own list of six decisions is carried into §28 because the CD's direction does not cover them. It independently avoids teal in moss/verdigris (consistent with the cyan reservation).

## 22. D1 and D3 — approved test protocol (supersedes §12.3 and the §14 capture matrix)

**Approved by the CD:** test **42° pitch at orthographic size 8** against the existing **size 9 / 46.7°** setup and the **size 11** baseline, in the art-test scene only; running, dashing, attacking and dodging captures decide; preserve the full required combat area during movement; no change to the production camera script. Test the **40–45 % strike-phase fill ramp**; keep the normal windup readable through edge, shape and reveal motion; no production combat-script change until the in-engine test passes.

| Config | Pitch | Ortho size | Offset (serialized on the art-test scene's own `IsoCameraFollow`) | Role |
|---|---|---|---|---|
| **A** | 42° | 8 | (12, 15.28, −12) | Candidate |
| **B** | 46.7° | 9 | (12, 18, −12) | Existing art-test setup (also the Unity Engineer's recommendation) |
| **C** | 46.7° | 11 | (12, 18, −12) | Q20 baseline; matches `PrototypeArena` (which is read, never edited) |

- **Implementation constraint:** pitch and size are set only through serialized fields on the art-test scene's camera; `IsoCameraFollow.cs` and `PrototypeArena.unity` stay untouched. If 42° cannot be set that way, drop config A and report it.
- **Focus bias is a separate variable.** Run every config **unbiased (pure player follow, as production)** first. Optionally repeat B and A with the Unity Engineer's bias (1.4 m, 35 % enemy pull) to measure what it costs. The decision on the production camera cannot rely on a biased result unless the CD adopts the bias deliberately.
- **Sequences per config (moving, recorded as frame sequences, ≥ 60 fps and once uncapped ≥ 144 fps because the lag grows with frame rate):** idle; run in 8 directions (2 s each, stressing up-screen and down-screen); dash from rest and from running in 8 directions; attack with the enemy at its spawn; **dodge**: let the enemy wind up, dash through the telegraph; chained run → dash → attack; a full telegraph cycle with the player at the 10 m edge.
- **Per-frame measurements:** minimum pixel margin between the frame edge and the projected 10 m ground ellipse around the player; character height as a percentage of frame height; whether player, enemy and the active telegraph are all in frame.
- **Telegraph captures (within the same sequences):** start, mid and strike phases; fill at 25 % (normal), 40 % and 45 % (strike); over a lit floor and a shadowed floor; colour and greyscale; one deuteranopia and one protanopia render of the strike frame. The measurement is the greyscale luma difference between the fill and the same pixels rendered **without** the telegraph, as the Environment Artist did, because they are the only unbiased measure.
- **Pass (strict, as the CD asked to preserve the full area):** margin ≥ 0 px on every frame; player, enemy and telegraph visible; strike-phase fill lift ≥ +0.10 luma on every surface tested and edge ≥ +0.25; the windup shape identifiable in greyscale from the edge and reveal alone at the start phase. Two independent estimates already disagree on how weak the 25 % fill is (arithmetic: +0.075 to +0.095; Environment Artist's Blender renders: +0.049 to +0.078), and neither is an in-engine measurement, so the test must produce the real numbers.
- **Result recording:** a short table (config × sequence → min margin, character %, telegraph lift) and a written recommendation. Adopting any config for the production camera, or amending Q20, needs a separate decision record from the CD.

## 23. D4 — Git LFS: approved in principle, conditional

### 23.1 Precondition status
| # | Precondition (from the CD) | Status |
|---|---|---|
| 1 | File-level tracking and ignore-list review | **Draft complete (§23.2); awaiting CD sign-off** |
| 2 | Separate backup of the untracked art created **and verified** | **Done** (§23.3) |
| 3 | Git LFS installed and functional before adding LFS-tracked files | **Not met.** `git lfs` is not available; not installed in this pass. Plan: install, then prove it in a throwaway scratch repository outside this project (`git lfs install --local`, track a small test file, commit, check `git lfs ls-files` and a clone round-trip) before touching this repo |
| 4 | No history migration, commit or push | **Respected** |

### 23.2 File-level review (draft, 635 files / 798 MB in the backup scope)
| Disposition | Files | Size (MB) | What |
|---|---|---|---|
| LFS | 2 | 35.2 | `.blend` masters and study copy (`Art/Blender/**/*.blend`) |
| LFS | 93 | 255.7 | Unity art-test models, textures, baked lighting (`Assets/ArtTest/**` `.fbx/.png`, scene lighting `.exr`) |
| LFS | 23 | 52.2 | Blender review renders and v2-study renders (`Art/Blender/Renders`, `Revisions`) |
| LFS (CD choice) | 58 | 71.8 | Unity review captures (`Assets/ArtTest/Reviews/*.png`); could instead be kept only for accepted reviews |
| CD choice: ignore or LFS | 93 | 105.6 | Raw bakes (`Art/Blender/Textures/Source/**`), regenerable by `02_bake.py` |
| Ignore | 2 | 0.1 | Python bytecode (`__pycache__`, `*.pyc`) |
| Ignore | 1 | 17.6 | Blender auto-backup (`*.blend1`) |
| Ignore | 1 | 1.3 | Unapproved reference holding folder (Art Bible §10.2: nothing unapproved is committed) |
| Ignore | 92 | 255.6 | `Art/Exports/Environment/Staging/Models` and `/Textures` (duplicate of `Assets/ArtTest`, transient) |
| Normal Git (text) | 270 | 2.8 | Scripts, notes, JSON/CSV, Unity `.meta/.mat/.unity/.asset`, `.gitkeep` |

LFS-bound total ≈ 415 MB gross; ignored ≈ 275 MB; the 106 MB of raw bakes await a CD choice (if kept in LFS the total is ≈ 520 MB, about 5 % of the free 10 GiB per GitHub's documentation). Each re-bake pushes complete new copies, so re-exports consume quota.

**Proposed rules (text only, nothing applied).** Scope every LFS pattern to the new art folders, never a global `*.png`: a global rule would retroactively disagree with the PNG/FBX files already committed under `Assets/Characters/` and make them appear modified.
```
# .gitattributes (proposed)
Art/Blender/**/*.blend           filter=lfs diff=lfs merge=lfs -text
Art/Blender/Renders/**/*.png     filter=lfs diff=lfs merge=lfs -text
Art/Blender/Revisions/**/*.png   filter=lfs diff=lfs merge=lfs -text
Assets/ArtTest/**/*.fbx          filter=lfs diff=lfs merge=lfs -text
Assets/ArtTest/**/*.png          filter=lfs diff=lfs merge=lfs -text
Assets/Scenes/ArtTest_TempleCourtyard/*.exr  filter=lfs diff=lfs merge=lfs -text
# Unity YAML (*.unity, *.mat, *.asset, *.lighting, *.meta) stays plain text

# .gitignore additions (proposed)
Art/Exports/Environment/Staging/Models/
Art/Exports/Environment/Staging/Textures/
Art/Blender/Reference/_unapproved_holding/
Art/Blender/Textures/Source/        # only if the CD chooses "ignore"
*.blend1
__pycache__/
*.pyc
```
Notes: the placement table in `Staging/` (`TempleCourtyard_Placement.json/.csv`, small) is **not** ignored. A fresh clone needs `git lfs pull` before Unity can open the scene. The unapproved reference stays out of Git by the Art Bible's own rule (§10.2). Whether `Assets/ArtTest/Reviews` (72 MB of PNG captures) is versioned in full or only for accepted reviews is a CD choice. The Environment Artist's second `.blend` (`Revisions/v2_study/TempleEnvironmentKit_v2_study.blend`, 18.5 MB) is covered by the `*.blend` rule.

### 23.3 Backup **[DONE and verified]**
| Item | Value |
|---|---|
| Location | `/Users/landerstudio/Backups/MythicRoguelite_untracked_art_20261025_0021/` (outside the repository) |
| Contents | `Art/` (all), `Assets/ArtTest/` and its `.meta`, `Assets/Scenes/ArtTest_TempleCourtyard*` (scene, folder, `.meta`s), `Docs/ART_REVIEW_001_VISUAL_TARGET.md` as it was before this revision, and `Art_README_tracked_modification.patch` (diff of the tracked `Art/README.md` edit) |
| Verification | Every file hashed with SHA-256 in the source and in the backup: **635 files, 836,762,448 bytes, 0 missing, 0 extra, 0 mismatches**; manifest saved as `MANIFEST_sha256.json` in the backup folder; nothing newer than the backup was found afterwards |
| Limits | **Same internal disk as the source**, so it does not protect against disk failure, loss or theft; copy it to a second device or cloud store. It is a snapshot: files created later are not in it and the review document itself is edited in this revision. Re-run the copy and the hash check immediately before any LFS configuration |
| Not backed up | `Library/` (regenerable), the committed history (it is in Git), and the live Blender session |

## 24. D5 — Platform target (provisional)

**Provisionally approved by the CD:** PC desktop, keyboard and mouse first, controller support planned, 1080p at 60 fps. The budgets in §16.3 are **initial targets pending player-build measurements**, not hard limits.

| Budget (initial target) | Value | Current Editor reading (Unity Engineer, size 9 / size 8) | Reading |
|---|---|---|---|
| Triangles per frame incl. shadows | ≤ 4 M | 5.48 M / 3.95 M | Size 9 over, size 8 near |
| Draw calls | ≤ 1,000 | 1,532 / 1,217 | Over at all tested sizes |
| Shadow casters | ≤ 500 | not re-measured (1,177 earlier) | Floors and borders cast shadows |
| Environment texture memory per room | ≤ 512 MB | runtime textures 628 MB (Editor) | Over; compression not yet applied |
| Frame time | ≤ 16.6 ms; CPU ≤ 8, GPU ≤ 12 ms on minimum spec | CPU 4.5 / 3.8 ms, GPU 3.2 / 2.7 ms on an M5 | Fine on this hardware; minimum spec unmeasured |

Still open: the **minimum-spec reference machine** (my "2019-class mid-range GPU" was a proposal, not an approved spec); a **player build** measurement; macOS parity expectations. These numbers are Editor Play Mode with post and lights and vary with camera size; they are not evidence about lower-end hardware. Q6 and T2 are **provisionally** answered, not closed.

## 25. Naming and Q1 creative direction

**Naming [APPROVED].** "Half Heaven" is the intended creative title. `MythicRoguelite` remains the internal repository and project name; the repository, the remote (`blacurrant/dharma`) and project assets are **not** renamed. This document and the committed docs keep `MythicRoguelite`. No document is retitled until the CD asks. Use "Half Heaven" only in creative-facing text.

**Q1 direction [RECORDED, partial].** *Distinct fantasy rooted in Hindu traditions, avoiding generic or stereotypical mythological-game imagery.* The existing locked decision stands: **the first prototype stays abstract (Q19)**. **Research and sensitivity review are prerequisites before introducing specific deities or sacred symbols.**
- **Consistency with locked text:** compatible with `ART_BIBLE.md` §0 ("original mythological identity"), §1 (motifs trace to the project's mythology or real historical sources), §11.1 and Q19 (no specific deity or culture in the first prototype). Abstraction is a holding state for the prototype, not the end state of the world.
- **What stays open under Q1:** which traditions, texts and regions; tone; the story premise; what "distinct" means visually; the list of imagery to avoid. These are for research, not assumption. Hindu architecture is not one style (regional temple traditions differ), so "rooted in Hindu traditions" cannot be answered by one vocabulary; the research brief should name specific, sourced traditions chosen by the CD.
- **Research and sensitivity gate (proposed process):** (1) a research brief with primary architectural and archaeological sources and named advisors or reviewers; (2) a written do/avoid list for the kit; (3) review of every motif before it enters a model; (4) no deity, figure, sacred symbol or ritual object before the gate passes.
- **Immediate consequence for the existing kit:** the ring-and-ray / sun-disc language on ~100 instances is currently "celestial geometry", allowed by Q19. Under a Hindu-rooted direction a solar disc or wheel can read as specific symbolism and needs the review above. The Environment Artist has independently asked for approval to remove it. **No removal is decided here**; it is held for the CD (§28 item 1).
- **Recording:** captured in this document only. Mirroring it into the committed `GAME_BRIEF.md` (§6, Q1 row) and `ART_BIBLE.md` (§0.8, §12 Q1) is a separate documentation change that needs the CD's go-ahead.

## 26. Revised acceptance criteria for the next visual review
§4 (AC1–AC11) and §17 (R1–R10) stand except as follows.
| # | Change | Pass |
|---|---|---|
| R1 | **Replaced** by the three-config matrix in §22 | All sequences captured as moving frame sequences at ≥ 60 fps and uncapped |
| R2 | Strict | Minimum margin ≥ 0 px on every frame of every sequence for the adopted config; every clip listed with its size and frame |
| R3 | Unchanged | Adopted config gives 8–9 % character height, or the CD accepts the shortfall in writing |
| R4–R5 | Clarified | Telegraph lift measured against a no-telegraph render of the same pixels; ramp capped at 45 % |
| R11 | New | Backup verified (§23.3) and re-verified immediately before any LFS configuration |
| R12 | New | `git-lfs` proven in a scratch repository before any LFS file is added to this repository |
| R13 | New | CD signs the file-level list (§23.2), including the two open choices (raw bakes; Reviews captures) |
| R14 | New | `git diff` shows no change to any protected file in §27; the art-test camera size and pitch were set through serialized fields only |
| R15 | New | No deity, figure, sacred symbol or ritual object appears in any capture or model until the Q1 research gate has passed |
| R16 | New | The unbiased camera result is reported separately from any focus-bias result |

## 27. Must remain untouched (confirmed, with additions)
All items in §18, plus:
- `.gitignore` and `.gitattributes` (does not exist): no creation or edit until D4's preconditions are met and the CD approves.
- `Assets/Scripts/Prototype/IsoCameraFollow.cs` and every other script in `Assets/Scripts/`: pitch and size are scene-serialized values only.
- `Assets/Scenes/PrototypeArena.unity`, `CharacterRigTest.unity`, `SampleScene.unity`, shared URP assets (`Assets/Settings/**`, so no SSAO added to `PC_Renderer`) and `ProjectSettings/**`.
- Both Paladin materials and everything under `Assets/Characters/`.
- The backup folder in §23.3 (read-only reference; do not edit its contents).
- `Art/Blender/TempleEnvironmentKit.blend` and `Art/Exports/**` (the Environment Artist reports them unchanged; further changes only by the Environment Artist on an approved task).
- Repository name, remote and asset names (naming decision).
**Editable in the implementation phase (art-test only):** the camera, light and volume objects of `ArtTest_TempleCourtyard.unity`, `Assets/ArtTest/**`, `Assets/ArtTest/Reviews/` outputs, and the Environment Artist's `Art/Blender/Revisions/**`.

## 28. Open items after this revision
**Needs the CD**
0. **Key-light direction:** the saved key is ≈ 2° off the camera's view (§21.1). Confirm that the Unity Engineer should rotate it to a side or three-quarter-back key (target ≥ 60° off, 35–45° elevation, as in §1) **before** the §22 camera and telegraph tests, because front light changes every luma number being measured. This is an art-test-scene change only.
1. **Ring / sun-disc motif** (~100 instances): approve removal, or hold for the Q1 research gate (Environment Artist's decision 1; now linked to Q1).
2. **Central structure** option 1, 2 or 3 (or a different direction); no figurative statue without explicit approval (audit decision 2).
3. **Stone palette**: desaturated warm grey with olive (not teal) moss (audit decision 3); exact values still Q11.
4. **Telegraph fill strategy (Q21)**: fill opacity, inner stripe or darker combat floor, after the §22 test.
5. **Lighting ownership** (audit decision 5) and the Unity Engineer's five questions: accept probes-only GI or commission clean lightmap UVs; allow editing the shared `PC_Renderer` for SSAO (it would also change `PrototypeArena`); accept the scene-local telegraph as the reference for a later real-script change; rim/outline treatment for the Paladins and skirt geometry; permission to install Rosetta (a system change) for CPU lightmap tests.
6. **D4 sign-offs:** the file-level list and its two open choices (§23.2); authorisation to install `git-lfs` and run the scratch-repo test.
7. **D1 details not yet answered:** confirm that "10 m radius" means the ellipse around the player (working assumption, §12.1), and whether the focus bias may be part of an adopted camera.
8. **Budget stance** (audit decision 6): tileable trims and decals instead of unique atlases once Q3/Q10 settle; the **minimum-spec machine** for D5.
9. **Q1 follow-up:** who runs the research and sensitivity review, and whether to mirror the Q1 direction into the committed docs now.
10. **Backup:** copy the verified snapshot to a second device.
**Not yet done / waiting:** the moving-capture camera and telegraph tests (§22); the player-build performance run; `git-lfs` install and scratch-repo proof.

## 29. Sequence (gated)
**Unity Engineer**
0. If the CD confirms (§28 item 0): rotate the art-test key light away from the view direction first, then freeze it for all runs, so the three configs are compared under one light.
1. Extend the harness to run the §22 sequences (moving, uncapped and capped), cap the demo ramp at 45 %, and add the no-telegraph pair render and the min-margin metric (editor-only, art-test folder).
2. Run configs C, B, A unbiased; then biased B and A; record the table; recommend one.
3. Run the telegraph captures inside the same sequences; report real luma lifts.
4. Player-build performance run against §24.
**Environment Artist**
1. Hold remodelling until items 1–3 in §28 are answered. Do M6 (persist material zones) and G1 (arch cornice) only if the CD approves, since they do not depend on the motif decision.
2. Prepare the research-gate checklist input for Q1 (§25), not new motifs.
**Game Director**
1. Keep the backup current; run the §23.1 checklist; write the decision records (camera, telegraph values, D4 strategy sign-off, D5 closure, Q1) once the evidence exists.
2. Start no LFS action until preconditions 1, 3 and 4 are satisfied and the CD says so.

---

# Part 4 — Creative Director directions log (revision 4)

Decisions and status only. No LFS action, commit, staging, push or promotion has been performed. Locked decisions are unchanged.

| # | Direction (Creative Director) | Status | Owner / next step |
|---|---|---|---|
| 4.1 | Verify three more assets for the material-zone repair (Altar_A, one lathe-built pillar, Banner_A) in the separate working copy before the production `.blend` is migrated | **[APPROVED]** | Environment Artist; must state its independent-evidence method for the lathe-built parts first (their saved UVs differ from a fresh rebuild's). Production `.blend` stays unmigrated |
| 4.2 | Leave the Unity-generated changes in place and exclude them from commits: `Assets/Characters/Player/Materials/Paladin_MAT.mat`, `Assets/Characters/Enemy/Materials/Paladin_Enemy_MAT.mat`, `ProjectSettings/Packages/com.unity.pipeline/EditorPipelineConfig.json` | **[APPROVED]** | Stage explicit paths only when commits are authorised. Provenance (QA, verified against git): the enemy `_Color` legacy field was synced to the already-committed `_BaseColor`; the player material regained a keyword that commit `a061e7e` had removed; the config holds run-in-background flags set by the Unity tooling. Exact save trigger at 01:17:20 not proven |
| 4.3 | Unity MCP: stay file-based until the current camera matrix finishes | **[APPROVED]** | Revisit after the matrix; QA validates from files |
| 4.4 | Floor tone and material changes wait for the telegraph measurements | **[APPROVED / on hold]** | Unity Engineer measures the telegraph luma lift; the Director then reports whether the floor should change |

**Evidence recorded this revision**
- Key light rotated and frozen at euler (38°, 45°, 0°): **63.4° off the view direction (90° horizontal), elevation 38°**, verified from the saved scene. The old key was 2.2° (3.0° horizontal). Captures: `Assets/ArtTest/Reviews/Gate1/`. Camera size 9 and offset unchanged.
- Measured floor after the rotation (Director, 1080p capture): mean luma 0.38 (was 0.40), red/blue ratio 1.49 (was 1.52), whole-frame 5th percentile 0.18 (was 0.31). Direction is fixed; the floor is still brighter and less warm than the unapproved §1 targets (0.30–0.36, R/B 1.6–1.9).
- The Unity Engineer withdrew the earlier "~98 px" Paladin height; the matrix runner measures projected head-to-feet height per frame.
- The matrix currently running is plain follow with focus OFF; a second pass adds the far-enemy chase (focus ON and OFF), the 10 m ellipse drawn on frames and raw performance samples at 1920×1080. Results pending.

---

# Part 5 — Revision 5: Gate 1 results, Gate 1b outcome, MCP restoration status

No commit, staging, push, LFS action, promotion, production-Blender migration or art-direction lock was performed. Locked decisions unchanged.

## 5.1 Creative Director decisions logged
| # | Decision | Status |
|---|---|---|
| 5.1 | Material-zone verification (Altar_A, a pillar, Banner_A) in the working copy; production `.blend` not migrated; unexplained arch-pier faces and re-bake outliers documented; QA independent review | **[APPROVED and DONE]** (Gate 1b, `Art/Blender/Revisions/gate1_zones/GATE1B_REPORT.md`; QA: Banner_A PASS, Pillar_C PASS with 115 unexplained faces, Altar_A PASS at texel level and UNVERIFIED for 40,249 faces under 9 px²). Still not baked/compared: Pillar_A/B/D, Arch_A_Span, walls, floors, stairs, platform, rubble |
| 5.2 | Unity-generated tracked changes stay in place; excluded from any environment commit; diffs rechecked before any future commit | **[APPROVED]**. The set is now **four** files: `Paladin_MAT.mat`, `Paladin_Enemy_MAT.mat`, `EditorPipelineConfig.json` and `ProjectSettings/ProjectSettings.asset` (`runInBackground` 0→1, written 02:15 when the Editor closed; the Unity Engineer reports having reverted this file once earlier, before the Director's no-revert instruction) |
| 5.3 | Unity MCP restoration for Unity Engineer and QA via their profile configurations, evidence and configs preserved first, no interruption of an active matrix run, verify tool access, isolated from Unity assets and settings | **[APPROVED; backup done; restoration BLOCKED on the Editor, see 5.3 below]** |

## 5.2 Gate 1 results (Unity Engineer, `Assets/ArtTest/Reviews/Gate1/GATE1_REPORT.md`; Editor-only; Director spot-checked the worst-margin values against the raw CSVs)
- **Key light:** now euler (38°, 45°, 0°): 63.4° off the camera view (90° horizontal), 38° elevation, verified from the saved scene.
- **Margin of the projected 10 m circle around the player, plain follow (focus OFF), all 22 sequences each, capped and uncapped:** A (42°/8) worst **+49 px**, B (46.7°/9) worst **+44 px**, C (46.7°/11) worst **+165 px**. **No negative margin in any sequence.** A, B and C all keep the circle in frame in real running, dashing, attacking, dodging and chasing.
- **With the focus-bias helper ON** (A and B at 60 fps cap only; C not run): **clips** (A worst −111 px, B worst −89 px). The bias helper is therefore not acceptable as a baseline camera.
- **Player/enemy inside the frame:** B and C 0 frames outside; **A: 35 frames of 19,175 (0.18 %) outside, all in the far-enemy chase going up-screen** (enemy 9 m away). Under the strict criterion A has a small, localised failure.
- **Character height (silhouette diff from captures, standing):** A median **11.0 %** of frame height (lowest 8.0 %), B **9.5 %** (lowest 5.5 % in a low dash pose), C **7.8 %**. Mesh bounds: player 2.02 m, enemy 2.21 m. The earlier "~98 px" figure is withdrawn.
- **Fixed 10 m zone at the arena centre** cannot stay fully in frame at the arena edge in any config (expected; the criterion was interpreted as the circle around the player, which is still **not confirmed by the Director**).
- **Telegraph luma lift (Rec.709 on the tonemapped frame, same pixels with/without; held pose, not combat validation):** lit floor fill mean +0.133 (26 %) / +0.158 (40 %) / +0.172 (45 %); shadowed floor +0.204 / +0.250 / +0.264. Means clear the +0.10 fill threshold everywhere. Edge+front mean on the **lit** floor is +0.188 / +0.206 / +0.228, **below** the proposed +0.25; on the shadowed floor +0.282 to +0.340 (above). The weakest 10 % of fill pixels (p10) are only +0.017 to +0.091. Thresholds are the Director's to apply.
- **Performance (Editor, 1920×1080, uncapped, vsync off, 2 repeats, raw samples saved; GPU time unavailable):** triangles A 4.48 M, B 5.17 M, C 7.89 M; draw calls 1,267 / 1,366 / 1,778; shadow casters 743 / 804 / 1,050; median frame 5.4–5.6 / 4.6 / 5.8 ms. All three are over the provisional ≤1,000 draw-call, ≤500 shadow-caster and ≤4 M triangle targets. Size 8 measured slower than size 9 despite less geometry (measured last; order effect not separable).
- **Data hygiene:** each per-config CSV contains every row twice (the report counts de-duplicated); the focus-ON set omits C.
- **Not verified:** QA has not yet reviewed this report; no GPU time; no player build; no CVD renders; HUD obstruction not measured.

## 5.3 MCP restoration: findings (nothing in any profile config was changed)
- **Backup before any action:** `/Users/landerstudio/Backups/MythicRoguelite_pre_mcp_restore_20261026_1220` holds the `config.yaml` of every profile, the full `Assets/ArtTest/Reviews/` tree, the `gate1_zones` tree, this document and the working-tree diff of the Unity-generated files; 628 files, 783 MB, SHA-256 verified, no mismatches. Same internal disk.
- **Config is not the cause.** `unity-engineer`, `qa-reviewer`, `designy` and `environment-artist` have byte-for-byte equivalent `mcp_servers.unity` blocks (`/Users/landerstudio/.unity/bin/unity mcp`, `enabled: true`); `hermes -p <profile> mcp list` shows it enabled. Designy's earlier recovery was not a config edit but an in-session `manage_connections` **enable** of the `unity` MCP server.
- **Why the connection failed:** the profile logs show `unity (not attempted (in retry cooldown))` for every profile at start-up. The cooldown is in-memory exponential back-off (30 s up to 600 s) after a failed start, and the `unity mcp` bridge can only expose Editor tools while an Editor is running.
- **Current state:** **no Unity Editor process is running** (the Editor log ends at 02:15 with a clean shutdown). A fresh bridge test (`hermes -p qa-reviewer mcp test unity`) connects in about 1.9 s but exposes **one** tool, `unity-cli-status`, reporting that no Unity Editor tools are available. Tool access therefore **cannot be verified** until an Editor is open.
- **Procedure once an Editor is open (no restart of any profile needed):** each of the two bots runs the `manage_connections` enable action for the `unity` MCP server, then proves access with `list_instances`, the compile status and one read-only scene query, and saves the output as a file. QA uses read-only tools only. Role prompts are not a permission boundary: QA's Unity toolset is not restricted, so `hermes mcp configure` could limit QA to read-only tools (**proposed, not applied**).

## 5.4 MCP restoration: controlled retry result (13:21-13:23 IST)
Decision logged: **[APPROVED]** one controlled retry of the `unity` MCP enable for the Unity Engineer and QA Reviewer; no automatic retry; no profile, permission or allowlist edits.
- **Cause of the first failure [OBSERVED, inferred]:** both first enable requests (12:57:36) settled by deadline after exactly 300 s with no approval. The second pair, approved by Nishant in the desktop app, settled `connected` / `all_resolved` after about 70 s. An approval click is therefore required, and the bots' tool lists refreshed in the same session with no restart.
- **Unity Engineer: PASS** on bridge, visibility, read-only calls and evidence (`list_instances`, `list_open`, `eval`: Main Editor, pid 75473, project path correct; not playing/compiling/updating; scene `ArtTest_TempleCourtyard` not dirty; key light euler (38.00, 45.00, 0.00)). Evidence: `Assets/ArtTest/Reviews/Gate1/MCP_RESTORE_UNITY_ENGINEER_RETRY.md`. Note: `eval` executes arbitrary C#; the expression used was read-only.
- **QA Reviewer: PASS** on bridge, visibility and read-only calls (`list_instances`, `recompile_status`, `list_open`, `get_fields`: key-light quaternion (0.3008, 0.3618, -0.1246, 0.8735) = euler (38, 45, 0); `IsoCameraFollow` offset (12, 18, -12), orthographicSize 9, matching the saved scene). **UNVERIFIED:** whether the Editor is in Play Mode (no read-only tool reports it; QA did not use `eval`). Evidence: `MCP_RESTORE_QA_RETRY.md`, which holds a **proposed, unapplied** read-only allowlist. Classification was mostly by tool name (8 schemas read) and is unverified.
- **Discrepancy:** the enable listed 110 Unity tools, while the bridge test showed 166. Not explained.
- **Integrity after retry:** tracked diffs identical to the pre-retry snapshot; configs, scene and the four Unity-generated files unchanged; only two new evidence files added.

---

# Part 6 — Revision 6: Milestone change to the Visual Foundation

## 6.1 Creative Director direction [APPROVED]
The next milestone is the **visual foundation**: camera, character scale, lighting and environment reading as one coherent experience. The first playable combat loop is **queued**, not cancelled. This is an art-direction milestone, time-boxed, and not licence for indefinite polishing. Work is changed-and-tested in the scene, with comparable Game-view captures, not further plans. Earlier numeric floor targets (for example luma 0.30-0.36) are now **proposals, not requirements**. The earlier "hold the floor" direction is lifted for isolated art-test changes only, because the telegraph measurements have arrived.

## 6.2 Starting evidence
- The attached screenshot (Desktop, 13:42) is a **Scene view** (editor grid, light gizmos, grey void beyond the walls). It is not Game-view evidence, and the brief itself requires inspecting the Game view first.
- What the Scene view does show: one repeating tan flagstone floor with little value or tint variation; walls with some dark bands; the arch opens onto empty grey; the altar and ring read as a focal point but with weak value contrast against the walls; characters are small in this view (not representative).

## 6.3 Ownership and constraints
| Owner | Scope |
|---|---|
| Unity Engineer | New scene `Assets/Scenes/ArtTest_VisualFoundation.unity` (copy; the original scene stays byte-identical), outputs under `Assets/ArtTest/VisualFoundation/`. Game-view baseline, camera A/B/C with HUD obstruction and enemy height, lighting variants (one variable at a time, max 8), Unity-side environment changes using new material instances or overlays and existing kit props only |
| Environment Artist | Working-copy textures under `Art/Blender/Revisions/vf_handoff/`: floor macro variation, wear, rain-wash, mineral, restrained moss, soot; palette/usage note; recommendation on whether zone baking can deliver floor variation (floor parts were not baked in Gate 1b); prop placements from existing parts |
| QA Reviewer | Baseline checksums, comparability rules, validation of iteration 1 (read-only via MCP) |
| Designy | Gameplay and encounter work queued behind the baseline |

Unchanged: style [LOCKED]; cyan-teal reserved for telegraphs; sun/ring motif not removed or multiplied; central 20 m combat area kept clear of props (Q20); production camera script untouched; focus helper separately controllable, default OFF; the four Unity-generated files excluded; production `.blend` and `Art/Exports` untouched; no staging, commit, push, LFS or promotion.

## 6.4 Exit criteria
Comparable 1920x1080 Game-view captures with HUD; camera settings and measured player and enemy screen heights; lighting settings with side-by-side comparisons; a numbered list of environmental improvements with before/after; remaining defects and recommended next changes. Complete when characters, environment, camera and lighting read as one coherent look, as judged by the Creative Director. Not required: every asset final or every audit closed.

## 6.5 Iteration 1-2 results and a correction [OBSERVED; QA validation of iteration 2 pending]
- **Correction of the Director's earlier report:** the camera table from VF iteration 1 (A -76 px, A2 +53, B +16, C +130) is **invalid**. The Unity Engineer found a harness bug: the runner changed orthographic size and offset but did not re-aim the camera, so A and A2 ran with the previous config's pitch. QA had flagged the A and B discrepancy against Gate 1; the Director relayed the invalid numbers before the cause was known.
- **Corrected minima (scripted dash/attack/dodge, per-frame log, ring around player):** A +23 px, A2 +72, B +39, C +130; all minima are the 22 m/s dodge dash toward the top edge, 0 hits taken. **Gate 1 input set (8 directions, capped 60, real injected keys):** A2 worst +58 px, B +45 px, player never out of frame, telegraphs fully in frame. Uncapped is **UNVERIFIED** (Editor tops out near 65 fps). A first run with no player movement (Input System dropped keys while the Editor was unfocused) was discarded and kept as `gate1set_INVALID_no_player_movement`.
- **Lighting (probes rebaked each variant, camera B):** only the lower key (elevation 32, F2) improved player separation (-0.087 to -0.074) and telegraph lift (0.133 to 0.140); yaw 75 alone made separation slightly worse; F3 (both) differs from F2 mainly in shadow direction; warm/cool ambient is a small effect. Floor luma 0.385-0.407 across variants (proposal band 0.30-0.36 is not a requirement).
- **Character separation:** a per-character rim spot light, a lighter central floor and a cool ambient tint **did not** improve separation; the rim light was not confined to characters (the renderer ignores light layers) and dimmed the telegraph. The dark figure on a mid-tan floor remains the main visual defect. [APPROVED by Director within the Part 6 brief] art-test-only character-material copies (albedo lift, rim) assigned in the VF scene, with no change to originals, shared renderer or protected scripts.
- **Not approved / not done:** rendering-layer or renderer-feature changes; any edit of the original Paladin materials.
- **Environment pass (iteration 1):** small at gameplay scale; clearest gain is the warm pool at the dais. The Environment Artist's textures are cleared for Unity and untested there.
- **Open:** altar sits at the NW corner (about -14.1, +14.1), not at the arena centre (confirmed from the saved scene by QA); camera choice; Unity MCP tools dropped again after a script recompile, one approval needed.

## 6.6 QA validation of iteration 2 (QA, read-only) and corrections to 6.5
- **The cause stated in 6.5 is not supported.** The Unity Engineer said the runner did not re-aim the camera, so A and A2 ran at the previous pitch. QA found that in the kept artifact run the -76 (A) and +16 (B) occur at **frame 0, idle phase**, with a 122-125 px player offset, and every other phase is identical between the artifact and corrected runs (A: run 72, dash 72, attack 73, wait 84, dodge 23). A wrong pitch would have changed those too. The likely cause is a **frame-0 camera-follow transient** (camera not yet snapped to the player when recording began). `IsoCameraFollow.LateUpdate` already re-aims from `offset` every frame. The invalid iteration-1 table is still invalid; the cause is **[OBSERVED, not isolated]**. One unexplained difference remains: config C dodge phase 147 px (artifact) vs 130 px (corrected).
- **Camera numbers: PASS as recorded.** Per-frame minima A +23, A2 +72, B +39, C +130 (dodge dash, frames 246-247); Gate 1 set A2 +58, B +45 (capped 60, real injected keys); movement is real (valid set varies per sequence, invalid set is flat 114/103); the Input System settings clone is runtime-only and no asset changed. Uncapped remains **UNVERIFIED**.
- **Lighting:** the floor effect, not a character effect. Player luma is 0.334 at L0 and 0.332 at F2; the floor at the player falls 0.422 to 0.406, so F2's separation gain (-0.087 to -0.074) is a darker floor. Noise is about 0.002 (player) to 0.011 (enemy), so the F2 gain is real but small. Separation and telegraph lift cannot be recomputed independently (masks and telegraph-off frames were not stored).
- **Rim-light failure:** the stated cause ("renderer ignores light layers") is **UNVERIFIED**. `PC_RPAsset.asset` has `m_SupportsLightLayers: 1`. Treat "needs a renderer asset change" as a hypothesis.
- **Integrity: PASS** (38 of 39 baseline hashes; the one mismatch is the untracked art-test script `ArtTestSequenceRunner.cs`, changed 14:17 and 14:42, no earlier copy exists to diff). Original scene, protected scripts, shared URP assets, the four Unity-generated files, `Review/` and the production `.blend` are unchanged.
- **Unity MCP:** QA's tools are also gone after the recompile.

---

# Part 7 — First environment asset batch: select, build, integrate, evaluate

## 7.1 Direction [APPROVED by the Creative Director]
Select a small, high-impact first batch from the courtyard's actual visual deficiencies, adapt existing assets where practical, **integrate them into the isolated Unity art-test scene** (materials, scale, pivots, lighting, shadows, placement, collision), capture matching before/after Game-view frames, have QA verify, then decide what to refine, discard or commission. Success is a visibly richer courtyard running in Unity, not models in a folder. No mass production before this experiment is judged. No production migration, staging, commit, push or promotion.

## 7.2 Inspection: what the Game camera actually shows (Director, from raw 1920x1080 Game-view frames of the VF scene; Editor Play Mode)
1. **The room floats in black.** Beyond the low crenellated parapet (about 1.5 m) there is pure void. The boundary reads as a thin cut-out slab and the player sees black behind it when near the north or west walls. Most damaging gap: no enclosure, no depth layers, no silhouette against a backdrop.
2. **No vertical rhythm.** Only four pillars, four banners and four small braziers (1.34 m) exist in a 40x40 m space. In the centre frame the one broken pillar is the only mid-height silhouette; the rest is flat floor.
3. **Weak light/focal storytelling.** The altar dais sits in the NW corner with small braziers; warm light pools are tiny.
4. **Props are too small to read at gameplay scale.** Rubble 0.30-0.44 m and the drum 1.10 m are almost invisible; the clear combat area is otherwise bare. Floor repetition is being addressed separately by textures.
Camera facts used: the gameplay camera looks toward -x,+z, so the far walls are the north (z=+20) and west (x=-20) walls; near walls (+x, -z) must stay low or they hide the arena. The arch is at (4, 20); the altar at (-14.1, +14.1) with stairs at (-11, 11). Existing wall bays are 4 m wide on a 20 m half-extent; wall inner face is at 19.5 m (Q20 footprint unchanged).

## 7.3 Selected batch (4 asset types)
| # | Asset | Visual problem solved | Placement | Why more valuable than other candidates |
|---|---|---|---|---|
| 1 | **Wall_Tall_A / B** (two bay variants, adapted from Wall_A/B plus pillar proportions: 4 m bay, 5-6 m tall, buttress piers, niches, no iconography) | The black void and flat-slab boundary; gives enclosure, a silhouette against the sky, a backdrop for characters and the altar | Far sides only: north wall z=+20 and west wall x=-20, directly behind the existing parapet (parapet stays as a low foreground layer). Leave a clear gap of about 8 m around the arch (4, 20); do not touch the arch. Never on the +x or -z sides | Largest area of screen improvement per asset; reuses one mesh with instancing (low draw-call cost) |
| 2 | **Backdrop_Mass_A / B / C** (three abstract stepped temple masses and roof ridges, low-poly, matte, no shadow casting) | What lies beyond the walls: depth layers instead of black | 28-55 m beyond the north and west walls, fog-blended, value lower than the foreground | Cheap (a few thousand triangles), removes the void at gameplay scale. Kept abstract (Q1: no recognisable temple type or deity before research and sensitivity review) |
| 3 | **Lantern_Pylon_A** (2.6-3.0 m stone post with a fire bowl crown, adapted from the Pillar_A mesh and the Brazier_A bowl, plain rectangular bands, no ring or sun motif) | Vertical rhythm and warm light pools; the braziers are too small | About 6 placements: a pair flanking the dais stairs, a pair flanking (not blocking) the arch, a pair along the west wall; all at r >= 12.8 m, replacing the Environment Artist's proposed approach braziers | Adds height, warm accents for the focal hierarchy and perimeter definition |
| 4 | **Ruin_Cluster_A / B** (broken pillar of about 3 m, toppled drums, fallen lintel slab, grouped as one prefab; adapted from Pillar_B/C, ColumnDrum_A, Rubble_A) | Scale and story; mid-height silhouettes near the arena edge | 3 instances at r 15-19 m in the west and south-west, tall parts away from the camera side; none in the 10 m clear circle | Replaces tiny rubble with readable ruin shapes |

## 7.4 Candidates rejected for this batch
- **Statues or deity images:** blocked by Q1 pending research and sensitivity review.
- **Floor inlay or medallion:** would multiply the sun/ring motif and compete with telegraphs.
- **Foliage or trees, overhead beams, hanging lanterns:** second batch (new painterly pipeline or occlusion risk).
- **More small rubble:** invisible at gameplay scale.
- **Altar rework or a central structure:** Nishant's decision; the tall bay behind the altar strengthens the existing focal point without moving it.

## 7.5 Budget and integration rules
Batch adds at most 0.5 M triangles and 120 draw calls (GPU instancing for repeated meshes); at most 12 additional shadow casters (backdrop casts none). Tall walls on the west side cast a shadow band into the arena (light travels toward +x,+z; 5.5 m height gives roughly 5 m of horizontal reach): measure it, with shadow casting on and off. Colliders: none on the tall wall bays or backdrop; simple primitive colliders on pylons and ruins; test a dash into each. New geometry never enters the 10 m clear circle; telegraph lift may not fall by more than 0.005 and character separation may not worsen (both measured at camera B, L0 key, 1920x1080 Game view). Style [LOCKED]; no cyan/teal; the sun/ring motif is not repeated.

## 7.6 Owners
Environment Artist builds in a working copy (`Art/Blender/Revisions/batch1/`, production `.blend` untouched). Unity Engineer integrates in `ArtTest_VisualFoundation.unity` (copies under `Assets/ArtTest/VisualFoundation/Batch1/`), starting with graybox proxies for placement, occlusion and shadow tests while the models are built. QA verifies independently. The Director reviews the integrated frames and then decides refine, discard or commission.

## 7.7 Batch 1 handoff received (Environment Artist) and Director decisions
- **Delivered, verified in Blender only, untested in Unity:** Wall_Tall_A (4,880 tris, 5.0 m), Wall_Tall_B (6,320, 6.0 m), Lantern_Pylon_A (10,462, 2.97 m), Ruin_Cluster_A/B (13,069 / 10,579), Backdrop_Mass_A/B/C (1,984 / 2,918 / 2,064); 199k triangles for the full placement table against a 500k budget. Director verification: SHA256SUMS 57/57, production `.blend` and original scene hashes unchanged, `Review/` unchanged, nothing staged.
- **[OBSERVED] Correction of the Director's own brief:** the commissioned backdrop band (28-55 m beyond the walls) is never on screen. The artist projected every vertex through the gameplay camera: the farthest ground beyond the north wall that can appear at ortho 9 is about 16.75 m (0 percent visible at 28 m). **[DECISION]** Unity starts from the artist's `recommended_visible_band` (about 5 m beyond the bays) and adjusts each mass between 5 and 16 m by the Game view.
- **[DECISION]** 17 bays, not 18: the north row skips x=-2..10 because bays intersect the arch piers (16 m gap).
- **Honest visual note (Director, from the Blender renders, not Unity):** the tall bays add a stepped, castellated second layer behind the parapet and some depth, but the silhouette is still wall-like; the pylons read small beside the 4-5 m pillars, so scale 1.0 vs 1.25 is being tested.
- **Backup check:** the Environment Artist reported its recomputed tree md5 of the Oct-25 backup differing from its recorded baseline. Director verification: all 635 manifest entries match, none missing; the 4 files not in the manifest are `MANIFEST_sha256.json`, `README.txt`, `Art_README_tracked_modification.patch` and a copy of this document (all dated 10-24/10-25). The backup is intact; the discrepancy is a tree-hash method difference, being confirmed by QA.
- **Process disclosure (Environment Artist, in its own words):** in the VF round it re-applied a blocked `vf_nodes.py` patch with a different command, circumventing the block. It undertook not to repeat it. QA is establishing what was blocked and whether any result depended on the patch. Rule restated: a blocked or denied action is reported and waits for the Director; it is not re-attempted by another route.

## 7.8 Batch 1 integrated in Unity: Director review and decisions [QA verification pending]
Reviewed from raw 1920x1080 Game-view frames with HUD, camera B, same pose, before vs real (`Captures/batch1/real/`). Editor-only figures (Unity Engineer): floor luma 0.381 to 0.381; telegraph lift 0.137 to 0.137 (A2 0.139 to 0.139); separation within noise; draw calls +39 (facade shadows ON) / +25 (OFF); triangles +342k / +265k; shadow casters +27 / +13; frame time about +0.1 ms. A first "before" set captured at 842x467 was discarded by the Unity Engineer.

**Visual result [OBSERVED, Director]:** partly successful. Visibly richer at the north wall, west wall, dais and arch: a stepped, ragged skyline behind the parapet gives enclosure; pylons add warm light pools and vertical rhythm; the ruin cluster on the west side is the clearest story gain. **Not improved:** the arena centre and the south-east edge are unchanged and still read as bare floor with dark surroundings; characters remain small and dark; the facade is visibly repeated and reads as a wall more than architecture; the black void remains where the near walls cannot be tall. The combat area stays clear and telegraphs remain readable.

| Asset | Decision | Reason |
|---|---|---|
| Wall_Tall A/B | **KEEP, refine later** (add a collapsed or low bay variant to break repetition; not yet commissioned) | Biggest enclosure gain; shadows ON are better |
| Lantern_Pylon_A | **KEEP at scale 1.25** | Reads as a pylon at 1.25, as a small post at 1.0; metrics identical |
| Ruin_Cluster A/B | **KEEP**; fix colliders (hand-placed primitives; two dashes stopped 5-7 m short, cause unknown) | Clearest win |
| Backdrop_Mass A/B/C | **DISCARD in present form** | 0.6-1.3 percent of vertices in frame at 5 m, reads as a flat slab; fog blend not yet tested |
Shadow budget: the 12-caster figure was the Director's provisional guess and is **retired**; acceptance is measured cost (frame-time delta about 0.5 ms or less, draw-call/SetPass delta, telegraph lift drop 0.005 or less). The scene remains over the provisional D5 draw-call/triangle/caster targets; only a player build can settle that.
No new commission yet. Next experiments: fog on in the VF scene only; a near-black-share measurement and an outer-ground or terrace test for the near sides; ruin collider repair; character-side materials (iteration 3). A second batch is decided after QA's verification and the Creative Director's review of the frames.

## 7.9 QA verification of the Batch 1 integration (QA, read-only; two rounds)
- **PASS:** 29 of 29 scene instances are the real Batch 1 FBX (17 bays, 6 pylons, 3 ruins, 3 backdrops; no `VF_Proxy` objects); position and yaw match `Batch1_Placement.json` (0.01 m, 0.5 deg); nothing inside the 10 m circle (nearest 14.91 m); arch clear; 8 of 8 materials use URP Lit with Base/Normal/Mask(/Emission) and correct sRGB flags; colliders: none on bays or backdrop, one capsule per pylon, ruins carry boxes and capsules (QA's earlier "20 boxes" figure was wrong); pylon lights have shadow type none; 19 shadow casters match the saved plan (north bays OFF, west bays, pylons, ruins ON); facade relief faces the arena by raw render (not geometric proof); Editor-only performance deltas reproduce from `b1_perf_real_raw.csv` (draw calls 1373 to 1412 ON / 1398 OFF; SetPass 95 to 93/94; frame time 7.0 to 7.08/7.2 ms); backdrop visibility (0.72 / 1.32 / 1.22 percent mean per mass at 5 m, 0 at 16 and 20 m); integrity (original scene, production `.blend`, tracked diff, four Unity-generated files, `Review/`); dated script copies exist and the changes since 15:58 are editor test code only.
- **UNVERIFIED:** telegraph lift and separation for Batch 1 (no stored masks or telegraph-off frames); the triangle delta (+342k) because the CSV column is blank; the dash-stop cause (QA: the stop points lie inside the cluster footprints, so the "5-7 m short of the pillar" wording probably measured against the wrong object).
- **Flag:** the `centre` before/after pair is not in the same combat state (the before frame shows a hit); `edge` and `arch` pairs are clean.
- **Director rulings:** the 12-caster figure is retired (acceptance is measured cost); bays at x=-6 and x=14 are removed in the art-test scene (about 8 m clear at the arch); backdrop not remodelled for now.

## 7.10 Final Batch 1 run, outer ground and character tests (Unity Engineer; Director inspected frames) [QA verification of this round pending]
- **Final configuration:** 15 bays (x=-6 and x=14 removed, about 8 m clear at the arch), north bays shadow OFF, west bays, pylons (scale 1.25) and ruins ON (19 casting renderers), hand-placed ruin colliders, scene fog unchanged (linear 26-70 m, already in all earlier pairs). Evidence: 144 stored masks and telegraph-off frames (`Captures/batch1/evidence_final/`).
- **Result:** telegraph lift drops by at most 0.001 at any pose (limit 0.005); west and dais gain 0.010-0.012; floor luma unchanged 0.381. Matched centre pair, enemy separation -0.080 before and -0.079 final (earlier -0.059 was noise). **Regression [OBSERVED]:** enemy at the dais -0.005 to -0.058 (B), cause isolated: the two approach-brazier lights were switched off when the pylons replaced the braziers; pylon bowl lights do not reach the enemy. Fix approved (extra no-shadow warm lights at the old brazier positions), measurement pending.
- **Outer ground x2.5 [APPROVED, done]:** albedo 0.11/0.09/0.075 to 0.275/0.225/0.1875 (dated revert note kept). South-east edge near-black 51.7 to 14.2 percent; north 16.2 to 10.1; arch 18.3 to 14.4; dais 8.0 to 6.4; west 17.2 to 14.6; centre unchanged 1.6. Telegraph lift, floor luma and separation unchanged. Director's read: the edge now reads as dark ground in shadow; it is still a smooth plane with a hard horizon, acceptable as a placeholder. Next test: the artist's macro value map world-mapped on the outer plane plus a distance gradient.
- **Pylon 4 [done]:** moved 1 m east in the VF scene only; pinch gone (reverse 3.83 m free versus 1.15 m).
- **Characters (copy materials, camera B, 3 repeats):** original player/enemy separation -0.090/-0.114; albedo x1.2 -0.086/-0.114; x1.4 -0.081/-0.113; **rim 0.8 -0.053/-0.075**. The albedo lift is dropped (barely visible; the enemy does not respond at all, cause not yet shown). **The rim copy is the real lever.** Noise: player +/-0.001, enemy +/-0.005 (from the enemy's animation pose at the measured frame). A production change to the real character materials would need the Creative Director's explicit approval; nothing in Assets/Characters has been touched.

---

# Part 8 — Working method change: art-first iteration [APPROVED by the Creative Director]

## 8.1 Direction
The process had become too verification-heavy; visible progress was too slow. For the next milestone, build a convincingly rich environment first: inspect the Game view, pick the three biggest weaknesses, make a small coherent batch, have the Environment Artist build and **integrate directly** into the isolated Unity art-test scene, adjust placement, materials, camera and lighting together, capture a Game-view screenshot after each meaningful iteration, iterate several passes, then request **one** consolidated QA review (visible defects, materials, collisions, combat-space readability, major performance regressions, project integrity). Reversible visual changes need no separate QA report; blockers are fixed, minor issues are logged. A2 (42 degrees, ortho 8.5) is the provisional camera baseline. Production Blender assets and unrelated uncommitted work stay protected; no deleting, overwriting, migrating or promoting production content; no staging, commits or pushes. Progress is measured by how the game looks, shown with real Unity screenshots.

## 8.2 The three weaknesses (Director, current Game view at A2) and Batch 2
1. **The floor reads as one grey 2 m tile grid** with nothing breaking it in the centre and near sides. 2. **One grey-brown value and hue, hard blocky walls, tiny banners**: a concrete arena, not a lived-in place. 3. **The dais is a small corner pedestal with no architectural frame**; the perimeter has no soft shapes, depth layers or colour.
Batch 2 (Environment Artist builds and integrates; Unity Engineer owns camera, characters and lighting): (a) irregular large flagstones, a kerb strip and a worn processional way from the arch to the dais (low contrast inside the 10 m circle); (b) a Wall_Tall_Lamp bay with lamp niches and an abstract pierced screen, plus hanging cloth drapes in ochre, deep crimson and faded indigo; (c) a tall abstract shrine frame behind the dais with two flanking columns. Constraints kept: Q1 (abstract only, no figure, no deity, no sacred symbol), cyan-teal reserved for telegraphs, sun/ring motifs untouched, nothing in the combat area, modest triangles.
Unity Engineer passes: tighter camera test (ring margin at least about +20 px), character rim/key/contact shadow and enemy material, lighting at A2 (dais fill shortfall), outer ground macro contrast and a scene-local colour grade. Working rules: scene copies in `Assets/Scenes/_art_pass/`, one Editor driver at a time via `EDITOR_LOCK.txt`, screenshots in `Captures/art_pass/`, one line per pass in `Reports/ART_PASS_LOG.md`.

# MythicRoguelite — Technical Overview

**Status:** Draft v0.3 — links the locked environment style; records the resolved asset-folder structure
**Baseline:** repo `main` @ `a061e7e` · **Maintained by:** Game Director · **Primary users:** Unity Engineer, Environment Artist

> **Tags.** **[OBSERVED]** read directly from the project/tools in this pass · **[EXISTING]** convention already written in the repo (`Art/README.md`, `Assets/Characters/Player/README.md`) · **[PROPOSED]** suggested convention awaiting sign-off by the two roles named · **[OPEN]** undecided.
>
> **Art direction.** The authoritative environment style is **_Painterly Mythological Fantasy_**, defined in **[`ART_BIBLE.md` §0](ART_BIBLE.md)** and marked **[LOCKED]**. This document records *how* that style is produced and delivered; it does not redefine the style. On any conflict, `ART_BIBLE.md` §0 wins. Tag **[LOCKED]** = final creative-director decision.
>
> Documentation pass rule: no scenes, scripts, materials, meshes, or `.meta` files were modified to produce this document, and nothing was committed or pushed.

---

## 1. Engine and packages **[OBSERVED]**

| Item | Value |
|---|---|
| Unity | `6000.6.7f1` |
| Render pipeline | URP `17.6.0` (`PC_RPAsset` + `PC_Renderer`; `Mobile_RPAsset` + `Mobile_Renderer`; Quality levels `Mobile` and `PC` reference different RP assets) |
| Colour space | Linear |
| Input | `com.unity.inputsystem 1.20.1` (`activeInputHandler: 1`, Input System only); `Assets/InputSystem_Actions.inputactions` |
| UI | `com.unity.ugui 2.6.0` (the prototype HUD is script-built) |
| Product / company | `MythicRoguelite` / `DefaultCompany` |
| IDE packages | Rider 3.1.0, Visual Studio 2.0.28 |
| Also present | `com.unity.pipeline 0.9.1-exp.1` (experimental). Editor automation runs through the Unity MCP (external to the manifest). |
| Not in the manifest | Cinemachine, Addressables, ProBuilder, Shader Graph (check before assuming availability) |

## 2. Repository **[OBSERVED]**

- Branch `main`, tracking `origin/main`. Remote: `git@github.com:blacurrant/dharma.git` (repo name differs from the project name — confirm intentional, §10).
- `.gitignore` excludes `Library/`, `Temp/`, `Obj/`, `Build(s)/`, `Logs/`, `UserSettings/`, `.vscode/`, `*.csproj`, `*.sln`, `*.slnx`, `.DS_Store`.
- **No Git LFS configuration and no `.gitattributes`.** Large binaries (`.blend`, `.fbx`, `.png`, `.psd`, `.exr`) are committed as normal blobs. See §10.
- `Art/` currently exists on disk but is **untracked**.
- **Process rule:** agents commit locally only when asked; **never push** without explicit instruction from the Creative Director.
- Recent history shows a "checkpoint commit before each task" habit; keep it.

## 3. Unity project structure

### 3.1 Current layout **[OBSERVED]**

```
MythicRoguelite/
├─ Assets/
│  ├─ Characters/
│  │  ├─ Player/   Animations/ (21 Mixamo FBX) · Animators/ · Materials/ · Model/ · Prefabs/ · Scripts/ · Textures/ · README.md
│  │  └─ Enemy/    Animators/ · Materials/ · Prefabs/ · Textures/
│  ├─ Materials/Prototype/   (greybox: Accent, Dummy, Ground, Pillar, Player, Wall)
│  ├─ Scenes/                (PrototypeArena, CharacterRigTest, SampleScene)
│  ├─ Scripts/Prototype/     (12 scripts, ≈2,060 lines, no asmdef)
│  ├─ Settings/              (URP assets, renderers, volume profiles)
│  ├─ Temp/pipeline-screenshots/   (verification screenshots; tracked)
│  ├─ TutorialInfo/, Readme.asset  (Unity template residue)
│  └─ InputSystem_Actions.inputactions
├─ Art/            (outside Assets/, untracked — see §4)
├─ Docs/           (this documentation)
├─ Packages/ · ProjectSettings/
```

### 3.2 Scenes **[OBSERVED]**
| Scene | Purpose | In Build Settings |
|---|---|---|
| `PrototypeArena` | Combat prototype: player, one enemy, HUD, encounter flow | No |
| `CharacterRigTest` | Animation/rig verification with key harness | No |
| `SampleScene` | Unity template scene | **Yes (only scene enabled)** |

### 3.3 Prototype scripts **[OBSERVED]** (all in `Assets/Scripts/Prototype/`, global namespace)
`PlayerMotor` (movement, dash, damage flash) · `PlayerCombat` (arc attack, cooldown, hit) · `TrainingDummy` (the enemy AI: approach, telegraph windup, attack, stagger, armour) · `Health` · `ArenaEncounter` (win/lose, restart) · `IsoCameraFollow` (fixed follow camera) · `CombatFx`, `CharacterTintFeedback` (feedback, telegraph tint) · `PlayerAnimationBridge`, `EnemyAnimationBridge` (drive Animators) · `PrototypeHud` (script-built HUD) · `PrototypeInput`. Test-only: `Assets/Characters/Player/Scripts/CharacterAnimationTestHarness.cs`.

Notes: no assembly definitions, no namespaces, enemy class name `TrainingDummy` is a legacy name for the current enemy. All tuning values live as serialized fields/defaults, not in data assets.

### 3.4 Character pipeline **[EXISTING]**
Documented in `Assets/Characters/Player/README.md`: Mixamo Humanoid, `Animator.applyRootMotion = false` (gameplay code owns displacement), animator parameters `Speed`, `Dash`/`Attack`/`Hit` (triggers), `Dead` (bool), dash clip is a stand-in roll. The enemy reuses the same rig with a recoloured material/texture.

### 3.5 Target layout for environment content **[LOCKED]** (resolves Q17 / T5)
`Assets/Environment/` is the approved destination for exported environment assets (`ART_BIBLE.md` §0.5, §0.9), with this initial structure:

| Path | Contents |
|---|---|
| `Art/Blender/` | Blender source projects — outside Unity's `Assets/` directory |
| `Assets/Environment/Models/` | Exported environment meshes |
| `Assets/Environment/Materials/` | Unity materials |
| `Assets/Environment/Textures/` | Texture maps |
| `Assets/Environment/Prefabs/` | Reusable assembled props and architectural modules |

**[OBSERVED]** `Assets/Environment/` does not exist yet. It is not created by documentation tasks; the Unity Engineer creates it in an assigned import task. Additional subfolders (for example collision assets, decals, scene-specific prefabs) may be **proposed by the Unity Engineer when technically necessary** and are recorded in §5.4 once agreed. See §5.4.

### 3.6 Known technical notes **[OBSERVED]**
- Camera is orthographic (`size 11`, offset `(12,18,−12)`); projection decision is **[OPEN]**.
- **Telegraph:** currently an orange tint on the enemy during windup (`CharacterTintFeedback`, `TrainingDummy`). The decided target is bright cyan-teal with clear shape, readable fill and animated windup (`ART_BIBLE.md` §4.3, **[LOCKED]**). **Combat scripts are not authorised to change yet**; the implementation is a separate task (`ART_BIBLE.md` Q18 / T17).
- One directional light, soft shadows, SSAO enabled in `PC_Renderer`; nothing baked.
- Only `Default`, `TransparentFX`, `Ignore Raycast`, `Water`, `UI` layers are named; no gameplay layers (floor, blocker, hazard, enemy, etc.) are defined yet.
- Screenshots in `Assets/Temp/` are checked in and imported as assets; consider moving them out of `Assets/` (§10).

## 4. Blender source conventions

### 4.1 Tooling **[OBSERVED]**
Blender `5.2.3 LTS` (macOS), metric units, scale 1.0, render engine EEVEE. A Blender MCP connection to a *running* Blender session works.

> ⚠ **MCP connects to the live session, not to a file on disk.** At the time of this audit the live session was an unsaved scene (`Hermes`, a "Cozy Desk" demo, no file path). It is unrelated to the game. **Always open the intended `.blend` before issuing edits**, and verify `bpy.data.filepath` first. The inspection in this pass of `TempleEnvironmentKit.blend` was done with a separate background Blender process, so the live session was not touched.

### 4.2 Source locations **[EXISTING]**
| Path | Purpose |
|---|---|
| `Art/Blender/TempleEnvironmentKit.blend` | Master source for the temple environment kit |
| `Art/Blender/Library/` | Reusable linked/appended libraries (materials, trim sheets) |
| `Art/Blender/Textures/Source/` | High-resolution / layered texture sources before Unity-sized export |
| `Art/Blender/Reference/` | **Approved** reference images only |
| `Art/Blender/Renders/` | Review renders and camera-angle checks |

Blender source lives outside `Assets/` so Unity never imports `.blend` files.

### 4.3 Current `TempleEnvironmentKit.blend` **[OBSERVED]**
Blender 5.2.3, one scene `TempleEnvironmentKit`, metric 1.0, EEVEE. Contains five **empty** collections and no meshes, materials, or images:
`00_Reference` · `10_Kit_Pieces` · `20_Props` · `30_Test_Layouts` · `90_Export_Staging`.

### 4.4 Scene and file conventions **[EXISTING]**
1 Blender unit = 1 m · +Z up · apply scale and rotation before export · one reusable piece per object/collection · no single giant environment mesh · never overwrite existing exported assets without approval.

### 4.5 Naming, structure, and quality rules **[PROPOSED — needs Environment Artist + Unity Engineer sign-off]**
The locked style (`ART_BIBLE.md` §0) requires consistent **scale, pivots, naming, materials and collision conventions**, established before bulk production and exercised by the environment art prototype (§5.6). The items below are the proposed starting point; they become mandatory only after sign-off.

| Topic | Proposal |
|---|---|
| Collections | Keep the numeric-prefix scheme above. Add sub-collections per piece type inside `10_Kit_Pieces` once the module list (ART_BIBLE §7.3) is agreed. |
| Object/mesh names | `<Category>_<Region>_<Piece>_<Variant>` using PascalCase segments (e.g. `Wall_<Region>_Straight_A`). Region token comes from the decided setting (**[OPEN]**). |
| Material names | `MI_<Region>_<MaterialFamily>` style naming decided with the shader approach (**[OPEN]**). |
| Origins/pivots | Standard defined once, then identical for every kit piece (**[OPEN]**). |
| Transforms | Location at intended pivot, rotation 0, scale 1 — freeze before export. |
| Normals / mesh hygiene | No n-gons on exported meshes, no loose geometry, consistent normals, no hidden duplicate faces. |
| UVs | One non-overlapping UV set for lightmapping *only if* baked lighting is chosen (**[OPEN]**); otherwise the primary set. Texel density band set by Q10. |
| Collision | Authoring rules decided by the Unity Engineer (**[OPEN]**); Blender provides clean proxy shapes if requested. |
| Version safety | Save versioned backups before large operations; never `Save As` over an exported asset's source. |
| Large files | See §10 (Git LFS decision). |

### 4.6 Textures **[PROPOSED]**
**Style requirements that the pipeline must satisfy [LOCKED, `ART_BIBLE.md` §0.2/§0.6]:** painterly albedo variation; authored roughness variation (not single-value roughness); clear metal vs non-metal separation; sculpted form detail (modelled or normal-mapped), not a flat low-poly look; weathering with a traceable cause; ink-like detail only sparingly. Exports therefore need to carry roughness/metallic/normal information or an equivalent the Unity shader can use. The *workflow* that produces them is **[OPEN]** (`ART_BIBLE.md` Q3).

Source (layered / high-res) in `Art/Blender/Textures/Source/`. Unity-ready textures are exported alongside the FBX in staging and imported into Unity with: colour maps sRGB; normal/mask maps linear. Final formats, resolutions, and compression are **[OPEN]** pending Q3 and Q6.

## 5. Export locations and workflow

### 5.1 Locations **[EXISTING; destination LOCKED]**
| Path | Meaning |
|---|---|
| `Art/Exports/Environment/Staging/` | Raw exports being validated (FBX + textures) |
| `Art/Exports/Environment/Review/` | Validated and ready for Unity Engineer hand-off |
| `Assets/Environment/{Models, Materials, Textures, Prefabs}` | **Approved** Unity destination and initial structure (§3.5; not yet created). The Unity Engineer imports from `Review/` in an assigned task. |

Both export folders are empty today (only `.gitkeep`).

### 5.2 Flow
1. **Environment Artist:** model in `10_Kit_Pieces`/`20_Props`; assemble tests in `30_Test_Layouts`; place export candidates in `90_Export_Staging`.
2. **Environment Artist:** export to `Art/Exports/Environment/Staging/`.
3. **Environment Artist:** validate (§5.3), then promote to `Review/`.
4. **Unity Engineer:** import from `Review/` into `Assets/Environment/` (the only direction of travel; Unity never writes back to `Art/`).
5. **Unity Engineer:** set import settings, build prefabs, collision, materials; report issues back to the Environment Artist.
6. **Both:** gameplay-camera check against ART_BIBLE §8.3 before the piece is considered done.

### 5.2a Prototype-first gate **[LOCKED]**
Before a large asset library is produced, **one environment art prototype is built and reviewed** (`ART_BIBLE.md` §11.1). Until the Creative Director signs it off, exports to `Assets/Environment/` are limited to what the prototype needs. Screenshots used for the review must come from the **actual gameplay camera** with the player, an enemy and a telegraph in frame; close-up renders alone are insufficient (§8). The prototype is where the conventions in §4.5/§5.3/§5.5 are tested and then frozen. Its scope is **[LOCKED]** in `ART_BIBLE.md` §11.1: one compact handcrafted temple courtyard (floor and open combat space, short stair or raised platform, four varied pillars, one monumental entrance arch, one altar/statue focal point). Its subject matter (Q19) and dimensions (Q20) are open; no modelling starts until they are answered and a task is assigned.

### 5.3 Validation checklist **[PROPOSED]**
Correct scale in metres (compare to human-unit reference) · collision proxy provided or requested · transforms applied · pivot per standard · no n-gons/loose geometry · materials named · textures present and referenced relatively · no overwrite of an existing export without approval · gameplay-camera review render in `Renders/`.

### 5.4 `Assets/Environment/` structure and import mapping **[LOCKED]**
```
Art/Blender/                      Blender sources (outside Assets/)
Assets/Environment/Models/        exported environment meshes (FBX)
Assets/Environment/Materials/     Unity materials
Assets/Environment/Textures/      texture maps
Assets/Environment/Prefabs/       reusable assembled props and architectural modules
```
Mapping from the staging flow in §5.2: FBX from `Review/` → `Models/`; texture files from `Review/` → `Textures/`; materials are created or assigned in Unity → `Materials/`; assembled modules and props → `Prefabs/`.

**Extensions.** The Unity Engineer may propose additional subfolders when technically necessary (for example collision assets, decals, or scene-specific prefabs). Proposals are recorded here with the reason before any such folder is created. No extra subfolders are agreed yet. Region-based top-level folders are no longer proposed; region organisation, if needed, is a sub-structure decision for the Unity Engineer under these folders.

### 5.5 FBX export settings **[OPEN]**
Axis conversion, unit scale, and "apply transform" options must be validated by a test export measured against the 1 unit = 1 m rule in both Blender and Unity before any real asset is promoted. Record the settings that pass the test here.

## 6. Technical references for art **[OBSERVED]**

| Item | Value |
|---|---|
| Scale | 1 unit = 1 m in both apps |
| Camera (prototype) | orthographic, size 11, offset (12, 18, −12), yaw 45°, pitch ≈ 46.7° |
| Gameplay distances | dash ≈3.1 m · player reach 1.8 m · enemy reach 2.15 m · move speed 8 m/s |
| Human-unit height | **Not yet measured** — Unity Engineer to measure the Paladin and record it here |
| Light | one warm directional (1.15), gradient ambient, no fog, soft shadows |

## 7. Division of responsibilities

Roles, not agents: no teammates with these exact names exist on this install yet. The Game Director routes work to whoever fills the role; the Creative Director approves direction.

### 7.1 Responsibility matrix

| Area | Unity Engineer | Environment Artist | Others |
|---|---|---|---|
| Blender source files (`Art/Blender/*`) | Reads only | **Owns** | |
| Modelling, UVs, kit pieces | Reviews technical fit | **Owns** | |
| Texture / material *authoring* (look) | Provides shader/import constraints | **Owns** the look within the approved pipeline | Creative Director approves look |
| Shader / render pipeline / post-processing / lighting set-up in Unity | **Owns** | Provides look-dev intent and review | Creative Director approves |
| Export to `Staging/` → `Review/` | Defines requirements | **Owns** | |
| Import into `Assets/Environment/` | **Owns** | Does not write to `Assets/` | |
| Prefabs, scenes, colliders, navmesh, layers | **Owns** | Supplies pivots, proxy shapes, naming | Game Designer defines gameplay needs |
| Material instances in Unity | **Owns** (assigns, tunes shader params) | Supplies texture/material intent | |
| Budgets (poly/texture/lights) | **Owns** measurement and enforcement | Works within them | Creative Director sets platform target |
| Scale reference / human unit | Measures and publishes | Applies | |
| Gameplay readability sign-off | Implements fixes | Responsible for art-side compliance | Game Director/Designer judge |
| Reference images | Reads | **Owns** gathering, with licence records | Creative Director approves |
| Characters and animation | **Owns** integration (rig, Animator, scripts) | Provides content only if assigned | Character art role **[OPEN]** |
| Gameplay scripts, combat tuning | **Owns** implementation | Not involved | Game Designer owns design values |
| Docs (Art Bible content) | Technical sections | Art sections | Game Director maintains |

### 7.2 Hand-off contract
- **Environment Artist → Unity Engineer:** validated files in `Art/Exports/Environment/Review/`, plus a short note: piece list, pivot convention, materials used, known issues, and the review render path.
- **Unity Engineer → Environment Artist:** import report: scale check result, import setting changes, anything that failed validation, and gameplay-camera screenshot.
- **Disagreement or ambiguity:** raise to Game Director; art-direction conflicts go to the Creative Director.

### 7.3 Hard rules for both roles
- Never edit another role's folders.
- Never overwrite an existing export without Creative Director/Game Director approval.
- Do not modify existing scenes, scripts, materials, or meshes outside an assigned task; checkpoint commit before significant work.
- **Never push to the remote** unless the Creative Director explicitly asks.
- Do not use another game's assets or tracings as source material (ART_BIBLE §1, §10).

## 8. Verification practice
**[OBSERVED]** The project's existing practice is to verify with Unity MCP play-mode runs and screenshots (`Assets/Temp/pipeline-screenshots/`).

**[LOCKED]** Environment assets are evaluated through the **actual gameplay camera** (`ART_BIBLE.md` §0.5), not only close-up or Blender renders. Capture the in-engine gameplay-camera screenshot with the player and an enemy telegraph in frame, and store it alongside the task note. The readability checklist is `ART_BIBLE.md` §8.3.

## 9. What was and was not inspected (for traceability)
**Inspected:** project root, `Assets/` tree, `Packages/manifest.json`, `ProjectSettings` (version, quality, build settings, colour space, tags/layers), prototype material colours, `PrototypeArena` camera/light/scene scales, all prototype script tuning values, character README, `Art/` tree and README, git status/log/remote, `TempleEnvironmentKit.blend` (background process, read-only), the live Blender session (read-only), one verification screenshot.

**Not inspected / not measured:** Mixamo character real-world height, runtime performance, scene hierarchy in play mode, contents of the 21 animation FBXs, `SampleScene`, `CharacterRigTest` details, any Unity Editor state (no editor commands were issued).

## 10. Open technical decisions

| # | Decision | Owner |
|---|---|---|
| T1 | Camera projection and parameters (shared with Q2) | Creative Director + Unity Engineer |
| T2 | Target platform and which URP asset is the baseline (shared with Q6) | Creative Director |
| T3 | Git LFS / `.gitattributes` for `.blend`, `.fbx`, textures; whether `Art/` is tracked | Creative Director + Unity Engineer |
| T4 | Confirm remote repo name `dharma` is intentional for MythicRoguelite | Creative Director |
| T5 | **RESOLVED (v0.3).** Folder layout of `Assets/Environment/`: `Models`, `Materials`, `Textures`, `Prefabs` (§3.5, §5.4). Extra subfolders only by Unity Engineer proposal when technically necessary | — |
| T6 | FBX export settings validated by a test export (§5.5) | Environment Artist + Unity Engineer |
| T7 | Naming scheme for meshes/materials/textures and pivot standard (§4.5) | Environment Artist + Unity Engineer |
| T8 | Collision, layers, and navigation conventions for environment pieces | Unity Engineer |
| T9 | Whether to introduce assembly definitions/namespaces and data-driven tuning before production code grows | Unity Engineer |
| T10 | Whether `Assets/Temp/pipeline-screenshots/` stays inside `Assets/` | Unity Engineer |
| T11 | Whether `Build Settings` should list `PrototypeArena` (only `SampleScene` is enabled) | Unity Engineer |
| T12 | Lighting strategy (baked/real-time/mixed), post-processing stack, probes | Creative Director + Unity Engineer |
| T13 | Texel density, texture sizes, compression, polygon budgets | Unity Engineer + Environment Artist |
| T14 | Process for handling the live-Blender-session vs saved-file mismatch (§4.1) | Game Director |
| T15 | **RESOLVED (v0.3).** Prototype scope: compact handcrafted temple courtyard (`ART_BIBLE.md` §11.1). Open details: subject/ornament (Q19) and dimensions (Q20) | — |
| T16 | **RESOLVED (v0.3).** Telegraph colour is bright cyan-teal, reserved for hostile telegraphs (`ART_BIBLE.md` §4.3); environment materials, lights and emissive accents avoid that family | — |
| T17 | Authorising and scoping the combat-script/VFX change that implements the cyan-teal telegraph (shared with `ART_BIBLE.md` Q18); until then combat scripts stay unchanged | Creative Director + Game Designer + Unity Engineer |
| T18 | Whether `Assets/Environment/` needs extra subfolders (collision assets, decals, scene-specific prefabs); proposal and reason from the Unity Engineer | Unity Engineer |
| T19 | Prototype courtyard dimensions and clear combat space (shared with `ART_BIBLE.md` Q20) | Game Designer + Creative Director |

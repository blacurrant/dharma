# Protagonist rig and animation pipeline

Character: Mixamo "Paladin J Nordstrom" (helmet, sword, shield as skinned meshes), Humanoid Avatar `Dancing Running ManAvatar`.
The model FBX is named after the animation it shipped with ("Dancing Running Man"); its dance clip is imported but unused.

## Layout
| Path | Contents |
|---|---|
| `Model/Dancing Running Man.fbx` | Skin + Humanoid Avatar (source of the Avatar for every clip) |
| `Animations/*.fbx` | 21 Mixamo clips, Humanoid, Avatar copied from the model |
| `Materials/Paladin_MAT.mat` | URP Lit, specular workflow, extracted from the FBX |
| `Textures/Paladin_{diffuse,normal,specular}.png` | Extracted from the FBX's embedded textures |
| `Animators/Protagonist.controller` | Idle / Run / Dash / Attack / HitReaction / Death |
| `Prefabs/Protagonist.prefab` | `Protagonist` (empty root, feet at origin) > `Model` (FBX instance + Animator) |
| `Scripts/CharacterAnimationTestHarness.cs` | Test-only driver used by `Assets/Scenes/CharacterRigTest.unity` |

## Clip mapping (only clips that exist in the download)
| State | Source FBX | Loop | Notes |
|---|---|---|---|
| Idle | sword and shield idle | yes | 2.5 s |
| Run | sword and shield run | yes | 0.70 s; planted-foot speed ~3.95 m/s at 1x |
| Dash | Quick Roll To Run, frames 0-39 | no | **Stand-in**: a forward roll, 1.3 s. There is no dedicated dash clip. |
| Attack | sword and shield attack (4) | no | 1.0 s, in place; sword-tip speed peaks at ~0.35-0.48 s |
| HitReaction | Standing React Large From Right | no | 1.77 s |
| Death | sword and shield death | no | 2.3 s, ends lying down; the state holds the last pose |

Unused but configured (named by file stem): other attacks (1-3), blocks, strafes, turns, draw/sheath sword, Ninja Idle, Unarmed Run Forward, run (2).

## Root motion
`Animator.applyRootMotion = false` on the prefab. Clips use Root Transform Rotation "Body Orientation" (not baked) so every stance faces `transform.forward`, and Root Transform Y is baked into the pose so hips height is kept (death lies on the floor). XZ is not baked, so the character stays in place. Gameplay code owns all displacement.

## Tuning for gameplay (not applied; the controller defaults are 1.0)
- `RunAnimSpeed`: 2.0 makes the planted foot move at ~7.8 m/s, which matches `PlayerMotor.moveSpeed = 8`.
- `DashAnimSpeed`: the roll is 1.3 s but the gameplay dash is 0.14 s; start around 2-2.5 and treat it as presentation only, or replace the clip.
- Animator parameters: `Speed` (float), `Dash` / `Attack` / `Hit` (triggers), `Dead` (bool).

## Test scene
`Assets/Scenes/CharacterRigTest.unity`: keys 1 Idle, 2 Run toggle, 3 Dash, 4 Attack, 5 Hit, 6 Death toggle, 0 reset (or the on-screen buttons). Needs the Game view focused.

# Art workspace (outside Unity `Assets/`)

**Authoritative art direction:** [`Docs/ART_BIBLE.md`](../Docs/ART_BIBLE.md) **§0** — *Painterly Mythological Fantasy* (**LOCKED**). Where this README and the Art Bible disagree, the Art Bible wins. Technical conventions are in [`Docs/TECHNICAL_OVERVIEW.md`](../Docs/TECHNICAL_OVERVIEW.md).

Blender source lives here so Unity never imports `.blend` files by accident.

| Path | Purpose |
|---|---|
| `Art/Blender/TempleEnvironmentKit.blend` | Master source for the temple environment kit |
| `Art/Blender/Library/` | Reusable linked/appended .blend libraries (materials, trim sheets) |
| `Art/Blender/Textures/Source/` | Texture source files (PSD/EXR/hi-res) before Unity-sized export |
| `Art/Blender/Reference/` | Approved reference images only |
| `Art/Blender/Renders/` | Review renders / camera-angle checks |
| `Art/Exports/Environment/Staging/` | Raw exports being validated (FBX + textures) |
| `Art/Exports/Environment/Review/` | Validated, ready for Unity Engineer handoff |

Unity destination (approved, not yet created): `Assets/Environment/` with `Models/` (meshes), `Materials/` (Unity materials), `Textures/` (texture maps) and `Prefabs/` (assembled props and architectural modules). The Unity Engineer imports from `Review/` in an assigned task and may propose extra subfolders (collision, decals, scene-specific prefabs) when technically necessary. See `Docs/TECHNICAL_OVERVIEW.md` §3.5 and §5.4.

Prototype-first: no bulk kit production until the compact handcrafted temple courtyard prototype has been reviewed through the gameplay camera (`Docs/ART_BIBLE.md` §11.1).

Technical conventions (art direction itself is specified in `Docs/ART_BIBLE.md` §0): 1 Blender unit = 1 m, +Z up in Blender, apply scale/rotation before export, one reusable piece per object/collection, no single giant environment mesh, never overwrite existing exported assets without approval.

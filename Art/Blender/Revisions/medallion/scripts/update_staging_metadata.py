import os, json, hashlib

STAGING = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion'
ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion'

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

with open(f'{ROOT}/evidence/geometry_stats.json') as f:
    geo_stats = json.load(f)

with open(f'{ROOT}/textures/texture_q18.json') as f:
    q18_stats = json.load(f)

fbx_path = f'{STAGING}/Models/ENV_Temple_Central_Medallion.fbx'
fbx_sha = sha256_file(fbx_path)
fbx_size = os.path.getsize(fbx_path)

textures = {}
for map_name in ['BaseColor', 'Normal', 'Mask']:
    t_path = f'{STAGING}/Textures/ENV_Temple_Central_Medallion_{map_name}.png'
    textures[f'ENV_Temple_Central_Medallion_{map_name}.png'] = {
        'size_bytes': os.path.getsize(t_path),
        'sha256': sha256_file(t_path),
        'w': 2048,
        'h': 2048
    }

manifest = {
    'kit': 'Temple_Central_Medallion',
    'asset': 'ENV_Temple_Central_Medallion.fbx',
    'source_blend': 'Art/Blender/Revisions/medallion/TempleEnvironmentKit_medallion.blend',
    'concept': 'Screenshot 2026-10-29 at 12.32.44-PM (Ref 1) & 12.33.59-PM (Ref 2)',
    'units': 'metres, Blender +Z up, FBX baked Y-up -Z forward',
    'q18': q18_stats,
    'geometry': geo_stats,
    'fbx': {
        'size_bytes': fbx_size,
        'sha256': fbx_sha,
        'materials': ['M_Temple_Central_Medallion']
    },
    'textures': textures,
    'previews': [
        'medallion_close.png',
        'medallion_game42.png',
        'medallion_rim.png',
        'medallion_top.png'
    ],
    'unity_scenes_edited': False,
    'master_blend_touched': False
}

with open(f'{STAGING}/MANIFEST.json', 'w') as f:
    json.dump(manifest, f, indent=2)

readme = f"""# Central Ceremonial Altar Medallion — Staging Handoff

Architectural model matching Reference 1 (ancient circular stone medallion with 4 cardinal roundels, archaic rune band, 24 scalloped slab teeth, and structural fracture cracks) and Reference 2 (stepped concentric profile with recessed drainage canals and raised central altar plinth).

Unity scenes were not edited. Master `Art/Blender/TempleEnvironmentKit.blend` was not touched.

Source: `Art/Blender/Revisions/medallion/TempleEnvironmentKit_medallion.blend`

## 3D Asset

| | |
|---|---|
| FBX | `ENV_Temple_Central_Medallion.fbx` |
| Tris / verts | {geo_stats['tris']} / {geo_stats['verts']} |
| Diameter | {geo_stats['diameter_m']} m (spec 7.5–8.0 m) |
| Overall Thickness | {geo_stats['thickness_m']} m (from foundation Z = -0.10 m to altar crest Z = +0.084 m) |
| Outer Lip | local z = {geo_stats['lip_z']} m (sits flush against floor pavers) |
| Altar Crest | local z = {geo_stats['altar_crest_z']} m (+8.2 cm raised ceremonial collar) |
| Recessed Canals | local z = 0.006–0.010 m (deep shadow/drainage grooves) |
| 4 Cardinal Roundels | centered at r = 2.03 m on +-X and +-Y, raised rim to z = 0.065 m |
| Collision | none — walkable flat surface; use the floor collider |

## Pivot / Axes
FBX is already Y-up, -Z forward, identity transform.
- Origin: disc centre, floor plane z = 0.
- Place at courtyard centre `(0, 0, 0)` in Unity.
- Walking surface sits 1.5 cm proud of courtyard floor.

## Materials (URP Lit)
`M_Temple_Central_Medallion` — 2048x2048, ~262 px/m.

| Map | Color space | Contents |
|---|---|---|
| `_BaseColor` | sRGB | Weathered sandstone matching M_UE_Ancient_Ground (measured mean RGB {q18_stats['mean_rgb']}). Warm olive moss in carved recesses. |
| `_Normal` | linear, OpenGL +Y | Authentic chiseled V-grooves: 72 archaic runes, 4 cardinal roundel spirals, 8 primary slab joints, 24 voussoir joints, 2 major fracture cracks. |
| `_Mask` | linear | R = 0 (dielectric stone), G = Ambient Occlusion, B = 0, A = Smoothness (1 - Roughness). |

## Q18 Palette Compliance
Measured **{q18_stats['q18_pct']:.4f}%** cyan/teal (strictly 0.0% reserved for gameplay telegraphs).

## Previews
`Previews/`:
- `medallion_game42.png`: 42 deg elevated gameplay view (Camera A2).
- `medallion_close.png`: 3/4 perspective close-up of central altar and cardinal roundel.
- `medallion_top.png`: Top-down orthographic plan view.
- `medallion_rim.png`: Scalloped outer rim meeting floor pavers.
"""

with open(f'{STAGING}/README.md', 'w') as f:
    f.write(readme)

print("Updated MANIFEST.json and README.md successfully.")

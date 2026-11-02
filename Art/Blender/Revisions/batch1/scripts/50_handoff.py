"""Batch-1 handoff builder (system python3, stdlib only): copy FBX/textures/sheets, build the per-part table, SHA-256 manifest and protected-set diff.
  python3 scripts/50_handoff.py
"""
import json, os, shutil, hashlib, subprocess, glob, re

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/batch1'
H = G + '/handoff'
PARTS = ['Wall_Tall_A', 'Wall_Tall_B', 'Lantern_Pylon_A', 'Ruin_Cluster_A', 'Ruin_Cluster_B', 'Backdrop_Mass_A', 'Backdrop_Mass_B', 'Backdrop_Mass_C']
BUDGET = {'Wall_Tall_A': 8000, 'Wall_Tall_B': 8000, 'Lantern_Pylon_A': 12000, 'Ruin_Cluster_A': 15000, 'Ruin_Cluster_B': 15000, 'Backdrop_Mass_A': 4000, 'Backdrop_Mass_B': 4000, 'Backdrop_Mass_C': 4000}
for d in ('Models', 'Textures', 'BEFORE_AFTER', 'evidence'):
    os.makedirs(f'{H}/{d}', exist_ok=True)

# ---- copy deliverables (batch1 -> handoff); FBX references ../Textures relative, same layout as Staging
for p in PARTS:
    shutil.copy2(f'{G}/Models/ENV_Temple_{p}.fbx', f'{H}/Models/')
    for t in glob.glob(f'{G}/Textures/ENV_Temple_{p}_*.png'):
        shutil.copy2(t, f'{H}/Textures/')
for f in glob.glob(f'{G}/contact/*_BEFORE_AFTER.png'):
    shutil.copy2(f, f'{H}/BEFORE_AFTER/')
for f in glob.glob(f'{G}/evidence/22_verify_*.json') + [G + '/evidence/31_overlap_visibility.json', G + '/evidence/20_geometry_stats.json']:
    shutil.copy2(f, f'{H}/evidence/')

# ---- per-part table
stats = json.load(open(G + '/evidence/20_geometry_stats.json'))
place = json.load(open(H + '/Batch1_Placement.json'))
count = {}
for r in place['instances']:
    if 'directive' in r['group']:
        continue                                            # directive and recommended backdrop rows are alternatives; count the recommended one
    count[r['part'].replace('ENV_Temple_', '')] = count.get(r['part'].replace('ENV_Temple_', ''), 0) + 1
rows, tot_unique, tot_scene = [], 0, 0
for p in PARTS:
    v = json.load(open(f'{G}/evidence/22_verify_{p}.json'))
    s = stats.get('ENV_Temple_' + p) or stats.get(p) or {}
    fc = v['F_checks']
    tris = v['A_reopen']['tris']
    tot_unique += tris; tot_scene += tris * count.get(p, 0)
    zones_same = len({v['A_reopen']['zone_md5'], v['B_restored']['zone_md5'], v['C2_bake']['zone_md5_after_bake'], v['D_after_swap']['zone_md5'], v['E_reopen']['zone_md5'], v['G_working_copy_updated']['zone_md5']}) == 1
    rows.append(dict(part=p, tris=tris, budget=BUDGET[p], within_budget=tris < BUDGET[p], zone_md5=v['A_reopen']['zone_md5'], zone_md5_identical_at_6_points=zones_same,
                     zone_faces=v['A_reopen']['zone_counts'], zone_texels=v['C1_zone_raster']['texels_by_zone'], tex_res=v['C1_zone_raster']['res'],
                     metallic_mean_by_zone={k: x['metallic_mean'] for k, x in v['C2_per_zone_baked'].items()}, cyan_texels=v['C2_cyan_scan'],
                     fbx_polys=fc['fbx_polys'], fbx_bytes=v['F_fbx']['bytes'], extents_error_fbx_units=fc['max_extent_error_fbx_units'], mesh_bounds_blender=fc['mesh_bounds_blender'],
                     identity_transform=fc['identity_transform'], textures_resolve=fc['textures_resolve'], fbx_texture_links=fc['texture_files'], instances_in_placement=count.get(p, 0)))
json.dump(dict(parts=rows, total_unique_tris=tot_unique, total_scene_tris_all_instances=tot_scene,
               note='scene total = sum over rows of tris x instances (backdrops counted once each at the recommended placement); budget 500000'),
          open(H + '/Batch1_PartTable.json', 'w'), indent=1)
print('unique tris', tot_unique, 'scene tris', tot_scene)
for r in rows:
    print(r['part'], r['tris'], r['within_budget'], r['zone_md5'][:8], r['zone_md5_identical_at_6_points'], r['fbx_polys'], r['extents_error_fbx_units'], r['mesh_bounds_blender'], r['instances_in_placement'], r['fbx_texture_links'], r['cyan_texels'])

# ---- shipped FBX texture link convention (reference only)
ref = subprocess.run(['/usr/bin/strings', ROOT + '/Art/Exports/Environment/Staging/Models/ENV_Temple_Wall_A.fbx'], capture_output=True, text=True).stdout
print('shipped Wall_A FBX texture refs:', sorted(set(re.findall(r'ENV_Temple_Wall_A_\w+\.png', ref))))
mine = subprocess.run(['/usr/bin/strings', H + '/Models/ENV_Temple_Wall_Tall_A.fbx'], capture_output=True, text=True).stdout
print('batch Wall_Tall_A FBX texture refs:', sorted(set(re.findall(r'ENV_Temple_Wall_Tall_A_\w+\.png', mine))))

# ---- SHA-256 manifest of the handoff folder
files = []
for dp, dn, fn in os.walk(H):
    for f in fn:
        if f in ('SHA256SUMS.txt', '.DS_Store'):
            continue
        files.append(os.path.join(dp, f))
files.sort()
with open(H + '/SHA256SUMS.txt', 'w') as out:
    for f in files:
        h = hashlib.sha256(open(f, 'rb').read()).hexdigest()
        out.write(f'{h}  {os.path.relpath(f, H)}\n')
print('manifest files', len(files))

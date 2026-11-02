"""Batch-1 stage 1: build geometry (+UVs, zone_id) for the named assets into the batch1 WORKING COPY (never the production .blend).
  Blender -b --factory-startup --python scripts/20_build.py -- Wall_Tall_A [Wall_Tall_B ...]
Re-runnable: an existing ENV_Temple_<name> object of the same name is replaced. Source materials are NOT regenerated (would unlink them).
"""
import sys, os, json, time, hashlib
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch1/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K
import batch1_assets as BA
assert os.path.dirname(os.path.abspath(K.__file__)) == HERE

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/batch1'
WC = G + '/TempleEnvironmentKit_batch1.blend'
names = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=WC)
assert bpy.data.filepath == WC and bpy.context.scene.name == 'TempleEnvironmentKit'
assert all(m in bpy.data.materials for m in K.SRC_MATS)
coll = bpy.data.collections.get('Batch1_NewParts') or bpy.data.collections.new('Batch1_NewParts')
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)
stats_path = G + '/evidence/20_geometry_stats.json'
stats = json.load(open(stats_path)) if os.path.exists(stats_path) else {}
for i, nm in enumerate(names):
    cat, fn, target, vm, wm, dm, cap = BA.REG1[nm]
    full = 'ENV_Temple_' + nm
    if full in bpy.data.objects:
        old = bpy.data.objects[full]; me = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    t0 = time.time()
    b = fn()
    obj = b.to_object(full, coll)
    obj['value_mult'] = vm; obj['wear_mult'] = wm; obj['damp_mult'] = dm; obj['tone_var'] = 1.0; obj['dirt_mult'] = 1.0
    obj['asset'] = full; obj['category'] = cat
    a3, a2, nt = K.uv_stats(obj)
    res, dens = K.pick_res(a3, a2, target, cap=cap)
    obj['tex_res'] = res
    me = obj.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    zc = K.zone_counts(obj)
    obj.location = (-300.0 + 40.0 * i, -400.0, 0.0)
    stats[full] = dict(tris=nt, area3d_m2=round(a3, 2), uv_fill=round(a2, 3), tex_res=res, texel_density_px_per_m=round(dens, 1), target=target,
                       bbox_min=[round(float(v), 3) for v in co.min(0)], bbox_max=[round(float(v), 3) for v in co.max(0)],
                       dims_m=[round(float(v), 3) for v in (co.max(0) - co.min(0))], faces=len(me.polygons), zones={K.ZONE_NAMES[k]: v for k, v in zc.items()},
                       seconds=round(time.time() - t0, 1))
    print('BUILT', full, json.dumps(stats[full]), flush=True)
json.dump(stats, open(stats_path, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=WC)
print('BUILD_DONE', names)

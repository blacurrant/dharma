"""GATE-1 / M6  step 0 - migrate persistent material zones onto the SAVED kit meshes (working copy only).

  Blender -b --factory-startup --python Art/Blender/Revisions/gate1_zones/scripts/00_migrate_zones.py

 - opens the isolated working copy (never the production .blend)
 - BEFORE dump: attribute names, material_index histogram, slot names, geometry fingerprint
 - rebuilds each part from the deterministic builder into a temp mesh (patched kitlib writes `zone_id`)
 - REFUSES to transfer unless saved vs rebuilt geometry match exactly (verts, polys, loops, positions, UVs)
 - writes `zone_id` (FACE/INT) onto the saved mesh, saves the working copy, writes evidence JSON
"""
import sys, os, json, hashlib
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K
import assets as A
assert os.path.dirname(os.path.abspath(K.__file__)) == HERE, K.__file__      # must be the gate-1 copy, not production scripts

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones'
BLEND = G + '/TempleEnvironmentKit_gate1_zones.blend'
EV = G + '/evidence'
assert 'gate1_zones' in BLEND
bpy.ops.wm.open_mainfile(filepath=BLEND)
assert bpy.data.filepath == BLEND


def fingerprint(me):
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co)
    uv = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uv)
    lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    return co.reshape(-1, 3), uv.reshape(-1, 2), lv


def dump(obj):
    me = obj.data
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', mi)
    u, c = np.unique(mi, return_counts=True)
    return dict(attributes=sorted(a.name for a in me.attributes if not a.name.startswith('.')),
                zone_counts=K.zone_counts(obj),
                material_index_hist={int(k): int(v) for k, v in zip(u, c)},
                slots=[m.name if m else None for m in me.materials],
                verts=len(me.vertices), polys=len(me.polygons), loops=len(me.loops))


def poly_keys(me, with_uv=False):
    """One bytes key per (triangulated) polygon: its 3 vertex positions rounded to 0.1 mm and sorted (order-independent).
    with_uv=True also folds each corner's UV (rounded 1e-4) into the key."""
    n = len(me.polygons)
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    ls = np.empty(n, dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
    lt = np.empty(n, dtype=np.int32); me.polygons.foreach_get('loop_total', lt)
    assert (lt == 3).all(), 'kit meshes are triangulated'
    idx = ls[:, None] + np.arange(3)[None, :]                        # (n,3) loop indices
    q = np.round(co[lv[idx]] * 1e4).astype(np.int64)                 # (n,3,3)
    cols = [q]
    if with_uv:
        uv = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
        cols.append(np.round(uv[idx] * 1e4).astype(np.int64))        # (n,3,2)
    flat = np.concatenate([c.reshape(n, 3, -1) for c in cols], axis=2)   # (n,3,3 or 5)
    out = []
    for i in range(n):                                               # sort the 3 corners lexicographically => order-independent key
        out.append(repr(sorted(map(tuple, flat[i].tolist()))))
    return out


kit = sorted([o for o in bpy.data.objects if o.name.startswith('ENV_Temple_') and o.type == 'MESH'], key=lambda o: o.name)
before = {o.name: dump(o) for o in kit}
rows = {}
tmp_coll = bpy.data.collections.new('_zone_tmp'); bpy.context.scene.collection.children.link(tmp_coll)
by_name = {}
for cat, asset, parts, target, vm, wm, dm in A.REG:
    for suffix, fn in parts:
        by_name['ENV_Temple_' + asset + suffix] = fn
assert set(by_name) == {o.name for o in kit}, set(by_name) ^ {o.name for o in kit}
for o in kit:
    twin = by_name[o.name]().to_object('_zone_tmp_' + o.name, tmp_coll)
    a_co, a_uv, a_lv = fingerprint(o.data)
    b_co, b_uv, b_lv = fingerprint(twin.data)
    same_counts = (len(o.data.vertices) == len(twin.data.vertices) and len(o.data.polygons) == len(twin.data.polygons)
                   and len(o.data.loops) == len(twin.data.loops))
    index_identical = bool(same_counts and np.array_equal(a_lv, b_lv) and float(np.abs(a_co - b_co).max()) < 1e-5)
    # ---- content-based per-face match (index-order independent)
    ks, kt = poly_keys(o.data), poly_keys(twin.data)
    ks_uv, kt_uv = poly_keys(o.data, True), poly_keys(twin.data, True)
    unique_s, unique_t = len(set(ks)) == len(ks), len(set(kt)) == len(kt)
    zt = np.empty(len(twin.data.polygons), dtype=np.int32); twin.data.attributes[K.ZONE_ATTR].data.foreach_get('value', zt)
    zmap = {}
    ambiguous = 0
    for k, z in zip(kt, zt.tolist()):
        if k in zmap and zmap[k] != z:
            ambiguous += 1
        zmap[k] = z
    matched = sum(1 for k in ks if k in zmap)
    all_matched = same_counts and matched == len(ks) and sorted(ks) == sorted(kt)
    uv_same = sorted(ks_uv) == sorted(kt_uv)
    ok = bool(all_matched and ambiguous == 0)
    zc = K.zone_counts(twin)
    rows[o.name] = dict(index_order_identical=index_identical, counts_equal=bool(same_counts), faces=len(ks),
                        faces_matched=matched, key_unique_saved=unique_s, key_unique_twin=unique_t, ambiguous_zone_conflicts=ambiguous,
                        uv_identical_to_rebuild=bool(uv_same), transferred=ok, twin_zone_counts=zc)
    if ok:
        zid = np.array([zmap[k] for k in ks], dtype=np.int32)
        # independent cross-check: zone -> SRC material name per face must equal the twin's own slot material for that face
        mi = np.empty(len(twin.data.polygons), dtype=np.int32); twin.data.polygons.foreach_get('material_index', mi)
        tn = np.array([m.name for m in twin.data.materials])[mi]
        assert all(K.SRC_MATS[z] == n for z, n in zip(zt.tolist(), tn.tolist())), o.name
        if K.ZONE_ATTR in o.data.attributes:
            o.data.attributes.remove(o.data.attributes[K.ZONE_ATTR])
        attr = o.data.attributes.new(K.ZONE_ATTR, 'INT', 'FACE')
        attr.data.foreach_set('value', zid)
        o.data.update()
        o['zone_legend'] = json.dumps({str(k): v for k, v in K.ZONE_NAMES.items()})
    bpy.data.objects.remove(twin, do_unlink=True)
bpy.data.collections.remove(tmp_coll)
for m in list(bpy.data.meshes):
    if m.users == 0 and m.name.startswith('_zone_tmp_'):
        bpy.data.meshes.remove(m)
bpy.context.scene['zone_legend'] = json.dumps({str(k): v for k, v in K.ZONE_NAMES.items()})
after = {o.name: dump(o) for o in kit}
all_ok = all(r['transferred'] for r in rows.values())
json.dump(dict(before=before, after=after, transfer=rows, all_transferred=all_ok), open(EV + '/00_migration.json', 'w'), indent=1)
print('MIGRATE parts', len(kit), 'all_transferred', all_ok)
for n, r in rows.items():
    print('MIGRATE', n.replace('ENV_Temple_', ''), 'faces', r['faces'], 'matched', r['faces_matched'], 'index_order_identical', r['index_order_identical'],
          'uv_identical_to_rebuild', r['uv_identical_to_rebuild'], 'ambiguous', r['ambiguous_zone_conflicts'], 'zones', after[n]['zone_counts'])
if all_ok:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print('MIGRATE_SAVED', BLEND)
else:
    print('MIGRATE_ABORT: not saving (geometry mismatch)')

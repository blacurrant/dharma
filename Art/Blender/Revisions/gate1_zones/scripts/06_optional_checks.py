"""GATE-1b optional checks (working copy / verify blends only).
  (1) sampling-independent zone check for parts with duplicate triangle keys (index-aligned, no bake, no centroid sampling)
  (2) the 21 unexplained PierL probe mismatches: record face/pixel locations; test the bake-margin-bleed hypothesis with a margin-0 probe
  (3) Brazier_A re-bake outliers vs shipped: pixel locations, zone region, containing faces
Outputs: evidence/07_optional_checks.json
"""
import sys, os, json
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K
import assets as A

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/gate1_zones'
WC = G + '/TempleEnvironmentKit_gate1_zones.blend'
out = {}


def zarr(o):
    a = np.empty(len(o.data.polygons), dtype=np.int32); o.data.attributes[K.ZONE_ATTR].data.foreach_get('value', a); return a


def tri_keys(me):
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    q = np.round(co[lv.reshape(-1, 3)] * 1e4).astype(np.int64)
    return [repr(sorted(map(tuple, t.tolist()))) for t in q], co, lv


# ------------------------------------------------------------------ (1)
bpy.ops.wm.open_mainfile(filepath=WC)
mig = json.load(open(G + '/evidence/00_migration.json'))['transfer']
nonunique = sorted(n for n, r in mig.items() if not r['key_unique_saved'] or not r['key_unique_twin'])
fns = {('ENV_Temple_' + a + s): f for c, a, p, *_ in A.REG for s, f in p}
res1 = {}
for name in nonunique:
    o = bpy.data.objects[name]
    twin = fns[name]().to_object('_t_' + name, bpy.context.scene.collection)
    ks, cs_, ls_ = tri_keys(o.data); kt, ct, lt = tri_keys(twin.data)
    zs, zt = zarr(o), K.zone_counts(twin) and np.empty(len(twin.data.polygons), dtype=np.int32)
    twin.data.attributes[K.ZONE_ATTR].data.foreach_get('value', zt)
    index_aligned = bool(len(cs_) == len(ct) and np.array_equal(ls_, lt) and float(np.abs(cs_ - ct).max()) < 1e-6)
    per_index_agree = int((zs == zt).sum()) if index_aligned else None
    groups = {}
    for i, k in enumerate(ks):
        groups.setdefault(k, []).append(i)
    dup = {k: v for k, v in groups.items() if len(v) > 1}
    conflict_groups = sum(1 for v in dup.values() if len(set(zs[v].tolist())) > 1)
    conflict_groups_twin = sum(1 for k, v in ((k, [i for i, kk in enumerate(kt) if kk == k]) for k in list(dup)[:2000]) if len(set(zt[v].tolist())) > 1)
    res1[name] = dict(faces=len(zs), duplicate_key_groups=len(dup), faces_in_duplicate_groups=int(sum(len(v) for v in dup.values())),
                      rebuild_index_aligned_exactly=index_aligned, per_index_zone_agreement=per_index_agree,
                      groups_with_conflicting_zones_saved=int(conflict_groups), groups_with_conflicting_zones_rebuild_checked=int(conflict_groups_twin))
    bpy.data.objects.remove(twin, do_unlink=True)
    print('OPT1', name, res1[name], flush=True)
out['one_nonunique_key_parts'] = dict(parts=nonunique, results=res1,
                                      note='index-aligned compare removes key-matching ambiguity; relies on the rebuild being index-identical (verified with 0 vertex delta + equal loop->vertex arrays)')


# ------------------------------------------------------------------ shared: probe raster
def probe(o, res, margin, samples=4):
    K.setup_cycles(samples)
    sc = bpy.context.scene
    pm = bpy.data.materials.new('_p'); pm.use_nodes = True; nt = pm.node_tree; nt.nodes.clear()
    at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = K.ZONE_ATTR
    ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.inputs[1].default_value = 1.0
    dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 8.0
    em = nt.nodes.new('ShaderNodeEmission'); oc = nt.nodes.new('ShaderNodeOutputMaterial'); cb = nt.nodes.new('ShaderNodeCombineColor')
    nt.links.new(at.outputs['Fac'], ad.inputs[0]); nt.links.new(ad.outputs[0], dv.inputs[0])
    for i in range(3):
        nt.links.new(dv.outputs[0], cb.inputs[i])
    nt.links.new(cb.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], oc.inputs['Surface'])
    saved = [m for m in o.data.materials]
    o.data.materials.clear(); o.data.materials.append(pm)
    img = K._new_img('_probe', res, False); sc.cycles.samples = samples
    K._bake(o, img, 'EMIT', margin=margin)
    a = np.empty(res * res * 4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(res, res, 4)
    bpy.data.images.remove(img)
    o.data.materials.clear()
    for m in saved:
        o.data.materials.append(m)
    bpy.data.materials.remove(pm)
    kk = a[..., 0] * 8.0
    r = np.full((res, res), -1, dtype=np.int32); ok = (np.abs(kk - np.rint(kk)) < 0.12) & (np.rint(kk) >= 1)
    r[ok] = (np.rint(kk[ok]) - 1).astype(int)
    return r


def geom(o, res):
    me = o.data
    uv = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
    tri = uv[ls[:, None] + np.arange(3)[None, :]]
    area = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 1, 1] - tri[:, 0, 1]) * (tri[:, 2, 0] - tri[:, 0, 0])) * res * res
    cen = tri.mean(1)
    return tri, area, np.clip((cen[:, 0] * res).astype(int), 0, res - 1), np.clip((cen[:, 1] * res).astype(int), 0, res - 1)


# ------------------------------------------------------------------ (2)
PL = 'ENV_Temple_Arch_A_PierL'
bpy.ops.wm.open_mainfile(filepath=f'{G}/verify/{PL}/{PL}_verify.blend')
o = bpy.data.objects[PL]; z = zarr(o); res = int(o['tex_res'])
tri, area, ix, iy = geom(o, res)
r10 = probe(o, res, 10); r0 = probe(o, res, 0)
v10, v0 = r10[iy, ix], r0[iy, ix]
bad10 = np.where(v10 != z)[0]
lo = np.floor(tri.min(1) * res).astype(int); hi = np.floor(tri.max(1) * res).astype(int)
rows, expl_cover, bleed = [], 0, 0
for f in bad10:
    cover = np.where((lo[:, 0] <= ix[f]) & (hi[:, 0] >= ix[f]) & (lo[:, 1] <= iy[f]) & (hi[:, 1] >= iy[f]))[0]
    covz = sorted({int(z[c]) for c in cover})
    explained_by_cover = int(v10[f]) in covz and int(v10[f]) != int(z[f])
    expl_cover += explained_by_cover
    if not explained_by_cover:
        bleed += int(v0[f] == -1 or v0[f] == z[f])
        rows.append(dict(face=int(f), zone=K.ZONE_NAMES[int(z[f])], uv_px=[int(ix[f]), int(iy[f])], uv_area_px2=round(float(area[f]), 3), probe_margin10=(K.ZONE_NAMES[int(v10[f])] if v10[f] >= 0 else 'empty'),
                         probe_margin0=(K.ZONE_NAMES[int(v0[f])] if v0[f] >= 0 else 'empty'), zones_of_bbox_covering_faces=[K.ZONE_NAMES[c] for c in covz]))
out['two_PierL_probe_mismatch'] = dict(faces=len(z), mismatched_margin10=int(len(bad10)), explained_by_other_face_covering_texel=int(expl_cover), unexplained_by_cover=len(rows),
                                       unexplained_where_margin0_texel_is_empty_or_own_zone=int(bleed),
                                       margin0_mismatch_total=int((v0 != z).sum()), margin0_mismatch_where_texel_empty=int(((v0 != z) & (v0 == -1)).sum()),
                                       unexplained_faces=rows)
print('OPT2', {k: v for k, v in out['two_PierL_probe_mismatch'].items() if k != 'unexplained_faces'}, flush=True)

# ------------------------------------------------------------------ (3)
BZ = 'ENV_Temple_Brazier_A'
bpy.ops.wm.open_mainfile(filepath=f'{G}/verify/{BZ}/{BZ}_verify.blend')
o = bpy.data.objects[BZ]; z = zarr(o); res = int(o['tex_res'])
tri, area, ix, iy = geom(o, res)
raster = probe(o, res, 0)
lo = np.floor(tri.min(1) * res).astype(int); hi = np.floor(tri.max(1) * res).astype(int)


def load(path, cs):
    im = bpy.data.images.load(path, check_existing=False); im.colorspace_settings.name = cs
    if path.endswith('_Mask.png'):
        im.alpha_mode = 'CHANNEL_PACKED'
    w, h = im.size; a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im); return a.reshape(h, w, 4)


CSM = {'BaseColor': 'sRGB', 'Emission': 'sRGB', 'Normal': 'Non-Color', 'Mask': 'Non-Color'}
b3 = {}
for k in ('BaseColor', 'Normal', 'Mask', 'Emission'):
    S = load(f'{ROOT}/Art/Exports/Environment/Staging/Textures/{BZ}_{k}.png', CSM[k]); Rr = load(f'{G}/bake_out/Textures/{BZ}_{k}.png', CSM[k])
    d = np.abs(S - Rr); dd = d.max(axis=2) if k == 'Mask' else d[..., :3].max(axis=2)
    flag = dd > 0.1
    zh = {('outside_or_edge' if int(q) < 0 else K.ZONE_NAMES[int(q)]): int(c) for q, c in zip(*np.unique(raster[flag], return_counts=True))}
    top = np.dstack(np.unravel_index(np.argsort(dd.ravel())[::-1][:6], dd.shape))[0]
    locs = []
    for (yy, xx) in top:
        cand = np.where((lo[:, 0] <= xx) & (hi[:, 0] >= xx) & (lo[:, 1] <= yy) & (hi[:, 1] >= yy))[0]
        locs.append(dict(x=int(xx), y=int(yy), diff=round(float(dd[yy, xx]), 4), raster_zone=(K.ZONE_NAMES[int(raster[yy, xx])] if raster[yy, xx] >= 0 else 'outside_or_edge'),
                         shipped=[round(float(v), 4) for v in S[yy, xx]], rebake=[round(float(v), 4) for v in Rr[yy, xx]],
                         zones_of_bbox_covering_faces=sorted({K.ZONE_NAMES[int(z[c])] for c in cand}), n_bbox_covering_faces=int(len(cand))))
    b3[k] = dict(texels_gt_0_1=int(flag.sum()), of=int(dd.size), outliers_by_zone_region=zh, mean_abs_diff=round(float(dd.mean()), 6), max=round(float(dd.max()), 4), top_outliers=locs)
    print('OPT3', k, {x: b3[k][x] for x in ('texels_gt_0_1', 'max', 'outliers_by_zone_region')}, flush=True)
out['three_brazier_outliers'] = b3
json.dump(out, open(G + '/evidence/07_optional_checks.json', 'w'), indent=1, default=str)
print('OPTIONAL_DONE')

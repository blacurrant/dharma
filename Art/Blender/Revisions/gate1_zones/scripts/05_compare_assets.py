"""GATE-1b independent comparison (no rebuild anywhere). See GATE1B_METHOD.md.
  Blender -b --factory-startup --python scripts/05_compare_assets.py -- ENV_Temple_Altar_A [more assets]
Inputs: verify_b/<asset>_verify.blend (saved mesh + saved UVs + zone_id), verify_b/<asset>_zoneraster.npy (texel-level zone raster),
        bake_out_b/Textures (re-bake), Art/Exports/Environment/Staging/Textures (SHIPPED, read-only).
Outputs: evidence/06_compare_<asset>.json
"""
import sys, os, json
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/gate1_zones'
SHIP = ROOT + '/Art/Exports/Environment/Staging/Textures'
THR_DIFF = 0.10
THR_METAL, THR_EMIT, THR_CRIMSON, MIN_AREA = 0.25, 0.002, 2.5, 9.0     # fixed a priori (GATE1B_METHOD.md)
CLASS_OF_ZONE = {0: 'stone', 1: 'stone', 2: 'metal', 3: 'metal', 4: 'crimson', 5: 'ember'}


def load(path, cs):
    im = bpy.data.images.load(path, check_existing=False)
    im.colorspace_settings.name = cs
    if path.endswith('_Mask.png'):
        im.alpha_mode = 'CHANNEL_PACKED'
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)


CS = {'BaseColor': 'sRGB', 'Emission': 'sRGB', 'Normal': 'Non-Color', 'Mask': 'Non-Color'}


def face_lookup(tri, lo, hi, z, ix, iy, res):
    cx, cy = (ix + 0.5) / res, (iy + 0.5) / res
    cand = np.where((lo[:, 0] <= ix) & (hi[:, 0] >= ix) & (lo[:, 1] <= iy) & (hi[:, 1] >= iy))[0]
    hits = []
    for f in cand:
        p0, p1, p2 = tri[f]
        d = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(d) < 1e-12:
            continue
        a = ((p1[1] - p2[1]) * (cx - p2[0]) + (p2[0] - p1[0]) * (cy - p2[1])) / d
        b = ((p2[1] - p0[1]) * (cx - p2[0]) + (p0[0] - p2[0]) * (cy - p2[1])) / d
        if a >= -0.02 and b >= -0.02 and (1 - a - b) >= -0.02:
            hits.append(dict(face=int(f), zone=K.ZONE_NAMES[int(z[f])]))
    return hits[:6], int(len(cand))


for ASSET in sys.argv[sys.argv.index('--') + 1:]:
    out = dict(asset=ASSET)
    V = f'{G}/verify_b/{ASSET}_verify.blend'
    bpy.ops.wm.open_mainfile(filepath=V)
    o = bpy.data.objects[ASSET]; me = o.data
    z = np.empty(len(me.polygons), dtype=np.int32); me.attributes[K.ZONE_ATTR].data.foreach_get('value', z)
    res = int(o['tex_res'])
    uv = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
    tri = uv[ls[:, None] + np.arange(3)[None, :]]
    area_px = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 1, 1] - tri[:, 0, 1]) * (tri[:, 2, 0] - tri[:, 0, 0])) * res * res
    cen = tri.mean(1)
    ix = np.clip((cen[:, 0] * res).astype(int), 1, res - 2); iy = np.clip((cen[:, 1] * res).astype(int), 1, res - 2)
    lo = np.floor(tri.min(1) * res).astype(int); hi = np.floor(tri.max(1) * res).astype(int)
    raster = np.load(f'{G}/verify_b/{ASSET}_zoneraster.npy').astype(np.int32)
    maps = [k for k in ('BaseColor', 'Normal', 'Mask', 'Emission') if os.path.exists(f'{SHIP}/{ASSET}_{k}.png')]
    S = {k: load(f'{SHIP}/{ASSET}_{k}.png', CS[k]) for k in maps}
    R = {k: load(f'{G}/bake_out_b/Textures/{ASSET}_{k}.png', CS[k]) for k in maps}
    # sanity: the colour-space switch took effect (raw mask R must be >= its sRGB-decoded self)
    chk = load(f'{SHIP}/{ASSET}_Mask.png', 'sRGB')
    out['sanity_mask_nonColor_mean_ge_sRGB_mean'] = bool(S['Mask'][..., 0].mean() >= chk[..., 0].mean() - 1e-6)
    out['res'] = res; out['faces'] = len(z); out['maps'] = maps

    # ---- 1. per-zone texel regions: diff + shipped vs rebake properties
    regions = {}
    for zz in sorted(int(x) for x in np.unique(z)):
        m = raster == zz
        r = dict(texels=int(m.sum()), faces=int((z == zz).sum()))
        if m.sum() == 0:
            r['note'] = 'no texel raster coverage (all faces sub-texel)'
            regions[K.ZONE_NAMES[zz]] = r; continue
        for k in maps:
            d = np.abs(S[k] - R[k])
            dd = d.max(axis=2) if k == 'Mask' else d[..., :3].max(axis=2)
            r[k] = dict(mean_abs_diff=round(float(dd[m].mean()), 5), frac_texels_gt_0_1=round(float((dd[m] > THR_DIFF).mean()), 5))
        _c = S['BaseColor'][..., :3][m]; _q = _c[:, 0] / (_c[:, 1] + _c[:, 2] + 1e-4)
        r['shipped_albedo_R_over_GplusB_p5_p50_p95'] = [round(float(x), 3) for x in np.percentile(_q, [5, 50, 95])]
        r['shipped_metallic_mean'] = round(float(S['Mask'][..., 0][m].mean()), 4); r['rebake_metallic_mean'] = round(float(R['Mask'][..., 0][m].mean()), 4)
        r['shipped_roughness_mean'] = round(float((1 - S['Mask'][..., 3][m]).mean()), 4); r['rebake_roughness_mean'] = round(float((1 - R['Mask'][..., 3][m]).mean()), 4)
        if 'Emission' in maps:
            r['shipped_emission_max_mean'] = round(float(S['Emission'][..., :3].max(2)[m].mean()), 5); r['rebake_emission_max_mean'] = round(float(R['Emission'][..., :3].max(2)[m].mean()), 5)
        regions[K.ZONE_NAMES[zz]] = r
    out['per_zone_regions'] = regions
    out['raster_unclassified_texels'] = int((raster < 0).sum())

    # ---- 2. global diff + outlier locations
    glob = {}
    for k in maps:
        d = np.abs(S[k] - R[k]); dd = d.max(axis=2) if k == 'Mask' else d[..., :3].max(axis=2)
        flag = dd > THR_DIFF
        zone_hist = {('outside_or_edge' if int(q) < 0 else K.ZONE_NAMES[int(q)]): int(c) for q, c in zip(*np.unique(raster[flag], return_counts=True))}
        top = np.dstack(np.unravel_index(np.argsort(dd.ravel())[::-1][:8], dd.shape))[0]
        locs = []
        for (yy, xx) in top:
            hits, ncand = face_lookup(tri, lo, hi, z, int(xx), int(yy), res)
            locs.append(dict(x=int(xx), y=int(yy), diff=round(float(dd[yy, xx]), 4), raster_zone=(K.ZONE_NAMES[int(raster[yy, xx])] if raster[yy, xx] >= 0 else 'outside_or_edge'),
                             shipped=[round(float(v), 4) for v in S[k][yy, xx]], rebake=[round(float(v), 4) for v in R[k][yy, xx]], faces_containing_texel=hits, faces_bbox_covering_texel=ncand))
        glob[k] = dict(mean_abs_diff=round(float(dd.mean()), 6), p99=round(float(np.percentile(dd, 99)), 4), max=round(float(dd.max()), 4),
                       texels_gt_0_1=int(flag.sum()), frac_gt_0_1=round(float(flag.mean()), 6), outliers_by_zone_region=zone_hist, top_outliers=locs)
    out['global_diff'] = glob

    # ---- 3. independent per-face classification from SHIPPED (and re-baked) textures
    def classify(MP, thr_crimson=THR_CRIMSON):
        ok = area_px >= MIN_AREA
        yy, xx = iy[ok], ix[ok]
        def med3(ch):
            stack = np.stack([ch[yy + dy, xx + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)], axis=0)
            return np.median(stack, axis=0)
        metal = med3(MP['Mask'][..., 0])
        emis = med3(MP['Emission'][..., :3].max(2)) if 'Emission' in MP else np.zeros(ok.sum())
        bc = MP['BaseColor']
        ratio = med3(bc[..., 0]) / (med3(bc[..., 1]) + med3(bc[..., 2]) + 1e-4)
        pred = np.where(emis > THR_EMIT, 'ember', np.where(metal > THR_METAL, 'metal', np.where(ratio > thr_crimson, 'crimson', 'stone')))
        exp = np.array([CLASS_OF_ZONE[int(q)] for q in z[ok]])
        conf = {}
        for e, p in zip(exp.tolist(), pred.tolist()):
            conf.setdefault(e, {}).setdefault(p, 0); conf[e][p] += 1
        agree = float((exp == pred).mean())
        per = {e: round(conf[e].get(e, 0) / sum(conf[e].values()), 4) for e in conf}
        return dict(crimson_threshold=thr_crimson, faces_assessed=int(ok.sum()), faces_excluded_lt_9px2=int((~ok).sum()), agreement=round(agree, 4), agreement_by_expected_class=per, confusion=conf)
    out['classification_from_shipped_textures'] = classify(S)
    out['classification_from_rebake_textures'] = classify(R)
    # POST-HOC (labelled): the a-priori crimson cut-off (2.5) came from hex arithmetic, not from the loaded textures; measured crimson regions sit at R/(G+B)~1.9-2.0
    # vs stone ~0.64 and metal <=0.94, so ANY cut-off in (1.0, 1.8) gives the same answer. 1.4 = midpoint of that gap.
    out['POSTHOC_classification_from_shipped_textures_crimson_1_4'] = classify(S, 1.4)
    out['POSTHOC_classification_from_rebake_textures_crimson_1_4'] = classify(R, 1.4)
    # ---- 4. TEXEL-level classification (sampling-free: every texel has exactly one owning zone from the Cycles raster; no centroid, no median)
    def texel_class(MP, thr):
        valid = raster >= 0
        metal = MP['Mask'][..., 0]
        emis = MP['Emission'][..., :3].max(2) if 'Emission' in MP else np.zeros_like(metal)
        bc = MP['BaseColor'][..., :3]
        ratio = bc[..., 0] / (bc[..., 1] + bc[..., 2] + 1e-4)
        pred = np.where(emis > THR_EMIT, 3, np.where(metal > THR_METAL, 2, np.where(ratio > thr, 1, 0)))          # 0 stone, 1 crimson, 2 metal, 3 ember
        expc = np.vectorize(lambda q: {'stone': 0, 'crimson': 1, 'metal': 2, 'ember': 3}[CLASS_OF_ZONE[int(q)]])(np.arange(6))[np.clip(raster, 0, 5)]
        res_ = {}
        for zz in sorted(int(q) for q in np.unique(raster[valid])):
            mm = raster == zz
            res_[K.ZONE_NAMES[zz]] = dict(texels=int(mm.sum()), agree=round(float((pred[mm] == expc[mm]).mean()), 5))
        return dict(texels_assessed=int(valid.sum()), agreement=round(float((pred[valid] == expc[valid]).mean()), 5), by_zone=res_)
    out['texel_level_classification_shipped_apriori_2_5'] = texel_class(S, THR_CRIMSON)
    out['POSTHOC_texel_level_classification_shipped_crimson_1_4'] = texel_class(S, 1.4)
    out['POSTHOC_texel_level_classification_rebake_crimson_1_4'] = texel_class(R, 1.4)
    # ---- 5. where do the per-face (centroid) disagreements come from?  (posthoc 1.4)
    ok = area_px >= MIN_AREA
    yy_, xx_ = iy[ok], ix[ok]
    def _m3(ch):
        return np.median(np.stack([ch[yy_ + dy, xx_ + dx] for dy in (-1, 0, 1) for dx in (-1, 0, 1)], axis=0), axis=0)
    met_ = _m3(S['Mask'][..., 0]); emi_ = _m3(S['Emission'][..., :3].max(2)) if 'Emission' in S else np.zeros(ok.sum())
    rat_ = _m3(S['BaseColor'][..., 0]) / (_m3(S['BaseColor'][..., 1]) + _m3(S['BaseColor'][..., 2]) + 1e-4)
    pr_ = np.where(emi_ > THR_EMIT, 'ember', np.where(met_ > THR_METAL, 'metal', np.where(rat_ > 1.4, 'crimson', 'stone')))
    ex_ = np.array([CLASS_OF_ZONE[int(q)] for q in z[ok]])
    mis = np.where(pr_ != ex_)[0]
    zf = z[ok]
    rz = raster[yy_, xx_]
    out['face_disagreement_breakdown_POSTHOC'] = dict(
        disagreeing_faces=int(len(mis)),
        median_uv_area_px2_disagreeing=(round(float(np.median(area_px[ok][mis])), 2) if len(mis) else None), median_uv_area_px2_all_assessed=round(float(np.median(area_px[ok])), 2),
        centroid_texel_raster_zone_is_a_different_zone_than_the_face=int((rz[mis] != zf[mis]).sum()) if len(mis) else 0,
        centroid_texel_raster_empty_or_edge=int((rz[mis] < 0).sum()) if len(mis) else 0,
        centroid_texel_raster_equals_own_zone_but_shipped_class_disagrees=int(((rz[mis] == zf[mis])).sum()) if len(mis) else 0,
        disagreeing_faces_whose_shipped_class_equals_class_of_the_zone_that_owns_the_centroid_texel=int(sum(1 for i in mis if rz[i] >= 0 and CLASS_OF_ZONE[int(rz[i])] == pr_[i])))
    json.dump(out, open(f'{G}/evidence/06_compare_{ASSET.replace("ENV_Temple_", "")}.json', 'w'), indent=1, default=str)
    cs = out['classification_from_shipped_textures']
    ph = out['POSTHOC_classification_from_shipped_textures_crimson_1_4']
    print('COMPARE', ASSET, 'POSTHOC(1.4) agreement', ph['agreement'], ph['agreement_by_expected_class'], 'confusion', json.dumps(ph['confusion']))
    print('COMPARE', ASSET, 'sanity', out['sanity_mask_nonColor_mean_ge_sRGB_mean'], '| a-priori shipped-class agreement', cs['agreement'], cs['agreement_by_expected_class'],
          '| assessed', cs['faces_assessed'], 'excluded', cs['faces_excluded_lt_9px2'], flush=True)
    tl = out['POSTHOC_texel_level_classification_shipped_crimson_1_4']
    print('COMPARE', ASSET, 'TEXEL-level agreement (shipped, posthoc 1.4)', tl['agreement'], {k: v['agree'] for k, v in tl['by_zone'].items()}, '| a-priori 2.5:', out['texel_level_classification_shipped_apriori_2_5']['agreement'], '| rebake:', out['POSTHOC_texel_level_classification_rebake_crimson_1_4']['agreement'])
    print('COMPARE', ASSET, 'face-disagreement breakdown', json.dumps(out['face_disagreement_breakdown_POSTHOC']))
    for zn, r in regions.items():
        print('   ZONE', zn, {k: v for k, v in r.items() if k in ('texels', 'faces', 'shipped_metallic_mean', 'rebake_metallic_mean')}, {k: r[k]['mean_abs_diff'] for k in maps if k in r}, flush=True)
    for k in maps:
        print('   GLOBAL', k, {x: glob[k][x] for x in ('mean_abs_diff', 'p99', 'max', 'texels_gt_0_1')}, glob[k]['outliers_by_zone_region'], flush=True)
print('COMPARE_DONE')

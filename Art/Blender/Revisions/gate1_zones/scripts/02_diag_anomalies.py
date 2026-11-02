"""GATE-1 diagnostics for two anomalies seen in 01_verify (read-only on verify blends; writes only evidence JSON + verify/diag/)."""
import sys, os, json
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones'
D = G + '/verify/diag'; os.makedirs(D, exist_ok=True)
out = {}


def zones(o):
    a = np.empty(len(o.data.polygons), dtype=np.int32); o.data.attributes[K.ZONE_ATTR].data.foreach_get('value', a); return a


# ---------------------------------------------------------------- 1. probe mismatches on PierL: are they sub-texel faces?
A = 'ENV_Temple_Arch_A_PierL'
bpy.ops.wm.open_mainfile(filepath=f'{G}/verify/{A}/{A}_verify.blend')
o = bpy.data.objects[A]; z = zones(o); res = int(o['tex_res'])
me = o.data
uvl = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uvl); uvl = uvl.reshape(-1, 2)
ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
tri = uvl[ls[:, None] + np.arange(3)[None, :]]
cen = tri.mean(1)
uv_area_px = 0.5 * np.abs((tri[:, 1, 0] - tri[:, 0, 0]) * (tri[:, 2, 1] - tri[:, 0, 1]) - (tri[:, 1, 1] - tri[:, 0, 1]) * (tri[:, 2, 0] - tri[:, 0, 0])) * res * res
ix = np.clip((cen[:, 0] * res).astype(int), 0, res - 1); iy = np.clip((cen[:, 1] * res).astype(int), 0, res - 1)
m = bpy.data.materials.new('_p'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = K.ZONE_ATTR
dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 5.0
em = nt.nodes.new('ShaderNodeEmission'); oc = nt.nodes.new('ShaderNodeOutputMaterial'); cb = nt.nodes.new('ShaderNodeCombineColor')
nt.links.new(at.outputs['Fac'], dv.inputs[0])
for i in range(3):
    nt.links.new(dv.outputs[0], cb.inputs[i])
nt.links.new(cb.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], oc.inputs['Surface'])
o.data.materials.clear(); o.data.materials.append(m)
K.setup_cycles(4)
img = K._new_img('probe', res, False); K._bake(o, img, 'EMIT')
a = np.empty(res * res * 4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(res, res, 4)
err = np.abs(a[iy, ix, 0] - z / 5.0)
bad = err > 0.02
# key test: is the bake pixel at the centroid owned by ANOTHER face (dense small faces share texels)?  -> compare against the
# set of zone values of ALL faces whose UV bbox covers that texel.
owners = {}
lo = np.floor(tri.min(1) * res).astype(int); hi = np.floor(tri.max(1) * res).astype(int)
for fi in np.where(bad)[0]:
    covered = set()
    for fj in np.where((lo[:, 0] <= ix[fi]) & (hi[:, 0] >= ix[fi]) & (lo[:, 1] <= iy[fi]) & (hi[:, 1] >= iy[fi]))[0]:
        covered.add(int(z[fj]))
    owners[int(fi)] = covered
pix_val = np.rint(a[iy[bad], ix[bad], 0] * 5.0).astype(int)
explained = sum(1 for fi, v in zip(np.where(bad)[0], pix_val) if int(v) in owners[int(fi)])
out['probe_PierL'] = dict(faces=len(z), mismatched=int(bad.sum()), mismatched_uv_area_px_max=round(float(uv_area_px[bad].max()), 3) if bad.any() else None,
                          mismatched_uv_area_px_median=round(float(np.median(uv_area_px[bad])), 3) if bad.any() else None,
                          all_faces_uv_area_px_median=round(float(np.median(uv_area_px)), 3),
                          mismatched_faces_whose_baked_value_is_a_zone_of_another_face_covering_that_texel=int(explained),
                          mismatched_zones=[int(x) for x in np.unique(z[bad])])
print('DIAG1', out['probe_PierL'])

# ---------------------------------------------------------------- 2. opt-in colour round trip: colour-space of FBX vertex colours
B = 'ENV_Temple_Brazier_A'; P = 'ENV_Temple_Arch_A_PierL'
res_ct = {}
for asset in (B, P):
    bpy.ops.wm.open_mainfile(filepath=f'{G}/verify/{asset}/{asset}_verify.blend')
    o = bpy.data.objects[asset]; zz = zones(o); me = o.data
    # palette of well separated values (0, .2, .4, .6, .8, 1.0 never relied on: decode by nearest palette entry under BOTH hypotheses)
    zc = me.attributes.new('zone_rgb', 'FLOAT_COLOR', 'CORNER')
    ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
    col = np.zeros((len(me.loops), 4), dtype=np.float32); col[:, 3] = 1
    for k in range(3):
        col[ls + k, 0] = zz / 5.0
    zc.data.foreach_set('color', col.ravel())
    tmpc = bpy.data.collections.new('_f'); bpy.context.scene.collection.children.link(tmpc)
    for ctype in ('LINEAR', 'SRGB'):
        t = bpy.data.objects.new(asset + '_x', me); tmpc.objects.link(t)
        for x in bpy.context.view_layer.objects:
            x.select_set(False)
        t.select_set(True); bpy.context.view_layer.objects.active = t
        pth = f'{D}/{asset}_{ctype}.fbx'
        bpy.ops.export_scene.fbx(filepath=pth, use_selection=True, object_types={'MESH'}, axis_forward='-Z', axis_up='Y', use_triangles=True,
                                 colors_type=ctype, bake_space_transform=True, apply_scale_options='FBX_SCALE_ALL', mesh_smooth_type='OFF')
        bpy.data.objects.remove(t)
        res_ct.setdefault(asset, {})[ctype] = pth
    me.attributes.remove(zc)
    for x in list(bpy.data.collections):
        if x.name == '_f':
            bpy.data.collections.remove(x)
    res_ct[asset]['src_hist'] = {int(k): int(v) for k, v in zip(*np.unique(zz, return_counts=True))}
rt = {}
for asset in (B, P):
    for ctype in ('LINEAR', 'SRGB'):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=res_ct[asset][ctype])
        x = [q for q in bpy.data.objects if q.type == 'MESH'][0]
        ca = x.data.color_attributes[0]
        buf = np.empty(len(x.data.loops) * 4, dtype=np.float32); ca.data.foreach_get('color', buf); buf = buf.reshape(-1, 4)
        ls = np.empty(len(x.data.polygons), dtype=np.int32); x.data.polygons.foreach_get('loop_start', ls)
        r = buf[ls, 0]
        u, c = np.unique(np.round(r, 3), return_counts=True)
        # hypothesis decode: value -> zone using the inverse of the sRGB transfer (importer converts file-sRGB to linear)
        def srgb_to_lin(v): return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)
        pal = {z: float(srgb_to_lin(np.array(z / 5.0))) for z in res_ct[asset]['src_hist']}
        palz = np.array(list(pal.keys())); palv = np.array(list(pal.values()))
        dec_srgbhyp = palz[np.abs(r[:, None] - palv[None, :]).argmin(1)]
        palv2 = np.array([z / 5.0 for z in palz])
        dec_direct = palz[np.abs(r[:, None] - palv2[None, :]).argmin(1)]
        hist = lambda arr: {int(k): int(v) for k, v in zip(*np.unique(arr, return_counts=True))}
        rt[f'{asset}_{ctype}'] = dict(distinct_values_after_import=[(float(a_), int(b_)) for a_, b_ in zip(u, c)],
                                      decode_if_direct=hist(dec_direct), decode_if_srgb_to_linear=hist(dec_srgbhyp), source=res_ct[asset]['src_hist'])
out['optin_colour_roundtrip'] = rt
for k, v in rt.items():
    print('DIAG2', k, 'distinct', v['distinct_values_after_import'], '| direct', v['decode_if_direct'] == v['source'], v['decode_if_direct'], '| srgb->lin', v['decode_if_srgb_to_linear'] == v['source'], v['decode_if_srgb_to_linear'])
json.dump(out, open(G + '/evidence/02_diagnostics.json', 'w'), indent=1, default=str)
print('DIAG_DONE')

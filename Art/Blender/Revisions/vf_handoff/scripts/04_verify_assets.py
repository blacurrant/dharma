"""GATE-1b per-asset verification (working copy only). See GATE1B_METHOD.md.
  Blender -b --factory-startup --python scripts/04_verify_assets.py -- ENV_Temple_Altar_A
Sequence (zone md5 asserted at each *):
  A* reopen working copy  -> B* restore SRC slots from zone_id -> C1 texel-level zone raster (margin-0 Cycles bake of the attribute)
  -> C2* bake from the SAVED mesh+UVs (+ the same painterly/pack post-process as the shipped pipeline) -> D* swap to baked material
  -> E* save + reopen -> F  FBX with the exact 05_export.py settings, file-level compare with the shipped FBX
Outputs only under vf_handoff/{bake_out_b,verify_b,evidence}.
"""
import sys, os, json, hashlib, time
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Vector
import kitlib as K
assert os.path.dirname(os.path.abspath(K.__file__)) == HERE

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/vf_handoff'
WC = G + '/TempleEnvironmentKit_vf_working.blend'
OUTB = G + '/bake_out_b'; TEX = OUTB + '/Textures'; SRCTEX = OUTB + '/Source'; MDL = OUTB + '/Models'; V = G + '/verify_b'
for d in (TEX, SRCTEX, MDL, V):
    os.makedirs(d, exist_ok=True)
ASSET = sys.argv[sys.argv.index('--') + 1]
SHIP_FBX = f'{ROOT}/Art/Exports/Environment/Staging/Models/{ASSET}.fbx'
rep = dict(asset=ASSET, t0=time.strftime('%H:%M:%S'))
t_start = time.time()


def zarr(o):
    a = np.empty(len(o.data.polygons), dtype=np.int32); o.data.attributes[K.ZONE_ATTR].data.foreach_get('value', a); return a


def zmd5(o):
    return hashlib.md5(zarr(o).tobytes()).hexdigest()


def state(o):
    me = o.data
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', mi)
    u, c = np.unique(mi, return_counts=True)
    return dict(slots=[m.name if m else None for m in me.materials], material_index_hist={int(k): int(v) for k, v in zip(u, c)},
                zone_counts={K.ZONE_NAMES[k]: v for k, v in (K.zone_counts(o) or {}).items()})


# ---------------------------------------------------------------- A reopen
bpy.ops.wm.open_mainfile(filepath=WC)
assert bpy.data.filepath == WC
o = bpy.data.objects[ASSET]
H = zmd5(o); n_faces = len(o.data.polygons)
rep['A_reopen'] = dict(zone_md5=H, faces=n_faces, **state(o))
assert rep['A_reopen']['material_index_hist'] == {0: n_faces} and rep['A_reopen']['slots'][0].startswith('MI_')
print('A', rep['A_reopen'], flush=True)

# ---------------------------------------------------------------- B restore
K.restore_zone_slots(o)
assert zmd5(o) == H
rep['B_restored'] = dict(zone_md5=zmd5(o), **state(o))
mi = np.empty(n_faces, dtype=np.int32); o.data.polygons.foreach_get('material_index', mi)
nm = np.array([m.name for m in o.data.materials])[mi]
assert all(K.SRC_MATS[z] == n for z, n in zip(zarr(o).tolist(), nm.tolist()))
print('B', rep['B_restored'], flush=True)

# ---------------------------------------------------------------- bake environment
res = int(o['tex_res'])
sc = bpy.context.scene
if 'TempleBakeWorld' not in bpy.data.worlds:
    w = bpy.data.worlds.new('TempleBakeWorld'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1); w.light_settings.distance = 1.2
sc.world = bpy.data.worlds['TempleBakeWorld']
K.setup_cycles(32)

# ---------------------------------------------------------------- C1 texel-level zone raster (value (z+1)/8, margin 0 => no dilation)
src_slots = [m for m in o.data.materials]
pm = bpy.data.materials.new('_zone_probe_b'); pm.use_nodes = True
nt = pm.node_tree; nt.nodes.clear()
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = K.ZONE_ATTR
ad = nt.nodes.new('ShaderNodeMath'); ad.operation = 'ADD'; ad.inputs[1].default_value = 1.0
dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 8.0
em = nt.nodes.new('ShaderNodeEmission'); oc = nt.nodes.new('ShaderNodeOutputMaterial'); cb = nt.nodes.new('ShaderNodeCombineColor')
nt.links.new(at.outputs['Fac'], ad.inputs[0]); nt.links.new(ad.outputs[0], dv.inputs[0])
for i in range(3):
    nt.links.new(dv.outputs[0], cb.inputs[i])
nt.links.new(cb.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], oc.inputs['Surface'])
o.data.materials.clear(); o.data.materials.append(pm)
zi = K._new_img(ASSET + '_zraster', res, False)
sc.cycles.samples = 4
K._bake(o, zi, 'EMIT', margin=0)
a = np.empty(res * res * 4, dtype=np.float32); zi.pixels.foreach_get(a); a = a.reshape(res, res, 4)
kk = a[..., 0] * 8.0
ok = (np.abs(kk - np.rint(kk)) < 0.12) & (np.rint(kk) >= 1)
raster = np.full((res, res), -1, dtype=np.int8); raster[ok] = (np.rint(kk[ok]) - 1).astype(np.int8)
np.save(f'{V}/{ASSET}_zoneraster.npy', raster)
cov = {K.ZONE_NAMES[int(z)]: int((raster == z).sum()) for z in np.unique(raster) if z >= 0}
rep['C1_zone_raster'] = dict(res=res, texels_by_zone=cov, texels_empty_or_edge=int((raster < 0).sum()), covered_fraction=round(float((raster >= 0).mean()), 4))
bpy.data.images.remove(zi)
o.data.materials.clear()
bpy.data.materials.remove(pm)
K.restore_zone_slots(o)
assert zmd5(o) == H
print('C1', rep['C1_zone_raster'], flush=True)

# ---------------------------------------------------------------- C2 bake from the saved mesh + saved UVs (same post-process as 02_bake)
def save_img(img, path, rgba=False):
    img.filepath_raw = path; img.file_format = 'PNG'
    if rgba:
        img.alpha_mode = 'CHANNEL_PACKED'
    img.save()


files = {k: f'{TEX}/{ASSET}_{k}.png' for k in ('BaseColor', 'Normal', 'Mask')}
has_em = any('Ember' in m.name for m in o.data.materials)
if has_em:
    files['Emission'] = f'{TEX}/{ASSET}_Emission.png'
t0 = time.time()
imgs = K.bake_maps(o, res, SRCTEX, ASSET, tex_samples=(32, 16, 4))
H_bake = zmd5(o)
assert H_bake == H
col = K.img_to_np(imgs['BaseColor']); r = 3 if res >= 2048 else 2
base = col.copy(); base[..., :3] = K.painterly(col[..., :3], r, 0.65); base[..., 3] = 1.0
save_img(K.np_to_img(base, ASSET + '_BaseColor_f', True), files['BaseColor'])
save_img(imgs['Normal'], files['Normal'])
mask = K.pack_mask(K.img_to_np(imgs['Metal']), K.img_to_np(imgs['AO']), K.img_to_np(imgs['Rough']))
save_img(K.np_to_img(mask, ASSET + '_Mask_f', False, True), files['Mask'], rgba=True)
if has_em:
    save_img(imgs['Emission'], files['Emission'])
for im in list(imgs.values()):
    bpy.data.images.remove(im)
rep['C2_bake'] = dict(res=res, seconds=round(time.time() - t0, 1), files={k: os.path.relpath(v, G) for k, v in files.items()}, zone_md5_after_bake=H_bake,
                      slots_during_bake=[m.name for m in o.data.materials])
print('C2', rep['C2_bake'], flush=True)

# ---------------------------------------------------------------- D material swap
name = 'MI_Temple_' + ASSET.replace('ENV_Temple_', '')
if name in bpy.data.materials:
    bpy.data.materials.remove(bpy.data.materials[name])
m = bpy.data.materials.new(name); m.use_nodes = True
nt = m.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(pb.outputs[0], out.inputs[0])


def tex(path, cs):
    n = nt.nodes.new('ShaderNodeTexImage'); img = bpy.data.images.load(path, check_existing=True); img.colorspace_settings.name = cs
    if cs == 'Non-Color' and path.endswith('_Mask.png'):
        img.alpha_mode = 'CHANNEL_PACKED'
    n.image = img; return n


tb = tex(files['BaseColor'], 'sRGB'); nt.links.new(tb.outputs['Color'], pb.inputs['Base Color'])
tn = tex(files['Normal'], 'Non-Color'); nmn = nt.nodes.new('ShaderNodeNormalMap'); nt.links.new(tn.outputs['Color'], nmn.inputs['Color']); nt.links.new(nmn.outputs['Normal'], pb.inputs['Normal'])
tm = tex(files['Mask'], 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tm.outputs['Color'], sp.inputs[0]); nt.links.new(sp.outputs['Red'], pb.inputs['Metallic'])
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0; nt.links.new(tm.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], pb.inputs['Roughness'])
if 'Emission' in files:
    te = tex(files['Emission'], 'sRGB'); nt.links.new(te.outputs['Color'], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = 1.0
o['src_materials'] = ','.join(s.name for s in src_slots)
o.data.materials.clear(); o.data.materials.append(m)
H_swap = zmd5(o)
assert H_swap == H
rep['D_after_swap'] = dict(zone_md5=H_swap, **state(o))
assert rep['D_after_swap']['material_index_hist'] == {0: n_faces}
print('D', rep['D_after_swap'], flush=True)

# ---------------------------------------------------------------- E save + reopen
VB = f'{V}/{ASSET}_verify.blend'
bpy.ops.wm.save_as_mainfile(filepath=VB)
bpy.ops.wm.open_mainfile(filepath=VB)
o = bpy.data.objects[ASSET]
H_re = zmd5(o)
rep['E_reopen'] = dict(file=os.path.relpath(VB, G), zone_md5=H_re, same_as_original=(H_re == H), **state(o))
assert H_re == H
print('E', rep['E_reopen'], flush=True)

# ---------------------------------------------------------------- F FBX (exact 05_export settings)
FB = f'{MDL}/{ASSET}.fbx'
tmpc = bpy.data.collections.new('_x'); bpy.context.scene.collection.children.link(tmpc)
t = bpy.data.objects.new(ASSET, o.data); tmpc.objects.link(t)
o.name = ASSET + '_src'; t.name = ASSET
for x in bpy.context.view_layer.objects:
    x.select_set(False)
t.select_set(True); bpy.context.view_layer.objects.active = t
bpy.ops.export_scene.fbx(filepath=FB, use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                         mesh_smooth_type='OFF', use_triangles=True, use_tspace=True, colors_type='NONE', add_leaf_bones=False,
                         path_mode='RELATIVE', embed_textures=False, bake_anim=False, use_custom_props=False)
from io_scene_fbx import parse_fbx


def inspect(pth):
    root, ver = parse_fbx.parse(pth)
    objs = [e for e in root.elems if e.id == b'Objects'][0]
    d = dict(bytes=os.path.getsize(pth), fbx_version=ver, textures=[], materials=[], models=[])
    for e in root.elems:
        if e.id == b'GlobalSettings':
            for ch in e.elems:
                if ch.id == b'Properties70':
                    for p in ch.elems:
                        if p.id == b'P' and p.props[0].decode() in ('UpAxis', 'UnitScaleFactor'):
                            d[p.props[0].decode()] = p.props[4]
    for e in objs.elems:
        if e.id == b'Texture':
            rel = [c for c in e.elems if c.id == b'RelativeFilename'][0].props[0].decode()
            d['textures'].append((os.path.basename(rel), os.path.exists(os.path.normpath(os.path.join(os.path.dirname(pth), rel)))))
        elif e.id == b'Material':
            d['materials'].append(e.props[1].decode().split('\x00')[0])
        elif e.id == b'Model':
            ps = {p.props[0].decode(): [float(x) for x in p.props[4:]] for ch in e.elems if ch.id == b'Properties70' for p in ch.elems if p.id == b'P' and p.props[0].decode() in ('Lcl Translation', 'Lcl Rotation', 'Lcl Scaling')}
            d['models'].append(dict(name=e.props[1].decode().split('\x00')[0], **ps))
        elif e.id == b'Geometry':
            vs = np.array([c for c in e.elems if c.id == b'Vertices'][0].props[0]).reshape(-1, 3)
            d['vertex_min'] = [round(float(x), 4) for x in vs.min(0)]; d['vertex_max'] = [round(float(x), 4) for x in vs.max(0)]
            d['polys'] = int(sum(1 for i in [c for c in e.elems if c.id == b'PolygonVertexIndex'][0].props[0] if i < 0))
    return d


g, s = inspect(FB), inspect(SHIP_FBX)
rep['F_fbx_gate1'] = g; rep['F_fbx_shipped'] = s
rep['F_checks'] = dict(polys_equal=g['polys'] == s['polys'], vertex_extents_equal=(g['vertex_min'] == s['vertex_min'] and g['vertex_max'] == s['vertex_max']),
                       up_axis_equal=g.get('UpAxis') == s.get('UpAxis'), unit_scale_equal=g.get('UnitScaleFactor') == s.get('UnitScaleFactor'),
                       materials_equal=g['materials'] == s['materials'], textures_equal=sorted(g['textures']) == sorted(s['textures']),
                       identity_transform_gate1=all(all(abs(v) < 1e-6 for v in m.get('Lcl Translation', [0, 0, 0]) + m.get('Lcl Rotation', [0, 0, 0])) and all(abs(v - 1) < 1e-6 for v in m.get('Lcl Scaling', [1, 1, 1])) for m in g['models']),
                       zone_id_in_fbx_bytes=('zone_id' in open(FB, 'rb').read().decode('latin1')))
print('F', rep['F_checks'], flush=True)
rep['seconds_total'] = round(time.time() - t_start, 1)
json.dump(rep, open(f'{G}/evidence/05_verify_{ASSET.replace("ENV_Temple_", "")}.json', 'w'), indent=1, default=str)
print('VERIFY_B_DONE', ASSET)

"""GATE-1 / M6  step 1 - prove zones survive: reopen -> restore slots -> BAKE -> material swap -> save/reopen -> FBX (+ opt-in).

  Blender -b --factory-startup --python scripts/01_verify_zones.py -- ENV_Temple_Arch_A_PierL
Works on the isolated working copy only. Writes ONLY under Art/Blender/Revisions/gate1_zones/ (evidence/, verify/).
Evidence JSON: evidence/01_verify_<asset>.json
"""
import sys, os, json, hashlib, math
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K
import assets as A
assert os.path.dirname(os.path.abspath(K.__file__)) == HERE

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones'
SRC_BLEND = G + '/TempleEnvironmentKit_gate1_zones.blend'
ASSET = sys.argv[sys.argv.index('--') + 1]
V = f'{G}/verify/{ASSET}'; os.makedirs(V, exist_ok=True)
EV = G + '/evidence'
PROD_FBX = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Models/' + ASSET.rsplit('_Pier', 1)[0].rsplit('_Span', 1)[0] + '.fbx'
rep = dict(asset=ASSET)


def zhash(obj):
    a = obj.data.attributes[K.ZONE_ATTR]
    arr = np.empty(len(obj.data.polygons), dtype=np.int32); a.data.foreach_get('value', arr)
    return hashlib.md5(arr.tobytes()).hexdigest(), arr


def state(obj):
    me = obj.data
    mi = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('material_index', mi)
    u, c = np.unique(mi, return_counts=True)
    return dict(slots=[m.name if m else None for m in me.materials], material_index_hist={int(k): int(v) for k, v in zip(u, c)},
                attributes=sorted(a.name for a in me.attributes if not a.name.startswith('.')), zone_counts=K.zone_counts(obj))


# ------------------------------------------------------------------ A. reopen
bpy.ops.wm.open_mainfile(filepath=SRC_BLEND)
assert bpy.data.filepath == SRC_BLEND
o = bpy.data.objects[ASSET]
h0, zones0 = zhash(o)
rep['A_reopen'] = dict(file=SRC_BLEND, zone_md5=h0, **state(o))
print('A reopen', rep['A_reopen'])
assert rep['A_reopen']['slots'] and rep['A_reopen']['slots'][0].startswith('MI_'), 'expected post-bake single material state'
assert rep['A_reopen']['material_index_hist'] == {0: len(zones0)}, 'defect reproduced: material_index carries no zone info'

# ------------------------------------------------------------------ B. rebuild slots from attribute only
K.restore_zone_slots(o)
rep['B_restored'] = state(o)
h1, _ = zhash(o)
assert h1 == h0
mi = np.empty(len(o.data.polygons), dtype=np.int32); o.data.polygons.foreach_get('material_index', mi)
names = np.array([m.name for m in o.data.materials])[mi]
assert all(K.SRC_MATS[z] == n for z, n in zip(zones0.tolist(), names.tolist()))
print('B restored', rep['B_restored'])

# independent cross-check vs a fresh builder rebuild (matched by vertex position; builder knows the zones from construction)
cat, fn = None, None
for c, a, parts, *_ in A.REG:
    for s, f in parts:
        if 'ENV_Temple_' + a + s == ASSET:
            fn = f
tw = fn().to_object('_twin', bpy.context.scene.collection)


def keys(me):
    co = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    lv = np.empty(len(me.loops), dtype=np.int32); me.loops.foreach_get('vertex_index', lv)
    q = np.round(co[lv.reshape(-1, 3)] * 1e4).astype(np.int64)
    return [repr(sorted(map(tuple, t.tolist()))) for t in q]


tz = np.empty(len(tw.data.polygons), dtype=np.int32); tw.data.attributes[K.ZONE_ATTR].data.foreach_get('value', tz)
tmap = dict(zip(keys(tw.data), tz.tolist()))
ks = keys(o.data)
indep = sum(1 for k, z in zip(ks, zones0.tolist()) if tmap.get(k) == z)
rep['B_independent_check'] = dict(faces=len(ks), faces_agree_with_fresh_builder_rebuild=indep)
assert indep == len(ks)
bpy.data.objects.remove(tw, do_unlink=True)

# ------------------------------------------------------------------ C. intended bake (resolution = kit value) on the SRC zones
res = int(o['tex_res'])
K.setup_cycles(32)
sc = bpy.context.scene
if 'TempleBakeWorld' in bpy.data.worlds:
    sc.world = bpy.data.worlds['TempleBakeWorld']
imgs = K.bake_maps(o, res, V, ASSET, tex_samples=(32, 16, 4))
rep['C_bake'] = dict(res=res, maps=sorted(imgs))
h2, _ = zhash(o)
assert h2 == h0
# --- sample bakes at every face's UV centroid, grouped by zone (proves the zone regions bake to their own materials)


def px(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a); return a.reshape(h, w, 4)


me = o.data
uvl = np.empty(len(me.loops) * 2, dtype=np.float32); me.uv_layers.active.data.foreach_get('uv', uvl); uvl = uvl.reshape(-1, 2)
ls = np.empty(len(me.polygons), dtype=np.int32); me.polygons.foreach_get('loop_start', ls)
cen = uvl[ls[:, None] + np.arange(3)[None, :]].mean(axis=1)
ix = np.clip((cen[:, 0] * res).astype(int), 0, res - 1); iy = np.clip((cen[:, 1] * res).astype(int), 0, res - 1)
base, rough, metal, ao = px(imgs['BaseColor']), px(imgs['Rough']), px(imgs['Metal']), px(imgs['AO'])


def lin2srgb(x):
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 1e-9), 1 / 2.4) - 0.055)


per_zone = {}
for z in sorted(set(zones0.tolist())):
    m = zones0 == z
    col = base[iy[m], ix[m], :3].mean(0)
    per_zone[K.ZONE_NAMES[z]] = dict(faces=int(m.sum()), albedo_srgb_mean=[round(float(v), 3) for v in lin2srgb(col)],
                                     metallic_mean=round(float(metal[iy[m], ix[m], 0].mean()), 3),
                                     roughness_mean=round(float(rough[iy[m], ix[m], 0].mean()), 3),
                                     ao_mean=round(float(ao[iy[m], ix[m], 0].mean()), 3))
rep['C_bake']['per_zone_from_baked_maps'] = per_zone
print('C per-zone', json.dumps(per_zone))

# --- shader-side proof: bake the zone_id attribute itself through Cycles (Attribute node -> Emission), compare to the array
ztmp = bpy.data.materials.new('_zone_probe'); ztmp.use_nodes = True
nt = ztmp.node_tree; nt.nodes.clear()
at = nt.nodes.new('ShaderNodeAttribute'); at.attribute_type = 'GEOMETRY'; at.attribute_name = K.ZONE_ATTR
dv = nt.nodes.new('ShaderNodeMath'); dv.operation = 'DIVIDE'; dv.inputs[1].default_value = 5.0
em = nt.nodes.new('ShaderNodeEmission'); oc = nt.nodes.new('ShaderNodeOutputMaterial'); cb = nt.nodes.new('ShaderNodeCombineColor')
nt.links.new(at.outputs['Fac'], dv.inputs[0])
for i in range(3):
    nt.links.new(dv.outputs[0], cb.inputs[i])
nt.links.new(cb.outputs[0], em.inputs['Color']); nt.links.new(em.outputs[0], oc.inputs['Surface'])
saved_slots = [m for m in o.data.materials]
o.data.materials.clear(); o.data.materials.append(ztmp)
zi = K._new_img(ASSET + '_zoneprobe', res, False)
sc.cycles.samples = 4
K._bake(o, zi, 'EMIT')
zp = px(zi)[iy, ix, 0]
err = np.abs(zp - zones0 / 5.0)
rep['C_zone_attribute_baked_through_shader'] = dict(max_abs_err=round(float(err.max()), 4), faces_within_0_02=int((err < 0.02).sum()), faces=len(zones0))
print('C zone-through-shader', rep['C_zone_attribute_baked_through_shader'])
o.data.materials.clear()
for m in saved_slots:
    o.data.materials.append(m)
bpy.data.materials.remove(ztmp)
bpy.data.images.remove(zi)

# ------------------------------------------------------------------ D. swap to baked final material exactly like 02_bake does
def save_png(img, path):
    img.filepath_raw = path; img.file_format = 'PNG'; img.save()


bc, nm = f'{V}/{ASSET}_BaseColor_raw.png', f'{V}/{ASSET}_Normal.png'
save_png(imgs['BaseColor'], bc); save_png(imgs['Normal'], nm)
mname = 'MI_gate1_verify_' + ASSET.replace('ENV_Temple_', '')
fm = bpy.data.materials.new(mname); fm.use_nodes = True
nt = fm.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(pb.outputs[0], out.inputs[0])
t1 = nt.nodes.new('ShaderNodeTexImage'); t1.image = bpy.data.images.load(bc, check_existing=False); t1.image.colorspace_settings.name = 'sRGB'
t2 = nt.nodes.new('ShaderNodeTexImage'); t2.image = bpy.data.images.load(nm, check_existing=False); t2.image.colorspace_settings.name = 'Non-Color'
nmn = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(t1.outputs['Color'], pb.inputs['Base Color']); nt.links.new(t2.outputs['Color'], nmn.inputs['Color']); nt.links.new(nmn.outputs['Normal'], pb.inputs['Normal'])
o.data.materials.clear(); o.data.materials.append(fm)            # <- the step that destroyed zones in the original pipeline
rep['D_after_material_swap'] = state(o)
h3, _ = zhash(o)
rep['D_after_material_swap']['zone_md5'] = h3
assert h3 == h0 and rep['D_after_material_swap']['material_index_hist'] == {0: len(zones0)}
print('D after swap', rep['D_after_material_swap'])

# ------------------------------------------------------------------ E. save + reopen
VB = f'{V}/{ASSET}_verify.blend'
for im in list(bpy.data.images):
    if im.name.endswith(('_AO', '_Rough', '_Metal', '_BaseColor', '_Normal', '_Emission')) and im.users == 0:
        bpy.data.images.remove(im)
bpy.ops.wm.save_as_mainfile(filepath=VB)
bpy.ops.wm.open_mainfile(filepath=VB)
o = bpy.data.objects[ASSET]
h4, zones4 = zhash(o)
rep['E_reopen_after_bake_swap'] = dict(file=VB, zone_md5=h4, same_as_original=(h4 == h0), **state(o))
print('E reopen', rep['E_reopen_after_bake_swap'])
assert h4 == h0

# ------------------------------------------------------------------ F. FBX
tmpc = bpy.data.collections.new('_fbx'); bpy.context.scene.collection.children.link(tmpc)


def export(path, **extra):
    t = bpy.data.objects.new(ASSET, o.data); tmpc.objects.link(t)
    for x in bpy.context.view_layer.objects:
        x.select_set(False)
    t.select_set(True); bpy.context.view_layer.objects.active = t
    old = o.name; o.name = ASSET + '_src'; t.name = ASSET
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y',
                             use_mesh_modifiers=True, mesh_smooth_type='OFF', use_triangles=True, use_tspace=True, add_leaf_bones=False,
                             path_mode='RELATIVE', embed_textures=False, bake_anim=False, use_custom_props=False, **extra)
    bpy.data.objects.remove(t); o.name = old


FB = f'{V}/{ASSET}_intended.fbx'
export(FB, colors_type='NONE')                                    # EXACT settings of 05_export.py

from io_scene_fbx import parse_fbx


def inspect_fbx(path):
    root, ver = parse_fbx.parse(path)
    d = dict(bytes=os.path.getsize(path), has_LayerElementColor=False, geometries=[], materials=[], user_properties=[])
    objs = [e for e in root.elems if e.id == b'Objects'][0]
    for e in objs.elems:
        if e.id == b'Geometry':
            d['has_LayerElementColor'] |= any(c.id == b'LayerElementColor' for c in e.elems)
            pi = [c for c in e.elems if c.id == b'PolygonVertexIndex'][0].props[0]
            d['geometries'].append(dict(polys=int(sum(1 for i in pi if i < 0)), layer_elements=sorted({c.id.decode() for c in e.elems if c.id.startswith(b'LayerElement')})))
        elif e.id == b'Material':
            d['materials'].append(e.props[1].decode().split('\x00')[0])
        elif e.id == b'Model':
            for ch in e.elems:
                if ch.id == b'Properties70':
                    d['user_properties'] += [p.props[0].decode() for p in ch.elems if p.id == b'P' and len(p.props) > 3 and 'U' in str(p.props[3])]
    return d


rep['F_fbx_intended'] = inspect_fbx(FB)
rep['F_fbx_intended']['zone_attribute_in_fbx'] = ('zone_id' in open(FB, 'rb').read().decode('latin1'))
print('F fbx intended', rep['F_fbx_intended'])

# production FBX (read-only) for the same part
def prod_info(path, part):
    root, ver = parse_fbx.parse(path)
    objs = [e for e in root.elems if e.id == b'Objects'][0]
    geoms = [e for e in objs.elems if e.id == b'Geometry']
    return len(geoms), [m.props[1].decode().split('\x00')[0] for m in objs.elems if m.id == b'Material']


# ------------------------------------------------------------------ G. opt-in: zone as FBX vertex colour, round-trip
zc = o.data.attributes.new('zone_rgb', 'FLOAT_COLOR', 'CORNER')
ls = np.empty(len(o.data.polygons), dtype=np.int32); o.data.polygons.foreach_get('loop_start', ls)
col = np.zeros((len(o.data.loops), 4), dtype=np.float32); col[:, 3] = 1.0
for k in range(3):
    col[ls + k, 0] = zones4 / 5.0
zc.data.foreach_set('color', col.ravel())
FZ = f'{V}/{ASSET}_optin_zonecolor.fbx'
export(FZ, colors_type='LINEAR')
rep['G_fbx_optin_zone_colour'] = inspect_fbx(FZ)
o.data.attributes.remove(zc)
h5, _ = zhash(o); assert h5 == h0

# ------------------------------------------------------------------ H. round-trip imports in a scratch scene
def roundtrip(path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=path)
    me = [x for x in bpy.data.objects if x.type == 'MESH']
    r = []
    for x in me:
        wb = np.array([list(x.matrix_world @ __import__('mathutils').Vector(c)) for c in x.bound_box])
        dims = (wb.max(0) - wb.min(0)).round(3).tolist()
        d = dict(name=x.name, tris=sum(len(p.vertices) - 2 for p in x.data.polygons), world_dims=dims, zmin=round(float(wb[:, 2].min()), 3),
                 materials=[m.name for m in x.data.materials if m], attributes=sorted(a.name for a in x.data.attributes if not a.name.startswith('.')))
        ca = [a for a in x.data.color_attributes]
        if ca:
            a = ca[0]; n = len(x.data.loops)
            buf = np.empty(n * 4, dtype=np.float32); a.data.foreach_get('color', buf); buf = buf.reshape(-1, 4)
            ls_ = np.empty(len(x.data.polygons), dtype=np.int32); x.data.polygons.foreach_get('loop_start', ls_)
            d['colour_attr'] = a.name
            d['_decoded_zone_per_face'] = np.rint(buf[ls_, 0] * 5.0).astype(int)
        r.append(d)
    return r


rt_intended = roundtrip(FB)
rt_color = roundtrip(FZ)
rep['H_roundtrip_intended'] = [{k: v for k, v in d.items() if not k.startswith('_')} for d in rt_intended]
dec = rt_color[0].get('_decoded_zone_per_face')
if dec is not None:
    # importer may reorder faces; compare as zone histograms and (faces count) rather than per-index
    hist_src = {int(k): int(v) for k, v in zip(*np.unique(zones4, return_counts=True))}
    hist_rt = {int(k): int(v) for k, v in zip(*np.unique(dec, return_counts=True))}
    rep['H_roundtrip_optin_colour'] = dict(colour_attr=rt_color[0].get('colour_attr'), zone_hist_source=hist_src, zone_hist_roundtrip=hist_rt,
                                           histograms_equal=hist_src == hist_rt, faces=int(len(dec)))
else:
    rep['H_roundtrip_optin_colour'] = dict(colour_attr=None, note='no colour attribute after import')
# production comparison (read-only parse + import)
prod_rt = roundtrip(PROD_FBX)
pm = [d for d in prod_rt if d['name'].startswith(ASSET)]
rep['H_vs_production_fbx'] = dict(production_file=PROD_FBX, production_part=({k: v for k, v in pm[0].items() if not k.startswith('_')} if pm else None),
                                  gate1=rep['H_roundtrip_intended'][0] if rep['H_roundtrip_intended'] else None)
json.dump(rep, open(f'{EV}/01_verify_{ASSET.replace("ENV_Temple_", "")}.json', 'w'), indent=1, default=str)
print('VERIFY_DONE', ASSET)

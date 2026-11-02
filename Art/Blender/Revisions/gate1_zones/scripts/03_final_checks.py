"""GATE-1 final checks (read-only on production; writes under gate1_zones/ only):
 T. texture comparison: gate1 re-bake (zones rebuilt from zone_id) vs the shipped Staging textures, per map
 X. FBX export of the baked result with the EXACT 05_export.py settings -> bake_out/Models, file-level + round trip vs production FBX
 R. full-kit reopen check of the migrated working copy in a fresh process
"""
import sys, os, json, hashlib, math
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
from mathutils import Vector
import kitlib as K

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/gate1_zones'
PROD_TEX = ROOT + '/Art/Exports/Environment/Staging/Textures'
PROD_FBX = ROOT + '/Art/Exports/Environment/Staging/Models/ENV_Temple_Brazier_A.fbx'
A = 'ENV_Temple_Brazier_A'
rep = {}


def load(path):
    im = bpy.data.images.load(path, check_existing=False); w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32); im.pixels.foreach_get(a); bpy.data.images.remove(im); return a.reshape(h, w, 4)


# ---------------- T
T = {}
for k in ('BaseColor', 'Normal', 'Mask', 'Emission'):
    p, g = load(f'{PROD_TEX}/{A}_{k}.png'), load(f'{G}/bake_out/Textures/{A}_{k}.png')
    d = np.abs(p - g)
    T[k] = dict(shape=list(p.shape), mean_abs_diff=round(float(d[..., :3].mean()), 5), p99_abs_diff=round(float(np.percentile(d[..., :3], 99)), 4),
                max_abs_diff=round(float(d.max()), 4), prod_mean=[round(float(x), 4) for x in p[..., :3].reshape(-1, 3).mean(0)],
                gate1_mean=[round(float(x), 4) for x in g[..., :3].reshape(-1, 3).mean(0)])
    if k == 'Mask':
        T[k]['alpha_mean_abs_diff'] = round(float(d[..., 3].mean()), 5)
rep['T_texture_compare_vs_shipped'] = T
print('T', json.dumps(T))

# ---------------- X
bpy.ops.wm.open_mainfile(filepath=G + '/bake_out/TempleEnvironmentKit_gate1_bake_test.blend')
o = bpy.data.objects[A]
mdl = G + '/bake_out/Models'; os.makedirs(mdl, exist_ok=True)
path = f'{mdl}/{A}.fbx'
tmpc = bpy.data.collections.new('_x'); bpy.context.scene.collection.children.link(tmpc)
t = bpy.data.objects.new(A, o.data); tmpc.objects.link(t)
o.name = A + '_src'; t.name = A
for x in bpy.context.view_layer.objects:
    x.select_set(False)
t.select_set(True); bpy.context.view_layer.objects.active = t
bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                         apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                         mesh_smooth_type='OFF', use_triangles=True, use_tspace=True, colors_type='NONE', add_leaf_bones=False,
                         path_mode='RELATIVE', embed_textures=False, bake_anim=False, use_custom_props=False)
from io_scene_fbx import parse_fbx


def inspect(pth, base_dir):
    root, ver = parse_fbx.parse(pth)
    objs = [e for e in root.elems if e.id == b'Objects'][0]
    d = dict(bytes=os.path.getsize(pth), fbx_version=ver, textures=[], materials=[])
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
            d['textures'].append((os.path.basename(rel), os.path.exists(os.path.normpath(os.path.join(base_dir, rel)))))
        elif e.id == b'Material':
            d['materials'].append(e.props[1].decode().split('\x00')[0])
        elif e.id == b'Model':
            ps = {p.props[0].decode(): list(p.props[4:]) for ch in e.elems if ch.id == b'Properties70' for p in ch.elems if p.id == b'P'}
            d['model_transform'] = {k: ps.get(k) for k in ('Lcl Translation', 'Lcl Rotation', 'Lcl Scaling')}
        elif e.id == b'Geometry':
            vs = np.array([c for c in e.elems if c.id == b'Vertices'][0].props[0]).reshape(-1, 3)
            d['vertex_min'] = [round(float(x), 3) for x in vs.min(0)]; d['vertex_max'] = [round(float(x), 3) for x in vs.max(0)]
            d['polys'] = int(sum(1 for i in [c for c in e.elems if c.id == b'PolygonVertexIndex'][0].props[0] if i < 0))
    return d


rep['X_fbx_gate1'] = inspect(path, mdl)
rep['X_fbx_production'] = inspect(PROD_FBX, os.path.dirname(PROD_FBX))
rep['X_identical_geometry_extents'] = (rep['X_fbx_gate1']['vertex_min'] == rep['X_fbx_production']['vertex_min'] and rep['X_fbx_gate1']['vertex_max'] == rep['X_fbx_production']['vertex_max']
                                       and rep['X_fbx_gate1']['polys'] == rep['X_fbx_production']['polys'])
rep['X_zone_in_fbx_bytes'] = ('zone_id' in open(path, 'rb').read().decode('latin1'))
print('X', json.dumps({k: rep[k] for k in ('X_fbx_gate1', 'X_fbx_production', 'X_identical_geometry_extents', 'X_zone_in_fbx_bytes')}, default=str)[:1800])

# ---------------- R
bpy.ops.wm.open_mainfile(filepath=G + '/TempleEnvironmentKit_gate1_zones.blend')
R = {}
for ob in sorted([x for x in bpy.data.objects if x.name.startswith('ENV_Temple_') and x.type == 'MESH'], key=lambda x: x.name):
    zc = K.zone_counts(ob)
    mi = np.empty(len(ob.data.polygons), dtype=np.int32); ob.data.polygons.foreach_get('material_index', mi)
    R[ob.name.replace('ENV_Temple_', '')] = dict(has_zone_id=zc is not None, zone_counts={K.ZONE_NAMES[k]: v for k, v in (zc or {}).items()}, faces=len(ob.data.polygons),
                                                  zone_faces_sum_ok=(sum((zc or {}).values()) == len(ob.data.polygons)), slots=[m.name for m in ob.data.materials])
rep['R_fullkit_reopen'] = R
rep['R_all_have_zone_id'] = all(v['has_zone_id'] and v['zone_faces_sum_ok'] for v in R.values())
rep['R_scene_legend'] = bpy.context.scene.get('zone_legend')
print('R all_have_zone_id', rep['R_all_have_zone_id'], 'parts', len(R))
json.dump(rep, open(G + '/evidence/04_final_checks.json', 'w'), indent=1, default=str)
print('FINAL_DONE')

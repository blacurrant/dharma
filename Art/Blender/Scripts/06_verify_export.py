"""Stage 6: verify staged FBX files (file-level + round-trip).
Run: Blender -b --factory-startup --python Art/Blender/Scripts/06_verify_export.py
File-level (io_scene_fbx.parse_fbx): GlobalSettings axes/unit scale, Model transforms, raw vertex extents, texture refs.
Round-trip: re-import in a scratch scene and compare dimensions / bbox pivot / tri count / materials with the kit source.
"""
import sys, os, json, glob, math
import bpy
import numpy as np
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite'
STG = ROOT + '/Art/Exports/Environment/Staging'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
OUT = ROOT + '/Art/Blender/Scripts/_build/export_verification.json'

# source dims from the kit file (read-only), measured the same way (box in object space, object at lineup position => use local box)
bpy.ops.wm.open_mainfile(filepath=BLEND)
src = {}
for o in bpy.data.objects:
    if o.name.startswith('ENV_Temple_') and o.type == 'MESH':
        bb = np.array([list(v) for v in o.bound_box])
        dims = bb.max(0) - bb.min(0)
        src[o.name] = dict(dims=[round(float(x), 3) for x in dims], zmin=round(float(bb[:, 2].min()), 3),
                           cx=round(float((bb[:, 0].min() + bb[:, 0].max()) / 2), 3), cy=round(float((bb[:, 1].min() + bb[:, 1].max()) / 2), 3),
                           tris=sum(len(p.vertices) - 2 for p in o.data.polygons))

from io_scene_fbx import parse_fbx


def props70(elem):
    out = {}
    for ch in elem.elems:
        if ch.id == b'Properties70':
            for p in ch.elems:
                if p.id == b'P':
                    name = p.props[0].decode() if isinstance(p.props[0], bytes) else p.props[0]
                    out[name] = p.props[4:]
    return out


report = {}
for fbx in sorted(glob.glob(STG + '/Models/*.fbx')):
    name = os.path.basename(fbx)[:-4]
    root, ver = parse_fbx.parse(fbx)
    d = dict(file=os.path.relpath(fbx, ROOT), bytes=os.path.getsize(fbx), fbx_version=ver)
    for e in root.elems:
        if e.id == b'GlobalSettings':
            p = props70(e)
            d['global'] = {k: (p[k][0] if k in p else None) for k in ('UpAxis', 'UpAxisSign', 'FrontAxis', 'FrontAxisSign', 'CoordAxis', 'CoordAxisSign', 'UnitScaleFactor', 'OriginalUnitScaleFactor')}
    models, geoms, mats, texs = [], [], [], []
    objs_e = [e for e in root.elems if e.id == b'Objects'][0]
    for e in objs_e.elems:
        if e.id == b'Model':
            p = props70(e)
            models.append(dict(name=e.props[1].decode().split('\x00')[0], type=e.props[2].decode(),
                               loc=list(p.get('Lcl Translation', [0, 0, 0, 0, 0, 0])[-3:]) if 'Lcl Translation' in p else [0, 0, 0],
                               rot=list(p.get('Lcl Rotation', [0, 0, 0])[-3:]) if 'Lcl Rotation' in p else [0, 0, 0],
                               scl=list(p.get('Lcl Scaling', [1, 1, 1])[-3:]) if 'Lcl Scaling' in p else [1, 1, 1]))
        elif e.id == b'Geometry':
            vs = [c for c in e.elems if c.id == b'Vertices'][0].props[0]
            a = np.array(vs, dtype=np.float64).reshape(-1, 3)
            pi = [c for c in e.elems if c.id == b'PolygonVertexIndex'][0].props[0]
            geoms.append(dict(verts=len(a), min=[round(float(x), 3) for x in a.min(0)], max=[round(float(x), 3) for x in a.max(0)],
                              polys=int(sum(1 for i in pi if i < 0))))
        elif e.id == b'Material':
            mats.append(e.props[1].decode().split('\x00')[0])
        elif e.id == b'Texture':
            rel = [c for c in e.elems if c.id == b'RelativeFilename']
            texs.append(rel[0].props[0].decode() if rel else '?')
    d['models'] = models; d['geometries'] = geoms; d['materials'] = mats; d['textures'] = texs
    d['textures_exist'] = [os.path.exists(os.path.normpath(os.path.join(STG, 'Models', t))) for t in texs]
    # round trip
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    rt = {}
    for o in bpy.data.objects:
        if o.type == 'MESH':
            wb = np.array([list(o.matrix_world @ Vector(c)) for c in o.bound_box])      # world-space box (importer adds +90 deg X)
            dims = wb.max(0) - wb.min(0)
            rt[o.name] = dict(dims=[round(float(x), 3) for x in dims], zmin=round(float(wb[:, 2].min()), 3),
                              cx=round(float((wb[:, 0].min() + wb[:, 0].max()) / 2), 3), cy=round(float((wb[:, 1].min() + wb[:, 1].max()) / 2), 3),
                              tris=sum(len(p.vertices) - 2 for p in o.data.polygons), materials=[m.name for m in o.data.materials if m],
                              has_uv=len(o.data.uv_layers) > 0, importer_rot_deg=[round(math.degrees(x), 2) for x in o.rotation_euler], scale=[round(x, 3) for x in o.scale])
    d['roundtrip'] = rt
    cmp = {}
    for pn, r in rt.items():
        s = src.get(pn)
        if not s:
            continue
        ok_dims = all(abs(a - b) < 0.02 for a, b in zip(r['dims'], s['dims']))
        cmp[pn] = dict(dims_match=ok_dims, zmin_match=abs(r['zmin'] - s['zmin']) < 0.01, pivot_xy_match=abs(r['cx'] - s['cx']) < 0.02 and abs(r['cy'] - s['cy']) < 0.02,
                       tris_src=s['tris'], tris_exported=r['tris'])
    d['compare'] = cmp
    report[name] = d
    print('VERIFIED', name, 'global', d.get('global', {}).get('UpAxis'), d.get('global', {}).get('UnitScaleFactor'), '|', {k: (v['dims_match'], v['zmin_match'], v['pivot_xy_match']) for k, v in cmp.items()}, flush=True)

json.dump(report, open(OUT, 'w'), indent=1, default=str)
print('VERIFY_DONE', len(report))

"""Courtyard before/after in the WORKING COPY (materials patched in memory only; the .blend is NOT saved).
Applies the exact world-space overlay stack from vf_nodes.py to the real kit materials, renders gameplay-camera and plan views
(EEVEE, Standard view transform - same settings as Art/Blender/Scripts/04_render.py) and measures luminance variation.
Blender -b --factory-startup --python scripts/13_courtyard_before_after.py
"""
import sys, os, math, json, random
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff/scripts'
sys.path.insert(0, HERE)
import bpy, numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
import vf_nodes as V

VF = V.VF
OUT = VF + '/renders'
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=VF + '/TempleEnvironmentKit_vf_working.blend')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 48
    sc.eevee.use_raytracing = True
except Exception as e:
    print('eevee', e)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
O = bpy.data.objects
Uv = lambda x, y, z: Vector((x, z, y))
res = {}

STRONG = os.environ.get('VF_STRONG') == '1'
SUF = '_strongmacro' if STRONG else ''
KV, KT = (1.0, 1.0) if STRONG else (0.75, 0.60)
FLOOR_STACK = [('VF_Floor_MacroValue_2048', KV, 'floor'), ('VF_Floor_MacroTint_1024', KT, 'floor'), ('VF_Floor_Cracks_2048', 0.75, 'floor'),
               ('VF_Floor_Wear_1024', 0.50, 'floor'), ('VF_Floor_ChippedEdges_1024', 0.85, 'floor'), ('VF_Weather_MossFloorJoints_1024', 0.80, 'floor')]
DAIS_STACK = [('VF_Floor_MacroValue_2048', KV, 'floor'), ('VF_Floor_MacroTint_1024', KT, 'floor'), ('VF_Floor_Cracks_2048', 0.75, 'floor'), ('VF_Floor_Wear_1024', 0.50, 'floor')]
WALL_STACK = [('VF_Wall_RainStreaks_1024', 0.65, 'wall'), ('VF_Weather_Salt_1024', 0.55, 'wall'), ('VF_Weather_MossWallBase_1024', 0.80, 'wall')]


def patch_material(m, stack):
    nt = m.node_tree
    bs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'][0]
    lk = [l for l in nt.links if l.to_node == bs and l.to_socket.name == 'Base Color'][0]
    src = lk.from_socket
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    out = V.build(nt, src, geo.outputs['Position'], geo.outputs['Normal'], stack)
    nt.links.new(out, bs.inputs['Base Color'])


def apply_stack():
    fm = sorted({m for o in O if o.users_collection and o.users_collection[0].name == 'LAY_Floor' for m in o.data.materials}, key=lambda m: m.name)
    wm = sorted({m for o in O if o.users_collection and o.users_collection[0].name == 'LAY_Walls' for m in o.data.materials}, key=lambda m: m.name)
    for m in fm:
        patch_material(m, FLOOR_STACK)
    for m in wm:
        patch_material(m, WALL_STACK)
    dm = sorted({m for o in O if o.name.startswith('LAY_Platform') or o.name.startswith('LAY_Stairs') for m in o.data.materials}, key=lambda m: m.name)
    for m in dm:
        patch_material(m, DAIS_STACK)
    print('PATCHED dais mats', [m.name for m in dm])
    print('PATCHED floor mats', [m.name for m in fm], 'wall mats', [m.name for m in wm], flush=True)
    return fm, wm


def decals():
    """soot smudges at the 4 braziers + wall plumes where a wall is within 2.2 m"""
    import json as js
    pl = js.load(open('/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/TempleCourtyard_Placement.json'))['instances']
    br = [i for i in pl if i['part'] == 'ENV_Temple_Brazier_A']
    rnd = random.Random(7)
    made = []
    for k, b in enumerate(br):
        x, z, y = b['unity_x'], b['unity_z'], b['unity_y']
        for kind in ('ring',) + (('plume',) if abs(z) > 17.2 or abs(x) > 17.2 else ()):
            me = bpy.data.meshes.new('d_' + kind)
            if kind == 'ring':
                h = 1.6; me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
                name = 'VF_Weather_SootFloorRing_1024'
            else:
                me.from_pydata([(-0.75, 0, 1.3), (0.75, 0, 1.3), (0.75, 0, 4.3), (-0.75, 0, 4.3)], [], [(0, 1, 2, 3)])
                name = 'VF_Weather_SootWallPlume_512x1024'
            uv = me.uv_layers.new(name='UV')
            for l, c in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                uv.data[l.index].uv = c
            m = bpy.data.materials.new('mat_' + kind + str(k)); m.use_nodes = True; nt = m.node_tree
            bs = nt.nodes['Principled BSDF']; bs.inputs['Roughness'].default_value = 1.0
            im = bpy.data.images.get(name + '.png') or bpy.data.images.load(V.TEX + name + '.png'); im.colorspace_settings.name = 'sRGB'; im.alpha_mode = 'STRAIGHT'
            tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = im; tx.extension = 'CLIP'
            mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = V.SPEC[name][3]
            nt.links.new(tx.outputs['Color'], bs.inputs['Base Color']); nt.links.new(tx.outputs['Alpha'], mul.inputs[0]); nt.links.new(mul.outputs[0], bs.inputs['Alpha'])
            try:
                m.surface_render_method = 'BLENDED'
            except Exception:
                pass
            me.materials.append(m)
            o = bpy.data.objects.new(f'VF_decal_{kind}_{k}', me); sc.collection.objects.link(o)
            if kind == 'ring':
                o.location = (x, z, y + 0.035); o.rotation_euler = (0, 0, math.radians(rnd.uniform(0, 360)))
            else:   # on the nearest wall, facing into the courtyard; plane normal is -Y at rotation 0
                if abs(z) >= abs(x):
                    wy = 19.46 if z > 0 else -19.46
                    o.location = (x, wy, 0); o.rotation_euler = (0, 0, 0 if z > 0 else math.pi)
                else:
                    wx = 19.46 if x > 0 else -19.46
                    o.location = (wx, z, 0); o.rotation_euler = (0, 0, -math.pi / 2 if x > 0 else math.pi / 2)
            made.append(o.name)
    print('DECALS', made, flush=True)
    return made


def set_proxies(pp, ep, show=True, tele=True):
    pl_, en = O['PROXY_Player'], O['PROXY_Enemy']
    pl_.location = Uv(pp[0], 0, pp[1]); en.location = Uv(ep[0], 0, ep[1])
    for o in [pl_, en] + list(en.children):
        o.hide_render = not show
    for n in ('PROXY_Telegraph_Edge', 'PROXY_Telegraph_Fill'):
        O[n].hide_render = not tele


def render(name, cam, size=None):
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = size or ((int(cam['res'][0]), int(cam['res'][1])) if 'res' in cam.keys() else (1920, 1080))
    keep_names = ('VF_courtyard_plan_after', 'VF_courtyard_gameplay_after')
    if name.startswith('_tmp') or (STRONG and name not in keep_names):
        sc.render.filepath = os.path.join(os.environ.get('TMPDIR', '/tmp'), f'vf_strong_{name}.png')      # throwaway: scratch dir, not the handoff folder
    else:
        sc.render.filepath = f'{OUT}/{name}{SUF}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', name, sc.render.resolution_x, sc.render.resolution_y, flush=True)
    return sc.render.filepath


def load_Y(path):
    im = bpy.data.images.load(path, check_existing=False); im.colorspace_settings.name = 'sRGB'
    w, h = im.size; a = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(a); a = a.reshape(h, w, 4)[..., :3]; bpy.data.images.remove(im)
    # pixels() of an sRGB image are linear
    return a, 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def stats(Y, mask):
    v = Y[mask]
    return dict(px=int(mask.sum()), mean=float(v.mean()), std=float(v.std()), p5=float(np.percentile(v, 5)), p95=float(np.percentile(v, 95)), cv=float(v.std() / max(v.mean(), 1e-9)),
                p5_p95_ratio=float(np.percentile(v, 95) / max(np.percentile(v, 5), 1e-9)))


plan = O['CAM_Plan_TopDown']; gc = O['CAM_Gameplay_Center']
cl = bpy.data.cameras.new('vf_close'); cl.type = 'ORTHO'; cl.ortho_scale = 6.0; cl.clip_end = 400
clo = bpy.data.objects.new('vf_close', cl); sc.collection.objects.link(clo); clo.rotation_euler = gc.rotation_euler
def closeup(name, tx, ty, tz, scale=6.0):
    cl.ortho_scale = scale
    clo.location = (tx + 12.0 * 1.6, ty - 12.0 * 1.6, tz + 18.0 * 1.6)
    return render(name, clo, (1600, 900))
CLOSE = [('closeup_wallbrazier', 9.4, 17.6, 1.2, 7.0), ('closeup_dais_brazier', -9.7, 14.65, 1.0, 7.0), ('closeup_wall_left', -19.0, 1.0, 1.2, 8.0)]
print('PLANCAM', plan.location[:], plan.data.type, plan.data.ortho_scale, dict(plan.items()) if hasattr(plan, 'items') else '')
# ---- BEFORE
set_proxies((0, 0), (0, 8), show=False, tele=False)
fb = render('VF_courtyard_plan_before', plan, (1600, 1600))
fgb = render('VF_courtyard_gameplay_before', gc)                                      # clean gameplay view, no proxies
set_proxies((0, 0), (0, 8), show=True, tele=True)
fgbt = render('VF_courtyard_gameplay_before_telegraph', gc)
set_proxies((0, 0), (0, 8), show=True, tele=False)
fgbn = render('_tmp_gameplay_before_notele', gc)
set_proxies((0, 0), (0, 8), show=False, tele=False)
for n_, a_, b_, c_, d_ in CLOSE:
    closeup('VF_' + n_ + '_before', a_, b_, c_, d_)
# ---- AFTER
fm, wm = apply_stack()
dec = decals()
set_proxies((0, 0), (0, 8), show=False, tele=False)
fa = render('VF_courtyard_plan_after', plan, (1600, 1600))
fga = render('VF_courtyard_gameplay_after', gc)
set_proxies((0, 0), (0, 8), show=True, tele=True)
fgat = render('VF_courtyard_gameplay_after_telegraph', gc)
set_proxies((0, 0), (0, 8), show=True, tele=False)
fgan = render('_tmp_gameplay_after_notele', gc)
# the dais view (altar + braziers) - where soot/moss are placed
for nme in ('PROXY_Player', 'PROXY_Enemy'):
    pass
set_proxies((-8.0, 8.0), (-9.5, 9.5), show=False, tele=False)
dc = O['CAM_Gameplay_Dais']
bpy.ops.object.select_all(action='DESELECT')
fda = render('VF_courtyard_dais_after', dc)
for n_, a_, b_, c_, d_ in CLOSE:
    closeup('VF_' + n_ + '_after', a_, b_, c_, d_)
for m in list(bpy.data.materials):
    pass

# ---- measurements (plan view: floor luminance variation vs radius)
sc.camera = plan
sc.render.resolution_x = sc.render.resolution_y = 1600
H = W = 1600
xs, ys = np.meshgrid(np.arange(W), np.arange(H))
# pixel -> world (plan is ortho top-down): build by projecting a grid of world points
def px_of(x, y):
    c = world_to_camera_view(sc, plan, Vector((x, y, 0.0)))
    return c.x * W, (1 - c.y) * H
p00, p10, p01 = px_of(0, 0), px_of(1, 0), px_of(0, 1)
a_x = np.array([p10[0] - p00[0], p10[1] - p00[1]]); a_y = np.array([p01[0] - p00[0], p01[1] - p00[1]])
M = np.array([[a_x[0], a_y[0]], [a_x[1], a_y[1]]]); Minv = np.linalg.inv(M)
d = np.stack([xs - p00[0], ys - p00[1]], -1)
wxy = d @ Minv.T
R = np.hypot(wxy[..., 0], wxy[..., 1])
res['plan_px_per_m'] = float(np.hypot(*a_x))
_, Yb = load_Y(fb); _, Ya = load_Y(fa)
inner = R < 9.5; ring = (R > 12.5) & (R < 17.0)
# only floor: exclude pixels near props/walls: restrict to |x|,|y| < 17 and exclude altar/dais quadrant (x<-9,y>9)
floor_ok = (np.abs(wxy[..., 0]) < 17) & (np.abs(wxy[..., 1]) < 17) & ~((wxy[..., 0] < -9) & (wxy[..., 1] > 9))
res['plan_floor_luminance'] = {}
for nm, Y in (('before', Yb), ('after', Ya)):
    res['plan_floor_luminance'][nm] = dict(inside_r_lt_9_5=stats(Y, inner & floor_ok), outside_12_5_to_17=stats(Y, ring & floor_ok))
# tile-to-tile repetition metric: mean luminance of each 2 m tile (centres on odd metres) -> spread of tile means
def tile_means(Y):
    out = {}
    for cx in range(-17, 18, 2):
        for cy in range(-17, 18, 2):
            if (cx < -9 and cy > 9):
                continue
            m = (np.abs(wxy[..., 0] - cx) < 0.9) & (np.abs(wxy[..., 1] - cy) < 0.9)
            out[(cx, cy)] = float(Y[m].mean()) if m.any() else None
    return {k: v for k, v in out.items() if v is not None}
for nm, Y in (('before', Yb), ('after', Ya)):
    t = tile_means(Y); v = np.array(list(t.values())); rr = np.array([math.hypot(*k) for k in t])
    res['plan_floor_luminance'][nm]['tile_mean_spread'] = dict(n_tiles=len(v), cv_all=float(v.std() / v.mean()), cv_inside_r10=float(v[rr < 10].std() / v[rr < 10].mean()), cv_outside_r12=float(v[rr > 12].std() / v[rr > 12].mean()),
                                                              p5_p95_ratio_all=float(np.percentile(v, 95) / np.percentile(v, 5)))
# ---- telegraph readability (gameplay camera, identical pixels)
resg = {}
for tag, f_off, f_on in (('before', fgbn, fgbt), ('after', fgan, fgat)):
    _, Yoff = load_Y(f_off); _, Yon = load_Y(f_on)
    diff = Yon - Yoff
    mask = diff > 0.004
    resg[tag] = dict(telegraph_px=int(mask.sum()), mean_lift_abs=float(diff[mask].mean()) if mask.any() else None,
                     mean_Y_without=float(Yoff[mask].mean()), lift_rel=float(diff[mask].mean() / max(Yoff[mask].mean(), 1e-9)) if mask.any() else None,
                     floor_Y_std_under_footprint_without_telegraph=float(Yoff[mask].std()), floor_Y_p5_p95_under_footprint=[float(np.percentile(Yoff[mask], 5)), float(np.percentile(Yoff[mask], 95))])
    if tag == 'before':
        keep = mask
resg['same_mask_after'] = None
_, Yoff_a = load_Y(fgan); _, Yon_a = load_Y(fgat); _, Yoff_b = load_Y(fgbn)
resg['same_mask_after'] = dict(telegraph_px=int(keep.sum()), floor_Y_std_under_before_footprint_after=float(Yoff_a[keep].std()), floor_Y_std_under_before_footprint_before=float(Yoff_b[keep].std()),
                                lift_after_abs=float((Yon_a - Yoff_a)[keep].mean()), mean_Y_without_after=float(Yoff_a[keep].mean()))
res['gameplay_telegraph'] = resg
json.dump(res, open(VF + f'/evidence/13_courtyard{SUF}.json', 'w'), indent=1)
print('RES', json.dumps(res)[:3000])
print('COURTYARD_DONE')

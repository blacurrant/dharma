"""Stage 4: review renders from the saved TempleEnvironmentKit.blend (background EEVEE).
Run: Blender -b --factory-startup --python Art/Blender/Scripts/04_render.py [-- --only gameplay_center,overview ...]
Writes Art/Blender/Renders/*.png (+ *_grey.png for gameplay views). Does not modify the .blend.
Gameplay views reproduce the PrototypeArena camera: ortho size 11, offset (12,18,-12).
"""
import sys, os, math, json
import bpy
import numpy as np
from mathutils import Vector, Matrix

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
OUT = ROOT + '/Art/Blender/Renders'
os.makedirs(OUT, exist_ok=True)
ONLY = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
VT = sys.argv[sys.argv.index('--vt') + 1] if '--vt' in sys.argv else 'Standard'
SAMPLES = int(sys.argv[sys.argv.index('--samples') + 1]) if '--samples' in sys.argv else 64
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = SAMPLES
except Exception:
    pass
for attr, val in (('use_raytracing', True),):
    try:
        setattr(sc.eevee, attr, val)
    except Exception as ex:
        print('eevee attr', attr, ex)
sc.view_settings.view_transform = VT
try:
    sc.view_settings.look = 'None'
except Exception:
    pass
sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'
sc.render.film_transparent = False

U = lambda x, y, z: Vector((x, z, y))
objs = bpy.data.objects
player, enemy = objs['PROXY_Player'], objs['PROXY_Enemy']


def set_proxies(pp, ep, show=True):
    player.location = U(pp[0], 0, pp[1]); enemy.location = U(ep[0], 0, ep[1])
    d = Vector((pp[0] - ep[0], pp[1] - ep[1]))
    enemy.rotation_euler = (0, 0, -math.atan2(d.x, d.y))
    player.rotation_euler = (0, 0, -math.atan2(-d.x, -d.y))
    for o in [player, enemy] + [c for c in enemy.children]:
        o.hide_render = not show


def to_grey(path):
    img = bpy.data.images.load(path, check_existing=False)
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4)
    lin = np.where(a[..., :3] <= 0.04045, a[..., :3] / 12.92, ((a[..., :3] + 0.055) / 1.055) ** 2.4)
    lum = 0.2126 * lin[..., 0] + 0.7152 * lin[..., 1] + 0.0722 * lin[..., 2]
    g = np.where(lum <= 0.0031308, lum * 12.92, 1.055 * lum ** (1 / 2.4) - 0.055)
    out = np.dstack([g, g, g, np.ones_like(g)]).astype(np.float32)
    gi = bpy.data.images.new('grey_tmp', w, h, alpha=False); gi.colorspace_settings.name = 'sRGB'
    gi.pixels.foreach_set(out.ravel()); gi.filepath_raw = path.replace('.png', '_grey.png'); gi.file_format = 'PNG'; gi.save()
    bpy.data.images.remove(gi); bpy.data.images.remove(img)


def render(name, cam, grey=False):
    if ONLY and name not in ONLY:
        return
    sc.camera = cam
    sc.render.resolution_x, sc.render.resolution_y = (int(cam['res'][0]), int(cam['res'][1])) if 'res' in cam.keys() else (1920, 1080)
    sc.render.filepath = f'{OUT}/{name}.png'
    bpy.ops.render.render(write_still=True)
    if grey:
        to_grey(sc.render.filepath)
    print('RENDERED', name, flush=True)


# ---- gameplay-camera views (courtyard; kit lineup hidden by distance)
set_proxies((0, 0), (0, 8))
render('gameplay_center', objs['CAM_Gameplay_Center'], grey=True)
set_proxies((-8.0, 8.0), (-9.5, 9.5))
render('gameplay_dais', objs['CAM_Gameplay_Dais'], grey=True)
set_proxies((3.0, 9.0), (4.5, 12.0))
render('gameplay_arch', objs['CAM_Gameplay_Arch'], grey=True)
set_proxies((0, 0), (0, 8))
render('overview', objs['CAM_Overview'])

# ---- plan view with clear-zone ring (diagnostic)
if not ONLY or 'plan_clearzone' in ONLY:
    bm_ring = bpy.data.meshes.new('ring')
    import bmesh
    bm = bmesh.new(); n = 128
    vs = []
    for r in (9.92, 10.08):
        vs.append([bm.verts.new((r * math.cos(math.tau * i / n), r * math.sin(math.tau * i / n), 1.2)) for i in range(n)])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i]))
    bm.to_mesh(bm_ring); bm.free()
    ring = bpy.data.objects.new('CLEARZONE_RING', bm_ring); sc.collection.objects.link(ring)
    m = bpy.data.materials.new('ring_mat'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    o_ = nt.nodes.new('ShaderNodeOutputMaterial'); e_ = nt.nodes.new('ShaderNodeEmission'); e_.inputs['Color'].default_value = (1.0, 0.2, 0.9, 1); e_.inputs['Strength'].default_value = 3
    nt.links.new(e_.outputs[0], o_.inputs[0]); bm_ring.materials.append(m)
    set_proxies((0, 0), (0, 8), show=False)
    render('plan_clearzone', objs['CAM_Plan_TopDown'])
    bpy.data.objects.remove(ring)

# ---- kit close-ups (non-gameplay camera; labelled as such in the report)
if not ONLY or any(k.startswith('kit_row') for k in ONLY):
    set_proxies((0, 0), (0, 8), show=False)
    for o in bpy.data.objects:
        if o.name.startswith('LAY_') and o.type == 'MESH':
            o.hide_render = True
    kit = [o for o in bpy.data.objects if o.name.startswith('ENV_Temple_') and o.type == 'MESH']
    rows = {}
    for o in kit:
        rows.setdefault(round((o.location.y + 60) / -22), []).append(o)
    cd = bpy.data.cameras.new('closeup'); cd.type = 'ORTHO'; cd.clip_end = 400
    cam = bpy.data.objects.new('closeup', cd); sc.collection.objects.link(cam)
    cam['res'] = (1800, 900)
    names = {0: 'floors_borders', 1: 'stairs_platform_walls', 2: 'pillars', 3: 'altar_arch', 4: 'props'}
    for r, os_ in sorted(rows.items()):
        for o in kit:
            o.hide_render = o not in os_
        xs = [o.location.x - o.dimensions.x / 2 for o in os_] + [o.location.x + o.dimensions.x / 2 for o in os_]
        cx = (min(xs) + max(xs)) / 2; wd = max(xs) - min(xs); hmax = max(o.dimensions.z for o in os_)
        d = Vector((0.35, -1.0, 0.62)).normalized()
        cam.location = Vector((cx, os_[0].location.y, hmax * 0.45)) + d * 80
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        cd.ortho_scale = max(wd * 1.15, hmax * (3.2 if r == 2 else 3.7), 6)
        render(f'kit_row{r}_{names[r]}', cam)
print('RENDER_DONE')

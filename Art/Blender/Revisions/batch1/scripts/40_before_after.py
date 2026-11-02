"""Batch-1 BEFORE | AFTER renders from the gameplay camera (offset 12,18,-12 => Blender (12,-12,18); ortho size 9 => ortho_scale 32 for 16:9).
Works on the batch1 WORKING COPY (never saved): new parts are instanced from handoff/Batch1_Placement.json; PROXY_Player gives scale; telegraph/enemy hidden.
  Blender -b --factory-startup --python scripts/40_before_after.py -- walls | pylons | ruins | backdrops
Outputs renders/<tag>_{BEFORE,AFTER}.png (raw 1920x1080) ; sheets are composed afterwards by scripts/41_sheets.py (system PIL).
"""
import sys, os, json, math
import bpy
from mathutils import Vector

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch1'
OUT = G + '/renders'
os.makedirs(OUT, exist_ok=True)
GROUP = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.open_mainfile(filepath=G + '/TempleEnvironmentKit_batch1.blend')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 48; sc.eevee.use_raytracing = True
except Exception as e:
    print('eevee', e)
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'; sc.view_settings.exposure = 0.0
sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
O = bpy.data.objects
P = json.load(open(G + '/handoff/Batch1_Placement.json'))['instances']
cam_d = bpy.data.cameras.new('b1cam'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = 32.0; cam_d.clip_start = 0.1; cam_d.clip_end = 600.0
cam = bpy.data.objects.new('b1cam', cam_d); sc.collection.objects.link(cam); sc.camera = cam
OFFS = Vector((12.0, -12.0, 18.0))
look_dir = (-OFFS).normalized()
cam.rotation_euler = look_dir.to_track_quat('-Z', 'Y').to_euler()
made = []


def place(rows):
    for r in rows:
        mesh_obj = O.get(r['part'])
        if mesh_obj is None:
            print('MISSING mesh object', r['part']); continue
        o = bpy.data.objects.new(r['instance'], mesh_obj.data)
        o.location = (r['unity_x'], r['unity_z'], r['unity_y'])
        o.rotation_euler = (0, 0, math.radians(-r['yaw_front_to_plusZ']))
        sc.collection.objects.link(o); made.append(o)


def clear():
    for o in made:
        bpy.data.objects.remove(o, do_unlink=True)
    made.clear()


def proxies(t):
    pl, en = O['PROXY_Player'], O['PROXY_Enemy']
    pl.location = (t[0], t[1], 0.0); pl.hide_render = False
    for o in [en] + list(en.children):
        o.hide_render = True
    for n in ('PROXY_Telegraph_Edge', 'PROXY_Telegraph_Fill'):
        O[n].hide_render = True


def shoot(tag, t):
    cam.location = Vector(t) + OFFS * 4.0
    sc.render.filepath = f'{OUT}/{tag}.png'
    bpy.ops.render.render(write_still=True)
    print('RENDERED', tag, flush=True)


def sel(part=None, group_prefix=None, contains=None):
    out = []
    for r in P:
        if part and r['part'] != 'ENV_Temple_' + part:
            continue
        if group_prefix and not r['group'].startswith(group_prefix):
            continue
        if contains and contains not in r['instance']:
            continue
        out.append(r)
    return out


JOBS = {
    'walls': [('Wall_Tall_A', (-9.0, 17.0, 0.0), 'WallTall_A_north'), ('Wall_Tall_B', (-9.0, 17.0, 0.0), 'WallTall_B_north'),
              ('Wall_Tall_A', (-16.0, 3.0, 0.0), 'WallTall_A_west'), ('Wall_Tall_B', (-16.0, 3.0, 0.0), 'WallTall_B_west'), ('*walls', (-9.0, 17.0, 0.0), 'WallTall_ALL_north'), ('*walls', (-16.0, 3.0, 0.0), 'WallTall_ALL_west')],
    'pylons': [('Lantern_Pylon_A', (-10.0, 10.5, 0.0), 'Pylon_stairs'), ('Lantern_Pylon_A', (4.0, 15.0, 0.0), 'Pylon_arch'), ('Lantern_Pylon_A', (-15.0, -4.0, 0.0), 'Pylon_west')],
    'ruins': [('Ruin_Cluster_A', (-13.0, -8.0, 0.0), 'Ruin_A'), ('Ruin_Cluster_B', (-13.0, -8.0, 0.0), 'Ruin_B'), ('*ruins', (-13.0, -8.0, 0.0), 'Ruin_ALL')],
}
if GROUP in JOBS:
    for part, T, tag in JOBS[GROUP]:
        proxies(T)
        clear(); shoot(tag + '_BEFORE', T)
        rows = sel(group_prefix={'walls': 'BATCH1_Walls', 'pylons': 'BATCH1_Pylons', 'ruins': 'BATCH1_Ruins'}[GROUP]) if part.startswith('*') else sel(part=part)
        place(rows); shoot(tag + '_AFTER', T)
elif GROUP == 'backdrops':
    jobs = [('Backdrop_Mass_A', (-6.0, 17.0, 0.0), 'Backdrop_A_north'), ('Backdrop_Mass_B', (10.0, 17.0, 0.0), 'Backdrop_B_north'), ('Backdrop_Mass_C', (-17.0, -2.0, 0.0), 'Backdrop_C_west')]
    for part, T, tag in jobs:
        proxies(T)
        clear(); place(sel(group_prefix='BATCH1_Walls')); shoot(tag + '_BEFORE', T)      # BEFORE here = courtyard + tall bays, so the masses' own effect is isolated
        for suffix, key in (('AFTER_recommended', 'recommended_visible_band'), ('AFTER_directive28-55m', 'directive_28_55m')):
            clear(); place(sel(part=part, contains=key))
            # walls also present for context in the AFTER (tall bays), because the masses are meant to sit behind them
            place(sel(group_prefix='BATCH1_Walls'))
            shoot(f'{tag}_{suffix}', T)
bpy.data.objects.remove(cam, do_unlink=True)
print('BA_DONE', GROUP)

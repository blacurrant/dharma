"""Dev helper: clay (Workbench) renders of the kit lineup rows for geometry QA."""
import bpy, sys, math, os
from mathutils import Vector
ROOT = '/Users/landerstudio/MythicRoguelite'
OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else '/tmp'
bpy.ops.wm.open_mainfile(filepath=ROOT + '/Art/Blender/TempleEnvironmentKit.blend')
sc = bpy.context.scene
sc.render.engine = 'BLENDER_WORKBENCH'
sc.render.resolution_x, sc.render.resolution_y = 1800, 700
sh = sc.display.shading
sh.light = 'STUDIO'; sh.color_type = 'SINGLE'; sh.single_color = (0.62, 0.58, 0.5)
sh.show_cavity = True; sh.cavity_type = 'BOTH'; sh.show_shadows = True
sc.view_settings.view_transform = 'Standard'
sc.world = bpy.data.worlds.new('w'); sc.world.color = (0.12, 0.12, 0.13)
cam = bpy.data.objects.new('cam', bpy.data.cameras.new('cam')); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = 'ORTHO'
rows = {}
for o in bpy.data.objects:
    if o.name.startswith('ENV_Temple_'):
        rows.setdefault(round((o.location.y + 60) / -22), []).append(o)
for r, objs in sorted(rows.items()):
    xs = [o.location.x - o.dimensions.x / 2 for o in objs] + [o.location.x + o.dimensions.x / 2 for o in objs]
    ys = objs[0].location.y
    cx = (min(xs) + max(xs)) / 2; w = max(xs) - min(xs); hmax = max(o.dimensions.z for o in objs)
    for o in bpy.data.objects:
        if o.name.startswith('ENV_Temple_'):
            o.hide_render = o not in objs
    d = Vector((0.55, -0.75, 0.5)).normalized() if False else Vector((0.35, -1.0, 0.75)).normalized()
    cam.location = Vector((cx, ys, hmax * 0.4)) + d * 60
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.data.ortho_scale = max(w * 1.08, (hmax * 2.0) * 1.8)
    cam.data.clip_end = 300
    sc.render.filepath = f'{OUT}/row{r}.png'
    bpy.ops.render.render(write_still=True)
    print('ROW', r, [o.name.replace('ENV_Temple_', '') for o in objs])

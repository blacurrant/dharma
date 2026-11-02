# Look-dev renders for ENV_Temple_Central_Medallion.
# Warm key, 42° gameplay camera, floor-tile context. Cycles, not Unity URP.
import bpy, math, os
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion'
PREV = f'{ROOT}/previews'
STG_PREV = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion/Previews'
os.makedirs(PREV, exist_ok=True)
os.makedirs(STG_PREV, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=f'{ROOT}/TempleEnvironmentKit_medallion.blend')
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Filmic'
sc.view_settings.look = 'Medium High Contrast'

PAVER = (0.22, 0.19, 0.14, 1.0)
JOINT = (0.14, 0.12, 0.09, 1.0)


def mat_rgb(name, rgb, rough=0.90):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = rgb
    bsdf.inputs['Roughness'].default_value = rough
    return m


M_PAVER = mat_rgb('preview_paver', PAVER)
M_JOINT = mat_rgb('preview_joint', JOINT)

# Darker joint slab under the courtyard, then 2 m pavers with a gap around the disc.
bpy.ops.mesh.primitive_cube_add(location=(0, 0, -0.05), scale=(10.0, 10.0, 0.03))
ground = bpy.context.object
ground.name = 'ctx_joint'
ground.data.materials.append(M_JOINT)

for ix in range(-4, 5):
    for iy in range(-4, 5):
        cx, cy = ix * 2.08, iy * 2.08
        if cx * cx + cy * cy < 4.25 * 4.25:
            continue
        bpy.ops.mesh.primitive_cube_add(location=(cx, cy, -0.015), scale=(0.98, 0.98, 0.018))
        t = bpy.context.object
        t.name = f'ctx_paver_{ix}_{iy}'
        t.data.materials.append(M_PAVER)

w = bpy.data.worlds.new('preview_world')
w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.36, 0.34, 0.30, 1.0)
bg.inputs[1].default_value = 0.28
sc.world = w

# Low raking sun so the 2048 relief actually reads.
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(26), 0, math.radians(-48)))
sun = bpy.context.object
sun.data.energy = 5.4
sun.data.color = (1.0, 0.92, 0.78)
sun.data.angle = math.radians(1.6)

bpy.ops.object.light_add(type='AREA', location=(3.0, -8.0, 4.0))
fill = bpy.context.object
fill.data.energy = 90
fill.data.size = 12
fill.data.color = (0.88, 0.84, 0.76)


def shot(path, loc, target, ortho=None, lens=50):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print('wrote', path)


# Gameplay A2 — 42° pitch, ortho covering the 7.8 m disc + a ring of pavers
pitch = math.radians(42.0)
dist = 14.0
shot(f'{PREV}/medallion_game42.png',
     loc=(0.0, -dist * math.cos(pitch), dist * math.sin(pitch)),
     target=(0.0, 0.2, 0.02), ortho=10.5)

# 3/4 close — inner scroll + concentric rings
shot(f'{PREV}/medallion_close.png',
     loc=(-2.4, -4.6, 2.6), target=(0.15, 0.1, 0.02), lens=35)

# Top-down — full disc silhouette
shot(f'{PREV}/medallion_top.png',
     loc=(0.0, 0.0, 12.0), target=(0.0, 0.0, 0.0), ortho=8.4)

# Rim / bevel close — judge trip edge
shot(f'{PREV}/medallion_rim.png',
     loc=(3.2, -2.8, 0.85), target=(3.6, 0.1, 0.01), lens=50)

import shutil
for fn in os.listdir(PREV):
    if fn.endswith('.png'):
        shutil.copy2(f'{PREV}/{fn}', f'{STG_PREV}/{fn}')

print('previews done')

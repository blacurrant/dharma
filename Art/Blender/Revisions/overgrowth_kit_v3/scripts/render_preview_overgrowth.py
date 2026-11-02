# Preview renders for Overgrowth Kit v3. Contextual masonry, warm key, 42° gameplay camera.
import bpy, math, os
from mathutils import Vector, Euler

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/overgrowth_kit_v3'
PREV = f'{ROOT}/previews'
os.makedirs(PREV, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=f'{ROOT}/TempleEnvironmentKit_overgrowth_v3.blend')
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.cycles.samples = 48
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'
sc.view_settings.view_transform = 'Filmic'
sc.view_settings.look = 'Medium High Contrast'

STONE = (0.36, 0.32, 0.24, 1.0)
EARTH = (0.22, 0.18, 0.12, 1.0)


def mat_rgb(name, rgb, rough=0.85):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = rgb
    bsdf.inputs['Roughness'].default_value = rough
    return m


M_STONE = mat_rgb('preview_stone', STONE)
M_EARTH = mat_rgb('preview_earth', EARTH)


def add_box(name, loc, size, mat):
    bpy.ops.mesh.primitive_cube_add(location=loc, scale=size)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o


def add_cyl(name, loc, r, h, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=32)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    return o


objs = {o.name: o for o in bpy.data.objects if o.name.startswith('ENV_')}

# Layout (metres), with context proxies
# Roots
objs['ENV_Temple_Root_Claw_Pillar'].location = (0, 0, 0)
add_cyl('ctx_pillar', (0, 0, 1.8), 0.56, 3.6, M_STONE)
add_box('ctx_plinth', (0, 0, 0.12), (0.95, 0.95, 0.12), M_STONE)

objs['ENV_Temple_Root_Claw_Corner'].location = (4.5, 0, 0)
add_box('ctx_wall_x', (4.5 - 0.25, 0.9, 1.5), (0.25, 1.2, 1.5), M_STONE)
add_box('ctx_wall_y', (4.5 + 0.9, -0.25, 1.5), (1.2, 0.25, 1.5), M_STONE)

# Vines hang from a wall cornice at z=3.1 so they drape down the face
objs['ENV_Temple_Vine_Curtain_A'].location = (9.0, 0.08, 3.10)
objs['ENV_Temple_Vine_Curtain_B'].location = (11.4, 0.08, 3.80)
add_box('ctx_wall_vines', (10.2, -0.20, 1.9), (3.4, 0.20, 1.9), M_STONE)
add_box('ctx_cornice', (10.2, -0.05, 3.85), (3.5, 0.28, 0.10), M_STONE)

# Trees
objs['ENV_Temple_Tree_Canopy_A'].location = (16.5, 0, 0)
objs['ENV_Temple_Tree_Canopy_B'].location = (24.0, 0, 0)
add_box('ctx_ground', (12.0, 1.0, -0.06), (18.0, 6.0, 0.06), M_EARTH)

# Earth beds
objs['ENV_Temple_EarthBed_A'].location = (30.0, 0, 0)
objs['ENV_Temple_EarthBed_B'].location = (34.2, 0, 0)
add_box('ctx_floor', (32.2, 0, -0.04), (5.5, 3.0, 0.04), M_STONE)

# World + sun
w = bpy.data.worlds.new('preview_world')
w.use_nodes = True
bg = w.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.28, 0.30, 0.33, 1.0)
bg.inputs[1].default_value = 0.80
sc.world = w
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(48), 0, math.radians(-38)))
sun = bpy.context.object
sun.data.energy = 3.6
sun.data.color = (1.0, 0.93, 0.82)
bpy.ops.object.light_add(type='AREA', location=(12, -8, 6))
fill = bpy.context.object
fill.data.energy = 250
fill.data.size = 8
fill.data.color = (0.85, 0.90, 1.0)


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


# Overview, slightly elevated 42° gameplay-like
shot(f'{PREV}/kit_overview_game42.png',
     loc=(17.0, -16.0, 14.5), target=(17.0, 0.5, 2.2), ortho=38.0)

# Roots close — 3/4
shot(f'{PREV}/roots_close.png',
     loc=(-2.4, -3.6, 2.4), target=(2.1, 0.3, 1.4), lens=35)

# Vines close — from courtyard, looking at hanging curtains
shot(f'{PREV}/vines_close.png',
     loc=(10.2, 3.8, 2.2), target=(10.2, 0.1, 1.6), lens=32)

# Trees close — elevated 42-ish
shot(f'{PREV}/trees_close.png',
     loc=(20.0, -11.0, 9.5), target=(20.2, 1.2, 4.5), lens=28)

# Earth beds
shot(f'{PREV}/earth_close.png',
     loc=(32.0, -3.6, 2.6), target=(32.1, 0.1, 0.15), lens=35)

# Tree A silhouette from the side (judge broccoli vs canopy)
shot(f'{PREV}/tree_A_side.png',
     loc=(16.5, -9.5, 5.5), target=(16.5, 1.2, 5.2), lens=40)

# Vine A profile (judge shelf vs drape)
shot(f'{PREV}/vine_A_profile.png',
     loc=(12.6, 1.4, 1.6), target=(9.0, 0.15, 1.5), lens=40)

print('previews done')

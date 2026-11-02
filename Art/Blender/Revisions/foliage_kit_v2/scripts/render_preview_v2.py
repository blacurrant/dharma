import bpy, math, os
from mathutils import Vector

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/foliage_kit_v2'
PREV_DIR = f'{OUT}/previews'
os.makedirs(PREV_DIR, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=f'{OUT}/TempleEnvironmentKit_foliage_v2.blend')
sc = bpy.context.scene

# Environment setup
# Neutral stone ground plane and wall/pillar backdrops for context
def make_stone_box(name, loc, size, rgb):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object
    o.name = name
    o.scale = size
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1.0)
    m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.85
    o.data.materials.append(m)
    return o

# Floor plane
make_stone_box('ground_slab', (9.0, 0, -0.05), (14.0, 6.0, 0.05), (0.32, 0.28, 0.22))

# Backdrops for creepers
objs = {o.name: o for o in bpy.data.objects if o.name.startswith('ENV_')}

# Clump A at x=0
objs['ENV_Temple_Foliage_Clump_A'].location = (0.0, 0.0, 0.0)

# Clump B at x=3.0
objs['ENV_Temple_Foliage_Clump_B'].location = (3.0, 0.0, 0.0)

# Creeper Wall at x=6.0, wall behind it at y=-0.15
objs['ENV_Temple_Foliage_Creeper_Wall'].location = (6.0, 0.0, 0.0)
make_stone_box('wall_slab', (6.0, -0.20, 1.2), (1.5, 0.15, 1.3), (0.34, 0.30, 0.24))

# Creeper Column at x=9.0, cylinder column behind it
objs['ENV_Temple_Foliage_Creeper_Column'].location = (9.0, 0.0, 0.0)
bpy.ops.mesh.primitive_cylinder_add(radius=0.50, depth=2.4, location=(9.0, 0.0, 1.2))
col_ob = bpy.context.object
col_ob.name = 'column_shaft'
m_col = bpy.data.materials.new('mat_col')
m_col.use_nodes = True
m_col.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.34, 0.30, 0.24, 1.0)
col_ob.data.materials.append(m_col)

# Dirt Patch A at x=12.0
objs['ENV_Temple_Ground_DirtPatch_A'].location = (12.0, 0.0, 0.0)

# Dirt Patch B at x=15.0
objs['ENV_Temple_Ground_DirtPatch_B'].location = (15.0, 0.0, 0.0)

# Cracked Mortar C at x=18.0
objs['ENV_Temple_Ground_CrackedMortar_C'].location = (18.0, 0.0, 0.0)

# Lighting: Warm sun key (50 deg pitch, -35 deg yaw), cool ambient sky
sc.render.engine = 'CYCLES'
sc.cycles.samples = 64
sc.cycles.use_denoising = True
sc.render.resolution_x = 1920
sc.render.resolution_y = 1080

w = bpy.data.worlds.new('world_sky')
w.use_nodes = True
w.node_tree.nodes['Background'].inputs[0].default_value = (0.24, 0.26, 0.29, 1.0) # Cool sky ambient
w.node_tree.nodes['Background'].inputs[1].default_value = 0.85
sc.world = w

bpy.ops.object.light_add(type='SUN', rotation=(math.radians(50), 0, math.radians(-35)))
sun = bpy.context.object
sun.data.energy = 3.8
sun.data.color = (1.0, 0.93, 0.82) # Warm sun key

def render_camera_shot(filename, cam_loc, target_loc, ortho_scale=None, lens=50):
    bpy.ops.object.camera_add(location=cam_loc)
    cam = bpy.context.object
    direction = Vector(target_loc) - Vector(cam_loc)
    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
    if ortho_scale:
        cam.data.type = 'ORTHO'
        cam.data.ortho_scale = ortho_scale
    else:
        cam.data.lens = lens
    sc.camera = cam
    sc.render.filepath = f'{PREV_DIR}/{filename}.png'
    print(f"Rendering {filename}...")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam)

# 1. Gameplay camera view across the full kit (Pitch 42 deg, Ortho)
pitch = math.radians(42)
dist = 32.0
render_camera_shot(
    'kit_overview_game42',
    (9.0, -dist * math.cos(pitch), dist * math.sin(pitch) + 1.2),
    (9.0, 0.0, 0.6),
    ortho_scale=22.0
)

# 2. Close-up on Foliage Clump A
render_camera_shot('clump_A_close', (0.0, -2.8, 1.6), (0.0, 0.0, 0.45), lens=60)

# 3. Close-up on Foliage Clump B
render_camera_shot('clump_B_close', (3.0, -2.8, 1.3), (3.0, 0.0, 0.28), lens=60)

# 4. Close-up on Creepers (Wall & Column)
render_camera_shot('creepers_close', (7.5, -3.8, 1.8), (7.5, 0.0, 1.1), lens=55)

# 5. Close-up on Ground Transition Patches
render_camera_shot('ground_patches_close', (15.0, -3.2, 1.9), (15.0, 0.0, 0.05), lens=55)

print("All preview renders completed successfully.")

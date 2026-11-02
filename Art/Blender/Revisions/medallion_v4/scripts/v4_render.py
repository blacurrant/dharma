# Look-dev renders for medallion v4 (Cycles; Unity URP will differ). Floor context uses the kit's
# ENV_Temple_Floor_D maps on a plane (2 m tiling) - context only, not part of the asset.
import bpy, math, os, sys
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion_v4'
PREV = f'{ROOT}/previews'
STG_PREV = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion_v4/Previews'
FLOOR = '/Users/landerstudio/MythicRoguelite/Assets/ArtTest/Environment/Textures/ENV_Temple_Floor_D_'
os.makedirs(PREV, exist_ok=True); os.makedirs(STG_PREV, exist_ok=True)
SAMPLES = int(os.environ.get('V4_SAMPLES', '96'))

bpy.ops.wm.open_mainfile(filepath=f'{ROOT}/ENV_Temple_Central_Medallion_v4.blend')
sc = bpy.context.scene
med = bpy.data.objects['ENV_Temple_Central_Medallion']
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.view_settings.view_transform = 'AgX'
sc.view_settings.look = 'AgX - Medium High Contrast'

# context floor: neutral offset-course paving in the floor kit's measured value range (context only)
bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0.0))
fl = bpy.context.object
fm = bpy.data.materials.new('ctx_floor'); nt = fm.node_tree
b = nt.nodes['Principled BSDF']
br = nt.nodes.new('ShaderNodeTexBrick')
tcb = nt.nodes.new('ShaderNodeTexCoord'); nt.links.new(tcb.outputs['Object'], br.inputs['Vector'])
br.inputs['Scale'].default_value = 0.6
br.inputs['Brick Width'].default_value = 1.0
br.inputs['Row Height'].default_value = 0.5
br.inputs['Mortar Size'].default_value = 0.012
br.inputs['Color1'].default_value = (0.052, 0.042, 0.029, 1)
br.inputs['Color2'].default_value = (0.040, 0.033, 0.024, 1)
br.inputs['Mortar'].default_value = (0.018, 0.015, 0.011, 1)
br.offset = 0.37
nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 3.0
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
mix.inputs['Factor'].default_value = 0.35
nt.links.new(br.outputs['Color'], mix.inputs['A']); nt.links.new(nz.outputs['Color'], mix.inputs['B'])
nt.links.new(mix.outputs['Result'], b.inputs['Base Color'])
bmp = nt.nodes.new('ShaderNodeBump'); bmp.inputs['Strength'].default_value = 0.6
nt.links.new(br.outputs['Fac'], bmp.inputs['Height']); nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
b.inputs['Roughness'].default_value = 0.9
fl.data.materials.append(fm)

w = bpy.data.worlds.new('lookdev'); sc.world = w
bg = w.node_tree.nodes['Background']
bg.inputs[0].default_value = (0.40, 0.42, 0.46, 1); bg.inputs[1].default_value = 0.55
# key from the far side (shadows fall toward camera), low enough to rake the relief
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(58), 0, math.radians(160)))
sun = bpy.context.object; sun.data.energy = 4.2; sun.data.color = (1.0, 0.90, 0.76); sun.data.angle = math.radians(1.5)


def shot(name, loc, target, ortho=None, lens=50, clay=False):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.object
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.lens = lens
    sc.camera = cam
    sc.render.filepath = f'{PREV}/{name}.png'
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)
    print('wrote', name, flush=True)


which = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['game', 'close', 'top', 'rim', 'clay']
pitch = math.radians(42)
D = 20.0
for s in which:
    if s == 'game':     # gameplay A2: 42 deg pitch, ortho 11 (true gameplay framing)
        shot('v4_game42', (0, -D * math.cos(pitch), D * math.sin(pitch)), (0, 0, 0), ortho=11.0)
    elif s == 'close':
        shot('v4_close', (-2.2, -4.4, 2.3), (0.4, 0.3, 0.05), lens=32)
    elif s == 'top':
        shot('v4_top', (0, 0, 15), (0, 0, 0), ortho=8.4)
    elif s == 'rim':
        shot('v4_rim', (3.0, -3.0, 0.75), (3.5, -0.2, 0.03), lens=45)
    elif s == 'clay':   # same low-poly mesh + baked normal only: shows the form the bake carries
        m = med.data.materials[0]; ntm = m.node_tree; bs = ntm.nodes['Principled BSDF']
        lk = [l for l in ntm.links if l.to_socket == bs.inputs['Base Color']]
        for l in lk:
            ntm.links.remove(l)
        bs.inputs['Base Color'].default_value = (0.42, 0.42, 0.42, 1)
        shot('v4_clay_game42', (0, -D * math.cos(pitch), D * math.sin(pitch)), (0, 0, 0), ortho=9.0)
import shutil
for fn in os.listdir(PREV):
    shutil.copy2(f'{PREV}/{fn}', f'{STG_PREV}/{fn}')

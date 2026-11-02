"""Clay preview (geometry only, no bake): build the named assets fresh, render gameplay-camera-angle and arena-side views with a grey clay material.
  Blender -b --factory-startup --python scripts/21_clay_preview.py -- Wall_Tall_A [Wall_Tall_B ...]
Outputs to $TMPDIR/clay_*.png (scratch; not deliverables)."""
import sys, os, math
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch2/scripts'
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector
import kitlib as K
import batch2_assets as BA

OUT = os.environ.get('TMPDIR', '/tmp')
names = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath='/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch2/TempleEnvironmentKit_batch2.blend')
sc = bpy.context.scene
for o in list(bpy.data.objects):
    if o.type == 'MESH' or o.type == 'LIGHT':
        bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'
try:
    sc.eevee.taa_render_samples = 24
except Exception:
    pass
sc.view_settings.view_transform = 'Standard'
w = bpy.data.worlds.new('clay'); w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0.05, 0.05, 0.055, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.6
sc.world = w
sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 3.5; sd.angle = 0.1
so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so); so.rotation_euler = (math.radians(50), 0, math.radians(-35))
clay = bpy.data.materials.new('clay'); clay.use_nodes = True
pb = clay.node_tree.nodes['Principled BSDF']; pb.inputs['Base Color'].default_value = (0.55, 0.50, 0.44, 1); pb.inputs['Roughness'].default_value = 0.9
zcol = {0: (0.55, 0.50, 0.44), 1: (0.22, 0.20, 0.19), 2: (0.55, 0.32, 0.12), 3: (0.8, 0.6, 0.2), 4: (0.4, 0.05, 0.05), 5: (1.0, 0.45, 0.08)}
cam = bpy.data.cameras.new('c'); cam.type = 'ORTHO'
co_ = bpy.data.objects.new('c', cam); sc.collection.objects.link(co_); sc.camera = co_
sc.render.resolution_x, sc.render.resolution_y = 1400, 900


def clay_for(o):
    me = o.data
    me.materials.clear()
    import numpy as np
    zs = np.empty(len(me.polygons), np.int32); me.attributes[K.ZONE_ATTR].data.foreach_get('value', zs)
    used = sorted(set(zs.tolist()))
    for z in used:
        m = bpy.data.materials.new('cz%d' % z); m.use_nodes = True
        p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = zcol[z] + (1,); p.inputs['Roughness'].default_value = 0.85
        if z == 5:
            p.inputs['Emission Color'].default_value = zcol[z] + (1,); p.inputs['Emission Strength'].default_value = 1.5
        me.materials.append(m)
    remap = {z: i for i, z in enumerate(used)}
    me.polygons.foreach_set('material_index', [remap[z] for z in zs.tolist()])


def look(target, direction, scale, name):
    d = Vector(direction).normalized()
    co_.location = Vector(target) + d * 80
    co_.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    cam.ortho_scale = scale; cam.clip_end = 400
    sc.render.filepath = f'{OUT}/clay_{name}.png'
    bpy.ops.render.render(write_still=True)
    print('CLAY', sc.render.filepath, flush=True)


for nm in names:
    cat, fn, *_ = BA.REG2[nm]
    b = fn(); o = b.to_object('t_' + nm); clay_for(o)
    dims = o.dimensions; zc = dims.z / 2
    big = max(dims.x, dims.y, dims.z)
    if cat == 'Wall':
        # (1) gameplay-camera angle seen from the arena (camera looks toward -x,+z; the bay's arena side faces -z there)
        gc = Vector((12, -12, 18))
        look((0, 0, zc), (12, -12, 18), max(dims.z * 1.35, 9.5), nm + '_gameplay')
        look((0, 0, zc), (0, -1, 0.0), max(dims.z * 1.15, dims.x * 1.2), nm + '_front')
        look((0, 0, zc), (0.9, -0.5, 0.35), max(dims.z * 1.3, 8.0), nm + '_oblique')
    else:
        look((0, 0, zc), (12, -12, 18), big * 1.35, nm + '_gameplay')
        look((0, 0, zc), (1.0, -1.0, 0.45), big * 1.35, nm + '_oblique')
        look((0, 0, zc), (-1.0, 1.0, 0.45), big * 1.35, nm + '_rear')
    bpy.data.objects.remove(o, do_unlink=True)
print('CLAY_DONE')

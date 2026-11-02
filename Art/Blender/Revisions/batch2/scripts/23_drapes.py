"""Batch-2 cloth drapes (no bake: plain meshes + one tintable grey weave texture; colour is a Unity material tint).
  Blender -b --factory-startup --python scripts/23_drapes.py
Meshes (pivot = hang point, top centre; hangs toward -Z; local +Y = front/outward like wall bays):
  Drape_A  1.7 x 3.1 m  gathered top, vertical folds, weighted hem (scalloped)
  Drape_B  1.0 x 4.0 m  long banner drape, swallow-tail hem, gentle S sway
  Drape_C  3.6 x 1.7 m  swag between two supports (catenary droop 1.1 m), pleated
Exports FBX (same settings as 05_export) to batch2/models and the shared weave PNG to batch2/textures. Never saves a .blend (the batch2 working copy is owned by run_asset.sh).
"""
import bpy, bmesh, math, os, random, sys
import numpy as np
from mathutils import Vector

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch2'
os.makedirs(G + '/models', exist_ok=True); os.makedirs(G + '/textures', exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---- weave texture (grey, tintable): warp/weft + two plain woven bands, slight mottling. No hue at all.
TEXP = G + '/textures/ENV_Temple_Drape_Weave.png'
W, H = 512, 1024
rng = np.random.default_rng(7)
x = np.arange(W)[None, :]; y = np.arange(H)[:, None]
weave = 0.5 + 0.5 * np.sin(x * 2 * math.pi / 3.0) * np.sin(y * 2 * math.pi / 3.0)
thread = rng.normal(0, 1, (H, W)); thread = (thread - thread.min()) / (thread.max() - thread.min())
blot = np.zeros((H, W))
for k, (f, a) in enumerate(((3, 0.12), (7, 0.06), (17, 0.035))):
    ph = rng.uniform(0, 6.28, 4)
    blot += a * (np.sin(x * f * 2 * math.pi / W + ph[0]) * np.sin(y * f * 2 * math.pi / H + ph[1]) + np.sin((x + y) * f * 2 * math.pi / (W + H) + ph[2]))
v = 0.78 + 0.10 * weave + 0.05 * thread + blot
vv = (y / H) * np.ones((1, W))
for c0, c1, d in ((0.06, 0.085, -0.22), (0.095, 0.105, 0.12), (0.90, 0.915, 0.12), (0.925, 0.96, -0.22)):    # plain woven bands near the top and bottom (V along the hang)
    v = np.where((vv >= c0) & (vv < c1), v + d, v)
v = np.clip(v, 0, 1)
px = np.clip(v * 255 + 0.5, 0, 255).astype(np.uint8)
img = bpy.data.images.new('weave', W, H, alpha=False)
arr = np.repeat((px.astype(np.float32) / 255.0)[:, :, None], 3, 2)
arr4 = np.concatenate([arr, np.ones((H, W, 1), np.float32)], 2)
img.colorspace_settings.name = 'sRGB'
img.pixels.foreach_set(arr4[::-1].ravel())
img.filepath_raw = TEXP; img.file_format = 'PNG'; img.save()
print('TEX', TEXP, flush=True)


def material():
    m = bpy.data.materials.new('MI_Temple_Drape'); m.use_nodes = True
    nt = m.node_tree; pb = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(TEXP)
    nt.links.new(t.outputs['Color'], pb.inputs['Base Color'])
    pb.inputs['Roughness'].default_value = 0.92
    return m


MAT = material()


def build(name, w, h, nx, ny, top_scale, fold_k, fold_amp, sway, hem, droop=0.0, seed=1):
    """Grid cloth. Columns x in [-w/2, w/2] (top gathered by top_scale), rows z from 0 down to -h. Front +Y. Returns object."""
    r = random.Random(seed)
    ph = [r.uniform(0, 6.28) for _ in range(4)]
    bm = bmesh.new(); uv = bm.loops.layers.uv.new('UVMap')
    verts = []
    for j in range(ny + 1):
        t = j / ny                                                     # 0 top .. 1 hem
        row = []
        for i in range(nx + 1):
            s = i / nx
            xx = (s - 0.5) * w * (top_scale + (1.0 - top_scale) * min(1.0, t * 3.0))   # gathered near the top
            amp = fold_amp * (0.25 + 0.75 * t) * (0.7 + 0.3 * math.sin(ph[0] + t * 5))
            yy = amp * (math.sin(2 * math.pi * fold_k * s + ph[1] + 0.8 * t) + 0.35 * math.sin(2 * math.pi * fold_k * 2.3 * s + ph[2]))
            yy += sway * math.sin(t * math.pi * 1.4 + ph[3]) * t
            zz = -t * h
            if droop > 0:                                              # swag: top edge follows a catenary, hem follows it too (cloth hangs from it)
                a_ = 2.0
                sag = droop * (1.0 - (math.cosh(a_ * (2 * s - 1)) - 1.0) / (math.cosh(a_) - 1.0))   # 0 at the supports, droop at the middle
                zz -= sag
                yy += 0.08 * math.sin(math.pi * s) * t
            if hem == 'scallop' and j == ny:
                zz += 0.07 * math.sin(2 * math.pi * fold_k * s + ph[1] + 0.8) ** 2 - 0.02
            if hem == 'swallow' and j >= ny - 6:
                depth = (1 - abs(2 * s - 1)) * 0.55                   # V notch: centre is shorter
                zz += depth * ((j - (ny - 6)) / 6.0) ** 1.5          # raises the centre of the hem -> V notch
            row.append(bm.verts.new((xx, yy, zz)))
        verts.append(row)
    for j in range(ny):
        for i in range(nx):
            f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
            for l, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                l[uv].uv = (ii / nx, 1.0 - jj / ny)
    # weighted hem: a small rolled hem tube along the bottom edge
    for i in range(nx):
        a, b_ = verts[ny][i], verts[ny][i + 1]
        c, d = Vector(a.co) + Vector((0, 0.045, 0.0)), Vector(b_.co) + Vector((0, 0.045, 0.0))
        va, vb = bm.verts.new(c), bm.verts.new(d)
        f = bm.faces.new((a, b_, vb, va))
        for l, (uu, vv_) in zip(f.loops, ((i / nx, 0.0), ((i + 1) / nx, 0.0), ((i + 1) / nx, 0.04), (i / nx, 0.04))):
            l[uv].uv = (uu, vv_)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # make sure normals face +Y (front)
    ny_sum = sum(f.normal.y for f in bm.faces)
    if ny_sum < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(MAT)
    ob = bpy.data.objects.new('ENV_Temple_' + name, me); bpy.context.scene.collection.objects.link(ob)
    return ob


objs = [
    build('Drape_A', 1.7, 3.1, 28, 36, 0.62, 5.0, 0.055, 0.04, 'scallop', seed=11),
    build('Drape_B', 1.0, 4.0, 18, 44, 0.80, 3.0, 0.045, 0.10, 'swallow', seed=12),
    build('Drape_C', 3.6, 1.7, 52, 24, 1.0, 9.0, 0.040, 0.0, None, droop=1.1, seed=13),
]
for o in objs:
    n = len(o.data.polygons) * 2
    zs = [v.co.z for v in o.data.vertices]; xs = [v.co.x for v in o.data.vertices]; ys = [v.co.y for v in o.data.vertices]
    print('DRAPE', o.name, 'tris', n, 'x', round(min(xs), 3), round(max(xs), 3), 'y', round(min(ys), 3), round(max(ys), 3), 'z', round(min(zs), 3), round(max(zs), 3), flush=True)
    for x_ in bpy.context.view_layer.objects:
        x_.select_set(False)
    o.select_set(True); bpy.context.view_layer.objects.active = o
    bpy.ops.export_scene.fbx(filepath=f'{G}/models/{o.name}.fbx', use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='OFF', use_triangles=True, use_tspace=True, colors_type='NONE', add_leaf_bones=False,
                             path_mode='RELATIVE', embed_textures=False, bake_anim=False, use_custom_props=False)
    print('EXPORTED', o.name, os.path.getsize(f'{G}/models/{o.name}.fbx'), flush=True)
print('DRAPES_DONE')

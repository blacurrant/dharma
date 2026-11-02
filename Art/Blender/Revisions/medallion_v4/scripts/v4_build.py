# ENV_Temple_Central_Medallion v4 - stage 2: low-poly masonry mesh + high-poly relief mesh,
# Cycles bakes (tangent normal high->low, AO on high), texture compose, FBX export, re-import check.
# Run: Blender -b --python v4_build.py
import bpy, bmesh, math, os, json, time, hashlib, zlib, struct, shutil
import numpy as np
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion_v4'
CACHE, TEX, MOD = f'{ROOT}/cache', f'{ROOT}/textures', f'{ROOT}/models'
STG = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion_v4'
for d in (TEX, MOD, f'{STG}/Models', f'{STG}/Textures'):
    os.makedirs(d, exist_ok=True)
NAME = 'ENV_Temple_Central_Medallion'
T0 = time.time()
TAU = math.tau


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


L = json.load(open(f'{CACHE}/layout.json'))
EXT, N, HG, R_OUT, Z_TOP, LIP = L['EXT'], L['N'], L['HG'], L['R_OUT'], L['Z_TOP'], L['LIP']
PX = 2 * EXT / N
Z = np.load(f'{CACHE}/Z.npy')
HsB = np.load(f'{CACHE}/HsB.npy')
BW = 0.025          # low-poly bevel inset
BEV = 0.014


def samp(A, x, y):
    x = np.asarray(x, np.float64); y = np.asarray(y, np.float64)
    fx = (x + EXT) / PX - 0.5; fy = (y + EXT) / PX - 0.5
    i0 = np.clip(np.floor(fx).astype(int), 0, N - 2); j0 = np.clip(np.floor(fy).astype(int), 0, N - 2)
    tx = np.clip(fx - i0, 0, 1); ty = np.clip(fy - j0, 0, 1)
    return (A[j0, i0] * (1 - tx) * (1 - ty) + A[j0, i0 + 1] * tx * (1 - ty) +
            A[j0 + 1, i0] * (1 - tx) * ty + A[j0 + 1, i0 + 1] * tx * ty)


def sst(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def zlow(bl, x, y):
    x = np.asarray(x); y = np.asarray(y)
    r = np.hypot(x, y)
    z = Z_TOP + bl['off'] + bl['tilt'][0] * (x - bl['c'][0]) + bl['tilt'][1] * (y - bl['c'][1]) + samp(HsB, x, y)
    s = sst(3.72, 3.90, r)
    return z * (1 - s) + LIP * s


def zbed(x, y):
    r = math.hypot(x, y)
    return float(0.030 - 0.018 * sst(3.70, 3.90, r))


def uv_planar(x, y):
    return ((x + EXT) / (2 * EXT), (y + EXT) / (2 * EXT))


def uv_side(x, y):   # walls: tiny patch in the unused texture corner (filled with joint stone)
    return (0.003 + 0.0016 * (x + EXT) / (2 * EXT), 0.003 + 0.0016 * (y + EXT) / (2 * EXT))


# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = 'METRIC'

# ---------------------------------------------------------------- low poly
bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UVMap')
wall_faces, top_faces = [], []


def add_face(vs, kind, outward=None):
    f = bm.faces.new(vs)
    f.normal_update()
    if kind == 'top' and f.normal.z < 0:
        f.normal_flip()
    if kind == 'wall' and outward is not None:
        fc = f.calc_center_median()
        if f.normal.dot(Vector((fc.x - outward[0], fc.y - outward[1], 0))) < 0:
            f.normal_flip()
    (top_faces if kind == 'top' else wall_faces).append(f)
    return f


def grid_block(bl):
    r_in, a0, a1 = bl['r0'] + HG, bl['a0'], bl['a1']
    outer = bl['ring'] == 3
    r_out = R_OUT if outer else bl['r1'] - HG
    if outer:
        mid = list(np.linspace(r_in + BW, 3.70, max(2, int(math.ceil((3.70 - r_in - BW) / 0.30)) + 1)))
        rows = [r_in] + mid + [3.80, 3.86, R_OUT]
    else:
        mid = list(np.linspace(r_in + BW, r_out - BW, max(2, int(math.ceil((r_out - r_in - 2 * BW) / 0.30)) + 1)))
        rows = [r_in] + mid + [r_out]
    rm = 0.5 * (r_in + r_out)
    m = max(2, int(math.ceil(((a1 - a0) * rm - 2 * (HG + BW)) / 0.30)) + 1)
    G = []
    for i, r in enumerate(rows):
        u = np.linspace(a0 + (HG + BW) / r, a1 - (HG + BW) / r, m)
        angs = [a0 + HG / r] + list(u) + [a1 - HG / r]
        xs = np.array([r * math.cos(a) for a in angs]); ys = np.array([r * math.sin(a) for a in angs])
        zs = zlow(bl, xs, ys)
        row = []
        for j in range(len(angs)):
            edge = (i == 0 or j == 0 or j == len(angs) - 1 or (i == len(rows) - 1 and not outer))
            row.append(bm.verts.new((xs[j], ys[j], float(zs[j]) - (BEV if edge else 0.0))))
        G.append(row)
    nr, nc = len(G), len(G[0])
    for i in range(nr - 1):
        for j in range(nc - 1):
            add_face((G[i][j], G[i][j + 1], G[i + 1][j + 1], G[i + 1][j]), 'top')
    loop = G[0][:] + [G[i][-1] for i in range(1, nr)] + G[-1][-2::-1] + [G[i][0] for i in range(nr - 2, 0, -1)]
    return loop, outer


def centre_block(bl):
    rad = [0.20, 0.42, 0.62, 0.84, 1.03, 1.20 - HG - BW, 1.20 - HG]
    seg = 40
    cz = float(zlow(bl, np.array([0.0]), np.array([0.0]))[0])
    cv = bm.verts.new((0, 0, cz))
    rings = []
    for k, r in enumerate(rad):
        a = np.array([TAU * j / seg for j in range(seg)])
        xs, ys = r * np.cos(a), r * np.sin(a)
        zs = zlow(bl, xs, ys) - (BEV if k == len(rad) - 1 else 0)
        rings.append([bm.verts.new((xs[j], ys[j], float(zs[j]))) for j in range(seg)])
    for j in range(seg):
        add_face((cv, rings[0][j], rings[0][(j + 1) % seg]), 'top')
    for k in range(len(rad) - 1):
        a, b = rings[k], rings[k + 1]
        for j in range(seg):
            add_face((a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]), 'top')
    return rings[-1], False


for bl in L['blocks']:
    loop, outer = centre_block(bl) if bl['ring'] == 0 else grid_block(bl)
    bots = []
    for v in loop:
        x, y = v.co.x, v.co.y
        zb = 0.0 if (outer and math.hypot(x, y) > R_OUT - 0.001) else zbed(x, y)
        bots.append(bm.verts.new((x, y, zb)))
    n = len(loop)
    for k in range(n):
        k2 = (k + 1) % n
        add_face((loop[k], loop[k2], bots[k2], bots[k]), 'wall', bl['c'])

# bed under the joints
seg = 48
bed_r = [1.20, 2.16, 3.06, R_OUT - 0.02]
cv = bm.verts.new((0, 0, zbed(0, 0) - 0.004))
rings = [[bm.verts.new((r * math.cos(TAU * j / seg), r * math.sin(TAU * j / seg), zbed(r, 0) - 0.004)) for j in range(seg)] for r in bed_r]
for j in range(seg):
    add_face((cv, rings[0][j], rings[0][(j + 1) % seg]), 'top')
for k in range(len(rings) - 1):
    for j in range(seg):
        add_face((rings[k][j], rings[k][(j + 1) % seg], rings[k + 1][(j + 1) % seg], rings[k + 1][j]), 'top')

for f in top_faces:
    f.smooth = True
    for lp in f.loops:
        lp[uvl].uv = uv_planar(lp.vert.co.x, lp.vert.co.y)
for f in wall_faces:
    f.smooth = False
    for lp in f.loops:
        lp[uvl].uv = uv_side(lp.vert.co.x, lp.vert.co.y)
me = bpy.data.meshes.new(NAME)
bm.to_mesh(me)
bm.free()
low = bpy.data.objects.new(NAME, me)
sc.collection.objects.link(low)
tris = sum(len(p.vertices) - 2 for p in me.polygons)
log('low poly', len(me.vertices), 'verts', tris, 'tris')

# ---------------------------------------------------------------- high poly (7 mm heightfield grid)
STEP = 0.007
G = int(round(2 * EXT / STEP)) + 1
g = np.linspace(-EXT, EXT, G)
GX, GY = np.meshgrid(g, g)
GZ = samp(Z, GX.ravel(), GY.ravel())
verts = np.stack([GX.ravel(), GY.ravel(), GZ], 1).astype(np.float32)
ii, jj = np.meshgrid(np.arange(G - 1), np.arange(G - 1))
a = (jj * G + ii).ravel()
faces = np.stack([a, a + 1, a + G + 1, a + G], 1)
hme = bpy.data.meshes.new('HIGH_relief')
hme.vertices.add(len(verts)); hme.vertices.foreach_set('co', verts.ravel())
hme.loops.add(faces.size); hme.loops.foreach_set('vertex_index', faces.ravel().astype(np.int32))
hme.polygons.add(len(faces)); hme.polygons.foreach_set('loop_start', (np.arange(len(faces)) * 4).astype(np.int32))
hme.update(calc_edges=True)
uvh = hme.uv_layers.new(name='UVMap')
lv = faces.ravel()
uvh.data.foreach_set('uv', np.stack([(verts[lv, 0] + EXT) / (2 * EXT), (verts[lv, 1] + EXT) / (2 * EXT)], 1).ravel().astype(np.float32))
hme.shade_smooth()
high = bpy.data.objects.new('HIGH_relief', hme)
sc.collection.objects.link(high)
log('high poly', len(hme.vertices), 'verts', len(hme.polygons) * 2, 'tris')

# ---------------------------------------------------------------- bakes
RES = 2048
sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
w = bpy.data.worlds.new('bake_world'); sc.world = w
w.light_settings.distance = 0.22


def bake_img(name, obj, btype, **kw):
    path = f'{CACHE}/{name}.exr'
    if os.path.exists(path):
        img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
        log('cached', name); return img
    img = bpy.data.images.new(name, RES, RES, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    mat = bpy.data.materials.new('bake_' + name)
    nt = mat.node_tree
    tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
    nt.nodes.active = tn
    obj.data.materials.clear(); obj.data.materials.append(mat)
    for o in sc.objects:
        o.select_set(False)
    if kw.get('use_selected_to_active'):
        high.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    t = time.time()
    bpy.ops.object.bake(type=btype, margin=6, **kw)
    img.filepath_raw = path; img.file_format = 'OPEN_EXR'; img.save()
    log('baked', name, f'{time.time() - t:.1f}s')
    return img


def img_np(img, ch=4):
    a = np.empty(RES * RES * 4, np.float32); img.pixels.foreach_get(a)
    return a.reshape(RES, RES, 4)


sc.cycles.samples = 1
# max_ray_distance>0 made most rays miss the relief (only joints baked); cage 0.10 + unlimited distance verified
nrm = img_np(bake_img('bake_normal_c10', low, 'NORMAL', use_selected_to_active=True, cage_extrusion=0.10,
                      max_ray_distance=0.0, normal_space='TANGENT'))
# AO from the 4096 heightfield (multi-scale cavity). The Cycles AO bake on the 7 mm grid gave
# binary self-shadow noise (terminator artefacts), so it is not used.
_Zf = np.load(f'{CACHE}/Z.npy')
_F2 = np.fft.fftfreq(N)[:, None] ** 2 + np.fft.rfftfreq(N)[None, :] ** 2
_Zh = np.fft.rfft2(_Zf)
occl = np.zeros_like(_Zf)
for sg, dz, wt in ((4, 0.004, 0.40), (12, 0.008, 0.35), (36, 0.016, 0.25)):
    bz = np.fft.irfft2(_Zh * np.exp(-2 * np.pi ** 2 * sg * sg * _F2), s=_Zf.shape)
    occl += wt * np.clip((bz - _Zf) / dz, 0, 1)
ao = (1 - 0.8 * occl).reshape(RES, 2, RES, 2).mean((1, 3)).astype(np.float32)

# ---------------------------------------------------------------- compose (rows: row 0 = v 0 = y -EXT)
def down2(a):
    return a.reshape(RES, 2, RES, 2, *a.shape[2:]).mean((1, 3))


col = down2(np.load(f'{CACHE}/col.npy'))
rough = down2(np.load(f'{CACHE}/rough.npy'))
cc = ((np.arange(RES) + 0.5) * 2 * EXT / RES - EXT)
RR = np.hypot(*np.meshgrid(cc, cc))
outside = RR > R_OUT + 0.01
ao = np.where(outside, 0.6, np.clip(ao, 0, 1))
base = col * 0.82 * (0.72 + 0.28 * ao)[..., None]  # 0.82: keep the disc close to the floor kit value
base[outside] = (0.17, 0.15, 0.11)

# fine grain detail normal (sub-7mm) blended UDN over the baked map; planar UV => tangent ~ +X, bitangent ~ +Y
Zf = np.load(f'{CACHE}/Z.npy')
from numpy.fft import rfft2, irfft2, fftfreq, rfftfreq
F2 = fftfreq(N)[:, None] ** 2 + rfftfreq(N)[None, :] ** 2
hp = Zf - irfft2(rfft2(Zf) * np.exp(-2 * np.pi ** 2 * 1.6 ** 2 * F2), s=Zf.shape)
hp = np.clip(hp, -0.002, 0.002)
dx = down2(np.gradient(hp, axis=1) / PX); dy = down2(np.gradient(hp, axis=0) / PX)
n = nrm[..., :3] * 2 - 1
n = np.stack([n[..., 0] - 0.6 * dx, n[..., 1] - 0.6 * dy, n[..., 2]], -1)
n /= np.linalg.norm(n, axis=-1, keepdims=True)
n[outside] = (0, 0, 1)
nrm8 = n * 0.5 + 0.5

mask = np.zeros((RES, RES, 4), np.float32)
mask[..., 1] = ao                                # URP: R metallic 0, G occlusion, B detail 0, A smoothness
mask[..., 3] = 1 - rough
mask[outside, 3] = 0.05


def to8(a):
    return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)


def write_png(path, a):
    a = np.ascontiguousarray(a[::-1]); h, w_ = a.shape[:2]; ch = 1 if a.ndim == 2 else a.shape[2]
    raw = b''.join(b'\x00' + a[i].tobytes() for i in range(h))
    ck = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    open(path, 'wb').write(b'\x89PNG\r\n\x1a\n' + ck(b'IHDR', struct.pack('>IIBBBBB', w_, h, 8, {1: 0, 3: 2, 4: 6}[ch], 0, 0, 0)) +
                           ck(b'IDAT', zlib.compress(raw, 6)) + ck(b'IEND', b''))


TX = {'BaseColor': to8(base), 'Normal': to8(nrm8), 'Mask': to8(mask)}
for k, a in TX.items():
    write_png(f'{TEX}/{NAME}_{k}.png', a)
log('textures written')

# Q18: cyan/teal band (hue 160-200 deg, sat > 0.2) on the shipped BaseColor bytes
b8 = TX['BaseColor'].astype(np.float32) / 255
mx, mn = b8.max(-1), b8.min(-1)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
r_, g_, b_ = b8[..., 0], b8[..., 1], b8[..., 2]
d = np.maximum(mx - mn, 1e-6)
hue = np.where(mx == r_, (g_ - b_) / d % 6, np.where(mx == g_, (b_ - r_) / d + 2, (r_ - g_) / d + 4)) * 60
q18 = float(((hue >= 160) & (hue <= 200) & (sat > 0.2)).mean() * 100)
disc = ~outside
mean_rgb = [round(float(v), 1) for v in (TX['BaseColor'][disc].mean(0))]
log('Q18', q18, 'mean', mean_rgb)

# ---------------------------------------------------------------- game material + export
low.data.materials.clear()
mat = bpy.data.materials.new('M_Temple_Central_Medallion_v4')
nt = mat.node_tree
bsdf = nt.nodes.get('Principled BSDF') or nt.nodes.new('ShaderNodeBsdfPrincipled')


def tex(k, cs):
    i = bpy.data.images.load(f'{TEX}/{NAME}_{k}.png'); i.colorspace_settings.name = cs
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = i
    return t, i


tb, _ = tex('BaseColor', 'sRGB'); nt.links.new(tb.outputs['Color'], bsdf.inputs['Base Color'])
tn_, _ = tex('Normal', 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap')
nt.links.new(tn_.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
tm, im = tex('Mask', 'Non-Color'); im.alpha_mode = 'CHANNEL_PACKED'
inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
nt.links.new(tm.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
low.data.materials.append(mat)
bpy.data.objects.remove(high, do_unlink=True)
bpy.ops.wm.save_as_mainfile(filepath=f'{ROOT}/ENV_Temple_Central_Medallion_v4.blend')

for o in sc.objects:
    o.select_set(False)
low.select_set(True); bpy.context.view_layer.objects.active = low
fbx = f'{MOD}/{NAME}.fbx'
bpy.ops.export_scene.fbx(filepath=fbx, use_selection=True, object_types={'MESH'}, global_scale=1.0,
                         apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                         axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_triangles=True, use_tspace=True,
                         path_mode='RELATIVE', embed_textures=False, bake_anim=False, add_leaf_bones=False)
log('fbx exported')

# ---------------------------------------------------------------- re-import check
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
ob = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bpy.context.view_layer.update()
ws = [ob.matrix_world @ v.co for v in ob.data.vertices]
mn_ = [min(v[i] for v in ws) for i in range(3)]; mx_ = [max(v[i] for v in ws) for i in range(3)]
chk = dict(tris=sum(len(p.vertices) - 2 for p in ob.data.polygons), verts=len(ob.data.vertices),
           uv_layers=[u.name for u in ob.data.uv_layers], materials=[m.name for m in ob.data.materials],
           bbox_min=[round(v, 4) for v in mn_], bbox_max=[round(v, 4) for v in mx_],
           diameter_m=round(mx_[0] - mn_[0], 4), height_m=round(mx_[2] - mn_[2], 4))
log('reimport', chk)

# ---------------------------------------------------------------- staging
sha = lambda p: hashlib.sha256(open(p, 'rb').read()).hexdigest()
shutil.copy2(fbx, f'{STG}/Models/{NAME}.fbx')
files = {}
for k in TX:
    src = f'{TEX}/{NAME}_{k}.png'; shutil.copy2(src, f'{STG}/Textures/{NAME}_{k}.png')
    files[f'Textures/{NAME}_{k}.png'] = sha(src)
files[f'Models/{NAME}.fbx'] = sha(fbx)
man = dict(asset=f'{NAME}.fbx', version='v4 (masonry blocks + high-poly relief bake)',
           source_blend='Art/Blender/Revisions/medallion_v4/ENV_Temple_Central_Medallion_v4.blend',
           scripts='Art/Blender/Revisions/medallion_v4/scripts/v4_maps.py, v4_build.py',
           units='metres; Blender +Z up; FBX Y-up, -Z forward, bake_space_transform',
           geometry=dict(low_tris_blender=tris, reimport=chk, blocks=len(L['blocks']), joint_gap_m=2 * HG,
                         top_z_m=Z_TOP, lip_z_m=LIP),
           high_poly=dict(grid_step_m=STEP, tris=int((G - 1) ** 2 * 2), source='4096 planar heightfield (1.93 mm/px)'),
           textures=dict(res=RES, uv='planar top-down for tops/bed; wall faces use a corner patch',
                         mask='URP Mask Map: R metallic 0, G AO (heightfield cavity AO), B 0, A smoothness'),
           q18=dict(pct_cyan_teal=q18, mean_rgb_srgb=mean_rgb), sha256=files,
           notes=['FBX links BaseColor + Normal only; assign Mask in Unity material.',
                  'Previous v3 staging folder untouched (Staging/Medallion/).'])
json.dump(man, open(f'{STG}/MANIFEST.json', 'w'), indent=1)
log('staged', STG)

# Overgrowth Kit v3 — Blender 5.x headless authoring
# Roots wrapping masonry, hanging ivy curtains, perimeter canopy trees,
# sunken earth / recessed flagstone beds. No Unity scene edits.
import bpy, bmesh, math, random, os, json, shutil
from mathutils import Vector, Matrix, noise

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/overgrowth_kit_v3'
TEX = f'{ROOT}/textures'
MOD = f'{ROOT}/models'
os.makedirs(MOD, exist_ok=True)
BLEND = f'{ROOT}/TempleEnvironmentKit_overgrowth_v3.blend'
TAU = math.tau
PILLAR_R = 0.56  # inner contact; shaft ~0.50–0.66 m

bpy.ops.wm.read_factory_settings(use_empty=True)


# ---------------------------------------------------------------------------
# Atlas UV helpers
# ---------------------------------------------------------------------------
def uv_bark_trunk(u, v):
    return ((u % 1.0) * 0.98 + 0.01, 0.52 + (v % 1.0) * 0.46)


def uv_bark_root(u, v):
    return ((u % 1.0) * 0.98 + 0.01, 0.02 + (v % 1.0) * 0.46)


def uv_leaf(col, u, t):
    return (col * 0.125 + 0.012 + max(0.0, min(1.0, u)) * 0.101,
            0.51 + max(0.0, min(1.0, t)) * 0.47)


def uv_canopy(ang, h):
    return (ang % 1.0, 0.26 + 0.23 * max(0.0, min(1.0, h)))


def uv_ivy(cell, u, t):
    return (cell * 0.125 + 0.012 + max(0.0, min(1.0, u)) * 0.101,
            0.012 + max(0.0, min(1.0, t)) * 0.226)


def uv_grass(cell, u, t):
    return (0.50 + cell * 0.125 + 0.012 + max(0.0, min(1.0, u)) * 0.101,
            0.012 + max(0.0, min(1.0, t)) * 0.226)


def uv_stone(x, y, s=0.42):
    return ((x * s + 0.5) % 0.96 + 0.02, 0.52 + ((y * s + 0.5) % 0.96) * 0.46)


def uv_loam(x, y, s=0.38):
    return ((x * s + 0.5) % 0.98 + 0.01, 0.26 + ((y * s + 0.5) % 0.96) * 0.23)


def uv_moss(x, y, s=0.5):
    return (((x * s + 0.5) % 0.96) * 0.58 + 0.01, 0.012 + ((y * s + 0.5) % 0.96) * 0.226)


def uv_gravel(x, y, s=0.7):
    return (0.61 + ((x * s + 0.5) % 0.96) * 0.37, 0.012 + ((y * s + 0.5) % 0.96) * 0.226)


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------
def make_pbr(name, base, nrm, mask, alpha_clip=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    img_c = bpy.data.images.load(base)
    tex_c = nt.nodes.new('ShaderNodeTexImage')
    tex_c.image = img_c
    tex_c.image.colorspace_settings.name = 'sRGB'
    nt.links.new(tex_c.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha_clip:
        img_c.alpha_mode = 'CHANNEL_PACKED'
        nt.links.new(tex_c.outputs['Alpha'], bsdf.inputs['Alpha'])
        mat.blend_method = 'CLIP'
        if hasattr(mat, 'shadow_method'):
            mat.shadow_method = 'CLIP'
        mat.alpha_threshold = 0.35
    img_n = bpy.data.images.load(nrm)
    img_n.colorspace_settings.name = 'Non-Color'
    tex_n = nt.nodes.new('ShaderNodeTexImage')
    tex_n.image = img_n
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nmap.inputs['Strength'].default_value = 1.0
    nt.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    img_m = bpy.data.images.load(mask)
    img_m.colorspace_settings.name = 'Non-Color'
    img_m.alpha_mode = 'CHANNEL_PACKED'
    tex_m = nt.nodes.new('ShaderNodeTexImage')
    tex_m.image = img_m
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(tex_m.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
    mat.use_backface_culling = False
    return mat


MAT_WOOD = make_pbr('M_Temple_Overgrowth_Wood',
                    f'{TEX}/ENV_Temple_Overgrowth_Wood_BaseColor.png',
                    f'{TEX}/ENV_Temple_Overgrowth_Wood_Normal.png',
                    f'{TEX}/ENV_Temple_Overgrowth_Wood_Mask.png')
MAT_FOL = make_pbr('M_Temple_Overgrowth_Foliage',
                   f'{TEX}/ENV_Temple_Overgrowth_Foliage_BaseColor.png',
                   f'{TEX}/ENV_Temple_Overgrowth_Foliage_Normal.png',
                   f'{TEX}/ENV_Temple_Overgrowth_Foliage_Mask.png',
                   alpha_clip=True)
MAT_GND = make_pbr('M_Temple_Overgrowth_Ground',
                   f'{TEX}/ENV_Temple_Overgrowth_Ground_BaseColor.png',
                   f'{TEX}/ENV_Temple_Overgrowth_Ground_Normal.png',
                   f'{TEX}/ENV_Temple_Overgrowth_Ground_Mask.png')


# ---------------------------------------------------------------------------
# Mesh builder
# ---------------------------------------------------------------------------
class MB:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.cn = self.bm.verts.layers.float_vector.new('custom_normal')

    def vert(self, co, nrm):
        v = self.bm.verts.new(Vector(co))
        v[self.cn] = Vector(nrm).normalized()
        return v

    def face(self, verts, uvs, mat=0):
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        f.material_index = mat
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f


def vnoise(p, seed):
    return noise.noise(Vector(p) + Vector((seed * 1.17, seed * 0.73, seed * 2.09)))


# ---------------------------------------------------------------------------
# Primitives
# ---------------------------------------------------------------------------
def _push_cyl(p, rmin):
    xy = Vector((p.x, p.y, 0.0))
    L = xy.length
    if 1e-6 < L < rmin:
        xy *= rmin / L
        return Vector((xy.x, xy.y, p.z))
    return p


def add_tube(mb, points, radii, sides=8, uv_fn=uv_bark_root, mat=0, v_tile=3.2,
             ridge=0.10, flatten_u=1.0, flatten_w=1.0, hug_r=None, hug_axes=None):
    """Tapered tube. flatten_u < 1 squashes against a surface. hug_r clamps inside a cylinder."""
    n = len(points)
    rings = []
    for i, p in enumerate(points):
        if i == 0:
            tang = (points[1] - points[0]).normalized()
        elif i == n - 1:
            tang = (points[-1] - points[-2]).normalized()
        else:
            tang = (points[i + 1] - points[i - 1]).normalized()
        # radial from pillar / origin when hugging a cylinder
        radial = Vector((p.x, p.y, 0.0))
        if radial.length > 1e-5:
            ref = radial.normalized()
        else:
            ref = Vector((0, 0, 1)) if abs(tang.dot(Vector((0, 0, 1)))) < 0.92 else Vector((1, 0, 0))
        u = tang.cross(ref)
        if u.length < 1e-5:
            u = tang.cross(Vector((0, 0, 1)))
        u.normalize()
        w = tang.cross(u).normalized()
        # prefer `w` pointing outward from pillar
        if Vector((p.x, p.y, 0)).dot(w) < 0:
            w = -w
            u = -u
        ring = []
        r = radii[i]
        for k in range(sides):
            a = TAU * k / sides
            # bark ridges
            rr = r * (1.0 + ridge * math.sin(a * 4.0 + i * 0.35))
            off = u * math.cos(a) * flatten_u + w * math.sin(a) * flatten_w
            pos = p + off * rr
            if hug_r is not None:
                pos = _push_cyl(pos, hug_r)
            if hug_axes == 'corner':
                pos = Vector((max(pos.x, 0.035), max(pos.y, 0.035), pos.z))
            nrm = off.normalized() if off.length > 1e-6 else w
            ring.append(mb.vert(pos, nrm))
        rings.append(ring)
    for i in range(n - 1):
        v0 = i / max(1, n - 1) * v_tile
        v1 = (i + 1) / max(1, n - 1) * v_tile
        for k in range(sides):
            k2 = (k + 1) % sides
            mb.face(
                [rings[i][k], rings[i][k2], rings[i + 1][k2], rings[i + 1][k]],
                [uv_fn(k / sides, v0), uv_fn((k + 1) / sides, v0),
                 uv_fn((k + 1) / sides, v1), uv_fn(k / sides, v1)],
                mat=mat,
            )


def add_knot(mb, pos, radius, seed, mat=0):
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=1, radius=radius)
    for tv in tmp.verts:
        d = tv.co.copy()
        sc = 1.0 + 0.22 * vnoise(d * 3.1, seed)
        p = Vector(pos) + Vector((d.x * sc * 1.15, d.y * sc * 0.85, d.z * sc * 0.90))
        tv.co = p
    newv = {}
    for tv in tmp.verts:
        nrm = (tv.co - Vector(pos)).normalized()
        newv[tv.index] = mb.vert(tv.co, nrm)
    for tf in tmp.faces:
        ids = [l.vert.index for l in tf.loops]
        uvs = [uv_bark_root((i % 3) * 0.3, (i // 3) * 0.3) for i in range(len(ids))]
        mb.face([newv[i] for i in ids], uvs, mat=mat)
    tmp.free()


def helix_path(r, z0, z1, th0, twist, n, r_fn=None, z_fn=None, jitter=0.0, seed=0):
    rng = random.Random(seed)
    pts = []
    for i in range(n):
        t = i / (n - 1)
        th = th0 + twist * t
        rr = (r_fn(t) if r_fn else r) + (rng.uniform(-jitter, jitter) if jitter else 0.0)
        zz = z0 + (z1 - z0) * (z_fn(t) if z_fn else t)
        # slight organic wobble
        wob = 0.035 * vnoise((math.cos(th) * 2, math.sin(th) * 2, zz * 0.4), seed)
        pts.append(Vector(((rr + wob) * math.cos(th), (rr + wob) * math.sin(th), zz)))
    return pts


def lerp_r(a, b, t, gamma=1.0):
    return a + (b - a) * (t ** gamma)


def add_lobe(mb, center, radii, seed, subdiv=3, amp=0.22, up_bias=0.48, mat=1, z_clamp=None):
    """Flattened organic canopy mass. Custom normals = radial + up bias (painterly wrap)."""
    c = Vector(center)
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1.0)
    info = {}
    for tv in tmp.verts:
        d = tv.co.copy()
        n = vnoise(d * 1.35, seed) * amp + vnoise(d * 3.1, seed + 9) * amp * 0.45 + vnoise(d * 6.2, seed + 3) * amp * 0.18
        sc = 1.0 + n
        p = c + Vector((d.x * radii[0] * sc, d.y * radii[1] * sc, d.z * radii[2] * sc))
        if z_clamp is not None and p.z < z_clamp:
            p.z = z_clamp + (p.z - z_clamp) * 0.12
        grad = Vector((d.x / radii[0], d.y / radii[1], d.z / radii[2])).normalized()
        nrm = (grad * (1.0 - up_bias) + Vector((0, 0, 1)) * up_bias).normalized()
        info[tv.index] = (p, nrm, d)
    zs = [v[0].z for v in info.values()]
    z0, z1 = min(zs), max(zs)
    newv = {i: mb.vert(p, n) for i, (p, n, d) in info.items()}
    for tf in tmp.faces:
        ids = [l.vert.index for l in tf.loops]
        uvs = []
        for i in ids:
            p, n, d = info[i]
            ang = math.atan2(d.y, d.x) / TAU + 0.5
            h = (p.z - z0) / max(1e-4, z1 - z0)
            uvs.append(uv_canopy(ang, h))
        mb.face([newv[i] for i in ids], uvs, mat=mat)
    tmp.free()
    return c, Vector(radii)


def add_lobe_thatch(mb, center, radii, count, seed, size=(0.85, 1.15)):
    """Large overlapping drooping plates that hide the hull silhouette."""
    c = Vector(center)
    rng = random.Random(seed)
    golden = (1 + math.sqrt(5)) / 2
    for i in range(count):
        th = TAU * i / golden
        phi = 0.40 + 0.95 * ((i + 0.5) / count)
        dx = math.sin(phi) * math.cos(th)
        dy = math.sin(phi) * math.sin(th)
        dz = math.cos(phi)
        d = Vector((dx, dy, dz)).normalized()
        pos = c + Vector((d.x * radii[0] * 0.88, d.y * radii[1] * 0.88, d.z * radii[2] * 0.80))
        down = (Vector((0, 0, -1)) * 0.72 + d * 0.28).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = Vector((1, 0, 0))
        side.normalize()
        out = (d * 0.55 + Vector((0, 0, 1)) * 0.45).normalized()
        add_droop_plate(
            mb, pos, down, side, out,
            w=size[0] * rng.uniform(0.75, 1.2),
            length=size[1] * rng.uniform(0.8, 1.25),
            col=rng.choice(range(8)), uv_fn=uv_leaf, mat=1,
            nrm=out, cup=0.10,
        )


def add_droop_plate(mb, origin, down, side, out, w, length, col, uv_fn, mat=1, nrm=None, cup=0.05):
    """Soft painterly leaf cluster plate. Droops along `down`, cups toward `out`."""
    down = down.normalized()
    side = side.normalized()
    out = out.normalized()
    nrm = (nrm if nrm is not None else (out * 0.55 + Vector((0, 0, 1)) * 0.45)).normalized()
    grid = []
    for row, t in enumerate((0.0, 0.55, 1.0)):
        rowv = []
        for s in (-0.5, 0.0, 0.5):
            # taper toward tip
            ww = w * (1.0 - 0.35 * t)
            lift = cup * (1.0 - (s * 2) ** 2) * math.sin(math.pi * t)
            p = origin + down * (length * t) + side * (ww * s) + out * lift
            rowv.append(mb.vert(p, nrm))
        grid.append(rowv)
    for r in range(2):
        for c in range(2):
            u0, t0 = c * 0.5, r * 0.5
            u1, t1 = (c + 1) * 0.5, (r + 1) * 0.5
            mb.face(
                [grid[r][c], grid[r + 1][c], grid[r + 1][c + 1], grid[r][c + 1]],
                [uv_fn(col, u0, t0), uv_fn(col, u0, t1), uv_fn(col, u1, t1), uv_fn(col, u1, t0)],
                mat=mat,
            )


def add_hanging_cluster(mb, pos, seed, size=0.28, cols=(0, 1, 2, 3), mat=1, uv_fn=uv_leaf):
    rng = random.Random(seed)
    down = Vector((rng.uniform(-0.18, 0.18), rng.uniform(-0.12, 0.28), -1.0)).normalized()
    # side perpendicular to down
    ref = Vector((1, 0, 0)) if abs(down.dot(Vector((1, 0, 0)))) < 0.85 else Vector((0, 1, 0))
    side = down.cross(ref).normalized()
    out = side.cross(down).normalized()
    n = rng.randint(3, 5)
    for i in range(n):
        a = (i / n) * TAU + rng.uniform(-0.2, 0.2)
        s = (side * math.cos(a) + out * math.sin(a) * 0.55).normalized()
        o = (out * 0.7 + Vector((0, 0, 0.3))).normalized()
        off = s * size * rng.uniform(0.05, 0.22)
        add_droop_plate(
            mb, pos + off, down, s, o,
            w=size * rng.uniform(0.45, 0.75),
            length=size * rng.uniform(0.85, 1.25),
            col=rng.choice(cols),
            uv_fn=uv_fn, mat=mat,
            nrm=(o * 0.4 + Vector((0, 0, 1)) * 0.6),
            cup=size * 0.12,
        )


def add_grass_tuft(mb, pos, seed, scale=1.0):
    rng = random.Random(seed)
    n = rng.randint(5, 8)
    for i in range(n):
        ang = i * TAU / n + rng.uniform(-0.25, 0.25)
        lean = Vector((math.cos(ang), math.sin(ang), 0))
        h = rng.uniform(0.07, 0.15) * scale
        w = rng.uniform(0.010, 0.022) * scale
        down = (Vector((0, 0, 1)) + lean * rng.uniform(0.15, 0.55)).normalized()
        side = lean.cross(Vector((0, 0, 1))).normalized()
        nrm = (Vector((0, 0, 1)) * 0.7 + lean * 0.3).normalized()
        col = rng.choice((0, 1, 2, 3))
        p0 = pos + lean * rng.uniform(0.0, 0.018)
        v00 = mb.vert(p0 - side * w * 0.5, nrm)
        v01 = mb.vert(p0 + side * w * 0.5, nrm)
        tip = p0 + down * h
        v10 = mb.vert(tip - side * w * 0.15, nrm)
        v11 = mb.vert(tip + side * w * 0.15, nrm)
        mb.face([v00, v10, v11, v01],
                [uv_grass(col, 0.0, 0.0), uv_grass(col, 0.0, 1.0),
                 uv_grass(col, 1.0, 1.0), uv_grass(col, 1.0, 0.0)], mat=1)


def add_ivy_leaf(mb, base, aim, nrm, size, cell, soft=None, cup=0.07):
    a = aim.normalized()
    n = nrm.normalized()
    s = a.cross(n)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    a = n.cross(s).normalized()
    soft = (soft if soft is not None else n)
    contour = [
        (0.0, 0.0), (0.34, 0.14), (0.58, 0.42), (0.22, 0.62),
        (0.0, 1.0), (-0.22, 0.62), (-0.58, 0.42), (-0.34, 0.14),
    ]

    def mk(x, y):
        lift = cup * size * (1.0 - abs(x) * 1.4) * math.sin(math.pi * min(1.0, max(0.0, y)))
        p = base + a * (y * size) + s * (x * size * 0.95) + n * lift
        return mb.vert(p, (soft * 0.65 + n * 0.35).normalized())

    cen = mk(0.0, 0.40)
    peri = [mk(x, y) for x, y in contour]
    cuv = uv_ivy(cell, 0.5, 0.40)
    for i in range(len(peri)):
        j = (i + 1) % len(peri)
        mb.face(
            [cen, peri[j], peri[i]],
            [cuv, uv_ivy(cell, contour[j][0] * 0.5 + 0.5, contour[j][1]),
             uv_ivy(cell, contour[i][0] * 0.5 + 0.5, contour[i][1])],
            mat=1,
        )


def add_slab(mb, cx, cy, z_bot, z_top, radius, n=6, seed=0, rot=0.0):
    rng = random.Random(seed)
    top, bot = [], []
    pts = []
    for i in range(n):
        a = rot + TAU * i / n + rng.uniform(-0.18, 0.18)
        r = radius * rng.uniform(0.72, 1.18)
        x = cx + r * math.cos(a)
        y = cy + r * math.sin(a)
        zt = z_top + rng.uniform(-0.010, 0.008)
        # slight undercut so the paver reads as a slab, not a prism
        xb = cx + (x - cx) * 0.94
        yb = cy + (y - cy) * 0.94
        pts.append((x, y, zt, z_bot, xb, yb))
        nrm_t = Vector((0, 0, 1))
        top.append(mb.vert((x, y, zt), nrm_t))
        bot.append(mb.vert((xb, yb, z_bot), Vector((0, 0, -1))))
    mb.face(list(reversed(top)), [uv_stone(p[0], p[1]) for p in reversed(pts)], mat=2)
    mb.face(bot, [uv_stone(p[0], p[1]) for p in pts], mat=2)
    for i in range(n):
        j = (i + 1) % n
        side_n = Vector((pts[j][1] - pts[i][1], pts[i][0] - pts[j][0], 0))
        if side_n.length > 1e-6:
            side_n.normalize()
        # re-set? keep existing vert normals; UVs along height
        mb.face(
            [top[i], top[j], bot[j], bot[i]],
            [uv_stone(pts[i][0], pts[i][1]), uv_stone(pts[j][0], pts[j][1]),
             uv_stone(pts[j][4], pts[j][5]), uv_stone(pts[i][4], pts[i][5])],
            mat=2,
        )
    return pts


def add_earth_grid(mb, x0, x1, y0, y1, nx, ny, z_fn, uv_fn, mat=2):
    verts = [[None] * (nx + 1) for _ in range(ny + 1)]
    for j in range(ny + 1):
        ty = j / ny
        y = y0 + (y1 - y0) * ty
        for i in range(nx + 1):
            tx = i / nx
            x = x0 + (x1 - x0) * tx
            z = z_fn(x, y, tx, ty)
            nrm = Vector((0, 0, 1))
            verts[j][i] = mb.vert((x, y, z), nrm)
    for j in range(ny):
        for i in range(nx):
            v00, v10 = verts[j][i], verts[j][i + 1]
            v11, v01 = verts[j + 1][i + 1], verts[j + 1][i]
            x = x0 + (x1 - x0) * (i / nx)
            y = y0 + (y1 - y0) * (j / ny)
            dx = (x1 - x0) / nx
            dy = (y1 - y0) / ny
            mb.face(
                [v00, v10, v11, v01],
                [uv_fn(x, y), uv_fn(x + dx, y), uv_fn(x + dx, y + dy), uv_fn(x, y + dy)],
                mat=mat,
            )


# ---------------------------------------------------------------------------
# Finalize + FBX
# ---------------------------------------------------------------------------
STATS = {}


def finalize(mb, name, materials):
    bm = mb.bm
    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()
    normals = [Vector(v[mb.cn]) for v in bm.verts]
    flip = [f for f in bm.faces if f.normal.dot(sum((Vector(v[mb.cn]) for v in f.verts), Vector())) < -0.1]
    if flip:
        bmesh.ops.reverse_faces(bm, faces=flip)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    try:
        me.normals_split_custom_set_from_vertices([tuple(n) for n in normals])
    except Exception as e:
        print('custom normals skipped', name, e)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for m in materials:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1, 1, 1)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    fbx = f'{MOD}/{name}.fbx'
    bpy.ops.export_scene.fbx(
        filepath=fbx,
        use_selection=True,
        object_types={'MESH'},
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        use_triangles=True,
        path_mode='COPY',
        embed_textures=False,
    )
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    stat = dict(
        tris=len(me.polygons),
        verts=len(me.vertices),
        bbox_min=[round(min(c[i] for c in bb), 3) for i in range(3)],
        bbox_max=[round(max(c[i] for c in bb), 3) for i in range(3)],
        dims=[round(max(c[i] for c in bb) - min(c[i] for c in bb), 3) for i in range(3)],
        materials=[m.name for m in materials],
        fbx=fbx,
    )
    STATS[name] = stat
    print(f"Exported {name}: {stat['tris']} tris | dims {stat['dims']} | bbox {stat['bbox_min']} .. {stat['bbox_max']}")
    return ob


# ===========================================================================
# 1. ROOT CLAW — pillar wrap
#    Inner surface hugs R=0.56 m shaft. Origin = pillar centre, z=0 floor.
# ===========================================================================
def build_root_pillar():
    mb = MB()
    specs = [
        # r_center, z0, z1, th0, twist, n, r0, r1, sides, seed
        (PILLAR_R + 0.13, 0.00, 3.20, 0.20,  2.05, 20, 0.16, 0.055, 10, 11),
        (PILLAR_R + 0.12, 0.00, 2.95, 1.65, -1.85, 18, 0.15, 0.048, 10, 12),
        (PILLAR_R + 0.125, 0.00, 3.40, 3.35,  1.55, 20, 0.14, 0.046, 9, 13),
        (PILLAR_R + 0.11,  0.00, 2.55, 4.85, -2.20, 16, 0.13, 0.042, 9, 14),
        (PILLAR_R + 0.12,  0.00, 2.20, 2.50,  2.40, 14, 0.12, 0.040, 8, 15),
        (PILLAR_R + 0.09,  0.25, 3.05, 0.85, -1.35, 16, 0.075, 0.028, 7, 16),
        (PILLAR_R + 0.085, 0.15, 2.70, 5.35,  1.75, 14, 0.065, 0.024, 7, 17),
        (PILLAR_R + 0.10,  0.00, 1.85, 6.10,  1.10, 12, 0.11, 0.038, 8, 18),
    ]
    for r, z0, z1, th0, tw, n, r0, r1, sides, sd in specs:
        pts = helix_path(r, z0, z1, th0, tw, n, jitter=0.018, seed=sd)
        flare = Vector((math.cos(th0), math.sin(th0), 0)) * 0.38
        pts[0] = Vector((pts[0].x, pts[0].y, -0.02)) + flare * 0.85
        if len(pts) > 2:
            pts[1] = pts[1] + flare * 0.40
            pts[2] = pts[2] + flare * 0.12
        rads = [lerp_r(r0, r1, i / (n - 1), 0.80) for i in range(n)]
        add_tube(mb, pts, rads, sides=sides, uv_fn=uv_bark_root, mat=0,
                 v_tile=4.0, ridge=0.16, flatten_u=0.70, flatten_w=1.25, hug_r=PILLAR_R + 0.01)
        # knots at mid-wrap
        add_knot(mb, pts[n // 3], r0 * 0.85, sd + 3)
        if n > 10:
            add_knot(mb, pts[2 * n // 3], r0 * 0.55, sd + 7)

    rng = random.Random(21)
    for k in range(6):
        th = rng.uniform(0, TAU)
        z_a = rng.uniform(0.5, 1.7)
        z_b = z_a + rng.uniform(0.55, 1.2)
        r_a = PILLAR_R + rng.uniform(0.08, 0.18)
        r_b = PILLAR_R + rng.uniform(0.05, 0.11)
        pts = helix_path(r_a, z_a, z_b, th, rng.uniform(-1.3, 1.3), 9,
                         r_fn=lambda t, a=r_a, b=r_b: a + (b - a) * t, seed=30 + k)
        rads = [lerp_r(0.038, 0.016, i / 8) for i in range(9)]
        add_tube(mb, pts, rads, sides=6, uv_fn=uv_bark_root, mat=0,
                 v_tile=2.5, ridge=0.12, flatten_u=0.75, flatten_w=1.15, hug_r=PILLAR_R + 0.01)

    return finalize(mb, 'ENV_Temple_Root_Claw_Pillar', [MAT_WOOD])


# ===========================================================================
# 2. ROOT CLAW — wall corner clamp
#    Walls occupy X<=0 and Y<=0. Courtyard +X/+Y. Origin at inner corner.
# ===========================================================================
def build_root_corner():
    mb = MB()
    rng = random.Random(41)

    def wall_path(along='x', z0=0.0, z1=2.6, s0=0.15, s1=1.6, off=0.10, n=14, seed=0):
        pts = []
        for i in range(n):
            t = i / (n - 1)
            s = s0 + (s1 - s0) * t
            z = z0 + (z1 - z0) * (t ** 0.88)
            wob = 0.035 * vnoise((s * 1.4, off, z * 0.7), seed)
            pulse = 0.04 * math.sin(t * 6.5 + seed)
            if along == 'x':
                pts.append(Vector((s, max(0.05, off + wob + pulse), z)))
            else:
                pts.append(Vector((max(0.05, off + wob + pulse), s, z)))
        return pts

    # thick strangler mass climbing the corner join
    main = []
    for i in range(18):
        t = i / 17
        z = -0.02 + 2.90 * t
        r = 0.18 + 0.11 * math.sin(t * math.pi)
        th = 0.78 + 0.28 * math.sin(t * 2.8)
        main.append(Vector((max(0.07, r * math.cos(th)), max(0.07, r * math.sin(th)), z)))
    add_tube(mb, main, [lerp_r(0.17, 0.055, i / 17, 0.75) for i in range(18)],
             sides=10, uv_fn=uv_bark_root, mat=0, v_tile=4.2, ridge=0.18,
             flatten_u=0.8, flatten_w=1.15, hug_axes='corner')
    add_knot(mb, main[4], 0.12, 90)
    add_knot(mb, main[10], 0.09, 91)

    # claws along +X wall (Y~0.10) — stay close to the plane, climb up
    for k, (s0, s1, z1, r0) in enumerate(((0.08, 1.95, 2.55, 0.12),
                                          (0.18, 1.55, 2.05, 0.10),
                                          (0.40, 2.20, 1.35, 0.085))):
        pts = wall_path('x', 0.0, z1, s0, s1, off=0.09 + 0.04 * k, n=14, seed=50 + k)
        pts[0] = Vector((0.12, 0.28, -0.02))
        pts[1] = Vector((pts[2].x * 0.45, 0.18, 0.12))
        add_tube(mb, pts, [lerp_r(r0, r0 * 0.32, i / 13) for i in range(14)],
                 sides=8, uv_fn=uv_bark_root, mat=0, v_tile=3.5, ridge=0.14,
                 hug_axes='corner')
        add_knot(mb, pts[5], r0 * 0.7, 52 + k)

    # claws along +Y wall
    for k, (s0, s1, z1, r0) in enumerate(((0.10, 1.80, 2.70, 0.115),
                                          (0.22, 1.50, 1.85, 0.09),
                                          (0.35, 1.95, 1.15, 0.075))):
        pts = wall_path('y', 0.0, z1, s0, s1, off=0.09 + 0.035 * k, n=14, seed=60 + k)
        pts[0] = Vector((0.30, 0.10, -0.02))
        pts[1] = Vector((0.18, pts[2].y * 0.45, 0.10))
        add_tube(mb, pts, [lerp_r(r0, r0 * 0.32, i / 13) for i in range(14)],
                 sides=8, uv_fn=uv_bark_root, mat=0, v_tile=3.5, ridge=0.14,
                 hug_axes='corner')

    for k in range(4):
        along = 'x' if k % 2 == 0 else 'y'
        pts = wall_path(along, rng.uniform(0.3, 1.1), rng.uniform(1.9, 2.8),
                        rng.uniform(0.25, 0.7), rng.uniform(1.3, 2.0),
                        off=0.07, n=10, seed=70 + k)
        add_tube(mb, pts, [lerp_r(0.038, 0.014, i / 9) for i in range(10)],
                 sides=6, uv_fn=uv_bark_root, mat=0, v_tile=2.4, ridge=0.10,
                 hug_axes='corner')

    return finalize(mb, 'ENV_Temple_Root_Claw_Corner', [MAT_WOOD])


# ===========================================================================
# 3–4. CASCADING IVY CURTAINS
#    Pivot at TOP (z=0). Geometry hangs in −Z. +Y = away from wall (courtyard).
#    No horizontal shelf. Stems start from a thin mortar-joint cluster.
# ===========================================================================
def _hanging_stem(x0, y0, drop, sway, n, seed):
    rng = random.Random(seed)
    pts = []
    freq = rng.uniform(1.1, 2.3)
    phase = rng.uniform(0, TAU)
    for i in range(n):
        t = i / (n - 1)
        x = x0 + sway * math.sin(t * math.pi * freq + phase) * (t ** 0.65)
        y = y0 + 0.16 * (t ** 1.55) + 0.04 * math.sin(t * 4 + phase)
        z = -drop * (t ** 1.04)
        pts.append(Vector((x, y, z)))
    return pts


def build_vine_curtain(name, width, drop, n_stems, dense=True):
    mb = MB()
    rng = random.Random(111 if name.endswith('_A') else 222)
    xs = [(-width * 0.5) + width * i / max(1, n_stems - 1) for i in range(n_stems)]

    # Cornice foliage masses — painterly hanging clumps, not a shelf
    n_mass = 4 if dense else 3
    for i in range(n_mass):
        t = (i + 0.5) / n_mass
        x = -width * 0.42 + width * 0.84 * t + rng.uniform(-0.08, 0.08)
        add_lobe(mb, (x, 0.12, -0.28),
                 (0.38 if dense else 0.28, 0.16, 0.32),
                 seed=80 + i, subdiv=2, amp=0.20, up_bias=0.35, mat=1, z_clamp=None)
        add_lobe_thatch(mb, (x, 0.12, -0.28),
                        (0.38 if dense else 0.28, 0.16, 0.32),
                        count=8, seed=90 + i, size=(0.32, 0.48))

    for i, x in enumerate(xs):
        nub = [Vector((x, 0.03, 0.02)), Vector((x, 0.06, -0.04)), Vector((x, 0.08, -0.14))]
        add_tube(mb, nub, [0.016, 0.012, 0.009], sides=5, uv_fn=uv_bark_root, mat=0, v_tile=1.2, ridge=0.08)
        d = drop * rng.uniform(0.70, 1.0)
        pts = _hanging_stem(x, 0.08, d, rng.uniform(0.05, 0.16), 12, 200 + i)
        r0 = rng.uniform(0.010, 0.016) if dense else rng.uniform(0.007, 0.012)
        add_tube(mb, pts, [lerp_r(r0, r0 * 0.30, k / 11) for k in range(12)],
                 sides=5, uv_fn=uv_bark_root, mat=0, v_tile=2.8, ridge=0.08)
        n_cl = 14 if dense else 9
        for k in range(n_cl):
            t = (k + 0.15) / n_cl
            if t > 0.93:
                continue
            idx = min(len(pts) - 2, int(t * (len(pts) - 1)))
            p = pts[idx]
            # larger overlapping plates near the top so they read as a curtain
            sz = (0.38 if dense else 0.30) * (1.25 - 0.70 * t) * rng.uniform(0.85, 1.2)
            add_hanging_cluster(mb, p, seed=300 + i * 20 + k, size=sz,
                                cols=(0, 1, 2, 3, 4, 5, 6, 7), uv_fn=uv_leaf)
            if t < 0.45:
                add_ivy_leaf(mb, p + Vector((rng.uniform(-0.04, 0.04), 0.02, 0.0)),
                             aim=Vector((rng.uniform(-0.25, 0.25), 0.15, -1.0)),
                             nrm=Vector((0, 1, 0.15)),
                             size=sz * 0.95,
                             cell=rng.choice((0, 1, 2, 3)),
                             soft=Vector((0, 0.35, 0.9)))
    return finalize(mb, name, [MAT_WOOD, MAT_FOL])


# ===========================================================================
# 5–6. PERIMETER CANOPY TREES
#    Origin at trunk base. +Y = courtyard lean. Designed for r >= 18 m.
# ===========================================================================
def _branch(mb, a, b, r0, r1, n=8, sides=7):
    pts = []
    for i in range(n):
        t = i / (n - 1)
        # slight sag
        p = a.lerp(b, t)
        p = p + Vector((0, 0, -0.08 * math.sin(t * math.pi)))
        pts.append(p)
    add_tube(mb, pts, [lerp_r(r0, r1, i / (n - 1), 0.9) for i in range(n)],
             sides=sides, uv_fn=uv_bark_trunk, mat=0, v_tile=2.4, ridge=0.12)


def _tree(name, height, lean_y, trunk_r, lobes, seed):
    mb = MB()
    rng = random.Random(seed)
    n = 14
    trunk = []
    for i in range(n):
        t = i / (n - 1)
        z = height * 0.40 * t
        y = lean_y * 0.32 * (t ** 1.15)
        x = 0.10 * math.sin(t * math.pi) + 0.04 * math.sin(t * 3.1)
        wob = Vector((vnoise((x, y, z * 0.25), seed) * 0.05,
                      vnoise((x + 3, y, z * 0.25), seed) * 0.04, 0))
        trunk.append(Vector((x, y, max(0.0, z))) + wob)
    # root flare at the base
    rads = [lerp_r(trunk_r * 1.45, trunk_r * 0.50, i / (n - 1), 0.75) for i in range(n)]
    add_tube(mb, trunk, rads, sides=10, uv_fn=uv_bark_trunk, mat=0, v_tile=5.0, ridge=0.14)
    # surface roots
    for k in range(4):
        ang = k * TAU / 4 + rng.uniform(-0.2, 0.2)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        pts = [
            d * 0.05 + Vector((0, 0, 0.02)),
            d * 0.32 + Vector((0, 0, 0.06)),
            d * 0.55 + Vector((0, 0, 0.02)),
        ]
        add_tube(mb, pts, [0.07, 0.045, 0.02], sides=6, uv_fn=uv_bark_root, mat=0, v_tile=1.6, ridge=0.12)

    # two-level fork: 3 primaries, then secondaries into lobes
    fork = trunk[-1]
    n_prim = 3
    prims = []
    for i in range(n_prim):
        a = -0.5 + i * 0.5 + rng.uniform(-0.12, 0.12)
        end = fork + Vector((math.sin(a) * 0.85, lean_y * 0.22 + rng.uniform(-0.1, 0.2), height * 0.16))
        r0 = trunk_r * rng.uniform(0.32, 0.42)
        _branch(mb, fork, end, r0, r0 * 0.55, n=6, sides=7)
        prims.append(end)

    for i, (lc, rad, _) in enumerate(lobes):
        parent = prims[i % n_prim]
        meet = Vector((lc[0], lc[1], lc[2] - rad[2] * 0.50))
        r0 = trunk_r * rng.uniform(0.18, 0.28)
        _branch(mb, parent, meet, r0, r0 * 0.40, n=6, sides=6)
        add_lobe(mb, lc, rad, seed=seed + 10 + i, subdiv=3, amp=0.22, up_bias=0.50, mat=1)
        add_lobe_thatch(mb, lc, rad, count=16, seed=seed + 40 + i,
                        size=(0.70 * (rad[0] / 1.8), 0.95 * (rad[0] / 1.8)))
        # extra hanging clusters on the underside only
        for k in range(6):
            th = TAU * k / 6 + rng.uniform(-0.15, 0.15)
            p = Vector(lc) + Vector((math.cos(th) * rad[0] * 0.7,
                                     math.sin(th) * rad[1] * 0.7,
                                     -rad[2] * 0.55))
            add_hanging_cluster(mb, p, seed=seed + 80 + i * 10 + k,
                                size=0.55 * (rad[0] / 1.8),
                                cols=tuple(range(8)), uv_fn=uv_leaf)
    return finalize(mb, name, [MAT_WOOD, MAT_FOL])


def build_tree_a():
    # ~11.8 m, slight +Y lean, 5 pancake canopy masses
    lobes = [
        ((0.15, 1.55, 8.6), (2.05, 1.85, 0.95), 0),
        ((-1.55, 1.05, 7.7), (1.55, 1.40, 0.78), 0),
        ((1.70, 1.20, 8.0), (1.60, 1.45, 0.80), 0),
        ((0.05, 2.35, 9.6), (1.45, 1.25, 0.70), 0),
        ((-0.20, 0.55, 7.2), (1.35, 1.20, 0.62), 0),
    ]
    return _tree('ENV_Temple_Tree_Canopy_A', height=11.8, lean_y=1.35,
                 trunk_r=0.38, lobes=lobes, seed=101)


def build_tree_b():
    # shorter, wider, more lean — spreading ruin tree
    lobes = [
        ((0.25, 1.85, 6.6), (2.35, 2.05, 0.88), 0),
        ((-1.80, 1.35, 5.9), (1.70, 1.55, 0.72), 0),
        ((1.90, 1.50, 6.1), (1.75, 1.50, 0.70), 0),
        ((0.10, 2.70, 7.4), (1.55, 1.35, 0.65), 0),
        ((-0.40, 0.70, 5.4), (1.40, 1.25, 0.58), 0),
        ((0.90, 2.10, 7.0), (1.20, 1.10, 0.52), 0),
    ]
    return _tree('ENV_Temple_Tree_Canopy_B', height=9.4, lean_y=1.85,
                 trunk_r=0.34, lobes=lobes, seed=202)


# ===========================================================================
# 7–8. SUNKEN EARTH / RECESSED FLAGSTONE BEDS
#    Stone rim top ~0.26 m (near floor-tile 0.30 m). Earth recessed ~0.12 m.
#    Grass tufts nest in earth and joints — never sprout from slab faces.
# ===========================================================================
def build_earth_a():
    mb = MB()
    rng = random.Random(301)
    z_rim = 0.24
    z_earth_edge = 0.15
    z_earth_c = 0.10
    thick = 0.085
    # border flagstones around a ~2.0 m module
    border = [
        # (cx, cy, radius, n, seed)
        (-0.70, -0.72, 0.38, 6, 1), (0.00, -0.80, 0.42, 5, 2), (0.72, -0.70, 0.36, 6, 3),
        (0.82, -0.05, 0.40, 6, 4), (0.70, 0.70, 0.38, 5, 5), (0.02, 0.82, 0.44, 6, 6),
        (-0.72, 0.68, 0.37, 6, 7), (-0.84, 0.02, 0.40, 5, 8),
        (-0.40, -0.78, 0.30, 5, 9), (0.40, 0.78, 0.32, 5, 10),
    ]
    for cx, cy, rad, n, sd in border:
        zt = z_rim + rng.uniform(-0.016, 0.012)
        add_slab(mb, cx, cy, zt - thick, zt, rad, n=n, seed=400 + sd)

    def z_earth(x, y, tx, ty):
        # concave basin
        dx, dy = (tx - 0.5) * 2, (ty - 0.5) * 2
        r2 = min(1.0, dx * dx + dy * dy)
        z = z_earth_c + (z_earth_edge - z_earth_c) * (r2 ** 0.8)
        z += 0.012 * vnoise((x * 2.2, y * 2.2, 0.4), 9)
        return z

    add_earth_grid(mb, -1.05, 1.05, -1.10, 1.15, 10, 10, z_earth, uv_loam, mat=2)
    # moss patches in the basin
    add_earth_grid(mb, -0.34, 0.30, -0.28, 0.32, 4, 4,
                   lambda x, y, tx, ty: z_earth(x, y, (x + 1.05) / 2.10, (y + 1.10) / 2.25) + 0.006,
                   uv_moss, mat=2)

    # nested grass tufts in earth (not on stone)
    tuft_pts = [
        (-0.22, -0.18), (0.16, -0.24), (0.28, 0.12), (-0.10, 0.26),
        (0.08, 0.02), (-0.30, 0.08), (0.20, -0.06), (-0.06, -0.30),
        (0.04, 0.18), (-0.18, 0.20),
    ]
    for i, (x, y) in enumerate(tuft_pts):
        z = z_earth(x, y, (x + 1.05) / 2.10, (y + 1.10) / 2.25)
        add_grass_tuft(mb, Vector((x, y, z)), seed=500 + i, scale=rng.uniform(0.85, 1.2))

    # a few broken chips sitting IN the earth
    for i, (x, y, r) in enumerate(((-0.12, 0.10, 0.11), (0.22, -0.14, 0.09), (-0.28, -0.22, 0.08))):
        z = z_earth(x, y, (x + 1.05) / 2.10, (y + 1.10) / 2.25)
        add_slab(mb, x, y, z - 0.008, z + 0.022, r, n=5, seed=600 + i)

    return finalize(mb, 'ENV_Temple_EarthBed_A', [MAT_WOOD, MAT_FOL, MAT_GND])


def build_earth_b():
    """Longer perimeter bed ~3.2 x 1.55 m. Open on +Y (earth bleeds toward wall)."""
    mb = MB()
    rng = random.Random(302)
    z_rim = 0.24
    thick = 0.085
    # flagstones on −Y, −X, +X; +Y is open earth
    border = [
        (-1.25, -0.58, 0.40, 6, 1), (-0.55, -0.68, 0.44, 5, 2), (0.20, -0.64, 0.40, 6, 3),
        (0.90, -0.60, 0.38, 5, 4), (1.35, -0.48, 0.36, 6, 5),
        (-1.40, 0.05, 0.38, 6, 6), (-1.32, 0.50, 0.34, 5, 7),
        (1.42, 0.02, 0.40, 6, 8), (1.30, 0.48, 0.34, 5, 9),
        (-0.90, -0.62, 0.30, 5, 10), (0.55, -0.66, 0.32, 5, 11),
    ]
    for cx, cy, rad, n, sd in border:
        zt = z_rim + rng.uniform(-0.014, 0.010)
        add_slab(mb, cx, cy, zt - thick, zt, rad, n=n, seed=700 + sd)

    def z_earth(x, y, tx, ty):
        # lower toward +Y (open side) and center
        basin = ((tx - 0.5) * 2) ** 2 * 0.4 + (1.0 - ty) * 0.35
        z = 0.07 + 0.08 * basin
        z += 0.014 * vnoise((x * 1.6, y * 1.8, 0.5), 11)
        return z

    add_earth_grid(mb, -1.15, 1.15, -0.42, 0.72, 12, 7, z_earth, uv_loam, mat=2)
    add_earth_grid(mb, -0.70, 0.65, 0.05, 0.62, 6, 4,
                   lambda x, y, tx, ty: z_earth(x, y, (x + 1.15) / 2.30, (y + 0.42) / 1.14) + 0.005,
                   uv_moss, mat=2)

    tufts = [
        (-0.80, 0.22), (-0.40, 0.40), (-0.10, 0.18), (0.25, 0.36),
        (0.60, 0.22), (0.90, 0.42), (-0.20, 0.55), (0.40, 0.58),
        (-0.55, 0.08), (0.10, 0.08), (0.75, 0.10), (-0.95, 0.48),
        (0.05, 0.32), (-0.30, 0.28),
    ]
    for i, (x, y) in enumerate(tufts):
        z = z_earth(x, y, (x + 1.15) / 2.30, (y + 0.42) / 1.14)
        add_grass_tuft(mb, Vector((x, y, z)), seed=800 + i, scale=rng.uniform(0.9, 1.25))

    for i, (x, y, r) in enumerate(((-0.15, 0.30, 0.12), (0.55, 0.18, 0.10), (-0.70, 0.36, 0.09))):
        z = z_earth(x, y, (x + 1.15) / 2.30, (y + 0.42) / 1.14)
        add_slab(mb, x, y, z - 0.01, z + 0.022, r, n=5, seed=900 + i)

    return finalize(mb, 'ENV_Temple_EarthBed_B', [MAT_WOOD, MAT_FOL, MAT_GND])


# ---------------------------------------------------------------------------
# Build all
# ---------------------------------------------------------------------------
print('=== Building Overgrowth Kit v3 ===')
build_root_pillar()
build_root_corner()
build_vine_curtain('ENV_Temple_Vine_Curtain_A', width=2.40, drop=3.10, n_stems=11, dense=True)
build_vine_curtain('ENV_Temple_Vine_Curtain_B', width=1.30, drop=3.85, n_stems=7, dense=False)
build_tree_a()
build_tree_b()
build_earth_a()
build_earth_b()

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
with open(f'{ROOT}/evidence/geometry_stats.json', 'w') as f:
    json.dump(STATS, f, indent=2)
print('Saved', BLEND)
print(json.dumps(STATS, indent=2))

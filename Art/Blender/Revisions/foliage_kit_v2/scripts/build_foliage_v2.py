# Sculpted painterly foliage kit v2 (volumes + leaf shells, opaque, no alpha cards, custom soft normals).
# Run: Blender -b --python build_foliage_v2.py ; writes models/*.fbx + TempleEnvironmentKit_foliage_v2.blend + stats.json
# Blender Z-up, origin at the ground/attach point. FBX: axis_forward=-Z, axis_up=Y (same as the rest of the kit).
import bpy, bmesh, math, random, os, json
from mathutils import Vector, noise

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/foliage_kit_v2'
TEXF = f'{OUT}/textures/ENV_Temple_Foliage2_BaseColor.png'
bpy.ops.wm.read_factory_settings(use_empty=True)

# ---------------- atlas UV zones ----------------
def leaf_uv(col, uu, t):       # leaf columns, v .5-1
    return (col * 0.125 + 0.012 + uu * 0.101, 0.5 + 0.006 + t * 0.488)
def ivy_uv(cell, uu, t):       # ivy cells, v 0-.25
    return (0.5 + cell * 0.125 + 0.012 + uu * 0.101, 0.006 + t * 0.238)
def lump_uv(ang, h):           # lump body, v .25-.5 ; ang in turns
    return (ang, 0.26 + 0.23 * max(0.0, min(1.0, h)))
def bark_uv(a, t):             # bark, u 0-.5, v 0-.25
    return (0.02 + a * 0.46, 0.01 + t * 0.23)

class B:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.cn = self.bm.verts.layers.float_vector.new('cn')
    def v(self, p, n):
        v = self.bm.verts.new(p); v[self.cn] = Vector(n).normalized(); return v
    def f(self, verts, uvs):
        try: f = self.bm.faces.new(verts)
        except ValueError: return None
        for l, uv in zip(f.loops, uvs): l[self.uv].uv = uv
        return f

def rv(s): return Vector((random.uniform(-1, 1) * s, random.uniform(-1, 1) * s, random.uniform(-1, 1) * s))
UP = Vector((0, 0, 1))

# ---------------- lump: noisy squashed ellipsoid with radial+up soft normals ----------------
def lump(b, c, r, seed, amp=0.16, flat_bottom=True, subdiv=2, up_bias=0.35, ang_off=0.0):
    c = Vector(c); tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1.0)
    verts = {}
    for tv in tmp.verts:
        d = tv.co.copy(); n = noise.noise(d * 1.7 + Vector((seed, seed * 0.7, seed * 1.3))) * amp + noise.noise(d * 4.1 + Vector((seed, 3, 9))) * amp * 0.45
        s = 1 + n
        p = Vector((d.x * r[0] * s, d.y * r[1] * s, d.z * r[2] * s))
        if flat_bottom and p.z < -0.02: p.z = -0.02 + (p.z + 0.02) * 0.15
        g = Vector((d.x / r[0], d.y / r[1], d.z / r[2])).normalized()
        nrm = (g * (1 - up_bias) + UP * up_bias).normalized()
        verts[tv.index] = (c + p, nrm, d)
    ztop = max(v[0].z for v in verts.values()); zbot = min(v[0].z for v in verts.values())
    new = {i: b.v(p, n) for i, (p, n, d) in verts.items()}
    for tf in tmp.faces:
        ids = [l.vert.index for l in tf.loops]
        us = []
        for i in ids:
            p, n, d = verts[i]
            us.append((math.atan2(d.y, d.x) / (2 * math.pi) + 0.5 + ang_off, (p.z - zbot) / max(1e-4, ztop - zbot)))
        if max(u for u, _ in us) - min(u for u, _ in us) > 0.5: us = [(u + 1 if u < 0.5 else u, h) for u, h in us]
        # pole faces: u is ill-defined; use the face mean
        if any(abs(verts[i][2].z) > 0.97 for i in ids):
            mu = sum(u for u, _ in us) / 3; us = [(mu, h) for _, h in us]
        b.f([new[i] for i in ids], [lump_uv(u, h) for u, h in us])
    tmp.free()
    return c, Vector(r)

# ---------------- leaf: 8-tri folded, drooping, lens-shaped ----------------
def leaf(b, base, axis, length, width, outward, col, droop=0.5, fold=0.07, nrm_mix=0.3, soft=None, taper_pow=0.85):
    a = axis.normalized(); s = a.cross(outward if abs(a.dot(outward.normalized())) < 0.95 else UP)
    if s.length < 1e-4: s = Vector((1, 0, 0))
    s.normalize(); ln = s.cross(a).normalized()
    if ln.dot(outward) < 0: ln = -ln
    soft = (soft if soft is not None else outward.normalized())
    def P(t, off):
        w = width * (math.sin(math.pi * t) ** taper_pow if 0 < t < 1 else 0.0)
        return base + a * (length * t) + Vector((0, 0, -1)) * (droop * length * t * t) + s * (w * off) + ln * (fold * length * math.sin(math.pi * t) * (1 - abs(off)))
    def mk(t, off):
        n = (soft * (1 - nrm_mix) + ln * nrm_mix); return b.v(P(t, off), n)
    TM = 0.46
    base_v = mk(0, 0); tip = mk(1, 0); r = [mk(TM, -1), mk(TM, 0), mk(TM, 1)]
    U = lambda off, t: leaf_uv(col, (off + 1) / 2, t)
    f = b.f
    f([base_v, r[0], r[1]], [U(0, 0), U(-1, TM), U(0, TM)]); f([base_v, r[1], r[2]], [U(0, 0), U(0, TM), U(1, TM)])
    f([r[0], tip, r[1]], [U(-1, TM), U(0, 1), U(0, TM)]); f([r[1], tip, r[2]], [U(0, TM), U(0, 1), U(1, TM)])

# ---------------- surface leaf shell over a lump ----------------
def leaf_shell(b, c, r, n, cols, lmin, lmax, wscale=0.5, zmin=-0.05, droop=(0.3, 0.8), up_bias=0.35, rng=None, spiral_seed=0):
    rng = rng or random
    c = Vector(c); gold = math.pi * (3 - math.sqrt(5)); placed = 0; i = 0
    while placed < n and i < n * 6:
        k = (i + 0.5) / (n * 1.6); i += 1
        z = 1 - 2 * k * 0.95; rad = math.sqrt(max(0, 1 - z * z)); th = gold * i + spiral_seed
        d = Vector((rad * math.cos(th), rad * math.sin(th), z))
        p = c + Vector((d.x * r[0], d.y * r[1], d.z * r[2]))
        if p.z < zmin: continue
        g = Vector((d.x / r[0], d.y / r[1], d.z / r[2])).normalized()
        soft = (g * (1 - up_bias) + UP * up_bias).normalized()
        tang = Vector((-d.y, d.x, 0)); tang.normalize() if tang.length > 1e-4 else None
        axis = g * 0.55 + UP * 0.22 + tang * rng.uniform(-0.55, 0.55) + rv(0.12)
        L = rng.uniform(lmin, lmax)
        leaf(b, p - g * 0.03, axis, L, L * wscale * rng.uniform(0.85, 1.15), g, rng.choice(cols), droop=rng.uniform(*droop), soft=soft)
        placed += 1

# ---------------- tapered tube (stems / vine strands) ----------------
def tube(b, pts, radii, sides=4, bark_t0=0.0, tw=1.0):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ref = Vector((0, 1, 0)) if abs(t.dot(Vector((0, 1, 0)))) < 0.9 else Vector((1, 0, 0))
        u = t.cross(ref).normalized(); w = t.cross(u).normalized()
        ring = []
        for k in range(sides):
            a = 2 * math.pi * k / sides; dvec = u * math.cos(a) + w * math.sin(a)
            ring.append((b.v(p + dvec * radii[i], dvec * 0.7 + UP * 0.3), k))
        rings.append(ring)
    n = len(pts) - 1
    for i in range(n):
        for k in range(sides):
            a0, a1 = rings[i][k][0], rings[i][(k + 1) % sides][0]; b0, b1 = rings[i + 1][k][0], rings[i + 1][(k + 1) % sides][0]
            ua, ub = k / sides, (k + 1) / sides
            b.f([a0, a1, b1, b0], [bark_uv(ua, i / n * tw), bark_uv(ub, i / n * tw), bark_uv(ub, (i + 1) / n * tw), bark_uv(ua, (i + 1) / n * tw)])

# ---------------- ivy leaf (lobed heart, 8 tris, fan from centre) ----------------
IVY_RING = [(0, 0), (.38, .12), (.52, .48), (.18, .58), (0, 1), (-.18, .58), (-.52, .48), (-.38, .12)]
def ivy_leaf(b, base, axis, nrm, size, cell, fold=0.10, soft=None):
    a = axis.normalized(); s = a.cross(nrm).normalized(); ln = s.cross(a).normalized()
    if ln.dot(nrm) < 0: ln = -ln
    soft = soft if soft is not None else nrm.normalized()
    def mk(x, y):
        return b.v(base + a * (y * size) + s * (x * size * 0.95) + ln * (fold * size * (1 - abs(x) * 1.4) * math.sin(math.pi * min(1, max(0, y)))), soft * 0.7 + ln * 0.3)
    cen = mk(0, 0.38); ring = [mk(x, y) for x, y in IVY_RING]
    uvf = lambda x, y: ivy_uv(cell, x / 1.1 + 0.5, y)
    cuv = uvf(0, 0.38)
    for i in range(len(ring)):
        j = (i + 1) % len(ring)
        # winding follows the ring (counter-clockwise seen from +ln when s = +x)
        b.f([cen, ring[j], ring[i]], [cuv, uvf(*IVY_RING[j]), uvf(*IVY_RING[i])])

# ---------------- grass blade ribbon ----------------
def blade(b, base, axis, length, width, col, bend, soft, rows=(0.0, 0.34, 0.68, 1.0)):
    a = Vector(axis).normalized(); out = Vector((a.x, a.y, 0)); out = out.normalized() if out.length > 1e-4 else Vector((1, 0, 0))
    s = Vector((-out.y, out.x, 0)); ln = s.cross(a).normalized()
    def P(t, off):
        w = width * (1 - t ** 1.4) * (1.0 if t < 1 else 0)
        # bend: blade leans further outward and falls toward the tip
        return base + a * (length * t) + out * (bend * length * t * t) + Vector((0, 0, -1)) * (bend * 0.5 * length * t * t) + s * (w * off) + ln * (0.04 * length * (1 - abs(off)) * (1 - t))
    mk = lambda t, off: b.v(P(t, off), soft * 0.65 + ln * 0.35)
    tip = mk(1, 0)
    R = [[mk(t, -1), mk(t, 0), mk(t, 1)] for t in rows[:3]]
    U = lambda off, t: leaf_uv(col, (off + 1) / 2, t)
    for i in range(2):
        for k in range(2):
            b.f([R[i][k], R[i + 1][k], R[i + 1][k + 1], R[i][k + 1]], [U(k - 1, rows[i]), U(k - 1, rows[i + 1]), U(k, rows[i + 1]), U(k, rows[i])])
    b.f([R[2][0], tip, R[2][1]], [U(-1, rows[2]), U(0, 1), U(0, rows[2])]); b.f([R[2][1], tip, R[2][2]], [U(0, rows[2]), U(0, 1), U(1, rows[2])])

# ---------------- finish / export ----------------
mat = bpy.data.materials.new('MI_Temple_Foliage2'); mat.use_nodes = True
nt = mat.node_tree; bsdf = nt.nodes['Principled BSDF']; tex = nt.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(TEXF); tex.image.colorspace_settings.name = 'sRGB'
nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color']); bsdf.inputs['Roughness'].default_value = 0.85
mat.use_backface_culling = False
stats = {}
def finish(b, name, loc=(0, 0, 0)):
    bm = b.bm; bm.verts.ensure_lookup_table(); bm.normal_update()
    nrm = [Vector(v[b.cn]) for v in bm.verts]
    flip = [f for f in bm.faces if f.normal.dot(sum((Vector(v[b.cn]) for v in f.verts), Vector())) < 0]
    if flip: bmesh.ops.reverse_faces(bm, faces=flip)
    stats['_flipped_' + name] = len(flip)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.normals_split_custom_set_from_vertices([tuple(n) for n in nrm])
    ob = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(ob); me.materials.append(mat)
    for p in me.polygons: p.use_smooth = True
    ob.location = loc
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    stats[name] = dict(tris=len(me.polygons), verts=len(me.vertices), bbox_min=[round(min(c[i] for c in bb), 3) for i in range(3)], bbox_max=[round(max(c[i] for c in bb), 3) for i in range(3)])
    return ob

# ======================= ASSETS =======================
LEAFCOLS = [0, 1, 2, 3, 6, 7]
def shrub_a():
    random.seed(7); noise.seed_set(7); b = B()
    lumps = [((0, 0, 0.34), (0.58, 0.55, 0.36)), ((0.42, 0.14, 0.26), (0.38, 0.34, 0.26)), ((-0.40, 0.22, 0.28), (0.40, 0.36, 0.27)),
             ((0.10, -0.42, 0.24), (0.40, 0.34, 0.24)), ((-0.18, 0.02, 0.62), (0.34, 0.32, 0.26)), ((0.30, -0.18, 0.56), (0.26, 0.26, 0.22))]
    for i, (c, r) in enumerate(lumps):
        lump(b, c, tuple(x * 0.9 for x in r), seed=3 + i * 5, amp=0.17, ang_off=i * 0.13)
        leaf_shell(b, c, r, (78 if i == 0 else 48) if i < 4 else 28, LEAFCOLS, 0.15, 0.26, wscale=0.42, zmin=0.06, spiral_seed=i * 1.7, droop=(0.2, 0.6))
    for i in range(7):   # woody stems emerging from beneath, bent outward
        a = i * 0.9 + random.uniform(-.2, .2); d = Vector((math.cos(a), math.sin(a), 0))
        pts = [d * 0.05 + Vector((0, 0, -0.02)), d * 0.28 + Vector((0, 0, 0.07)), d * 0.52 + Vector((0, 0, 0.20))]
        tube(b, pts, [0.036, 0.026, 0.014], 4)
    return finish(b, 'ENV_Temple_Foliage_Shrub_A_v2')
def shrub_b():
    random.seed(21); noise.seed_set(21); b = B()
    lumps = [((-0.62, 0, 0.17), (0.50, 0.44, 0.20)), ((0.0, 0.10, 0.20), (0.56, 0.48, 0.23)), ((0.64, -0.06, 0.15), (0.48, 0.40, 0.18)),
             ((-0.28, -0.34, 0.12), (0.34, 0.30, 0.14)), ((0.34, 0.36, 0.13), (0.34, 0.28, 0.14)), ((-0.10, 0.10, 0.36), (0.30, 0.28, 0.17))]
    for i, (c, r) in enumerate(lumps):
        lump(b, c, r, seed=40 + i * 4, amp=0.20, ang_off=i * 0.21)
        leaf_shell(b, c, r, 48 if i < 3 else 24, LEAFCOLS, 0.14, 0.24, wscale=0.42, zmin=0.03, droop=(0.4, 0.9), spiral_seed=i * 2.3)
    for i in range(7):   # upright sprigs: narrow leaf fans, break the dome silhouette
        a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.1, 0.7); base = Vector((math.cos(a) * rr * 1.05, math.sin(a) * rr * 0.6, 0.14))
        lean = Vector((math.cos(a), math.sin(a), 0)) * 0.25
        for k in range(4):
            leaf(b, base, Vector((0, 0, 1)) + lean + rv(0.18), random.uniform(0.36, 0.55), 0.10, lean + UP * 0.3, random.choice([0, 1, 6]), droop=0.25, soft=(UP * 0.6 + lean.normalized() * 0.4), nrm_mix=0.2)
    return finish(b, 'ENV_Temple_Foliage_Shrub_B_v2')

def vine_a():   # wall creeper: origin at the TOP attach point, hangs along -Z, face toward +Y (wall at y=0)
    random.seed(33); noise.seed_set(33); b = B()
    lump(b, (0, 0.06, -0.05), (0.62, 0.17, 0.20), seed=5, amp=0.18, flat_bottom=False, up_bias=0.2)   # mat of growth at the attach point
    strands = [(-0.38, 2.15), (-0.12, 1.55), (0.14, 1.95), (0.40, 1.15), (0.0, 0.85)]
    for si, (x0, L) in enumerate(strands):
        n = 8; pts = []; rad = []
        for i in range(n + 1):
            t = i / n; z = -L * t
            x = x0 + 0.10 * math.sin(t * 5 + si * 1.7) + 0.05 * (t ** 1.5) * random.uniform(-1, 1)
            y = 0.045 + 0.05 * math.sin(t * 3 + si) ** 2
            pts.append(Vector((x, y, z))); rad.append(0.020 * (1 - 0.72 * t))
        tube(b, pts, rad, 4, tw=1.0)
        for i in range(1, n + 1):
            for side in (-1, 1):
                t = i / n; p = pts[i] + Vector((0, 0.01, random.uniform(0.0, 0.08)))
                sz = random.uniform(0.20, 0.30) * (1 - 0.45 * t)
                ax = Vector((side * random.uniform(0.35, 0.8), random.uniform(0.15, 0.4), -random.uniform(0.6, 1.0)))
                ivy_leaf(b, p, ax, Vector((0, 1, 0.15)), sz, random.randrange(4), soft=Vector((side * 0.15, 1, 0.25)))
    return finish(b, 'ENV_Temple_Foliage_Vine_A_v2')

def vine_b():   # cap/pier drape: origin at the TOP SURFACE centre of a broken column/pier (radius ~0.5), strands fall around the shaft
    random.seed(55); noise.seed_set(55); b = B()
    lump(b, (0, 0, 0.06), (0.60, 0.58, 0.13), seed=9, amp=0.20, ang_off=0.3)
    lump(b, (0.16, -0.10, 0.16), (0.30, 0.28, 0.11), seed=14, amp=0.2, ang_off=0.6)
    leaf_shell(b, (0, 0, 0.06), (0.60, 0.58, 0.15), 52, LEAFCOLS, 0.14, 0.24, wscale=0.45, zmin=-0.02, droop=(0.5, 0.9))
    leaf_shell(b, (0.16, -0.10, 0.16), (0.30, 0.28, 0.12), 12, LEAFCOLS, 0.16, 0.24, wscale=0.52, zmin=0.0, droop=(0.5, 0.9))
    nstr = 9
    for si in range(nstr):
        a0 = 2 * math.pi * si / nstr + random.uniform(-.15, .15); L = random.uniform(0.7, 1.7); n = 8; pts = []; rad = []
        for i in range(n + 1):
            t = i / n
            if t < 0.12: p = Vector((math.cos(a0) * (0.45 + 0.12 * (0.12 - t) / 0.12 * 0 + t * 1.5), math.sin(a0) * (0.45 + t * 1.5), 0.04 - t * 0.2))
            else:
                z = -(t - 0.12) / 0.88 * L; ang = a0 + 0.55 * math.sin(t * 4 + si)
                R = 0.55 + 0.04 * math.sin(t * 6 + si)
                p = Vector((math.cos(ang) * R, math.sin(ang) * R, z))
            pts.append(p); rad.append(0.020 * (1 - 0.7 * t))
        tube(b, pts, rad, 4)
        for i in range(2, n + 1):
            t = i / n; p = pts[i]; out = Vector((p.x, p.y, 0)).normalized()
            for side in (-1, 1):
                tang = Vector((-out.y, out.x, 0))
                ax = tang * side * random.uniform(0.3, 0.8) + out * random.uniform(0.1, 0.45) + Vector((0, 0, -random.uniform(0.6, 1.0)))
                ivy_leaf(b, p, ax, out + UP * 0.1, random.uniform(0.18, 0.28) * (1 - 0.4 * t), random.randrange(4), soft=out + UP * 0.25)
    return finish(b, 'ENV_Temple_Foliage_Vine_B_v2')

def tuft_a():   # upright hardy grass tuft nestling against rubble
    random.seed(77); noise.seed_set(77); b = B()
    lump(b, (0, 0, 0.03), (0.22, 0.22, 0.09), seed=2, amp=0.2, subdiv=1, up_bias=0.5)
    cl = [Vector((random.uniform(-.12, .12), random.uniform(-.12, .12), 0)) for _ in range(4)]
    for i in range(36):
        cc = cl[i % 4]; a = random.uniform(0, 2 * math.pi); rr = random.uniform(0.0, 0.07); L = random.uniform(0.26, 0.50)
        out = Vector((math.cos(a), math.sin(a), 0)); lean = random.uniform(0.25, 0.7)
        base = cc + out * rr + Vector((0, 0, 0.03))
        blade(b, base, Vector((0, 0, 1)) + out * lean, L, random.uniform(0.034, 0.05), random.choice([4, 5, 4, 1, 7]), random.uniform(0.35, 0.9), (out * 0.5 + UP * 0.5))
    return finish(b, 'ENV_Temple_Foliage_Tuft_A_v2')
def tuft_b():   # low moss cushion + short broad fronds for damp joints / corners
    random.seed(91); noise.seed_set(91); b = B()
    lump(b, (0, 0, 0.04), (0.34, 0.30, 0.12), seed=6, amp=0.22, subdiv=2, up_bias=0.45)
    leaf_shell(b, (0, 0, 0.04), (0.34, 0.30, 0.12), 8, [2, 6, 1], 0.12, 0.2, wscale=0.5, zmin=0.0, droop=(0.5, 1.0), up_bias=0.5)
    for i in range(14):
        a = 2 * math.pi * i / 14 + random.uniform(-.2, .2); out = Vector((math.cos(a), math.sin(a), 0)); L = random.uniform(0.24, 0.42)
        blade(b, out * random.uniform(0.03, 0.12) + Vector((0, 0, 0.05)), Vector((0, 0, 1)) + out * random.uniform(0.5, 1.0), L, random.uniform(0.04, 0.06), random.choice([2, 6, 0, 1]), random.uniform(0.5, 1.0), out * 0.4 + UP * 0.6)
    return finish(b, 'ENV_Temple_Foliage_Tuft_B_v2')

objs = [shrub_a(), shrub_b(), vine_a(), vine_b(), tuft_a(), tuft_b()]
os.makedirs(f'{OUT}/models', exist_ok=True)
for ob in objs:
    for o in bpy.context.view_layer.objects: o.select_set(False)
    ob.select_set(True); bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(filepath=f'{OUT}/models/{ob.name}.fbx', use_selection=True, object_types={'MESH'}, global_scale=1.0, apply_unit_scale=True,
                             apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True, axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True,
                             mesh_smooth_type='FACE', use_triangles=True, path_mode='COPY', embed_textures=False)
# spread objects for the review file
for i, ob in enumerate(objs): ob.location = (i * 2.6, 0, 0)
bpy.ops.wm.save_as_mainfile(filepath=f'{OUT}/TempleEnvironmentKit_foliage_v2.blend')
json.dump(stats, open(f'{OUT}/models/stats.json', 'w'), indent=1)
for k, v in stats.items(): print(k, v)

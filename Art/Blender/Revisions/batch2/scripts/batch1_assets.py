"""Batch-1 asset builders (working copy only): Wall_Tall_A/B, Lantern_Pylon_A, Ruin_Cluster_A/B, Backdrop_Mass_A/B/C.
Same conventions as the kit: 1 BU = 1 m, +Z up, local +Y = 'front' (OUTWARD for wall bays, arena side is -Y), pivots in mesh coordinates.
Uses kitlib.B (zone_id written in to_object) and the shared source materials. Low-poly budgets: bay <8k, pylon <12k, cluster <15k, backdrop <4k tris.
"""
import math
from mathutils import Vector, Matrix
import bmesh
from kitlib import B, M_STONE, M_CHARCOAL, M_BRONZE, M_GOLD, M_CRIMSON, M_EMBER, TAU
from assets import _flute


def fin(b, L, drop=True, **sc):
    """drop hidden floor faces, unwrap the clean mesh, sculpt to edge length L (NO global LM multiplier here), smooth-shade."""
    if drop:
        b.drop_bottom()
    b.unwrap()
    b.sculpt(L=L, **sc)
    b.shade()
    return b


# ------------------------------------------------------------------ helpers for the tall bay
def _carve(x0, x1, z0, z1, holes):
    """Rectangle [x0,x1]x[z0,z1] minus `holes` [(x0,x1,z0,z1)...] -> list of rectangles (horizontal-band decomposition)."""
    zs = sorted({z0, z1} | {h[2] for h in holes if z0 < h[2] < z1} | {h[3] for h in holes if z0 < h[3] < z1})
    out = []
    for a, c in zip(zs[:-1], zs[1:]):
        zm = (a + c) / 2
        cuts = sorted((max(h[0], x0), min(h[1], x1)) for h in holes if h[2] < zm < h[3] and h[1] > x0 and h[0] < x1)
        cur = x0
        for hx0, hx1 in cuts:
            if hx0 > cur + 1e-6:
                out.append((cur, hx0, a, c))
            cur = max(cur, hx1)
        if cur < x1 - 1e-6:
            out.append((cur, x1, a, c))
    return out


def _courses(b, x0, x1, z0, z1, holes, y_face, thick, course_h=0.5, charcoal_p=0.10, jitter=0.012, zgrid0=0.4):
    """Thin stone plates on a front face y=y_face (plate occupies y_face-thick .. y_face) laid in `course_h` courses, hole-aware.
    Reads as ashlar coursing + staggered vertical joints without the hidden faces of full blocks."""
    n0 = int(round((z0 - zgrid0) / course_h))
    zc = zgrid0 + n0 * course_h
    k = 0
    while zc < z1 - 1e-6:
        za, zb = max(zc, z0), min(zc + course_h, z1)
        if zb - za > 0.08:
            for (sx0, sx1, sza, szb) in _carve(x0, x1, za, zb, holes):      # batch2 fix: use the sub-band z extents, so plates never overhang a hole edge
                pos = sx0 + (0.0 if k % 2 == 0 else b.rng.uniform(0.35, 0.8))
                cuts = [sx0]
                while pos < sx1 - 0.55:
                    if pos > sx0 + 0.45:
                        cuts.append(pos)
                    pos += b.rng.uniform(0.85, 1.5)
                cuts.append(sx1)
                for i in range(len(cuts) - 1):
                    px0, px1 = cuts[i] + 0.006, cuts[i + 1] - 0.006
                    if px1 - px0 < 0.12:
                        continue
                    t = thick * b.rng.uniform(0.7, 1.35)
                    m = M_CHARCOAL if b.rng.random() < charcoal_p else M_STONE
                    b.box(((px0 + px1) / 2, y_face - t / 2 + 0.002, (sza + szb) / 2), (px1 - px0, t, szb - sza - 0.012), m, tone=b.rng.random(), jitter=jitter)
        zc += course_h
        k += 1


LBAY = 0.74
ZVIS = 2.20        # below this the 3.0 m parapet hides the bay from the gameplay camera (measured, see report): keep it plain


def _tall_bay(name, seed, variant):
    """4 m bay: half-pier on each side (adjacent bays form a full 1.0 m pier), recessed front layer with niches, coursed face,
    ragged weathered top between taller pier caps.  Arena-facing side = -Y.  Footprint y in [-0.60, +0.60] (piers), skirt to z=-0.4."""
    b = B(name, seed=seed)
    A = variant == 'A'
    H = 5.0 if A else 6.0                      # pier top
    YF, YB = -0.60, 0.60                       # pier front / back
    FL0, FL1 = -0.25, 0.10                     # front layer (the visible infill face is at FL0; recess back plane at FL1)
    zb = 0.40                                  # top of the plinth
    top_base = 4.55 if A else 5.25             # infill below the ragged top
    # plinth / foundation skirt (below z=0 is hidden foundation)
    b.box((0, 0, 0.0), (4.0, 1.2, 0.80), M_CHARCOAL, tone=0.35)
    b.box((0, -0.04, 0.46), (4.0, 1.12, 0.12), M_STONE, tone=0.5)     # plinth cap
    # back panel (full height of the infill, behind everything)
    b.box((0, (FL1 + YB) / 2, (zb + top_base) / 2), (3.0, YB - FL1, top_base - zb), M_STONE, tone=0.5)
    # niches (holes in the front layer, full layer depth -> recess back plane at FL1)
    if A:
        holes = [(-0.80, 0.80, 2.75, 4.05), (-0.60, 0.60, 4.05, 4.28)]               # one wide niche with a stepped (corbel) head
    else:
        holes = [(-1.05, -0.45, 2.95, 4.60), (-0.93, -0.57, 4.60, 4.90), (-0.82, -0.68, 4.90, 5.12),
                 (0.45, 1.05, 2.95, 4.60), (0.57, 0.93, 4.60, 4.90), (0.68, 0.82, 4.90, 5.12)]   # two slit niches with stepped heads
    for (x0, x1, za, zc) in _carve(-1.5, 1.5, zb, top_base, holes):
        b.box(((x0 + x1) / 2, (FL0 + FL1) / 2, (za + zc) / 2), (x1 - x0, FL1 - FL0, zc - za), M_STONE, tone=b.rng.random())
    # sill / ledge under the niche(s) and a string course across the whole infill
    sill_z = 2.75 if A else 2.95
    b.box((0, FL0 - 0.05, sill_z - 0.07), (3.0, 0.14, 0.14), M_STONE, tone=0.55)
    b.box((0, FL0 - 0.04, 2.20), (3.0, 0.12, 0.10), M_STONE, tone=0.5)
    # piers: shaft in two lifts + step-back + cap; bronze strap (plain rectangular band) under the cap
    for sx in (-1, 1):
        cx = sx * 1.75
        b.box((cx, 0.0, (zb + 2.3) / 2), (0.5, 1.2, 2.3 - zb), M_STONE, tone=b.rng.random())
        b.box((cx, 0.0, (2.3 + H - 0.55) / 2), (0.5, 1.16, H - 0.55 - 2.3), M_STONE, tone=b.rng.random())
        b.box((cx, 0.0, 2.3), (0.5, 1.24, 0.10), M_STONE, tone=0.55)                      # pier string course
        b.box((cx, 0.0, H - 0.64), (0.504, 1.23, 0.07), M_BRONZE, tone=0.5)    # bronze strap
        b.box((cx - sx * 0.07, 0.0, H - 0.27), (0.5 + 0.14, 1.28, 0.54), M_STONE, tone=0.6)  # cap (overhangs the shaft; flush at the tile joint)
    b.bevel(0.03, 1, angle=34)                                   # structural pieces only; plates / ragged top are added afterwards (not bevelled)
    # ashlar courses on the infill face (lower zone + jambs + above the niches), hole-aware
    _courses(b, -1.5, 1.5, ZVIS, top_base, holes, FL0, 0.07, course_h=0.55, zgrid0=ZVIS, jitter=0.010)   # coursing only above the parapet-hidden zone
    # recessed back-panel courses inside the niches (shallow, lit from the arena side)
    for (x0, x1, za, zc) in holes[:1] if A else holes[::3]:
        _courses(b, x0, x1, za, zc, [], FL1, 0.04, charcoal_p=0.0, jitter=0.004)
    # ragged weathered top: infill blocks of varied height (some missing) between the pier caps
    xs = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
    hts = ([0.30, 0.0, 0.45, 0.18, 0.0, 0.38] if A else [0.0, 0.42, 0.22, 0.0, 0.46, 0.14])
    for i, h in enumerate(hts):
        if h <= 0.0:
            continue
        b.box(((xs[i] + xs[i + 1]) / 2, (FL0 + YB) / 2 - 0.05, top_base + h / 2), (0.5 - 0.012, YB - FL0 - 0.1, h), M_STONE, tone=b.rng.random(), jitter=0.01)
    return fin(b, LBAY, warp=(0.014, 0.55), chip=(0.040, 3.2), fine=(0.004, 8.0), edge_ang=0.35)


def wall_tall_A():
    return _tall_bay('Wall_Tall_A', 201, 'A')


def wall_tall_B():
    return _tall_bay('Wall_Tall_B', 202, 'B')


# ------------------------------------------------------------------ Lantern pylon
LPYL = 0.17


def lantern_pylon():
    """2.98 m stone post: stepped plinth, tapering square shaft in three lifts with plain rectangular bands (stone + one bronze),
    corbelled capital, bronze fire bowl (Brazier_A profile, 1.0x) and an emissive flame body. No ring, no relief, no sun motif."""
    b = B('Lantern_Pylon_A', seed=121)
    b.box((0, 0, 0.10), (1.04, 1.04, 0.20), M_STONE, tone=0.5)
    b.box((0, 0, 0.27), (0.84, 0.84, 0.14), M_STONE, tone=0.45)
    zs = [0.34, 0.86, 1.34, 1.72]; ws = [0.60, 0.55, 0.51]
    for i in range(3):
        b.box((0, 0, (zs[i] + zs[i + 1]) / 2 + 0.002), (ws[i], ws[i], zs[i + 1] - zs[i] - 0.008), M_STONE, tone=b.rng.random())
    b.box((0, 0, 0.86), (0.64, 0.64, 0.07), M_STONE, tone=0.5)
    b.box((0, 0, 1.34), (0.60, 0.60, 0.07), M_STONE, tone=0.5)
    b.box((0, 0, 1.55), (0.56, 0.56, 0.06), M_BRONZE, tone=0.5)                          # plain bronze band
    for z0, z1, w in ((1.72, 1.80, 0.66), (1.80, 1.91, 0.76), (1.91, 2.03, 0.88), (2.03, 2.12, 0.98)):   # corbelled capital
        b.box((0, 0, (z0 + z1) / 2), (w, w, z1 - z0), M_STONE, tone=b.rng.random())
    b.bevel(0.035, 1, angle=34)                                                           # structural blocks only
    for i in range(3):                                                                     # raised plain rectangular panel on each face (no motif); not bevelled
        for n in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            pw, ph = ws[i] * 0.46, (zs[i + 1] - zs[i]) * 0.62
            b.box((n[0] * (ws[i] / 2 + 0.008), n[1] * (ws[i] / 2 + 0.008), (zs[i] + zs[i + 1]) / 2), (0.022 if n[0] else pw, 0.022 if n[1] else pw, ph), M_STONE, tone=0.55)
    # bowl: Brazier_A profile shifted to z=2.12, scale 1.0
    zo = 2.12
    bowl = [(0.12, 0.00), (0.30, 0.06), (0.46, 0.24), (0.52, 0.38), (0.53, 0.44), (0.49, 0.44), (0.44, 0.26), (0.28, 0.14)]
    b.lathe([(r, z + zo) for r, z in bowl], seg=24, mat=M_BRONZE, tone=0.5, dz=0.10)
    for a in range(4):                                                                   # four plain rectangular lugs on the bowl
        th = a * TAU / 4 + TAU / 8
        m = Matrix.Translation((0.47 * math.cos(th), 0.47 * math.sin(th), zo + 0.28)) @ Matrix.Rotation(th, 4, 'Z')
        b.box_m(m, (0.08, 0.14, 0.20), M_BRONZE, 0.5)
    # emissive flame zone: coals bed + a tapering faceted flame body (Unity adds the light)
    b.lathe([(0.0, zo + 0.31), (0.36, zo + 0.31), (0.40, zo + 0.36)], seg=20, mat=M_EMBER, tone=0.5, dz=0.06, rot_phase=0.0)
    b.lathe([(0.24, zo + 0.34), (0.27, zo + 0.46), (0.22, zo + 0.60), (0.14, zo + 0.72), (0.06, zo + 0.82), (0.0, zo + 0.86)], seg=10, mat=M_EMBER, tone=0.5, dz=0.07, rot_phase=0.3)
    return fin(b, LPYL, warp=(0.006, 0.9), chip=(0.016, 6.0), fine=(0.0018, 18.0))


# ------------------------------------------------------------------ Ruin clusters
LRUIN_A = 0.245
LRUIN = 0.20


def _hull_chunk(b, c, size, n=18, tilt=0.25, mat=M_STONE, slope=None, base_r=None):
    """Convex fractured stone (as kit Rubble). slope=(dx,dy,dz-per-m) tilts the top plane for broken shaft ends."""
    rz = b.rng.uniform(0, TAU)
    R = Matrix.Rotation(rz, 3, 'Z') @ Matrix.Rotation(b.rng.uniform(-tilt, tilt), 3, 'X')
    pts = []
    for _ in range(n):
        d = Vector((b.rng.gauss(0, 1), b.rng.gauss(0, 1), b.rng.gauss(0, 1))).normalized()
        p = Vector((d.x * size[0] / 2, d.y * size[1] / 2, size[2] * 0.30 + d.z * size[2] * 0.5))
        p = R @ p
        p.z = max(p.z, 0.0)
        pts.append(Vector((p.x + c[0], p.y + c[1], p.z + c[2])))
    verts = [b.bm.verts.new(p) for p in pts]
    res = bmesh.ops.convex_hull(b.bm, input=verts)
    dead = list({g for g in (res['geom_interior'] + res['geom_unused']) if isinstance(g, bmesh.types.BMVert)})
    if dead:
        bmesh.ops.delete(b.bm, geom=dead, context='VERTS')
    out = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
    b._tag(out, mat, b.rng.random())


def _broken_top(b, c, r, z0, z1, seg, slope, phase=0.0, mat=M_STONE):
    """Faceted frustum with a slanted, ragged break plane (convex hull of two rings). slope=(sx,sy) metres of rise per metre."""
    pts = []
    for i in range(seg):
        th = TAU * i / seg + phase
        rr = r * (1.0 + b.rng.uniform(-0.03, 0.03))
        x, y = rr * math.cos(th), rr * math.sin(th)
        pts.append(Vector((c[0] + x, c[1] + y, z0)))
        zt = z1 + slope[0] * x + slope[1] * y + b.rng.uniform(-0.07, 0.07)
        pts.append(Vector((c[0] + x * 0.96, c[1] + y * 0.96, zt)))
    verts = [b.bm.verts.new(p) for p in pts]
    res = bmesh.ops.convex_hull(b.bm, input=verts)
    dead = list({g for g in (res['geom_interior'] + res['geom_unused']) if isinstance(g, bmesh.types.BMVert)})
    if dead:
        bmesh.ops.delete(b.bm, geom=dead, context='VERTS')
    out = [g for g in res['geom'] if isinstance(g, bmesh.types.BMVert)]
    b._tag(out, mat, b.rng.random())


def _lying_drum(b, c, r, length, yaw, seg=40, flute=True, octa=False, tone=None, roll=0.0):
    """Drum lying on its side resting on the floor (axis horizontal, along yaw)."""
    rad = (lambda th, z: 1.0) if (octa or not flute) else _flute(10, 0.07)
    b.lathe([(r, -length / 2), (r * 0.99, 0.0), (r * 0.98, length / 2)], seg=(8 if octa else seg), center=(c[0], c[1], r * (0.93 if octa else 1.0) - 0.02),
            rot=(0, math.pi / 2, yaw), mat=M_STONE, tone=tone if tone is not None else b.rng.random(), radial=rad, dz=0.25, rot_phase=(math.pi / 8 if octa else 0.0) + roll)


def _slab(b, c, size, yaw, tilt=0.0, mat=M_STONE, zc=None):
    """Rectangular slab (fallen lintel) with its low end resting on the floor; tilt about local Y."""
    L, W, T = size
    zc = zc if zc is not None else (L / 2) * math.sin(abs(tilt)) + (T / 2) * math.cos(tilt) - 0.01
    m = Matrix.Translation((c[0], c[1], zc)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y')
    b.box_m(m, (L, W, T), mat, b.rng.random())


def ruin_cluster_A():
    """Round fluted broken pillar (3.1 m) + plinth chunk, three toppled drums, a fallen lintel slab and rubble. Tall end at local (-x,+y) = away from the gameplay camera."""
    b = B('Ruin_Cluster_A', seed=131)
    pc = (-0.95, 0.95)
    _hull_chunk(b, (pc[0], pc[1], 0.0), (2.0, 2.0, 0.55), n=22, tilt=0.06)                                   # plinth remnant
    r0 = 0.54
    for z0, z1 in ((0.30, 1.32), (1.32, 2.30)):
        b.lathe([(r0, z0 + 0.006), (r0 * 0.985, (z0 + z1) / 2), (r0 * 0.97, z1 - 0.006)], seg=40, center=(pc[0], pc[1], 0), mat=M_STONE, tone=b.rng.random(), radial=_flute(10, 0.07), dz=0.5, rot_phase=b.rng.uniform(-0.03, 0.03))
        b.bevel(0.012, 1)
    _broken_top(b, (pc[0], pc[1]), 0.52, 2.30, 3.0, 14, slope=(0.30, -0.18), phase=0.2)
    _lying_drum(b, (0.80, 0.85), 0.55, 1.20, yaw=0.10)
    _lying_drum(b, (1.95, -0.45), 0.50, 1.00, yaw=1.05, roll=0.1)
    _lying_drum(b, (-0.45, -1.15), 0.44, 0.80, yaw=1.7, flute=False)
    _slab(b, (1.05, -2.35), (2.70, 0.78, 0.46), yaw=0.22, tilt=0.06)
    _hull_chunk(b, (2.9, 0.9, 0.0), (0.7, 0.55, 0.42)); _hull_chunk(b, (-0.75, -2.3, 0.0), (0.55, 0.45, 0.34)); _hull_chunk(b, (3.05, -1.6, 0.0), (0.6, 0.5, 0.30))
    b.bevel(0.03, 2, angle=20)
    return fin(b, LRUIN_A, warp=(0.010, 0.8), chip=(0.034, 5.0), fine=(0.003, 14.0))


def ruin_cluster_B():
    """Octagonal broken pillar (2.8 m) with a plain bronze band, two toppled octagonal drums bridged by a fallen lintel slab, rubble. Different arrangement from A."""
    b = B('Ruin_Cluster_B', seed=132)
    pc = (-1.05, 0.70)
    _hull_chunk(b, (pc[0], pc[1], 0.0), (1.8, 1.8, 0.42), n=20, tilt=0.05)
    r0 = 0.50
    b.lathe([(r0, 0.26), (r0 * 0.97, 1.25)], seg=8, center=(pc[0], pc[1], 0), mat=M_STONE, tone=b.rng.random(), rot_phase=math.pi / 8, dz=0.4); b.bevel(0.02, 1, angle=30)
    b.lathe([(0.545, 1.25), (0.545, 1.31)], seg=8, center=(pc[0], pc[1], 0), mat=M_BRONZE, tone=0.5, rot_phase=math.pi / 8, dz=0.06)   # plain octagonal bronze band
    b.lathe([(r0 * 0.97, 1.31), (r0 * 0.93, 2.2)], seg=8, center=(pc[0], pc[1], 0), mat=M_STONE, tone=b.rng.random(), rot_phase=math.pi / 8, dz=0.4); b.bevel(0.02, 1, angle=30)
    _broken_top(b, (pc[0], pc[1]), 0.46, 2.2, 2.75, 8, slope=(-0.22, 0.25), phase=math.pi / 8)
    _lying_drum(b, (0.55, -0.55), 0.46, 1.25, yaw=0.10, octa=True)
    _lying_drum(b, (0.65, 0.85), 0.46, 1.25, yaw=0.10, octa=True, roll=0.2)
    _slab(b, (0.60, 0.15), (2.30, 0.80, 0.40), yaw=1.62, tilt=0.0, zc=0.85 + 0.20)           # bridges the two drums (their tops are at ~0.85 m)
    _hull_chunk(b, (2.4, -0.7, 0.0), (0.8, 0.6, 0.45)); _hull_chunk(b, (-0.6, -1.5, 0.0), (0.6, 0.5, 0.32)); _hull_chunk(b, (2.3, 1.7, 0.0), (0.55, 0.45, 0.30))
    b.bevel(0.03, 2, angle=20)
    return fin(b, LRUIN, warp=(0.010, 0.8), chip=(0.034, 5.0), fine=(0.003, 14.0))


# ------------------------------------------------------------------ Backdrop masses (abstract, matte)
def _gable(b, cx, cy, w, d, z0, z1, ridge_x=True, mat=M_STONE):
    """Gable-roof prism: footprint w (x) by d (y), eaves at z0, ridge at z1 running along x (or y)."""
    if ridge_x:
        pts = [(cx - w / 2, z0), (cx + w / 2, z0), (cx + w / 2, z1), (cx - w / 2, z1)]
        # build as hexahedron-like prism with triangular section across y: section (y,z) extruded along x
        sec = [(cy - d / 2, z0), (cy + d / 2, z0), (cy, z1)]
        f = [b.bm.verts.new((cx - w / 2, y, z)) for y, z in sec]; k = [b.bm.verts.new((cx + w / 2, y, z)) for y, z in sec]
    else:
        sec = [(cx - w / 2, z0), (cx + w / 2, z0), (cx, z1)]
        f = [b.bm.verts.new((x, cy - d / 2, z)) for x, z in sec]; k = [b.bm.verts.new((x, cy + d / 2, z)) for x, z in sec]
    try:
        b.bm.faces.new(f); b.bm.faces.new(list(reversed(k)))
    except ValueError:
        pass
    for i in range(3):
        j = (i + 1) % 3
        try:
            b.bm.faces.new((f[i], f[j], k[j], k[i]))
        except ValueError:
            pass
    b._tag(f + k, mat, b.rng.random())


LBACK = 5.0


BACK_SC = dict(warp=(0.10, 0.10), chip=(0.10, 0.40), fine=(0.02, 0.8), edge_ang=0.4)


def backdrop_A():
    """Staggered terrace massif (asymmetric): offset stacked blocks, a separate gabled hall and a lower wing. ~28 x 20 m, 17 m tall."""
    b = B('Backdrop_Mass_A', seed=301)
    b.box((0, 0, 2.5), (28, 18, 5.0), M_STONE, tone=0.4)
    b.box((4.0, -1.0, 7.5), (18, 12, 5.0), M_STONE, tone=0.5)
    b.box((7.0, -1.5, 12.0), (11, 8, 4.0), M_STONE, tone=0.45)
    b.box((-5.0, 0.5, 7.0), (12, 9, 4.0), M_STONE, tone=0.55)
    _gable(b, -5.0, 0.5, 13.0, 8.4, 9.0, 12.2, ridge_x=True)
    b.box((-5.0, 0.5, 12.5), (14.0, 1.4, 1.0), M_CHARCOAL, tone=0.3)
    b.box((-15.0, 5.5, 3.0), (9, 8, 6.0), M_STONE, tone=0.5)
    _gable(b, 7.0, -1.5, 11.6, 6.4, 14.0, 16.6, ridge_x=False)
    b.box((7.0, -1.5, 16.9), (1.4, 7.0, 1.0), M_CHARCOAL, tone=0.3)
    b.bevel(0.25, 1, angle=34)
    return fin(b, LBACK, **BACK_SC)


def backdrop_B():
    """Long hall with an asymmetric pair of wings: a gabled hall, a keep-like flat block on one side and a two-step wing on the other. ~40 x 14 m, 15 m tall."""
    b = B('Backdrop_Mass_B', seed=302)
    b.box((0, 0, 4.0), (28, 11, 8.0), M_STONE, tone=0.45)
    _gable(b, 0, 0, 28.6, 12.0, 8.0, 12.6, ridge_x=True)
    b.box((0, 0, 12.9), (29.0, 1.4, 1.1), M_CHARCOAL, tone=0.3)
    b.box((20.0, 1.0, 7.5), (12, 10, 15.0), M_STONE, tone=0.5)
    b.box((20.0, 1.0, 15.3), (12.6, 10.6, 0.6), M_CHARCOAL, tone=0.35)
    b.box((-19.0, 0.8, 3.0), (10, 9, 6.0), M_STONE, tone=0.5)
    b.box((-25.0, 1.2, 2.0), (6, 7, 4.0), M_STONE, tone=0.55)
    _gable(b, -19.0, 0.8, 10.4, 9.6, 6.0, 8.6, ridge_x=False)
    b.box((-3.0, -8.0, 1.6), (22, 2.0, 3.2), M_STONE, tone=0.6)
    b.bevel(0.25, 1, angle=34)
    return fin(b, LBACK, **BACK_SC)


def backdrop_C():
    """Staggered row of three vertical masses (22 / 15 / 9 m) joined by terraces, two with short gabled ridges. ~30 x 14 m, 22 m tall."""
    b = B('Backdrop_Mass_C', seed=303)
    b.box((-8.0, 0, 11.0), (9, 9, 22.0), M_STONE, tone=0.4)
    _gable(b, -8.0, 0, 9.6, 6.4, 22.0, 24.4, ridge_x=False)
    b.box((-8.0, 0, 24.6), (1.2, 7.0, 0.9), M_CHARCOAL, tone=0.3)
    b.box((2.0, 1.0, 7.5), (11, 10, 15.0), M_STONE, tone=0.5)
    b.box((2.0, 1.0, 15.3), (11.6, 10.6, 0.6), M_CHARCOAL, tone=0.35)
    b.box((11.0, -0.5, 4.5), (9, 8, 9.0), M_STONE, tone=0.5)
    _gable(b, 11.0, -0.5, 9.6, 8.6, 9.0, 11.6, ridge_x=True)
    b.box((11.0, -0.5, 11.9), (10.0, 1.2, 0.9), M_CHARCOAL, tone=0.3)
    b.box((-1.5, -1.0, 3.0), (16, 12, 6.0), M_STONE, tone=0.55)
    b.box((16.5, -2.0, 1.5), (6, 6, 3.0), M_STONE, tone=0.6)
    b.bevel(0.25, 1, angle=34)
    return fin(b, LBACK, **BACK_SC)


# name -> (category, builder, density target px/m, value_mult, wear_mult, damp_mult, texres cap)
REG1 = {
    'Wall_Tall_A':    ('Wall',     wall_tall_A,    120, 0.93, 1.0, 1.0, 2048),
    'Wall_Tall_B':    ('Wall',     wall_tall_B,    120, 0.93, 1.0, 1.0, 2048),
    'Lantern_Pylon_A': ('Prop',    lantern_pylon,  200, 1.0, 1.0, 0.6, 2048),
    'Ruin_Cluster_A': ('Prop',     ruin_cluster_A, 110, 0.95, 1.2, 1.0, 2048),
    'Ruin_Cluster_B': ('Prop',     ruin_cluster_B, 110, 0.95, 1.2, 1.0, 2048),
    'Backdrop_Mass_A': ('Backdrop', backdrop_A,     10, 0.55, 1.0, 0.6, 1024),
    'Backdrop_Mass_B': ('Backdrop', backdrop_B,     10, 0.55, 1.0, 0.6, 1024),
    'Backdrop_Mass_C': ('Backdrop', backdrop_C,     10, 0.55, 1.0, 0.6, 1024),
}

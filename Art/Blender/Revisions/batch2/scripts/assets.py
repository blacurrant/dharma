"""Temple environment kit - asset builders (abstract mythological architecture; no real deity/culture/script).

Local frame of every piece: +Z up, +Y = 'front' (faces the arena / outward for walls),
pivot rules per ART/README (floor tiles: centre of bottom face; everything else: centre of floor footprint).
"""
import math
from mathutils import Vector, Matrix
from kitlib import B, M_STONE, M_CHARCOAL, M_BRONZE, M_GOLD, M_CRIMSON, M_EMBER, TAU


# ------------------------------------------------------------------ shared motifs
def relief_sun(b, c, n, s=1.0, rays=12, stud=M_BRONZE, mat=M_STONE):
    """Invented 'celestial' relief: disc + two rings + radial rays. Abstract, not a real symbol."""
    c = Vector(c); n = Vector(n).normalized()
    q = n.to_track_quat('Z', 'Y')
    eul = q.to_euler()
    qm = q.to_matrix().to_4x4()
    b.lathe([(0.11 * s, 0.0), (0.11 * s, 0.045 * s)], seg=28, center=c, rot=tuple(eul), mat=mat, tone=0.5, dz=0.05)
    b.annulus(c, n, 0.17 * s, 0.215 * s, 0.03 * s, seg=40, mat=mat, tone=0.5)
    b.annulus(c, n, 0.29 * s, 0.33 * s, 0.04 * s, seg=48, mat=mat, tone=0.5)
    for i in range(rays):
        a = TAU * i / rays + 0.13
        ln = (0.17 if i % 2 else 0.11) * s
        m = Matrix.Translation(c) @ qm @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation((0.35 * s + ln / 2, 0, 0.012 * s))
        b.box_m(m, (ln, 0.035 * s, 0.03 * s), mat, 0.5)
    if stud is not None:
        b.lathe([(0.045 * s, 0.045 * s), (0.045 * s, 0.075 * s)], seg=16, center=c, rot=tuple(eul), mat=stud, tone=0.5, dz=0.04)


def slabs(b, rects, H, g, mat=M_STONE, jitter_top=0.004, ox=0.0, oy=0.0, charcoal_p=0.0):
    for (x0, x1, y0, y1) in rects:
        top = H + b.rng.uniform(-jitter_top, jitter_top)
        m = M_CHARCOAL if b.rng.random() < charcoal_p else mat
        b.box(((x0 + x1) / 2 + ox, (y0 + y1) / 2 + oy, top / 2), (x1 - x0 - 2 * g, y1 - y0 - 2 * g, top), m, tone=b.rng.random())


LM = 1.8   # global sculpt-density multiplier (prototype budget knob; gameplay camera is ~49 px/m)


def finish(b, L, bevel2=None, **sc):
    b.drop_bottom()
    b.unwrap()
    b.sculpt(L=L * LM, **sc)
    b.shade()
    return b


# ------------------------------------------------------------------ floor / border
FLOOR_LAYOUTS = {
    'A': [(-1, 0, -1, 0), (0, 1, -1, 0), (-1, 0, 0, 1), (0, 1, 0, 1)],
    'B': [(-1, 1, -1, 1)],
    'C': [(-1, 1, -1, 0), (-1, 1, 0, 1)],
    'D': [(-1, 0.4, -1, 0), (0.4, 1, -1, 0), (-1, -0.4, 0, 1), (-0.4, 1, 0, 1)],
}


def floor_tile(v):
    b = B('Floor_' + v, seed={'A': 11, 'B': 12, 'C': 13, 'D': 14}[v])
    H, g = 0.30, 0.010
    slabs(b, FLOOR_LAYOUTS[v], H, g, charcoal_p=0.0)
    b.bevel(0.016, 2)
    return finish(b, 0.22, warp=(0.005, 0.7), chip=(0.010, 6.0), fine=(0.0015, 18.0))


def border_straight():
    b = B('FloorBorder_Straight_A', seed=31)
    H, g = 0.30, 0.010
    slabs(b, [(-1, 0, 0, 1), (0, 1, 0, 1), (-1, 1, -1, 0)], H, g)
    b.bevel(0.016, 2)
    # inlay + invented diamond band; gold limited to a single stud per module
    b.box((0, -0.55, H + 0.004), (1.94, 0.05, 0.016), M_BRONZE, tone=0.5)
    for row in (-0.83, -0.27):
        for i in range(6):
            b.box((-0.80 + 0.32 * i, row, H + 0.012), (0.13, 0.13, 0.026), M_STONE, tone=b.rng.random(), rot=(0, 0, math.pi / 4))
    b.lathe([(0.075, H), (0.075, H + 0.032)], seg=20, center=(0, -0.55, 0), mat=M_GOLD, tone=0.5, dz=0.04)
    b.bevel(0.006, 1)
    return finish(b, 0.10, warp=(0.004, 0.8), chip=(0.008, 8.0), fine=(0.0012, 22.0))


def border_corner():
    b = B('FloorBorder_Corner_A', seed=32)
    H, g = 0.30, 0.010
    slabs(b, [(-1, 0, -1, 0), (0, 1, -1, 0), (-1, 0, 0, 1), (0, 1, 0, 1)], H, g)
    b.bevel(0.016, 2)
    b.torus((0, 0, H + 0.004), 0.62, 0.022, seg=64, sseg=8, mat=M_BRONZE, tone=0.5, stretch=0.8)
    b.annulus((0, 0, H), (0, 0, 1), 0.30, 0.40, 0.03, seg=48, mat=M_STONE, tone=0.5)
    b.lathe([(0.14, H), (0.14, H + 0.05)], seg=24, center=(0, 0, 0), mat=M_GOLD, tone=0.5, dz=0.05)
    b.bevel(0.006, 1)
    return finish(b, 0.10, warp=(0.004, 0.8), chip=(0.008, 8.0), fine=(0.0012, 22.0))


# ------------------------------------------------------------------ stairs / platform
def stairs():
    b = B('Stairs_A', seed=21)
    g = 0.007
    for i in range(4):
        y0 = -1.0 + 0.5 * i
        h = 0.2 * (i + 1)
        b.box((0, y0 + 0.25, h / 2), (3.2 - 2 * g, 0.5 - 2 * g, h), M_STONE, jitter=0.002)
        for sx in (-1, 1):
            b.box((sx * 1.8, y0 + 0.25, (h + 0.16) / 2), (0.4 - 2 * g, 0.5 - 2 * g, h + 0.16), M_STONE, jitter=0.002)
    b.bevel(0.014, 2)

    def wear(bm):  # treads dip where feet land (cause-driven)
        for v in bm.verts:
            if v.normal.z > 0.6 and abs(v.co.x) < 1.55 and v.co.z > 0.05:
                v.co.z -= 0.008 * math.cos(v.co.x / 1.6 * math.pi / 2) ** 2
    return finish(b, 0.15, warp=(0.004, 0.8), chip=(0.014, 6.0), fine=(0.0015, 18.0), hook=wear)


def platform():
    b = B('Platform_A', seed=22)
    g = 0.008
    # base plinth (two blocks), inset body, overhanging top slabs
    for (y0, y1) in ((-3, 0), (0, 3)):
        b.box((0, (y0 + y1) / 2, 0.125), (4.0 - 2 * g, (y1 - y0) - 2 * g, 0.25), M_STONE, jitter=0.002)
    b.box((0, 0, 0.475), (3.8, 5.8, 0.45), M_STONE)
    for ix in (-1, 1):
        for (y0, y1) in ((-3, -1), (-1, 1), (1, 3)):
            top = 0.10 + b.rng.uniform(-0.003, 0.003)
            b.box((ix * 1.0, (y0 + y1) / 2, 0.70 + top / 2), (2.0 - 2 * g, 2.0 - 2 * g, top), M_STONE, tone=b.rng.random())
    b.bevel(0.02, 2)
    return finish(b, 0.20, warp=(0.006, 0.7), chip=(0.020, 6.0), fine=(0.002, 18.0))


# ------------------------------------------------------------------ pillars
def _flute(n, d):
    return lambda th, z: 1.0 - d * (0.5 + 0.5 * math.cos(n * th)) ** 3


def pillar_A():
    b = B('Pillar_A', seed=41)
    b.box((0, 0, 0.2), (1.9, 1.9, 0.4), M_STONE, tone=0.55); b.bevel(0.035, 2)
    b.lathe([(0.84, 0.40), (0.84, 0.50), (0.76, 0.56), (0.70, 0.62), (0.66, 0.72)], seg=48, mat=M_STONE, tone=0.5, dz=0.1); b.bevel(0.01, 1)
    zs = [0.72, 1.96, 3.20, 4.44, 5.42]
    rf = lambda z: 0.60 + 0.012 * math.sin(math.pi * (z - 0.72) / 4.7) - 0.10 * ((z - 0.72) / 4.7)
    for i in range(4):
        z0, z1 = zs[i] + 0.006, zs[i + 1] - 0.006
        b.lathe([(rf(z0), z0), (rf((z0 + z1) / 2), (z0 + z1) / 2), (rf(z1), z1)], seg=96, mat=M_STONE, tone=b.rng.random(),
                radial=_flute(16, 0.07), rot_phase=b.rng.uniform(-0.02, 0.02), dz=0.3)
        b.bevel(0.012, 1)
    b.lathe([(0.52, 5.42), (0.50, 5.47), (0.50, 5.58), (0.58, 5.64)], seg=48, mat=M_STONE, tone=0.5, dz=0.08)
    b.torus((0, 0, 5.52), 0.505, 0.03, seg=48, sseg=8, mat=M_GOLD, tone=0.5)
    b.lathe([(0.58, 5.64), (0.72, 5.78), (0.88, 5.96), (0.94, 6.08)], seg=48, mat=M_STONE, tone=0.5, dz=0.1)
    b.box((0, 0, 6.23), (1.95, 1.95, 0.30), M_STONE, tone=0.6); b.bevel(0.03, 2)
    return finish(b, 0.10, warp=(0.008, 0.8), chip=(0.022, 6.0), fine=(0.002, 18.0))


def pillar_B():
    b = B('Pillar_B', seed=42)
    b.box((0, 0, 0.16), (1.95, 1.95, 0.32), M_STONE, tone=0.5); b.bevel(0.03, 2)
    b.box((0, 0, 0.45), (1.65, 1.65, 0.26), M_STONE, tone=0.45); b.bevel(0.03, 2)
    zs = [0.58, 1.86, 3.14, 4.42, 5.60]
    ws = [1.28, 1.22, 1.16, 1.10]
    for i in range(4):
        b.box((0, 0, (zs[i] + zs[i + 1]) / 2 + 0.003), (ws[i], ws[i], zs[i + 1] - zs[i] - 0.012), M_STONE, tone=b.rng.random())
        b.bevel(0.08, 2)
    zc = 2.5; hw = ws[1] / 2
    for n in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
        relief_sun(b, (n[0] * hw, n[1] * hw, zc), n, s=1.2, stud=M_BRONZE)
    b.bevel(0.006, 1)
    b.box((0, 0, 5.05), (ws[3] + 0.07, ws[3] + 0.07, 0.15), M_BRONZE, tone=0.5); b.bevel(0.015, 1)
    b.box((0, 0, 5.72), (1.42, 1.42, 0.24), M_STONE, tone=0.5); b.bevel(0.03, 2)
    b.box((0, 0, 6.00), (1.84, 1.84, 0.32), M_STONE, tone=0.55); b.bevel(0.035, 2)
    b.box((0, 0, 6.24), (1.52, 1.52, 0.18), M_STONE, tone=0.5); b.bevel(0.03, 2)
    return finish(b, 0.10, warp=(0.008, 0.8), chip=(0.024, 6.0), fine=(0.002, 18.0))


def pillar_C():
    b = B('Pillar_C', seed=43)
    ph = math.pi / 8
    b.lathe([(0.98, 0.0), (0.98, 0.28)], seg=8, mat=M_STONE, tone=0.5, rot_phase=ph, dz=0.28); b.bevel(0.04, 2)
    b.lathe([(0.84, 0.28), (0.84, 0.44), (0.72, 0.55)], seg=8, mat=M_STONE, tone=0.45, rot_phase=ph, dz=0.16); b.bevel(0.03, 2)
    rf = lambda z: 0.64 - 0.12 * (z - 0.55) / 4.8
    zs = [0.55, 2.13, 3.73, 5.35]
    for i in range(3):
        z0, z1 = zs[i] + 0.006, zs[i + 1] - 0.006
        b.lathe([(rf(z0), z0), (rf(z1), z1)], seg=8, mat=M_STONE, tone=b.rng.random(), rot_phase=ph, dz=0.4)
        b.bevel(0.04, 2)
    pts = []
    N = 140
    for k in range(N + 1):
        t = k / N
        z = 1.0 + 3.9 * t
        a = TAU * 2.25 * t
        r = rf(z) * 1.0 + 0.045
        pts.append(Vector((r * math.cos(a), r * math.sin(a), z)))
    b.tube(pts, 0.065, sseg=8, mat=M_BRONZE, tone=0.5, taper=lambda t: min(1.0, 0.35 + 3 * min(t, 1 - t) * 1.5))
    b.lathe([(0.52, 5.35), (0.58, 5.45), (0.78, 5.70), (0.98, 5.95), (1.05, 6.08)], seg=8, mat=M_STONE, tone=0.5, rot_phase=ph, dz=0.12); b.bevel(0.025, 2)
    b.box((0, 0, 6.21), (1.9, 1.9, 0.26), M_STONE, tone=0.55, rot=(0, 0, math.pi / 8)); b.bevel(0.035, 2)
    return finish(b, 0.10, warp=(0.008, 0.8), chip=(0.024, 6.0), fine=(0.002, 18.0))


def pillar_D():
    b = B('Pillar_D', seed=44)
    b.box((0, 0, 0.2), (1.9, 1.9, 0.4), M_STONE, tone=0.5); b.bevel(0.035, 2)
    b.lathe([(0.84, 0.40), (0.84, 0.50), (0.76, 0.56), (0.70, 0.62), (0.66, 0.72)], seg=48, mat=M_STONE, tone=0.5, dz=0.1); b.bevel(0.01, 1)
    rf = lambda z: 0.60 + 0.012 * math.sin(math.pi * (z - 0.72) / 4.7) - 0.10 * ((z - 0.72) / 4.7)
    for (z0, z1) in ((0.726, 1.954), (1.966, 3.0)):
        b.lathe([(rf(z0), z0), (rf((z0 + z1) / 2), (z0 + z1) / 2), (rf(z1), z1)], seg=96, mat=M_STONE, tone=b.rng.random(),
                radial=_flute(16, 0.07), rot_phase=b.rng.uniform(-0.02, 0.02), dz=0.3)
        b.bevel(0.012, 1)
    # broken drum: jagged fracture (settled sideways slightly)
    z0, z1 = 3.012, 3.75
    vs = b.lathe([(rf(z0), z0), (rf((z0 + z1) / 2), (z0 + z1) / 2), (rf(z1), z1)], seg=96, mat=M_STONE, tone=0.6,
                 radial=_flute(16, 0.07), center=(0.035, -0.02, 0), rot=(0.012, -0.015, 0.0), dz=0.3)
    for v in vs:
        if v.co.z > z1 - 0.2:
            th = math.atan2(v.co.y + 0.02, v.co.x - 0.035)
            jag = 0.40 * abs(math.sin(th * 2.0 + 0.7)) + 0.12 * abs(math.sin(th * 7.0 + 1.3)) + 0.05 * math.sin(th * 17.0)
            v.co.z -= jag * (1.0 if v.co.z > z1 - 0.01 else 0.35)
    b.bevel(0.012, 1)
    return finish(b, 0.09, warp=(0.008, 0.8), chip=(0.03, 6.0), fine=(0.002, 18.0))


# ------------------------------------------------------------------ arch (3 parts: PierL, PierR, Span)
def _pier(name, xc, seed, flip, repair):
    b = B(name, seed=seed)
    g = 0.008
    hs = [0.5, 0.8, 0.75, 0.75, 0.8, 0.8]
    z = 0.0
    for i, h in enumerate(hs):
        w, d = (1.80, 2.30) if i == 0 else (1.50, 2.0)
        mat = M_STONE
        if i == 0:
            b.box((xc, 0, z + h / 2), (w - 2 * g, d - 2 * g, h), M_STONE, tone=b.rng.random(), jitter=0.002)
        elif (i + (1 if flip else 0)) % 2 == 1:
            for k, yy in enumerate((-0.5, 0.5)):
                m = M_CHARCOAL if (repair and i == 3 and k == 1) else mat
                b.box((xc, yy, z + h / 2), (w - 2 * g, 1.0 - 2 * g, h - 2 * g), m, tone=b.rng.random(), jitter=0.003)
        else:
            b.box((xc, 0, z + h / 2), (w - 2 * g, d - 2 * g, h - 2 * g), mat, tone=b.rng.random(), jitter=0.003)
        z += h
    # impost cornice projects toward the opening
    inward = 1 if xc < 0 else -1
    b.box((xc + inward * 0.2, 0, 4.55), (1.9, 2.3, 0.30), M_STONE, tone=0.5)
    b.bevel(0.03, 2)
    for sy in (-1, 1):
        b.box((xc, sy * 1.015, 2.2), (1.0, 0.04, 2.7), M_STONE, tone=0.5)
        relief_sun(b, (xc, sy * 1.035, 2.9), (0, sy, 0), s=1.0, stud=M_GOLD if sy < 0 else M_BRONZE)
        for k in range(3):
            b.lathe([(0.04, 0.0), (0.04, 0.03)], seg=12, center=(xc - 0.25 + 0.25 * k, sy * 1.035, 1.35), rot=(-sy * math.pi / 2, 0, 0), mat=M_BRONZE, tone=0.5, dz=0.03)
    b.bevel(0.008, 1)
    return finish(b, 0.14, warp=(0.010, 0.7), chip=(0.028, 6.0), fine=(0.0025, 16.0))


def arch_pierL():
    return _pier('Arch_A_PierL', -3.25, 51, False, True)


def arch_pierR():
    return _pier('Arch_A_PierR', 3.25, 52, True, False)


def arch_span():
    b = B('Arch_A_Span', seed=53)
    zs, ri, ro, d = 4.70, 2.50, 3.35, 2.0
    n = 17
    for i in range(n):
        a, c = math.pi * i / n + 0.003, math.pi * (i + 1) / n - 0.003
        key = (i == n // 2)
        rout = ro + (0.28 if key else 0.0)
        dd = d + (0.06 if key else 0.0)
        pts = []
        for y in (-dd / 2, dd / 2):
            pts += [(ri * math.cos(a), y, zs + ri * math.sin(a)), (rout * math.cos(a), y, zs + rout * math.sin(a)),
                    (rout * math.cos(c), y, zs + rout * math.sin(c)), (ri * math.cos(c), y, zs + ri * math.sin(c))]
        b.hexa(pts, M_STONE, tone=b.rng.random())
    b.bevel(0.025, 2)
    # spandrel masonry courses (outside the extrados)
    rs = 3.30
    xc = lambda z: math.sqrt(max(0.0, rs * rs - (z - zs) ** 2))
    levels = [4.70, 5.45, 6.20, 6.95, 7.70, 8.0]
    for j in range(len(levels) - 1):
        za, zb = levels[j] + 0.006, levels[j + 1] - 0.006
        for side in (-1, 1):
            pts = [(side * 4.0, za), (side * xc(za), za)]
            m = 6
            for k in range(1, m + 1):
                zz = za + (zb - za) * k / m
                pts.append((side * xc(zz), zz))
            pts.append((side * 4.0, zb))
            if side == 1:
                pts = list(reversed(pts))
            b.prism(pts, -0.9, 0.9, M_STONE, tone=b.rng.random())
    b.bevel(0.03, 2)
    # top courses + cornice
    for k, (x0, x1) in enumerate(((-4.0, -1.4), (-1.4, 1.5), (1.5, 4.0))):
        b.box(((x0 + x1) / 2, 0, 8.25), (x1 - x0 - 0.016, 1.8, 0.44), M_STONE, tone=b.rng.random(), jitter=0.002)
    b.box((0, 0, 8.58), (8.5, 2.3, 0.26), M_STONE, tone=0.5)
    b.box((0, 0, 8.76), (8.2, 2.1, 0.12), M_STONE, tone=0.55)
    b.bevel(0.03, 2)
    # keystone relief + gold intrados bands (accent only)
    zk = zs + (ri + ro) / 2 + 0.12
    for sy in (-1, 1):
        relief_sun(b, (0, sy * (d / 2 + 0.03), zk), (0, sy, 0), s=1.25, stud=M_GOLD)
        b.torus((0, sy * (d / 2 - 0.005), zs), ri + 0.02, 0.028, rot=(math.pi / 2, 0, 0), seg=64, sseg=8, mat=M_GOLD, tone=0.5, arc=(0, math.pi), stretch=0.8)
    b.bevel(0.006, 1)
    return finish(b, 0.14, warp=(0.010, 0.7), chip=(0.030, 6.0), fine=(0.0025, 16.0), pin_z0=False)


# ------------------------------------------------------------------ altar (abstract celestial focal point)
def altar():
    b = B('Altar_A', seed=61)
    b.box((0, 0, 0.125), (3.2, 3.2, 0.25), M_STONE, tone=0.5); b.bevel(0.03, 2)
    b.box((0, 0, 0.375), (2.7, 2.7, 0.25), M_STONE, tone=0.45); b.bevel(0.03, 2)
    b.box((0, 0.1, 1.05), (1.8, 1.2, 1.1), M_STONE, tone=0.55)
    b.box((0, 0.1, 1.68), (2.15, 1.5, 0.2), M_STONE, tone=0.5)
    b.bevel(0.03, 2)
    b.box((0, 0.1, 1.15), (1.84, 1.24, 0.05), M_GOLD, tone=0.5)        # single restrained gold band
    b.bevel(0.008, 1)
    # crimson runner draped over the altar front
    b.box((0, 0.1, 1.795), (1.0, 1.0, 0.02), M_CRIMSON, tone=0.5)
    b.box((0, 0.74, 1.35), (1.0, 0.02, 0.78), M_CRIMSON, tone=0.5)
    # standing 'sun disc' behind the altar on a socket block
    b.box((0, -1.25, 0.8), (1.5, 0.9, 0.7), M_STONE, tone=0.5); b.bevel(0.03, 2)
    zc, yc = 2.9, -1.25
    b.annulus((0, yc - 0.2, zc), (0, 1, 0), 1.10, 1.62, 0.40, seg=72, mat=M_STONE, tone=0.5)
    b.bevel(0.03, 2)
    for i in range(16):
        a = TAU * i / 16 + 0.1
        L = 0.62 if i % 2 == 0 else 0.34
        m = Matrix.Translation((0, yc, zc)) @ Matrix.Rotation(a, 4, 'Y') @ Matrix.Translation((0, 0, 1.62 + L / 2 - 0.02))
        # rays lie in the XZ plane; rotate about Y so +Z points outward radially
        b.box_m(m, (0.20, 0.34, L), M_STONE, 0.5)
    b.bevel(0.025, 2)
    b.torus((0, yc + 0.0, zc), 1.36, 0.035, rot=(math.pi / 2, 0, 0), seg=96, sseg=8, mat=M_BRONZE, tone=0.5, stretch=1.0)
    # gimballed bronze rings around an ember core (selective warm emissive)
    zc2, yc2 = 2.6, 0.1
    for (rx, ry, R) in ((0, 0, 0.60), (math.pi / 2, 0, 0.60), (math.pi / 3, math.pi / 4, 0.76)):
        b.torus((0, yc2, zc2), R, 0.032, rot=(rx, ry, 0), seg=64, sseg=8, mat=M_BRONZE, tone=0.5)
    b.lathe([(0.20, 0.0), (0.22, 0.06), (0.22, 0.16), (0.20, 0.22)], seg=24, center=(0, yc2, zc2 - 0.11), mat=M_EMBER, tone=0.5, dz=0.06)
    b.lathe([(0.10, 0.0), (0.10, 0.80)], seg=16, center=(0, yc2, 1.78), mat=M_BRONZE, tone=0.5, dz=0.2)   # stem to the altar slab
    b.lathe([(0.30, 0.0), (0.30, 0.05)], seg=24, center=(0, yc2, 1.78), mat=M_GOLD, tone=0.5, dz=0.05)
    return finish(b, 0.08, warp=(0.007, 0.8), chip=(0.020, 6.0), fine=(0.002, 18.0))


# ------------------------------------------------------------------ props
def brazier():
    b = B('Brazier_A', seed=71)
    b.lathe([(0.40, 0.0), (0.40, 0.16)], seg=8, mat=M_STONE, tone=0.5, rot_phase=math.pi / 8, dz=0.16); b.bevel(0.02, 2)
    b.lathe([(0.20, 0.16), (0.12, 0.30), (0.09, 0.55), (0.12, 0.80), (0.22, 0.92)], seg=24, mat=M_BRONZE, tone=0.5, dz=0.1)
    b.lathe([(0.12, 0.90), (0.30, 0.96), (0.46, 1.14), (0.52, 1.28), (0.53, 1.34), (0.49, 1.34), (0.44, 1.16), (0.28, 1.04)],
            seg=32, mat=M_BRONZE, tone=0.5, dz=0.08)
    b.lathe([(0.30, 1.03), (0.40, 1.12), (0.34, 1.20), (0.18, 1.25)], seg=20, mat=M_EMBER, tone=0.5, dz=0.05)
    return finish(b, 0.05, warp=(0.004, 1.2), chip=(0.012, 8.0), fine=(0.0015, 22.0))


def _chunk(b, c, size, n=18, tilt=0.25):
    """Fractured stone: convex hull of random points on a truncated ellipsoid (flat floor contact)."""
    import bmesh
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
    b._tag(out, M_STONE, b.rng.random())


def rubble_A():
    b = B('Rubble_A', seed=81)
    _chunk(b, (0, 0, 0), (1.0, 0.8, 0.65)); _chunk(b, (0.85, 0.4, 0), (0.6, 0.5, 0.40)); _chunk(b, (-0.5, 0.8, 0), (0.45, 0.4, 0.30))
    b.bevel(0.03, 2, angle=20)
    return finish(b, 0.07, warp=(0.008, 1.0), chip=(0.03, 5.0), fine=(0.003, 14.0))


def rubble_B():
    b = B('Rubble_B', seed=82)
    _chunk(b, (0, 0, 0), (1.4, 0.9, 0.28)); _chunk(b, (0.6, -0.65, 0), (0.65, 0.55, 0.45)); _chunk(b, (-0.75, 0.6, 0), (0.45, 0.35, 0.22))
    b.bevel(0.025, 2, angle=20)
    return finish(b, 0.07, warp=(0.008, 1.0), chip=(0.03, 5.0), fine=(0.003, 14.0))


def column_drum():
    b = B('ColumnDrum_A', seed=83)
    b.lathe([(0.56, -0.62), (0.55, 0.0), (0.54, 0.62)], seg=96, center=(0, 0, 0.55), rot=(0, math.pi / 2, 0.3), mat=M_STONE, tone=0.5,
            radial=_flute(16, 0.07), dz=0.3)
    b.bevel(0.014, 1)
    return finish(b, 0.09, warp=(0.008, 0.8), chip=(0.03, 6.0), fine=(0.002, 18.0))


def banner():
    b = B('Banner_A', seed=91)
    b.box((0, 0, 1.2), (1.1, 0.018, 2.4), M_CRIMSON, tone=0.5)
    b.box((0, 0.0, 0.04), (1.12, 0.036, 0.075), M_GOLD, tone=0.5)
    b.lathe([(0.03, -0.78), (0.03, 0.78)], seg=16, center=(0, 0, 2.47), rot=(0, math.pi / 2, 0), mat=M_BRONZE, tone=0.5, dz=0.2)
    for sx in (-1, 1):
        b.lathe([(0.045, 0.0), (0.045, 0.06)], seg=16, center=(sx * 0.78, 0, 2.47), rot=(0, math.pi / 2, 0), mat=M_BRONZE, tone=0.5, dz=0.06)

    def folds(bm):
        for v in bm.verts:
            if v.co.z > 0.08 and v.co.z < 2.42 and abs(v.co.x) < 0.56:
                v.co.y += 0.045 * math.sin(v.co.x * 7.0 + 0.8) * (0.35 + 0.65 * v.co.z / 2.4) + 0.012 * math.sin(v.co.z * 5.0)
    return finish(b, 0.06, warp=(0.0, 1.0), chip=(0.0, 1.0), fine=(0.0008, 25.0), pin_z0=False, hook=folds)


# ------------------------------------------------------------------ walls
def _wall(name, seed, panel):
    b = B(name, seed=seed)
    g = 0.006
    hs = [0.5] * 6
    z = 0.0
    for i, h in enumerate(hs):
        d = 1.08 if i == 0 else (1.14 if i == 5 else 1.0)
        x = -2.0
        cuts = []
        pos = -2.0 + (0.0 if i % 2 == 0 else b.rng.uniform(0.5, 1.0))
        cuts = [-2.0]
        while pos < 2.0 - 0.6:
            if pos > -2.0 + 0.4:
                cuts.append(pos)
            pos += b.rng.uniform(0.9, 1.6)
        cuts.append(2.0)
        for k in range(len(cuts) - 1):
            x0, x1 = cuts[k] + (g if k else 0.0), cuts[k + 1] - (g if k < len(cuts) - 2 else 0.0)
            b.box(((x0 + x1) / 2, 0, z + h / 2), (x1 - x0 - g, d - 2 * g, h - 2 * g), M_STONE, tone=b.rng.random(), jitter=0.002)
        z += h
    b.bevel(0.022, 2)
    if panel:
        b.box((0, -0.535, 1.55), (2.1, 0.07, 1.35), M_STONE, tone=0.5)
        b.bevel(0.02, 2)
        relief_sun(b, (0, -0.57, 1.55), (0, -1, 0), s=1.7, stud=M_GOLD)
        for sx in (-1, 1):
            b.box((sx * 0.98, -0.585, 1.55), (0.035, 0.02, 1.2), M_BRONZE, tone=0.5)
        b.bevel(0.006, 1)
    return finish(b, 0.14, warp=(0.010, 0.7), chip=(0.026, 6.0), fine=(0.0025, 16.0))


def wall_A():
    return _wall('Wall_A', 101, False)


def wall_B():
    return _wall('Wall_B', 102, True)


# ------------------------------------------------------------------ registry
# name -> dict(parts=[(suffix, builder)], density target px/m, props)
REG = [
    # category, asset, parts, target px/m, value_mult, wear_mult, damp_mult
    ('Floor', 'Floor_A', [('', lambda: floor_tile('A'))], 220, 0.78, 1.0, 0.0),
    ('Floor', 'Floor_B', [('', lambda: floor_tile('B'))], 220, 0.78, 1.0, 0.0),
    ('Floor', 'Floor_C', [('', lambda: floor_tile('C'))], 220, 0.76, 1.0, 0.0),
    ('Floor', 'Floor_D', [('', lambda: floor_tile('D'))], 220, 0.80, 1.0, 0.0),
    ('Floor', 'FloorBorder_Straight_A', [('', border_straight)], 280, 0.88, 1.0, 0.0),
    ('Floor', 'FloorBorder_Corner_A', [('', border_corner)], 280, 0.88, 1.0, 0.0),
    ('Stair', 'Stairs_A', [('', stairs)], 240, 0.95, 1.0, 0.7),
    ('Stair', 'Platform_A', [('', platform)], 200, 0.95, 1.0, 0.7),
    ('Pillar', 'Pillar_A', [('', pillar_A)], 300, 1.0, 1.0, 1.0),
    ('Pillar', 'Pillar_B', [('', pillar_B)], 300, 1.0, 1.0, 1.0),
    ('Pillar', 'Pillar_C', [('', pillar_C)], 300, 1.0, 1.0, 1.0),
    ('Pillar', 'Pillar_D', [('', pillar_D)], 300, 0.95, 1.2, 1.2),
    ('Arch', 'Arch_A', [('_PierL', arch_pierL), ('_PierR', arch_pierR), ('_Span', arch_span)], 220, 1.0, 1.0, 1.0),
    ('Focal', 'Altar_A', [('', altar)], 280, 1.0, 1.0, 0.8),
    ('Prop', 'Brazier_A', [('', brazier)], 300, 1.0, 1.0, 0.5),
    ('Prop', 'Rubble_A', [('', rubble_A)], 300, 0.92, 1.2, 1.0),
    ('Prop', 'Rubble_B', [('', rubble_B)], 300, 0.92, 1.2, 1.0),
    ('Prop', 'ColumnDrum_A', [('', column_drum)], 300, 0.95, 1.1, 1.0),
    ('Prop', 'Banner_A', [('', banner)], 300, 1.0, 0.0, 0.0),
    ('Wall', 'Wall_A', [('', wall_A)], 240, 1.0, 1.0, 1.0),
    ('Wall', 'Wall_B', [('', wall_B)], 240, 1.0, 1.0, 1.0),
]

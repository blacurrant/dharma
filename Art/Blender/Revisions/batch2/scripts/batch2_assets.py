"""Batch-2 asset builders (zone-baked architecture): Wall_Tall_Lamp_A, Shrine_Backdrop_A, Column_Tall_A.
Same conventions as Batch 1 (1 BU = 1 m, +Z up, local +Y = 'front' = OUTWARD for wall bays, arena side = -Y). Reuses batch1_assets helpers.
"""
import math
from mathutils import Vector, Matrix
from kitlib import B, M_STONE, M_CHARCOAL, M_BRONZE, M_GOLD, M_CRIMSON, M_EMBER, TAU
from assets import _flute
import batch1_assets as B1
from batch1_assets import fin, _carve, _courses, ZVIS


# ------------------------------------------------------------------ lamp bay
LLAMP = 1.0


def _grille_holes(x0, x1, z0, z1):
    """Abstract pierced pattern: staggered grid of large/small square apertures (chequered grille). Rectangles inside the frame only."""
    holes = []
    cell = 0.32
    nx = int((x1 - x0 - 0.16) / cell)
    xs0 = x0 + 0.08 + ((x1 - x0 - 0.16) - nx * cell) / 2
    rows = 3
    ch = (z1 - z0 - 0.16) / rows
    for r in range(rows):
        zc = z0 + 0.08 + ch * (r + 0.5)
        for c in range(nx):
            xc = xs0 + cell * (c + 0.5)
            big = (c + r) % 2 == 0
            hw, hh = (0.105, ch * 0.34) if big else (0.050, ch * 0.18)
            holes.append((xc - hw, xc + hw, zc - hh, zc + hh))
    return holes


def wall_tall_lamp():
    """4 m bay, 5.0 m tall (same piers/caps/plinth as Wall_Tall_A so it tiles). Front layer carries a row of three lamp niches with a bronze
    bowl and emissive flame, and above it a recessed pierced stone screen (chequered square apertures) in front of a warm glow plane.
    Visible band from the gameplay camera is z > ~2.2 m, so the features sit at z 2.8 .. 4.4."""
    b = B('Wall_Tall_Lamp_A', seed=211)
    H = 5.0
    YB = 0.60
    FL0, FL1, FLD = -0.25, 0.10, 0.24            # face plane, normal recess back plane, deep pocket back plane
    zb = 0.40
    top_base = 4.55
    b.box((0, 0, 0.0), (4.0, 1.2, 0.80), M_CHARCOAL, tone=0.35)
    b.box((0, -0.04, 0.46), (4.0, 1.12, 0.12), M_STONE, tone=0.5)
    lamp_holes = [(-1.16, -0.76, 2.78, 3.38), (-0.20, 0.20, 2.78, 3.38), (0.76, 1.16, 2.78, 3.38)]
    screen = (-1.30, 1.30, 3.62, 4.42)
    pockets = lamp_holes + [screen]
    # back panel (carved by pockets) + deep pocket floors
    for (x0, x1, za, zc) in _carve(-1.5, 1.5, zb, top_base, pockets):
        b.box(((x0 + x1) / 2, (FL1 + YB) / 2, (za + zc) / 2), (x1 - x0, YB - FL1, zc - za), M_STONE, tone=b.rng.random())
    for (x0, x1, za, zc) in pockets:
        b.box(((x0 + x1) / 2, (FLD + YB) / 2, (za + zc) / 2), (x1 - x0, YB - FLD, zc - za), M_CHARCOAL, tone=0.35)
    # front layer with pockets cut out
    for (x0, x1, za, zc) in _carve(-1.5, 1.5, zb, top_base, pockets):
        b.box(((x0 + x1) / 2, (FL0 + FL1) / 2, (za + zc) / 2), (x1 - x0, FL1 - FL0, zc - za), M_STONE, tone=b.rng.random())
    # pocket side walls (between face plane and the deep back plane: the front layer already spans FL0..FL1, so add FL1..FLD liners)
    for (x0, x1, za, zc) in pockets:
        zm = (za + zc) / 2
        b.box((x0 - 0.02, (FL1 + FLD) / 2, zm), (0.04, FLD - FL1, zc - za), M_STONE, tone=0.5)
        b.box((x1 + 0.02, (FL1 + FLD) / 2, zm), (0.04, FLD - FL1, zc - za), M_STONE, tone=0.5)
        b.box(((x0 + x1) / 2, (FL1 + FLD) / 2, za - 0.02), (x1 - x0 + 0.08, FLD - FL1, 0.04), M_STONE, tone=0.5)
        b.box(((x0 + x1) / 2, (FL1 + FLD) / 2, zc + 0.02), (x1 - x0 + 0.08, FLD - FL1, 0.04), M_STONE, tone=0.5)
    # ledges: sill under the lamp row, projecting lintel above the screen, string course
    b.box((0, FL0 - 0.05, 2.78 - 0.07), (3.0, 0.14, 0.14), M_STONE, tone=0.55)
    b.box((0, FL0 - 0.06, 3.46), (3.0, 0.12, 0.08), M_STONE, tone=0.55)
    b.box((0, FL0 - 0.05, 4.42 + 0.06), (3.0, 0.14, 0.12), M_STONE, tone=0.5)
    b.box((0, FL0 - 0.04, 2.20), (3.0, 0.12, 0.10), M_STONE, tone=0.5)
    # piers (same as Wall_Tall_A)
    for sx in (-1, 1):
        cx = sx * 1.75
        b.box((cx, 0.0, (zb + 2.3) / 2), (0.5, 1.2, 2.3 - zb), M_STONE, tone=b.rng.random())
        b.box((cx, 0.0, (2.3 + H - 0.55) / 2), (0.5, 1.16, H - 0.55 - 2.3), M_STONE, tone=b.rng.random())
        b.box((cx, 0.0, 2.3), (0.5, 1.24, 0.10), M_STONE, tone=0.55)
        b.box((cx, 0.0, H - 0.64), (0.504, 1.23, 0.07), M_BRONZE, tone=0.5)
        b.box((cx - sx * 0.07, 0.0, H - 0.27), (0.5 + 0.14, 1.28, 0.54), M_STONE, tone=0.6)
    b.bevel(0.03, 1, angle=34)
    # coursing above the parapet-hidden zone, hole-aware (pockets are holes)
    _courses(b, -1.5, 1.5, ZVIS, top_base, pockets, FL0, 0.07, course_h=0.55, zgrid0=ZVIS, jitter=0.010)
    # ragged weathered top
    xs = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
    for i, h in enumerate([0.0, 0.36, 0.20, 0.0, 0.40, 0.14]):
        if h > 0:
            b.box(((xs[i] + xs[i + 1]) / 2, (FL0 + YB) / 2 - 0.05, top_base + h / 2), (0.5 - 0.012, YB - FL0 - 0.1, h), M_STONE, tone=b.rng.random(), jitter=0.01)
    # pierced screen (square apertures) in the middle of the pocket depth + glow plane behind it
    sx0, sx1, sz0, sz1 = screen
    gy = -0.02
    for (x0, x1, za, zc) in _carve(sx0 + 0.02, sx1 - 0.02, sz0 + 0.02, sz1 - 0.02, _grille_holes(sx0, sx1, sz0, sz1)):
        b.box(((x0 + x1) / 2, gy, (za + zc) / 2), (x1 - x0, 0.16, zc - za), M_STONE, tone=b.rng.random())
    b.box((0, FLD - 0.03, (sz0 + sz1) / 2), ((sx1 - sx0) - 0.04, 0.03, (sz1 - sz0) - 0.04), M_EMBER, tone=0.5)
    # lamps: bronze bowl + emissive flame in each niche
    for (x0, x1, za, zc) in lamp_holes:
        cx = (x0 + x1) / 2
        b.box((cx, 0.05, za + 0.03), (x1 - x0 - 0.04, 0.34, 0.05), M_BRONZE, tone=0.5)                       # bronze tray
        b.lathe([(0.05, za + 0.05), (0.11, za + 0.08), (0.16, za + 0.17), (0.13, za + 0.17), (0.08, za + 0.11)], seg=12, center=(cx, 0.04, 0), mat=M_BRONZE, tone=0.5, dz=0.01)
        b.lathe([(0.0, za + 0.12), (0.07, za + 0.15), (0.08, za + 0.25), (0.05, za + 0.36), (0.0, za + 0.46)], seg=8, center=(cx, 0.04, 0), mat=M_EMBER, tone=0.5, dz=0.01, rot_phase=0.3)
    return fin(b, LLAMP, warp=(0.014, 0.55), chip=(0.040, 3.2), fine=(0.004, 8.0), edge_ang=0.35)


# ------------------------------------------------------------------ shrine backdrop (altar frame)
LSHR = 1.0


def shrine_backdrop():
    """Abstract stepped shrine mass for the NW corner behind the dais. Local frame: arena side = -Y, origin at base centre of the front face line.
    4 tiers (12 x 4.8 / 10 x 4.0 / 7.4 x 3.2 / 5 x 2.4 m, 8.6 m tall), central tall recess + two side niches, vertical slit rows, plain bronze bands,
    cornices and a stepped crown. No figure, no deity, no ring/sun motif, no iconography."""
    b = B('Shrine_Backdrop_A', seed=231)
    # tier t: (width, depth, z0, z1); each tier's back edge aligned at y = +D0 so the mass reads as a stepped block against a wall
    T = [(12.0, 5.0, 0.0, 2.3), (10.0, 4.2, 2.3, 5.1), (7.4, 3.4, 5.1, 7.3), (5.0, 2.6, 7.3, 8.6)]
    back = 5.0
    ys = []
    for (w, d, z0, z1) in T:
        yc = back - d / 2
        ys.append(yc)
        b.box((0, yc, (z0 + z1) / 2), (w, d, z1 - z0), M_STONE, tone=b.rng.random())
        b.box((0, yc - 0.10, z1 + 0.06), (w + 0.34, d + 0.34, 0.12), M_STONE, tone=0.55)          # cornice slab on each tier
    # front steps (3) in front of tier 1
    for i in range(3):
        b.box((0, -0.0 - 0.36 * (i + 1) - 0.0, 0.17 * (i + 1) / 2 + 0.0), (12.0 - 0.9 * i, 0.72, 0.17 * (i + 1)), M_STONE, tone=b.rng.random())
    # central tall recess (dark) cut on tiers 2-3 front faces, flanked by piers: built as charcoal slab proud of the face + stone jambs
    yf2 = back - T[1][1]                                                        # tier-2 front face y
    yf3 = back - T[2][1]
    yf4 = back - T[3][1]
    yf1 = back - T[0][1]
    b.box((0, yf1 - 0.04, 1.15), (3.2, 0.10, 2.0), M_CHARCOAL, tone=0.3)                    # tier-1 door-like recess panel (just dark stone)
    for sx in (-1, 1):
        b.box((sx * 1.9, yf1 - 0.10, 1.2), (0.5, 0.2, 2.2), M_STONE, tone=0.5)
    # tier 2: central tall niche (stepped head) + 2 side niches, expressed as dark charcoal inset plates with raised stone frames
    b.box((0, yf2 - 0.03, 3.9), (2.4, 0.08, 2.5), M_CHARCOAL, tone=0.25)
    b.box((0, yf2 - 0.03, 5.18), (1.7, 0.08, 0.35), M_CHARCOAL, tone=0.25)
    for sx in (-1, 1):
        b.box((sx * 1.45, yf2 - 0.14, 3.9), (0.34, 0.28, 2.7), M_STONE, tone=0.55)           # jambs of the central niche
        b.box((sx * 3.7, yf2 - 0.03, 3.8), (1.2, 0.08, 1.9), M_CHARCOAL, tone=0.25)          # side niches
        b.box((sx * 3.7, yf2 - 0.12, 4.88), (1.5, 0.24, 0.16), M_STONE, tone=0.55)
        b.box((sx * 3.7, yf2 - 0.12, 2.72), (1.5, 0.24, 0.16), M_STONE, tone=0.55)
    b.box((0, yf2 - 0.12, 5.18 + 0.1), (2.7, 0.24, 0.14), M_STONE, tone=0.55)               # lintel over the central niche
    b.box((0, yf2 - 0.14, 2.68), (2.9, 0.28, 0.16), M_STONE, tone=0.55)                      # sill
    # bronze bands (plain rectangular)
    for z, w in ((2.30 + 0.03, 12.04), (5.10 + 0.03, 10.04)):
        pass
    b.box((0, back - T[1][1] / 2 - 0.00, 2.30 + 0.14), (10.04, T[1][1] + 0.04, 0.07), M_BRONZE, tone=0.5)
    b.box((0, back - T[2][1] / 2, 5.10 + 0.14), (7.44, T[2][1] + 0.04, 0.07), M_BRONZE, tone=0.5)
    # tier 3: row of 5 vertical slits (dark) + piers
    for i in range(5):
        x = (i - 2) * 1.2
        b.box((x, yf3 - 0.03, 6.2), (0.34, 0.08, 1.5), M_CHARCOAL, tone=0.25)
        b.box((x, yf3 - 0.10, 7.0), (0.52, 0.20, 0.12), M_STONE, tone=0.55)
    # tier 4: three stepped merlon blocks on the crown, plain
    for i in range(3):
        x = (i - 1) * 1.6
        hh = 0.55 + (0.25 if i == 1 else 0.0)
        b.box((x, back - T[3][1] / 2, 8.6 + 0.12 + hh / 2), (0.9, 1.5, hh), M_STONE, tone=b.rng.random())
    # corner pilasters (full height of tier 1 and 2)
    for sx in (-1, 1):
        b.box((sx * (6.0 - 0.3), yf1 - 0.12, 1.15), (0.6, 0.30, 2.3), M_STONE, tone=0.5)
        b.box((sx * (5.0 - 0.28), yf2 - 0.12, 3.7), (0.56, 0.30, 2.8), M_STONE, tone=0.5)
    b.bevel(0.07, 1, angle=34)
    # coursing on the tier faces (above nothing hidden: this whole mass is visible)
    H1 = [(-1.75, 1.75, 0.0, 2.3)]
    H2 = [(-1.45, 1.45, 2.5, 5.4), (-4.45, -2.95, 2.6, 5.0), (2.95, 4.45, 2.6, 5.0)]
    H3 = [((i - 2) * 1.2 - 0.3, (i - 2) * 1.2 + 0.3, 5.4, 7.15) for i in range(5)]
    for (w, d, z0, z1), yf, hl in zip(T[:3], (yf1, yf2, yf3), (H1, H2, H3)):
        _courses(b, -w / 2 + 0.3, w / 2 - 0.3, z0 + 0.1, z1 - 0.1, hl, yf, 0.08, course_h=0.75, zgrid0=z0 + 0.1, jitter=0.02, charcoal_p=0.08)
    return fin(b, LSHR, warp=(0.05, 0.35), chip=(0.07, 2.2), fine=(0.010, 6.0), edge_ang=0.35)


# ------------------------------------------------------------------ tall column
LCOL = 0.5


def column_tall():
    """Tall slender column, 6.8 m: battered square plinth, fluted tapered shaft, plain bronze bands, stepped capital + abacus. Pivot at base centre."""
    b = B('Column_Tall_A', seed=241)
    b.box((0, 0, 0.12), (1.60, 1.60, 0.24), M_STONE, tone=0.5)
    b.box((0, 0, 0.36), (1.30, 1.30, 0.24), M_STONE, tone=0.45)
    b.box((0, 0, 0.58), (1.10, 1.10, 0.20), M_STONE, tone=0.55)
    shaft = [(0.46, 0.68), (0.47, 0.8), (0.455, 2.0), (0.43, 3.8), (0.40, 5.4), (0.385, 6.1), (0.38, 6.2)]
    b.lathe(shaft, seg=48, mat=M_STONE, tone=0.5, radial=_flute(12, 0.045), dz=0.15)
    b.lathe([(0.495, 0.62), (0.495, 0.72)], seg=24, mat=M_STONE, tone=0.5, dz=0.01)
    for z in (2.2, 5.7):
        b.lathe([(0.47 - (0.0 if z < 3 else 0.06), z), (0.47 - (0.0 if z < 3 else 0.06), z + 0.14)], seg=24, mat=M_BRONZE, tone=0.5, dz=0.01)
    for z0, z1, w in ((6.20, 6.32, 0.78), (6.32, 6.46, 0.96), (6.46, 6.62, 1.12), (6.62, 6.78, 1.24)):
        b.box((0, 0, (z0 + z1) / 2), (w, w, z1 - z0), M_STONE, tone=b.rng.random())
    b.bevel(0.03, 1, angle=34)
    return fin(b, LCOL, warp=(0.010, 0.8), chip=(0.020, 5.0), fine=(0.003, 14.0), edge_ang=0.4)


# ------------------------------------------------------------------ paving (irregular flagstones + kerb)
def _flag_poly(rng, w, d, n):
    """Boxy slab outline: rectangle with cut/chipped corners and jittered edge points (n only sets the minimum count of edge points)."""
    hw, hd = w / 2, d / 2
    pts = []
    corners = [(-hw, -hd, 1, 1), (hw, -hd, -1, 1), (hw, hd, -1, -1), (-hw, hd, 1, -1)]
    for k, (cx, cy, sx, sy) in enumerate(corners):
        c1, c2 = rng.uniform(0.05, 0.22), rng.uniform(0.05, 0.22)
        a = (cx + sx * c1, cy)
        b = (cx, cy + sy * c2)
        pass
    # walk the outline: bottom edge (left->right), right edge (bottom->top), top edge (right->left), left edge (top->bottom)
    def jit(v, a=0.045):
        return v + rng.uniform(-a, a)
    ch = [rng.uniform(0.06, 0.24) for _ in range(8)]
    k = max(1, (n - 8) // 4)
    out = []
    out.append((-hw + ch[0], jit(-hd)))
    for i in range(k):
        out.append((-hw + (i + 1) * w / (k + 1), jit(-hd)))
    out.append((hw - ch[1], jit(-hd)))
    out.append((jit(hw), -hd + ch[2]))
    for i in range(k):
        out.append((jit(hw), -hd + (i + 1) * d / (k + 1)))
    out.append((jit(hw), hd - ch[3]))
    out.append((hw - ch[4], jit(hd)))
    for i in range(k):
        out.append((hw - (i + 1) * w / (k + 1), jit(hd)))
    out.append((-hw + ch[5], jit(hd)))
    out.append((jit(-hw), hd - ch[6]))
    for i in range(k):
        out.append((jit(-hw), hd - (i + 1) * d / (k + 1)))
    out.append((jit(-hw), -hd + ch[7]))
    return out


def _flag(name, seed, w, d, n, zt=0.06, L=0.16):
    b = B(name, seed=seed)
    pts = _flag_poly(b.rng, w, d, n)
    zb = -0.03
    f = [b.bm.verts.new((x, y, zb)) for x, y in pts]
    k = [b.bm.verts.new((x, y, zt)) for x, y in pts]
    m = len(pts)
    b.bm.faces.new(list(reversed(f))); b.bm.faces.new(k)
    for i in range(m):
        j = (i + 1) % m
        b.bm.faces.new((f[i], f[j], k[j], k[i]))
    b._tag(f + k, M_STONE, 0.5)
    b.bevel(0.014, 1, angle=30)
    b.drop_bottom(z=zb + 0.002)
    b.unwrap()
    b.sculpt(L=L, warp=(0.010, 0.5), chip=(0.026, 4.5), fine=(0.003, 10.0), edge_ang=0.5, pin_z0=False)
    b.shade()
    return b


def flagstone_A():
    return _flag('Flagstone_A', 251, 1.1, 2.0, 12)


def flagstone_B():
    return _flag('Flagstone_B', 252, 2.0, 3.0, 12, zt=0.055, L=0.22)


def flagstone_C():
    return _flag('Flagstone_C', 253, 3.0, 3.0, 16, zt=0.05, L=0.26)


def flagstone_D():
    return _flag('Flagstone_D', 254, 1.5, 1.5, 12, zt=0.065, L=0.14)


def kerb_A():
    b = B('Kerb_A', seed=255)
    b.box((0, 0, 0.01), (3.0, 0.42, 0.14), M_CHARCOAL, tone=0.35)
    b.box((0.0, 0.0, 0.06), (2.92, 0.36, 0.04), M_CHARCOAL, tone=0.5)
    b.bevel(0.03, 2, angle=30)
    b.drop_bottom(z=-0.07)
    b.unwrap()
    b.sculpt(L=0.3, warp=(0.008, 0.8), chip=(0.028, 4.0), fine=(0.003, 12.0), edge_ang=0.5, pin_z0=False)
    b.shade()
    return b


# name -> (category, builder, density target px/m, value_mult, wear_mult, damp_mult, texres cap)
REG2 = {
    'Wall_Tall_Lamp_A': ('Wall', wall_tall_lamp, 120, 0.93, 1.0, 1.0, 2048),
    'Shrine_Backdrop_A': ('Backdrop', shrine_backdrop, 70, 0.90, 1.0, 0.8, 2048),
    'Column_Tall_A': ('Prop', column_tall, 130, 0.95, 1.0, 1.0, 2048),
    'Flagstone_A': ('Floor', flagstone_A, 120, 1.0, 1.0, 0.0, 512),
    'Flagstone_B': ('Floor', flagstone_B, 100, 1.0, 1.0, 0.0, 1024),
    'Flagstone_C': ('Floor', flagstone_C, 90, 1.0, 1.0, 0.0, 1024),
    'Flagstone_D': ('Floor', flagstone_D, 120, 1.0, 1.0, 0.0, 512),
    'Kerb_A': ('Floor', kerb_A, 120, 0.9, 1.0, 0.0, 512),
}


# ------------------------------------------------------------------ low / broken wall bays (near-side counterweight, max 1.9 m)
def _low_bay(name, seed, variant):
    """4 m wide, collapsed bay: same plinth, half-piers and arena-facing -Y as Wall_Tall (tiles with the 4 m grid), but the top is broken
    down to 1.9 m (stub pier) / 0.5-1.5 m (stepped rubble crest). Variant A: left pier stands, right collapsed. Variant B: both piers broken, a notch in the middle."""
    b = B(name, seed=seed)
    A = variant == 'A'
    b.box((0, 0, 0.0), (4.0, 1.2, 0.80), M_CHARCOAL, tone=0.35)
    b.box((0, -0.04, 0.46), (4.0, 1.12, 0.12), M_STONE, tone=0.5)
    FL0, FL1, YB = -0.25, 0.10, 0.60
    hts = [1.9, 1.5, 1.2, 0.9, 0.7, 0.55] if A else [1.2, 1.45, 0.8, 0.55, 1.1, 0.9]       # per half-metre infill column
    xs = [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
    for i, h in enumerate(hts):
        b.box(((xs[i] + xs[i + 1]) / 2, (FL0 + YB) / 2, (0.4 + h) / 2), (0.5 - 0.012, YB - FL0, h - 0.4), M_STONE, tone=b.rng.random(), jitter=0.012)
    pier_h = [1.9, 0.95] if A else [1.35, 1.65]
    for sx, ph in zip((-1, 1), pier_h):
        cx = sx * 1.75
        b.box((cx, 0.0, (0.4 + ph) / 2), (0.5, 1.2, ph - 0.4), M_STONE, tone=b.rng.random())
        if ph > 1.5:
            b.box((cx, 0.0, ph - 0.05), (0.504, 1.23, 0.07), M_BRONZE, tone=0.5)
    b.bevel(0.03, 1, angle=34)
    # coursing on the visible face above the 0.4 plinth
    for (x0, x1, za, zc) in [(-1.5, 1.5, 0.6, 1.5)]:
        B1._courses(b, x0, x1, za, zc, [], FL0, 0.06, course_h=0.45, zgrid0=za, jitter=0.010)
    # a few fallen blocks on the arena side
    for k in range(3 if A else 4):
        px = b.rng.uniform(-1.4, 1.4); b.box((px, -0.9 - b.rng.uniform(0, 0.35), 0.17), (b.rng.uniform(0.35, 0.6), b.rng.uniform(0.3, 0.5), 0.34), M_STONE, tone=b.rng.random(), rot=(0, 0, b.rng.uniform(-0.5, 0.5)), jitter=0.01)
    return fin(b, 0.7, warp=(0.014, 0.55), chip=(0.045, 3.2), fine=(0.004, 8.0), edge_ang=0.35)


def wall_low_A():
    return _low_bay('Wall_Low_Broken_A', 261, 'A')


def wall_low_B():
    return _low_bay('Wall_Low_Broken_B', 262, 'B')


REG2['Wall_Low_Broken_A'] = ('Wall', wall_low_A, 120, 0.93, 1.1, 1.0, 2048)
REG2['Wall_Low_Broken_B'] = ('Wall', wall_low_B, 120, 0.93, 1.1, 1.0, 2048)

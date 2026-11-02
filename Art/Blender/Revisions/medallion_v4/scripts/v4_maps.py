# ENV_Temple_Central_Medallion v4 - stage 1: planar 4096 relief heightfield + colour fields.
# Masonry layout: centre stone + 3 rings of voussoir blocks (6 / 8 / 20) with real joints.
# Carving: concentric ridges, 4 emblem roundels, incised archaic glyph rows, running-scroll band,
# wear field, spalls, chips, cracks. All in metres; arrays are [row=y, col=x], row 0 = y=-EXT.
# Run: Blender -b --python v4_maps.py   (numpy only, no bpy needed beyond the interpreter)
import numpy as np, math, os, json, time

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion_v4'
CACHE = f'{ROOT}/cache'
os.makedirs(CACHE, exist_ok=True)
T0 = time.time()

EXT = 3.95                  # map half-extent (m)
N = 4096
PX = 2 * EXT / N            # 1.93 mm / px
R_OUT = 3.90
HG = 0.010                  # half joint gap
TAU = math.tau

c = ((np.arange(N) + 0.5) * PX - EXT).astype(np.float32)
X, Y = np.meshgrid(c, c)
R = np.hypot(X, Y)
TH = np.mod(np.arctan2(Y, X), TAU).astype(np.float32)

FX = np.fft.fftfreq(N).astype(np.float32)
FY = np.fft.rfftfreq(N).astype(np.float32)
F2 = FX[:, None] ** 2 + FY[None, :] ** 2


def blur(a, s):
    return np.fft.irfft2(np.fft.rfft2(a) * np.exp(-2 * np.pi ** 2 * s * s * F2), s=a.shape).astype(np.float32)


def fbm(seed, sig, w):
    g = np.random.default_rng(seed)
    out = np.zeros((N, N), np.float32)
    for s, k in zip(sig, w):
        n = blur(g.standard_normal((N, N), dtype=np.float32), s)
        out += k * n / (n.std() + 1e-9)
    return out / (out.std() + 1e-9)


def sst(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def log(*a):
    print(f'[{time.time() - T0:6.1f}s]', *a, flush=True)


# ---------------------------------------------------------------- layout
RINGS = [(0.0, 1.20, 1, 0.0), (1.20, 2.16, 6, 0.21), (2.16, 3.06, 8, math.radians(22.5)), (3.06, R_OUT, 20, 0.07)]
rng = np.random.default_rng(4242)
blocks = []
blk = np.full((N, N), -1, np.int32)
dedge = np.full((N, N), 9.0, np.float32)
for ri, (r0, r1, n, ph) in enumerate(RINGS):
    m = (R >= r0) & (R < r1)
    if n == 1:
        blocks.append(dict(id=len(blocks), ring=ri, r0=r0, r1=r1, a0=0.0, a1=TAU))
        blk[m] = blocks[-1]['id']
        dedge[m] = r1 - R[m]
        continue
    jit = rng.uniform(-0.22, 0.22, n) if ri == 3 else rng.uniform(-0.06, 0.06, n)
    b = np.sort(np.mod(ph + TAU * (np.arange(n) + jit) / n, TAU))
    base = len(blocks)
    for k in range(n):
        a0, a1 = b[k], b[(k + 1) % n]
        if a1 <= a0:
            a1 += TAU
        blocks.append(dict(id=base + k, ring=ri, r0=r0, r1=r1, a0=float(a0), a1=float(a1)))
    t = TH[m]
    idx = np.searchsorted(b, t)
    lo, hi = b[(idx - 1) % n], b[idx % n]
    dlo, dhi = np.mod(t - lo, TAU), np.mod(hi - t, TAU)
    blk[m] = base + (idx - 1) % n
    rr = R[m]
    dr = (rr - r0) if ri == 3 else np.minimum(rr - r0, r1 - rr)
    dedge[m] = np.minimum(dr, np.minimum(dlo, dhi) * rr)
nb = len(blocks)
for bl in blocks:  # settling: offset + tilt, centroid
    bl['off'] = float(rng.normal(0, 0.0028))
    bl['tilt'] = [float(rng.normal(0, 0.0035)), float(rng.normal(0, 0.0035))]
    if bl['ring'] == 0:
        bl['c'] = [0.0, 0.0]
    else:
        am, rm = 0.5 * (bl['a0'] + bl['a1']), 0.5 * (bl['r0'] + bl['r1'])
        bl['c'] = [rm * math.cos(am), rm * math.sin(am)]
    bl['tone'] = float(rng.normal(0, 1))
    bl['band'] = float(rng.uniform(0, math.pi))
log('layout', nb, 'blocks')

# ---------------------------------------------------------------- structural relief (not eroded)
Hs = np.zeros((N, N), np.float32)


def ridge(A, r0, w, h):
    Hs.__iadd__(h * (1 - sst(0.15 * w, w, np.abs(A - r0))))


def channel(A, r0, w, d, mask=None):
    v = d * (1 - sst(0.55 * w, w, np.abs(A - r0)))
    Hs.__isub__(v if mask is None else v * mask)


Hs -= 0.032 * (1 - sst(0.0, 0.40, R))           # ritual basin
Hs += 0.016 * (1 - sst(1.04, 1.16, R))          # raised centre plinth
ridge(R, 0.445, 0.032, 0.008)                   # basin lip
channel(R, 0.80, 0.024, 0.009)
ridge(R, 0.97, 0.026, 0.006)
for r0 in (1.29, 2.07, 2.25, 2.97, 3.15, 3.67):  # band border ridges
    ridge(R, r0, 0.030, 0.007)

ROUND_A = [math.radians(45 + 90 * k) for k in range(4)]
ROUND_R, ROUND_RAD = 2.61, 0.33
rmin = np.full((N, N), 9.0, np.float32)
for k, a in enumerate(ROUND_A):
    cx, cy = ROUND_R * math.cos(a), ROUND_R * math.sin(a)
    rr = np.hypot(X - cx, Y - cy)
    rmin = np.minimum(rmin, rr)
    Hs += 0.012 * (1 - sst(ROUND_RAD - 0.03, ROUND_RAD + 0.01, rr))
    Hs -= 0.008 * (1 - sst(0.55 * 0.018, 0.018, np.abs(rr - 0.275)))
    Hs += 0.005 * (1 - sst(0.004, 0.018, np.abs(rr - 0.243)))
    Hs += 0.006 * (1 - sst(0.03, 0.05, rr))      # central boss
lane = sst(ROUND_RAD + 0.03, ROUND_RAD + 0.07, rmin)
channel(R, 2.43, 0.013, 0.005, lane)            # incised guide lines of the glyph lane
channel(R, 2.80, 0.013, 0.005, lane)
log('structural relief')

# ---------------------------------------------------------------- carved detail (eroded later)
Hd = np.zeros((N, N), np.float32)
Hk = np.zeros((N, N), np.float32)                # cracks: never eroded


def carve(pts, hw, d, tgt=Hd, power=0.6):
    pts = np.asarray(pts, np.float64)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        x0, x1 = min(a[0], b[0]) - hw, max(a[0], b[0]) + hw
        y0, y1 = min(a[1], b[1]) - hw, max(a[1], b[1]) + hw
        i0, i1 = max(0, int((x0 + EXT) / PX)), min(N, int((x1 + EXT) / PX) + 2)
        j0, j1 = max(0, int((y0 + EXT) / PX)), min(N, int((y1 + EXT) / PX) + 2)
        if i1 <= i0 or j1 <= j0:
            continue
        px = c[i0:i1][None, :] - a[0]
        py = c[j0:j1][:, None] - a[1]
        ab = b - a
        L2 = ab @ ab + 1e-12
        t = np.clip((px * ab[0] + py * ab[1]) / L2, 0, 1)
        dist = np.hypot(px - t * ab[0], py - t * ab[1])
        prof = (-d * np.clip(1 - (dist / hw) ** 2, 0, 1) ** power).astype(np.float32)
        sub = tgt[j0:j1, i0:i1]
        np.minimum(sub, prof, out=sub)


def resample(pts, step=0.015, g=None, jit=0.0):
    pts = np.asarray(pts, np.float64)
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(np.linalg.norm(b - a) / step))
        for k in range(1, n + 1):
            p = a + (b - a) * k / n
            if g is not None and jit and k < n:
                p = p + g.normal(0, jit, 2)
            out.append(p)
    return np.array(out)


LAT = [(x, y) for y in (-0.5, 0.0, 0.5) for x in (-0.36, 0.0, 0.36)]


def make_glyph(g):
    S = []
    if g.random() < 0.6:
        x = float(g.choice([-0.36, 0.0, 0.36]))
        S.append([(x, -0.5), (x, 0.5)])
    for _ in range(int(g.integers(1, 4))):
        k = g.random()
        if k < 0.5:
            a, b = g.choice(9, 2, replace=False)
            S.append([LAT[a], LAT[b]])
        elif k < 0.82:
            cx, cy = LAT[int(g.integers(9))]
            rad, a0, sp = g.uniform(0.2, 0.36), g.uniform(0, TAU), g.uniform(2.0, 3.6)
            S.append([(cx + rad * math.cos(a0 + sp * t), cy + rad * math.sin(a0 + sp * t)) for t in np.linspace(0, 1, 9)])
        else:
            cx, cy = LAT[int(g.integers(9))]
            S.append([(cx + 0.09 * math.cos(t), cy + 0.09 * math.sin(t)) for t in np.linspace(0, TAU, 8)])
    return [[(x + g.normal(0, 0.03), y + g.normal(0, 0.03)) for x, y in s] for s in S]


def glyph_row(rc, h, w, pitch, hw, depth, seed, skip=None):
    g = np.random.default_rng(seed)
    s, circ, cnt = g.uniform(0, pitch), TAU * rc, 0
    while s < circ - 0.6 * pitch:
        phi = s / rc
        if not (skip and skip(phi)) and g.random() > 0.06:
            n = np.array([math.cos(phi), math.sin(phi)])
            t = np.array([-math.sin(phi), math.cos(phi)])
            f = g.uniform(0.65, 1.0)
            hh = h * g.uniform(0.88, 1.08)
            if g.random() < 0.1:   # word divider: stacked pair of drill dots
                for q in (-0.18, 0.18):
                    p0 = rc * n + q * hh * n
                    carve([p0 + 0.008 * np.array([math.cos(u), math.sin(u)]) for u in np.linspace(0, TAU, 7)], hw * 1.1, depth * f)
                s += pitch * 0.5
                continue
            for st in make_glyph(g):
                pts = [rc * n + x * w * t + y * hh * n for x, y in st]
                carve(resample(pts, 0.02, g, 0.0015), hw * g.uniform(0.85, 1.15), depth * f)
            cnt += 1
        s += pitch * g.uniform(0.86, 1.18)
    return cnt


def near_roundel(rc):
    return lambda phi: min(abs((phi - a + math.pi) % TAU - math.pi) for a in ROUND_A) * rc < ROUND_RAD + 0.11


n_out = glyph_row(3.41, 0.27, 0.17, 0.255, 0.0145, 0.0115, 11)
n_lane = glyph_row(2.615, 0.23, 0.145, 0.215, 0.0125, 0.0100, 12, near_roundel(2.615))
log("glyphs", n_out, n_lane)

# running scroll band (ring 1): a wave whose troughs/crests sprout curling tendrils
rc, nW, A = 1.68, 12, 0.165
P = TAU * rc / nW


def sq(s, q):
    return np.array([(rc + q) * math.cos(s / rc), (rc + q) * math.sin(s / rc)])


g = np.random.default_rng(13)
ss = np.linspace(0, TAU * rc, 2400)
carve([sq(s, A * math.sin(TAU * s / P)) for s in ss], 0.0135, 0.010)
for k in range(nW):
    for sign, s_c in ((+1, k * P + 0.75 * P), (-1, k * P + 0.25 * P)):   # tendril above trough / below crest
        q_wave = -sign * A
        cq = sign * 0.075
        rad0 = 0.115
        stem = [sq(s_c, q_wave), sq(s_c, cq - sign * rad0)]
        a_start = -sign * math.pi / 2
        turn = sign * (1 if k % 2 else -1)
        sp = [sq(s_c + (rad0 - (rad0 - 0.022) * u) * math.cos(a_start + turn * 3.4 * math.pi * u * 0.5),
                 cq + (rad0 - (rad0 - 0.022) * u) * math.sin(a_start + turn * 3.4 * math.pi * u * 0.5))
              for u in np.linspace(0, 1, 70)]
        carve(resample(stem, 0.015), 0.012, 0.009)
        carve(sp, 0.0115 * g.uniform(0.9, 1.1), 0.009)
log('scroll band')

# roundel emblems (abstract: spiral / interlocked rings / broken labyrinth / S-scroll)
for k, a in enumerate(ROUND_A):
    C = np.array([ROUND_R * math.cos(a), ROUND_R * math.sin(a)])
    rot = a + 0.4 * k
    if k == 0:
        us = np.linspace(0, 1, 260)
        carve([C + (0.04 + 0.16 * u) * np.array([math.cos(rot + 5.2 * math.pi * u), math.sin(rot + 5.2 * math.pi * u)]) for u in us], 0.012, 0.010)
    elif k == 1:
        for j in range(3):
            cc = C + 0.075 * np.array([math.cos(rot + TAU * j / 3), math.sin(rot + TAU * j / 3)])
            carve([cc + 0.095 * np.array([math.cos(t), math.sin(t)]) for t in np.linspace(0, TAU, 60)], 0.011, 0.009)
    elif k == 2:
        for j, (rad, gap) in enumerate(((0.07, 0.0), (0.125, 2.1), (0.18, 4.0))):
            carve([C + rad * np.array([math.cos(rot + gap + t), math.sin(rot + gap + t)]) for t in np.linspace(0.45, TAU - 0.45, 70)], 0.011, 0.009)
        carve([C + np.array([math.cos(rot), math.sin(rot)]) * r for r in (0.07, 0.125)], 0.011, 0.009)
    else:
        for sgn in (1, -1):
            cc = C + sgn * 0.085 * np.array([math.cos(rot), math.sin(rot)])
            carve([cc + (0.02 + 0.075 * u) * np.array([math.cos(rot + sgn * 4.6 * math.pi * (1 - u)), math.sin(rot + sgn * 4.6 * math.pi * (1 - u))]) for u in np.linspace(0, 1, 120)], 0.011, 0.009)
log('emblems')

# centre plinth: worn ring of short incised marks just outside basin lip (not radial rays: tangential dashes)
g = np.random.default_rng(21)
for k in range(26):
    phi = TAU * k / 26 + g.normal(0, 0.03)
    r = 0.62 + g.normal(0, 0.008)
    span = g.uniform(0.07, 0.11)
    carve([np.array([r * math.cos(phi + d), r * math.sin(phi + d)]) for d in np.linspace(-span, span, 8)], 0.011, 0.007 * g.uniform(0.4, 1))

# cracks (random walk fractures), never eroded
g = np.random.default_rng(31)
CRACKS = [((-0.95, 0.55), -0.33, 2.3), ((-3.55, -1.4), 0.35, 1.0), ((1.6, -2.4), 2.1, 1.25),
          ((-1.1, 1.75), 1.2, 0.9), ((2.9, 2.2), -2.5, 0.8), ((0.3, -3.3), 1.6, 0.6)]
for (x0, y0), ang, L in CRACKS:
    p = np.array([x0, y0]); pts = [p.copy()]
    for _ in range(int(L / 0.025)):
        ang += g.normal(0, 0.22)
        p = p + 0.025 * np.array([math.cos(ang), math.sin(ang)])
        pts.append(p.copy())
        if g.random() < 0.03:   # short branch
            q, b = p.copy(), ang + g.choice([-1, 1]) * g.uniform(0.5, 1.0); br = [q.copy()]
            for _ in range(int(g.integers(4, 10))):
                b += g.normal(0, 0.3); q = q + 0.02 * np.array([math.cos(b), math.sin(b)]); br.append(q.copy())
            carve(br, 0.0045, 0.010, Hk)
    pts = np.array(pts)
    for i in range(len(pts) - 1):
        carve(pts[i:i + 2], 0.0055 + 0.003 * g.random(), 0.020, Hk)
log('cracks')

# ---------------------------------------------------------------- wear, spalls, chips
n_low = fbm(101, (90, 40), (1.0, 0.5))
n_mid = fbm(102, (14, 6), (1.0, 0.6))
n_fine = fbm(103, (1.2, 0.6), (1.0, 0.7))
n_edge = fbm(104, (5, 2), (1.0, 0.5))
n_chip = fbm(105, (10, 4), (1.0, 0.4))
E = 0.5 + 0.5 * np.tanh(1.3 * n_low)
path = np.exp(-(X / 1.05) ** 2)                                  # main walking lane (camera-forward)
wear = np.clip((0.45 + 0.55 * E) * (1 - 0.35 * path), 0.30, 1)  # 1 = crisp, low = worn smooth
Hd_w = Hd * wear
Hd_w = Hd_w * wear + blur(Hd_w, 3.5) * (1 - wear)
log('wear')

spall = np.zeros((N, N), np.float32)
g = np.random.default_rng(41)
SP = []
while len(SP) < 9:
    r, a = g.uniform(0.5, 3.85), g.uniform(0, TAU)
    x, y = r * math.cos(a), r * math.sin(a)
    i, j = int((x + EXT) / PX), int((y + EXT) / PX)
    if dedge[j, i] < 0.14:
        SP.append((x, y, g.uniform(0.10, 0.26), g.uniform(0.005, 0.010)))
SP.append((3.78 * math.cos(3.62), 3.78 * math.sin(3.62), 0.32, 0.030))   # broken-off chunk at the rim
spdepth = np.zeros((N, N), np.float32)
for x, y, rad, dep in SP:
    d = np.hypot(X - x, Y - y)
    m = sst(-0.012, 0.012, rad - d + 0.05 * rad / 0.2 * n_edge)
    spdepth = np.maximum(spdepth, m * dep)
    spall = np.maximum(spall, m)
log('spalls', len(SP))

dj = dedge + 0.004 * n_edge - 0.035 * np.clip(n_chip - 1.45, 0, None)
inside = (dj > HG) & (R < R_OUT)
bw = 0.020 + 0.010 * np.clip(n_mid, -1.5, 1.5)
bev = -0.014 * (1 - sst(0.0, 1.0, (dj - HG) / bw))

# per-block settle
off = np.array([b['off'] for b in blocks], np.float32)
tlx = np.array([b['tilt'][0] for b in blocks], np.float32)
tly = np.array([b['tilt'][1] for b in blocks], np.float32)
cx = np.array([b['c'][0] for b in blocks], np.float32)
cy = np.array([b['c'][1] for b in blocks], np.float32)
bi = np.clip(blk, 0, nb - 1)
settle = np.where(blk >= 0, off[bi] + tlx[bi] * (X - cx[bi]) + tly[bi] * (Y - cy[bi]), 0).astype(np.float32)

slope = sst(3.72, 3.90, R)
Z_TOP, LIP = 0.090, 0.015
Hs_b = blur(Hs, 4.0)
Ztop = Z_TOP + settle + Hs + Hd_w + Hk + bev + 0.0016 * n_mid + 0.0006 * n_fine
# spall: surface flaked off, carving gone, cracks kept
Ztop = np.where(spall > 0, (Z_TOP + settle + Hs_b - spdepth + 0.0015 * n_mid + bev) * spall + Ztop * (1 - spall), Ztop)
Ztop = Ztop * (1 - slope) + (LIP + 0.002 * n_mid) * slope
Zbed = 0.030 - 0.018 * sst(3.70, 3.90, R) + 0.002 * n_mid
Z = np.where(inside, Ztop, Zbed)
Z = np.where(R < R_OUT + 0.004, Z, 0.0).astype(np.float32)
log('Z', float(Z[inside].min()), float(Z[inside].max()))

# ---------------------------------------------------------------- colour fields (sRGB 0..1)
Zc = np.where(inside, Ztop - 0.0016 * n_mid - 0.0006 * n_fine, Zbed).astype(np.float32)  # grime follows carving, not grain
cav = blur(Zc, 7) - Zc
cav2 = blur(Zc, 30) - Zc
dirt = np.clip((cav - 0.0008) / 0.005, 0, 1) ** 0.8
deep = np.clip(cav2 / 0.020, 0, 1)
convex = np.clip(-cav / 0.003, 0, 1)
n_tone = fbm(201, (60, 20, 6), (1.0, 0.6, 0.35))
n_moss = fbm(202, (40, 12, 3), (1.0, 0.6, 0.5))
n_lich = fbm(203, (8, 3), (1.0, 0.5))
n_spec = fbm(204, (0.8,), (1.0,))

tone_b = np.array([b['tone'] for b in blocks], np.float32)[bi]
band_a = np.array([b['band'] for b in blocks], np.float32)[bi]
strata = np.sin((X * np.cos(band_a) + Y * np.sin(band_a)) * TAU * 3.2 + 2.2 * n_mid) * (np.array([b['id'] % 3 == 0 for b in blocks])[bi])

base = np.array([0.475, 0.410, 0.315], np.float32)        # warm limestone/sandstone
v = 1 + 0.055 * tone_b + 0.065 * n_tone + 0.025 * strata + 0.03 * n_spec
col = base[None, None, :] * v[..., None]
col[..., 0] += 0.012 * tone_b; col[..., 2] -= 0.010 * tone_b
fresh = np.array([0.52, 0.45, 0.35], np.float32)
col = col * (1 - 0.8 * spall[..., None]) + fresh * (0.8 * spall[..., None]) * (1 + 0.05 * n_spec[..., None])
col *= (1 + 0.13 * convex)[..., None]                      # worn arrises catch light
col *= (1 + 0.05 * path * E)[..., None]                    # foot-polished lane
grime = np.array([0.20, 0.165, 0.12], np.float32)
dm = np.clip(0.75 * dirt + 0.35 * deep, 0, 0.88)
col = col * (1 - dm[..., None]) + grime * dm[..., None]
lich = sst(1.4, 2.0, n_lich) * (1 - dirt) * (1 - path) * 0.35
col = col * (1 - lich[..., None]) + np.array([0.56, 0.53, 0.44], np.float32) * lich[..., None]
moss_m = np.clip(0.5 * sst(-0.2, 1.0, n_moss) * (0.9 * deep + 0.7 * dirt) * (1 - 0.6 * path), 0, 0.7)
moss = np.array([0.255, 0.255, 0.135], np.float32) * (1 + 0.18 * n_spec[..., None])
col = col * (1 - moss_m[..., None]) + moss * moss_m[..., None]
earth = np.array([0.15, 0.125, 0.09], np.float32)
gm = np.clip(0.55 + 0.4 * sst(-0.3, 0.8, n_moss), 0, 1)[..., None]
gapcol = earth * (1 - 0.6 * gm) + np.array([0.21, 0.215, 0.115], np.float32) * 0.6 * gm
col = np.where(inside[..., None], col, gapcol)
out = (R >= R_OUT + 0.004)[..., None]
col = np.where(out, np.array([0.17, 0.15, 0.11], np.float32), col)
col = np.clip(col, 0, 1).astype(np.float32)

rough = 0.86 + 0.05 * n_spec * 0.5 - 0.10 * path * E + 0.08 * moss_m + 0.04 * dirt
rough = np.where(inside, rough, 0.95)
rough = np.clip(rough, 0.55, 0.98).astype(np.float32)
log('colour')

np.save(f'{CACHE}/Z.npy', Z)
np.save(f'{CACHE}/col.npy', col)
np.save(f'{CACHE}/rough.npy', rough)
np.save(f'{CACHE}/HsB.npy', Hs_b)
json.dump(dict(EXT=EXT, N=N, HG=HG, R_OUT=R_OUT, Z_TOP=Z_TOP, LIP=LIP, blocks=blocks,
               glyphs=dict(outer=n_out, lane=n_lane), spalls=len(SP), cracks=len(CRACKS)),
          open(f'{CACHE}/layout.json', 'w'), indent=1)
# quick-look previews (system PIL composes later)
def to8(a): return (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
np.save(f'{CACHE}/prev_col.npy', to8(col[::4, ::4]))
zz = Z[::4, ::4]; np.save(f'{CACHE}/prev_z.npy', to8((zz - 0.0) / 0.12))
log('done')

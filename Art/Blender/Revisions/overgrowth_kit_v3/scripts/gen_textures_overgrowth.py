#!/usr/bin/env python3
"""PBR atlases for Overgrowth Kit v3.

Three 2048 atlases, Q18-locked (0.0% cyan/teal, sat>0.20 in hue 160-200).
Palette: warm sandstone, umber bark, olive/sage/dried-ochre foliage.
"""
import numpy as np, zlib, struct, os, json

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/overgrowth_kit_v3/textures'
os.makedirs(OUT, exist_ok=True)
N = 2048
LUMA = np.array([0.2126, 0.7152, 0.0722], np.float32)


def write_png_rgb(path, arr_u8):
    h, w, _ = arr_u8.shape
    raw = b''.join(b'\x00' + arr_u8[y].tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def write_png_rgba(path, arr_u8):
    h, w, _ = arr_u8.shape
    raw = b''.join(b'\x00' + arr_u8[y].tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def periodic_noise(seed, sx=0.0, sy=0.0, beta=2.0, n=N):
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    f2 = fx ** 2 + fy ** 2
    f2[0, 0] = 1.0
    amp = 1.0 / (f2 ** (beta / 4.0))
    if sx > 0:
        amp = amp * np.exp(-(fx * sx) ** 2)
    if sy > 0:
        amp = amp * np.exp(-(fy * sy) ** 2)
    spec = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) * amp
    spec[0, 0] = 0
    x = np.fft.ifft2(spec).real
    return (x - x.min()) / (x.max() - x.min() + 1e-9)


def compute_normal(height, scale=3.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5 * scale
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5 * scale
    dz = np.ones_like(height)
    norm = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2) + 1e-9
    n_rgb = np.zeros((height.shape[0], height.shape[1], 3), dtype=np.uint8)
    n_rgb[..., 0] = np.clip((-dx / norm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    n_rgb[..., 1] = np.clip((-dy / norm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    n_rgb[..., 2] = np.clip((dz / norm * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    return n_rgb


def verify_q18(arr_u8, label):
    f = arr_u8[..., :3].reshape(-1, 3).astype(np.float32) / 255.0
    mx = f.max(1)
    mn = f.min(1)
    d = mx - mn + 1e-9
    hue = np.where(mx == f[:, 0], ((f[:, 1] - f[:, 2]) / d) % 6,
          np.where(mx == f[:, 1], (f[:, 2] - f[:, 0]) / d + 2,
                                 (f[:, 0] - f[:, 1]) / d + 4)) * 60.0
    sat = d / (mx + 1e-9)
    bad = ((hue >= 160) & (hue <= 200) & (sat > 0.20)).mean() * 100.0
    mean_rgb = arr_u8[..., :3].reshape(-1, 3).mean(0).round(1)
    print(f'[{label}] Q18 cyan-teal: {bad:.4f}% | mean RGB {mean_rgb} | mean sat {sat.mean():.3f}')
    assert bad == 0.0, f'Q18 VIOLATION: {bad}% cyan-teal in {label}'
    return dict(q18_pct=float(bad), mean_rgb=[float(x) for x in mean_rgb], mean_sat=float(sat.mean()))


def lerp3(a, b, t):
    t = np.clip(t, 0, 1)
    if t.ndim == 2:
        t = t[..., None]
    return a + (b - a) * t


def write_mask(path, ao, rough):
    m = np.zeros((N, N, 4), np.uint8)
    m[..., 0] = 0
    m[..., 1] = np.clip(ao * 255 + 0.5, 0, 255).astype(np.uint8)[::-1]
    m[..., 2] = 0
    m[..., 3] = np.clip((1.0 - rough) * 255 + 0.5, 0, 255).astype(np.uint8)[::-1]
    write_png_rgba(path, m)


report = {}

# =============================================================================
# 1. WOOD / BARK atlas
# Layout:
#   V 0.50-1.00 : trunk bark (straighter vertical ridges)
#   V 0.00-0.50 : gnarled root bark (twisting, knotted, moss in crevices)
# =============================================================================
print('=== Wood / Bark atlas ===')
wood_alb = np.zeros((N, N, 3), np.float32)
wood_h = np.zeros((N, N), np.float32)
wood_ao = np.ones((N, N), np.float32)
wood_r = np.ones((N, N), np.float32) * 0.88
H = N // 2

ridge = periodic_noise(11, sx=0, sy=90, beta=1.65)
knot = periodic_noise(12, beta=1.15)
fine = periodic_noise(13, beta=0.75)
moss_n = periodic_noise(14, beta=2.0)

c_bark_d = np.array((0.17, 0.13, 0.09), np.float32)
c_bark_m = np.array((0.28, 0.22, 0.15), np.float32)
c_bark_l = np.array((0.40, 0.32, 0.21), np.float32)
c_moss = np.array((0.22, 0.24, 0.12), np.float32)

# Trunk (top half)
tv = 0.55 * ridge[H:] + 0.25 * knot[H:] + 0.20 * fine[H:]
wood_alb[H:] = lerp3(c_bark_d, c_bark_m, tv / 0.55)
wood_alb[H:] = np.where((tv > 0.55)[..., None],
                        lerp3(c_bark_m, c_bark_l, (tv - 0.55) / 0.45),
                        wood_alb[H:])
# shallow moss in deep grooves only
groove = (1.0 - ridge[H:]) ** 2.2
moss_w = np.clip((groove - 0.55) * 2.2, 0, 1) * (0.35 + 0.65 * moss_n[H:])
wood_alb[H:] = wood_alb[H:] * (1 - moss_w * 0.45)[..., None] + c_moss * (moss_w * 0.45)[..., None]
wood_h[H:] = tv
wood_ao[H:] = np.clip(0.55 + 0.45 * ridge[H:], 0.45, 1.0)
wood_r[H:] = 0.86

# Root bark (bottom half) — more knotted, twisting
rv = 0.40 * ridge[:H] + 0.40 * knot[:H] + 0.20 * fine[:H]
c_root_d = np.array((0.15, 0.12, 0.08), np.float32)
c_root_m = np.array((0.26, 0.21, 0.14), np.float32)
c_root_l = np.array((0.38, 0.31, 0.20), np.float32)
wood_alb[:H] = lerp3(c_root_d, c_root_m, rv / 0.5)
wood_alb[:H] = np.where((rv > 0.5)[..., None],
                        lerp3(c_root_m, c_root_l, (rv - 0.5) / 0.5),
                        wood_alb[:H])
groove_r = (1.0 - knot[:H]) ** 1.8
moss_wr = np.clip((groove_r - 0.50) * 2.0, 0, 1) * (0.40 + 0.60 * moss_n[:H])
wood_alb[:H] = wood_alb[:H] * (1 - moss_wr * 0.50)[..., None] + c_moss * (moss_wr * 0.50)[..., None]
wood_h[:H] = rv
wood_ao[:H] = np.clip(0.50 + 0.50 * ridge[:H] * knot[:H], 0.40, 1.0)
wood_r[:H] = 0.90

luma = (wood_alb * LUMA).sum(2, keepdims=True)
wood_alb = np.clip(wood_alb * 0.88 + luma * 0.12, 0, 1)

u8 = (wood_alb * 255 + 0.5).astype(np.uint8)[::-1]
report['wood'] = verify_q18(u8, 'Wood BaseColor')
write_png_rgb(f'{OUT}/ENV_Temple_Overgrowth_Wood_BaseColor.png', u8)
write_png_rgb(f'{OUT}/ENV_Temple_Overgrowth_Wood_Normal.png', compute_normal(wood_h, 3.4)[::-1])
write_mask(f'{OUT}/ENV_Temple_Overgrowth_Wood_Mask.png', wood_ao, wood_r)
print('Wood maps written.')

# =============================================================================
# 2. FOLIAGE atlas (RGBA albedo: A used for alpha-clip on leaves/ivy/grass)
# Layout:
#   V 0.50-1.00 : 8 painterly leaf columns (silhouette alpha)
#   V 0.25-0.50 : dense canopy / cluster volume (opaque)
#   V 0.00-0.25, U 0.00-0.50 : 4 ivy leaf cells (silhouette alpha)
#   V 0.00-0.25, U 0.50-1.00 : 4 grass-blade cells (silhouette alpha)
# =============================================================================
print('=== Foliage atlas ===')
fol_alb = np.zeros((N, N, 3), np.float32)
fol_a = np.ones((N, N), np.float32)
fol_h = np.zeros((N, N), np.float32)
fol_ao = np.ones((N, N), np.float32)
fol_r = np.ones((N, N), np.float32) * 0.80

# Warm olive / sage / dried ochre — hue stays ~70-95, never cyan
PAL_LEAF = [
    ((0.20, 0.22, 0.11), (0.40, 0.41, 0.20)),
    ((0.23, 0.25, 0.13), (0.46, 0.45, 0.24)),
    ((0.18, 0.20, 0.10), (0.36, 0.38, 0.17)),
    ((0.26, 0.24, 0.13), (0.50, 0.44, 0.23)),  # dried ochre tip
    ((0.22, 0.24, 0.12), (0.43, 0.44, 0.22)),
    ((0.27, 0.26, 0.14), (0.52, 0.48, 0.26)),
    ((0.17, 0.20, 0.09), (0.34, 0.37, 0.16)),
    ((0.24, 0.26, 0.13), (0.48, 0.47, 0.24)),
]

stroke = periodic_noise(101, sx=0, sy=70, beta=1.7)
speck = periodic_noise(102, beta=0.85)
CW = N // 8
HH = N // 2

yy, xx = np.mgrid[0:HH, 0:CW]
u = (xx / (CW - 1)) * 2 - 1
t = yy / (HH - 1)

for k, (c0, c1) in enumerate(PAL_LEAF):
    c0a, c1a = np.array(c0, np.float32), np.array(c1, np.float32)
    grad = c0a + (c1a - c0a) * (t ** 0.85)[:, :, None]
    # painterly leaf silhouette: broad oval, slightly pointed tip, soft edge
    half_w = 0.78 * (1.0 - 0.55 * (t ** 1.6)) * (0.55 + 0.45 * np.sin(np.pi * np.clip(t, 0, 1)))
    half_w = np.clip(half_w, 0.12, 0.92)
    edge_d = (np.abs(u) - half_w) / 0.10
    alpha = np.clip(1.0 - edge_d, 0, 1)
    alpha = alpha * np.clip(t / 0.04, 0, 1) * np.clip((1.0 - t) / 0.06, 0, 1)
    vein = 1.0 + 0.14 * np.exp(-(u / 0.08) ** 2)
    ribs = 1.0 + 0.05 * np.sin((t * 14 - np.abs(u) * 5) * np.pi)
    sl = stroke[HH:, k * CW:(k + 1) * CW]
    sp = speck[:HH, k * CW:(k + 1) * CW]
    mod = (0.88 + 0.24 * sl) * (0.94 + 0.12 * sp)
    col = k * CW
    fol_alb[HH:, col:col + CW] = grad * (vein * ribs * mod)[:, :, None]
    fol_a[HH:, col:col + CW] = alpha
    fol_h[HH:, col:col + CW] = (1.0 - np.abs(u) ** 1.6) * 0.55 + np.exp(-(u / 0.08) ** 2) * 0.35
    fol_ao[HH:, col:col + CW] = np.clip(0.60 + 0.40 * (1 - np.abs(u) ** 2) * (0.4 + 0.6 * t), 0.45, 1)
    fol_r[HH:, col:col + CW] = 0.76 - 0.08 * t

# Dense canopy volume (opaque painterly cloud)
LH = N // 4
blob = periodic_noise(201, beta=2.3)
fine_c = periodic_noise(202, beta=1.15)
c_lo = np.array((0.14, 0.16, 0.08), np.float32)
c_mid = np.array((0.26, 0.28, 0.14), np.float32)
c_hi = np.array((0.42, 0.42, 0.21), np.float32)
tt = np.linspace(0, 1, LH)[:, None]
cg = np.clip(tt * 1.05 + (blob[:LH] - 0.5) * 0.75, 0, 1)
cloud = np.where(cg[..., None] < 0.5,
                 lerp3(c_lo, c_mid, cg / 0.5),
                 lerp3(c_mid, c_hi, (cg - 0.5) / 0.5))
cloud = cloud * (0.90 + 0.20 * fine_c[:LH])[..., None]
fol_alb[LH:2 * LH] = cloud
fol_a[LH:2 * LH] = 1.0
fol_h[LH:2 * LH] = blob[:LH] * 0.7 + fine_c[:LH] * 0.3
fol_ao[LH:2 * LH] = 0.58 + 0.42 * (tt ** 0.7)
fol_r[LH:2 * LH] = 0.82

# Ivy cells (4) — palmate-ish painterly silhouette
PAL_IVY = [
    ((0.18, 0.21, 0.10), (0.38, 0.40, 0.18)),
    ((0.21, 0.23, 0.11), (0.42, 0.43, 0.21)),
    ((0.24, 0.23, 0.12), (0.46, 0.43, 0.22)),
    ((0.19, 0.22, 0.10), (0.39, 0.41, 0.19)),
]
IW = N // 8
ivy_n = periodic_noise(401, sx=0, sy=36, beta=1.65)
for k, (c0, c1) in enumerate(PAL_IVY):
    u = np.linspace(-1, 1, IW)[None, :]
    t = np.linspace(0, 1, LH)[:, None]
    base = np.array(c0, np.float32) + (np.array(c1, np.float32) - c0) * (t ** 0.8)[:, :, None]
    # 3-lobe ivy silhouette
    lobe = np.exp(-((np.abs(u) - 0.42) / 0.22) ** 2) * np.exp(-((t - 0.42) / 0.28) ** 2)
    center = np.exp(-(u / 0.28) ** 2) * np.exp(-((t - 0.48) / 0.42) ** 2)
    sil = np.clip(center * 1.15 + lobe * 0.85, 0, 1)
    sil = sil * np.clip(t / 0.06, 0, 1) * np.clip((1.02 - t) / 0.08, 0, 1)
    v_c = np.exp(-(u / 0.07) ** 2) * (t < 0.94)
    vein = 1.0 + 0.22 * v_c
    m = 0.90 + 0.20 * ivy_n[:LH, k * IW:(k + 1) * IW]
    col0 = k * IW
    fol_alb[:LH, col0:col0 + IW] = base * (vein * m)[:, :, None]
    fol_a[:LH, col0:col0 + IW] = np.clip(sil * 1.25, 0, 1)
    fol_h[:LH, col0:col0 + IW] = (0.45 * (1 - u ** 2) + 0.35 * v_c) * m
    fol_ao[:LH, col0:col0 + IW] = np.clip(0.62 + 0.38 * (1 - u ** 2), 0.5, 1)
    fol_r[:LH, col0:col0 + IW] = 0.74

# Grass blade cells (4)
PAL_GRASS = [
    ((0.20, 0.22, 0.11), (0.40, 0.42, 0.20)),
    ((0.24, 0.23, 0.12), (0.48, 0.44, 0.22)),
    ((0.17, 0.20, 0.09), (0.34, 0.37, 0.16)),
    ((0.22, 0.24, 0.12), (0.44, 0.43, 0.21)),
]
gn = periodic_noise(501, sx=0, sy=50, beta=1.6)
for k, (c0, c1) in enumerate(PAL_GRASS):
    u = np.linspace(-1, 1, IW)[None, :]
    t = np.linspace(0, 1, LH)[:, None]
    base = np.array(c0, np.float32) + (np.array(c1, np.float32) - c0) * (t ** 0.7)[:, :, None]
    half = 0.55 * (1.0 - t ** 1.35) + 0.04
    alpha = np.clip(1.0 - (np.abs(u) - half) / 0.08, 0, 1)
    alpha = alpha * np.clip(t / 0.03, 0, 1) * np.clip((1.0 - t) / 0.05, 0, 1)
    m = 0.90 + 0.20 * gn[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW]
    col0 = N // 2 + k * IW
    fol_alb[:LH, col0:col0 + IW] = base * m[:, :, None]
    fol_a[:LH, col0:col0 + IW] = alpha
    fol_h[:LH, col0:col0 + IW] = (1 - np.abs(u) ** 1.4) * (0.4 + 0.6 * t)
    fol_ao[:LH, col0:col0 + IW] = 0.70 + 0.25 * t[:, :, 0] if False else np.clip(0.70 + 0.25 * t, 0.55, 1)
    fol_r[:LH, col0:col0 + IW] = 0.78

luma = (fol_alb * LUMA).sum(2, keepdims=True)
fol_alb = np.clip(fol_alb * 0.82 + luma * 0.18, 0, 1)

u8 = (fol_alb * 255 + 0.5).astype(np.uint8)[::-1]
a8 = np.clip(fol_a * 255 + 0.5, 0, 255).astype(np.uint8)[::-1]
rgba = np.dstack([u8, a8])
report['foliage'] = verify_q18(u8, 'Foliage BaseColor')
write_png_rgba(f'{OUT}/ENV_Temple_Overgrowth_Foliage_BaseColor.png', rgba)
write_png_rgb(f'{OUT}/ENV_Temple_Overgrowth_Foliage_Normal.png', compute_normal(fol_h, 2.6)[::-1])
write_mask(f'{OUT}/ENV_Temple_Overgrowth_Foliage_Mask.png', fol_ao, fol_r)
print('Foliage maps written.')

# =============================================================================
# 3. GROUND atlas
# Layout:
#   V 0.50-1.00 : weathered sandstone (temple-matched)
#   V 0.25-0.50 : packed loam / sunken earth
#   V 0.00-0.25, U 0.00-0.60 : moss / lichen on earth
#   V 0.00-0.25, U 0.60-1.00 : gravel / broken mortar
# =============================================================================
print('=== Ground atlas ===')
gnd_alb = np.zeros((N, N, 3), np.float32)
gnd_h = np.zeros((N, N), np.float32)
gnd_ao = np.ones((N, N), np.float32)
gnd_r = np.ones((N, N), np.float32) * 0.88

sn = periodic_noise(601, beta=1.8)
sg = periodic_noise(602, beta=0.9)
sc = periodic_noise(603, beta=2.2)
c_sd = np.array((0.27, 0.23, 0.17), np.float32)
c_sm = np.array((0.37, 0.33, 0.25), np.float32)
c_sl = np.array((0.46, 0.41, 0.32), np.float32)
sv = 0.50 * sn[H:] + 0.30 * sc[H:] + 0.20 * sg[H:]
gnd_alb[H:] = np.where((sv < 0.5)[..., None], lerp3(c_sd, c_sm, sv / 0.5), lerp3(c_sm, c_sl, (sv - 0.5) / 0.5))
gnd_h[H:] = sv
gnd_ao[H:] = 0.78 + 0.22 * sv
gnd_r[H:] = 0.80

# Loam
soil_n = periodic_noise(701, sx=70, sy=0, beta=1.75)
soil_p = periodic_noise(702, beta=0.85)
c_ld = np.array((0.16, 0.13, 0.09), np.float32)
c_lm = np.array((0.26, 0.21, 0.14), np.float32)
c_ll = np.array((0.36, 0.30, 0.20), np.float32)
lv = 0.65 * soil_n[LH:2 * LH] + 0.35 * soil_p[LH:2 * LH]
gnd_alb[LH:2 * LH] = np.where((lv < 0.5)[..., None], lerp3(c_ld, c_lm, lv / 0.5), lerp3(c_lm, c_ll, (lv - 0.5) / 0.5))
gnd_h[LH:2 * LH] = lv * 0.75
gnd_ao[LH:2 * LH] = 0.70 + 0.30 * soil_n[LH:2 * LH]
gnd_r[LH:2 * LH] = 0.92

# Moss on earth
moss_b = periodic_noise(801, beta=2.1)
moss_f = periodic_noise(802, beta=1.0)
mw = int(N * 0.60)
c_md = np.array((0.16, 0.18, 0.09), np.float32)
c_mm = np.array((0.24, 0.26, 0.13), np.float32)
c_ml = np.array((0.34, 0.35, 0.16), np.float32)
mv = 0.6 * moss_b[:LH, :mw] + 0.4 * moss_f[:LH, :mw]
gnd_alb[:LH, :mw] = np.where((mv < 0.5)[..., None], lerp3(c_md, c_mm, mv / 0.5), lerp3(c_mm, c_ml, (mv - 0.5) / 0.5))
gnd_h[:LH, :mw] = mv
gnd_ao[:LH, :mw] = 0.62 + 0.38 * mv
gnd_r[:LH, :mw] = 0.84

# Gravel / mortar
rub_n = periodic_noise(901, beta=1.0)
rub_l = periodic_noise(902, beta=2.2)
c_mort = np.array((0.40, 0.36, 0.28), np.float32)
c_peb = np.array((0.32, 0.29, 0.22), np.float32)
peb = (rub_n[:LH, mw:] > 0.62).astype(np.float32)
gnd_alb[:LH, mw:] = (1 - peb[..., None]) * (c_mort * 0.55 + c_ld * 0.45) + peb[..., None] * c_peb
gnd_h[:LH, mw:] = 0.4 * rub_l[:LH, mw:] + 0.6 * rub_n[:LH, mw:]
gnd_ao[:LH, mw:] = 0.68 + 0.32 * rub_l[:LH, mw:]
gnd_r[:LH, mw:] = 0.87

luma = (gnd_alb * LUMA).sum(2, keepdims=True)
gnd_alb = np.clip(gnd_alb * 0.86 + luma * 0.14, 0, 1)

u8 = (gnd_alb * 255 + 0.5).astype(np.uint8)[::-1]
report['ground'] = verify_q18(u8, 'Ground BaseColor')
write_png_rgb(f'{OUT}/ENV_Temple_Overgrowth_Ground_BaseColor.png', u8)
write_png_rgb(f'{OUT}/ENV_Temple_Overgrowth_Ground_Normal.png', compute_normal(gnd_h, 3.6)[::-1])
write_mask(f'{OUT}/ENV_Temple_Overgrowth_Ground_Mask.png', gnd_ao, gnd_r)
print('Ground maps written.')

with open(f'{OUT}/texture_q18.json', 'w') as f:
    json.dump(report, f, indent=2)
print('All atlases OK.')

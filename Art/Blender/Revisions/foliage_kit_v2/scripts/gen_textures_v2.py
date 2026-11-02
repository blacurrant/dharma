# Painterly foliage atlas (opaque, no alpha). Deterministic: fixed seeds, stdlib PNG writer.
# Run: Blender -b --python gen_textures_v2.py   (Blender python has numpy)
# Atlas layout (v up, 1024x1024):
#   v 0.50-1.00 : 8 leaf columns (u cell 0.125 each), v along leaf length (dark base -> light tip)
#   v 0.25-0.50 : lump body (tileable in u), v = dark underside -> lit crown
#   v 0.00-0.25, u 0.00-0.50 : bark / stem, streaks along v
#   v 0.00-0.25, u 0.50-1.00 : 4 ivy leaf cells (veined), v along leaf length
import numpy as np, zlib, struct, os
OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/foliage_kit_v2/textures'
os.makedirs(OUT, exist_ok=True)
N = 1024

def noise(seed, sx=0.0, sy=0.0, beta=2.0, n=N):
    """periodic noise; sx/sy>0 low-passes that axis (stretches strokes along it)"""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    f2 = fx**2 + fy**2; f2[0, 0] = 1.0
    amp = 1.0 / (f2 ** (beta / 4.0))
    if sx > 0: amp = amp * np.exp(-(fx * sx) ** 2)
    if sy > 0: amp = amp * np.exp(-(fy * sy) ** 2)
    spec = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) * amp
    spec[0, 0] = 0
    x = np.fft.ifft2(spec).real
    return (x - x.min()) / (x.max() - x.min())

def lerp(a, b, t): return a + (b - a) * t
def col(c): return np.array(c, dtype=np.float32)

img = np.zeros((N, N, 3), np.float32)

# ---- leaf columns (v .5-1) ----
LEAF = [  # (base, tip) sRGB; desaturated olive / sage / moss, no blue-green
    ((0.17, 0.20, 0.08), (0.44, 0.47, 0.20)),   # olive
    ((0.22, 0.26, 0.14), (0.52, 0.56, 0.34)),   # sage
    ((0.14, 0.20, 0.07), (0.36, 0.45, 0.16)),   # moss
    ((0.22, 0.20, 0.10), (0.52, 0.46, 0.22)),   # dry olive-umber
    ((0.20, 0.23, 0.09), (0.50, 0.52, 0.24)),   # grass olive
    ((0.25, 0.26, 0.13), (0.58, 0.55, 0.30)),   # grass dry
    ((0.15, 0.19, 0.07), (0.40, 0.46, 0.17)),   # moss 2
    ((0.24, 0.27, 0.12), (0.56, 0.58, 0.28)),   # sun-lit olive
]
H = N // 2; CW = N // 8
stroke = noise(11, sx=0, sy=60, beta=1.6)   # long strokes along v
speck = noise(12, beta=0.6)
for k, (c0, c1) in enumerate(LEAF):
    u = np.linspace(0, 1, CW)[None, :]
    t = np.linspace(0, 1, H)[:, None]
    base = lerp(col(c0), col(c1), (t ** 0.85)[:, :, None])
    edge = 1.0 - 0.22 * (np.abs(2 * u - 1) ** 2.2)
    vein = 1.0 + 0.10 * np.exp(-((2 * u - 1) / 0.07) ** 2)
    side = 1.0 + 0.045 * np.sin((t * 14 - np.abs(2 * u - 1) * 5) * np.pi)
    sl = stroke[H:, k * CW:(k + 1) * CW]; sp = speck[:H, k * CW:(k + 1) * CW]
    m = (0.86 + 0.28 * sl) * (0.94 + 0.12 * sp)
    img[H:, k * CW:(k + 1) * CW] = base * (edge * vein * side * m)[:, :, None]

# ---- lump body (v .25-.5) ----
LH = N // 4
blob = noise(21, beta=2.6); fine = noise(22, beta=1.3); lo = col((0.12, 0.15, 0.06)); mid = col((0.27, 0.31, 0.13)); hi = col((0.46, 0.49, 0.22))
tt = np.linspace(0, 1, LH)[:, None]
b = blob[:LH]; fi = fine[:LH]
grad = np.clip(tt * 1.15 + (b - 0.5) * 0.9, 0, 1)[:, :, None]
body = np.where(grad < 0.5, lerp(lo, mid, grad / 0.5), lerp(mid, hi, (grad - 0.5) / 0.5))
body = body * (0.88 + 0.24 * fi)[:, :, None]
img[LH:2 * LH] = body

# ---- bark (v 0-.25, u 0-.5) ----
bk = noise(31, sx=0, sy=40, beta=1.6)[:LH, :N // 2]; bk2 = noise(32, beta=1.0)[:LH, :N // 2]
bark = lerp(col((0.14, 0.12, 0.08)), col((0.34, 0.29, 0.19)), (0.7 * bk + 0.3 * bk2))[:, :, None] if False else None
bark = lerp(col((0.14, 0.12, 0.08)), col((0.34, 0.29, 0.19)), (0.7 * bk + 0.3 * bk2)[:, :, None])
img[:LH, :N // 2] = bark

# ---- ivy leaf cells (v 0-.25, u .5-1) ----
IVY = [((0.12, 0.17, 0.07), (0.34, 0.42, 0.17)), ((0.15, 0.19, 0.08), (0.40, 0.46, 0.20)),
       ((0.17, 0.18, 0.08), (0.44, 0.45, 0.20)), ((0.13, 0.18, 0.07), (0.36, 0.44, 0.16))]
IW = N // 8
isk = noise(41, sx=0, sy=30, beta=1.6)
for k, (c0, c1) in enumerate(IVY):
    u = np.linspace(-1, 1, IW)[None, :]; t = np.linspace(0, 1, LH)[:, None]
    base = lerp(col(c0), col(c1), (t ** 0.8)[:, :, None])
    v_c = np.exp(-(u / 0.05) ** 2) * (t < 0.95)
    v_s = np.zeros((LH, IW), np.float32)
    for sgn in (-1, 1):   # side veins radiating from the centre line
        d = np.abs((u * sgn) * 0.9 - (t - 0.12) * 0.55)
        v_s += (np.exp(-(d / 0.035) ** 2) * (np.abs(u) > 0.07) * (t > 0.1) * (t < 0.85)).astype(np.float32)
    vein = 1.0 + 0.30 * v_c + 0.16 * v_s
    edge = 1.0 - 0.18 * np.abs(u) ** 2.4
    m = 0.88 + 0.24 * isk[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW]
    img[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW] = base * (vein * edge * m)[:, :, None]

luma = (img * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
img = np.clip(img * 0.78 + luma * 0.22, 0, 1)   # pull 22 % toward grey: desaturated antique olive/sage
u8 = (img * 255 + 0.5).astype(np.uint8)[::-1]   # PNG rows go top->bottom; v=1 is the top row

def write_png(path, a):
    h, w, _ = a.shape
    raw = b''.join(b'\x00' + a[y].tobytes() for y in range(h))
    def chunk(t, d): c = struct.pack('>I', len(d)) + t + d; return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
write_png(f'{OUT}/ENV_Temple_Foliage2_BaseColor.png', u8)

# Q18 check: hue 160-200 deg with sat>0.2 must not appear
f = u8.reshape(-1, 3).astype(np.float32) / 255
mx = f.max(1); mn = f.min(1); d = mx - mn + 1e-9
hue = np.where(mx == f[:, 0], ((f[:, 1] - f[:, 2]) / d) % 6, np.where(mx == f[:, 1], (f[:, 2] - f[:, 0]) / d + 2, (f[:, 0] - f[:, 1]) / d + 4)) * 60
sat = d / (mx + 1e-9)
bad = ((hue >= 160) & (hue <= 200) & (sat > 0.2)).mean() * 100
print(f'BaseColor written; cyan-teal texels (hue160-200,sat>0.2): {bad:.4f}%  mean RGB {u8.reshape(-1,3).mean(0).round(1)}  mean sat {sat.mean():.3f}')

"""VF handoff - texture ingredient generator (Blender background python: numpy only, no external packages).

  Blender -b --factory-startup --python scripts/10_generate_textures.py

Everything is seeded and periodic (FFT noise) => deterministic and tileable by construction; the painterly pass wraps (no edge seams).
PNGs are written byte-exact by a tiny writer (no colour management involved):
  * colour textures: sRGB-encoded 8-bit RGBA, STRAIGHT alpha, colour defined everywhere (no halos with bilinear filtering)
  * data textures (macro value / macro tint): LINEAR data, neutral = 0.5, import with sRGB OFF
World mapping for the 40 x 40 m maps: image U = (x + 20)/40 (+X right), V = (z + 20)/40 (+Z up, row 0 of the file = z=+20).
Palette constraint: nothing in [145 deg, 215 deg] hue with saturation > 0.06 (cyan-teal is reserved for telegraphs).
"""
import sys, os, json, math, struct, zlib, hashlib, time
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff/scripts'
import numpy as np

ROOT = '/Users/landerstudio/MythicRoguelite'
VF = ROOT + '/Art/Blender/Revisions/vf_handoff'
OUT = VF + '/textures'
os.makedirs(OUT, exist_ok=True)
SEED0 = 20261026


# ------------------------------------------------------------------ helpers
def hexrgb(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], dtype=np.float32)


def sm(x, a, b):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def U01(n, k=0.9):
    return 0.5 + 0.5 * np.tanh(n * k)


def pn(H, W, wx, wy, seed):
    """Periodic gaussian low-pass noise, unit std, feature size ~ (wx, wy) px."""
    r = np.random.default_rng(SEED0 + seed)
    F = np.fft.rfft2(r.standard_normal((H, W)).astype(np.float32))
    fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.rfftfreq(W)[None, :]
    filt = np.exp(-0.5 * ((fx * wx / 0.55) ** 2 + (fy * wy / 0.55) ** 2))
    o = np.fft.irfft2(F * filt, s=(H, W)).astype(np.float32)
    o -= o.mean()
    return o / (o.std() + 1e-9)


def kuwahara(rgb, r, wrap=True):
    H, W, C = rgb.shape
    pad = np.pad(rgb, ((r, r), (r, r), (0, 0)), mode='wrap' if wrap else 'reflect').astype(np.float64)
    lum = pad.mean(axis=2)

    def integ(a):
        I = np.zeros((a.shape[0] + 1, a.shape[1] + 1) + a.shape[2:], dtype=np.float64)
        I[1:, 1:] = a.cumsum(0).cumsum(1); return I
    I1, I2, IL = integ(pad), integ(lum * lum), integ(lum)
    n = (r + 1) ** 2

    def bs(I, y0, y1, x0, x1):
        ya, yb, xa, xb = r + y0, r + y1 + 1, r + x0, r + x1 + 1
        return I[yb:yb + H, xb:xb + W] - I[ya:ya + H, xb:xb + W] - I[yb:yb + H, xa:xa + W] + I[ya:ya + H, xa:xa + W]
    best_var, best = None, None
    for (y0, y1, x0, x1) in ((-r, 0, -r, 0), (-r, 0, 0, r), (0, r, -r, 0), (0, r, 0, r)):
        m = bs(I1, y0, y1, x0, x1) / n; ml = bs(IL, y0, y1, x0, x1) / n; var = bs(I2, y0, y1, x0, x1) / n - ml * ml
        if best_var is None:
            best_var, best = var, m
        else:
            s = var < best_var
            best = np.where(s[..., None], m, best); best_var = np.where(s, var, best_var)
    return best.astype(np.float32)


def paint(a, r=2, mix=0.55, wrap=True):
    """Kuwahara 'brush' smoothing of a single channel, wrap-safe."""
    k = kuwahara(np.dstack([a, a, a]), r, wrap)[..., 0]
    return a * (1 - mix) + k * mix


def strokes(H, W, seed, amp=0.12):
    s = 0.5 * (pn(H, W, 44, 5, seed) + pn(H, W, 5, 44, seed + 1))
    return 1.0 - amp + amp * np.tanh(s)             # dry-brush modulation of coverage


def gblur(a, sigma):
    """Periodic gaussian blur (FFT)."""
    H, W = a.shape
    fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.rfftfreq(W)[None, :]
    return np.fft.irfft2(np.fft.rfft2(a) * np.exp(-2 * (np.pi * sigma) ** 2 * (fx * fx + fy * fy)), s=(H, W)).astype(np.float32)


def over(layers):
    """layers: bottom->top list of (rgb (3,) or (H,W,3), alpha (H,W)). Returns straight RGBA float."""
    H, W = layers[0][1].shape
    A = np.zeros((H, W), np.float32); C = np.zeros((H, W, 3), np.float32)
    for rgb, a in layers:
        a = np.clip(a, 0, 1).astype(np.float32)
        rgb = np.broadcast_to(np.asarray(rgb, np.float32), (H, W, 3))
        newA = a + A * (1 - a)
        C = np.where(newA[..., None] > 1e-6, (rgb * a[..., None] + C * (A * (1 - a))[..., None]) / np.maximum(newA, 1e-6)[..., None], C)
        A = newA
    fill = np.full((H, W, 3), -1.0, np.float32)
    for sg in (1.5, 4.0, 10.0, 28.0, 80.0):
        num = np.dstack([gblur(C[..., i] * A, sg) for i in range(3)]); den = gblur(A, sg)
        est = num / np.maximum(den, 1e-7)[..., None]
        need = (fill < 0).all(2) & (den > 1e-5)
        fill[need] = est[need]
    unset = (fill < 0).all(2)
    fill[unset] = np.broadcast_to(np.asarray(layers[-1][0], np.float32), (H, W, 3))[unset]
    C = np.where((A > 1e-3)[..., None], C, fill)
    return np.dstack([C, A])


def q8(a, dither=True, seed=1):
    a = np.clip(a, 0, 1) * 255.0
    if dither:
        a = a + np.random.default_rng(seed).random(a.shape).astype(np.float32)
        return np.clip(np.floor(a), 0, 255).astype(np.uint8)
    return np.clip(np.rint(a), 0, 255).astype(np.uint8)


def write_png(path, arr):
    H, W, C = arr.shape
    ct = {1: 0, 2: 4, 3: 2, 4: 6}[C]
    raw = b''.join(b'\x00' + arr[i].tobytes() for i in range(H))

    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, ct, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)
    return hashlib.sha256(png).hexdigest()


MAN = []


def emit(name, arr_float, kind, meta):
    """kind: 'data_gray' (H,W) | 'data_rgb' (H,W,3) | 'color_rgba' (H,W,4)."""
    path = f'{OUT}/{name}.png'
    if kind == 'data_gray':
        a8 = q8(arr_float, True, 7)[..., None]
    elif kind == 'data_rgb':
        a8 = q8(arr_float, True, 8)
    else:
        a8 = np.dstack([q8(arr_float[..., :3], False), q8(arr_float[..., 3], False)])
    sha = write_png(path, a8)
    h, w = a8.shape[:2]
    MAN.append(dict(file=f'textures/{name}.png', sha256=sha, width=w, height=h, channels=a8.shape[2], bytes=os.path.getsize(path), **meta))
    print('EMIT', name, w, h, a8.shape[2], os.path.getsize(path), 'bytes', sha[:12], flush=True)
    return a8


def grid_m(H, W, size_m):
    """x (cols), z (rows, +Z up so row 0 = +size/2) in metres, centred on 0."""
    x = (np.arange(W) + 0.5) / W * size_m - size_m / 2
    z = size_m / 2 - (np.arange(H) + 0.5) / H * size_m
    return np.meshgrid(x, z)


def vor_edge(H, W, n, seed, warp_amp, warp_wl):
    r = np.random.default_rng(SEED0 + seed)
    pts = r.uniform(0, 1, (n, 2)) * [W, H]
    X = np.arange(W)[None, :] + pn(H, W, warp_wl, warp_wl, seed + 101) * warp_amp
    Y = np.arange(H)[:, None] + pn(H, W, warp_wl, warp_wl, seed + 102) * warp_amp
    F1 = np.full((H, W), 1e9, np.float32); F2 = F1.copy()
    for px, py in pts:
        dx = np.abs(((X - px + W / 2) % W) - W / 2); dy = np.abs(((Y - py + H / 2) % H) - H / 2)
        d = np.sqrt(dx * dx + dy * dy).astype(np.float32)
        F2 = np.minimum(F2, np.maximum(F1, d)); F1 = np.minimum(F1, d)
    return (F2 - F1) * 0.5


T0 = time.time()
# =============================================================================== FLOOR: macro value (40 x 40 m, 2048)
H = W = 2048
n_lo, n_mid, n_hi = pn(H, W, 640, 640, 1), pn(H, W, 210, 210, 2), pn(H, W, 64, 64, 3)
v = 0.58 * n_lo + 0.30 * n_mid + 0.12 * n_hi
v = v / v.std()
v = paint(0.5 + 0.105 * np.clip(v, -2.4, 2.4), 5, 0.55)                         # brushed patches
v = v + 0.012 * np.tanh(0.5 * (pn(H, W, 90, 10, 4) + pn(H, W, 10, 90, 5)))       # fine dry-brush strokes
X, Z = grid_m(H, W, 40.0)
R = np.hypot(X, Z)
wdamp = 0.25 + 0.75 * sm(R, 8.0, 14.0)                                          # combat circle: amplitude x0.25 at r<=8 m, full at r>=14 m
ground = -0.07 * sm(np.maximum(np.abs(X), np.abs(Z)), 15.0, 19.5)                 # darkening toward the walls (grounding)
raw = v
damped = 0.5 + (v - 0.5) * wdamp + ground
inside = R < 10.0
stats_macro = dict(std_inside_r10=float(damped[inside].std()), std_outside_r13=float(damped[R > 13].std()), std_raw_inside=float(raw[inside].std()),
                   mean=float(damped.mean()), min=float(damped.min()), max=float(damped.max()))
emit('VF_Floor_MacroValue_2048', damped, 'data_gray', dict(
    role='floor macro value variation (combat-circle damped, wall grounding baked in)', color_space='LINEAR data (sRGB OFF)', neutral=0.5, tiling='none: one sheet = 40x40 m floor',
    world_extent_m=[-20, 20, -20, 20], mapping='U=(x+20)/40, V=(z+20)/40, file row 0 = z +20', blend='albedo *= 1 + (m-0.5)*2*k', stats=stats_macro))
emit('VF_Floor_MacroValue_NoDamp_2048', raw, 'data_gray', dict(
    role='same pattern WITHOUT combat-circle damping / grounding (for shader-side radial control)', color_space='LINEAR data (sRGB OFF)', neutral=0.5, tiling='none: 40x40 m',
    world_extent_m=[-20, 20, -20, 20], mapping='U=(x+20)/40, V=(z+20)/40, file row 0 = z +20', blend='albedo *= 1 + (m-0.5)*2*k * radialWeight(r)',
    stats=dict(std_inside_r10=float(raw[inside].std()), std_outside_r13=float(raw[R > 13].std()), mean=float(raw.mean()))))

# =============================================================================== FLOOR: macro tint (40 x 40 m, 1024)
H = W = 1024
a = 0.6 * pn(H, W, 330, 330, 11) + 0.4 * pn(H, W, 100, 100, 12)
a = np.clip(a / a.std(), -2.2, 2.2) / 2.2                                         # -1 cool .. +1 warm
a = paint(a * 0.5 + 0.5, 3, 0.5) * 2 - 1
Xs, Zs = grid_m(H, W, 40.0)
wd = 0.35 + 0.65 * sm(np.hypot(Xs, Zs), 8.0, 14.0)
warm = np.array([+0.050, +0.010, -0.050], np.float32); cool = np.array([-0.030, -0.020, +0.050], np.float32)
dev = np.where(a[..., None] > 0, warm * a[..., None], cool * (-a[..., None])) * wd[..., None]
tint = 0.5 + dev
emit('VF_Floor_MacroTint_1024', tint.astype(np.float32), 'data_rgb', dict(
    role='floor macro warm/cool tint (hue stays at ~36 deg warm / ~232 deg cool, never cyan)', color_space='LINEAR data (sRGB OFF)', neutral=0.5, tiling='none: 40x40 m',
    world_extent_m=[-20, 20, -20, 20], mapping='U=(x+20)/40, V=(z+20)/40, file row 0 = z +20', blend='albedo *= lerp(1, tint*2, k)',
    stats=dict(min=[float(tint[..., i].min()) for i in range(3)], max=[float(tint[..., i].max()) for i in range(3)])))

# =============================================================================== FLOOR: cracks (8 m tile, 2048, RGBA)
H = W = 2048
d1 = vor_edge(H, W, 34, 21, 24, 150)
gate1 = sm(pn(H, W, 330, 330, 31), 0.25, 1.0)
wid = 12.0 + 14.0 * U01(pn(H, W, 64, 64, 32))              # core width 12-26 px = 4.7-10 cm @256 px/m (gameplay cam ~49 px/m => 2-5 px)
core = 1 - sm(d1, wid * 0.5, wid)
stain = (1 - sm(d1, wid * 0.4, wid * 2.6))
d2 = vor_edge(H, W, 112, 22, 12, 80)
hair = (1 - sm(d2, 1.8, 5.0)) * sm(pn(H, W, 170, 170, 33), 0.7, 1.4) * 0.70
dark_a = 1 - (1 - np.clip(core * gate1 * 0.92, 0, 1)) * (1 - hair)
stain_a = stain * gate1 * 0.16
light_a = np.roll(core * gate1, (8, 8), (0, 1)) * (1 - core * gate1) * 0.38           # lit lip on one side (hand-painted cue)
for_paint = paint(dark_a, 2, 0.5)
modul = U01(pn(H, W, 200, 200, 34), 0.5)
cdark = hexrgb('#0F0E0C')[None, None, :] * (0.85 + 0.3 * modul[..., None])
rgba = over([(hexrgb('#1A1814'), stain_a * strokes(H, W, 35)), (np.clip(cdark, 0, 1), for_paint * strokes(H, W, 36, 0.06)), (hexrgb('#B2AC98'), light_a)])
emit('VF_Floor_Cracks_2048', rgba, 'color_rgba', dict(
    role='floor cracks + hairlines + faint stain, lit lip', color_space='sRGB colour + straight alpha', tiling='seamless, tile = 8 x 8 m (256 px/m)', tile_size_m=[8, 8],
    projection='world-space planar (top-down XZ) or decal; NOT mesh UV0 (kit UVs are per-part atlases)', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# =============================================================================== FLOOR: wear / scuffs (4 m tile, 1024, RGBA)
H = W = 1024
sel = U01(pn(H, W, 260, 260, 43), 2.0)
smear = sel * pn(H, W, 150, 16, 41) + (1 - sel) * pn(H, W, 16, 150, 42)
patch = sm(pn(H, W, 230, 230, 44), 0.0, 1.2)
light = patch * sm(smear, -0.1, 1.2) * 0.62
pit = sm(pn(H, W, 3, 3, 45), 1.9, 2.7) * sm(pn(H, W, 120, 120, 46), -0.1, 1.1) * 0.62
light = paint(light, 2, 0.5) * strokes(H, W, 47)
dsel = U01(pn(H, W, 300, 300, 48), 2.0)
dsmear = dsel * pn(H, W, 18, 120, 49) + (1 - dsel) * pn(H, W, 120, 18, 50)
dark = sm(pn(H, W, 190, 190, 55), 0.2, 1.3) * sm(dsmear, 0.2, 1.4) * 0.34
dark = paint(dark, 2, 0.5) * strokes(H, W, 56)
rgba = over([(hexrgb('#221F19'), dark), (hexrgb('#AFA894'), light), (hexrgb('#16140F'), pit)])
emit('VF_Floor_Wear_1024', rgba, 'color_rgba', dict(
    role='floor traffic wear: polished smears + pits', color_space='sRGB colour + straight alpha', tiling='seamless, tile = 4 x 4 m (256 px/m)', tile_size_m=[4, 4],
    projection='world-space planar or decal; NOT mesh UV0', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# =============================================================================== FLOOR: chipped tile edges (2 m tile, 1024, aligned to the 2 m grid)
H = W = 1024
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
e = np.minimum(np.minimum(xx + 0.5, W - xx - 0.5), np.minimum(yy + 0.5, H - yy - 0.5))      # px to the nearest tile border (512 px/m)
S = sm(pn(H, W, 46, 46, 51) + 0.5 * pn(H, W, 110, 110, 52), 0.35, 1.3)
depth = 62.0 * S + 8.0 * pn(H, W, 9, 9, 53) * (S > 0.02)       # chip depth up to ~12 cm @512 px/m
inpit = 1 - sm(e - depth, -1.5, 1.5)
pit_a = inpit * (S > 0.04) * 0.82
rim_a = (1 - sm(np.abs(e - depth), 2.0, 8.0)) * (S > 0.04) * 0.55
arris_a = (1 - sm(e, 0.0, 9.0)) * 0.24 * (0.5 + 0.5 * U01(pn(H, W, 80, 80, 54)))
pit_a = paint(pit_a, 1, 0.5)
rgba = over([(hexrgb('#A9A38F'), arris_a), (hexrgb('#17150F'), pit_a), (hexrgb('#BAB39F'), rim_a)])
emit('VF_Floor_ChippedEdges_1024', rgba, 'color_rgba', dict(
    role='chipped / worn tile perimeter (applies on every floor variant; internal joints not covered)', color_space='sRGB colour + straight alpha',
    tiling='ONE 2 x 2 m floor tile per repeat; borders of the image = tile borders (world 2 m grid, edges at even metres)', tile_size_m=[2, 2],
    projection='world-space planar, u = frac(x/2), v = frac(z/2)', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# =============================================================================== WEATHER: rain-wash streaks (3 m tile, 1024)
H = W = 1024
s = 0.65 * pn(H, W, 20, 300, 61) + 0.35 * pn(H, W, 44, 430, 62)
s = s / s.std()
vgate = sm(pn(H, W, 720, 210, 63), -0.4, 0.9)
taper = 0.6 + 0.4 * U01(pn(H, W, 800, 320, 64))
a1 = sm(s, 0.85, 2.0) * vgate * taper * 0.52
fine = sm(pn(H, W, 9, 120, 65), 1.2, 2.3) * 0.17 * vgate
a_all = paint(1 - (1 - a1) * (1 - fine), 2, 0.45) * strokes(H, W, 66, 0.08)
col = hexrgb('#1B1812')[None, None, :] * (0.85 + 0.35 * U01(pn(H, W, 300, 300, 67))[..., None])
rgba = over([(np.clip(col, 0, 1), a_all)])
emit('VF_Wall_RainStreaks_1024', rgba, 'color_rgba', dict(
    role='rain-wash vertical streaks for wall faces (stain below ledges)', color_space='sRGB colour + straight alpha', tiling='seamless, tile = 3 x 3 m (341 px/m); streaks run along V (image vertical)', tile_size_m=[3, 3],
    projection='world-space planar on the wall plane (u along the wall, v = world Y), or wall UVs of a tiling shader; NOT kit UV0', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# =============================================================================== WEATHER: salt / mineral deposits (2 m tile, 1024)
H = W = 1024
patch = sm(pn(H, W, 170, 170, 71) + 0.5 * pn(H, W, 60, 60, 72), 0.7, 1.7)
crystal = sm(pn(H, W, 3.2, 3.2, 73), 1.1, 1.9)
crust = sm(pn(H, W, 24, 24, 74), 0.5, 1.6)
a_s = np.clip(patch * (0.55 * crust + 0.9 * crystal) * 0.62, 0, 0.55)
a_s = paint(a_s, 1, 0.4) * strokes(H, W, 75, 0.08)
stain = patch * sm(pn(H, W, 50, 50, 76), -0.2, 1.2) * 0.22
rgba = over([(hexrgb('#8F8974'), stain), (hexrgb('#D2CCB8'), a_s)])
emit('VF_Weather_Salt_1024', rgba, 'color_rgba', dict(
    role='mineral / salt efflorescence (clusters + crystalline speckle + faint damp stain)', color_space='sRGB colour + straight alpha', tiling='seamless, tile = 2 x 2 m (512 px/m)', tile_size_m=[2, 2],
    projection='world-space planar or triplanar; gate by height (low on walls) and by crevice/occlusion if available', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))


# =============================================================================== WEATHER: moss (generic clumps; restrained, low saturation)
def moss_rgba(H, W, seed, gate=None, cover=(0.9, 1.6)):
    clump = 0.7 * pn(H, W, 110, 110, seed) + 0.3 * pn(H, W, 38, 38, seed + 1)
    clump = clump / clump.std()
    core = sm(clump, cover[0], cover[1])
    fuzz = sm(pn(H, W, 5, 5, seed + 2), -0.4, 1.0)
    a = core * (0.55 + 0.45 * fuzz) * 0.85
    if gate is not None:
        a = a * gate
    a = paint(a, 1, 0.45) * strokes(H, W, seed + 3, 0.1)
    t = U01(pn(H, W, 30, 30, seed + 4), 0.8)[..., None]
    col = hexrgb('#3A4228')[None, None, :] * (1 - t) + hexrgb('#5C6342')[None, None, :] * t        # olive, hue ~72 deg, sat ~0.33 max
    return over([(col, a)])


rgba = moss_rgba(1024, 1024, 81)
emit('VF_Weather_Moss_1024', rgba, 'color_rgba', dict(
    role='restrained moss clumps (generic; MUST be gated by height / drain / joint mask in the shader)', color_space='sRGB colour + straight alpha', tiling='seamless, tile = 2 x 2 m', tile_size_m=[2, 2],
    projection='world-space planar or triplanar', blend='lerp(base, rgb, a * opacity * gate)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# wall base: tileable in U only. Image bottom = wall base. 1024 px = 3 m tall x 3 m wide.
H = W = 1024
hgt = ((H - 1 - np.arange(H)) + 0.5)[:, None] / H * 3.0                         # metres above the wall base
wob = (0.5 + 0.5 * np.tanh(pn(H, W, 70, 1e5, 85)))                            # varies along U only
top = 0.30 + 0.55 * wob
gate_h = 1 - sm(hgt, top * 0.35, top)
runners = sm(pn(H, W, 13, 210, 86), 1.3, 2.0) * (1 - sm(hgt, 0.45, 1.15))
gate = np.clip(gate_h + runners * 0.8, 0, 1)
rgba = moss_rgba(H, W, 87, gate=gate, cover=(0.0, 0.9))
emit('VF_Weather_MossWallBase_1024', rgba, 'color_rgba', dict(
    role='moss pre-gated for wall bases: dense under ~0.3 m, scattered up to ~1 m, a few runners (restrained)', color_space='sRGB colour + straight alpha',
    tiling='seamless in U; V is NOT tiling: image bottom = wall base, 1024 px = 3 m wall height', tile_size_m=[3, 3],
    projection='wall-local UV (u along wall, v = height/3 m), or world planar with v = clamp(y/3); bottom edge on the floor line', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()), alpha_mean_bottom_30pct=float(rgba[int(H * 0.7):, :, 3].mean()), alpha_mean_top_50pct=float(rgba[:H // 2, :, 3].mean()))))

# floor joints: tile perimeter band (aligned to the 2 m grid)
H = W = 1024
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
e = np.minimum(np.minimum(xx + 0.5, W - xx - 0.5), np.minimum(yy + 0.5, H - yy - 0.5))
band = 1 - sm(e, 8.0, 44.0)
sporadic = sm(pn(H, W, 150, 150, 91), -0.7, 0.5)
rgba = moss_rgba(H, W, 92, gate=np.minimum(band * sporadic * 1.6, 1.0), cover=(-0.9, 0.1))
rgba[..., 3] = np.minimum(rgba[..., 3], 0.82)
emit('VF_Weather_MossFloorJoints_1024', rgba, 'color_rgba', dict(
    role='sparse moss in floor joints (tile perimeter), outer ring only', color_space='sRGB colour + straight alpha', tiling='ONE 2 x 2 m floor tile per repeat, aligned to the 2 m grid', tile_size_m=[2, 2],
    projection='world-space planar, u = frac(x/2), v = frac(z/2)', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

# =============================================================================== WEATHER: soot (decals)
# Deliberately ASYMMETRIC: an elongated, wind-smeared smudge with noisy falloff - no ring, no hole, no radial symmetry, no scalloped edge
# (a symmetric ring reads as a sun/cog motif, which is out of bounds for this project).
H = W = 1024
Xm, Ym = (np.arange(W)[None, :] + 0.5 - W / 2) / 320.0, -(np.arange(H)[:, None] + 0.5 - H / 2) / 320.0       # 320 px/m => 3.2 m decal, +Y up
th = math.radians(28.0); xr = (Xm - 0.10) * math.cos(th) + (Ym + 0.06) * math.sin(th); yr = -(Xm - 0.10) * math.sin(th) + (Ym + 0.06) * math.cos(th)
rr = np.hypot(xr / 1.35, yr / 0.78) * (1 + 0.30 * pn(H, W, 170, 170, 101) + 0.10 * pn(H, W, 55, 55, 103))
body = 1 - sm(rr, 0.10, 1.35)
mott = 0.55 + 0.45 * U01(pn(H, W, 14, 14, 102), 0.8)
streak = 0.75 + 0.25 * np.tanh(pn(H, W, 10, 120, 104))
fleck = sm(pn(H, W, 6, 6, 105), 1.7, 2.5) * (1 - sm(rr, 0.5, 1.6)) * 0.45
edge = 1 - sm(np.maximum(np.abs(Xm), np.abs(Ym)), 1.20, 1.58)                       # hard guarantee: alpha 0 at the decal border
ring = np.clip((body * mott * streak * 0.74 + fleck) * edge, 0, 0.8)
ring = paint(ring, 2, 0.5)
rgba = over([(hexrgb('#0D0C0A'), ring)])
emit('VF_Weather_SootFloorRing_1024', rgba, 'color_rgba', dict(
    role='soot / scorch smudge on the floor beside a brazier (asymmetric, elongated ~28 deg; NOT a ring; rotate per instance, mirror freely)', color_space='sRGB colour + straight alpha', tiling='none: single decal, 3.2 x 3.2 m (320 px/m)', tile_size_m=[3.2, 3.2],
    projection='top-down decal, centre near the brazier; rotate randomly per instance; keep it AWAY from the combat circle', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()), alpha_border_max=float(max(rgba[0, :, 3].max(), rgba[-1, :, 3].max(), rgba[:, 0, 3].max(), rgba[:, -1, 3].max())))))

H, W = 1024, 512                                                                 # 1.5 m wide x 3.0 m tall (341 px/m)
hh = ((H - 1 - np.arange(H)) + 0.5)[:, None] / H                                  # 0 bottom .. 1 top
xs = np.arange(W)[None, :] + 0.5
cx = W / 2 + 30 * np.sin(hh * 7.0 + 0.6) + 18 * pn(H, W, 1e5, 160, 111)[:, :1] * 0 + 14 * np.sin(hh * 17 + 1.9)
hw = W * (0.075 + 0.20 * hh) * (1 + 0.25 * pn(H, W, 60, 120, 112))
d = np.abs(xs - cx) / hw
lick = 0.35 * pn(H, W, 30, 70, 113)
plume = (1 - sm(d + lick * 0.35, 0.30, 1.0)) * (1 - sm(hh + 0.1 * pn(H, W, 80, 80, 114), 0.12, 1.0))
halo = (1 - sm(d, 0.6, 2.4)) * (1 - sm(hh, 0.0, 0.85)) * 0.28
a_sm = np.clip(plume * 0.74 + halo, 0, 0.8) * (0.7 + 0.3 * U01(pn(H, W, 14, 14, 115), 0.8))
a_sm = paint(a_sm, 2, 0.5, wrap=False)
rgba = over([(hexrgb('#0E0C0A'), a_sm)])
emit('VF_Weather_SootWallPlume_512x1024', rgba, 'color_rgba', dict(
    role='soot plume rising on a wall behind a brazier (bottom of image = just above the brazier bowl, ~1.4 m)', color_space='sRGB colour + straight alpha', tiling='none: single decal, 1.5 m wide x 3.0 m tall', tile_size_m=[1.5, 3.0],
    projection='wall-plane decal, bottom edge at ~1.3-1.5 m above the floor, centred on the brazier', blend='lerp(base, rgb, a * opacity)', stats=dict(alpha_mean=float(rgba[..., 3].mean()))))

json.dump(dict(generator='scripts/10_generate_textures.py', seed=SEED0, textures=MAN), open(VF + '/evidence/10_generation.json', 'w'), indent=1)
print('GEN_DONE', len(MAN), 'textures', round(time.time() - T0, 1), 's')

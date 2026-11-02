# PBR Texture Generator for Foliage and Ground Transition Kits
# Outputs:
#   ENV_Temple_Foliage_{BaseColor, Normal, Mask}.png
#   ENV_Temple_GroundTransition_{BaseColor, Normal, Mask}.png
# Strict Art Bible & Q18 compliance: 0.000% cyan-teal texels, desaturated warm earthy palette.

import numpy as np, zlib, struct, os

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/foliage_kit_v2/textures'
os.makedirs(OUT, exist_ok=True)
N = 2048

def write_png_rgb(path, arr_u8):
    h, w, _ = arr_u8.shape
    raw = b''.join(b'\x00' + arr_u8[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

def write_png_rgba(path, arr_u8):
    h, w, _ = arr_u8.shape
    raw = b''.join(b'\x00' + arr_u8[y].tobytes() for y in range(h))
    def chunk(t, d): return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))

def periodic_noise(seed, sx=0.0, sy=0.0, beta=2.0, n=N):
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(n)[:, None]
    fx = np.fft.fftfreq(n)[None, :]
    f2 = fx**2 + fy**2
    f2[0, 0] = 1.0
    amp = 1.0 / (f2 ** (beta / 4.0))
    if sx > 0: amp = amp * np.exp(-(fx * sx) ** 2)
    if sy > 0: amp = amp * np.exp(-(fy * sy) ** 2)
    spec = (rng.normal(size=(n, n)) + 1j * rng.normal(size=(n, n))) * amp
    spec[0, 0] = 0
    x = np.fft.ifft2(spec).real
    return (x - x.min()) / (x.max() - x.min() + 1e-9)

def compute_normal(height, scale=3.0):
    # Sobel / central difference for smooth normal map
    # height is shape (H, W) in [0, 1]
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5 * scale
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5 * scale
    dz = np.ones_like(height)
    norm = np.sqrt(dx**2 + dy**2 + dz**2) + 1e-9
    nx = -dx / norm
    ny = -dy / norm
    nz = dz / norm
    # convert to [0, 255]
    n_rgb = np.zeros((height.shape[0], height.shape[1], 3), dtype=np.uint8)
    n_rgb[..., 0] = np.clip((nx * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    n_rgb[..., 1] = np.clip((ny * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    n_rgb[..., 2] = np.clip((nz * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    return n_rgb

def verify_q18(arr_u8, label):
    f = arr_u8[..., :3].reshape(-1, 3).astype(np.float32) / 255.0
    mx = f.max(1); mn = f.min(1); d = mx - mn + 1e-9
    hue = np.where(mx == f[:, 0], ((f[:, 1] - f[:, 2]) / d) % 6,
          np.where(mx == f[:, 1], (f[:, 2] - f[:, 0]) / d + 2,
                                 (f[:, 0] - f[:, 1]) / d + 4)) * 60.0
    sat = d / (mx + 1e-9)
    bad = ((hue >= 160) & (hue <= 200) & (sat > 0.20)).mean() * 100.0
    mean_rgb = arr_u8[..., :3].reshape(-1, 3).mean(0).round(1)
    print(f'[{label}] Q18 Cyan-Teal Violations: {bad:.4f}% | Mean RGB: {mean_rgb} | Mean Sat: {sat.mean():.3f}')
    assert bad == 0.0, f"Q18 VIOLATION: {bad}% cyan-teal texels detected in {label}!"

print("=== Generating 1. Foliage PBR Atlas ===")
# 2048 x 2048 Atlas:
# - V in [0.5, 1.0]: 8 Foliage Clump / Shell leaf columns
# - V in [0.25, 0.5]: Foliage dense cluster volume cap (cloud lobes)
# - V in [0.0, 0.25], U in [0.0, 0.5]: Woody vine & root bark
# - V in [0.0, 0.25], U in [0.5, 1.0]: 4 Ivy leaf & weed cells

fol_albedo = np.zeros((N, N, 3), np.float32)
fol_height = np.zeros((N, N), np.float32)
fol_ao = np.ones((N, N), np.float32)
fol_rough = np.ones((N, N), np.float32) * 0.82

# 1A. Leaf Columns (Top Half V: [1024, 2048])
H = N // 2
CW = N // 8
# Palette tuned to warm sandstone harmony: antique olive, lichen sage, warm dried tip ochre, shaded olive
PAL_LEAF = [
    ((0.22, 0.24, 0.12), (0.42, 0.44, 0.22)), # Antique olive
    ((0.25, 0.27, 0.15), (0.48, 0.49, 0.28)), # Muted lichen sage
    ((0.20, 0.22, 0.10), (0.38, 0.40, 0.18)), # Deep olive shadow
    ((0.26, 0.25, 0.14), (0.50, 0.46, 0.24)), # Sun-bleached dried tip
    ((0.23, 0.26, 0.13), (0.45, 0.46, 0.25)), # Mid olive
    ((0.28, 0.27, 0.15), (0.54, 0.50, 0.28)), # Warm ochre-olive
    ((0.19, 0.22, 0.10), (0.36, 0.39, 0.17)), # Canopy underleaf
    ((0.27, 0.28, 0.15), (0.52, 0.51, 0.27)), # Soft sage crown
]

stroke_fol = periodic_noise(101, sx=0, sy=80, beta=1.7)
speck_fol = periodic_noise(102, beta=0.8)

for k, (c0, c1) in enumerate(PAL_LEAF):
    u = np.linspace(0, 1, CW)[None, :]
    t = np.linspace(0, 1, H)[:, None]
    c0_arr = np.array(c0, dtype=np.float32)
    c1_arr = np.array(c1, dtype=np.float32)
    grad = c0_arr + (c1_arr - c0_arr) * (t ** 0.85)[:, :, None]
    
    # leaf curvature and central rib
    edge = 1.0 - 0.25 * (np.abs(2 * u - 1) ** 2.2)
    vein = 1.0 + 0.12 * np.exp(-((2 * u - 1) / 0.08) ** 2)
    ribs = 1.0 + 0.04 * np.sin((t * 16 - np.abs(2 * u - 1) * 6) * np.pi)
    
    sl = stroke_fol[H:, k * CW:(k + 1) * CW]
    sp = speck_fol[:H, k * CW:(k + 1) * CW]
    mod = (0.88 + 0.24 * sl) * (0.94 + 0.12 * sp)
    
    col_block = grad * (edge * vein * ribs * mod)[:, :, None]
    fol_albedo[H:, k * CW:(k + 1) * CW] = col_block
    
    # Height map for normal: central vein + arched leaf curvature
    h_leaf = (1.0 - np.abs(2 * u - 1) ** 1.8) * 0.6 + np.exp(-((2 * u - 1) / 0.08) ** 2) * 0.4
    fol_height[H:, k * CW:(k + 1) * CW] = h_leaf * mod
    fol_ao[H:, k * CW:(k + 1) * CW] = np.clip(0.65 + 0.35 * (1.0 - np.abs(2 * u - 1)**2) * (0.5 + 0.5 * t), 0.5, 1.0)
    fol_rough[H:, k * CW:(k + 1) * CW] = 0.76 - 0.10 * (t * 0.5) # slightly smoother towards the leaf tip

# 1B. Dense Foliage Cloud Lobe Body (V: [512, 1024])
LH = N // 4
blob = periodic_noise(201, beta=2.4)
fine = periodic_noise(202, beta=1.2)
c_lo = np.array((0.15, 0.17, 0.09), np.float32)
c_mid = np.array((0.28, 0.30, 0.15), np.float32)
c_hi = np.array((0.44, 0.45, 0.22), np.float32)

tt = np.linspace(0, 1, LH)[:, None]
b_sample = blob[:LH]
fi_sample = fine[:LH]
cloud_grad = np.clip(tt * 1.1 + (b_sample - 0.5) * 0.8, 0, 1)[:, :, None]
cloud_body = np.where(cloud_grad < 0.5,
                      c_lo + (c_mid - c_lo) * (cloud_grad / 0.5),
                      c_mid + (c_hi - c_mid) * ((cloud_grad - 0.5) / 0.5))
cloud_body = cloud_body * (0.90 + 0.20 * fi_sample)[:, :, None]
fol_albedo[LH:2 * LH] = cloud_body
fol_height[LH:2 * LH] = b_sample * 0.7 + fi_sample * 0.3
fol_ao[LH:2 * LH] = 0.60 + 0.40 * (tt ** 0.7)
fol_rough[LH:2 * LH] = 0.82

# 1C. Woody Vine & Root Bark (V: [0, 512], U: [0, 1024])
bark_stroke = periodic_noise(301, sx=0, sy=60, beta=1.8)[:LH, :N // 2]
bark_knot = periodic_noise(302, beta=1.1)[:LH, :N // 2]
c_bark_dark = np.array((0.18, 0.15, 0.11), np.float32) # weathered walnut/umber
c_bark_light = np.array((0.34, 0.29, 0.20), np.float32)
bark_tex = c_bark_dark + (c_bark_light - c_bark_dark) * (0.75 * bark_stroke + 0.25 * bark_knot)[:, :, None]
fol_albedo[:LH, :N // 2] = bark_tex
fol_height[:LH, :N // 2] = bark_stroke * 0.8 + bark_knot * 0.2
fol_ao[:LH, :N // 2] = 0.70 + 0.30 * bark_stroke
fol_rough[:LH, :N // 2] = 0.88 # rough woody fiber

# 1D. Clinging Ivy Leaves & Tendrils (V: [0, 512], U: [1024, 2048])
PAL_IVY = [
    ((0.18, 0.21, 0.10), (0.38, 0.41, 0.19)),
    ((0.21, 0.23, 0.11), (0.42, 0.44, 0.22)),
    ((0.24, 0.24, 0.13), (0.46, 0.45, 0.24)),
    ((0.19, 0.22, 0.10), (0.39, 0.42, 0.20)),
]
IW = N // 8
ivy_noise = periodic_noise(401, sx=0, sy=40, beta=1.7)
for k, (c0, c1) in enumerate(PAL_IVY):
    u = np.linspace(-1, 1, IW)[None, :]
    t = np.linspace(0, 1, LH)[:, None]
    c0_arr = np.array(c0, np.float32)
    c1_arr = np.array(c1, np.float32)
    base = c0_arr + (c1_arr - c0_arr) * (t ** 0.8)[:, :, None]
    
    # Ivy primary and secondary radial veins
    v_c = np.exp(-(u / 0.06) ** 2) * (t < 0.95)
    v_s = np.zeros((LH, IW), np.float32)
    for sgn in (-1, 1):
        d = np.abs((u * sgn) * 0.9 - (t - 0.15) * 0.6)
        v_s += (np.exp(-(d / 0.04) ** 2) * (np.abs(u) > 0.07) * (t > 0.1) * (t < 0.88)).astype(np.float32)
    vein = 1.0 + 0.26 * v_c + 0.14 * v_s
    edge = 1.0 - 0.20 * np.abs(u) ** 2.2
    m = 0.90 + 0.20 * ivy_noise[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW]
    
    fol_albedo[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW] = base * (vein * edge * m)[:, :, None]
    fol_height[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW] = (0.5 * (1 - np.abs(u)**2) + 0.3 * v_c + 0.2 * v_s) * m
    fol_ao[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW] = np.clip(0.65 + 0.35 * (1.0 - np.abs(u)**2), 0.5, 1.0)
    fol_rough[:LH, N // 2 + k * IW:N // 2 + (k + 1) * IW] = 0.74

# Subtle desaturation toward earthy warm olive
luma_fol = (fol_albedo * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
fol_albedo = np.clip(fol_albedo * 0.80 + luma_fol * 0.20, 0, 1)

# Write Foliage textures
u8_fol_albedo = (fol_albedo * 255.0 + 0.5).astype(np.uint8)[::-1]
verify_q18(u8_fol_albedo, "Foliage BaseColor")
write_png_rgb(f'{OUT}/ENV_Temple_Foliage_BaseColor.png', u8_fol_albedo)

u8_fol_normal = compute_normal(fol_height, scale=2.8)[::-1]
write_png_rgb(f'{OUT}/ENV_Temple_Foliage_Normal.png', u8_fol_normal)

# URP Lit Mask: R=Metallic (0), G=AO, B=0, A=Smoothness (1 - Roughness)
u8_fol_mask = np.zeros((N, N, 4), dtype=np.uint8)
u8_fol_mask[..., 0] = 0 # Metallic
u8_fol_mask[..., 1] = np.clip(fol_ao * 255.0 + 0.5, 0, 255).astype(np.uint8)[::-1] # AO
u8_fol_mask[..., 2] = 0
u8_fol_mask[..., 3] = np.clip((1.0 - fol_rough) * 255.0 + 0.5, 0, 255).astype(np.uint8)[::-1] # Smoothness
write_png_rgba(f'{OUT}/ENV_Temple_Foliage_Mask.png', u8_fol_mask)
print("Foliage PBR maps written successfully.")


print("\n=== Generating 2. Ground Transition & Dirt/Rubble PBR Atlas ===")
# 2048 x 2048 Atlas:
# - V in [0.5, 1.0]: Weathered Sandstone flagstone & cracked paver stone (matches temple floor)
# - V in [0.0, 0.5], U in [0.0, 0.6]: Sandy soil drift & packed loam
# - V in [0.0, 0.5], U in [0.6, 1.0]: Mortar crumble, gravel pebbles, & crack loam bed

gnd_albedo = np.zeros((N, N, 3), np.float32)
gnd_height = np.zeros((N, N), np.float32)
gnd_ao = np.ones((N, N), np.float32)
gnd_rough = np.ones((N, N), np.float32) * 0.88

# 2A. Weathered Sandstone Flagstone (V: [1024, 2048])
stone_noise = periodic_noise(501, beta=1.8)
stone_grain = periodic_noise(502, beta=0.9)
stone_chip = periodic_noise(503, beta=2.2)

c_stone_dark = np.array((0.26, 0.22, 0.17), np.float32) # warm sandstone umber
c_stone_mid = np.array((0.36, 0.32, 0.25), np.float32)  # base floor sandstone
c_stone_light = np.array((0.44, 0.40, 0.32), np.float32) # weathered chiseled crest

s_n = stone_noise[H:]
s_g = stone_grain[H:]
s_c = stone_chip[H:]

stone_val = 0.5 * s_n + 0.3 * s_c + 0.2 * s_g
stone_col = np.where((stone_val < 0.5)[:, :, None],
                     c_stone_dark + (c_stone_mid - c_stone_dark) * (stone_val / 0.5)[:, :, None],
                     c_stone_mid + (c_stone_light - c_stone_mid) * ((stone_val - 0.5) / 0.5)[:, :, None])
gnd_albedo[H:] = stone_col
gnd_height[H:] = stone_val
gnd_ao[H:] = 0.80 + 0.20 * stone_val
gnd_rough[H:] = 0.78 # smooth weathered stone

# 2B. Sandy Soil Drift & Packed Loam (V: [0, 1024], U: [0, 1228])
soil_w = int(N * 0.60)
soil_drift = periodic_noise(601, sx=80, sy=0, beta=1.8)[:H, :soil_w] # wind-drift ripples
soil_pebble = periodic_noise(602, beta=0.8)[:H, :soil_w]
c_soil_dark = np.array((0.20, 0.16, 0.12), np.float32) # damp loam
c_soil_mid = np.array((0.30, 0.25, 0.18), np.float32)  # warm sandy silt
c_soil_light = np.array((0.40, 0.34, 0.24), np.float32) # dry surface sand

s_val = 0.65 * soil_drift + 0.35 * soil_pebble
soil_col = np.where((s_val < 0.5)[:, :, None],
                    c_soil_dark + (c_soil_mid - c_soil_dark) * (s_val / 0.5)[:, :, None],
                    c_soil_mid + (c_soil_light - c_soil_mid) * ((s_val - 0.5) / 0.5)[:, :, None])
gnd_albedo[:H, :soil_w] = soil_col
gnd_height[:H, :soil_w] = s_val * 0.8
gnd_ao[:H, :soil_w] = 0.75 + 0.25 * soil_drift
gnd_rough[:H, :soil_w] = 0.92 # matte diffuse earth

# 2C. Mortar Crumble, Gravel Pebbles & Crack Bed (V: [0, 1024], U: [1228, 2048])
rub_w = N - soil_w
rub_noise = periodic_noise(701, beta=1.0)[:H, soil_w:] # high frequency pebbles
rub_large = periodic_noise(702, beta=2.2)[:H, soil_w:]
c_mortar = np.array((0.42, 0.38, 0.30), np.float32) # crumbling pale mortar
c_pebble_dark = np.array((0.22, 0.20, 0.16), np.float32)
c_pebble_light = np.array((0.38, 0.35, 0.28), np.float32)

peb_mask = (rub_noise > 0.65).astype(np.float32)
r_col = (1.0 - peb_mask[:, :, None]) * (c_mortar * 0.6 + c_soil_mid * 0.4) + peb_mask[:, :, None] * c_pebble_light
gnd_albedo[:H, soil_w:] = r_col
gnd_height[:H, soil_w:] = 0.4 * rub_large + 0.6 * rub_noise
gnd_ao[:H, soil_w:] = 0.70 + 0.30 * rub_large
gnd_rough[:H, soil_w:] = 0.85

# Subtle harmonious tuning to ground palette
luma_gnd = (gnd_albedo * np.array([0.2126, 0.7152, 0.0722], np.float32)).sum(2, keepdims=True)
gnd_albedo = np.clip(gnd_albedo * 0.85 + luma_gnd * 0.15, 0, 1)

u8_gnd_albedo = (gnd_albedo * 255.0 + 0.5).astype(np.uint8)[::-1]
verify_q18(u8_gnd_albedo, "Ground Transition BaseColor")
write_png_rgb(f'{OUT}/ENV_Temple_GroundTransition_BaseColor.png', u8_gnd_albedo)

u8_gnd_normal = compute_normal(gnd_height, scale=3.5)[::-1]
write_png_rgb(f'{OUT}/ENV_Temple_GroundTransition_Normal.png', u8_gnd_normal)

u8_gnd_mask = np.zeros((N, N, 4), dtype=np.uint8)
u8_gnd_mask[..., 0] = 0 # Metallic
u8_gnd_mask[..., 1] = np.clip(gnd_ao * 255.0 + 0.5, 0, 255).astype(np.uint8)[::-1]
u8_gnd_mask[..., 2] = 0
u8_gnd_mask[..., 3] = np.clip((1.0 - gnd_rough) * 255.0 + 0.5, 0, 255).astype(np.uint8)[::-1]
write_png_rgba(f'{OUT}/ENV_Temple_GroundTransition_Mask.png', u8_gnd_mask)
print("Ground Transition PBR maps written successfully.")

"""2048 PBR maps for ENV_Temple_Central_Medallion.
Faithfully authored after Reference 1 (ancient circular stone medallion embedded in pavers with
4 cardinal roundels, archaic rune band, segmented stone slabs, and structural fracture cracks)
and Reference 2 (stepped architectural profile with recessed channels and raised central altar).

Palette: Warm ancient sandstone (Floor_A / M_UE_Ancient_Ground family).
Q18 constraint: Strictly 0.0% cyan/teal (all greens are desaturated warm olive/sage).
"""
import numpy as np
import zlib
import struct
import os
import json
import math

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion/textures'
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


def compute_normal(height, scale=18.0):
    dx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * 0.5 * scale
    dy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * 0.5 * scale
    dz = np.ones_like(height)
    n = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2) + 1e-9
    rgb = np.zeros((height.shape[0], height.shape[1], 3), np.uint8)
    rgb[..., 0] = np.clip((-dx / n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    rgb[..., 1] = np.clip((-dy / n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    rgb[..., 2] = np.clip((dz / n * 0.5 + 0.5) * 255, 0, 255).astype(np.uint8)
    return rgb


def verify_q18(arr_u8, label):
    f = arr_u8[..., :3].reshape(-1, 3).astype(np.float32) / 255.0
    mx, mn = f.max(1), f.min(1)
    d = mx - mn + 1e-9
    hue = np.where(mx == f[:, 0], ((f[:, 1] - f[:, 2]) / d) % 6,
          np.where(mx == f[:, 1], (f[:, 2] - f[:, 0]) / d + 2,
                                 (f[:, 0] - f[:, 1]) / d + 4)) * 60.0
    sat = d / (mx + 1e-9)
    bad = ((hue >= 160) & (hue <= 200) & (sat > 0.20)).mean() * 100.0
    mean_rgb = arr_u8[..., :3].reshape(-1, 3).mean(0).round(1)
    print(f'[{label}] Q18 cyan-teal: {bad:.4f}% | mean RGB {mean_rgb} | mean sat {sat.mean():.3f}')
    assert bad == 0.0, f'Q18 VIOLATION {bad}% in {label}'
    return dict(q18_pct=float(bad), mean_rgb=[float(x) for x in mean_rgb], mean_sat=float(sat.mean()))


def v_groove(dist, half_w, power=0.45):
    """Sharp V-shaped stone incision with steep walls."""
    t = np.abs(dist) / (half_w + 1e-9)
    return np.clip(1.0 - t, 0, 1) ** power


def dist_to_segment(px, py, x1, y1, x2, y2):
    """Distance from points (px, py) to line segment (x1, y1)-(x2, y2)."""
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return np.sqrt((px - x1) ** 2 + (py - y1) ** 2)
    t = np.clip(((px - x1) * dx + (py - y1) * dy) / l2, 0.0, 1.0)
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return np.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)


print("Building coordinate grids...")
yy, xx = np.mgrid[0:N, 0:N]
u = (xx / (N - 1)) * 2.0 - 1.0
v = (yy / (N - 1)) * 2.0 - 1.0
r = np.sqrt(u * u + v * v)
th = np.arctan2(v, u)
TAU = 2.0 * np.pi

# Noise layers for realistic stone grain, broad undulation, and cracks
n_fine = periodic_noise(101, beta=0.85)
n_mid = periodic_noise(102, beta=1.60)
n_broad = periodic_noise(103, beta=2.40)
n_chisel = periodic_noise(104, sx=32, sy=0, beta=1.35)

height = np.full((N, N), 0.55, np.float32)
# Sub-millimeter sandstone grain & weathered broad undulation
height += 0.035 * (n_broad - 0.5)
height += 0.020 * (n_fine - 0.5)
height += 0.012 * (n_chisel - 0.5)

carve = np.zeros((N, N), np.float32)
crack = np.zeros((N, N), np.float32)
displacement = np.zeros((N, N), np.float32)

# ==============================================================================
# 1. ARCHITECTURAL CONCENTRIC STEPPING & TIERS (Matching Ref 1 & Ref 2)
# ==============================================================================
print("Carving architectural tiers and concentric profiles...")

# Outer toothed / scalloped rim: r in [0.93, 1.00]
# 24 radial modular slab teeth with beveled edges
n_teeth = 24
th_tooth = (th / TAU * n_teeth) % 1.0
tooth_joint = np.minimum(th_tooth, 1.0 - th_tooth)
rim_bevel = np.clip((r - 0.93) / 0.05, 0, 1)
# Rim height step
height += 0.045 * np.clip((r - 0.77) / 0.05, 0, 1) * np.clip((0.98 - r) / 0.03, 0, 1)

# Outer Canal (Drainage / Shadow Trench between glyph band and roundel ring)
# r in [0.68, 0.76], centered at 0.72
outer_canal = v_groove(r - 0.725, 0.038, power=0.55)
height -= 0.14 * outer_canal
carve = np.maximum(carve, outer_canal * 0.95)

# Stepped lips bordering the outer canal
lip_outer = v_groove(r - 0.765, 0.012, power=0.7)
lip_inner = v_groove(r - 0.685, 0.012, power=0.7)
height += 0.04 * (lip_outer + lip_inner)

# Inner Canal (around Central Altar)
# r in [0.27, 0.34], centered at 0.305
inner_canal = v_groove(r - 0.305, 0.032, power=0.55)
height -= 0.16 * inner_canal
carve = np.maximum(carve, inner_canal * 0.95)

# Central Altar Plinth: r in [0, 0.27]
# Raised heavy circular stone collar at r in [0.21, 0.27]
altar_collar = np.clip((r - 0.21) / 0.02, 0, 1) * np.clip((0.275 - r) / 0.015, 0, 1)
height += 0.09 * altar_collar

# Sunken Ritual Well / Basin: r < 0.21
altar_basin = np.clip((0.21 - r) / 0.03, 0, 1)
height -= 0.07 * altar_basin

# Concentric carved rings inside the central ritual basin
for r_ring, w_ring, depth in [(0.17, 0.008, 0.14), (0.12, 0.007, 0.12), (0.07, 0.006, 0.10)]:
    ring_g = v_groove(r - r_ring, w_ring, power=0.45) * altar_basin
    height -= depth * ring_g
    carve = np.maximum(carve, ring_g)

# Central Sacred Boss / Hub in the ritual well: r < 0.045
center_boss = np.clip(1.0 - r / 0.045, 0, 1) ** 0.8
height += 0.08 * center_boss

# Radial ceremonial marker spokes inside the ritual basin (8 spokes)
spoke_angle = (th / TAU * 8.0) % 1.0
spoke_dist = np.minimum(spoke_angle, 1.0 - spoke_angle) * (TAU / 8.0) * r
spoke_cut = v_groove(spoke_dist, 0.006, power=0.45) * (r > 0.045) * (r < 0.20)
height -= 0.10 * spoke_cut
carve = np.maximum(carve, spoke_cut * 0.8)


# ==============================================================================
# 2. FOUR CARDINAL ROUNDELS & SCROLLWORK (Matching Ref 1 exactly)
# ==============================================================================
print("Carving the 4 Cardinal Roundels with deep spiral relief...")

# 4 Cardinal roundels centered at radius r_c = 0.525, at angles 0, pi/2, pi, 3pi/2
r_c = 0.520
roundel_radius = 0.128
cardinal_angles = [0.0, 0.5 * np.pi, np.pi, 1.5 * np.pi]

for ang in cardinal_angles:
    uc = r_c * np.cos(ang)
    vc = r_c * np.sin(ang)
    dist_c = np.sqrt((u - uc) ** 2 + (v - vc) ** 2)
    rho = dist_c / roundel_radius
    in_roundel = dist_c < roundel_radius

    # Raised heavy circular stone rim for each roundel
    roundel_rim = np.clip((dist_c - 0.102) / 0.012, 0, 1) * np.clip((roundel_radius - dist_c) / 0.012, 0, 1)
    height += 0.095 * roundel_rim

    # Recessed inner field of the roundel
    roundel_field = np.clip((0.102 - dist_c) / 0.015, 0, 1)
    height += 0.02 * roundel_field

    # Deep carved swirling spiral motif inside the roundel (Reference 1 signature)
    phi = np.arctan2(v - vc, u - uc) - ang
    # Double interlocking spiral arms
    spiral_arm1 = (phi - 4.5 * np.sqrt(np.clip(rho, 0, 1))) % np.pi - 0.5 * np.pi
    dist_spiral = np.abs(spiral_arm1) * np.clip(dist_c, 0.015, roundel_radius)
    spiral_cut = v_groove(dist_spiral, 0.014, power=0.40) * (dist_c < 0.098) * (dist_c > 0.018)
    height -= 0.16 * spiral_cut
    carve = np.maximum(carve, spiral_cut * 0.95)

    # Raised central eye/boss of each cardinal roundel
    roundel_eye = np.clip(1.0 - dist_c / 0.022, 0, 1) ** 0.8
    height += 0.06 * roundel_eye

# Between the roundels: Concentric stone ribs and stepped wave friezes (r in [0.38, 0.66])
inter_roundel = np.ones((N, N), np.float32)
for ang in cardinal_angles:
    uc = r_c * np.cos(ang)
    vc = r_c * np.sin(ang)
    d = np.sqrt((u - uc) ** 2 + (v - vc) ** 2)
    inter_roundel *= np.clip((d - roundel_radius * 0.90) / 0.04, 0, 1)

# Concentric stone ribs between roundels
for r_rib, w_rib, h_rib in [(0.42, 0.010, 0.045), (0.52, 0.012, 0.040), (0.62, 0.010, 0.045)]:
    rib = v_groove(r - r_rib, w_rib, power=0.6) * inter_roundel * (r > 0.34) * (r < 0.68)
    height += h_rib * rib

# Carved wave / meander frieze in the channels between roundels
frieze_zone1 = (r > 0.44) & (r < 0.50) & (inter_roundel > 0.3)
wave1 = np.sin(th * 32.0) * 0.018
wave_dist1 = np.abs(r - 0.47 - wave1)
wave_cut1 = v_groove(wave_dist1, 0.008, power=0.45) * frieze_zone1
height -= 0.11 * wave_cut1
carve = np.maximum(carve, wave_cut1 * 0.85)

frieze_zone2 = (r > 0.54) & (r < 0.60) & (inter_roundel > 0.3)
wave2 = np.cos(th * 32.0 + 0.8) * 0.018
wave_dist2 = np.abs(r - 0.57 - wave2)
wave_cut2 = v_groove(wave_dist2, 0.008, power=0.45) * frieze_zone2
height -= 0.11 * wave_cut2
carve = np.maximum(carve, wave_cut2 * 0.85)


# ==============================================================================
# 3. OUTER ARCHAIC RUNES / GLYPHS BAND (Matching Ref 1 exactly)
# ==============================================================================
print("Carving authentic archaic runes/glyphs on the outer frieze band...")

# The glyph band sits at r in [0.77, 0.93], spanning 24 voussoir sectors
glyph_mask = (r >= 0.775) & (r <= 0.925)
rng = np.random.default_rng(20261029)

# Pre-define 32 archaic glyph stroke templates in normalized glyph box [-0.5, 0.5]^2
# Each glyph is a list of segments: ((x1, y1), (x2, y2))
GLYPH_TEMPLATES = [
    # 0: Arrow / Chevron upright
    [((-0.3, -0.4), (0.0, 0.4)), ((0.0, 0.4), (0.3, -0.4))],
    # 1: Crossed bar with vertical
    [((0.0, -0.45), (0.0, 0.45)), ((-0.35, 0.1), (0.35, 0.1))],
    # 2: Archaic 'F' / double bar
    [((-0.2, -0.45), (-0.2, 0.45)), ((-0.2, 0.35), (0.3, 0.1)), ((-0.2, 0.0), (0.2, -0.2))],
    # 3: X / crossed slashes
    [((-0.35, -0.4), (0.35, 0.4)), ((-0.35, 0.4), (0.35, -0.4))],
    # 4: Hook / shepherd crook
    [((-0.2, -0.45), (-0.2, 0.2)), ((-0.2, 0.2), (0.1, 0.4)), ((0.1, 0.4), (0.3, 0.2)), ((0.3, 0.2), (0.1, 0.0))],
    # 5: Rune tree / algorithmic branching
    [((0.0, -0.45), (0.0, 0.45)), ((0.0, -0.1), (0.35, 0.15)), ((0.0, 0.1), (0.35, 0.35))],
    # 6: Cuneiform wedge / triangle
    [((-0.3, 0.2), (0.3, 0.2)), ((-0.3, 0.2), (0.0, -0.4)), ((0.3, 0.2), (0.0, -0.4))],
    # 7: Diamond / archaic rune
    [((0.0, 0.4), (0.3, 0.0)), ((0.3, 0.0), (0.0, -0.4)), ((0.0, -0.4), (-0.3, 0.0)), ((-0.3, 0.0), (0.0, 0.4))],
    # 8: Double vertical + diagonal cross
    [((-0.25, -0.4), (-0.25, 0.4)), ((0.25, -0.4), (0.25, 0.4)), ((-0.25, -0.4), (0.25, 0.4))],
    # 9: Trident / Psi rune
    [((0.0, -0.45), (0.0, 0.45)), ((-0.35, 0.3), (-0.1, -0.1)), ((0.35, 0.3), (0.1, -0.1)), ((-0.1, -0.1), (0.1, -0.1))],
    # 10: Hourglass / double chevron
    [((-0.3, 0.4), (0.3, 0.4)), ((-0.3, 0.4), (0.3, -0.4)), ((0.3, -0.4), (-0.3, -0.4)), ((-0.3, -0.4), (0.3, 0.4))],
    # 11: Stepped angle / key
    [((-0.3, -0.4), (-0.3, 0.4)), ((-0.3, 0.4), (0.2, 0.4)), ((0.2, 0.4), (0.2, 0.0)), ((0.2, 0.0), (-0.1, 0.0))],
    # 12: Diagonal chevron pair
    [((-0.3, 0.3), (0.1, 0.1)), ((0.1, 0.1), (-0.3, -0.1)), ((-0.1, 0.1), (0.3, -0.1)), ((0.3, -0.1), (-0.1, -0.3))],
    # 13: Solar wheel / 4-spoke cross in box
    [((-0.3, -0.3), (0.3, -0.3)), ((0.3, -0.3), (0.3, 0.3)), ((0.3, 0.3), (-0.3, 0.3)), ((-0.3, 0.3), (-0.3, -0.3)),
     ((0.0, -0.3), (0.0, 0.3)), ((-0.3, 0.0), (0.3, 0.0))],
    # 14: Three vertical tall strokes (tally)
    [((-0.25, -0.4), (-0.25, 0.4)), ((0.0, -0.4), (0.0, 0.4)), ((0.25, -0.4), (0.25, 0.4))],
    # 15: Crown / triple peak
    [((-0.35, -0.3), (-0.35, 0.3)), ((-0.35, -0.3), (0.35, -0.3)), ((0.35, -0.3), (0.35, 0.3)),
     ((-0.35, 0.3), (-0.1, 0.0)), ((-0.1, 0.0), (0.0, 0.4)), ((0.0, 0.4), (0.1, 0.0)), ((0.1, 0.0), (0.35, 0.3))],
]

# Distribute glyphs around the 24 sectors (3 glyphs per sector = 72 glyphs)
total_glyphs = 72
for g_idx in range(total_glyphs):
    g_th = (g_idx + 0.5) / total_glyphs * TAU + rng.uniform(-0.015, 0.015)
    g_r = 0.850 + rng.uniform(-0.025, 0.025)
    g_scale = 0.038 * (0.90 + 0.20 * rng.uniform())
    template = GLYPH_TEMPLATES[rng.integers(len(GLYPH_TEMPLATES))]

    # Tangent coordinate system at (g_r, g_th):
    # u_tangent along circumference (th direction), v_tangent along radial direction (r direction)
    cos_th = np.cos(g_th)
    sin_th = np.sin(g_th)
    # Glyph center in (u, v)
    g_uc = g_r * cos_th
    g_vc = g_r * sin_th

    # Quick bounding box check in pixel coords
    px = int((g_uc * 0.5 + 0.5) * (N - 1))
    py = int((g_vc * 0.5 + 0.5) * (N - 1))
    box_r = int(g_scale * 1.8 * (N - 1))
    x0, x1 = max(0, px - box_r), min(N, px + box_r)
    y0, y1 = max(0, py - box_r), min(N, py + box_r)

    if x1 <= x0 or y1 <= y0:
        continue

    # Local coordinates within the bounding box
    sub_u = u[y0:y1, x0:x1] - g_uc
    sub_v = v[y0:y1, x0:x1] - g_vc

    # Project onto local radial (dr) and circumferential (dth) axes
    # Radial unit vector: (cos_th, sin_th)
    # Circumferential unit vector: (-sin_th, cos_th)
    lx = (-sin_th * sub_u + cos_th * sub_v) / g_scale
    ly = (cos_th * sub_u + sin_th * sub_v) / g_scale

    glyph_dist = np.full(sub_u.shape, 999.0, np.float32)
    for (sx1, sy1), (sx2, sy2) in template:
        d_seg = dist_to_segment(lx, ly, sx1, sy1, sx2, sy2)
        glyph_dist = np.minimum(glyph_dist, d_seg)

    # Convert to world scale distance
    world_dist = glyph_dist * g_scale
    carve_stroke = v_groove(world_dist, 0.0075, power=0.42)
    # Weathering: some strokes eroded/broken
    stroke_wear = 0.75 + 0.25 * n_fine[y0:y1, x0:x1]
    carve_stroke *= stroke_wear

    height[y0:y1, x0:x1] -= 0.16 * carve_stroke
    carve[y0:y1, x0:x1] = np.maximum(carve[y0:y1, x0:x1], carve_stroke * 0.95)


# ==============================================================================
# 4. STRUCTURAL SLAB SEAMS & FRACTURE CRACKS (Matching Ref 1 exactly)
# ==============================================================================
print("Carving structural slab joints and major geological fractures...")

# 8 Primary Radial Mortar Joints (dividing the disc into 8 monumental stone pie slabs)
n_slabs = 8
th_slab = (th / TAU * n_slabs) % 1.0
slab_joint_dist = np.minimum(th_slab, 1.0 - th_slab) * (TAU / n_slabs) * r
# Add organic waviness to joint line
slab_joint_dist += 0.005 * (n_fine - 0.5)
slab_cut = v_groove(slab_joint_dist, 0.012, power=0.45) * (r > 0.12) * (r < 0.98)
height -= 0.18 * slab_cut
carve = np.maximum(carve, slab_cut * 0.98)
crack = np.maximum(crack, slab_cut)

# 24 Outer Rim Voussoir Joints (r in [0.76, 0.99])
th_outer_joint = (th / TAU * 24.0) % 1.0
outer_joint_dist = np.minimum(th_outer_joint, 1.0 - th_outer_joint) * (TAU / 24.0) * r
outer_joint_cut = v_groove(outer_joint_dist, 0.009, power=0.45) * (r > 0.76) * (r < 0.99)
height -= 0.15 * outer_joint_cut
carve = np.maximum(carve, outer_joint_cut * 0.90)

# MAJOR FRACTURE CRACK 1 (Directly from Ref 1: Diagonal rupture cutting across center)
# Path: from top-left (-0.65, 0.75) through (-0.25, 0.35), (0.05, -0.05), (0.45, -0.55), (0.75, -0.70)
nodes_crack1 = np.array([
    [-0.72, 0.70],
    [-0.52, 0.56],
    [-0.32, 0.40],
    [-0.18, 0.22],
    [-0.04, 0.08],
    [0.10, -0.06],
    [0.26, -0.22],
    [0.42, -0.42],
    [0.58, -0.58],
    [0.72, -0.72],
    [0.85, -0.80]
], np.float32)

dist_crack1 = np.full((N, N), 999.0, np.float32)
for i in range(len(nodes_crack1) - 1):
    p1 = nodes_crack1[i]
    p2 = nodes_crack1[i + 1]
    d_seg = dist_to_segment(u, v, p1[0], p1[1], p2[0], p2[1])
    dist_crack1 = np.minimum(dist_crack1, d_seg)

# Add jagged micro-fracture noise to crack 1
dist_crack1 += 0.007 * (n_fine - 0.5)
c1_cut = v_groove(dist_crack1, 0.010, power=0.40) * (r < 0.98)
height -= 0.20 * c1_cut
carve = np.maximum(carve, c1_cut * 0.98)
crack = np.maximum(crack, c1_cut)

# Structural height displacement across Crack 1 (+1.5 mm step across fault)
# Crack 1 line normal approximately (1, 1) / sqrt(2)
crack1_side = (u + v > -0.05).astype(np.float32)
displacement += 0.022 * crack1_side * (r < 0.98)

# MAJOR FRACTURE CRACK 2 (Branching rupture in lower-left quadrant)
nodes_crack2 = np.array([
    [-0.88, -0.20],
    [-0.70, -0.32],
    [-0.52, -0.45],
    [-0.38, -0.58],
    [-0.22, -0.72],
    [-0.12, -0.88]
], np.float32)

dist_crack2 = np.full((N, N), 999.0, np.float32)
for i in range(len(nodes_crack2) - 1):
    p1 = nodes_crack2[i]
    p2 = nodes_crack2[i + 1]
    d_seg = dist_to_segment(u, v, p1[0], p1[1], p2[0], p2[1])
    dist_crack2 = np.minimum(dist_crack2, d_seg)

dist_crack2 += 0.006 * (n_fine - 0.5)
c2_cut = v_groove(dist_crack2, 0.009, power=0.40) * (r < 0.98)
height -= 0.18 * c2_cut
carve = np.maximum(carve, c2_cut * 0.95)
crack = np.maximum(crack, c2_cut)

# Hairline secondary cracks (6 random fracture lines)
for k in range(6):
    th0 = rng.uniform(-np.pi, np.pi)
    r0 = rng.uniform(0.25, 0.60)
    length = rng.uniform(0.18, 0.40)
    ang = th0 + rng.uniform(-0.8, 0.8)
    p1 = np.array([r0 * np.cos(th0), r0 * np.sin(th0)], np.float32)
    p2 = p1 + np.array([length * np.cos(ang), length * np.sin(ang)], np.float32)
    d_h = dist_to_segment(u, v, p1[0], p1[1], p2[0], p2[1]) + 0.005 * (n_fine - 0.5)
    h_cut = v_groove(d_h, 0.0065, power=0.40) * (r < 0.98)
    height -= 0.14 * h_cut
    carve = np.maximum(carve, h_cut * 0.90)
    crack = np.maximum(crack, h_cut)

# Weathered Chipping on stone joints and perimeter edge
joint_chips = (n_fine > 0.72).astype(np.float32) * (crack > 0.3)
height -= 0.12 * joint_chips

# Apply geological displacement
height += displacement
# Outer bounding clip
height = np.where(r < 1.015, height, 0.48)
height = np.clip(height, 0.0, 1.0)


# ==============================================================================
# 5. PBR MAPS (BaseColor, Normal, Mask) & PALETTE HARMONIZATION
# ==============================================================================
print("Generating PBR texture maps...")

# Ambient Occlusion: deep shadowing inside glyphs, canals, and cracks
ao = np.clip(0.35 + 0.65 * height - 0.52 * carve, 0.18, 1.0)
ao = np.where(r < 1.015, ao, 1.0)

# BaseColor: Authentic Ancient Sandstone (matching M_UE_Ancient_Ground & Ref 1)
# High-traffic stone highlights: warm cream-sandstone (0.48, 0.42, 0.33)
# Midtone stone: weathered olive-sandstone (0.34, 0.30, 0.23)
# Shadow / dirt crevices: rich dark umber (0.13, 0.11, 0.08)
# Moss / lichen: warm sage / olive green (0.24, 0.27, 0.13) -> Strictly Q18 compliant (hue ~72°)
c_hi = np.array((0.48, 0.42, 0.33), np.float32)
c_mid = np.array((0.34, 0.30, 0.23), np.float32)
c_lo = np.array((0.13, 0.11, 0.08), np.float32)
c_moss = np.array((0.24, 0.27, 0.13), np.float32)

t_stone = height
albedo = np.where(
    t_stone[..., None] < 0.5,
    c_lo + (c_mid - c_lo) * (t_stone / 0.5)[..., None],
    c_mid + (c_hi - c_mid) * ((t_stone - 0.5) / 0.5)[..., None]
)

# Surface grain variation & natural mineral mottling
albedo *= (0.88 + 0.24 * n_fine)[..., None]
albedo *= (0.92 + 0.16 * n_mid)[..., None]

# Organic moss & loam accumulation settled in joints, cracks, and deep carved troughs
moss_weight = np.clip((carve - 0.20) * 2.2, 0, 1) * (0.35 + 0.65 * n_mid)
# Extra moss settled in outer canal and perimeter tooth gaps
moss_weight += 0.45 * np.clip(1.0 - np.abs(r - 0.725) / 0.04, 0, 1) * (n_mid > 0.40)
moss_weight += 0.50 * np.clip((r - 0.92) / 0.06, 0, 1) * (tooth_joint < 0.15)
moss_weight = np.clip(moss_weight, 0.0, 0.85)

albedo = albedo * (1.0 - moss_weight * 0.75)[..., None] + c_moss * (moss_weight * 0.75)[..., None]

# Multiply with Ambient Occlusion for rich crevice depth
albedo *= (ao[..., None] * 0.35 + 0.65)
albedo = np.where(r[..., None] < 1.015, albedo, c_mid)

# Roughness:
# Raw stone: 0.82–0.92 (matte, weathered)
# Foot-traffic worn raised stone: 0.65–0.72
# Recessed carved grooves (with powdery dust/moss): 0.88–0.95
roughness = 0.86 - 0.14 * height + 0.12 * carve
roughness = np.clip(roughness, 0.60, 0.95)

# Smoothness for URP Mask Alpha channel = (1.0 - roughness)
smoothness = 1.0 - roughness

print("Saving maps to disk...")
# BaseColor
u8_albedo = (np.clip(albedo, 0, 1) * 255 + 0.5).astype(np.uint8)[::-1]
report = verify_q18(u8_albedo, 'Central Medallion BaseColor')
write_png_rgb(f'{OUT}/ENV_Temple_Central_Medallion_BaseColor.png', u8_albedo)

# Normal Map
normal_rgb = compute_normal(height, scale=22.0)[::-1]
write_png_rgb(f'{OUT}/ENV_Temple_Central_Medallion_Normal.png', normal_rgb)

# Mask Map (URP Lit Standard: R=Metallic 0, G=Occlusion, B=0, A=Smoothness)
mask_rgba = np.zeros((N, N, 4), np.uint8)
mask_rgba[..., 0] = 0  # Metallic = 0 (dielectric stone)
mask_rgba[..., 1] = np.clip(ao * 255 + 0.5, 0, 255).astype(np.uint8)[::-1]  # AO
mask_rgba[..., 2] = 0  # Detail map
mask_rgba[..., 3] = np.clip(smoothness * 255 + 0.5, 0, 255).astype(np.uint8)[::-1]  # Smoothness
write_png_rgba(f'{OUT}/ENV_Temple_Central_Medallion_Mask.png', mask_rgba)

with open(f'{OUT}/texture_q18.json', 'w') as f:
    json.dump(report, f, indent=2)

print("SUCCESS: 2048 PBR maps written and Q18 verified.")

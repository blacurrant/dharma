"""Colour audit straight from the PNG bytes (no Blender, no colour management): HSV saturation / hue / cyan test on the stored 8-bit sRGB values.
Run with Blender's python for numpy:  Blender -b --factory-startup --python scripts/16_color_audit.py
Supersedes the saturation / hue / hex figures in evidence/11_texture_qa.json (those double-applied the sRGB transfer function: see VF_HANDOFF_REPORT.md corrections).
Definitions:  HSV saturation s = (max-min)/max on the stored sRGB bytes /255;  hue in degrees;  'visible' = alpha > 0.02 (stored alpha / 255);
cyan-teal = hue in [145, 215] AND s > 0.06.   Colour under alpha 0 is also checked ('all texels').
"""
import zlib, struct, json, os, glob, math
import numpy as np
VF = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff'


def read_png(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n'
    pos, idat, hdr = 8, b'', None
    while pos < len(b):
        n, = struct.unpack('>I', b[pos:pos + 4]); t = b[pos + 4:pos + 8]; d = b[pos + 8:pos + 8 + n]; pos += 12 + n
        if t == b'IHDR': hdr = struct.unpack('>IIBBBBB', d)
        elif t == b'IDAT': idat += d
    w, h, bd, ct = hdr[:4]
    assert bd == 8 and hdr[5:] == (0, 0)
    ch = {0: 1, 2: 3, 4: 2, 6: 4}[ct]
    raw = np.frombuffer(zlib.decompress(idat), np.uint8).reshape(h, 1 + w * ch)
    assert (raw[:, 0] == 0).all(), 'non-zero PNG filter: this reader only supports filter 0 (the generator\'s writer)'
    return raw[:, 1:].reshape(h, w, ch)


def hsv(rgb):
    x = rgb.astype(np.float32) / 255.0
    mx, mn = x.max(-1), x.min(-1); d = mx - mn
    s = np.where(mx > 0, d / np.maximum(mx, 1e-9), 0.0)
    dd = np.maximum(d, 1e-9); r, g, b = x[..., 0], x[..., 1], x[..., 2]
    h = np.where(mx == r, ((g - b) / dd) % 6, np.where(mx == g, (b - r) / dd + 2, (r - g) / dd + 4)) * 60.0
    return h, s, mx


def hexof(c):
    return '#%02X%02X%02X' % tuple(int(round(float(v))) for v in c)


def srgb_to_lin(v):
    v = v / 255.0
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(v):
    v = np.clip(v, 0, 1)
    return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(np.maximum(v, 1e-9), 1 / 2.4) - 0.055) * 255.0


gen = json.load(open(VF + '/evidence/10_generation.json'))['textures']
out = {}
for t in gen:
    name = os.path.basename(t['file'])[:-4]
    a = read_png(VF + '/' + t['file'])
    r = dict(shape=list(a.shape), color_space=t['color_space'])
    if 'Floor_MacroValue' in name:
        r['kind'] = 'grey data, single-channel PNG (no colour)'; r['png_channels'] = int(a.shape[-1]); r['saturation_max'] = 0.0
    elif 'MacroTint' in name:
        r['kind'] = 'RGB data (neutral 128); applied as multiplier 2*t'
        mult = a.astype(np.float32) / 255.0 * 2.0
        r['multiplier_min'] = [round(float(mult[..., i].min()), 3) for i in range(3)]; r['multiplier_max'] = [round(float(mult[..., i].max()), 3) for i in range(3)]
        # the two extreme tints (largest warm / cool deviations)
        warm = mult[np.unravel_index(np.argmax(mult[..., 0] - mult[..., 2]), mult.shape[:2])]; cool = mult[np.unravel_index(np.argmax(mult[..., 2] - mult[..., 0]), mult.shape[:2])]
        def hue_of(c):
            cc = (np.array(c) * 255 / 2).reshape(1, 1, 3); h, s, _ = hsv(cc); return round(float(h[0, 0]), 1), round(float(s[0, 0]), 3)
        r['warmest_multiplier'] = [round(float(v), 3) for v in warm]; r['warmest_multiplier_hue_sat(of the raw data colour)'] = hue_of(warm)
        r['coolest_multiplier'] = [round(float(v), 3) for v in cool]; r['coolest_multiplier_hue_sat(of the raw data colour)'] = hue_of(cool)
        h, s, _ = hsv(a[..., :3])
        r['raw_data_hue_range_all_texels_deg'] = [round(float(h.min()), 1), round(float(h.max()), 1)]; r['raw_data_saturation_max'] = round(float(s.max()), 3)
        r['raw_data_texels_in_145_215_with_sat_gt_0_06'] = int(((h >= 145) & (h <= 215) & (s > 0.06)).sum())
        # effect on a neutral stone card (#8A857D) and on the shipped floor mean: result hue/sat/cyan
        base = np.array([0x8A, 0x85, 0x7D], np.float32)
        res = {}
        for lbl, m in (('warmest', warm), ('coolest', cool), ('all_texels_k1.0', None)):
            if m is not None:
                c = lin_to_srgb(srgb_to_lin(base) * np.array(m)); h2, s2, _ = hsv(c.reshape(1, 1, 3)); res[lbl] = dict(hex=hexof(c), hue=round(float(h2[0, 0]), 1), sat=round(float(s2[0, 0]), 3))
            else:
                c = lin_to_srgb(srgb_to_lin(base)[None, None, :] * mult); h2, s2, _ = hsv(c)
                res[lbl] = dict(hue_range=[round(float(h2.min()), 1), round(float(h2.max()), 1)], sat_max=round(float(s2.max()), 3),
                                texels_in_145_215_with_sat_gt_0_06=int(((h2 >= 145) & (h2 <= 215) & (s2 > 0.06)).sum()), hue_range_p1_p99_where_sat_gt_0_06=[round(float(np.percentile(h2[s2 > 0.06], 1)), 1), round(float(np.percentile(h2[s2 > 0.06], 99)), 1)])
        r['applied_to_neutral_stone_#8A857D'] = res
    else:
        r['kind'] = 'colour + straight alpha'
        rgb, al = a[..., :3], a[..., 3].astype(np.float32) / 255.0
        h, s, v = hsv(rgb)
        vis = al > 0.02; hi = al > 0.5
        cy_all = (h >= 145) & (h <= 215) & (s > 0.06)
        r['texels_visible_a_gt_0_02'] = int(vis.sum()); r['texels_a_gt_0_5'] = int(hi.sum())
        r['cyan_texels_visible'] = int((cy_all & vis).sum()); r['cyan_texels_all_incl_alpha0'] = int(cy_all.sum())
        for lbl, m in (('visible', vis), ('a_gt_0_5', hi)):
            if m.any():
                r['saturation_' + lbl] = dict(p50=round(float(np.median(s[m])), 3), p95=round(float(np.percentile(s[m], 95)), 3), max=round(float(s[m].max()), 3))
        sat = vis & (s > 0.06)
        r['hue_deg_visible_sat_gt_0_06_p1_p50_p99'] = [round(float(np.percentile(h[sat], q)), 1) for q in (1, 50, 99)] if sat.any() else None
        r['hue_deg_visible_sat_gt_0_06_min_max'] = [round(float(h[sat].min()), 1), round(float(h[sat].max()), 1)] if sat.any() else None
        r['texels_visible_sat_gt_0_06_outside_30_77'] = int((sat & ((h < 30) | (h > 77))).sum()); r['texels_visible_sat_gt_0_06'] = int(sat.sum())
        if hi.any():
            r['mean_rgb_bytes_a_gt_0_5'] = hexof(rgb[hi].mean(0))
        w = al[..., None]
        r['alpha_weighted_mean_hex'] = hexof((rgb * w).sum((0, 1)) / max(float(w.sum()), 1e-9))
        r['darkest_visible_p5_hex'] = hexof(np.percentile(rgb[vis], 5, axis=0)) if vis.any() else None
    out[name] = r
    print('AUDIT', name, json.dumps({k: v for k, v in r.items() if k not in ('shape', 'color_space')})[:700], flush=True)
json.dump(out, open(VF + '/evidence/16_color_audit.json', 'w'), indent=1)
print('AUDIT_DONE')

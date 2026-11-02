"""VF handoff QA: reads every PNG back through Blender's loader (independent of the writer) and measures.
 - seam: |wrap neighbour diff| vs |interior neighbour diff| (ratio ~1 = seamless) for the textures declared tileable
 - cyan/teal: alpha-weighted fraction of texels with hue in [145,215] deg and sat > 0.06 (colour maps) -> must be 0
 - data maps: mean (neutral 0.5), std inside r<10 m vs outside r>13 m (macro value)
 - alpha: mean, coverage at several thresholds; colour defined where alpha==0 (no black halos): colour mean where a<0.01 vs where a>0.5
"""
import bpy, json, colorsys, os
import numpy as np
VF = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff'
man = json.load(open(VF + '/evidence/10_generation.json'))['textures']
out = {}


def load(path, data):
    im = bpy.data.images.load(path, check_existing=False)
    im.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    if not data:
        im.alpha_mode = 'STRAIGHT'
    w, h = im.size
    a = np.empty(w * h * im.channels, np.float32); im.pixels.foreach_get(a)
    a = a.reshape(h, w, im.channels); n = im.channels
    bpy.data.images.remove(im); return a, n


def seam(a2, axes):
    """wrap-line step vs the distribution of ALL interior line steps; rank = fraction of interior lines with a LARGER step than the wrap (>=0.05 = wrap is typical)."""
    r = {}
    for ax, nm in ((0, 'rows(v)'), (1, 'cols(u)')):
        if ax not in axes:
            continue
        a = np.moveaxis(a2, ax, 0)
        steps = np.abs(np.diff(a, axis=0)).reshape(a.shape[0] - 1, -1).mean(1)
        wrap = float(np.abs(a[0] - a[-1]).mean())
        r[nm] = dict(wrap=round(wrap, 5), interior_mean=round(float(steps.mean()), 5), interior_p95=round(float(np.percentile(steps, 95)), 5), interior_max=round(float(steps.max()), 5),
                     rank_frac_interior_lines_larger=round(float((steps > wrap).mean()), 3))
    return r


def seam_old(a2, axes):
    r = {}
    for ax, nm in ((0, 'rows(v)'), (1, 'cols(u)')):
        if ax not in axes:
            continue
        wrap = np.abs(np.take(a2, 0, axis=ax) - np.take(a2, -1, axis=ax)).mean()
        inter = np.abs(np.diff(a2, axis=ax)).mean()
        r[nm] = dict(wrap=round(float(wrap), 5), interior_step=round(float(inter), 5), ratio=round(float(wrap / max(inter, 1e-9)), 2))
    return r


for t in man:
    name = os.path.basename(t['file'])[:-4]
    data = 'data' in t['color_space'].lower() or 'LINEAR' in t['color_space']
    a, n = load(VF + '/' + t['file'], data)
    r = dict(shape=list(a.shape), color_space=t['color_space'])
    tileable = ('seamless' in t['tiling'])
    border_map = 'ONE' in t['tiling']
    axes = (0, 1)
    if 'MossWallBase' in name: axes = (1,)
    if tileable or 'MacroValue' in name:
        lum = a[..., :3].mean(2) if n >= 3 else a[..., 0]
        al = a[..., 3] if n == 4 else None
        r['seam_luma'] = seam(lum, axes if tileable else ())
        if al is not None:
            r['seam_alpha'] = seam(al, axes)
        if n >= 3:
            r['seam_rgb_where_visible'] = seam(a[..., :3] * (al[..., None] if al is not None else 1), axes)
    if data:
        n = 1 if 'Tint' not in name else 3
        a = a[..., :n]
    if n == 4:
        al = a[..., 3]; rgb = a[..., :3]
        r['alpha'] = dict(mean=round(float(al.mean()), 4), max=round(float(al.max()), 3), cov_gt_0_05=round(float((al > .05).mean()), 4), cov_gt_0_5=round(float((al > .5).mean()), 4))
        # hue test on sRGB-encoded values for texels with a > 0.02
        m = al > 0.02
        px = rgb[m]
        # LOAD returned sRGB-decoded floats? the image is flagged sRGB so pixels are LINEAR; convert back to display to judge hue
        disp = np.where(px <= 0.0031308, px * 12.92, 1.055 * np.power(np.clip(px, 1e-9, 1), 1 / 2.4) - 0.055)
        mx, mn = disp.max(1), disp.min(1); sat = (mx - mn) / np.maximum(mx, 1e-6)
        d = np.maximum(mx - mn, 1e-9); rr, gg, bb = disp[:, 0], disp[:, 1], disp[:, 2]
        hue = np.where(mx == rr, ((gg - bb) / d) % 6, np.where(mx == gg, (bb - rr) / d + 2, (rr - gg) / d + 4)) * 60
        cy = (hue >= 145) & (hue <= 215) & (sat > 0.06)
        r['teal_cyan'] = dict(texels_checked=int(m.sum()), cyan_texels=int(cy.sum()), max_sat_overall=round(float(sat.max()), 3), hue_p50=round(float(np.median(hue)), 1),
                              hue_range_p1_p99=[round(float(np.percentile(hue, 1)), 1), round(float(np.percentile(hue, 99)), 1)])
        # halo test: colour in transparent texels vs in opaque texels
        from numpy.lib.stride_tricks import sliding_window_view as swv
        hi_ = al > 0.4; lo_ = al < 0.01
        near = np.zeros_like(hi_)
        for dy in (-2, -1, 0, 1, 2):
            for dx in (-2, -1, 0, 1, 2):
                near |= np.roll(np.roll(hi_, dy, 0), dx, 1)
        edge_t = lo_ & near
        if edge_t.any() and hi_.any():
            # nearest-opaque colour approximated by the mean of opaque texels in the same 5x5 neighbourhood
            from itertools import product
            acc = np.zeros(rgb.shape, np.float32); cnt = np.zeros(al.shape, np.float32)
            for dy, dx in product((-2, -1, 0, 1, 2), repeat=2):
                m_ = np.roll(np.roll(hi_, dy, 0), dx, 1); c_ = np.roll(np.roll(rgb, dy, 0), dx, 1)
                acc += c_ * m_[..., None]; cnt += m_
            near_col = acc / np.maximum(cnt, 1)[..., None]
            d = np.abs(rgb - near_col).max(2)[edge_t]
            r['halo_edge_texels'] = dict(count=int(edge_t.sum()), mean_abs_rgb_diff_to_adjacent_visible=round(float(d.mean()), 4), p99=round(float(np.percentile(d, 99)), 4), max=round(float(d.max()), 4))
        lo = al < 0.01; hi = al > 0.5
        if lo.any() and hi.any():
            r['halo'] = dict(rgb_mean_transparent=[round(float(x), 3) for x in rgb[lo].mean(0)], rgb_mean_opaque=[round(float(x), 3) for x in rgb[hi].mean(0)])
        # display-space mean colour of opaque texels (hex)
        if hi.any():
            c = rgb[hi].mean(0); cd = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.clip(c, 1e-9, 1), 1 / 2.4) - 0.055)
            r['opaque_mean_hex'] = '#%02X%02X%02X' % tuple(int(round(float(x) * 255)) for x in cd)
    else:
        if n == 3:
            for i, c in enumerate('RGB'):
                pass
            r['channels'] = {c: dict(min=round(float(a[..., i].min()), 3), mean=round(float(a[..., i].mean()), 3), max=round(float(a[..., i].max()), 3)) for i, c in enumerate('RGB')}
            # hue of the extreme tints (as a colour offset; display = data here)
            ext = []
            for sel, nm in ((a.sum(2) > np.percentile(a.sum(2), 99.5), 'warmest'), (a.sum(2) < np.percentile(a.sum(2), 0.5), 'coolest')):
                pass
            warm = a[a[..., 0] - a[..., 2] > np.percentile(a[..., 0] - a[..., 2], 99.5)].mean(0)
            cool = a[a[..., 2] - a[..., 0] > np.percentile(a[..., 2] - a[..., 0], 99.5)].mean(0)
            r['coolest_5pct_example_rgb(0..1)'] = [round(float(x), 3) for x in cool]
            r['warmest_example_rgb'] = [round(float(x), 3) for x in warm]
        else:
            g = a[..., 0]
            H = g.shape[0]
            x = (np.arange(H) + 0.5) / H * 40 - 20; z = 20 - (np.arange(H) + 0.5) / H * 40
            X, Z = np.meshgrid(x, z); R = np.hypot(X, Z)
            r['data'] = dict(mean=round(float(g.mean()), 4), min=round(float(g.min()), 3), max=round(float(g.max()), 3), std_all=round(float(g.std()), 4),
                             std_r_lt_10=round(float(g[R < 10].std()), 4), std_r_gt_13=round(float(g[R > 13].std()), 4), mean_r_lt_10=round(float(g[R < 10].mean()), 4),
                             p1_p99_r_lt_10=[round(float(np.percentile(g[R < 10], 1)), 3), round(float(np.percentile(g[R < 10], 99)), 3)],
                             p1_p99_r_gt_13=[round(float(np.percentile(g[R > 13], 1)), 3), round(float(np.percentile(g[R > 13], 99)), 3)])
    if border_map:
        r['seam_test'] = 'not applicable: per-tile-border map (content is anchored to the tile border; each tile edge is independent by design)'
    out[name] = r
    print('QA', name, json.dumps({k: v for k, v in r.items() if k not in ('shape', 'color_space')})[:900], flush=True)
json.dump(out, open(VF + '/evidence/11_texture_qa.json', 'w'), indent=1)
print('QA_DONE')

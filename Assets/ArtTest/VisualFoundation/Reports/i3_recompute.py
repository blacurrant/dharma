#!/usr/bin/env python3
"""Recompute floor luma, character separation and telegraph lift from the stored evidence (needs only PIL).
Mirrors VFRunner.MeasureRoutine exactly (same strides, thresholds, Rec.709 luma on the 8-bit frame).
Usage: python3 i3_recompute.py <evidence_dir> <label> [<label> ...]
Evidence per label: <label>_floorMask.png, _silPlayer.png, _silEnemy.png (full 1920x1080, upright PNG, white = true),
                    <label>_A_actors_telegraphOff.png, _F_floorOnly.png, _FT_floorPlusTelegraph.png (cropped to the box in <label>_crop.json)
Arrays in Unity are bottom-up; PNG row r (from top) = array row H-1-r.
"""
import json, sys, os
from PIL import Image

def lum(p): return (0.2126 * p[0] + 0.7152 * p[1] + 0.0722 * p[2]) / 255.0

def recompute(d, label):
    c = json.load(open(f"{d}/{label}_crop.json")); W, H, x0, y0, bw, bh = c["W"], c["H"], c["x0"], c["y0_bottomUp"], c["w"], c["h"]
    ld = lambda n: Image.open(f"{d}/{label}_{n}.png").convert("RGB")
    fm, sp, se = [ld(n).convert("L").load() for n in ("floorMask", "silPlayer", "silEnemy")]
    A, F, FT = [ld(n).load() for n in ("A_actors_telegraphOff", "F_floorOnly", "FT_floorPlusTelegraph")]
    def mask(m, x, yb): return m[x, H - 1 - yb] > 127
    def px(img, x, yb):
        xx, yy = x - x0, yb - y0
        if xx < 0 or yy < 0 or xx >= bw or yy >= bh: return None
        return img[xx, bh - 1 - yy]
    # floor mean luma (floor-mask pixels that are not character) and telegraph lift
    fs = 0.0; fn = 0; lifts = []
    for y in range(0, H, 2):          # Unity samples the floor mask at (x even, y even) screen coordinates -> array row H-1-y
        yb = H - 1 - y
        for x in range(0, W, 2):
            if not mask(fm, x, yb): continue
            a, f, ft = px(A, x, yb), px(F, x, yb), px(FT, x, yb)
            if abs(lum(a) - lum(f)) <= 0.012: fs += lum(f); fn += 1
            dd = lum(ft) - lum(f)
            if dd > 0.004: lifts.append(dd)
    lifts.sort(); lm = sum(lifts) / len(lifts) if lifts else 0; p10 = lifts[len(lifts) // 10] if lifts else 0
    def sep(sil):
        near = set(); cs = bs = 0.0; cn = bn = 0
        for yb in range(10, H - 10, 2):
            for x in range(10, W - 10, 2):
                if not mask(sil, x, yb): continue
                for dy in range(-10, 11, 5):
                    for dx in range(-10, 11, 5): near.add((yb + dy) * W + x + dx)
        # the Unity loop walks every 2nd flat index: i = yb*W + x with i even
        for yb in range(H):
            start = 0 if (yb * W) % 2 == 0 else 1
            for x in range(start, W, 2):
                i = yb * W + x
                if mask(sil, x, yb):
                    a = px(A, x, yb)
                    if a is not None: cs += lum(a); cn += 1
                elif i in near:
                    f = px(F, x, yb)
                    if f is not None: bs += lum(f); bn += 1
        return (cs / cn - bs / bn) if cn and bn else float("nan")
    return dict(label=label, floor_mean_luma_8m=round(fs / max(1, fn), 3), player_sep=round(sep(sp), 3), enemy_sep=round(sep(se), 3), lift_mean=round(lm, 3), lift_p10=round(p10, 3))

if __name__ == "__main__":
    d = sys.argv[1]
    for lab in sys.argv[2:]: print(recompute(d, lab))

#!/usr/bin/env python3
"""Bakes Textures/VF_OuterGround_MacroGradient_1024.png for the 160 x 160 m outer-ground quad (1024 px = 0.156 m/px).
Colour = lerp( base * (1 + CONTRAST*(macro-0.5)), FOG, smoothstep(0,1,(d-20)/38) ), d = max(|x|,|z|) in metres (parapet foot at 20 m).
macro = VF_Floor_MacroValue_NoDamp_2048 (copied, unedited) tiled once per 70 m. Raw colour numbers are written as sRGB-encoded pixels (the material _BaseColor is set to white),
so the base value matches what the former _BaseColor 0.275,0.225,0.1875 produced."""
import os
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
M = Image.open(os.path.join(ROOT, 'Textures', 'VF_Floor_MacroValue_NoDamp_2048.png')).convert('L'); mw, mh = M.size; mp = M.load()
BASE = (0.275, 0.225, 0.1875); FOG = (0.10, 0.085, 0.075); CONTRAST = 0.45; CYCLE = 70.0; SIZE = 160.0; N = 1024
out = Image.new('RGB', (N, N)); op = out.load()
for j in range(N):
    z = (j / (N - 1) - 0.5) * SIZE
    for i in range(N):
        x = (i / (N - 1) - 0.5) * SIZE
        u = (x / CYCLE) % 1.0; v = (z / CYCLE) % 1.0
        m = mp[int(u * (mw - 1)), int(v * (mh - 1))] / 255.0
        f = 1.0 + CONTRAST * (m - 0.5)
        d = max(abs(x), abs(z)); t = min(1.0, max(0.0, (d - 20.0) / 38.0)); t = t * t * (3 - 2 * t)
        c = [min(1.0, BASE[k] * f) * (1 - t) + FOG[k] * t for k in range(3)]
        op[i, j] = tuple(int(round(max(0.0, min(1.0, ch)) * 255)) for ch in c)
out.save(os.path.join(ROOT, 'Textures', 'VF_OuterGround_MacroGradient_1024.png'))
print('baked')

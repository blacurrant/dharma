#!/usr/bin/env python3
"""Share of non-HUD pixels whose Rec.709 luma (sRGB-encoded values /255) is below a threshold. HUD box (top-left 45% x 35%) is masked out in every frame."""
import sys
from PIL import Image
def share(p, thr):
    im = Image.open(p).convert('RGB'); W, H = im.size; px = im.load(); n = 0; k = 0; t = thr*255
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if y < 0.35*H and x < 0.45*W: continue
            r, g, b = px[x, y]; n += 1; k += (0.2126*r+0.7152*g+0.0722*b) < t
    return 100.0*k/n
if __name__ == '__main__':
    pre = sys.argv[1] if len(sys.argv) > 1 else 'real/before'; post = sys.argv[2] if len(sys.argv) > 2 else 'real/real_shadowON'
    print('camera,view,thr,before_pct,after_pct')
    for cam in ('B', 'A2'):
        for v in ('centre', 'north', 'west', 'dais', 'arch', 'edge'):
            for thr in (0.08, 0.12): print(f'{cam},{v},{thr},{share(f"{pre}_{cam}_{v}.png", thr):.1f},{share(f"{post}_{cam}_{v}.png", thr):.1f}')

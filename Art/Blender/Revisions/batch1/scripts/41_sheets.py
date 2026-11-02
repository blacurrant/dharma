"""Compose labelled BEFORE | AFTER sheets from renders/*.png with system PIL.  python3 scripts/41_sheets.py [walls|pylons|ruins|backdrops|all]"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch1'
R = G + '/renders'
os.makedirs(G + '/contact', exist_ok=True)
try:
    F = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 34); F2 = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 26)
except Exception:
    F = F2 = ImageFont.load_default()


def sheet(out, title, rows, scale=0.5):
    """rows: [(row_label, [(png, caption), ...])] ; panels scaled by `scale`."""
    pw, ph = int(1920 * scale), int(1080 * scale)
    ncol = max(len(r[1]) for r in rows)
    W = ncol * pw + (ncol + 1) * 12
    H = 70 + len(rows) * (ph + 76) + 12
    im = Image.new('RGB', (W, H), (22, 22, 24)); d = ImageDraw.Draw(im)
    d.text((14, 14), title, fill=(235, 232, 220), font=F)
    y = 70
    for label, panels in rows:
        d.text((14, y), label, fill=(190, 186, 170), font=F2)
        for ci, (png, cap) in enumerate(panels):
            x = 12 + ci * (pw + 12)
            p = Image.open(f'{R}/{png}.png').convert('RGB').resize((pw, ph), Image.LANCZOS)
            im.paste(p, (x, y + 34)); d.text((x + 6, y + 36), cap, fill=(255, 255, 255), font=F2, stroke_width=2, stroke_fill=(0, 0, 0))
        y += ph + 76
    im.save(out); print('SHEET', out, im.size)


which = sys.argv[1] if len(sys.argv) > 1 else 'all'
B, A = 'BEFORE', 'AFTER'
if which in ('all', 'walls'):
    for v in ('A', 'B'):
        sheet(f'{G}/contact/Wall_Tall_{v}_BEFORE_AFTER.png', f'Wall_Tall_{v}: BEFORE | AFTER  (gameplay camera offset 12,18,-12, ortho 9; only Wall_Tall_{v} instances in AFTER)',
              [('north wall (player proxy near x=-9, z=17)', [(f'WallTall_{v}_north_BEFORE', B), (f'WallTall_{v}_north_AFTER', A)]),
               ('west wall (player proxy near x=-16, z=3)', [(f'WallTall_{v}_west_BEFORE', B), (f'WallTall_{v}_west_AFTER', A)])])
    sheet(f'{G}/contact/Wall_Tall_ALL_BEFORE_AFTER.png', 'Wall_Tall A+B together: BEFORE | AFTER',
          [('north wall', [('WallTall_ALL_north_BEFORE', B), ('WallTall_ALL_north_AFTER', A)]), ('west wall', [('WallTall_ALL_west_BEFORE', B), ('WallTall_ALL_west_AFTER', A)])])
if which in ('all', 'pylons'):
    sheet(f'{G}/contact/Lantern_Pylon_A_BEFORE_AFTER.png', 'Lantern_Pylon_A: BEFORE | AFTER (6 placements)',
          [('dais stairs flank pair', [('Pylon_stairs_BEFORE', B), ('Pylon_stairs_AFTER', A)]), ('arch flank pair', [('Pylon_arch_BEFORE', B), ('Pylon_arch_AFTER', A)]),
           ('west wall pair', [('Pylon_west_BEFORE', B), ('Pylon_west_AFTER', A)])])
if which in ('all', 'ruins'):
    for v, nm in (('A', 'Ruin_Cluster_A'), ('B', 'Ruin_Cluster_B')):
        sheet(f'{G}/contact/{nm}_BEFORE_AFTER.png', f'{nm}: BEFORE | AFTER (only {nm} instances in AFTER)', [('west / south-west, camera near x=-13, z=-8', [(f'Ruin_{v}_BEFORE', B), (f'Ruin_{v}_AFTER', A)])])
    sheet(f'{G}/contact/Ruin_Clusters_ALL_BEFORE_AFTER.png', 'Ruin_Cluster A+B: BEFORE | AFTER (3 placements)', [('west / south-west', [('Ruin_ALL_BEFORE', B), ('Ruin_ALL_AFTER', A)])])
if which in ('all', 'backdrops'):
    for v, side in (('A', 'north'), ('B', 'north'), ('C', 'west')):
        sheet(f'{G}/contact/Backdrop_Mass_{v}_BEFORE_AFTER.png', f'Backdrop_Mass_{v}: BEFORE (courtyard + tall bays) | AFTER recommended 5 m band | AFTER directive 28-55 m',
              [(f'{side} side', [(f'Backdrop_{v}_{side}_BEFORE', 'BEFORE (+tall bays)'), (f'Backdrop_{v}_{side}_AFTER_recommended', 'AFTER: 5 m band'), (f'Backdrop_{v}_{side}_AFTER_directive28-55m', 'AFTER: 28-55 m')])], scale=0.42)

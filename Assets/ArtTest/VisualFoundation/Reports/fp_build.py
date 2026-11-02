import csv, os, statistics as st
from PIL import Image, ImageDraw
V = '/Users/landerstudio/MythicRoguelite/Assets/ArtTest/VisualFoundation/'
P = V + 'Captures/final_package/'
views = ['centre', 'north', 'west', 'dais', 'arch', 'edge']
os.makedirs(P + 'composites', exist_ok=True)
def comp(cam, v):
    a = Image.open(f'{P}before_{cam}_{v}.png').convert('RGB'); b = Image.open(f'{P}after_{cam}_{v}.png').convert('RGB')
    im = Image.new('RGB', (3848, 1080), (255, 255, 255)); im.paste(a, (0, 0)); im.paste(b, (1928, 0)); d = ImageDraw.Draw(im)
    d.text((10, 1060), f'BEFORE (original courtyard) {cam} {v}', fill=(255, 255, 0)); d.text((1938, 1060), f'AFTER (Visual Foundation) {cam} {v}', fill=(255, 255, 0)); im.save(f'{P}composites/{cam}_{v}_before_after.png')
for cam in ('B', 'A2'):
    for v in views: comp(cam, v)
for cam in ('B', 'A2'):
    W = 640; H = 360; sh = Image.new('RGB', (2 * W + 8, 6 * (H + 8)), (255, 255, 255)); d = ImageDraw.Draw(sh)
    for i, v in enumerate(views):
        for j, t in enumerate(('before', 'after')):
            sh.paste(Image.open(f'{P}{t}_{cam}_{v}.png').convert('RGB').resize((W, H)), (j * (W + 8), i * (H + 8))); d.text((j * (W + 8) + 6, i * (H + 8) + 6), f'{t.upper()} {cam} {v}', fill=(255, 255, 0))
    sh.save(f'{P}overview_{cam}.png')
for seq in ('run', 'dash', 'attack'):
    W = 480; H = 270; sh = Image.new('RGB', (4 * W + 24, 2 * H + 8), (255, 255, 255)); d = ImageDraw.Draw(sh)
    for k in range(8):
        sh.paste(Image.open(f'{P}seq/{seq}_{k:02d}.png').convert('RGB').resize((W, H)), ((k % 4) * (W + 8), (k // 4) * (H + 8))); d.text(((k % 4) * (W + 8) + 6, (k // 4) * (H + 8) + 6), f'{seq} {k}', fill=(255, 255, 0))
    sh.save(f'{P}strip_{seq}.png')
def lum_share(p, thr):
    im = Image.open(p).convert('RGB'); W, H = im.size; px = im.load(); n = k = 0
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if y < 0.35 * H and x < 0.45 * W: continue
            r, g, b = px[x, y]; n += 1; k += (0.2126 * r + 0.7152 * g + 0.0722 * b) < thr * 255
    return 100.0 * k / n
rows = []
for t in ('before', 'after'):
    m = {r['variant']: r for r in csv.DictReader(open(f'{V}Reports/fp_metrics_{t}.csv'))}
    s = {(r['camera'], r['view']): r for r in csv.DictReader(open(f'{V}Reports/fp_stats_{t}.csv'))}
    for cam in ('B', 'A2'):
        for v in views:
            r = m[f'{t}_{cam}_{v}']; q = s[(cam, v)]
            rows.append(dict(state=t, cam=cam, view=v, floor=r['floor_mean_luma_8m'], player_luma=r['player_luma'], enemy_luma=r['enemy_luma'], player_sep=r['player_sep'], enemy_sep=r['enemy_sep'], lift=r['telegraph_fill_mean_lift'],
                dim12=round(lum_share(f'{P}{t}_{cam}_{v}.png', 0.12), 1), dim08=round(lum_share(f'{P}{t}_{cam}_{v}.png', 0.08), 1), draw_calls=q['draw_calls'], setpass=q['set_pass'], tris=q['triangles'], casters=q['shadow_casters']))
w = csv.DictWriter(open(V + 'Reports/fp_table.csv', 'w', newline=''), fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for t in ('before', 'after'):
    pr = list(csv.DictReader(open(f'{V}Reports/fp_perf_{t}.csv')))
    print(t, 'ms', [r['avg_ms'] for r in pr], 'dc', pr[0]['draw_calls'], 'sp', pr[0]['setpass'], 'tris', pr[0]['tris'], 'casters', pr[0]['shadow_casters'])
for r in rows: print(*[r[k] for k in r])

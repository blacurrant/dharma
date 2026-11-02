import csv,glob,collections,statistics
from PIL import Image
D='data/'
rows=[]
for f in sorted(glob.glob(D+'[ABC]_*.csv')):
    rows+= [r for r in csv.DictReader(open(f)) if r['label']=='ALL']
seqs=['idle','run','dash_rest','dash_run','attack','dodge','chain','edge_up','edge_down','far_chase_up','far_chase_down']
T={(r['config'],r['fps_mode'],r['sequence']):r for r in rows}
CFG=[('A_plain','OFF'),('B_plain','OFF'),('C_plain','OFF'),('A_focusON','ON'),('B_focusON','ON')]
out=['| Config | Focus | FPS state (avg fps) | Sequence | Min margin, ring around player (px) | Min margin, fixed 10 m zone at centre (px) | Player/enemy outside frame (frames/total) | Telegraph fully in frame (frames) |','|---|---|---|---|---|---|---|---|']
for cfg,focus in CFG:
    for mode in (['cap60','uncapped'] if 'plain' in cfg else ['cap60']):
        for s in seqs:
            r=T.get((cfg,mode,s))
            if not r: continue
            out.append(f"| {cfg[0]} | {focus} | {mode} ({r['avg_fps']}) | {s} | {r['min_margin_player_ring_px']} | {r['min_margin_fixed_ring_px']} | {r['not_all_in_frame_frames']}/{r['frames']} | {r['telegraph_all_in_frame']}/{r['telegraph_frames']} |")
tbl='\n'.join(out)
summ=[]
for cfg,focus in CFG:
    rr=[r for r in rows if r['config']==cfg]
    mp=min(int(r['min_margin_player_ring_px']) for r in rr); mf=min(int(r['min_margin_fixed_ring_px']) for r in rr)
    neg=sum(1 for r in rr if int(r['min_margin_player_ring_px'])<0)
    fr=sum(int(r['frames']) for r in rr); nf=sum(int(r['not_all_in_frame_frames']) for r in rr)
    tf=sum(int(r['telegraph_frames']) for r in rr); ti=sum(int(r['telegraph_all_in_frame']) for r in rr)
    summ.append(f"| {cfg[0]} | {focus} | {mp} | {neg}/{len(rr)} | {mf} | {nf}/{fr} | {ti}/{tf} |")
ch=collections.defaultdict(list)
for r in csv.reader(open(D+'char_height.csv')):
    ch[r[0].split('_')[0]+('' if 'plain' in r[0] else '+focusON')].append((float(r[4]),r[2]))
cl=[]
for k,v in sorted(ch.items()):
    st_=[p for p,s in v if p>0 and s!='dash_rest' and s!='dash_run']
    al=[p for p,s in v if p>0]
    m=sorted(st_)[len(st_)//2]
    cl.append(f"| {k} | {len(al)} | {int(m)} px = {m/10.8:.1f}% | {int(min(st_))}-{int(max(st_))} px | {int(min(al))} px ({min(al)/10.8:.1f}%) |")
perf=[]
for f in sorted(glob.glob(D+'perf/perf_*.csv')):
    R=list(csv.DictReader(open(f))); c=lambda k:[float(r[k]) for r in R]; dt=sorted(c('dt_ms'))
    perf.append(f"| {f.split('perf_')[1][:-4]} | {statistics.median(dt):.2f} | {dt[int(len(dt)*.95)]:.2f} | {statistics.median(c('cpuMain_ms')):.2f} | {int(statistics.median(c('drawCalls')))} | {int(statistics.median(c('setPass')))} | {statistics.median(c('triangles'))/1e6:.2f} | {int(statistics.median(c('shadowCasters')))} |")
luma=list(csv.DictReader(open(D+'luma_lift.csv')))
ll=[f"| {r['surface']} | {r['alpha_fill']} | {r['part']} | {r['mean_luma_lift']} | {r['p10_luma_lift']} | {r['max_luma_lift']} |" for r in luma]
heights=open(D+'model_heights.txt').read().strip().replace('\n','; ')
NL='\n'
rep=f'''# Gate 1: key light + camera matrix (ArtTest_TempleCourtyard)

Continues from `CAMERA_LIGHTING_REPORT.md` and the saved `ArtTest_TempleCourtyard.unity`. All figures are **Editor-only, Play Mode**: Unity 6000.6.7f1, URP 17.6, Metal, Apple M5. Raw data in `data/` (per-config CSVs, `char_height.csv`, `luma_lift.csv`, `perf/*.csv`, `shots/`). Harness: `Assets/ArtTest/Scripts/ArtTestSequenceRunner.cs`.

## Step 1: key light (frozen for all runs)
- Before: euler (46, 318, 0): **2.2 deg** (3D) / **3.0 deg** (horizontal) off the camera view direction, elevation 46 deg (matches the Director's and QA's figures).
- After: euler (**38, 45, 0**): **63.4 deg** (3D) / **90.0 deg** (horizontal), elevation **38 deg**. Light travels toward +X+Z; shadows fall screen-right/up.
- Same frozen pose, geometry and materials: `key_before_*.png`, `key_after_*.png`, `key_BA_gameplay.png`, `key_BA_wide.png`. Probes re-baked (207 probes, 3 s). Saved in the scene; the 45 % demo ramp cap (`endAlpha = 0.45`) is also saved.

## Step 2: camera matrix
Configs are set through the serialized `orthographicSize` and `offset` fields of the art-test scene's own `IsoCameraFollow`: A offset (12, 15.28, -12) = pitch 41.999 deg, size 8; B (12, 18, -12) = 46.686 deg, size 9; C same pitch, size 11. Applied at runtime per run and **not saved** (the saved scene is still B). `IsoCameraFollow.cs` untouched.
**Focus OFF** = pure player follow (`IsoCameraFollow.Target = Player`, `ArtTestCameraFocus` disabled). **Focus ON** = `ArtTestCameraFocus`, bias (-1, 1), enemy pull 0.35 (max 3 m).
Input: real keyboard events through the Input System (WASD, Space, Enter) into the unmodified gameplay scripts; player health raised so sequences complete. Capped = `targetFrameRate 60`; uncapped = `-1`, vsync 0 (reached about 130-366 fps).
Reference frame for every metric: 1920x1080 with the camera aspect forced to 16:9. The Game view window was not a fixed size (1689x1027 at the end); captures are rendered offscreen at 1920x1080.
Margin = smallest distance from 180 points on the projected 10 m ground circle to the frame edge, per frame (negative = clipped). Two circles: **around the player** (the protocol's measure) and the **fixed 10 m clear zone at the arena centre**. Saved frames have both drawn (red = around player, blue = fixed).
**"Visible" means inside the camera frame, not unobstructed by the HUD.** My frames are camera renders without the HUD overlay. QA's figure for the top-left HUD (about 38 % x 43 % of the frame) was not re-measured by me; anything under the HUD counts as visible here.

### Summary by config (all sequences, capped and uncapped)
| Config | Focus | Worst margin, ring around player (px) | Sequences with a negative margin | Worst margin, fixed zone at centre (px) | Frames with player/enemy outside frame | Telegraph frames fully in frame |
|---|---|---|---|---|---|---|
{NL.join(summ)}

### Full table (config x sequence)
{tbl}

Notes: `edge_up/edge_down` put the player 10 m from the arena centre up-/down-screen. The enemy counts as "in frame" only within 10 m of the player. `far_chase_*`: enemy starts 9 m away and stays inactive for the first 1.8 s while the player chases, then attacks. The fixed-zone circle cannot stay fully in frame when the player is near the arena edge in any config, so negative values there are expected. The dodge sequence found a telegraph in every run. Min fps in the CSVs includes capture hitches (screenshot and measurement frames).

### Character height measured directly from the captures
Method: render each frame twice (player shadow-only vs normal) and diff, giving the silhouette head-top to feet in pixels (it includes the foot-plane depth of the body). Real size from mesh bounds at the idle pose: {heights}. The Director's correction holds: projected height is about height x cos(pitch); my earlier "~98 px at size 11" was an estimate and is superseded. "Standing" excludes the two dash sequences.
| Config | Frames measured | Median standing height | Range (standing) | Lowest frame |
|---|---|---|---|---|
{NL.join(cl)}

Low outliers occur in the low dash pose (example: `shots/B_plain_cap60_dash_rest_S(down).png`).

### Telegraph visibility (in-engine luma lift, same pixels with vs without the telegraph)
Rec.709 luma on the final tonemapped frame, over pixels that changed, fixed pose. This is photometry on a held pose, **not combat validation**. `fill+area` = fill plus the faint 10 % area tint as shown; `edge+front` = outline plus front arc. Mean over lifted pixels; p10 = weakest pixels.
| Surface | Fill alpha | Part | Mean lift | p10 lift | Max lift |
|---|---|---|---|---|---|
{NL.join(ll)}
Lit floor = arena centre. Shadowed floor = nearest point to the centre where five sample points are all in shadow under the new key (the wall-shadow band). Images: `data/luma_*_with_45.png` / `_without_45.png`.

## Performance (Editor only)
Conditions: Editor Play Mode, Metal, Apple M5, **every row rendered to the same 1920x1080 render target**, uncapped, vsync 0, 60 warm-up frames then 300 sampled frames, same held pose (player at spawn, enemy 2 m away, windup 30 %, AI frozen), two repeats per row, rows interleaved (A8 measured last). "after" = current state (new key, post-processing, 2 actor point lights, probes). "before" = same ortho size with post-processing off, actor lights off and the old front-lit key (46, 318, 0). Raw samples: `data/perf/perf_*.csv`.
| Row | Frame ms median | Frame ms p95 | CPU main ms | Draw calls | SetPass | Triangles (M) | Shadow casters |
|---|---|---|---|---|---|---|---|
{NL.join(perf)}
Reading: before vs after at the same size shows almost no median frame-time change in this Editor test (size 9: 4.57-4.72 vs 4.59-4.62 ms), but +17 SetPass calls and +0.8 M triangles at size 9 (+0.35 M at size 11). GPU time was **not available** (FrameTimingManager reported 0), so GPU cost is UNVERIFIED. Size 8 read slower than size 9 despite fewer draws; it was measured last, so order/thermal drift or a pitch effect cannot be separated (UNVERIFIED).

## State
- Editor was **not in Play Mode** when this was written; scene saved, not dirty, key (38, 45, 0), ramp cap 0.45, camera size 9 (B).
- Tracked changes: only the three Unity-generated files already known plus `Art/README.md`. `ProjectSettings/ProjectSettings.asset` mtime 22:18:22, content identical to HEAD (from my earlier revert). Nothing under `Assets/Scripts`, shared URP assets or the other scenes was touched.

## UNVERIFIED / not done
- GPU frame time; any player build; sustained long-run frame time.
- Colour-vision-deficiency renders (luma lift above is the greyscale measure); telegraph lift on only two surfaces (lit and shadowed floor).
- Pass thresholds (+0.10 fill, +0.25 edge) are the CD's to apply: means clear +0.10, the weakest 10 % of pixels do not.
- HUD obstruction of the ring and telegraph (HUD not in the camera captures).
- Camera lag not isolated numerically (`max_player_offset_px` is in the CSVs).
- Whether the low dash pose is intended.
'''
open('GATE1_REPORT.md','w').write(rep)
names=['A_plain_cap60_edge_up_telegraph_mid','B_plain_cap60_edge_up_telegraph_mid','C_plain_cap60_edge_up_telegraph_mid','A_focusON_cap60_edge_up_telegraph_mid']
ims=[Image.open(D+'shots/'+n+'.png').convert('RGB').resize((960,540)) for n in names]
s=Image.new('RGB',(1920,1080))
for i,im in enumerate(ims): s.paste(im,((i%2)*960,(i//2)*540))
s.save('GATE1_edge_telegraph_sheet.png')
print(NL.join(summ)); print(NL.join(cl))

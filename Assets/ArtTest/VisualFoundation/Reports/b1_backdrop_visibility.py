#!/usr/bin/env python3
"""Share of each backdrop mass's vertices inside the Game-view frame (ignoring occlusion), over a 7x7 grid of player positions (-18..18 m, step 6),
for gameplay camera B (size 9, offset (12,18,-12)) and A2 (size 8.5, offset (12,15.28,-12)), as a function of the gap beyond the tall bays (5 m = the placement table).
Masses are moved outward by (gap-5): A, B toward +z, C toward -x. Vertices: b1_backdrop_world_vertices_gap5.json (exported from the Unity scene)."""
import json, math, sys
V = json.load(open(__file__.replace('b1_backdrop_visibility.py', 'b1_backdrop_world_vertices_gap5.json')))
def look(off):
    l = [-off[0], -off[1], -off[2]]; n = math.sqrt(sum(c*c for c in l)); l = [c/n for c in l]
    up0 = [0, 1, 0]; r = [l[1]*up0[2]-l[2]*up0[1], l[2]*up0[0]-l[0]*up0[2], l[0]*up0[1]-l[1]*up0[0]]; rn = math.sqrt(sum(c*c for c in r)); r = [c/rn for c in r]
    u = [r[1]*l[2]-r[2]*l[1], r[2]*l[0]-r[0]*l[2], r[0]*l[1]-r[1]*l[0]]; return l, r, u
def frac(verts, shift, camcfg, positions):
    size, off = camcfg; l, r, u = look(off); asp = 16/9; out = []
    for P in positions:
        cam = [P[0]+off[0], off[1], P[1]+off[2]]; c = 0
        for v in verts:
            w = [v[0]+shift[0]-cam[0], v[1]-cam[1], v[2]+shift[1]-cam[2]]
            x = sum(a*b for a, b in zip(w, r))/(size*asp)*0.5+0.5; y = sum(a*b for a, b in zip(w, u))/size*0.5+0.5
            if 0 <= x <= 1 and 0 <= y <= 1: c += 1
        out.append(100.0*c/len(verts))
    return out
pos = [(x, z) for x in range(-18, 19, 6) for z in range(-18, 19, 6)]
cams = {'B': (9.0, (12, 18, -12)), 'A2': (8.5, (12, 15.28, -12))}
print('camera,mass,gap_m,mean_pct,max_pct,positions_with_any_vertex_in_frame')
rows = []
for cn, cc in cams.items():
    for name, verts in V.items():
        west = 'Mass_C' in name; short = name.split('Backdrop_')[1].split('_recommended')[0]
        for gap in (5, 8, 12, 16, 20):
            sh = (-(gap-5), 0) if west else (0, gap-5); f = frac(verts, sh, cc, pos)
            rows.append((cn, short, gap, sum(f)/len(f), max(f), sum(1 for x in f if x > 0)))
            print(f'{cn},{short},{gap},{sum(f)/len(f):.2f},{max(f):.2f},{sum(1 for x in f if x > 0)}/49')

"""Batch-1 placement table (pure python). Reads the Unity-side placement JSON (read-only) and writes handoff/Batch1_Placement.{json,csv}.
Same row format as Stage 7 (instance, group, mesh, part, unity_x, unity_y, unity_z, yaw_front_to_plusZ, yaw_front_to_minusZ, scale) + a 'role' string.
Authoring map: Blender (x, y, z) = Unity (x, z, y_up); Unity yaw (clockwise from above, 0 = +Z) = -rotation_z(Blender).  Local FRONT = Blender +Y.
Wall bays: front (+Y) points OUTWARD, the niche face is -Y = toward the arena (same as Wall_A/B).
Run: python3 scripts/30_placements.py
"""
import json, math, csv, os

ROOT = '/Users/landerstudio/MythicRoguelite'
G = ROOT + '/Art/Blender/Revisions/batch1'
SRC = ROOT + '/Assets/ArtTest/Environment/TempleCourtyard_Placement.json'
d = json.load(open(SRC))
inst = d['instances']
ex = [i for i in inst if not i['part'].startswith(('ENV_Temple_Floor_', 'ENV_Temple_FloorBorder'))]

# measured: existing parapet (Wall_A/B) outer face at +0.573 from the wall axis (Wall_A top course max y 0.573, Wall_B 0.571), height 3.00 m
PARAPET_OUT = 0.573
CLEAR = 0.12                    # air gap between the parapet's outer face and the bay's front-most surface (pier fronts)
BAY_FRONT = 0.632               # measured: bay local min y (arena-facing front-most surface incl. sculpt displacement), Wall_Tall_A/B bbox
OFFSET = round(20.0 + PARAPET_OUT + CLEAR + BAY_FRONT, 2)      # origin offset from the wall axis -> 21.33

rows, notes = [], []


def row(group, part, mesh, x, z, rot_z_deg, name, role, y=0.0):
    yaw = (-rot_z_deg) % 360.0
    rows.append(dict(instance=name, group=group, mesh=mesh, part='ENV_Temple_' + part, unity_x=round(x, 3), unity_y=round(y, 3), unity_z=round(z, 3),
                     yaw_front_to_plusZ=round(yaw, 2), yaw_front_to_minusZ=round((yaw + 180.0) % 360.0, 2), scale=1.0, role=role))


# ---------------------------------------------------------------- 1. Wall_Tall bays (north z=+20 and west x=-20, behind the parapet)
walls = [i for i in inst if i['part'].startswith('ENV_Temple_Wall_')]
north = sorted(i['unity_x'] for i in walls if abs(i['unity_z'] - 20.0) < 0.01)
west = sorted(i['unity_z'] for i in walls if abs(i['unity_x'] + 20.0) < 0.01)
ARCH = next(i for i in inst if i['part'] == 'ENV_Temple_Arch_A_Span')
ax = ARCH['unity_x']
# existing north parapet bays: every 4 m except the arch gap (x = 2, 6): keep the same gap (8 m around the arch at x=4)
north_all = [x for x in north if abs(x - ax) > 6.5]      # BVH test (evidence/31) showed the bays at x=-2 and x=10 intersect the arch piers: dropped (arch-adjacent bays omitted)
pat_n = ['A', 'B', 'A', 'A', 'B', 'B', 'A', 'B', 'A', 'B']                    # explicit variant pattern (no three equal neighbours)
pat_w = ['B', 'A', 'A', 'B', 'A', 'B', 'A', 'A', 'B', 'A']
k = 0
for x in [-22.0] + north_all:                                                    # -22: corner bay closing the NW corner (see notes)
    v = pat_n[k % len(pat_n)]; k += 1
    row('BATCH1_Walls', 'Wall_Tall_' + v, 'ENV_Temple_Wall_Tall_' + v, x, OFFSET, 0.0, f'B1_WallTall_{v}_N{int(round(x)):+03d}',
        'north tall bay' + (' (corner)' if x == -22.0 else ''))
k = 0
for z in west:
    v = pat_w[k % len(pat_w)]; k += 1
    row('BATCH1_Walls', 'Wall_Tall_' + v, 'ENV_Temple_Wall_Tall_' + v, -OFFSET, z, 90.0, f'B1_WallTall_{v}_W{int(round(z)):+03d}', 'west tall bay')
notes.append(f'Wall bay origin offset from the wall axis = {OFFSET} m = 20.0 + parapet outer face {PARAPET_OUT} + air gap {CLEAR} + bay front {BAY_FRONT} (all measured). '
             'North bays at z=+{0}, west bays at x=-{0}; the corner bay (x=-22, north orientation) closes the NW corner; a ~0.7 m slit remains between it and the last west bay (z=18..20).'.format(OFFSET))
notes.append('Arch gap: north bays omitted at x = -2, 2, 6, 10 (parapet gap x=2,6 plus the two arch-adjacent bays at x=-2 and x=10, which the BVH surface-intersection test showed intersect the arch piers). Clear gap in the north tall-bay row: x=-4..12 (16 m), arch itself x about -0.25..8.25. If Nishant/GD meant 8 m EACH side, also drop x=-6 and x=14.')

# ---------------------------------------------------------------- 2. clearance helpers for pylons / ruins (2D footprints; the BVH check in Blender is the authority)
RAD = {'Pillar_A': 1.05, 'Pillar_B': 1.05, 'Pillar_C': 1.3, 'Pillar_D': 1.05, 'Altar_A': 2.7, 'Stairs_A': 2.15, 'Platform_A': 3.2, 'Brazier_A': 0.6, 'ColumnDrum_A': 0.9,
       'Rubble_A': 1.0, 'Rubble_B': 1.0, 'Banner_A': 0.0, 'Arch_A_PierL': 0.0, 'Arch_A_PierR': 0.0, 'Arch_A_Span': 0.0, 'Wall_A': 0.0, 'Wall_B': 0.0}
exist = [(i['part'].replace('ENV_Temple_', ''), i['unity_x'], i['unity_z']) for i in ex]
exist_pts = [(n, x, z, RAD.get(n, 1.0)) for n, x, z in exist if RAD.get(n, 1.0) > 0]


def clear_of(x, z, r, margin, others=(), other_margin=None):
    for n, ex_, ez_, er in exist_pts:
        if math.hypot(x - ex_, z - ez_) < r + er + margin:
            return False, n, math.hypot(x - ex_, z - ez_)
    for ox, oz, orr in others:
        if math.hypot(x - ox, z - oz) < r + orr + (margin if other_margin is None else other_margin):
            return False, 'new', math.hypot(x - ox, z - oz)
    # arch approach lane (opening x 1.9..6.1, z 10..20) must stay free
    if 1.9 - r - 0.6 < x < 6.1 + r + 0.6 and z > 10.0:
        return False, 'arch lane', 0
    return True, None, None


placed = []
# ---------------------------------------------------------------- 3. pylons (6): stairs flank pair, arch flank pair, west-wall pair
st = next(i for i in ex if i['part'] == 'ENV_Temple_Stairs_A')
sx, sz = st['unity_x'], st['unity_z']
axis = (-0.7071, 0.7071)                 # from the arena towards the altar
perp = (0.7071, 0.7071)
foot = (sx - axis[0] * 1.0, sz - axis[1] * 1.0)
pyl = []
for sgn, nm in ((+1, 'stairs flank (south-east side)'), (-1, 'stairs flank (north-west side)')):
    pyl.append((foot[0] + sgn * perp[0] * 3.4, foot[1] + sgn * perp[1] * 3.4, nm))
pyl += [(-3.4, 18.2, 'arch flank, outside the existing arch braziers (west)'), (11.4, 18.2, 'arch flank, outside the existing arch braziers (east)')]
pyl += [(-17.7, -9.0, 'west wall pair (south)'), (-17.7, 0.6, 'west wall pair (north)')]
PR = 0.55
for n, (x, z, why) in enumerate(pyl, 1):
    ok, who, dist = clear_of(x, z, PR, 0.9, [(p[0], p[1], PR) for p in placed])
    r = math.hypot(x, z)
    assert r >= 12.8, (x, z, r)
    row('BATCH1_Pylons', 'Lantern_Pylon_A', 'ENV_Temple_Lantern_Pylon_A', x, z, 0.0, f'B1_Pylon_{n}', why)
    rows[-1]['_check'] = dict(r_from_centre=round(r, 2), clear=bool(ok), blocker=who, blocker_dist=(round(dist, 2) if dist else None))
    placed.append((x, z, PR))

# ---------------------------------------------------------------- 4. ruin clusters (3): r 15-19, west / south-west, deterministic search (clearance vs everything incl. pylons)
RR = 2.4                                   # effective footprint radius about its pivot (measured bbox x -1.9..3.3, y -3.0..1.9; mass is sparse, tall pillar is near the pivot side)
cand = []
for ix in range(-19 * 4, -9 * 4):
    for iz in range(-19 * 4, 6 * 4):
        x, z = ix / 4.0, iz / 4.0
        r = math.hypot(x, z)
        if 15.0 <= r <= 19.0 and -17.0 <= x < -6.0 and -16.5 <= z < 9.0:      # keeps the cluster (x -1.9..3.3, y -3.0..1.9 about its pivot) clear of the parapet inner face
            cand.append((x, z))
chosen = []
targets = [('Ruin_Cluster_A', 0.0, 'west'), ('Ruin_Cluster_B', 20.0, 'south-west'), ('Ruin_Cluster_A', -25.0, 'west-south-west')]
want_dir = [(-0.99, 0.10), (-0.55, -0.83), (-0.85, -0.52)]                  # rough bearings (west / south-west / between)
for (part, rot, nm), wd in zip(targets, want_dir):
    best = None
    for (x, z) in cand:
        ok, who, dist = clear_of(x, z, RR, 0.3, [(p[0], p[1], PR) for p in placed] + [(c[0], c[1], RR) for c in chosen], other_margin=1.0)
        if not ok:
            continue
        r = math.hypot(x, z); cos = (x * wd[0] + z * wd[1]) / r
        sc = cos - 0.01 * abs(r - 17.0)
        if best is None or sc > best[0]:
            best = (sc, x, z)
    assert best, 'no clear spot'
    chosen.append((best[1], best[2], RR))
    n = len(chosen)
    row('BATCH1_Ruins', part, 'ENV_Temple_' + part, best[1], best[2], rot, f'B1_Ruin_{n}', f'{nm}; tall end toward -x,+z (away from the gameplay camera)')
    rows[-1]['_check'] = dict(r_from_centre=round(math.hypot(best[1], best[2]), 2), clear=True)

# ---------------------------------------------------------------- 5. backdrop masses
# built with local -Y facing the arena (like the walls): north rot 0, west rot 90. bbox (measured, evidence/20_geometry_stats.json) local y: A -9.0..9.5, B -9.06..6.3, C -7.0..6.3
TALL_OUT = 20.0 + PARAPET_OUT + CLEAR + 2 * BAY_FRONT      # outer face of the tall bays' pier backs is ~ OFFSET + 0.63
OUTER = round(OFFSET + 0.64, 2)                            # tall-bay back face distance from the wall axis (21.97)
MASS = {'Backdrop_Mass_A': dict(front=9.0, xc=-2.7), 'Backdrop_Mass_B': dict(front=9.06, xc=-0.9), 'Backdrop_Mass_C': dict(front=7.0, xc=3.5)}
# (part, side, along-wall position of the mass's local origin, nearest-face distance beyond the tall-bay back face)
DIRECTIVE = [('Backdrop_Mass_A', 'N', -12.0, 28.0), ('Backdrop_Mass_B', 'N', 18.0, 40.0), ('Backdrop_Mass_C', 'W', -8.0, 34.0)]
RECOMMENDED = [('Backdrop_Mass_A', 'N', -12.0, 5.0), ('Backdrop_Mass_B', 'N', 18.0, 5.0), ('Backdrop_Mass_C', 'W', -8.0, 5.0)]
for tag, lst in (('directive_28_55m', DIRECTIVE), ('recommended_visible_band', RECOMMENDED)):
    for part, side, along, gap in lst:
        fr = MASS[part]['front']
        dist = OUTER + gap + fr                           # origin distance from the wall axis
        if side == 'N':
            row('BATCH1_Backdrop_' + tag, part, 'ENV_Temple_' + part, along, dist, 0.0, f'B1_{part}_{tag}', f'{tag}: nearest face {gap:g} m beyond the tall bays (north)')
        else:
            row('BATCH1_Backdrop_' + tag, part, 'ENV_Temple_' + part, -dist, along, 90.0, f'B1_{part}_{tag}', f'{tag}: nearest face {gap:g} m beyond the tall bays (west)')
        rows[-1]['_check'] = dict(nearest_face_beyond_tall_bay_m=gap)

# ---------------------------------------------------------------- write
out_rows = [{k: v for k, v in r_.items() if k != '_check'} for r_ in rows]
checks = {r_['instance']: r_['_check'] for r_ in rows if '_check' in r_}
meta = dict(coordinate_note=open(__file__).read().split('"""')[1].strip(), count=len(out_rows),
            arena=dict(floor_half_extent_m=20.0, wall_inner_face_m=19.5, clear_zone_radius_m=10.0, parapet_outer_face_from_axis_m=PARAPET_OUT, parapet_height_m=3.0),
            wall_bay_origin_offset_m=OFFSET, notes=notes, planning_checks=checks, source_of_existing_layout=os.path.relpath(SRC, ROOT), instances=out_rows)
os.makedirs(G + '/handoff', exist_ok=True)
json.dump(meta, open(G + '/handoff/Batch1_Placement.json', 'w'), indent=1)
with open(G + '/handoff/Batch1_Placement.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys())); w.writeheader(); w.writerows(out_rows)
print('PLACEMENT_DONE', len(out_rows), 'rows; wall offset', OFFSET)
for r_ in rows:
    if not r_['group'].startswith('BATCH1_Walls'):
        print(r_['instance'], r_['part'].replace('ENV_Temple_', ''), r_['unity_x'], r_['unity_z'], r_['yaw_front_to_plusZ'], r_.get('_check'))
print('wall rows', sum(1 for r_ in rows if r_['group'] == 'BATCH1_Walls'))

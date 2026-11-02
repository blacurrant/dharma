"""Batch-1 placement validation on the WORKING COPY (read-only; nothing saved).
  Blender -b --factory-startup --python scripts/31_overlap_visibility.py
 1. BVH triangle-intersection tests: every placed instance vs every existing non-floor piece, and new vs new (wall bays vs each other skipped: they abut by design)
 2. wall-bay clearance: bay front-most surface vs the parapet outer face (from vertices); bay vs arch nearest distance (BVH find_nearest)
 3. screen visibility of the backdrop masses through the real gameplay camera (ortho 9, offset 12,18,-12) for a grid of player positions
Outputs evidence/31_overlap_visibility.json
"""
import sys, os, json, math
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/batch1'
bpy.ops.wm.open_mainfile(filepath=G + '/TempleEnvironmentKit_batch1.blend')
sc = bpy.context.scene
O = bpy.data.objects
P = json.load(open(G + '/handoff/Batch1_Placement.json'))['instances']
out = {}

# ---- instantiate new parts (temporary, in memory)
new = []
for r in P:
    src = O.get(r['part'])
    if src is None:
        continue
    o = bpy.data.objects.new(r['instance'], src.data)
    o.location = (r['unity_x'], r['unity_z'], r['unity_y']); o.rotation_euler = (0, 0, math.radians(-r['yaw_front_to_plusZ']))
    sc.collection.objects.link(o); new.append((r, o))
bpy.context.view_layer.update()
dg = bpy.context.evaluated_depsgraph_get()


def world_verts(o):
    me = o.data
    co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    m = np.array(o.matrix_world)
    return (co @ m[:3, :3].T) + m[:3, 3]


def tree(o):
    """BVH in WORLD space (BVHTree.FromObject is object-local, which is wrong for transformed instances)."""
    ev = o.evaluated_get(dg); me = ev.to_mesh()
    me.calc_loop_triangles()
    m = o.matrix_world
    verts = [m @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, tris, epsilon=0.0)


existing = [o for o in O if o.name.startswith('LAY_') and o.type == 'MESH' and o.users_collection and o.users_collection[0].name not in ('LAY_Floor', 'LAY_Proxies_TestOnly', 'LAY_Cameras_Lights')]
ex_trees = {o.name: tree(o) for o in existing}
new_trees = {r['instance']: tree(o) for r, o in new if not r['group'].startswith('BATCH1_Backdrop')}
# ---- 1. intersections
hits = []
for r, o in new:
    if r['group'].startswith('BATCH1_Backdrop'):
        continue
    t = new_trees[r['instance']]
    for en, et in ex_trees.items():
        ov = t.overlap(et)
        if ov:
            hits.append(dict(new=r['instance'], existing=en, intersecting_triangle_pairs=len(ov)))
    for r2, o2 in new:
        if r2['instance'] <= r['instance'] or r2['group'].startswith('BATCH1_Backdrop'):
            continue
        if r['group'] == 'BATCH1_Walls' and r2['group'] == 'BATCH1_Walls':
            continue
        ov = t.overlap(new_trees[r2['instance']])
        if ov:
            hits.append(dict(new=r['instance'], new_other=r2['instance'], intersecting_triangle_pairs=len(ov)))
out['intersections'] = dict(tested_new=len(new_trees), existing_non_floor=len(ex_trees), intersecting_pairs=hits,
                            note='surface-intersection test only (a mesh fully inside another would not be detected); wall bays are not tested against each other (they abut at the 4 m joint by design)')
print('INTERSECT', len(hits), hits[:20], flush=True)

# ---- 1b. measured minimum distance new instance -> every existing non-floor piece (sampled vertices of the new mesh vs BVH of each existing piece)
mind = []
for r, o in new:
    if r['group'].startswith('BATCH1_Backdrop') or r['group'] == 'BATCH1_Walls':
        continue
    wv = world_verts(o)
    pts = wv[:: max(1, len(wv) // 700)]
    best = (1e9, None)
    for en, et in ex_trees.items():
        for p_ in pts:
            hit = et.find_nearest(Vector(p_.tolist()))
            if hit and hit[3] is not None and hit[3] < best[0]:
                best = (hit[3], en)
    mind.append(dict(instance=r['instance'], nearest_existing=best[1], distance_m=round(best[0], 3)))
out['min_distance_to_existing_pieces'] = mind
print('MIND', mind, flush=True)

# ---- 2. wall-bay clearance to the parapet and to the arch
par = [o for o in existing if o.name.startswith('LAY_Wall_')]
arch = [o for o in existing if 'Arch_A' in o.name]
arch_trees = [(o.name, tree(o)) for o in arch]
clr = []
for r, o in new:
    if r['group'] != 'BATCH1_Walls':
        continue
    wv = world_verts(o)
    north = abs(r['unity_z']) > abs(r['unity_x'])
    if north:
        front = float(wv[:, 1].min())                      # arena-facing front-most surface (north bays: smallest y)
        near = [p for p in par if abs(p.location.y - 20.0) < 0.1 and abs(p.location.x - r['unity_x']) < 2.5]
        pout = max(float(world_verts(p)[:, 1].max()) for p in near) if near else None
        gap = (front - pout) if pout is not None else None
    else:
        front = float(wv[:, 0].max())                      # west bays: largest x faces the arena
        near = [p for p in par if abs(p.location.x + 20.0) < 0.1 and abs(p.location.y - r['unity_z']) < 2.5]
        pout = min(float(world_verts(p)[:, 0].min()) for p in near) if near else None
        gap = (pout - front) if pout is not None else None
    d = dict(instance=r['instance'], part=r['part'].replace('ENV_Temple_', ''), bay_front_surface=round(front, 3), parapet_outer_face=(round(pout, 3) if pout is not None else None), gap_m=(round(gap, 3) if gap is not None else None))
    # nearest distance to the arch (sampled over the bay's vertices within 6 m of the arch centre)
    ax = 4.0
    if north and abs(r['unity_x'] - ax) < 9.0:
        sel_ = wv[(np.abs(wv[:, 0] - ax) < 7.0)]
        dm = 1e9
        for nm, t in arch_trees:
            for p in sel_[:: max(1, len(sel_) // 1500)]:
                hit = t.find_nearest(Vector(p.tolist()))
                if hit and hit[3] is not None:
                    dm = min(dm, hit[3])
        d['nearest_distance_to_arch_m'] = round(dm, 3)
    clr.append(d)
out['wall_clearance'] = clr
print('CLEAR', [c['gap_m'] for c in clr][:8], [c for c in clr if 'nearest_distance_to_arch_m' in c], flush=True)

# ---- 3. backdrop visibility through the real gameplay camera
OFFS = Vector((12.0, -12.0, 18.0)); look = (-OFFS).normalized()
rot = look.to_track_quat('-Z', 'Y').to_matrix()           # camera basis columns: X right, Y up, Z back
R = np.array(rot)
asp = 1080.0 / 1920.0
ortho = 32.0                                              # ortho size 9 -> vertical 18 m -> horizontal 32 m at 16:9


def screen(pts, target):
    c = pts - np.array(target)[None, :]
    x = c @ R[:, 0]; y = c @ R[:, 1]
    return x / ortho + 0.5, y / (ortho * asp) + 0.5


vis = {}
grid = [(x, z) for x in range(-19, 20, 2) for z in range(-19, 20, 2)]
for r, o in new:
    if not r['group'].startswith('BATCH1_Backdrop') and r['group'] != 'BATCH1_Walls':
        continue
    wv = world_verts(o)
    # also sample points on the surface (triangle centroids) to be area-aware
    best = dict(max_visible_vertex_fraction=0.0, at_player=None, max_visible_height_m=0.0, min_visible_height_m=None)
    for (px, pz) in grid:
        sx, sy = screen(wv, (px, pz, 0.0))
        m = (sx >= 0) & (sx <= 1) & (sy >= 0) & (sy <= 1)
        f = float(m.mean())
        if f > best['max_visible_vertex_fraction']:
            best.update(max_visible_vertex_fraction=round(f, 4), at_player=(px, pz), max_visible_height_m=round(float(wv[m, 2].max()), 2) if m.any() else 0.0,
                        min_visible_height_m=round(float(wv[m, 2].min()), 2) if m.any() else None)
    vis[r['instance']] = best
out['screen_visibility_through_gameplay_camera_ortho9'] = dict(player_grid='x,z in -19..19 step 2 (arena)', per_instance=vis)
# farthest ground distance beyond the north wall (z=+20) that can ever be on screen: player at the wall, same x
best = 0.0
for pz in np.arange(10.0, 19.6, 0.25):
    zs = np.arange(19.5, 80.0, 0.25)
    pts = np.stack([np.full_like(zs, -5.0), zs, np.zeros_like(zs)], 1)
    sx, sy = screen(pts, (-5.0, pz, 0.0))
    m = (sx >= 0) & (sx <= 1) & (sy >= 0) & (sy <= 1)
    if m.any():
        best = max(best, float(zs[m].max()))
out['screen_visibility_through_gameplay_camera_ortho9']['farthest_ground_z_ever_on_screen_north_of_wall_player_x_minus5'] = round(best, 2)
out['screen_visibility_through_gameplay_camera_ortho9']['farthest_distance_beyond_wall_axis_m'] = round(best - 20.0, 2)
print('VIS', json.dumps(out['screen_visibility_through_gameplay_camera_ortho9'])[:1500], flush=True)
# ---- gap sweep: how much of each backdrop mass can ever be on screen as a function of its nearest-face distance beyond the tall bays
OUTER = 21.97
sweep = {}
for ortho_size, ortho in ((9, 32.0), (11, 39.11)):
    for part, side in (('ENV_Temple_Backdrop_Mass_A', 'N'), ('ENV_Temple_Backdrop_Mass_B', 'N'), ('ENV_Temple_Backdrop_Mass_C', 'W')):
        me = O[part]; _c = np.empty(len(me.data.vertices) * 3, np.float32); me.data.vertices.foreach_get('co', _c); co = _c.reshape(-1, 3)   # LOCAL coords (builder frame): arena side is -Y
        front = float(-co[:, 1].min())
        res = {}
        for gap in (4, 8, 12, 16, 20, 28, 40, 55):
            dist = OUTER + gap + front
            if side == 'N':
                pts = np.stack([co[:, 0] + 0.0, co[:, 1] + dist, co[:, 2]], 1)
            else:
                pts = np.stack([-(co[:, 1] + dist), co[:, 0] - 8.0, co[:, 2]], 1)
            best_f, best_p = 0.0, None
            for (px, pz) in grid:
                c = pts - np.array([px, pz, 0.0])[None, :]
                sx = c @ R[:, 0] / ortho + 0.5; sy = c @ R[:, 1] / (ortho * asp) + 0.5
                f = float(((sx >= 0) & (sx <= 1) & (sy >= 0) & (sy <= 1)).mean())
                if f > best_f:
                    best_f, best_p = f, (px, pz)
            res[str(gap)] = dict(max_vertex_fraction_on_screen=round(best_f, 3), at_player=best_p)
        sweep[f'{part.replace("ENV_Temple_", "")}@ortho{ortho_size}'] = res
out['backdrop_visibility_gap_sweep'] = dict(note='nearest-face gap beyond the tall-bay back face; mass built with local -Y facing the arena; any vertex on screen for the best player position on the 2 m grid. A vertex fraction is not a visible-area fraction.', sweep=sweep)
print('SWEEP', json.dumps(sweep)[:2500])
json.dump(out, open(G + '/evidence/31_overlap_visibility.json', 'w'), indent=1)
print('VALIDATE_DONE')

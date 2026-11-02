"""Prop placement proposals (EXISTING kit parts only) + validation against the real layout. Pure python (no bpy). Unity convention: x/z metres, yaw clockwise from above, 0 = +Z (placement-table convention yaw_front_to_plusZ)."""
import json, math
ROOT = '/Users/landerstudio/MythicRoguelite'
VF = ROOT + '/Art/Blender/Revisions/vf_handoff'
d = json.load(open(ROOT + '/Art/Exports/Environment/Staging/TempleCourtyard_Placement.json'))
ex = [i for i in d['instances'] if not i['part'].startswith(('ENV_Temple_Floor', 'ENV_Temple_FloorBorder'))]
altar = next(i for i in ex if i['part'] == 'ENV_Temple_Altar_A'); ax, az = altar['unity_x'], altar['unity_z']
ar = math.hypot(ax, az); ux, uz = ax / ar, az / ar          # focal axis: origin -> altar
def lat(x, z): return (x * uz - z * ux) * -1.0              # signed lateral offset from the focal axis (m)
def along(x, z): return x * ux + z * uz
P = [
 ('Brazier_A', 'approach brazier L', -6.86, 10.82, 0, 'Lit pair 3 m before the stairs frames the approach to the altar and pulls the eye along the axis. Warm light only, stays outside the clear circle.'),
 ('Brazier_A', 'approach brazier R', -10.82, 6.86, 0, 'Pair partner (5.6 m gap). Symmetry here is deliberate: it is the formal entrance to the focal zone; everything else stays asymmetric.'),
 ('Banner_A', 'banner W wall by dais', -19.40, 11.00, 90, 'Crimson (the only crimson in the kit) concentrated at the focal corner = colour hierarchy. Wall-mounted: no collision, no combat footprint.'),
 ('Banner_A', 'banner N wall by dais', -11.00, 19.40, 180, 'Second banner flanks the dais from the other wall; same yaw convention as the existing wall banners.'),
 ('ColumnDrum_A', 'fallen drum, flank', -12.00, 5.50, 70, 'Low ruin silhouette on the flank; its diagonal leads toward the altar without blocking the sight line (1.1 m tall, measured).'),
 ('Rubble_A', 'rubble, approach flank', -5.50, 12.20, 40, 'Breaks the clean floor beside the approach; low and small, no collision problem.'),
 ('Rubble_B', 'rubble, far flank', -17.00, 3.00, 100, 'Pushes debris toward the wall edge, away from the combat circle and the approach lane.'),
 ('Rubble_B', 'rubble, east corner', 15.50, 16.50, 160, 'Weights the far (screen-top) corner so the frame is not empty away from the altar; outside any lane.'),
]
rows = []
for part, nm, x, z, yaw, why in P:
    others = [(i['part'], math.hypot(x - i['unity_x'], z - i['unity_z'])) for i in ex]
    near = min(others, key=lambda t: t[1])
    r = math.hypot(x, z); wall = 19.5 - max(abs(x), abs(z))
    rows.append(dict(part='ENV_Temple_' + part, label=nm, unity_x=x, unity_z=z, yaw_front_to_plusZ_deg=yaw, reason=why, radius_from_centre_m=round(r, 2),
                     lateral_from_focal_axis_m=round(lat(x, z), 2), along_axis_m=round(along(x, z), 2), nearest_existing=near[0].replace('ENV_Temple_', ''), nearest_existing_dist_m=round(near[1], 2),
                     clear_of_combat_circle_r10=bool(r > 10.0), gap_to_inner_wall_m=round(wall, 2),
                     checks=dict(r_ge_11=bool(r >= 11.0), nearest_ge_1_5=bool(near[1] >= 1.5) or part.startswith('Banner'), inside_walls=bool(max(abs(x), abs(z)) <= 19.5))))
out = dict(focal_axis=dict(from_=[0, 0], to=[ax, az], altar_radius_m=round(ar, 2), unit=[round(ux, 3), round(uz, 3)], note='Altar currently at the NW corner (r ~19.9 m); whether a central structure replaces/adds to it is Nishant\'s decision - this list does not assume it.'),
           camera_note='Gameplay camera sits toward +x,-z of the player and looks toward -x,+z, so the altar axis runs UP the screen. Tall pieces are kept off the +x/-z side; heights measured from the kit meshes: Brazier_A 1.34 m, ColumnDrum_A 1.10 m, Rubble_A 0.44 m, Rubble_B 0.30 m; only the wall-mounted Banner_A (2.52 m) is taller.',
           parts_used='existing kit parts only (Brazier_A, Banner_A, ColumnDrum_A, Rubble_A, Rubble_B); no new meshes', placements=rows)
json.dump(out, open(VF + '/VF_PROP_PLACEMENTS.json', 'w'), indent=1)
for r in rows:
    print('%-14s %-26s x %7.2f z %7.2f yaw %5s | r %5.2f lat %6.2f nearest %-18s %5.2f | wall gap %5.2f | %s' % (r['part'].replace('ENV_Temple_', ''), r['label'], r['unity_x'], r['unity_z'], r['yaw_front_to_plusZ_deg'], r['radius_from_centre_m'], r['lateral_from_focal_axis_m'], r['nearest_existing'], r['nearest_existing_dist_m'], r['gap_to_inner_wall_m'], r['checks']))

"""Stage 7: export the courtyard placement table for the Unity Engineer (read-only on the .blend).
Run: Blender -b --factory-startup --python Art/Blender/Scripts/07_export_placement.py
Output: Art/Exports/Environment/Staging/TempleCourtyard_Placement.json  (+ .csv)

Authoring map (used when composing in Blender):  Blender (x, y, z) = Unity (x, z, y_up).
Positions are therefore Unity (x, y_up, z) = (Bx, Bz, By).
Yaw (Unity, degrees clockwise from above, 0 = +Z) as authored = -rotation_z(Blender).
An asset's local FRONT is Blender +Y.  Where that lands in Unity depends on the FBX importer convention, which is
NOT yet verified in Unity, so two yaw columns are given:
  yaw_front_to_plusZ   : use if Unity shows the imported piece's front facing +Z at yaw 0   (authoring map above)
  yaw_front_to_minusZ  : use if the front faces -Z at yaw 0 (=yaw + 180)
Verification piece: ENV_Temple_Stairs_A (high end is local +Y) or ENV_Temple_Wall_B (relief panel is local -Y).
"""
import os, json, csv, math
import bpy

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
OUT = ROOT + '/Art/Exports/Environment/Staging/TempleCourtyard_Placement'
bpy.ops.wm.open_mainfile(filepath=BLEND)
rows = []
for o in bpy.data.objects:
    if not o.name.startswith('LAY_') or o.type != 'MESH':
        continue
    cname = o.users_collection[0].name
    if cname == 'LAY_Proxies_TestOnly':
        continue
    part = o.name[4:].rsplit('_', 1)[0]            # e.g. Floor_A, Arch_A_Span
    asset = o.data.name
    mw = o.matrix_world
    t = mw.to_translation(); e = mw.to_euler('XYZ')
    assert abs(e.x) < 1e-4 and abs(e.y) < 1e-4, (o.name, e)
    s = mw.to_scale()
    yaw = (-math.degrees(e.z)) % 360.0
    rows.append(dict(instance=o.name, group=cname, mesh=o['asset'] if 'asset' in o.keys() else None, part='ENV_Temple_' + part,
                     unity_x=round(t.x, 3), unity_y=round(t.z, 3), unity_z=round(t.y, 3),
                     yaw_front_to_plusZ=round(yaw, 2), yaw_front_to_minusZ=round((yaw + 180) % 360, 2),
                     scale=round(s.x, 3)))
rows.sort(key=lambda r: (r['group'], r['part'], r['instance']))
meta = dict(coordinate_note=__doc__.strip(), count=len(rows), arena=dict(floor_half_extent_m=20.0, wall_inner_face_m=19.5, clear_zone_radius_m=10.0),
            floor_tile_pivot='centre of bottom face; place at y=-0.30 so the top surface is at y=0',
            instances=rows)
json.dump(meta, open(OUT + '.json', 'w'), indent=1)
with open(OUT + '.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print('PLACEMENT_DONE', len(rows), 'instances')

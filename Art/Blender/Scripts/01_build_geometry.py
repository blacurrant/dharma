"""Stage 1: build kit geometry + UVs into TempleEnvironmentKit.blend (background Blender).
Run:  Blender -b --factory-startup --python Art/Blender/Scripts/01_build_geometry.py
Rebuilds ALL kit pieces from scratch (idempotent): existing ENV_Temple_* objects/meshes are replaced.
"""
import sys, os, json, time, math
HERE = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/Users/landerstudio/MythicRoguelite/Art/Blender/Scripts'
sys.path.insert(0, HERE)
import bpy
import kitlib as K
import assets as A

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
STATS = ROOT + '/Art/Blender/Scripts/_build/geometry_stats.json'
os.makedirs(os.path.dirname(STATS), exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
assert sc.name == 'TempleEnvironmentKit', sc.name

# clean previous kit objects (only ours)
for o in list(bpy.data.objects):
    if o.name.startswith('ENV_Temple_'):
        bpy.data.objects.remove(o, do_unlink=True)
for m in list(bpy.data.meshes):
    if m.users == 0:
        bpy.data.meshes.remove(m)

K.make_src_materials()
coll_kit = bpy.data.collections['10_Kit_Pieces']
coll_prop = bpy.data.collections['20_Props']
subs = {}


def sub(parent, name):
    key = parent.name + '/' + name
    if key not in subs:
        c = bpy.data.collections.get('Kit_' + name) or bpy.data.collections.new('Kit_' + name)
        if c.name not in [x.name for x in parent.children]:
            parent.children.link(c)
        subs[key] = c
    return subs[key]


stats = {}
t0 = time.time()
cursor = {}
ROW = {'Floor': 0, 'Stair': 1, 'Wall': 1, 'Pillar': 2, 'Arch': 3, 'Focal': 3, 'Prop': 4}
for cat, asset, parts, target, vm, wm, dm in A.REG:
    t = time.time()
    parent = coll_prop if cat == 'Prop' else coll_kit
    coll = sub(parent, cat)
    row = ROW[cat]
    x = cursor.get(row, -60.0)
    widest = 0.0
    objs = []
    for suffix, fn in parts:
        b = fn()
        name = 'ENV_Temple_' + asset + suffix
        obj = b.to_object(name, coll)
        obj['value_mult'] = vm; obj['wear_mult'] = wm; obj['damp_mult'] = dm
        # floors: low-contrast on purpose (Art Bible 3.2 rule 3: walkable floor is the quietest surface in the frame)
        obj['tone_var'] = 0.30 if cat == 'Floor' else 1.0
        obj['dirt_mult'] = 0.55 if cat == 'Floor' else 1.0
        obj['asset'] = 'ENV_Temple_' + asset; obj['category'] = cat
        a3, a2, nt = K.uv_stats(obj)
        res, dens = K.pick_res(a3, a2, target, cap=2048)
        obj['tex_res'] = res
        dims = obj.dimensions
        widest = max(widest, dims.x)
        # bbox in local coords (pivot audit)
        bb = [tuple(round(c, 3) for c in v) for v in (obj.bound_box[0], obj.bound_box[6])]
        stats[name] = dict(asset='ENV_Temple_' + asset, category=cat, tris=nt, area3d_m2=round(a3, 2), uv_fill=round(a2, 3),
                           tex_res=res, texel_density_px_per_m=round(dens, 1), target=target,
                           dims_m=[round(d, 3) for d in dims], bbox_min=bb[0], bbox_max=bb[1],
                           materials=[m.name for m in obj.data.materials])
        objs.append(obj)
        print(f"  {name:38s} tris={nt:7d} dims={tuple(round(d,2) for d in dims)} res={res} dens={dens:5.0f}px/m  ({time.time()-t:.1f}s)")
    for o in objs:
        o.location = (x + widest / 2, -60.0 - 22.0 * row, 0.0)
    cursor[row] = x + widest + 3.0

json.dump(stats, open(STATS, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('STAGE1_DONE', len(stats), 'parts', round(time.time() - t0, 1), 's; total tris', sum(s['tris'] for s in stats.values()))

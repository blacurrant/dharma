"""Stage 5: FBX export of each kit asset to Art/Exports/Environment/Staging/Models/.
Run: Blender -b --factory-startup --python Art/Blender/Scripts/05_export.py
 - one FBX per asset (arch = 3 mesh objects); pieces exported at the origin with their baked pivot
 - Z-up/-Y fwd (Blender) -> -Z fwd / Y up (FBX); apply FBX_SCALE_ALL + bake_space_transform so Unity gets scale 1, rotation 0
 - textures are referenced relatively (../Textures/); materials export as Principled->diffuse/normal links
Never overwrites an existing FBX unless --overwrite is passed.
"""
import sys, os, json
import bpy

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
STG = ROOT + '/Art/Exports/Environment/Staging/Models'
os.makedirs(STG, exist_ok=True)
OVER = '--overwrite' in sys.argv
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
kit = {o.name: o for o in bpy.data.objects if o.name.startswith('ENV_Temple_') and o.type == 'MESH'}
assets = {}
for n, o in kit.items():
    assets.setdefault(o['asset'], []).append(n)
tmp_coll = bpy.data.collections.new('_export_tmp'); sc.collection.children.link(tmp_coll)
report = {}
for asset, parts in sorted(assets.items()):
    path = f'{STG}/{asset}.fbx'
    if os.path.exists(path) and not OVER:
        print('SKIP (exists)', path); continue
    # rename sources aside so temp exports carry the final names
    for p in parts:
        kit[p].name = p + '_src'
    temps = []
    for p in parts:
        t = bpy.data.objects.new(p, kit[p].data)       # shares mesh data + baked material
        tmp_coll.objects.link(t); temps.append(t)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    for t in temps:
        t.select_set(True)
    bpy.context.view_layer.objects.active = temps[0]
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={'MESH'}, global_scale=1.0,
                             apply_unit_scale=True, apply_scale_options='FBX_SCALE_ALL', bake_space_transform=True,
                             axis_forward='-Z', axis_up='Y', use_mesh_modifiers=True, mesh_smooth_type='OFF',
                             use_triangles=True, use_tspace=True, colors_type='NONE', add_leaf_bones=False,
                             path_mode='RELATIVE', embed_textures=False, bake_anim=False, use_custom_props=False)
    for t in temps:
        bpy.data.objects.remove(t)
    for p in parts:
        kit[p].name = p
    report[asset] = dict(path=os.path.relpath(path, ROOT), bytes=os.path.getsize(path), parts=parts)
    print('EXPORTED', asset, os.path.getsize(path), 'bytes', flush=True)
bpy.data.collections.remove(tmp_coll)
json.dump(report, open(ROOT + '/Art/Blender/Scripts/_build/export_report.json', 'w'), indent=1)
print('EXPORT_DONE', len(report))

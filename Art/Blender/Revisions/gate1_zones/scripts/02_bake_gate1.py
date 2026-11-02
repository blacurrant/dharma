"""GATE-1 bake stage (zone-aware).  Derived from Art/Blender/Scripts/02_bake.py with these changes ONLY:
  1. source = isolated working copy; every output path is under Art/Blender/Revisions/gate1_zones/bake_out/ (never Staging/)
  2. if a part is not on SRC_* materials (e.g. it was already baked), the SRC slots are REBUILT from the persistent `zone_id`
     attribute instead of aborting with "rerun stage 1"
  3. `zone_id` md5 is asserted identical before the bake, after the bake and after the final-material swap
  4. only parts listed after --only are touched; the saved result goes to a separate *_bake_test.blend (the migrated working copy is not modified)
Run: Blender -b --factory-startup --python scripts/02_bake_gate1.py -- --only Brazier_A
"""
import sys, os, json, time, hashlib
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones/scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K
assert os.path.dirname(os.path.abspath(K.__file__)) == HERE

G = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/gate1_zones'
BLEND_IN = G + '/TempleEnvironmentKit_gate1_zones.blend'
OUT = G + '/bake_out'
TEX, SRCTEX = OUT + '/Textures', OUT + '/Source'
BLEND_OUT = OUT + '/TempleEnvironmentKit_gate1_bake_test.blend'
ONLY = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
assert ONLY, 'pass --only <parts>; this gate-1 script does not bulk bake'
for d in (TEX, SRCTEX):
    os.makedirs(d, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND_IN)
sc = bpy.context.scene
if 'TempleBakeWorld' not in bpy.data.worlds:
    w = bpy.data.worlds.new('TempleBakeWorld'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
    w.light_settings.distance = 1.2
sc.world = bpy.data.worlds['TempleBakeWorld']
K.setup_cycles(32)


def zmd5(o):
    a = np.empty(len(o.data.polygons), dtype=np.int32); o.data.attributes[K.ZONE_ATTR].data.foreach_get('value', a)
    return hashlib.md5(a.tobytes()).hexdigest()


def save_img(img, path, rgba=False):
    img.filepath_raw = path; img.file_format = 'PNG'
    if rgba:
        img.alpha_mode = 'CHANNEL_PACKED'
    img.save()


def make_final_material(part, files):
    name = 'MI_Temple_' + part.replace('ENV_Temple_', '')
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(pb.outputs[0], out.inputs[0])

    def tex(path, cs):
        n = nt.nodes.new('ShaderNodeTexImage'); img = bpy.data.images.load(path, check_existing=True); img.colorspace_settings.name = cs
        if cs == 'Non-Color' and path.endswith('_Mask.png'):
            img.alpha_mode = 'CHANNEL_PACKED'
        n.image = img; return n
    tb = tex(files['BaseColor'], 'sRGB'); nt.links.new(tb.outputs['Color'], pb.inputs['Base Color'])
    tn = tex(files['Normal'], 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
    tm = tex(files['Mask'], 'Non-Color'); sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tm.outputs['Color'], sp.inputs[0])
    nt.links.new(sp.outputs['Red'], pb.inputs['Metallic'])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(tm.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], pb.inputs['Roughness'])
    if 'Emission' in files:
        te = tex(files['Emission'], 'sRGB'); nt.links.new(te.outputs['Color'], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = 1.0
    return m


report = {}
for o in sorted([x for x in bpy.data.objects if x.name.startswith('ENV_Temple_') and x.type == 'MESH'], key=lambda x: x.name):
    if not any(k in o.name for k in ONLY):
        continue
    name = o.name; res = int(o['tex_res']); t0 = time.time()
    h_before = zmd5(o)
    slots_before = [m.name for m in o.data.materials]
    if not all(m and m.name.startswith('SRC_') for m in o.data.materials):
        K.restore_zone_slots(o)                                   # <-- replaces the old "rerun stage 1" abort
    slots_src = [m.name for m in o.data.materials]
    files = {k: f'{TEX}/{name}_{k}.png' for k in ('BaseColor', 'Normal', 'Mask')}
    has_em = any('Ember' in m.name for m in o.data.materials)
    if has_em:
        files['Emission'] = f'{TEX}/{name}_Emission.png'
    imgs = K.bake_maps(o, res, SRCTEX, name, tex_samples=(32, 16, 4))
    h_mid = zmd5(o)
    col = K.img_to_np(imgs['BaseColor'])
    r = 3 if res >= 2048 else 2
    base = col.copy(); base[..., :3] = K.painterly(col[..., :3], r, 0.65); base[..., 3] = 1.0
    save_img(K.np_to_img(base, name + '_BaseColor_f', True), files['BaseColor'])
    save_img(imgs['Normal'], files['Normal'])
    mask = K.pack_mask(K.img_to_np(imgs['Metal']), K.img_to_np(imgs['AO']), K.img_to_np(imgs['Rough']))
    save_img(K.np_to_img(mask, name + '_Mask_f', False, True), files['Mask'], rgba=True)
    if has_em:
        save_img(imgs['Emission'], files['Emission'])
    for im in list(imgs.values()):
        bpy.data.images.remove(im)
    m = make_final_material(name, files)
    o['src_materials'] = ','.join(slots_src)
    o.data.materials.clear(); o.data.materials.append(m)
    h_after = zmd5(o)
    assert h_before == h_mid == h_after, (name, h_before, h_mid, h_after)
    report[name] = dict(res=res, slots_before=slots_before, slots_rebuilt_from_zone_id=slots_src, zone_md5_before=h_before, zone_md5_after_bake=h_mid,
                        zone_md5_after_material_swap=h_after, zone_counts=K.zone_counts(o), files={k: os.path.relpath(v, G) for k, v in files.items()},
                        seconds=round(time.time() - t0, 1))
    print('BAKED', name, report[name]['slots_before'], '->', slots_src, '->', report[name]['slots_before'] if False else [x.name for x in o.data.materials],
          'zone_md5 stable:', h_before == h_mid == h_after, f'{time.time()-t0:.1f}s', flush=True)
json.dump(report, open(G + '/evidence/03_bake_gate1.json', 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND_OUT)
print('BAKE_GATE1_DONE', list(report))

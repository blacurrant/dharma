"""Stage 2: bake procedural source materials to texture maps and assign baked, export-safe materials.
Run: Blender -b --factory-startup --python Art/Blender/Scripts/02_bake.py [-- --force]
Resumable: parts whose final textures already exist are not re-baked (use --force to redo).
Outputs
  Art/Blender/Textures/Source/<Part>/*.png   raw bakes (unfiltered colour, roughness, metallic, AO)
  Art/Exports/Environment/Staging/Textures/<Part>_{BaseColor,Normal,Mask,Emission}.png   Unity-ready
"""
import sys, os, json, time
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Scripts'
sys.path.insert(0, HERE)
import bpy
import numpy as np
import kitlib as K

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
TEX = ROOT + '/Art/Exports/Environment/Staging/Textures'
SRCTEX = ROOT + '/Art/Blender/Textures/Source'
MANIFEST = HERE + '/_build/texture_manifest.json'
FORCE = '--force' in sys.argv
ONLY = None
if '--only' in sys.argv:
    ONLY = sys.argv[sys.argv.index('--only') + 1].split(',')
os.makedirs(TEX, exist_ok=True); os.makedirs(SRCTEX, exist_ok=True)

bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
# NOTE: source materials (SRC_Temple_*) were saved by stage 1; do NOT regenerate here (would unlink them).
if 'TempleBakeWorld' not in bpy.data.worlds:
    w = bpy.data.worlds.new('TempleBakeWorld'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs['Color'].default_value = (1, 1, 1, 1)
    w.light_settings.distance = 1.2          # AO range in metres (contact occlusion only)
sc.world = bpy.data.worlds['TempleBakeWorld']
K.setup_cycles(32)


def save_img(img, path, rgba=False):
    img.filepath_raw = path
    img.file_format = 'PNG'
    if rgba:
        img.alpha_mode = 'CHANNEL_PACKED'
    img.save()


def make_final_material(part, files):
    name = 'MI_Temple_' + part.replace('ENV_Temple_', '')
    if name in bpy.data.materials:
        bpy.data.materials.remove(bpy.data.materials[name])
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(pb.outputs[0], out.inputs[0])

    def tex(path, cs):
        n = nt.nodes.new('ShaderNodeTexImage')
        img = bpy.data.images.load(path, check_existing=True)
        img.colorspace_settings.name = cs
        if cs == 'Non-Color' and path.endswith('_Mask.png'):
            img.alpha_mode = 'CHANNEL_PACKED'
        n.image = img
        return n
    tb = tex(files['BaseColor'], 'sRGB'); nt.links.new(tb.outputs['Color'], pb.inputs['Base Color'])
    tn = tex(files['Normal'], 'Non-Color'); nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(tn.outputs['Color'], nm.inputs['Color']); nt.links.new(nm.outputs['Normal'], pb.inputs['Normal'])
    tm = tex(files['Mask'], 'Non-Color')
    sp = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(tm.outputs['Color'], sp.inputs[0])
    nt.links.new(sp.outputs['Red'], pb.inputs['Metallic'])
    inv = nt.nodes.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1.0
    nt.links.new(tm.outputs['Alpha'], inv.inputs[1]); nt.links.new(inv.outputs[0], pb.inputs['Roughness'])
    if 'Emission' in files:
        te = tex(files['Emission'], 'sRGB')
        nt.links.new(te.outputs['Color'], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = 1.0
    return m


manifest = {}
objs = sorted([o for o in bpy.data.objects if o.name.startswith('ENV_Temple_') and o.type == 'MESH'], key=lambda o: o.name)
t_all = time.time()
for o in objs:
    name = o.name
    res = int(o['tex_res'])
    files = {k: f'{TEX}/{name}_{k}.png' for k in ('BaseColor', 'Normal', 'Mask')}
    has_em = any('Ember' in (s.material.name if s.material else '') for s in o.material_slots)
    if has_em:
        files['Emission'] = f'{TEX}/{name}_Emission.png'
    done = all(os.path.exists(p) for p in files.values()) and not FORCE
    if ONLY and any(k in o.name for k in ONLY):
        done = False                      # --only X  => re-bake X, reuse cached textures for everything else
    t0 = time.time()
    if not done:
        # make sure source materials are on the object (rerun-safe)
        if not all(s.material and s.material.name.startswith('SRC_') for s in o.material_slots):
            raise RuntimeError(f'{name}: not on source materials; rerun stage 1 first')
        imgs = K.bake_maps(o, res, SRCTEX, name, tex_samples=(32, 16, 4))
        col = K.img_to_np(imgs['BaseColor'])
        os.makedirs(f'{SRCTEX}/{name}', exist_ok=True)
        save_img(imgs['BaseColor'], f'{SRCTEX}/{name}/{name}_BaseColor_raw.png')
        save_img(imgs['Rough'], f'{SRCTEX}/{name}/{name}_Roughness.png')
        save_img(imgs['Metal'], f'{SRCTEX}/{name}/{name}_Metallic.png')
        save_img(imgs['AO'], f'{SRCTEX}/{name}/{name}_AO.png')
        # painterly pass on albedo (edge-preserving, subtle): reads as brushed colour fields, keeps form edges
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
    # keep source materials on a fake-user so the node networks stay re-bakeable
    o['src_materials'] = ','.join(s.material.name for s in o.material_slots if s.material and s.material.name.startswith('SRC_'))
    o.data.materials.clear(); o.data.materials.append(m)
    manifest[name] = dict(res=res, files={k: os.path.relpath(v, ROOT) for k, v in files.items()}, material=m.name, baked=not done, seconds=round(time.time() - t0, 1))
    print(f"BAKED {name:36s} res={res} {'(cached)' if done else ''} {time.time()-t0:5.1f}s", flush=True)

os.makedirs(os.path.dirname(MANIFEST), exist_ok=True)
old = json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}
old.update(manifest)
json.dump(old, open(MANIFEST, 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('STAGE2_DONE', len(manifest), round(time.time() - t_all, 1), 's')

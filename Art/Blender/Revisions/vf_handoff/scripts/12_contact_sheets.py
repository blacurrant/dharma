"""Contact sheets: every texture on a neutral test card, BEFORE | AFTER | MAP.  Cycles, Standard view transform, sun strength pi straight down
=> a Lambertian card renders as exactly its albedo (no lighting bias).  Runs in a FRESH scene (nothing from the kit is touched).
Blender -b --factory-startup --python scripts/12_contact_sheets.py
"""
import sys, os, math, json
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff/scripts'
sys.path.insert(0, HERE)
import bpy
import vf_nodes as V

VF = V.VF
OUT = VF + '/contact'
os.makedirs(OUT, exist_ok=True)
BASE_HEX = '8A857D'
PANEL, GAP, ROWH = 6.0, 1.2, 8.0


def lin(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]


def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 8; sc.cycles.use_denoising = False
    sc.cycles.use_adaptive_sampling = False
    sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
    sc.render.image_settings.file_format = 'PNG'; sc.render.film_transparent = False
    w = bpy.data.worlds.new('W'); w.use_nodes = True
    w.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 0.0
    sc.world = w
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = math.pi; sd.angle = 0.0
    so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
    return sc


def plane(name, cx, cy, size, mat, z=0.0):
    me = bpy.data.meshes.new(name)
    h = size / 2
    me.from_pydata([(-h, -h, 0), (h, -h, 0), (h, h, 0), (-h, h, 0)], [], [(0, 1, 2, 3)])
    o = bpy.data.objects.new(name, me); o.location = (cx, cy, z)
    bpy.context.scene.collection.objects.link(o); me.materials.append(mat); return o


def diffuse(name, rgb=None):
    m = bpy.data.materials.new(name); m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes['Principled BSDF']


def card_material(name, layers, mode, view_m, off, view_map=False, base_hex=BASE_HEX, ring=False):
    m, nt, bsdf = diffuse(name)
    bsdf.inputs['Roughness'].default_value = 1.0
    try:
        bsdf.inputs['Specular IOR Level'].default_value = 0.0
    except KeyError:
        pass
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sv = nt.nodes.new('ShaderNodeVectorMath'); sv.operation = 'SCALE'; sv.inputs['Scale'].default_value = view_m / PANEL
    nt.links.new(tc.outputs['Object'], sv.inputs[0])
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(sv.outputs[0], sep.inputs[0])
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    ox, oy = sep.outputs[0], sep.outputs[1]
    if mode == 'wall':
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; nt.links.new(oy, add.inputs[0]); add.inputs[1].default_value = view_m / 2 + off[1]
        add2 = nt.nodes.new('ShaderNodeMath'); add2.operation = 'ADD'; nt.links.new(ox, add2.inputs[0]); add2.inputs[1].default_value = off[0]
        nt.links.new(add2.outputs[0], comb.inputs[0]); nt.links.new(add.outputs[0], comb.inputs[2])
        N = nt.nodes.new('ShaderNodeCombineXYZ'); N.inputs[1].default_value = 1.0     # wall facing -Y => along-wall = x
    else:
        add = nt.nodes.new('ShaderNodeMath'); add.operation = 'ADD'; nt.links.new(oy, add.inputs[0]); add.inputs[1].default_value = off[1]
        add2 = nt.nodes.new('ShaderNodeMath'); add2.operation = 'ADD'; nt.links.new(ox, add2.inputs[0]); add2.inputs[1].default_value = off[0]
        nt.links.new(add2.outputs[0], comb.inputs[0]); nt.links.new(add.outputs[0], comb.inputs[1])
        N = nt.nodes.new('ShaderNodeCombineXYZ'); N.inputs[2].default_value = 1.0
    base = nt.nodes.new('ShaderNodeRGB'); base.outputs[0].default_value = tuple(lin(base_hex)) + (1,) if not view_map else (0, 0, 0, 1)
    out = V.build(nt, base.outputs[0], comb.outputs[0], N.outputs[0], layers, view_map=view_map, radial=False) if layers else base.outputs[0]
    nt.links.new(out, bsdf.inputs['Base Color'])
    return m


def text(body, x, y, size):
    cu = bpy.data.curves.new('t', 'FONT'); cu.body = body; cu.size = size; cu.align_x = 'LEFT'
    o = bpy.data.objects.new('t', cu); o.location = (x, y, 0.02); bpy.context.scene.collection.objects.link(o)
    m, nt, b = diffuse('tm'); b.inputs['Base Color'].default_value = (0.9, 0.9, 0.88, 1); b.inputs['Roughness'].default_value = 1.0
    cu.materials.append(m); return o


def ring_obj(cx, cy, radius_card):
    import bmesh
    me = bpy.data.meshes.new('ring'); bm = bmesh.new(); n = 160
    vs = [[bm.verts.new(((radius_card + d) * math.cos(math.tau * i / n), (radius_card + d) * math.sin(math.tau * i / n), 0)) for i in range(n)] for d in (-0.025, 0.025)]
    for i in range(n):
        j = (i + 1) % n; bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i]))
    bm.to_mesh(me); bm.free()
    m, nt, b = diffuse('ringm'); b.inputs['Base Color'].default_value = (1.0, 0.2, 0.9, 1); b.inputs['Roughness'].default_value = 1.0
    o = bpy.data.objects.new('ring', me); o.location = (cx, cy, 0.01); bpy.context.scene.collection.objects.link(o); me.materials.append(m)


def make_sheet(title, rows, out):
    sc = setup()
    ncol = 3
    W = ncol * PANEL + (ncol + 1) * GAP
    H = len(rows) * ROWH + 2.0
    bd = diffuse('bd')[0]; mm, nn, bb = diffuse('bd2'); bb.inputs['Base Color'].default_value = (0.0135, 0.0135, 0.014, 1); bb.inputs['Roughness'].default_value = 1
    plane('backdrop', 0, 0, 400, mm, z=-0.05)
    text(title, -W / 2 + GAP, H / 2 - 1.0, 0.5)
    for ri, row in enumerate(rows):
        name, k, mode, view_m, off = row['name'], row['k'], row['mode'], row['view'], row.get('off', (0, 0))
        ytop = H / 2 - 2.0 - ri * ROWH
        text(f"{ri + 1}. {name}  |  panel {view_m:g} m  |  k = {k}  |  {row['note']}", -W / 2 + GAP, ytop - 0.55, 0.33)
        cy = ytop - 1.0 - PANEL / 2
        caps = ('BEFORE: neutral card #' + BASE_HEX, 'AFTER', 'MAP (alpha / data)')
        for ci in range(ncol):
            cx = -W / 2 + GAP + PANEL / 2 + ci * (PANEL + GAP)
            if ci == 0:
                mat = card_material(f'm_b{ri}', [], mode, view_m, off)
            elif ci == 1:
                mat = card_material(f'm_a{ri}', [(name, k, mode)], mode, view_m, off)
            else:
                mat = card_material(f'm_m{ri}', [(name, 1.0, mode)], mode, view_m, off, view_map=True)
            plane(f'card_{ri}_{ci}', cx, cy, PANEL, mat)
            text(caps[ci], cx - PANEL / 2, cy + PANEL / 2 + 0.12, 0.3)
            if row.get('ring'):
                ring_obj(cx, cy, 10.0 * PANEL / 40.0)
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.ortho_scale = W; cd.clip_end = 100
    co = bpy.data.objects.new('c', cd); co.location = (0, 0, 20); sc.collection.objects.link(co); sc.camera = co
    sc.render.resolution_x = int(W * 100); sc.render.resolution_y = int(H * 100)
    # ortho_scale is the larger dimension: make the frame exactly W wide
    cd.ortho_scale = max(W, H) if H > W else W
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print('SHEET', out, sc.render.resolution_x, sc.render.resolution_y, flush=True)


def make_image_sheet(title, rows, out, pw=11.0, gap=0.9):
    """rows: list of (label, left_png, left_caption, right_png, right_caption). Emission shader = the image shown 1:1 (Standard view)."""
    sc = setup()
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT':
            bpy.data.objects.remove(o)
    W = 2 * pw + 3 * gap
    heights = []
    for r in rows:
        im = bpy.data.images.load(r[1]); heights.append(pw * im.size[1] / im.size[0])
    H = 2.0 + sum(heights) + len(rows) * 1.6
    text(title, -W / 2 + gap, H / 2 - 1.0, 0.42)
    y = H / 2 - 1.6
    for (label, lp, lc, rp, rc), hh in zip(rows, heights):
        text(label, -W / 2 + gap, y - 0.5, 0.30)
        y -= 1.0
        for ci, (pth, cap) in enumerate(((lp, lc), (rp, rc))):
            cx = -W / 2 + gap + pw / 2 + ci * (pw + gap)
            m = bpy.data.materials.new('im'); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
            tx = nt.nodes.new('ShaderNodeTexImage'); im = bpy.data.images.load(pth); im.colorspace_settings.name = 'sRGB'; tx.image = im
            em = nt.nodes.new('ShaderNodeEmission'); oc = nt.nodes.new('ShaderNodeOutputMaterial')
            nt.links.new(tx.outputs['Color'], em.inputs['Color']); nt.links.new(em.outputs[0], oc.inputs['Surface'])
            me = bpy.data.meshes.new('p'); hw = pw / 2; hh2 = hh / 2
            me.from_pydata([(-hw, -hh2, 0), (hw, -hh2, 0), (hw, hh2, 0), (-hw, hh2, 0)], [], [(0, 1, 2, 3)])
            uv = me.uv_layers.new(name='UV')
            for l, c in zip(me.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
                uv.data[l.index].uv = c
            o = bpy.data.objects.new('p', me); o.location = (cx, y - hh2 - 0.05, 0); sc.collection.objects.link(o); me.materials.append(m)
            text(cap, cx - pw / 2, y + 0.05, 0.3)
        y -= hh + 0.6
    bb = bpy.data.materials.new('bd'); bb.use_nodes = True; bb.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1)
    me = bpy.data.meshes.new('bd'); me.from_pydata([(-300, -300, -0.05), (300, -300, -0.05), (300, 300, -0.05), (-300, 300, -0.05)], [], [(0, 1, 2, 3)]); me.materials.append(bb)
    bo = bpy.data.objects.new('bd', me); sc.collection.objects.link(bo)
    sd = bpy.data.lights.new('sun', 'SUN'); sd.energy = 0.3; so = bpy.data.objects.new('sun', sd); sc.collection.objects.link(so)
    cd = bpy.data.cameras.new('c'); cd.type = 'ORTHO'; cd.clip_end = 100
    co = bpy.data.objects.new('c', cd); co.location = (0, 0, 20); sc.collection.objects.link(co); sc.camera = co
    sc.render.resolution_x = int(W * 90); sc.render.resolution_y = int(H * 90)
    cd.ortho_scale = max(W, H)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    print('SHEET', out, sc.render.resolution_x, sc.render.resolution_y, flush=True)


S = V.SPEC
def row(name, view, mode, note, off=(0, 0), ring=False, kk=None):
    return dict(name=name, k=S[name][3] if kk is None else kk, mode=mode, view=view, off=off, note=note, ring=ring)


floor_rows = [
    row('VF_Floor_MacroValue_2048', 40.0, 'floor', '40x40 m floor; magenta ring = r 10 m combat circle', ring=True),
    row('VF_Floor_MacroTint_1024', 40.0, 'floor', '40x40 m floor; ring = combat circle', ring=True),
    row('VF_Floor_Cracks_2048', 6.0, 'floor', '6 m window of the 8 m tile', off=(4.0, 4.0)),
    row('VF_Floor_Wear_1024', 4.0, 'floor', 'one 4 m tile', off=(2.0, 2.0)),
    row('VF_Floor_ChippedEdges_1024', 6.0, 'floor', '3x3 floor tiles (2 m)', off=(3.0, 3.0)),
    row('VF_Weather_MossFloorJoints_1024', 6.0, 'floor', '3x3 floor tiles (2 m)', off=(3.0, 3.0)),
]
weather_rows = [
    row('VF_Wall_RainStreaks_1024', 6.0, 'wall', 'wall plane, card bottom = floor'),
    row('VF_Weather_Salt_1024', 4.0, 'floor', 'two tiles of 2 m', off=(2.0, 2.0)),
    row('VF_Weather_Moss_1024', 4.0, 'floor', 'generic: gate by height/joint mask', off=(2.0, 2.0)),
    row('VF_Weather_MossWallBase_1024', 6.0, 'wall', 'wall plane, card bottom = floor'),
    row('VF_Weather_SootFloorRing_1024', 6.0, 'floor', 'decal 3.2 m', off=(0.0, 0.0)),
    row('VF_Weather_SootWallPlume_512x1024', 6.0, 'wall', 'decal 1.5 x 3 m', off=(0.0, 0.0)),
]
if __name__ == '__main__' or True:
    which = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'all'
    if which in ('all', 'floor'):
        make_sheet('VF handoff - FLOOR ingredients on a neutral test card (Cycles, Standard view)', floor_rows, OUT + '/VF_contact_floor.png')
    if which in ('all', 'weather'):
        make_sheet('VF handoff - WEATHERING overlays on a neutral test card (Cycles, Standard view)', weather_rows, OUT + '/VF_contact_weather.png')
    if which in ('all', 'courtyard'):
        R = VF + '/renders/'
        make_image_sheet('VF handoff - COURTYARD before / after (EEVEE, Standard view)', [
            ('1. Plan view, 40x40 m floor. Variation fades inside the r = 10 m combat circle.', R + 'VF_courtyard_plan_before.png', 'BEFORE', R + 'VF_courtyard_plan_after.png', 'AFTER (floor stack + wall stack + soot)'),
            ('2. Gameplay camera (ortho 11, offset 12,18,-12), clean view.', R + 'VF_courtyard_gameplay_before.png', 'BEFORE', R + 'VF_courtyard_gameplay_after.png', 'AFTER'),
            ('3. Gameplay camera + existing test telegraph (readability check).', R + 'VF_courtyard_gameplay_before_telegraph.png', 'BEFORE', R + 'VF_courtyard_gameplay_after_telegraph.png', 'AFTER'),
            ('4. Dais brazier close-up (platform/stairs get value, tint, cracks, wear).', R + 'VF_courtyard_gameplay_before.png' if False else R + 'VF_closeup_dais_brazier_before.png', 'BEFORE', R + 'VF_closeup_dais_brazier_after.png', 'AFTER'),
            ('5. Brazier next to a wall.', R + 'VF_closeup_wallbrazier_before.png', 'BEFORE', R + 'VF_closeup_wallbrazier_after.png', 'AFTER'),
            ('6. Wall base: rain streaks, salt, restrained moss.', R + 'VF_closeup_wall_left_before.png', 'BEFORE', R + 'VF_closeup_wall_left_after.png', 'AFTER'),
        ], OUT + '/VF_contact_courtyard.png')
    print('SHEETS_DONE')

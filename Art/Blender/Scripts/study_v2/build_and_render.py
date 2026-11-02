"""v2 art-direction STUDY (isolated; does not open or write the production .blend or any export).

Rebuilds the kit pieces from the deterministic builders (assets.py, same seeds => same meshes) into a FRESH scene,
instances them from TempleCourtyard_Placement.json, and renders the same courtyard under three looks:
  current  : original source materials + original sun (front-lit) .......... baseline (matches the kit that shipped)
  material : proposed study materials, original lighting ................... isolates the material change
  full     : study materials + study lighting + haze + mortar underlay ..... target direction

Run: Blender -b --factory-startup --python Art/Blender/Scripts/study_v2/build_and_render.py -- --look full --views gameplay,closeup [--samples 64] [--save]
Outputs: Art/Blender/Revisions/v2_study/renders/<look>_<view>.png  (+ sampling report JSON)
"""
import sys, os, json, math
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Scripts'
sys.path.insert(0, HERE)
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix
from bpy_extras.object_utils import world_to_camera_view
import kitlib as K
import assets as A

ROOT = '/Users/landerstudio/MythicRoguelite'
OUT = ROOT + '/Art/Blender/Revisions/v2_study'
os.makedirs(OUT + '/renders', exist_ok=True)
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
LOOK = argv[argv.index('--look') + 1] if '--look' in argv else 'full'
VIEWS = (argv[argv.index('--views') + 1] if '--views' in argv else 'gameplay,closeup').split(',')
SAMPLES = int(argv[argv.index('--samples') + 1]) if '--samples' in argv else 64
SAVE = '--save' in argv
HAZE = float(argv[argv.index('--haze') + 1]) if '--haze' in argv else 0.008
MORTAR = '--nomortar' not in argv
TAG = argv[argv.index('--tag') + 1] if '--tag' in argv else ''
assert LOOK in ('current', 'material', 'full')
U = lambda x, y, z: Vector((x, z, y))

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.name = 'TempleStudyV2'

# ---------------------------------------------------------------- 1. rebuild kit meshes (deterministic) -> shared mesh data
K.make_src_materials()
tmp = bpy.data.collections.new('_kit_build'); sc.collection.children.link(tmp)
mesh_of, cat_of, props_of, slotnames = {}, {}, {}, {}
for cat, asset, parts, target, vm, wm, dm in A.REG:
    for suffix, fn in parts:
        name = 'ENV_Temple_' + asset + suffix
        b = fn()
        o = b.to_object(name, tmp)
        mesh_of[name] = o.data
        cat_of[name] = cat
        props_of[name] = dict(value_mult=vm, wear_mult=wm, damp_mult=dm,
                              tone_var=0.30 if cat == 'Floor' else 1.0, dirt_mult=0.55 if cat == 'Floor' else 1.0)
        slotnames[name] = [m.name for m in o.data.materials]
        bpy.data.objects.remove(o, do_unlink=True)
bpy.data.collections.remove(tmp)

# ---------------------------------------------------------------- 2. study materials
def hx(h):
    return K.hexc(h)


def study_stone(name, pal, kind):
    """kind: 'floor' | 'struct' | 'dark'. Palette is desaturated neutral-warm grey (NOT tan/saffron)."""
    mat = bpy.data.materials.new(name); mat.use_fake_user = True
    nb = K.NB(mat); c = K._common_inputs(nb)
    rnd = nb.node('ShaderNodeObjectInfo').outputs['Random']
    floor = kind == 'floor'
    tv = 0.40 if floor else 0.95
    V = nb.math('ADD', nb.math('MULTIPLY', c['n_lo'], 0.60), nb.math('MULTIPLY', c['n_mid'], 0.24))
    V = nb.math('ADD', V, nb.math('MULTIPLY', c['n_a'], 0.07))
    V = nb.math('ADD', V, nb.math('MULTIPLY', nb.math('SUBTRACT', c['tone'], 0.5), 0.55 * tv))
    V = nb.math('ADD', V, nb.math('MULTIPLY', nb.math('SUBTRACT', rnd, 0.5), 0.20))          # per-instance value shift
    gain = 1.25 if floor else 1.75
    V = nb.math('ADD', 0.5, nb.math('MULTIPLY', nb.math('SUBTRACT', V, 0.5), gain))
    col = nb.ramp(V, [(0.0, hx(pal[0])), (0.30, hx(pal[1])), (0.55, hx(pal[2])), (0.80, hx(pal[3])), (1.0, hx(pal[4]))])
    # painterly drift: broad cool-grey / warm-grey fields (not noise: follows the large low-frequency field)
    col = nb.mix(nb.maprange(c['n_lo'], 0.50, 0.72, 0.0, 0.24), col, hx('#5A615E'))
    crev = nb.maprange(c['ao'], 0.35, 1.0, 1.0, 0.0)
    if floor:
        damp = 0.0
    else:
        zz = nb.math('ADD', c['Z'], nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_mid'], 0.5), 0.9))
        damp = nb.maprange(zz, 0.10, 1.30, 1.0, 0.0)
    dirt = nb.math('MINIMUM', 1.0, nb.math('ADD', nb.math('ADD', nb.math('MULTIPLY', crev, 0.85), nb.math('MULTIPLY', damp, 0.55) if not floor else 0.0),
                                           nb.math('MULTIPLY', c['cracks'], 0.95)))
    if floor:
        dirt = nb.math('MULTIPLY', dirt, 0.65)
    col = nb.mix(nb.math('MULTIPLY', dirt, 0.60), col, hx('#161513'))
    # moss / lichen: where water sits (low faces, crevices); olive hue ~80 deg (never teal)
    mmask = nb.math('MULTIPLY', nb.math('ADD', nb.math('MULTIPLY', damp, 0.75) if not floor else 0.0, nb.math('MULTIPLY', crev, 0.55)),
                    nb.maprange(c['n_a'], 0.44, 0.66, 0.0, 1.0))
    col = nb.mix(nb.math('MULTIPLY', mmask, 0.35 if floor else 0.95, clamp=True), col, hx('#434F2A' if kind != 'dark' else '#363F26'))
    col = nb.mix(nb.math('MULTIPLY', nb.math('MULTIPLY', c['top'], nb.maprange(c['n_hi'], 0.50, 0.68, 0.0, 1.0)), 0.30 if not floor else 0.12),
                 col, hx('#8D9279'))
    if not floor:                                           # rain-wash streaks: elongated along Z, strongest high on the piece
        mp = nb.node('ShaderNodeMapping', vector_type='POINT')
        nb.nt.links.new(c['P'], mp.inputs['Vector']); mp.inputs['Scale'].default_value = (6.0, 6.0, 0.14)
        st = nb.noise(mp.outputs[0], 5.0, 3.0, 0.5)
        streak = nb.math('MULTIPLY', nb.maprange(st, 0.50, 0.70, 0.0, 1.0), nb.maprange(c['Z'], 0.4, 3.0, 0.15, 1.0))
        col = nb.mix(nb.math('MULTIPLY', streak, 0.50), col, hx('#14130F'))
    edge = nb.math('MULTIPLY', nb.maprange(c['edge_raw'], 0.02, 0.35, 0.0, 1.0), nb.maprange(c['n_hi'], 0.35, 0.65, 0.35, 1.0))
    col = nb.mix(nb.math('MULTIPLY', edge, 0.42), col, hx('#9A9686' if kind != 'dark' else '#55524B'))
    rough = nb.math('ADD', 0.80, nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.30))
    rough = nb.math('ADD', rough, nb.math('MULTIPLY', mmask, 0.14))
    rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', c['top'], 0.06))
    rough = nb.math('ADD', rough, nb.math('MULTIPLY', c['cracks'], 0.10))
    if floor:   # damp sheen patches: darker + glossier where water pools (large, causal, readable under a raking key)
        wet = nb.maprange(c['n_lo'], 0.58, 0.68, 0.0, 1.0)
        rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', wet, 0.34))
        col = nb.mix(nb.math('MULTIPLY', wet, 0.28), col, hx('#222120'))
    rough = nb.math('MAXIMUM', 0.32, nb.math('MINIMUM', 1.0, rough))
    h = nb.math('ADD', nb.math('MULTIPLY', c['n_hi'], 0.35), nb.math('MULTIPLY', c['n_a'], 0.40))
    h = nb.math('SUBTRACT', nb.math('ADD', h, nb.math('MULTIPLY', c['n_mid'], 0.25)), nb.math('MULTIPLY', c['cracks'], 0.9))
    K._finish_principled(nb, col, rough, 0.0, bump_h=h, bump_str=0.55, bump_dist=0.04)
    return mat


def study_metal(name, ramp, patina_hex, burnish_hex, rough0, metal_min):
    mat = bpy.data.materials.new(name); mat.use_fake_user = True
    nb = K.NB(mat); c = K._common_inputs(nb)
    base = nb.ramp(nb.math('ADD', c['n_mid'], nb.math('MULTIPLY', c['n_lo'], 0.5)), [(p, hx(h)) for p, h in ramp])
    crev = nb.maprange(c['ao'], 0.4, 1.0, 1.0, 0.0)
    edge = nb.maprange(c['edge_raw'], 0.02, 0.30, 0.0, 1.0)
    patina = nb.math('MINIMUM', 1.0, nb.math('ADD', nb.math('MULTIPLY', crev, 0.9), nb.maprange(c['n_a'], 0.50, 0.75, 0.0, 0.7)))
    base = nb.mix(nb.math('MULTIPLY', patina, 0.80), base, hx(patina_hex))       # olive-umber patina, deliberately not teal
    base = nb.mix(nb.math('MULTIPLY', edge, 0.55), base, hx(burnish_hex))
    rough = nb.math('ADD', rough0, nb.math('ADD', nb.math('MULTIPLY', patina, 0.30), nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.2)))
    rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', edge, 0.16))
    metal = nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', patina, 1.0 - metal_min))
    h = nb.math('ADD', nb.math('MULTIPLY', c['n_hi'], 0.5), nb.math('MULTIPLY', c['n_a'], 0.5))
    K._finish_principled(nb, base, nb.math('MAXIMUM', 0.22, rough), metal, bump_h=h, bump_str=0.25, bump_dist=0.02)
    return mat


def study_cloth(name):
    mat = bpy.data.materials.new(name); mat.use_fake_user = True
    nb = K.NB(mat); c = K._common_inputs(nb)
    base = nb.ramp(nb.math('ADD', c['n_mid'], nb.math('MULTIPLY', c['n_lo'], 0.6)),
                   [(0.0, hx('#4A130D')), (0.55, hx('#7C2418')), (1.0, hx('#9C3524'))])
    crev = nb.maprange(c['ao'], 0.5, 1.0, 1.0, 0.0)
    base = nb.mix(nb.math('MULTIPLY', crev, 0.5), base, hx('#2A0A07'))
    fade = nb.maprange(nb.math('ADD', c['Z'], nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_mid'], 0.5), 0.6)), -1.4, 0.2, 0.0, 1.0)
    base = nb.mix(nb.math('MULTIPLY', fade, 0.40), base, hx('#33231A'))             # soiled hem
    weave = nb.noise(c['P'], 160.0, 2.0, 0.6)
    K._finish_principled(nb, base, nb.math('ADD', 0.84, nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.1)), 0.0,
                         bump_h=nb.math('ADD', nb.math('MULTIPLY', weave, 0.7), nb.math('MULTIPLY', c['n_a'], 0.3)), bump_str=0.4, bump_dist=0.01)
    return mat


def study_mortar(name):
    mat = bpy.data.materials.new(name); mat.use_fake_user = True
    nb = K.NB(mat); c = K._common_inputs(nb)
    col = nb.ramp(nb.math('ADD', c['n_mid'], nb.math('MULTIPLY', c['n_hi'], 0.4)), [(0.0, hx('#2B2926')), (0.6, hx('#3D3A35')), (1.0, hx('#4E4A43'))])
    col = nb.mix(nb.maprange(c['n_a'], 0.5, 0.7, 0.0, 0.35), col, hx('#3B4326'))     # earth/moss in the joints
    K._finish_principled(nb, col, 0.95, 0.0, bump_h=nb.math('MULTIPLY', c['n_hi'], 0.8), bump_str=0.6, bump_dist=0.03)
    return mat


STUDY = {}
if LOOK != 'current':
    STUDY['floor'] = study_stone('STUDY_StoneFloor', ['#201D1A', '#37332D', '#504B42', '#6A6355', '#857C6A'], 'floor')
    STUDY['struct'] = study_stone('STUDY_StoneStruct', ['#211F1C', '#3F3B35', '#635E52', '#8A826F', '#ABA38D'], 'struct')
    STUDY['dark'] = study_stone('STUDY_StoneDark', ['#0F0F10', '#1B1C1D', '#292A2A', '#383A39', '#474846'], 'dark')
    STUDY['bronze'] = study_metal('STUDY_BronzeAged', [(0.0, '#221C10'), (0.5, '#54432A'), (1.0, '#83693C')], '#262515', '#B08A50', 0.46, 0.45)
    STUDY['brass'] = study_metal('STUDY_BrassMuted', [(0.0, '#43341A'), (0.5, '#7C6130'), (1.0, '#A58545')], '#2E2813', '#C2A15E', 0.52, 0.6)
    STUDY['cloth'] = study_cloth('STUDY_ClothOxideRed')
    STUDY['mortar'] = study_mortar('STUDY_Mortar')
    SRC2STUDY = {'SRC_Temple_StoneCharcoal': 'dark', 'SRC_Temple_Bronze': 'bronze', 'SRC_Temple_Gold': 'brass', 'SRC_Temple_CrimsonCloth': 'cloth'}
    for name, me in mesh_of.items():
        kind = 'floor' if cat_of[name] == 'Floor' else 'struct'
        me.materials.clear()
        for sn in slotnames[name]:
            if sn == 'SRC_Temple_StoneWarm':
                me.materials.append(STUDY[kind])
            elif sn == 'SRC_Temple_EmberAmber':
                me.materials.append(bpy.data.materials[sn])
            else:
                me.materials.append(STUDY[SRC2STUDY[sn]])

# ---------------------------------------------------------------- 3. instances from the placement table
coll = bpy.data.collections.new('LAY_Courtyard'); sc.collection.children.link(coll)
pl = json.load(open(ROOT + '/Art/Exports/Environment/Staging/TempleCourtyard_Placement.json'))
inst = []
for r in pl['instances']:
    part = r['part']
    o = bpy.data.objects.new('LAY_' + part.replace('ENV_Temple_', ''), mesh_of[part])
    o.matrix_world = Matrix.Translation(U(r['unity_x'], r['unity_y'], r['unity_z'])) @ Matrix.Rotation(-math.radians(r['yaw_front_to_plusZ']), 4, 'Z')
    for k, v in props_of[part].items():
        o[k] = v
    coll.objects.link(o); inst.append((part, o))
CL = bpy.data.collections.new('LAY_Cameras_Lights_Proxies'); sc.collection.children.link(CL)

# ---------------------------------------------------------------- 4. lighting / world per look
def make_world(ambient_rgb, ambient_strength, haze_density):
    wd = bpy.data.worlds.new('StudyWorld'); wd.use_nodes = True
    nt = wd.node_tree; nt.nodes.clear()
    wo = nt.nodes.new('ShaderNodeOutputWorld')
    b_amb = nt.nodes.new('ShaderNodeBackground'); b_amb.inputs['Color'].default_value = (*ambient_rgb, 1); b_amb.inputs['Strength'].default_value = ambient_strength
    b_dark = nt.nodes.new('ShaderNodeBackground'); b_dark.inputs['Color'].default_value = (0.020, 0.018, 0.017, 1)
    lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); nt.links.new(b_amb.outputs[0], mx.inputs[1]); nt.links.new(b_dark.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], wo.inputs['Surface'])
    if haze_density > 0:
        vs = nt.nodes.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = haze_density
        vs.inputs['Color'].default_value = (0.86, 0.82, 0.76, 1); vs.inputs['Anisotropy'].default_value = 0.55
        nt.links.new(vs.outputs[0], wo.inputs['Volume'])
    sc.world = wd


def make_sun(energy, rgb, elev_deg, horiz_xz):
    sun = bpy.data.lights.new('SUN_Key', 'SUN'); sun.energy = energy; sun.color = rgb; sun.angle = math.radians(2.0)
    so = bpy.data.objects.new('SUN_Key', sun); CL.objects.link(so)
    el = math.radians(elev_deg); h = Vector(horiz_xz).normalized()
    tu = Vector((h.x * math.cos(el), -math.sin(el), h.y * math.cos(el)))          # travel direction, Unity space
    so.rotation_euler = Vector((tu.x, tu.z, tu.y)).to_track_quat('-Z', 'Y').to_euler()
    return so


if LOOK in ('current', 'material'):
    make_world((0.27, 0.27, 0.285), 0.85, 0.0)
    make_sun(3.8, (1.0, 0.91, 0.78), 52, (0.31, 0.95))                                 # original: light travels ~ with the camera => front-lit, flat
    brazier_w, altar_w = 110, 220
else:
    make_world((0.34, 0.38, 0.45), 0.70, 0.0)     # infinite world volume swallows light with an ortho camera -> use a bounded haze box below                                       # cool fill, thin haze
    # key from the far/right side: travel toward -Z (and a little -X): long shadows fall toward the camera, rim-light on the actors
    make_sun(7.5, (1.0, 0.82, 0.60), 34, (-0.38, -0.93))
    brazier_w, altar_w = 190, 380
for part, o in inst:
    if part == 'ENV_Temple_Brazier_A':
        L = bpy.data.lights.new('LIGHT_Ember', 'POINT'); L.energy = brazier_w; L.color = (1.0, 0.52, 0.20); L.shadow_soft_size = 0.25
        lo = bpy.data.objects.new('LIGHT_Ember', L); lo.location = o.matrix_world @ Vector((0, 0, 1.25)); CL.objects.link(lo)
    if part == 'ENV_Temple_Altar_A':
        L = bpy.data.lights.new('LIGHT_AltarCore', 'POINT'); L.energy = altar_w; L.color = (1.0, 0.55, 0.20); L.shadow_soft_size = 0.2
        lo = bpy.data.objects.new('LIGHT_AltarCore', L); lo.location = o.matrix_world @ Vector((0, 0.1, 2.5)); CL.objects.link(lo)

if LOOK == 'full' and MORTAR:      # mortar underlay: ONE plane under the existing tiles (grout reads as packed earth, not a black slot)
    bm = bmesh.new(); bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=20.4)
    me = bpy.data.meshes.new('mortar'); bm.to_mesh(me); bm.free(); me.materials.append(STUDY['mortar'])
    mo = bpy.data.objects.new('STUDY_MortarUnderlay', me); mo.location = (0, 0, -0.026); CL.objects.link(mo)

if LOOK == 'full' and HAZE > 0:       # bounded haze: a box around the courtyard (Unity-side equivalent: height fog / volume)
    hm = bpy.data.materials.new('STUDY_Haze'); hm.use_nodes = True; nt = hm.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); vs = nt.nodes.new('ShaderNodeVolumeScatter')
    vs.inputs['Density'].default_value = HAZE; vs.inputs['Color'].default_value = (0.88, 0.84, 0.78, 1); vs.inputs['Anisotropy'].default_value = 0.5
    nt.links.new(vs.outputs[0], out.inputs['Volume'])
    bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0, 7.0)) @ Matrix.Diagonal((44, 44, 14, 1)))
    me = bpy.data.meshes.new('haze'); bm.to_mesh(me); bm.free(); me.materials.append(hm)
    ho = bpy.data.objects.new('STUDY_HazeBox', me); CL.objects.link(ho)

# ---------------------------------------------------------------- 5. proxies (scale/readability only) + telegraph
def proxy_mat(name, rgb, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(pb.outputs[0], out.inputs[0])
    pb.inputs['Base Color'].default_value = (*rgb, 1); pb.inputs['Roughness'].default_value = rough
    return m


def emit_alpha(name, rgb, alpha):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Color'].default_value = (*rgb, 1); mx.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
    return m


def figure(name, h, mat):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.30, radius2=0.22, depth=h * 0.76, matrix=Matrix.Translation((0, 0, h * 0.38)))
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.16, matrix=Matrix.Translation((0, 0, h * 0.88)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0.26, h * 0.55)) @ Matrix.Diagonal((0.09, 0.30, 0.09, 1)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    o = bpy.data.objects.new(name, me); CL.objects.link(o); return o


def sector(name, R, half_deg, mat):
    bm = bmesh.new(); n = 28; c0 = bm.verts.new((0, 0, 0))
    vs = [bm.verts.new((R * math.sin(math.radians(-half_deg + 2 * half_deg * i / n)), R * math.cos(math.radians(-half_deg + 2 * half_deg * i / n)), 0)) for i in range(n + 1)]
    for i in range(n):
        bm.faces.new((c0, vs[i + 1], vs[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); CL.objects.link(o); return o


def outline(name, R, half_deg, w, mat):
    bm = bmesh.new(); n = 28
    pts = [(R * math.sin(math.radians(-half_deg + 2 * half_deg * i / n)), R * math.cos(math.radians(-half_deg + 2 * half_deg * i / n))) for i in range(n + 1)]

    def strip(a, b):
        d = Vector((b[0] - a[0], b[1] - a[1])).normalized(); nr = Vector((-d.y, d.x)) * w / 2
        bm.faces.new([bm.verts.new((a[0] + nr.x, a[1] + nr.y, 0)), bm.verts.new((b[0] + nr.x, b[1] + nr.y, 0)),
                      bm.verts.new((b[0] - nr.x, b[1] - nr.y, 0)), bm.verts.new((a[0] - nr.x, a[1] - nr.y, 0))])
    for i in range(n):
        strip(pts[i], pts[i + 1])
    strip((0, 0), pts[0]); strip((0, 0), pts[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); CL.objects.link(o); return o


player = figure('PROXY_Player', 1.78, proxy_mat('PROXY_Player', (0.16, 0.17, 0.19), 0.45))
enemy = figure('PROXY_Enemy', 1.78, proxy_mat('PROXY_Enemy', (0.20, 0.05, 0.04), 0.45))
tel_fill = sector('PROXY_Telegraph_Fill', 2.4 * 0.62, 58, emit_alpha('PROXY_Tel_Fill', K.hexc('#27DCD1')[:3], 0.25))
tel_edge = outline('PROXY_Telegraph_Edge', 2.4, 58, 0.07, emit_alpha('PROXY_Tel_Edge', K.hexc('#9BFFF6')[:3], 0.9))
PL, EN = (-6.5, 6.5), (-4.0, 4.0)
player.location = U(PL[0], 0, PL[1]); enemy.location = U(EN[0], 0, EN[1])
dvec = Vector((PL[0] - EN[0], PL[1] - EN[1])); fwd = dvec.normalized()
enemy.rotation_euler = (0, 0, -math.atan2(dvec.x, dvec.y)); player.rotation_euler = (0, 0, -math.atan2(-dvec.x, -dvec.y))
for t in (tel_fill, tel_edge):
    t.location = U(EN[0], 0.04, EN[1]); t.rotation_euler = enemy.rotation_euler

# ---------------------------------------------------------------- 6. cameras (PrototypeArena: ortho size 11 => 39.1 m wide at 16:9, offset 12/18/-12)
def make_cam(name, target_u, ortho):
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_start = 0.1; cd.clip_end = 200
    o = bpy.data.objects.new(name, cd); CL.objects.link(o)
    o.location = U(target_u[0] + 12, target_u[1] + 18, target_u[2] - 12)
    o.rotation_euler = (U(*target_u) - o.location).to_track_quat('-Z', 'Y').to_euler()
    return o


cams = {'gameplay': make_cam('CAM_Gameplay', (-7.0, 0.0, 7.0), 2 * 11 * 16 / 9),
        'closeup': make_cam('CAM_Dais_Closeup', (-12.0, 1.4, 12.0), 15.0)}

# ---------------------------------------------------------------- 7. render
K.setup_cycles(SAMPLES)
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception:
    pass
sc.cycles.max_bounces = 6
sc.view_settings.view_transform = 'Standard'
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
sc.render.image_settings.file_format = 'PNG'
report = {}


def luma_srgb(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def load_px(path):
    img = bpy.data.images.load(path); w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a); a = a.reshape(h, w, 4); bpy.data.images.remove(img)
    return a


def sample_luma(a, cam, pts):
    h, w = a.shape[:2]; vals = []
    for (x, z) in pts:
        co = world_to_camera_view(sc, cam, U(x, 0.0, z))
        px, py = int(co.x * w), int(co.y * h)
        if 2 <= px < w - 2 and 2 <= py < h - 2:
            vals.append(luma_srgb(a[py - 1:py + 2, px - 1:px + 2, :3].reshape(-1, 3).mean(0)))
    return np.array(vals)


def measure_telegraph(path, cam):
    """Exact lift: same pixels, same seed, render WITH and WITHOUT the telegraph proxies (display-referred sRGB luma)."""
    right = Vector((fwd.y, -fwd.x))
    fill_pts, ring_pts = [], []
    for r in np.linspace(0.55, 1.35, 9):
        for phi in np.radians(np.linspace(-38, 38, 15)):
            off = fwd * (r * math.cos(phi)) + right * (r * math.sin(phi)); fill_pts.append((EN[0] + off.x, EN[1] + off.y))
    for phi in np.radians(np.linspace(-50, 50, 41)):
        off = fwd * (2.4 * math.cos(phi)) + right * (2.4 * math.sin(phi)); ring_pts.append((EN[0] + off.x, EN[1] + off.y))
    with_t = load_px(path)
    for t in (tel_fill, tel_edge):
        t.hide_render = True
    p0 = path.replace('.png', '_notelegraph.png'); sc.render.filepath = p0
    bpy.ops.render.render(write_still=True)
    for t in (tel_fill, tel_edge):
        t.hide_render = False
    sc.render.filepath = path
    wo = load_px(p0)
    f1, f0 = sample_luma(with_t, cam, fill_pts), sample_luma(wo, cam, fill_pts)
    e1, e0 = sample_luma(with_t, cam, ring_pts), sample_luma(wo, cam, ring_pts)
    return dict(n_fill=int(len(f1)), floor_luma_under_fill=round(float(f0.mean()), 4), fill_luma=round(float(f1.mean()), 4),
                fill_lift=round(float(f1.mean() - f0.mean()), 4), floor_luma_under_edge=round(float(e0.mean()), 4),
                edge_luma=round(float(e1.mean()), 4), edge_lift=round(float(e1.mean() - e0.mean()), 4))


for v in VIEWS:
    cam = cams[v]; sc.camera = cam
    path = f'{OUT}/renders/{LOOK}{TAG}_{v}.png'
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    if v == 'gameplay':
        report[v] = measure_telegraph(path, cam)
    print('RENDERED', LOOK, v, report.get(v), flush=True)
json.dump(report, open(f'{OUT}/renders/{LOOK}{TAG}_measure.json', 'w'), indent=1)
if SAVE:
    bpy.ops.wm.save_as_mainfile(filepath=OUT + '/TempleEnvironmentKit_v2_study.blend')
    print('SAVED working copy', OUT + '/TempleEnvironmentKit_v2_study.blend')
print('STUDY_DONE', LOOK)

"""Stage 3: compose ONE courtyard from linked-duplicate kit pieces in '30_Test_Layouts' (no new modelling).

Coordinates: author in Unity-style (x, y_up, z); Blender position = (x, z, y_up).  Unity yaw (clockwise from above,
0 = +Z) maps to Blender rotation_z = -yaw.  Local piece frame: +Y (Blender) = 'front'.

Verified PrototypeArena footprint (Docs/ART_BIBLE.md 6.2): floor +-20 m, wall inner faces +-19.5 m, clear combat zone r = 10 m.
Camera: orthographic size 11, offset (12, 18, -12) from the player => yaw 45 deg, pitch ~46.7 deg, on the +X/-Z side.
"""
import sys, os, json, math, random
HERE = '/Users/landerstudio/MythicRoguelite/Art/Blender/Scripts'
sys.path.insert(0, HERE)
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix

ROOT = '/Users/landerstudio/MythicRoguelite'
BLEND = ROOT + '/Art/Blender/TempleEnvironmentKit.blend'
OUTJ = HERE + '/_build/layout_report.json'
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc = bpy.context.scene
rng = random.Random(7)
TAU = math.tau


def U(x, y, z):
    return Vector((x, z, y))


def xf(pos, yaw=0.0, local=(0, 0, 0)):
    return Matrix.Translation(U(*pos)) @ Matrix.Rotation(-math.radians(yaw), 4, 'Z') @ Matrix.Translation(Vector(local))


# ---------------------------------------------------------------- collections
parent = bpy.data.collections['30_Test_Layouts']
for c in list(parent.children):
    for o in list(c.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    parent.children.unlink(c); bpy.data.collections.remove(c)
for o in list(parent.objects):
    bpy.data.objects.remove(o, do_unlink=True)
C = {}
for n in ('LAY_Floor', 'LAY_Walls', 'LAY_Landmarks', 'LAY_Props', 'LAY_Proxies_TestOnly', 'LAY_Cameras_Lights'):
    C[n] = bpy.data.collections.new(n); parent.children.link(C[n])

kit = {o.name: o for o in bpy.data.objects if o.name.startswith('ENV_Temple_') and o.type == 'MESH'}
counter = {}


def place(asset_parts, M, coll):
    """Linked duplicates (shared mesh data) of one asset's parts at matrix M."""
    out = []
    for p in asset_parts:
        src = kit['ENV_Temple_' + p]
        counter[p] = counter.get(p, 0) + 1
        o = bpy.data.objects.new(f'LAY_{p}_{counter[p]:03d}', src.data)
        o.matrix_world = M
        coll.objects.link(o)
        out.append(o)
    return out


# ---------------------------------------------------------------- floor field + border ring
FT = -0.30     # tile pivot is bottom face; top surface must sit at y = 0
vars_, w = ['A', 'B', 'C', 'D'], [0.30, 0.20, 0.25, 0.25]
tiles = 0
for ix in range(18):
    for iz in range(18):
        v = rng.choices(vars_, w)[0]
        place(['Floor_' + v], xf((-17 + 2 * ix, FT, -17 + 2 * iz), 90 * rng.randrange(4)), C['LAY_Floor']); tiles += 1
for k in range(18):
    c = -17 + 2 * k
    place(['FloorBorder_Straight_A'], xf((19, FT, c), 90), C['LAY_Floor'])
    place(['FloorBorder_Straight_A'], xf((-19, FT, c), 270), C['LAY_Floor'])
    place(['FloorBorder_Straight_A'], xf((c, FT, 19), 0), C['LAY_Floor'])
    place(['FloorBorder_Straight_A'], xf((c, FT, -19), 180), C['LAY_Floor'])
for sx in (-1, 1):
    for sz in (-1, 1):
        place(['FloorBorder_Corner_A'], xf((19 * sx, FT, 19 * sz), 90 * rng.randrange(4)), C['LAY_Floor'])

# ---------------------------------------------------------------- perimeter walls (3 m, inner faces at +-19.5)
ARCH_X = 4.0
for c in range(-18, 19, 4):
    for (side, pos, yaw) in (('+Z', (c, 0, 20), 0), ('-Z', (c, 0, -20), 180), ('+X', (20, 0, c), 90), ('-X', (-20, 0, c), 270)):
        if side == '+Z' and c in (2, 6):
            continue            # arch opening (8 m)
        v = 'B' if rng.random() < 0.28 else 'A'
        place(['Wall_' + v], xf(pos, yaw), C['LAY_Walls'])

# ---------------------------------------------------------------- landmarks (far side = -X / +Z)
place(['Arch_A_PierL', 'Arch_A_PierR', 'Arch_A_Span'], xf((ARCH_X, 0, 20), 0), C['LAY_Landmarks'])
place(['Pillar_A'], xf((-15.0, 0, 4.0), 20), C['LAY_Landmarks'])
place(['Pillar_B'], xf((-4.5, 0, 14.5), 10), C['LAY_Landmarks'])
place(['Pillar_C'], xf((8.5, 0, 14.0), 0), C['LAY_Landmarks'])
place(['Pillar_D'], xf((-2.0, 0, -12.5), 30), C['LAY_Landmarks'])   # broken stump on the NEAR side: low, never hides the combat zone
DAIS = xf((-13.8, 0, 13.8), 135)                                    # front (+Y) faces the arena centre
for lx in (-2.0, 2.0):
    place(['Platform_A'], DAIS @ Matrix.Translation((lx, 0, 0)), C['LAY_Landmarks'])
place(['Stairs_A'], DAIS @ Matrix.Translation((0, 4.0, 0)) @ Matrix.Rotation(math.pi, 4, 'Z'), C['LAY_Landmarks'])
place(['Altar_A'], DAIS @ Matrix.Translation((0, -0.4, 0.8)), C['LAY_Landmarks'])

# ---------------------------------------------------------------- supporting props
brazier_pts = []
for (lx, ly) in ((-3.5, 2.3), (3.5, 2.3)):
    M = DAIS @ Matrix.Translation((lx, ly, 0.8)); place(['Brazier_A'], M, C['LAY_Props']); brazier_pts.append(M @ Vector((0, 0, 1.25)))
for pos in ((-1.4, 0, 17.6), (9.4, 0, 17.6)):
    M = xf(pos); place(['Brazier_A'], M, C['LAY_Props']); brazier_pts.append(M @ Vector((0, 0, 1.25)))
place(['Rubble_A'], xf((-17.2, 0, 9.0), 40), C['LAY_Props'])
place(['Rubble_B'], xf((-17.0, 0, -4.0), 100), C['LAY_Props'])
place(['Rubble_A'], xf((12.8, 0, 16.0), 200), C['LAY_Props'])
place(['Rubble_B'], xf((14.5, 0, 12.5), 15), C['LAY_Props'])
place(['ColumnDrum_A'], xf((-4.6, 0, -13.8), 70), C['LAY_Props'])
for (pos, yaw) in (((-19.40, 0.35, -3.0), 90), ((-19.40, 0.35, 7.0), 90), ((-9.0, 0.35, 19.40), 180), ((13.0, 0.35, 19.40), 180)):
    place(['Banner_A'], xf(pos, yaw), C['LAY_Props'])

# ---------------------------------------------------------------- test-only proxies (never exported)
def proxy_mat(name, rgb, emit=False):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); pb = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(pb.outputs[0], out.inputs[0])
    pb.inputs['Base Color'].default_value = (*rgb, 1); pb.inputs['Roughness'].default_value = 0.6
    return m


def make_figure(name, height, mat, coll):
    bm = bmesh.new()
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=0.30, radius2=0.22, depth=height * 0.76,
                              matrix=Matrix.Translation((0, 0, height * 0.38)))
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=12, radius=0.16, matrix=Matrix.Translation((0, 0, height * 0.88)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0, 0.26, height * 0.55)) @ Matrix.Diagonal((0.09, 0.30, 0.09, 1)))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(mat); coll.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    return o


def sector(name, radius, half_deg, mat, coll, ring=None):
    bm = bmesh.new(); n = 28
    c = bm.verts.new((0, 0, 0))
    vs = [bm.verts.new((radius * math.sin(math.radians(-half_deg + 2 * half_deg * i / n)), radius * math.cos(math.radians(-half_deg + 2 * half_deg * i / n)), 0)) for i in range(n + 1)]
    for i in range(n):
        bm.faces.new((c, vs[i + 1], vs[i]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(mat); coll.objects.link(o); return o


def outline(name, radius, half_deg, w, mat, coll):
    bm = bmesh.new(); n = 28
    pts_o = [(radius * math.sin(math.radians(-half_deg + 2 * half_deg * i / n)), radius * math.cos(math.radians(-half_deg + 2 * half_deg * i / n))) for i in range(n + 1)]
    def strip(a, b):
        d = Vector((b[0] - a[0], b[1] - a[1])).normalized(); nrm = Vector((-d.y, d.x)) * w / 2
        v = [bm.verts.new((a[0] + nrm.x, a[1] + nrm.y, 0)), bm.verts.new((b[0] + nrm.x, b[1] + nrm.y, 0)),
             bm.verts.new((b[0] - nrm.x, b[1] - nrm.y, 0)), bm.verts.new((a[0] - nrm.x, a[1] - nrm.y, 0))]
        bm.faces.new(v)
    for i in range(n):
        strip(pts_o[i], pts_o[i + 1])
    strip((0, 0), pts_o[0]); strip((0, 0), pts_o[-1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(mat); coll.objects.link(o); return o


mp = proxy_mat('PROXY_Player', (0.62, 0.66, 0.72)); me_ = proxy_mat('PROXY_Enemy', (0.30, 0.06, 0.05))
def emit_alpha(name, rgb, alpha):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial'); em = nt.nodes.new('ShaderNodeEmission'); tr = nt.nodes.new('ShaderNodeBsdfTransparent'); mx = nt.nodes.new('ShaderNodeMixShader')
    em.inputs['Color'].default_value = (*rgb, 1); mx.inputs[0].default_value = alpha
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2]); nt.links.new(mx.outputs[0], out.inputs[0])
    try:
        m.surface_render_method = 'BLENDED'
    except Exception:
        m.blend_method = 'BLEND'
    m.use_backface_culling = False
    return m


import kitlib as K
tf = emit_alpha('PROXY_Telegraph_Fill', K.hexc('#27DCD1')[:3], 0.25)   # spec: fill #27DCD1 ~22-28 %
te = emit_alpha('PROXY_Telegraph_Edge', K.hexc('#9BFFF6')[:3], 0.9)    # spec: edge #9BFFF6
P = C['LAY_Proxies_TestOnly']
player = make_figure('PROXY_Player', 1.78, mp, P)
enemy = make_figure('PROXY_Enemy', 1.78, me_, P)
tel_fill = sector('PROXY_Telegraph_Fill', 2.4 * 0.62, 58, tf, P)
tel_edge = outline('PROXY_Telegraph_Edge', 2.4, 58, 0.07, te, P)
tel_fill.parent = enemy; tel_edge.parent = enemy
tel_fill.location = tel_edge.location = (0, 0, 0.04)
tel_fill['note'] = 'visual proxy only - NOT the Unity telegraph implementation'


def set_proxies(pp, ep):
    """Player at pp, enemy at ep (Unity xz); enemy faces the player."""
    player.location = U(pp[0], 0, pp[1]); enemy.location = U(ep[0], 0, ep[1])
    d = Vector((pp[0] - ep[0], pp[1] - ep[1]))
    yaw = math.degrees(math.atan2(d.x, d.y))       # Unity yaw: clockwise from +Z
    enemy.rotation_euler = (0, 0, -math.radians(yaw))
    d2 = Vector((ep[0] - pp[0], ep[1] - pp[1]))
    player.rotation_euler = (0, 0, -math.atan2(d2.x, d2.y))


set_proxies((0, 0), (0, 8))     # PrototypeArena spawns
# parenting changes world matrix handling: keep telegraph local
tel_fill.matrix_parent_inverse = Matrix.Identity(4); tel_edge.matrix_parent_inverse = Matrix.Identity(4)

# ---------------------------------------------------------------- cameras
def make_cam(name, pos_u, target_u, ortho, res, coll):
    cd = bpy.data.cameras.new(name); cd.type = 'ORTHO'; cd.ortho_scale = ortho; cd.clip_start = 0.1; cd.clip_end = 200
    o = bpy.data.objects.new(name, cd); coll.objects.link(o)
    o.location = U(*pos_u)
    d = U(*target_u) - o.location
    o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    o['res'] = res
    return o


CL = C['LAY_Cameras_Lights']
OFF = (12, 18, -12)
ORTHO_11 = 2 * 11 * 16 / 9
def gameplay_cam(name, player_xz):
    px, pz = player_xz
    return make_cam(name, (px + OFF[0], OFF[1], pz + OFF[2]), (px, 0, pz), ORTHO_11, (1920, 1080), CL)
cam_a = gameplay_cam('CAM_Gameplay_Center', (0, 0))
cam_b = gameplay_cam('CAM_Gameplay_Dais', (-8.0, 8.0))
cam_c = gameplay_cam('CAM_Gameplay_Arch', (3.0, 9.0))
cam_o = make_cam('CAM_Overview', (12, 18, -12), (0, 0, 0), 58, (1600, 1200), CL)
cam_p = make_cam('CAM_Plan_TopDown', (0, 60, 0), (0, 0, 0), 46, (1400, 1400), CL)
cam_p.rotation_euler = (0, 0, 0)
sc.camera = cam_a
for c in (cam_a, cam_b, cam_c, cam_o):
    c['pitch_deg'] = round(math.degrees(math.atan2(18, math.hypot(12, 12))), 2); c['yaw_deg'] = 45.0

# ---------------------------------------------------------------- lighting: warm directional key + soft charcoal fill
sun = bpy.data.lights.new('SUN_Key', 'SUN'); sun.energy = 3.8; sun.color = (1.0, 0.91, 0.78); sun.angle = math.radians(2.5)
so = bpy.data.objects.new('SUN_Key', sun); CL.objects.link(so)
el = math.radians(52)
travel_u = Vector((0.31 * math.cos(el), -math.sin(el), 0.95 * math.cos(el))).normalized()   # light travel direction (Unity space)
travel_b = Vector((travel_u.x, travel_u.z, travel_u.y))
so.rotation_euler = travel_b.to_track_quat('-Z', 'Y').to_euler()
for i, pt in enumerate(brazier_pts):
    L = bpy.data.lights.new(f'LIGHT_Ember_{i}', 'POINT'); L.energy = 110; L.color = (1.0, 0.52, 0.18); L.shadow_soft_size = 0.25
    lo = bpy.data.objects.new(f'LIGHT_Ember_{i}', L); lo.location = pt; CL.objects.link(lo)
altar_core = DAIS @ Vector((0, -0.4 + 0.1, 0.8 + 2.6))
L = bpy.data.lights.new('LIGHT_AltarCore', 'POINT'); L.energy = 220; L.color = (1.0, 0.55, 0.2); L.shadow_soft_size = 0.2
lo = bpy.data.objects.new('LIGHT_AltarCore', L); lo.location = altar_core; CL.objects.link(lo)

wd = bpy.data.worlds.get('TempleLookDevWorld') or bpy.data.worlds.new('TempleLookDevWorld')
wd.use_nodes = True
nt = wd.node_tree; nt.nodes.clear()
wo = nt.nodes.new('ShaderNodeOutputWorld')
b_amb = nt.nodes.new('ShaderNodeBackground'); b_amb.inputs['Color'].default_value = (0.27, 0.27, 0.285, 1); b_amb.inputs['Strength'].default_value = 0.85   # neutral charcoal fill
b_dark = nt.nodes.new('ShaderNodeBackground'); b_dark.inputs['Color'].default_value = (0.020, 0.018, 0.017, 1); b_dark.inputs['Strength'].default_value = 1.0   # out-of-bounds backdrop: darker & calmer than play space
lp = nt.nodes.new('ShaderNodeLightPath'); mx = nt.nodes.new('ShaderNodeMixShader')
nt.links.new(lp.outputs['Is Camera Ray'], mx.inputs[0]); nt.links.new(b_amb.outputs[0], mx.inputs[1]); nt.links.new(b_dark.outputs[0], mx.inputs[2])
nt.links.new(mx.outputs[0], wo.inputs[0])
sc.world = wd

# ---------------------------------------------------------------- clear-zone verification (plan view, numeric)
def hull(points):
    pts = sorted(set(map(tuple, np.round(points, 4))))
    if len(pts) <= 2:
        return pts
    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo = []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    up = []
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def dist_origin(poly):
    # point-in-polygon (origin) + distance to edges
    inside = True
    n = len(poly)
    best = 1e9
    for i in range(n):
        a, b = np.array(poly[i]), np.array(poly[(i + 1) % n])
        ab = b - a
        t = max(0.0, min(1.0, float(np.dot(-a, ab) / max(np.dot(ab, ab), 1e-12))))
        d = float(np.linalg.norm(a + ab * t))
        best = min(best, d)
        if ab[0] * (-a[1]) - ab[1] * (-a[0]) < 0:
            inside = False
    return 0.0 if inside else best


vcache = {}
rows = []
for o in bpy.data.objects:
    if not o.name.startswith('LAY_') or o.type != 'MESH' or o.users_collection[0].name in ('LAY_Floor',):
        continue
    if o.users_collection[0].name == 'LAY_Proxies_TestOnly':
        continue
    me = o.data
    if me.name not in vcache:
        a = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', a); vcache[me.name] = a.reshape(-1, 3)
    v = vcache[me.name]
    Mw = np.array(o.matrix_world)
    wv = (v @ Mw[:3, :3].T) + Mw[:3, 3]
    poly = hull(wv[:, :2])
    rows.append((o.name, round(dist_origin(poly), 2), round(float(wv[:, 2].max()), 2)))
rows.sort(key=lambda r: r[1])
inside = [r for r in rows if r[1] < 10.0]
report = dict(clear_radius_m=10.0, min_distance_m=rows[0][1], nearest=rows[:8], objects_checked=len(rows), objects_inside_zone=inside,
              floor_tiles=tiles, instance_counts=counter)
os.makedirs(os.path.dirname(OUTJ), exist_ok=True)
json.dump(report, open(OUTJ, 'w'), indent=1)
print('CLEARZONE min dist', rows[0], 'inside:', inside, 'checked', len(rows))
print('NEAREST', rows[:8])

bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)   # drop duplicate proxy materials from reruns
bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('STAGE3_DONE')

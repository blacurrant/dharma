# ENV_Temple_Central_Medallion — Blender 5.x Headless Authoring
# Faithfully rebuilt to match Reference 1 & Reference 2.
# Monumental 7.80 m circular sandstone altar medallion with stepped 3D tiers,
# 4 cardinal roundel bosses, recessed drainage canals, 24 scalloped outer teeth,
# and authentic chiseled relief.
import bpy
import bmesh
import math
import os
import json
import shutil
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion'
TEX = f'{ROOT}/textures'
MOD = f'{ROOT}/models'
os.makedirs(MOD, exist_ok=True)
BLEND = f'{ROOT}/TempleEnvironmentKit_medallion.blend'
STAGING = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion'

NAME = 'ENV_Temple_Central_Medallion'
RADIUS = 3.90          # 7.80 m diameter
NSEG = 96              # 96 radial segments (divisible by 8, 16, 24, 32)
Z_BOTTOM = -0.100      # 10 cm thick base foundation
Z_LIP = 0.015          # outer rim lip at ~1.5 cm

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0


def make_pbr(name, base, nrm, mask):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']

    # Base Color
    img_c = bpy.data.images.load(base)
    tex_c = nt.nodes.new('ShaderNodeTexImage')
    tex_c.image = img_c
    tex_c.image.colorspace_settings.name = 'sRGB'
    nt.links.new(tex_c.outputs['Color'], bsdf.inputs['Base Color'])

    # Normal Map
    img_n = bpy.data.images.load(nrm)
    img_n.colorspace_settings.name = 'Non-Color'
    tex_n = nt.nodes.new('ShaderNodeTexImage')
    tex_n.image = img_n
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nmap.inputs['Strength'].default_value = 1.40
    nt.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])

    # Mask Map (URP: R=0, G=AO, B=0, A=Smoothness)
    img_m = bpy.data.images.load(mask)
    img_m.colorspace_settings.name = 'Non-Color'
    img_m.alpha_mode = 'CHANNEL_PACKED'
    tex_m = nt.nodes.new('ShaderNodeTexImage')
    tex_m.image = img_m

    # Roughness = 1.0 - Smoothness (from Alpha channel)
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(tex_m.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = 0.0
    mat.use_backface_culling = True
    return mat


MAT = make_pbr(
    'M_Temple_Central_Medallion',
    f'{TEX}/{NAME}_BaseColor.png',
    f'{TEX}/{NAME}_Normal.png',
    f'{TEX}/{NAME}_Mask.png',
)


# Radial stations (r_norm, z_base):
# r_norm is normalized to RADIUS (3.90 m)
# Gives the stepped architectural profile seen in Ref 1 & Ref 2
RINGS_SPEC = [
    # Center to Altar Well
    (0.000, 0.065),   # central hub/boss
    (0.050, 0.058),
    (0.100, 0.045),   # ritual well basin floor
    (0.160, 0.045),
    (0.205, 0.048),
    # Raised Altar Collar / Rim (Ref 2 signature)
    (0.215, 0.078),   # steep rise
    (0.245, 0.082),   # top crest of altar rim
    (0.270, 0.072),   # bevel outer drop
    # Inner Canal (recessed shadow trench)
    (0.285, 0.012),   # drop into inner canal
    (0.315, 0.010),   # floor of canal
    (0.345, 0.014),
    # Roundel Zone Base
    (0.365, 0.042),   # rise out of canal
    (0.400, 0.044),
    (0.440, 0.042),
    (0.480, 0.045),
    (0.520, 0.045),   # roundel center radius
    (0.560, 0.045),
    (0.600, 0.042),
    (0.640, 0.044),
    (0.675, 0.040),
    # Outer Canal (recessed shadow trench)
    (0.695, 0.008),   # drop into outer canal
    (0.725, 0.006),   # floor of canal
    (0.755, 0.010),
    # Outer Glyph Frieze Band (Ref 1 signature)
    (0.775, 0.038),   # rise out of canal
    (0.815, 0.040),   # glyph band surface
    (0.855, 0.040),
    (0.895, 0.038),
    (0.930, 0.035),
    # Scalloped Outer Toothed Rim (Ref 1 signature)
    (0.955, 0.028),   # beveled outer lip
    (0.980, 0.020),
    (1.000, Z_LIP),   # outer edge flush with courtyard pavers
]


def eval_z(x, y, r_norm, z_base):
    """Adds 3D relief for the 4 cardinal roundels, slab joints, and fault displacement."""
    z = z_base
    r = math.sqrt(x * x + y * y)
    th = math.atan2(y, x)

    # 1. 4 Cardinal Roundels: Raised collar and center boss at (+-r_c, 0) and (0, +-r_c)
    r_c_m = 0.520 * RADIUS  # ~2.03 m
    roundel_rad_m = 0.128 * RADIUS  # ~0.50 m
    for ang in (0.0, 0.5 * math.pi, math.pi, 1.5 * math.pi):
        uc = r_c_m * math.cos(ang)
        vc = r_c_m * math.sin(ang)
        dc = math.sqrt((x - uc) ** 2 + (y - vc) ** 2)
        if dc < roundel_rad_m:
            rho = dc / roundel_rad_m
            # Raised outer stone collar for the roundel (rises to z ~ 0.065 m)
            if 0.78 <= rho <= 1.0:
                t_rim = math.sin((rho - 0.78) / 0.22 * math.pi)
                z += 0.022 * t_rim
            elif rho < 0.78:
                # Recessed carved interior with raised eye/boss in center
                z -= 0.006
                if rho < 0.22:
                    z += 0.016 * math.cos(rho / 0.22 * 0.5 * math.pi)

    # 2. 8 Primary Radial Slab Joints (0.8 cm groove where joints meet)
    th_slab = (th / math.tau * 8.0) % 1.0
    d_joint = min(th_slab, 1.0 - th_slab) * (math.tau / 8.0) * r
    if d_joint < 0.06 and r > 0.40 and r < 3.85:
        z -= 0.008 * (1.0 - d_joint / 0.06)

    # 3. Geological displacement across Major Crack 1 (+1.5 mm step)
    if (x + y) > -0.20 and r < 3.85:
        z += 0.002

    return z


def eval_rim_radius(r_norm, i_seg):
    """Scalloped outer teeth (24 modular blocks) matching Reference 1."""
    if r_norm < 0.94:
        return r_norm * RADIUS
    # Modulate outer rim with 24 scalloped teeth and notched joints
    a = i_seg / NSEG * math.tau
    tooth = math.sin(a * 12.0) ** 2  # 24 peaks/troughs
    # Scallop depth ~ 2.5 cm at tooth joints
    t_rim = (r_norm - 0.94) / 0.06
    scallop = 1.0 - 0.010 * (1.0 - tooth) * t_rim
    # Chipped corner notch
    chip = 0.005 * math.sin(a * 7.0 + 1.2) * t_rim
    return r_norm * RADIUS * scallop - chip


def uv_xy(x, y):
    return (0.5 + 0.5 * x / RADIUS, 0.5 + 0.5 * y / RADIUS)


def build():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new('UVMap')
    nrings = len(RINGS_SPEC)

    # Center vertex
    centre = bm.verts.new((0.0, 0.0, RINGS_SPEC[0][1]))
    rings = [[centre] * NSEG]

    # Generate concentric vertex rings
    for ri in range(1, nrings):
        r_n, z_base = RINGS_SPEC[ri]
        row = []
        for i in range(NSEG):
            r = eval_rim_radius(r_n, i)
            a = i / NSEG * math.tau
            x = r * math.cos(a)
            y = r * math.sin(a)
            z = eval_z(x, y, r_n, z_base)
            row.append(bm.verts.new((x, y, z)))
        rings.append(row)

    def add_face(vs, uvs):
        f = bm.faces.new(vs)
        f.smooth = True
        for loop, uv in zip(f.loops, uvs):
            loop[uv_lay].uv = uv
        return f

    # Inner triangle fan around central hub
    for i in range(NSEG):
        j = (i + 1) % NSEG
        v0, v1, v2 = rings[0][0], rings[1][i], rings[1][j]
        add_face(
            (v0, v1, v2),
            (uv_xy(0, 0), uv_xy(v1.co.x, v1.co.y), uv_xy(v2.co.x, v2.co.y))
        )

    # Concentric quad strips
    for ri in range(1, nrings - 1):
        for i in range(NSEG):
            j = (i + 1) % NSEG
            a = rings[ri][i]
            b = rings[ri][j]
            c = rings[ri + 1][j]
            d = rings[ri + 1][i]
            add_face(
                (a, b, c, d),
                (uv_xy(a.co.x, a.co.y), uv_xy(b.co.x, b.co.y),
                 uv_xy(c.co.x, c.co.y), uv_xy(d.co.x, d.co.y))
            )

    # Bottom foundation disc (Z_BOTTOM = -0.10 m)
    bot_c = bm.verts.new((0.0, 0.0, Z_BOTTOM))
    bot_ring = []
    for i in range(NSEG):
        x, y = rings[-1][i].co.x, rings[-1][i].co.y
        bot_ring.append(bm.verts.new((x, y, Z_BOTTOM)))

    for i in range(NSEG):
        j = (i + 1) % NSEG
        a, b = bot_ring[i], bot_ring[j]
        # Inverted winding for bottom face (facing -Z)
        add_face(
            (bot_c, b, a),
            (uv_xy(0, 0), uv_xy(b.co.x, b.co.y), uv_xy(a.co.x, a.co.y))
        )

    # Side walls (connecting top outer rim to bottom foundation)
    for i in range(NSEG):
        j = (i + 1) % NSEG
        t0, t1 = rings[-1][i], rings[-1][j]
        b0, b1 = bot_ring[i], bot_ring[j]
        add_face(
            (t0, t1, b1, b0),
            (uv_xy(t0.co.x, t0.co.y), uv_xy(t1.co.x, t1.co.y),
             uv_xy(b1.co.x, b1.co.y), uv_xy(b0.co.x, b0.co.y))
        )

    bm.verts.ensure_lookup_table()
    bm.faces.ensure_lookup_table()
    bm.normal_update()

    # Mark sharp edges along steep architectural lips (angle > 35 deg)
    for e in bm.edges:
        if len(e.link_faces) == 2:
            dot = e.link_faces[0].normal.dot(e.link_faces[1].normal)
            if dot < 0.65:
                e.smooth = False

    bmesh.ops.triangulate(bm, faces=bm.faces[:])

    me = bpy.data.meshes.new(NAME)
    bm.to_mesh(me)
    bm.free()

    ob = bpy.data.objects.new(NAME, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(MAT)
    for p in me.polygons:
        p.use_smooth = True

    ob.location = (0, 0, 0)
    ob.rotation_euler = (0, 0, 0)
    ob.scale = (1, 1, 1)
    return ob


print("Building 3D medallion mesh...")
ob = build()


def export_fbx(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={'MESH'},
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        use_triangles=True,
        use_tspace=True,
        path_mode='RELATIVE',
        embed_textures=False,
        bake_anim=False,
        add_leaf_bones=False,
        use_custom_props=False,
    )


src_fbx = f'{MOD}/{NAME}.fbx'
stg_fbx = f'{STAGING}/Models/{NAME}.fbx'
export_fbx(src_fbx)
export_fbx(stg_fbx)
shutil.copy2(src_fbx, f'{STAGING}/{NAME}.fbx')

# Copy textures to staging
for suffix in ('BaseColor', 'Normal', 'Mask'):
    src = f'{TEX}/{NAME}_{suffix}.png'
    dst_dir = f'{STAGING}/Textures'
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, f'{dst_dir}/{NAME}_{suffix}.png')
    shutil.copy2(src, f'{STAGING}/{NAME}_{suffix}.png')

bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
stat = dict(
    name=NAME,
    tris=len(ob.data.polygons),
    verts=len(ob.data.vertices),
    bbox_min=[round(min(c[i] for c in bb), 4) for i in range(3)],
    bbox_max=[round(max(c[i] for c in bb), 4) for i in range(3)],
    dims_m=[round(max(c[i] for c in bb) - min(c[i] for c in bb), 4) for i in range(3)],
    diameter_m=round(max(c[0] for c in bb) - min(c[0] for c in bb), 4),
    thickness_m=round(max(c[2] for c in bb) - min(c[2] for c in bb), 4),
    lip_z=Z_LIP,
    altar_crest_z=0.082,
    materials=[MAT.name],
    fbx_src=src_fbx,
    fbx_staging=stg_fbx,
)
os.makedirs(f'{ROOT}/evidence', exist_ok=True)
with open(f'{ROOT}/evidence/geometry_stats.json', 'w') as f:
    json.dump(stat, f, indent=2)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
print('STAT', json.dumps(stat, indent=2))
print('Saved', BLEND)

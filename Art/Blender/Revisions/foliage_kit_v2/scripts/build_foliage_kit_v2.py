# Production-ready 3D Foliage & Ground Transition Asset Kit Authoring Script
# Authors 7 assets:
#   1. ENV_Temple_Foliage_Clump_A (Medium/Large Stylized Foliage Clump)
#   2. ENV_Temple_Foliage_Clump_B (Low-spreading Stylized Foliage Mound)
#   3. ENV_Temple_Foliage_Creeper_Wall (Wall-conforming Clinging Ivy Creeper)
#   4. ENV_Temple_Foliage_Creeper_Column (Column-conforming Clinging Ivy Drape)
#   5. ENV_Temple_Ground_DirtPatch_A (Curved Dirt/Sediment Accumulation Patch)
#   6. ENV_Temple_Ground_DirtPatch_B (Linear Seam Wall-Base Dirt Drift)
#   7. ENV_Temple_Ground_CrackedMortar_C (Fractured Flagstone with Mortar Gravel Bed & Weed Sprout)

import bpy, bmesh, math, random, os, json
from mathutils import Vector, Matrix, noise

OUT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/foliage_kit_v2'
TEX_DIR = f'{OUT}/textures'
MODELS_DIR = f'{OUT}/models'
os.makedirs(MODELS_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# ----------------- Atlas UV Helper Functions -----------------
# Foliage Atlas (2048 x 2048):
# - V in [0.5, 1.0]: 8 Leaf Columns (u in [k*0.125, (k+1)*0.125])
# - V in [0.25, 0.5]: Cloud Lobe Body (u in [0, 1])
# - V in [0.0, 0.25], U in [0.0, 0.5]: Woody Vine / Bark
# - V in [0.0, 0.25], U in [0.5, 1.0]: 4 Ivy Leaf Cells (u in [0.5 + cell*0.125, 0.5 + (cell+1)*0.125])

def fol_leaf_uv(col, u_norm, t_norm):
    u = col * 0.125 + 0.012 + u_norm * 0.101
    v = 0.50 + 0.010 + t_norm * 0.480
    return (u, v)

def fol_cloud_uv(ang_norm, h_norm):
    u = ang_norm % 1.0
    v = 0.26 + 0.23 * max(0.0, min(1.0, h_norm))
    return (u, v)

def fol_bark_uv(u_norm, v_norm):
    u = 0.015 + (u_norm % 1.0) * 0.470
    v = 0.010 + max(0.0, min(1.0, v_norm)) * 0.230
    return (u, v)

def fol_ivy_uv(cell, u_norm, t_norm):
    u = 0.50 + cell * 0.125 + 0.012 + u_norm * 0.101
    v = 0.010 + t_norm * 0.230
    return (u, v)

# Ground Transition Atlas (2048 x 2048):
# - V in [0.5, 1.0]: Weathered Sandstone Flagstone
# - V in [0.0, 0.5], U in [0.0, 0.6]: Sandy Soil Drift
# - V in [0.0, 0.5], U in [0.6, 1.0]: Mortar Crumble & Gravel Bed

def gnd_stone_uv(x, y, scale=0.5):
    u = (x * scale + 0.5) % 0.96 + 0.02
    v = 0.52 + ((y * scale + 0.5) % 0.96) * 0.46
    return (u, v)

def gnd_soil_uv(x, y, scale=0.4):
    u = ((x * scale + 0.5) % 0.96) * 0.58 + 0.01
    v = 0.02 + ((y * scale + 0.5) % 0.96) * 0.46
    return (u, v)

def gnd_gravel_uv(x, y, scale=0.8):
    u = 0.61 + ((x * scale + 0.5) % 0.96) * 0.37
    v = 0.02 + ((y * scale + 0.5) % 0.96) * 0.46
    return (u, v)


# ----------------- Mesh Builder Class -----------------
class MeshBuilder:
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.cn = self.bm.verts.layers.float_vector.new('custom_normal')

    def add_vert(self, co, normal):
        v = self.bm.verts.new(co)
        v[self.cn] = Vector(normal).normalized()
        return v

    def add_face(self, verts, uvs):
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f


# ----------------- Materials Setup -----------------
def create_pbr_material(name, base_tex, norm_tex, mask_tex):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    
    # BaseColor
    tex_col = nt.nodes.new('ShaderNodeTexImage')
    tex_col.image = bpy.data.images.load(base_tex)
    tex_col.image.colorspace_settings.name = 'sRGB'
    nt.links.new(tex_col.outputs['Color'], bsdf.inputs['Base Color'])
    
    # Normal Map
    tex_norm = nt.nodes.new('ShaderNodeTexImage')
    tex_norm.image = bpy.data.images.load(norm_tex)
    tex_norm.image.colorspace_settings.name = 'Non-Color'
    norm_node = nt.nodes.new('ShaderNodeNormalMap')
    norm_node.inputs['Strength'].default_value = 1.0
    nt.links.new(tex_norm.outputs['Color'], norm_node.inputs['Color'])
    nt.links.new(norm_node.outputs['Normal'], bsdf.inputs['Normal'])
    
    # Mask (R=Metal, G=AO, A=Smoothness)
    tex_mask = nt.nodes.new('ShaderNodeTexImage')
    tex_mask.image = bpy.data.images.load(mask_tex)
    tex_mask.image.colorspace_settings.name = 'Non-Color'
    tex_mask.image.alpha_mode = 'CHANNEL_PACKED'
    
    # Invert Roughness from Smoothness (Alpha)
    inv = nt.nodes.new('ShaderNodeMath')
    inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0
    nt.links.new(tex_mask.outputs['Alpha'], inv.inputs[1])
    nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
    
    mat.use_backface_culling = False
    return mat

mat_foliage = create_pbr_material(
    'M_Temple_Foliage',
    f'{TEX_DIR}/ENV_Temple_Foliage_BaseColor.png',
    f'{TEX_DIR}/ENV_Temple_Foliage_Normal.png',
    f'{TEX_DIR}/ENV_Temple_Foliage_Mask.png'
)

mat_ground = create_pbr_material(
    'M_Temple_GroundTransition',
    f'{TEX_DIR}/ENV_Temple_GroundTransition_BaseColor.png',
    f'{TEX_DIR}/ENV_Temple_GroundTransition_Normal.png',
    f'{TEX_DIR}/ENV_Temple_GroundTransition_Mask.png'
)


# ----------------- Geometric Primitives -----------------

# 1. Cloud Lobe Hull (Convex organic volume hull with radial spherical normals)
def make_cloud_lobe(builder, center, radii, seed, subdiv=2, noise_amp=0.18, up_bias=0.35, z_min=0.0):
    c = Vector(center)
    tmp = bmesh.new()
    bmesh.ops.create_icosphere(tmp, subdivisions=subdiv, radius=1.0)
    
    vert_info = {}
    for tv in tmp.verts:
        d = tv.co.copy()
        n = noise.noise(d * 1.8 + Vector((seed, seed * 0.73, seed * 1.41))) * noise_amp
        n += noise.noise(d * 4.2 + Vector((seed * 2.1, 7.3, 11.2))) * (noise_amp * 0.4)
        scale = 1.0 + n
        
        # Ellipsoidal scaling
        pos = Vector((d.x * radii[0] * scale, d.y * radii[1] * scale, d.z * radii[2] * scale))
        world_p = c + pos
        
        # Ground clamping for base lobes
        if world_p.z < z_min:
            world_p.z = z_min + (world_p.z - z_min) * 0.15
            
        # Radial spherical normal oriented from lobe center + upward bias
        grad = Vector((d.x / radii[0], d.y / radii[1], d.z / radii[2])).normalized()
        normal = (grad * (1.0 - up_bias) + Vector((0, 0, 1)) * up_bias).normalized()
        vert_info[tv.index] = (world_p, normal, d)
        
    z_min_val = min(v[0].z for v in vert_info.values())
    z_max_val = max(v[0].z for v in vert_info.values())
    
    new_verts = {idx: builder.add_vert(p, n) for idx, (p, n, d) in vert_info.items()}
    
    for tf in tmp.faces:
        idx_list = [l.vert.index for l in tf.loops]
        uvs = []
        for idx in idx_list:
            p, n, d = vert_info[idx]
            ang = math.atan2(d.y, d.x) / (2 * math.pi) + 0.5
            h = (p.z - z_min_val) / max(1e-4, z_max_val - z_min_val)
            uvs.append(fol_cloud_uv(ang, h))
            
        builder.add_face([new_verts[i] for i in idx_list], uvs)
        
    tmp.free()
    return c, Vector(radii)

# 2. Tangent Silhouette Shell Cards (Curved leaf cluster plates that hug the volume contour)
def make_tangent_shell_cards(builder, center, radii, count, seed, col_list, card_size=(0.22, 0.35), up_bias=0.35, z_cutoff=0.05):
    c = Vector(center)
    rng = random.Random(seed)
    golden_ratio = (1 + math.sqrt(5)) / 2
    
    for i in range(count):
        # Fibonacci sphere sampling for even spherical distribution
        theta = 2 * math.pi * i / golden_ratio
        phi = math.acos(1 - 2 * (i + 0.5) / count)
        
        dx = math.sin(phi) * math.cos(theta)
        dy = math.sin(phi) * math.sin(theta)
        dz = math.cos(phi)
        d = Vector((dx, dy, dz)).normalized()
        
        # Position on the ellipsoid hull
        pos = c + Vector((d.x * radii[0], d.y * radii[1], d.z * radii[2]))
        if pos.z < z_cutoff:
            continue
            
        # Spherical radial normal
        rad_norm = (d * (1.0 - up_bias) + Vector((0, 0, 1)) * up_bias).normalized()
        
        # Tangent vectors: tangent along latitude and longitude
        tang_lat = Vector((-d.y, d.x, 0))
        if tang_lat.length < 1e-4:
            tang_lat = Vector((1, 0, 0))
        tang_lat.normalize()
        tang_long = d.cross(tang_lat).normalized()
        
        # Slight organic tilt & droop
        w = rng.uniform(card_size[0] * 0.75, card_size[0] * 1.25)
        length = rng.uniform(card_size[1] * 0.8, card_size[1] * 1.2)
        droop_v = Vector((0, 0, -1)) * (length * 0.25)
        
        # 4-quad (8 tri) curved petal plate hugging the hull
        # 3 rows of 3 vertices (curved shell)
        col = rng.choice(col_list)
        verts_grid = []
        for row_i, t in enumerate([0.0, 0.5, 1.0]):
            row_verts = []
            for col_i, s in enumerate([-0.5, 0.0, 0.5]):
                # Curve shell inward towards the hull
                cup = (1.0 - (s * 2)**2) * 0.04 - (t - 0.5)**2 * 0.03
                p_vert = pos + tang_long * (length * (t - 0.5)) + tang_lat * (w * s) + rad_norm * cup + droop_v * (t**2)
                # Normals smoothly inherited from cluster sphere
                v_obj = builder.add_vert(p_vert, rad_norm)
                row_verts.append(v_obj)
            verts_grid.append(row_verts)
            
        # Create 4 quad faces (as 2x2 grid)
        for r in range(2):
            for c_idx in range(2):
                v00 = verts_grid[r][c_idx]
                v10 = verts_grid[r+1][c_idx]
                v11 = verts_grid[r+1][c_idx+1]
                v01 = verts_grid[r][c_idx+1]
                
                u0 = fol_leaf_uv(col, c_idx * 0.5, r * 0.5)
                u1 = fol_leaf_uv(col, c_idx * 0.5, (r + 1) * 0.5)
                u2 = fol_leaf_uv(col, (c_idx + 1) * 0.5, (r + 1) * 0.5)
                u3 = fol_leaf_uv(col, (c_idx + 1) * 0.5, r * 0.5)
                builder.add_face([v00, v10, v11, v01], [u0, u1, u2, u3])

# 3. Gnarled Branch / Vine Stem Tube
def make_tube(builder, points, radii, sides=5, bark_tw=1.0):
    rings = []
    n_pts = len(points)
    for i, p in enumerate(points):
        # Tangent vector
        if i == 0:
            tang = (points[1] - points[0]).normalized()
        elif i == n_pts - 1:
            tang = (points[-1] - points[-2]).normalized()
        else:
            tang = (points[i+1] - points[i-1]).normalized()
            
        ref = Vector((0, 1, 0)) if abs(tang.dot(Vector((0, 1, 0)))) < 0.9 else Vector((1, 0, 0))
        u = tang.cross(ref).normalized()
        w = tang.cross(u).normalized()
        
        ring = []
        for k in range(sides):
            angle = 2 * math.pi * k / sides
            offset = u * math.cos(angle) + w * math.sin(angle)
            v_pos = p + offset * radii[i]
            v_norm = (offset * 0.75 + Vector((0, 0, 0.25))).normalized()
            ring.append((builder.add_vert(v_pos, v_norm), k))
        rings.append(ring)
        
    for i in range(n_pts - 1):
        for k in range(sides):
            a0, k0 = rings[i][k]
            a1, k1 = rings[i][(k + 1) % sides]
            b0, _ = rings[i+1][k]
            b1, _ = rings[i+1][(k + 1) % sides]
            
            u0 = k0 / sides
            u1 = (k0 + 1) / sides
            v0 = i / (n_pts - 1) * bark_tw
            v1 = (i + 1) / (n_pts - 1) * bark_tw
            
            uv0 = fol_bark_uv(u0, v0)
            uv1 = fol_bark_uv(u1, v0)
            uv2 = fol_bark_uv(u1, v1)
            uv3 = fol_bark_uv(u0, v1)
            builder.add_face([a0, a1, b1, b0], [uv0, uv1, uv2, uv3])

# 4. Sculpted Clinging Ivy Leaf Cluster (Fan of 3-to-5 lobed leaves adhering to surface)
IVY_CONTOUR = [
    (0.0, 0.0), (0.35, 0.15), (0.55, 0.45), (0.22, 0.60),
    (0.0, 1.0), (-0.22, 0.60), (-0.55, 0.45), (-0.35, 0.15)
]
def make_clinging_ivy_leaf(builder, base_pos, aim_dir, normal, size, cell, soft_norm=None, cup=0.08):
    a = aim_dir.normalized()
    n = normal.normalized()
    s = a.cross(n).normalized()
    a_real = n.cross(s).normalized()
    soft = soft_norm if soft_norm is not None else n
    
    def mk_v(x, y):
        # cup curvature so leaf edges touch stone, center slightly lifted
        z_lift = cup * size * (1.0 - abs(x)*1.5) * math.sin(math.pi * min(1.0, max(0.0, y)))
        pos = base_pos + a_real * (y * size) + s * (x * size * 0.95) + n * z_lift
        v_norm = (soft * 0.70 + n * 0.30).normalized()
        return builder.add_vert(pos, v_norm)
        
    cen_v = mk_v(0.0, 0.40)
    perim_verts = [mk_v(x, y) for x, y in IVY_CONTOUR]
    
    cen_uv = fol_ivy_uv(cell, 0.5, 0.40)
    for i in range(len(perim_verts)):
        next_i = (i + 1) % len(perim_verts)
        p0 = perim_verts[i]
        p1 = perim_verts[next_i]
        uv0 = fol_ivy_uv(cell, IVY_CONTOUR[i][0] * 0.5 + 0.5, IVY_CONTOUR[i][1])
        uv1 = fol_ivy_uv(cell, IVY_CONTOUR[next_i][0] * 0.5 + 0.5, IVY_CONTOUR[next_i][1])
        builder.add_face([cen_v, p1, p0], [cen_uv, uv1, uv0])

# ----------------- Mesh Finalizer & FBX Exporter -----------------
def finalize_and_export(builder, name, material, loc=(0, 0, 0)):
    bm = builder.bm
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    
    # Store custom normals
    normals = [Vector(v[builder.cn]) for v in bm.verts]
    
    # Reverse any flipped faces
    flip_faces = [f for f in bm.faces if f.normal.dot(sum((Vector(v[builder.cn]) for v in f.verts), Vector())) < -0.1]
    if flip_faces:
        bmesh.ops.reverse_faces(bm, faces=flip_faces)
        
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    
    # Set custom split vertex normals for soft painterly shading
    me.normals_split_custom_set_from_vertices([tuple(n) for n in normals])
    
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(material)
    
    for poly in me.polygons:
        poly.use_smooth = True
        
    ob.location = loc
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    
    # Export clean FBX
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    
    fbx_path = f'{MODELS_DIR}/{name}.fbx'
    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
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
        path_mode='COPY',
        embed_textures=False
    )
    
    stat = dict(
        tris=len(me.polygons),
        verts=len(me.vertices),
        bbox_min=[round(min(c[i] for c in bb), 3) for i in range(3)],
        bbox_max=[round(max(c[i] for c in bb), 3) for i in range(3)],
        fbx=fbx_path
    )
    print(f"Exported {name}: {stat['tris']} tris, {stat['verts']} verts | BBox: {stat['bbox_min']} to {stat['bbox_max']}")
    return ob, stat


# ==============================================================================
# ASSET AUTHORING DEFINITIONS
# ==============================================================================

stats_all = {}

# 1. ENV_Temple_Foliage_Clump_A (Medium/Large Stylized Foliage Clump)
def build_clump_a():
    builder = MeshBuilder()
    random.seed(101)
    
    # 5 Interlocking Cloud Lobes
    lobes = [
        # (center, radii, seed, subdiv, amp, up_bias)
        ((0.0, 0.0, 0.42), (0.62, 0.58, 0.40), 11, 2, 0.16, 0.35),   # Main central mass
        ((-0.38, 0.16, 0.32), (0.44, 0.40, 0.30), 12, 2, 0.18, 0.30), # Left flank
        ((0.40, -0.12, 0.28), (0.42, 0.38, 0.26), 13, 2, 0.17, 0.32), # Right flank
        ((0.08, 0.32, 0.36), (0.40, 0.36, 0.32), 14, 2, 0.15, 0.35),  # Rear crown
        ((-0.10, -0.32, 0.22), (0.36, 0.32, 0.22), 15, 2, 0.16, 0.30),# Front apron
    ]
    
    cols = [0, 1, 2, 3, 4, 5, 6, 7]
    for c, r, sd, sub, amp, ub in lobes:
        make_cloud_lobe(builder, c, r, sd, subdiv=sub, noise_amp=amp, up_bias=ub, z_min=0.0)
        # Add tangent silhouette shell cards
        make_tangent_shell_cards(builder, c, r, count=36, seed=sd*7, col_list=cols, card_size=(0.20, 0.32), up_bias=ub, z_cutoff=0.08)
        
    # Gnarled woody stem base emerging from soil (z=0)
    for i in range(5):
        ang = i * (2 * math.pi / 5) + random.uniform(-0.2, 0.2)
        dir_v = Vector((math.cos(ang), math.sin(ang), 0))
        pts = [
            dir_v * 0.08 + Vector((0, 0, -0.01)),
            dir_v * 0.28 + Vector((0, 0, 0.09)),
            dir_v * 0.48 + Vector((0, 0, 0.22))
        ]
        make_tube(builder, pts, [0.038, 0.026, 0.015], sides=5, bark_tw=1.0)
        
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Foliage_Clump_A', mat_foliage)
    stats_all['ENV_Temple_Foliage_Clump_A'] = stat
    return ob

# 2. ENV_Temple_Foliage_Clump_B (Low-spreading Stylized Foliage Mound)
def build_clump_b():
    builder = MeshBuilder()
    random.seed(202)
    
    # 5 Low, horizontally spreading cloud lobes
    lobes = [
        ((0.0, 0.0, 0.22), (0.68, 0.46, 0.24), 21, 2, 0.17, 0.40),    # Central spread
        ((-0.58, 0.08, 0.18), (0.50, 0.38, 0.19), 22, 2, 0.19, 0.35), # West spread
        ((0.60, -0.06, 0.17), (0.52, 0.36, 0.18), 23, 2, 0.18, 0.35), # East spread
        ((-0.18, -0.34, 0.14), (0.38, 0.30, 0.15), 24, 2, 0.16, 0.30),# South lip
        ((0.22, 0.30, 0.16), (0.40, 0.32, 0.16), 25, 2, 0.16, 0.35),  # North bank
    ]
    
    cols = [1, 2, 4, 5, 7]
    for c, r, sd, sub, amp, ub in lobes:
        make_cloud_lobe(builder, c, r, sd, subdiv=sub, noise_amp=amp, up_bias=ub, z_min=0.0)
        make_tangent_shell_cards(builder, c, r, count=28, seed=sd*9, col_list=cols, card_size=(0.18, 0.28), up_bias=ub, z_cutoff=0.04)
        
    # Low trailing woody roots
    for i in range(6):
        ang = i * (2 * math.pi / 6) + random.uniform(-0.25, 0.25)
        dir_v = Vector((math.cos(ang), math.sin(ang), 0))
        pts = [
            dir_v * 0.10 + Vector((0, 0, 0.0)),
            dir_v * 0.42 + Vector((0, 0, 0.04)),
            dir_v * 0.75 + Vector((0, 0, 0.01))
        ]
        make_tube(builder, pts, [0.030, 0.020, 0.010], sides=5, bark_tw=1.2)
        
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Foliage_Clump_B', mat_foliage)
    stats_all['ENV_Temple_Foliage_Clump_B'] = stat
    return ob

# 3. ENV_Temple_Foliage_Creeper_Wall (Wall-conforming Clinging Ivy Creeper)
def build_creeper_wall():
    builder = MeshBuilder()
    random.seed(303)
    
    # Vertical wall face sits at Y = 0. Vine extends in X: [-0.7, +0.7], Z: [0.0, 2.2], Y: [0.01, 0.06]
    # 5 Sinuous climbing runner stems branching up the wall
    runners = [
        # (x_root, z_root, x_tip, z_tip, n_pts, rad_base, rad_tip, seed)
        (0.0, 0.0, -0.35, 2.15, 12, 0.032, 0.012, 31),
        (0.0, 0.0, 0.30, 2.05, 12, 0.030, 0.011, 32),
        (-0.15, 0.45, -0.62, 1.45, 9, 0.022, 0.009, 33),
        (0.12, 0.50, 0.58, 1.35, 9, 0.020, 0.009, 34),
        (0.0, 0.0, 0.02, 1.60, 10, 0.026, 0.010, 35),
    ]
    
    for x0, z0, x1, z1, n, r0, r1, sd in runners:
        rng = random.Random(sd)
        pts = []
        radii = []
        for i in range(n + 1):
            t = i / n
            x = x0 + (x1 - x0) * t + math.sin(t * 5.0 + sd) * 0.08
            z = z0 + (z1 - z0) * t
            # Flat against wall plane at y=0, hugging tightly
            y = 0.025 + 0.020 * math.sin(t * 4.0 + sd * 1.5)**2
            pts.append(Vector((x, y, z)))
            radii.append(r0 + (r1 - r0) * t)
        make_tube(builder, pts, radii, sides=4, bark_tw=1.5)
        
        # Dense clinging ivy leaves along the runner
        for i in range(1, n + 1):
            p = pts[i]
            t = i / n
            sz = rng.uniform(0.18, 0.28) * (1.0 - 0.35 * t)
            cell = rng.randint(0, 3)
            
            # 2 to 3 leaves per stem node spreading horizontally along the wall plane
            for side in (-1, 1):
                leaf_ang = rng.uniform(0.2, 0.8)
                aim = Vector((side * math.cos(leaf_ang), 0.08, math.sin(leaf_ang))).normalized()
                # Wall normal is +Y (0, 1, 0)
                norm = Vector((side * 0.15, 0.95, 0.20)).normalized()
                soft_n = Vector((side * 0.25, 0.85, 0.40)).normalized()
                make_clinging_ivy_leaf(builder, p, aim, norm, sz, cell, soft_norm=soft_n)
                
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Foliage_Creeper_Wall', mat_foliage)
    stats_all['ENV_Temple_Foliage_Creeper_Wall'] = stat
    return ob

# 4. ENV_Temple_Foliage_Creeper_Column (Column-conforming Clinging Ivy Drape)
def build_creeper_column():
    builder = MeshBuilder()
    random.seed(404)
    
    # Cylindrical column radius R = 0.50 m. Arc: theta in [-55 deg, +55 deg]. Z: [0.0, 1.8 m]
    # Sinuous runner vines clasping the curved column shaft
    col_runners = [
        # (ang_base, z_base, ang_tip, z_tip, n_pts, rad_base, rad_tip, seed)
        (-0.10, 1.80, -0.65, 0.20, 14, 0.028, 0.012, 41), # Hanging drape west
        (0.08, 1.80, 0.60, 0.35, 13, 0.026, 0.011, 42),  # Hanging drape east
        (-0.35, 1.40, -0.75, 0.60, 8, 0.020, 0.009, 43),  # Branch west
        (0.25, 1.35, 0.70, 0.70, 8, 0.019, 0.009, 44),   # Branch east
        (0.0, 1.80, 0.05, 0.50, 11, 0.024, 0.010, 45),   # Center vertical runner
    ]
    
    R = 0.50
    for a0, z0, a1, z1, n, r0, r1, sd in col_runners:
        rng = random.Random(sd)
        pts = []
        radii = []
        for i in range(n + 1):
            t = i / n
            ang = a0 + (a1 - a0) * t + math.sin(t * 4.5 + sd) * 0.06
            z = z0 + (z1 - z0) * t
            # Radius slightly outside column surface
            r_curr = R + 0.022 + 0.012 * math.sin(t * 3.0 + sd)**2
            x = math.sin(ang) * r_curr
            y = math.cos(ang) * r_curr
            pts.append(Vector((x, y, z)))
            radii.append(r0 + (r1 - r0) * t)
        make_tube(builder, pts, radii, sides=4, bark_tw=1.5)
        
        # Ivy leaves hugging the cylindrical surface
        for i in range(1, n + 1):
            p = pts[i]
            t = i / n
            sz = rng.uniform(0.18, 0.26) * (1.0 - 0.30 * t)
            cell = rng.randint(0, 3)
            
            # Normal is radial from column Z axis
            cyl_norm = Vector((p.x, p.y, 0)).normalized()
            tang = Vector((-cyl_norm.y, cyl_norm.x, 0))
            
            for side in (-1, 1):
                aim = (tang * (side * rng.uniform(0.4, 0.8)) + Vector((0, 0, -rng.uniform(0.3, 0.7)))).normalized()
                leaf_norm = (cyl_norm * 0.85 + Vector((0, 0, 0.25))).normalized()
                make_clinging_ivy_leaf(builder, p, aim, leaf_norm, sz, cell, soft_norm=leaf_norm)
                
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Foliage_Creeper_Column', mat_foliage)
    stats_all['ENV_Temple_Foliage_Creeper_Column'] = stat
    return ob

# 5. ENV_Temple_Ground_DirtPatch_A (Curved Dirt/Sediment Accumulation Patch)
def build_dirt_patch_a():
    builder = MeshBuilder()
    random.seed(505)
    
    # Low-profile mound: 2.2 m x 1.6 m, height 0.045 m at center, feathering to 0.001 m at boundary
    # Grid mesh (16 x 12 quads)
    nx, ny = 16, 12
    lx, ly = 2.2, 1.6
    
    grid = []
    for j in range(ny + 1):
        row = []
        v_coord = (j / ny - 0.5) * ly
        for i in range(nx + 1):
            u_coord = (i / nx - 0.5) * lx
            # Radial falloff
            dist_norm = math.sqrt((u_coord / (lx * 0.5))**2 + (v_coord / (ly * 0.5))**2)
            falloff = max(0.0, 1.0 - dist_norm**1.6)
            
            # Organic noise ripples in the dirt
            nz = noise.noise(Vector((u_coord * 2.5, v_coord * 2.5, 5.5))) * 0.012
            z = (0.045 * falloff + nz * falloff)
            z = max(0.001, z)
            
            pos = Vector((u_coord, v_coord, z))
            # Normal points up with slope
            norm = (Vector((-u_coord * 0.04 * falloff, -v_coord * 0.04 * falloff, 1.0))).normalized()
            v_obj = builder.add_vert(pos, norm)
            row.append(v_obj)
        grid.append(row)
        
    for j in range(ny):
        for i in range(nx):
            v00 = grid[j][i]
            v10 = grid[j+1][i]
            v11 = grid[j+1][i+1]
            v01 = grid[j][i+1]
            
            x0 = (i / nx - 0.5) * lx
            x1 = ((i + 1) / nx - 0.5) * lx
            y0 = (j / ny - 0.5) * ly
            y1 = ((j + 1) / ny - 0.5) * ly
            
            uv0 = gnd_soil_uv(x0, y0)
            uv1 = gnd_soil_uv(x0, y1)
            uv2 = gnd_soil_uv(x1, y1)
            uv3 = gnd_soil_uv(x1, y0)
            builder.add_face([v00, v10, v11, v01], [uv0, uv1, uv2, uv3])
            
    # 4 Embedded weathered stone flagstone chips (partially submerged in dirt)
    stone_chips = [
        ((-0.45, 0.20, 0.035), (0.28, 0.22, 0.040), 15),
        ((0.50, -0.15, 0.030), (0.32, 0.24, 0.035), -25),
        ((-0.15, -0.38, 0.022), (0.22, 0.18, 0.028), 40),
        ((0.20, 0.35, 0.025), (0.25, 0.20, 0.030), -10),
    ]
    for (cx, cy, cz), (sx, sy, sz), rot_deg in stone_chips:
        rot = math.radians(rot_deg)
        c_rot, s_rot = math.cos(rot), math.sin(rot)
        # 6-sided beveled chip slab
        corners = [
            (-sx*0.5, -sy*0.5), (sx*0.5, -sy*0.5), (sx*0.5, sy*0.5), (-sx*0.5, sy*0.5)
        ]
        top_verts = []
        bot_verts = []
        for x_loc, y_loc in corners:
            xr = cx + (x_loc * c_rot - y_loc * s_rot)
            yr = cy + (x_loc * s_rot + y_loc * c_rot)
            vt = builder.add_vert(Vector((xr, yr, cz + sz)), Vector((0, 0, 1)))
            vb = builder.add_vert(Vector((xr, yr, cz - sz*0.5)), Vector((0, 0, -1)))
            top_verts.append(vt)
            bot_verts.append(vb)
            
        # Top face (sandstone flagstone texture)
        uvs_top = [gnd_stone_uv(cx + x, cy + y) for x, y in corners]
        builder.add_face(top_verts, uvs_top)
        # Side faces
        for k in range(4):
            k_next = (k + 1) % 4
            builder.add_face(
                [top_verts[k], bot_verts[k], bot_verts[k_next], top_verts[k_next]],
                [gnd_gravel_uv(0, 0), gnd_gravel_uv(0, 1), gnd_gravel_uv(1, 1), gnd_gravel_uv(1, 0)]
            )
            
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Ground_DirtPatch_A', mat_ground)
    stats_all['ENV_Temple_Ground_DirtPatch_A'] = stat
    return ob

# 6. ENV_Temple_Ground_DirtPatch_B (Linear Seam Wall-Base Dirt Drift)
def build_dirt_patch_b():
    builder = MeshBuilder()
    random.seed(606)
    
    # Linear drift: 2.4 m long (X), 0.6 m wide (Y). High along back edge Y=0.30 (Z=0.035), sloping to 0.001 at Y=-0.30
    nx, ny = 16, 6
    lx, ly = 2.4, 0.6
    
    grid = []
    for j in range(ny + 1):
        row = []
        t_y = j / ny
        y = (t_y - 0.5) * ly
        for i in range(nx + 1):
            t_x = i / nx
            x = (t_x - 0.5) * lx
            
            # Feather ends in X
            falloff_x = math.sin(t_x * math.pi)**0.5
            # Slope from back (t_y=1, high) to front (t_y=0, low)
            slope_y = (t_y)**1.5
            
            nz = noise.noise(Vector((x * 3.0, y * 3.0, 7.1))) * 0.008
            z = max(0.001, (0.038 * slope_y + nz) * falloff_x)
            
            pos = Vector((x, y, z))
            norm = (Vector((0, -0.05, 1.0))).normalized()
            v_obj = builder.add_vert(pos, norm)
            row.append(v_obj)
        grid.append(row)
        
    for j in range(ny):
        for i in range(nx):
            v00 = grid[j][i]
            v10 = grid[j+1][i]
            v11 = grid[j+1][i+1]
            v01 = grid[j][i+1]
            
            x0 = (i / nx - 0.5) * lx
            x1 = ((i + 1) / nx - 0.5) * lx
            y0 = (j / ny - 0.5) * ly
            y1 = ((j + 1) / ny - 0.5) * ly
            
            # Back zone uses mortar crumble/gravel, front uses sandy soil
            if j >= ny // 2:
                uv0 = gnd_gravel_uv(x0, y0)
                uv1 = gnd_gravel_uv(x0, y1)
                uv2 = gnd_gravel_uv(x1, y1)
                uv3 = gnd_gravel_uv(x1, y0)
            else:
                uv0 = gnd_soil_uv(x0, y0)
                uv1 = gnd_soil_uv(x0, y1)
                uv2 = gnd_soil_uv(x1, y1)
                uv3 = gnd_soil_uv(x1, y0)
            builder.add_face([v00, v10, v11, v01], [uv0, uv1, uv2, uv3])
            
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Ground_DirtPatch_B', mat_ground)
    stats_all['ENV_Temple_Ground_DirtPatch_B'] = stat
    return ob

# 7. ENV_Temple_Ground_CrackedMortar_C (Fractured Flagstone with Mortar Gravel Bed & Weed Sprout)
def build_cracked_mortar_c():
    builder = MeshBuilder()
    random.seed(707)
    
    # 1.4 m x 1.2 m stone slab plate, split diagonally into 3 jagged pieces with open fissure
    # Piece 1: North-West stone slab
    poly_nw = [(-0.65, -0.55), (-0.65, 0.55), (0.10, 0.55), (-0.15, 0.05), (-0.35, -0.55)]
    # Piece 2: South-East stone slab
    poly_se = [(-0.15, -0.55), (0.05, 0.0), (0.35, 0.55), (0.65, 0.55), (0.65, -0.55)]
    # Fissure bed runs between them
    
    def make_slab_piece(poly, h_top=0.032, h_bot=0.0):
        top_v = []
        bot_v = []
        for x, y in poly:
            vt = builder.add_vert(Vector((x, y, h_top)), Vector((0, 0, 1)))
            vb = builder.add_vert(Vector((x, y, h_bot)), Vector((0, 0, -1)))
            top_v.append(vt)
            bot_v.append(vb)
            
        # Top face
        uvs_top = [gnd_stone_uv(x, y) for x, y in poly]
        builder.add_face(top_v, uvs_top)
        
        # Side chiseled faces
        for k in range(len(poly)):
            next_k = (k + 1) % len(poly)
            builder.add_face(
                [top_v[k], bot_v[k], bot_v[next_k], top_v[next_k]],
                [gnd_stone_uv(0, 0), gnd_stone_uv(0, 0.1), gnd_stone_uv(0.1, 0.1), gnd_stone_uv(0.1, 0)]
            )
            
    make_slab_piece(poly_nw, h_top=0.032, h_bot=0.002)
    make_slab_piece(poly_se, h_top=0.030, h_bot=0.002)
    
    # Recessed fissure bed (mortar crumble, gravel, damp loam)
    poly_fissure = [(-0.35, -0.55), (-0.15, 0.05), (0.10, 0.55), (0.35, 0.55), (0.05, 0.0), (-0.15, -0.55)]
    fis_verts = []
    for x, y in poly_fissure:
        v = builder.add_vert(Vector((x, y, 0.006)), Vector((0, 0, 1)))
        fis_verts.append(v)
    uvs_fis = [gnd_gravel_uv(x, y) for x, y in poly_fissure]
    builder.add_face(fis_verts, uvs_fis)
    
    ob, stat = finalize_and_export(builder, 'ENV_Temple_Ground_CrackedMortar_C', mat_ground)
    stats_all['ENV_Temple_Ground_CrackedMortar_C'] = stat
    return ob


# ==============================================================================
# MAIN PIPELINE EXECUTION
# ==============================================================================
print("=== Building Foliage & Ground Transition Asset Kit ===")

objs = [
    build_clump_a(),
    build_clump_b(),
    build_creeper_wall(),
    build_creeper_column(),
    build_dirt_patch_a(),
    build_dirt_patch_b(),
    build_cracked_mortar_c(),
]

# Arrange objects in master review blend file for easy visual inspection
spacing = 3.0
for i, ob in enumerate(objs):
    ob.location = (i * spacing, 0, 0)

blend_path = f'{OUT}/TempleEnvironmentKit_foliage_v2.blend'
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved master working blend: {blend_path}")

json_path = f'{MODELS_DIR}/stats.json'
with open(json_path, 'w') as f:
    json.dump(stats_all, f, indent=2)
print(f"Saved asset statistics: {json_path}")

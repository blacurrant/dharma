import bpy
import bmesh
import math
import random
import os

random.seed(101)

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

ROOT = '/Users/landerstudio/MythicRoguelite'
G = f'{ROOT}/Art/Blender/Revisions/foliage_kit'
MODELS = f'{G}/models'
TEXTURES = f'{G}/textures'
os.makedirs(MODELS, exist_ok=True)

# Create shared foliage material
mat = bpy.data.materials.new(name='MI_Temple_Foliage')
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

node_output = nodes.new(type='ShaderNodeOutputMaterial')
node_principled = nodes.new(type='ShaderNodeBsdfPrincipled')
links.new(node_principled.outputs['BSDF'], node_output.inputs['Surface'])

# BaseColor
tex_base = nodes.new(type='ShaderNodeTexImage')
tex_base_img = bpy.data.images.load(f'{TEXTURES}/ENV_Temple_Foliage_BaseColor.png')
tex_base.image = tex_base_img
links.new(tex_base.outputs['Color'], node_principled.inputs['Base Color'])
links.new(tex_base.outputs['Alpha'], node_principled.inputs['Alpha'])
# blend mode handled in engine

# Helper to create quad with UV
def add_card(bm, uv_layer, p0, p1, p2, p3, uv0, uv1, uv2, uv3):
    v0 = bm.verts.new(p0)
    v1 = bm.verts.new(p1)
    v2 = bm.verts.new(p2)
    v3 = bm.verts.new(p3)
    f = bm.faces.new((v0, v1, v2, v3))
    for l, uv in zip(f.loops, [uv0, uv1, uv2, uv3]):
        l[uv_layer].uv = uv
    return f

# 1. Shrub A: volumetric dome of 8 curved cross-cards
def build_shrub_a():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    num_cards = 8
    radius = 0.65
    height = 1.05
    for i in range(num_cards):
        angle = i * (math.pi / num_cards) + random.uniform(-0.1, 0.1)
        ca, sa = math.cos(angle), math.sin(angle)
        r_bot = radius * random.uniform(0.7, 0.9)
        r_mid = radius * random.uniform(0.9, 1.1)
        r_top = radius * 0.4
        z_mid = height * 0.55
        z_top = height
        
        # Segment 1 (bottom to mid)
        p0 = (-ca * r_bot, -sa * r_bot, 0.0)
        p1 = (ca * r_bot, sa * r_bot, 0.0)
        p2 = (ca * r_mid, sa * r_mid, z_mid)
        p3 = (-ca * r_mid, -sa * r_mid, z_mid)
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.0, 0.5), (0.5, 0.5), (0.5, 0.75), (0.0, 0.75))
        
        # Segment 2 (mid to top)
        p4 = (ca * r_top, sa * r_top, z_top)
        p5 = (-ca * r_top, -sa * r_top, z_top)
        add_card(bm, uv_lay, p3, p2, p4, p5, (0.0, 0.75), (0.5, 0.75), (0.5, 1.0), (0.0, 1.0))
        
    bm.normal_update()
    return bm

# 2. Shrub B: low spreading shrub (10 cards, wider spread)
def build_shrub_b():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    num_cards = 10
    radius_x = 1.0
    radius_y = 0.55
    height = 0.75
    for i in range(num_cards):
        angle = i * (math.pi / num_cards) + random.uniform(-0.1, 0.1)
        ca = math.cos(angle) * radius_x
        sa = math.sin(angle) * radius_y
        h = height * random.uniform(0.8, 1.05)
        p0 = (-ca * 0.8, -sa * 0.8, 0.0)
        p1 = (ca * 0.8, sa * 0.8, 0.0)
        p2 = (ca, sa, h)
        p3 = (-ca, -sa, h)
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.0, 0.5), (0.5, 0.5), (0.5, 1.0), (0.0, 1.0))
    bm.normal_update()
    return bm

# 3. Vine A: vertical hanging creeper (hanging from Z=0 down to Z=-2.4)
def build_vine_a():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    width = 0.4
    depth = 0.08
    y_step = -0.4
    for seg in range(6):
        z0 = seg * y_step
        z1 = (seg + 1) * y_step
        w0 = width * (1.0 - seg * 0.1)
        w1 = width * (1.0 - (seg + 1) * 0.1)
        x_off = math.sin(seg * 1.1) * 0.06
        
        p0 = (-w0 + x_off, depth, z0)
        p1 = (w0 + x_off, depth, z0)
        p2 = (w1 + x_off, depth, z1)
        p3 = (-w1 + x_off, depth, z1)
        
        v_low = 0.5 + (seg / 6.0) * 0.5
        v_high = 0.5 + ((seg + 1) / 6.0) * 0.5
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.5, v_low), (1.0, v_low), (1.0, v_high), (0.5, v_high))
        
        # Side tendril card
        if seg in [1, 3, 4]:
            side = 1.0 if seg % 2 == 1 else -1.0
            tp0 = (side * w0 + x_off, depth, z0)
            tp1 = (side * (w0 + 0.35) + x_off, depth + 0.04, z0 - 0.15)
            tp2 = (side * (w0 + 0.30) + x_off, depth + 0.04, z0 - 0.45)
            tp3 = (side * w1 + x_off, depth, z1)
            add_card(bm, uv_lay, tp0, tp1, tp2, tp3, (0.5, 0.7), (1.0, 0.7), (1.0, 1.0), (0.5, 1.0))

    bm.normal_update()
    return bm

# 4. Vine B: wide cornice / ledge hanging creeper (hanging from Z=0 down to Z=-1.3)
def build_vine_b():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    num_strands = 5
    span = 1.5
    for s in range(num_strands):
        sx = -span * 0.5 + (s / (num_strands - 1)) * span
        w = 0.28
        h = 1.1 + math.sin(s * 1.7) * 0.3
        p0 = (sx - w * 0.5, 0.05, 0.0)
        p1 = (sx + w * 0.5, 0.05, 0.0)
        p2 = (sx + w * 0.35, 0.08, -h)
        p3 = (sx - w * 0.35, 0.08, -h)
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.5, 0.5), (1.0, 0.5), (1.0, 1.0), (0.5, 1.0))
    bm.normal_update()
    return bm

# 5. Tuft A: upright hardy grass clump (height 0.45, radius 0.35)
def build_tuft_a():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    num_blades = 7
    radius = 0.32
    height = 0.45
    for i in range(num_blades):
        angle = i * (math.pi / num_blades) + random.uniform(-0.15, 0.15)
        ca = math.cos(angle)
        sa = math.sin(angle)
        w = 0.12 * random.uniform(0.8, 1.2)
        h = height * random.uniform(0.85, 1.15)
        p0 = (-ca * 0.05, -sa * 0.05, 0.0)
        p1 = (ca * 0.05, sa * 0.05, 0.0)
        p2 = (ca * radius + random.uniform(-0.04, 0.04), sa * radius + random.uniform(-0.04, 0.04), h)
        p3 = (ca * radius * 0.4, sa * radius * 0.4, h * 0.6)
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5))
    bm.normal_update()
    return bm

# 6. Tuft B: low spreading stone-joint grass clump (height 0.28, radius 0.45)
def build_tuft_b():
    bm = bmesh.new()
    uv_lay = bm.loops.layers.uv.new("UVMap")
    num_blades = 9
    radius = 0.42
    height = 0.28
    for i in range(num_blades):
        angle = i * (math.pi / num_blades) + random.uniform(-0.2, 0.2)
        ca = math.cos(angle)
        sa = math.sin(angle)
        h = height * random.uniform(0.8, 1.2)
        p0 = (-ca * 0.08, -sa * 0.08, 0.0)
        p1 = (ca * 0.08, sa * 0.08, 0.0)
        p2 = (ca * radius, sa * radius, h)
        p3 = (-ca * radius * 0.3, -sa * radius * 0.3, h * 0.7)
        add_card(bm, uv_lay, p0, p1, p2, p3, (0.5, 0.0), (1.0, 0.0), (1.0, 0.5), (0.5, 0.5))
    bm.normal_update()
    return bm

builders = [
    ('ENV_Temple_Foliage_Shrub_A', build_shrub_a),
    ('ENV_Temple_Foliage_Shrub_B', build_shrub_b),
    ('ENV_Temple_Foliage_Vine_A', build_vine_a),
    ('ENV_Temple_Foliage_Vine_B', build_vine_b),
    ('ENV_Temple_Foliage_Tuft_A', build_tuft_a),
    ('ENV_Temple_Foliage_Tuft_B', build_tuft_b),
]

unity_models = f'{ROOT}/Assets/ArtTest/VisualFoundation/Art2/Models'
os.makedirs(unity_models, exist_ok=True)

created_objects = []
for name, fn in builders:
    bm = fn()
    mesh = bpy.data.meshes.new(name + '_Mesh')
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new(name, mesh)
    sc.collection.objects.link(obj)
    obj.data.materials.append(mat)
    created_objects.append(obj)
    
    # Export individual FBX
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    
    fbx_path_staging = f'{MODELS}/{name}.fbx'
    fbx_path_unity = f'{unity_models}/{name}.fbx'
    
    for dest in [fbx_path_staging, fbx_path_unity]:
        bpy.ops.export_scene.fbx(
            filepath=dest,
            use_selection=True,
            object_types={'MESH'},
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=True,
            axis_forward='-Z',
            axis_up='Y',
            use_mesh_modifiers=True,
            mesh_smooth_type='OFF',
            use_triangles=True,
            use_tspace=True,
            colors_type='NONE',
            add_leaf_bones=False,
            path_mode='RELATIVE',
            embed_textures=False,
            bake_anim=False,
            use_custom_props=False
        )
    print(f'Exported {name} -> {len(mesh.polygons)} faces ({len(mesh.polygons)*2} tris)')

# Save working blend file
blend_out = f'{G}/TempleEnvironmentKit_foliage.blend'
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print(f'Saved working blend file: {blend_out}')

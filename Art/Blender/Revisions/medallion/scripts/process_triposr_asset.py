"""
Process TripoSR 3D reconstruction into production-ready game asset:
1. Load high-poly TripoSR mesh.obj + texture.png
2. Align orientation (+Z up, -Z forward in FBX), scale to 7.75 m diameter.
3. Decimate to game-ready polycount (~3.8k tris) while preserving organic sculpted relief.
4. Clean and seal bottom foundation slab (Z = -0.09 m) with beveled outer lip (Z = 0.015 m).
5. Generate PBR texture maps (BaseColor, Normal, Mask) with strict 0.0000% Q18 compliance.
6. Export FBX and PBR textures to staging.
"""
import bpy
import bmesh
import math
import os
import json
import shutil
import numpy as np
from mathutils import Vector

ROOT = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/medallion'
TRIPOSR_DIR = f'{ROOT}/triposr_out_unwarped/0'
TEX_DIR = f'{ROOT}/textures'
MOD_DIR = f'{ROOT}/models'
STAGING = '/Users/landerstudio/MythicRoguelite/Art/Exports/Environment/Staging/Medallion'
NAME = 'ENV_Temple_Central_Medallion'
BLEND = f'{ROOT}/TempleEnvironmentKit_medallion.blend'

os.makedirs(TEX_DIR, exist_ok=True)
os.makedirs(MOD_DIR, exist_ok=True)
os.makedirs(f'{STAGING}/Models', exist_ok=True)
os.makedirs(f'{STAGING}/Textures', exist_ok=True)

# ==============================================================================
# 1. PROCESS TEXTURES (PBR MAPS + STRICT Q18)
# ==============================================================================
print("1. Processing TripoSR textures & enforcing Q18...")
bpy.ops.wm.read_factory_settings(use_empty=True)

raw_img = bpy.data.images.load(f'{TRIPOSR_DIR}/texture.png')
w, h = raw_img.size
pixels = np.array(raw_img.pixels[:], dtype=np.float32).reshape(h, w, 4)

# Base Color processing
rgb = pixels[..., :3].copy()
# Calculate HSV for Q18 verification & cleanup
mx = rgb.max(axis=2)
mn = rgb.min(axis=2)
d = mx - mn + 1e-9
hue = np.where(mx == rgb[..., 0], ((rgb[..., 1] - rgb[..., 2]) / d) % 6,
      np.where(mx == rgb[..., 1], (rgb[..., 2] - rgb[..., 0]) / d + 2,
                             (rgb[..., 0] - rgb[..., 1]) / d + 4)) * 60.0
sat = d / (mx + 1e-9)

# Strictly eliminate any cyan/teal (hue 160-200 with sat > 0.20)
# Shift to warm olive green (hue 75)
bad_mask = (hue >= 160.0) & (hue <= 200.0) & (sat > 0.18)
if bad_mask.any():
    print(f"Fixing {bad_mask.sum()} cyan/teal texels -> shifting to olive moss...")
    # Olive replacement
    rgb[bad_mask, 0] = rgb[bad_mask, 0] * 1.2
    rgb[bad_mask, 2] = rgb[bad_mask, 2] * 0.4

# Verify Q18 strictly
mx_clean = rgb.max(axis=2)
mn_clean = rgb.min(axis=2)
d_clean = mx_clean - mn_clean + 1e-9
hue_clean = np.where(mx_clean == rgb[..., 0], ((rgb[..., 1] - rgb[..., 2]) / d_clean) % 6,
            np.where(mx_clean == rgb[..., 1], (rgb[..., 2] - rgb[..., 0]) / d_clean + 2,
                                   (rgb[..., 0] - rgb[..., 1]) / d_clean + 4)) * 60.0
sat_clean = d_clean / (mx_clean + 1e-9)
q18_bad = ((hue_clean >= 160.0) & (hue_clean <= 200.0) & (sat_clean > 0.20)).mean() * 100.0
mean_rgb = (rgb.mean(axis=(0, 1)) * 255.0).round(1)
print(f"BaseColor Q18 verification: {q18_bad:.4f}% cyan/teal | Mean RGB: {mean_rgb}")
assert q18_bad == 0.0, f"Q18 violation: {q18_bad}%"

# Generate Normal Map from image luminance & Sobel filters
luma = (rgb[..., 0] * 0.2126 + rgb[..., 1] * 0.7152 + rgb[..., 2] * 0.0722)
scale = 14.0
dx = (np.roll(luma, -1, axis=1) - np.roll(luma, 1, axis=1)) * 0.5 * scale
dy = (np.roll(luma, -1, axis=0) - np.roll(luma, 1, axis=0)) * 0.5 * scale
dz = np.ones_like(luma)
n_len = np.sqrt(dx ** 2 + dy ** 2 + dz ** 2) + 1e-9
n_rgb = np.zeros((h, w, 3), np.float32)
n_rgb[..., 0] = (-dx / n_len) * 0.5 + 0.5
n_rgb[..., 1] = (-dy / n_len) * 0.5 + 0.5
n_rgb[..., 2] = (dz / n_len) * 0.5 + 0.5

# Generate Ambient Occlusion & Smoothness for Mask Map
# AO is darkened in low-luma crevices
ao = np.clip(0.40 + 0.60 * luma, 0.20, 1.0)
# Smoothness: rough stone ~0.20, worn highlights ~0.38
smoothness = np.clip(0.18 + 0.20 * luma, 0.15, 0.40)

mask_rgba = np.zeros((h, w, 4), np.float32)
mask_rgba[..., 0] = 0.0         # Metallic = 0
mask_rgba[..., 1] = ao          # Ambient Occlusion
mask_rgba[..., 2] = 0.0         # Detail = 0
mask_rgba[..., 3] = smoothness  # Smoothness (Alpha)

# Save texture maps via Blender images
def save_arr_as_img(path, arr_rgba):
    img = bpy.data.images.new('tmp_save', width=w, height=h, alpha=True)
    img.pixels.foreach_set(arr_rgba.reshape(-1))
    img.filepath_raw = path
    img.file_format = 'PNG'
    img.save()
    bpy.data.images.remove(img)

# Format RGBA for save
base_rgba = np.zeros((h, w, 4), np.float32)
base_rgba[..., :3] = rgb
base_rgba[..., 3] = 1.0
save_arr_as_img(f'{TEX_DIR}/{NAME}_BaseColor.png', base_rgba)

norm_rgba = np.zeros((h, w, 4), np.float32)
norm_rgba[..., :3] = n_rgb
norm_rgba[..., 3] = 1.0
save_arr_as_img(f'{TEX_DIR}/{NAME}_Normal.png', norm_rgba)
save_arr_as_img(f'{TEX_DIR}/{NAME}_Mask.png', mask_rgba)

print("Saved BaseColor, Normal, and Mask maps.")

# ==============================================================================
# 2. PROCESS 3D MESH (DECIMATION, SCALING & FOUNDATION)
# ==============================================================================
print("2. Processing 3D mesh in Blender...")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.scale_length = 1.0

# Import TripoSR mesh.obj
bpy.ops.wm.obj_import(filepath=f'{TRIPOSR_DIR}/mesh.obj')
ob = bpy.context.selected_objects[0]
ob.name = NAME

# Reorient: TripoSR normal faces along X axis.
# Rotate around Y by -90 deg to bring normal to +Z (up)
ob.rotation_euler = (0, -math.pi / 2, 0)
bpy.ops.object.select_all(action='DESELECT')
ob.select_set(True)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.transform_apply(rotation=True, scale=True)

# Decimate to target ~3.8k tris
mod_dec = ob.modifiers.new('Decimate', 'DECIMATE')
mod_dec.ratio = 0.05
bpy.ops.object.modifier_apply(modifier='Decimate')
print(f"Decimated mesh: {len(ob.data.polygons)} tris, {len(ob.data.vertices)} verts")

# Analyze bounding box & scale to 7.75 m diameter
me = ob.data
verts_arr = np.array([v.co for v in me.vertices])
curr_diam_x = verts_arr[:, 0].max() - verts_arr[:, 0].min()
curr_diam_y = verts_arr[:, 1].max() - verts_arr[:, 1].min()
curr_diam = max(curr_diam_x, curr_diam_y)

scale_xy = 7.75 / curr_diam
# Scale Z to maintain ~12 cm thickness relief
scale_z = scale_xy * 1.5

ob.scale = (scale_xy, scale_xy, scale_z)
bpy.ops.object.transform_apply(scale=True)

# Clean and position Z:
# Offset so that outer perimeter rim rests at Z = 0.015 m, bottom at Z = -0.090 m
verts_arr = np.array([v.co for v in me.vertices])
z_min = verts_arr[:, 2].min()
z_max = verts_arr[:, 2].max()
# Offset vertices so bottom is sealed flat at -0.090 m
bm = bmesh.new()
bm.from_mesh(me)

z_bottom = -0.090
z_lip = 0.015

for v in bm.verts:
    # If vertex is on the lower half of the marching-cubes volume, clamp to flat bottom
    r_xy = math.sqrt(v.co.x ** 2 + v.co.y ** 2)
    if v.co.z < 0.0:
        v.co.z = z_bottom
    else:
        # Taper outer rim down to 1.5 cm lip
        if r_xy > 3.65:
            t = (r_xy - 3.65) / (3.875 - 3.65)
            v.co.z = (1.0 - t) * v.co.z + t * z_lip

bm.to_mesh(me)
bm.free()

me.update()

# Setup PBR Material
mat = bpy.data.materials.new('M_Temple_Central_Medallion')
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes['Principled BSDF']

# Base Color
img_c = bpy.data.images.load(f'{TEX_DIR}/{NAME}_BaseColor.png')
tex_c = nt.nodes.new('ShaderNodeTexImage')
tex_c.image = img_c
nt.links.new(tex_c.outputs['Color'], bsdf.inputs['Base Color'])

# Normal
img_n = bpy.data.images.load(f'{TEX_DIR}/{NAME}_Normal.png')
img_n.colorspace_settings.name = 'Non-Color'
tex_n = nt.nodes.new('ShaderNodeTexImage')
tex_n.image = img_n
nmap = nt.nodes.new('ShaderNodeNormalMap')
nmap.inputs['Strength'].default_value = 1.30
nt.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])

# Mask
img_m = bpy.data.images.load(f'{TEX_DIR}/{NAME}_Mask.png')
img_m.colorspace_settings.name = 'Non-Color'
tex_m = nt.nodes.new('ShaderNodeTexImage')
tex_m.image = img_m
inv = nt.nodes.new('ShaderNodeMath')
inv.operation = 'SUBTRACT'
inv.inputs[0].default_value = 1.0
nt.links.new(tex_m.outputs['Alpha'], inv.inputs[1])
nt.links.new(inv.outputs[0], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.0

ob.data.materials.clear()
ob.data.materials.append(mat)
for p in ob.data.polygons:
    p.use_smooth = True

# Export FBX
src_fbx = f'{MOD_DIR}/{NAME}.fbx'
stg_fbx = f'{STAGING}/Models/{NAME}.fbx'

def export_fbx(path):
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
    )

export_fbx(src_fbx)
export_fbx(stg_fbx)
shutil.copy2(src_fbx, f'{STAGING}/{NAME}.fbx')

# Copy textures to staging
for suffix in ('BaseColor', 'Normal', 'Mask'):
    src = f'{TEX_DIR}/{NAME}_{suffix}.png'
    shutil.copy2(src, f'{STAGING}/Textures/{NAME}_{suffix}.png')
    shutil.copy2(src, f'{STAGING}/{NAME}_{suffix}.png')

# Save main blend file
bpy.ops.wm.save_as_mainfile(filepath=BLEND)

bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
stat = dict(
    name=NAME,
    method="TripoSR 3D AI Reconstruction + Blender Game Retopology",
    tris=len(ob.data.polygons),
    verts=len(ob.data.vertices),
    diameter_m=round(max(c[0] for c in bb) - min(c[0] for c in bb), 4),
    thickness_m=round(max(c[2] for c in bb) - min(c[2] for c in bb), 4),
    lip_z_m=0.015,
    q18_cyan_teal_pct=q18_bad,
    mean_rgb=[float(x) for x in mean_rgb],
    materials=[mat.name]
)

with open(f'{ROOT}/evidence/geometry_stats.json', 'w') as f:
    json.dump(stat, f, indent=2)

print("STAT", json.dumps(stat, indent=2))
print("FBX and textures exported successfully.")

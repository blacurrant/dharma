"""Shared node builder: the exact overlay maths recommended to Unity, expressed as Blender shader nodes (world space, no UV0 dependency).

Coordinates: Blender world (x, y, z) = Unity (x, z, y_up).  P = world position in metres.
  macro maps  : U = (x + 20) / 40, V = (y + 20) / 40     (V = Unity z; image row 0 = z +20)
  floor tiles : U = x / T, V = y / T                      (T = tile size in metres; floor tile edges sit on even metres)
  wall maps   : u = (|Nx| > |Ny| ? y : x) / T, v = z / T  (u runs along the wall, v = height)
Blend maths (all on LINEAR albedo):
  macro value : albedo *= lerp(1, 2*m, k)
  macro tint  : albedo *= lerp(1, 2*tint.rgb, k)
  overlay     : albedo  = lerp(albedo, overlay.rgb, overlay.a * k * w)   (w = radial weight, 1 outside the combat circle)
"""
import bpy, math

VF = '/Users/landerstudio/MythicRoguelite/Art/Blender/Revisions/vf_handoff'
TEX = VF + '/textures/'

# name -> (kind, mapping, tile_m, default_opacity, (min, max), weight_inside_r10)
SPEC = {
    'VF_Floor_MacroValue_2048':       ('macro_value', 'macro', 40.0, 0.75, (0.5, 1.0), 1.0),      # damping is baked into the map
    'VF_Floor_MacroTint_1024':        ('macro_tint',  'macro', 40.0, 0.60, (0.3, 1.0), 1.0),
    'VF_Floor_Cracks_2048':           ('overlay', 'floor', 8.0, 0.75, (0.4, 0.9), 0.35),
    'VF_Floor_Wear_1024':             ('overlay', 'floor', 4.0, 0.50, (0.25, 0.7), 0.40),
    'VF_Floor_ChippedEdges_1024':     ('overlay', 'floor', 2.0, 0.85, (0.5, 1.0), 0.50),
    'VF_Wall_RainStreaks_1024':       ('overlay', 'wall',  3.0, 0.65, (0.3, 0.9), 1.0),
    'VF_Weather_Salt_1024':           ('overlay', 'any',   2.0, 0.55, (0.3, 0.8), 0.30),
    'VF_Weather_Moss_1024':           ('overlay', 'any',   2.0, 0.70, (0.4, 0.9), 0.0),
    'VF_Weather_MossWallBase_1024':   ('overlay', 'wallbase', 3.0, 0.80, (0.5, 1.0), 1.0),
    'VF_Weather_MossFloorJoints_1024': ('overlay', 'floor', 2.0, 0.80, (0.5, 1.0), 0.0),
    'VF_Weather_SootFloorRing_1024':  ('decal', 'decal', 3.2, 0.85, (0.5, 1.0), 0.0),
    'VF_Weather_SootWallPlume_512x1024': ('decal', 'decal', 3.0, 0.80, (0.5, 1.0), 1.0),
}


def _img(nt, name, data):
    n = nt.nodes.new('ShaderNodeTexImage')
    im = bpy.data.images.get(name + '.png') or bpy.data.images.load(TEX + name + '.png', check_existing=False)
    im.colorspace_settings.name = 'Non-Color' if data else 'sRGB'
    if not data:
        im.alpha_mode = 'STRAIGHT'
    n.image = im; n.interpolation = 'Linear'
    n.extension = 'EXTEND' if data else 'REPEAT'
    return n


def _math(nt, op, a=None, b=None, clamp=False):
    m = nt.nodes.new('ShaderNodeMath'); m.operation = op; m.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _uv(nt, ux, vy):
    c = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(ux, c.inputs[0]); nt.links.new(vy, c.inputs[1])
    return c.outputs[0]


def build(nt, color_sock, P, N, layers, view_map=False, radial=True):
    """layers: list of (name, opacity, mode) where mode in {'floor','wall'} selects mapping flavour.
    P: world position socket; N: world normal socket; radial: socket 'weight inside circle' multiplier source (r in metres) or None."""
    sep = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(P, sep.inputs[0]); X, Y, Z = sep.outputs
    sepn = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(N, sepn.inputs[0])
    cur = color_sock
    # radius from the arena centre (Unity x,z = Blender x,y)
    r = _math(nt, 'POWER', _math(nt, 'ADD', _math(nt, 'MULTIPLY', X, X), _math(nt, 'MULTIPLY', Y, Y)), 0.5)
    inside = _math(nt, 'LESS_THAN', r, 10.0)          # 1 inside combat circle
    for name, k, mode in layers:
        kind, mapping, T, kd, rng, win = SPEC[name]
        if kind in ('macro_value', 'macro_tint'):
            im = _img(nt, name, True)
            nt.links.new(_uv(nt, _math(nt, 'DIVIDE', _math(nt, 'ADD', X, 20.0), 40.0), _math(nt, 'DIVIDE', _math(nt, 'ADD', Y, 20.0), 40.0)), im.inputs['Vector'])
            mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MULTIPLY'
            mix.inputs[0].default_value = k
            nt.links.new(cur, mix.inputs[6])
            if kind == 'macro_value':
                g = _math(nt, 'MULTIPLY', _sepr(nt, im), 2.0)
                comb = nt.nodes.new('ShaderNodeCombineColor')
                for i in range(3):
                    nt.links.new(g, comb.inputs[i])
                nt.links.new(comb.outputs[0], mix.inputs[7])
            else:
                vm = nt.nodes.new('ShaderNodeVectorMath'); vm.operation = 'SCALE'; vm.inputs['Scale'].default_value = 2.0
                nt.links.new(im.outputs['Color'], vm.inputs[0])
                nt.links.new(vm.outputs[0], mix.inputs[7])
            cur = mix.outputs[2]
            if view_map:
                cur = (comb.outputs[0] if kind == 'macro_value' else im.outputs['Color'])
                if kind == 'macro_value':
                    gg = _sepr(nt, im); comb2 = nt.nodes.new('ShaderNodeCombineColor')
                    for i in range(3):
                        nt.links.new(gg, comb2.inputs[i])
                    cur = comb2.outputs[0]
            continue
        # tiled / decal overlay
        if mode == 'wall' and mapping in ('any', 'floor'):
            mapping = 'wall'
        if mapping == 'decal':
            if 'Ring' in name:
                u = _math(nt, 'ADD', _math(nt, 'DIVIDE', X, T), 0.5); v = _math(nt, 'ADD', _math(nt, 'DIVIDE', Y, T), 0.5)
            else:   # wall plume: 1.5 m wide x 3.0 m tall, bottom edge 1.3 m above the floor, centred on x=0
                u = _math(nt, 'ADD', _math(nt, 'DIVIDE', X, 1.5), 0.5); v = _math(nt, 'DIVIDE', _math(nt, 'SUBTRACT', Z, 1.3), 3.0)
        elif mapping in ('wall', 'wallbase'):
            along = _math(nt, 'ADD', X, _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', Y, X), _math(nt, 'GREATER_THAN', _math(nt, 'ABSOLUTE', sepn.outputs[0]), _math(nt, 'ABSOLUTE', sepn.outputs[1]))))
            u = _math(nt, 'DIVIDE', along, T); v = _math(nt, 'DIVIDE', Z, T)
        else:
            u = _math(nt, 'DIVIDE', X, T); v = _math(nt, 'DIVIDE', Y, T)
        im = _img(nt, name, False)
        if mapping == 'decal':
            im.extension = 'CLIP'
        nt.links.new(_uv(nt, u, v), im.inputs['Vector'])
        a = im.outputs['Alpha']
        if mapping == 'wallbase':   # V does not tile: only 0..1 (0..3 m) above the base
            a = _math(nt, 'MULTIPLY', a, _math(nt, 'MULTIPLY', _math(nt, 'GREATER_THAN', v, 0.0), _math(nt, 'LESS_THAN', v, 1.0)))
        w = 1.0
        wnode = None
        if win < 1.0 and radial:
            wnode = _math(nt, 'SUBTRACT', 1.0, _math(nt, 'MULTIPLY', inside, 1.0 - win))
        fac = _math(nt, 'MULTIPLY', a, k)
        if mapping in ('floor', 'any') and kind == 'overlay':
            # planar top-down projection stretches on vertical faces (stair risers, platform sides): keep only up-facing surfaces. Blender +Z = Unity +Y.
            up = _math(nt, 'MULTIPLY', _math(nt, 'SUBTRACT', sepn.outputs[2], 0.55), 1.0 / 0.30, clamp=True)
            fac = _math(nt, 'MULTIPLY', fac, up)
        if wnode is not None:
            fac = _math(nt, 'MULTIPLY', fac, wnode)
        mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'; mix.blend_type = 'MIX'
        nt.links.new(fac, mix.inputs[0]); nt.links.new(cur, mix.inputs[6])
        if view_map:
            mix.inputs[7].default_value = (1, 1, 1, 1)
        else:
            nt.links.new(im.outputs['Color'], mix.inputs[7])
        cur = mix.outputs[2]
    return cur


def _sepr(nt, im):
    s = nt.nodes.new('ShaderNodeSeparateColor'); nt.links.new(im.outputs['Color'], s.inputs[0]); return s.outputs[0]

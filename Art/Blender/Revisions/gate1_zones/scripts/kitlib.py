"""MythicRoguelite - Temple environment kit helper library (Blender 5.x, run headless).

Conventions: 1 BU = 1 m, +Z up. Piece pivots are baked into mesh coordinates.
Nothing here depends on the live Blender session; scripts run via `Blender -b`.
"""
import bpy, bmesh, math, random, os
import numpy as np
from mathutils import Vector, Matrix, noise

TAU = math.tau

# ----------------------------------------------------------------------------
# Material slots (indices used while modelling)
# ----------------------------------------------------------------------------
M_STONE, M_CHARCOAL, M_BRONZE, M_GOLD, M_CRIMSON, M_EMBER = range(6)
SRC_MATS = ['SRC_Temple_StoneWarm', 'SRC_Temple_StoneCharcoal', 'SRC_Temple_Bronze',
            'SRC_Temple_Gold', 'SRC_Temple_CrimsonCloth', 'SRC_Temple_EmberAmber']
ZONE_ATTR = 'zone_id'          # FACE-domain INT attribute; value = index into SRC_MATS (== M_* constants)
ZONE_NAMES = {i: n.replace('SRC_Temple_', '') for i, n in enumerate(SRC_MATS)}


def zone_counts(obj):
    """{zone_id: face_count} read from the persistent attribute, or None when the mesh has no zone attribute."""
    a = obj.data.attributes.get(ZONE_ATTR)
    if a is None:
        return None
    n = len(obj.data.polygons)
    arr = np.empty(n, dtype=np.int32); a.data.foreach_get('value', arr)
    u, c = np.unique(arr, return_counts=True)
    return {int(k): int(v) for k, v in zip(u, c)}


def restore_zone_slots(obj):
    """Rebuild the SRC material slots + per-face material_index from zone_id (exactly what to_object produced originally:
    slots = used zones in ascending order). Returns the zone->slot map."""
    a = obj.data.attributes[ZONE_ATTR]
    n = len(obj.data.polygons)
    arr = np.empty(n, dtype=np.int32); a.data.foreach_get('value', arr)
    used = sorted(int(z) for z in np.unique(arr))
    obj.data.materials.clear()
    for z in used:
        obj.data.materials.append(bpy.data.materials[SRC_MATS[z]])
    remap = np.zeros(max(used) + 1, dtype=np.int32)
    for i, z in enumerate(used):
        remap[z] = i
    obj.data.polygons.foreach_set('material_index', remap[arr])
    obj.data.update()
    return {z: i for i, z in enumerate(used)}


def srgb2lin(c):
    out = []
    for v in c[:3]:
        out.append(v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4)
    return tuple(out) + (1.0,)


def hexc(h):
    h = h.lstrip('#')
    return srgb2lin(tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)))


# ----------------------------------------------------------------------------
# Geometry builder
# ----------------------------------------------------------------------------
class B:
    """Accumulates primitives in one bmesh (one reusable piece = one B)."""

    def __init__(self, name, seed=1):
        self.name, self.seed = name, seed
        self.bm = bmesh.new()
        self.rng = random.Random(seed)
        self.tone = self.bm.verts.layers.float.new('blocktone')
        self.pas = self.bm.verts.layers.int.new('pas')
        self.pass_id = 1

    # -- internals
    def _tag(self, verts, mat, tone):
        faces = set(f for v in verts for f in v.link_faces)
        for f in faces:
            f.material_index = mat
        t = self.rng.random() if tone is None else tone
        for v in verts:
            v[self.tone] = t
            v[self.pas] = self.pass_id

    def _mat4(self, center, rot):
        rx, ry, rz = rot
        return (Matrix.Translation(center) @ Matrix.Rotation(rz, 4, 'Z') @
                Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X'))

    # -- primitives
    def box(self, center, size, mat=M_STONE, tone=None, rot=(0, 0, 0), jitter=0.0):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        sx, sy, sz = size
        if jitter:
            j = self.rng.uniform
            center = Vector(center) + Vector((j(-jitter, jitter), j(-jitter, jitter), 0))
            rot = (rot[0] + j(-jitter, jitter) * 0.02, rot[1] + j(-jitter, jitter) * 0.02, rot[2] + j(-jitter, jitter) * 0.04)
        m = self._mat4(center, rot) @ Matrix.Diagonal((sx, sy, sz, 1.0))
        bmesh.ops.transform(self.bm, matrix=m, verts=r['verts'])
        self._tag(r['verts'], mat, tone)
        return r['verts']

    def cyl(self, base, r1, r2, h, seg=24, mat=M_STONE, tone=None, rot=(0, 0, 0)):
        """Frustum, axis +Z from `base`, r1 at bottom, r2 at top."""
        m = self._mat4(Vector(base) + Vector((0, 0, h / 2)), rot)
        r = bmesh.ops.create_cone(self.bm, cap_ends=True, cap_tris=False, segments=seg,
                                  radius1=r1, radius2=r2, depth=h, matrix=m)
        self._tag(r['verts'], mat, tone)
        return r['verts']

    def lathe(self, profile, seg=32, center=(0, 0, 0), mat=M_STONE, tone=None, radial=None,
              rot=(0, 0, 0), dz=0.2, closed=False, rot_phase=0.0):
        """Revolve [(r,z)...] bottom->top about +Z. radial(theta,z)->multiplier. Capped unless closed."""
        pts = []
        for i in range(len(profile) - 1):
            (r0, z0), (r1, z1) = profile[i], profile[i + 1]
            n = max(1, int(math.ceil(math.hypot(r1 - r0, z1 - z0) / dz)))
            for k in range(n):
                t = k / n
                pts.append((r0 + (r1 - r0) * t, z0 + (z1 - z0) * t))
        pts.append(profile[-1])
        if closed and pts[-1] != pts[0]:
            pass
        mat4 = self._mat4(center, rot)
        rings = []
        for (r, z) in pts:
            ring = []
            for j in range(seg):
                th = TAU * j / seg + rot_phase
                rr = r * (radial(th, z) if radial else 1.0)
                ring.append(self.bm.verts.new(mat4 @ Vector((rr * math.cos(th), rr * math.sin(th), z))))
            rings.append(ring)
        allv = [v for ring in rings for v in ring]
        n_r = len(rings)
        last = n_r if closed else n_r - 1
        for i in range(last):
            a, b = rings[i], rings[(i + 1) % n_r]
            for j in range(seg):
                j2 = (j + 1) % seg
                try:
                    self.bm.faces.new((a[j], a[j2], b[j2], b[j]))
                except ValueError:
                    pass
        if not closed:
            try:
                self.bm.faces.new(list(reversed(rings[0])))
                self.bm.faces.new(rings[-1])
            except ValueError:
                pass
        self._tag(allv, mat, tone)
        return allv

    def torus(self, center, R, r, rot=(0, 0, 0), seg=40, sseg=10, mat=M_BRONZE, tone=None, arc=(0, TAU), stretch=1.0):
        mat4 = self._mat4(center, rot)
        a0, a1 = arc
        full = abs((a1 - a0) - TAU) < 1e-6
        nseg = seg if full else seg + 1
        verts = []
        for i in range(nseg):
            th = a0 + (a1 - a0) * i / seg
            row = []
            for j in range(sseg):
                ph = TAU * j / sseg
                rr = R + r * math.cos(ph)
                row.append(self.bm.verts.new(mat4 @ Vector((rr * math.cos(th), rr * math.sin(th), r * math.sin(ph) * stretch))))
            verts.append(row)
        nrows = seg if full else seg
        for i in range(nrows):
            a, b = verts[i], verts[(i + 1) % nseg]
            for j in range(sseg):
                j2 = (j + 1) % sseg
                try:
                    self.bm.faces.new((a[j], b[j], b[j2], a[j2]))
                except ValueError:
                    pass
        flat = [v for row in verts for v in row]
        if not full:  # cap ends
            try:
                self.bm.faces.new(list(reversed(verts[0])))
                self.bm.faces.new(verts[-1])
            except ValueError:
                pass
        self._tag(flat, mat, tone)
        return flat

    def tube(self, pts, r, sseg=8, mat=M_STONE, tone=None, taper=None):
        """Swept tube along a polyline of Vectors."""
        pts = [Vector(p) for p in pts]
        rows = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            u = t.cross(up).normalized(); v = t.cross(u).normalized()
            rr = r * (taper(i / (len(pts) - 1)) if taper else 1.0)
            rows.append([self.bm.verts.new(p + (u * math.cos(TAU * j / sseg) + v * math.sin(TAU * j / sseg)) * rr) for j in range(sseg)])
        for i in range(len(rows) - 1):
            for j in range(sseg):
                j2 = (j + 1) % sseg
                try:
                    self.bm.faces.new((rows[i][j], rows[i][j2], rows[i + 1][j2], rows[i + 1][j]))
                except ValueError:
                    pass
        try:
            self.bm.faces.new(list(reversed(rows[0]))); self.bm.faces.new(rows[-1])
        except ValueError:
            pass
        flat = [v for row in rows for v in row]
        self._tag(flat, mat, tone)
        return flat

    def annulus(self, center, normal, r_in, r_out, t, seg=48, mat=M_STONE, tone=None):
        """Flat ring (raised relief) standing on a surface whose outward normal is `normal`."""
        n = Vector(normal).normalized()
        q = n.to_track_quat('Z', 'Y')
        m = Matrix.Translation(center) @ q.to_matrix().to_4x4()
        return self.lathe([(r_in, 0), (r_out, 0), (r_out, t), (r_in, t)], seg=seg, center=(0, 0, 0), mat=mat, tone=tone,
                          rot=(0, 0, 0), closed=True) if False else self._annulus_m(m, r_in, r_out, t, seg, mat, tone)

    def _annulus_m(self, m, r_in, r_out, t, seg, mat, tone):
        prof = [(r_in, 0.0), (r_out, 0.0), (r_out, t), (r_in, t)]
        rings = []
        for (r, z) in prof:
            rings.append([self.bm.verts.new(m @ Vector((r * math.cos(TAU * j / seg), r * math.sin(TAU * j / seg), z))) for j in range(seg)])
        for i in range(4):
            a, b = rings[i], rings[(i + 1) % 4]
            for j in range(seg):
                j2 = (j + 1) % seg
                try:
                    self.bm.faces.new((a[j], a[j2], b[j2], b[j]))
                except ValueError:
                    pass
        flat = [v for r in rings for v in r]
        self._tag(flat, mat, tone)
        return flat

    def box_m(self, matrix, size, mat=M_STONE, tone=None):
        """Box placed by an arbitrary 4x4 matrix (unit cube scaled by `size` first)."""
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        bmesh.ops.transform(self.bm, matrix=matrix @ Matrix.Diagonal((size[0], size[1], size[2], 1.0)), verts=r['verts'])
        self._tag(r['verts'], mat, tone)
        return r['verts']

    def hexa(self, p, mat=M_STONE, tone=None):
        """Hexahedron from 8 points: bottom quad p0..p3, top quad p4..p7 (same order)."""
        v = [self.bm.verts.new(Vector(x)) for x in p]
        for idx in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            try:
                self.bm.faces.new([v[i] for i in idx])
            except ValueError:
                pass
        self._tag(v, mat, tone)
        return v

    def prism(self, pts_xz, y0, y1, mat=M_STONE, tone=None):
        """Polygon (x,z) extruded along Y between y0 and y1."""
        f = [self.bm.verts.new((x, y0, z)) for x, z in pts_xz]
        k = [self.bm.verts.new((x, y1, z)) for x, z in pts_xz]
        n = len(pts_xz)
        try:
            self.bm.faces.new(f); self.bm.faces.new(list(reversed(k)))
        except ValueError:
            pass
        for i in range(n):
            j = (i + 1) % n
            try:
                self.bm.faces.new((f[i], f[j], k[j], k[i]))
            except ValueError:
                pass
        self._tag(f + k, mat, tone)
        return f + k

    def drop_bottom(self, z=0.002):
        """Remove hidden floor-contact faces (saves UV area)."""
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        dead = [f for f in bm.faces if f.normal.z < -0.9 and all(v.co.z <= z for v in f.verts)]
        if dead:
            bmesh.ops.delete(bm, geom=dead, context='FACES')

    # -- processing
    def bevel(self, width, segments=2, angle=28.0, only_new=True):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        lim = math.radians(angle)
        edges = []
        for e in bm.edges:
            if len(e.link_faces) != 2:
                continue
            if only_new and not all(v[self.pas] == self.pass_id for v in e.verts):
                continue
            if e.calc_face_angle(0.0) > lim:
                edges.append(e)
        if edges:
            bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=segments,
                            profile=0.55, affect='EDGES', clamp_overlap=True, loop_slide=True)
        self.pass_id += 1

    def unwrap(self, angle=66.0, margin=0.002):
        """Smart-UV the clean (pre-displacement) mesh; later subdivision interpolates the UVs."""
        me = bpy.data.meshes.new('_unwrap_tmp')
        self.bm.to_mesh(me)
        obj = bpy.data.objects.new('_unwrap_tmp', me)
        bpy.context.scene.collection.objects.link(obj)
        smart_uv(obj, angle, margin)
        self.bm.free()
        self.bm = bmesh.new()
        self.bm.from_mesh(me)
        self.tone = self.bm.verts.layers.float['blocktone']
        self.pas = self.bm.verts.layers.int['pas']
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(me)

    def move(self, verts, d):
        bmesh.ops.translate(self.bm, vec=d, verts=verts)

    def sculpt(self, L=0.1, warp=(0.012, 0.9), chip=(0.02, 7.0), fine=(0.003, 22.0), pin_z0=True,
               edge_ang=0.30, hook=None, bend=None):
        """Adaptive subdivide to ~L, then cause-driven displacement:
        low-freq warp (settling), edge-weighted chips (impact), fine pitting."""
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        for _ in range(8):
            long = [e for e in bm.edges if e.calc_length() > L]
            if not long:
                break
            bmesh.ops.subdivide_edges(bm, edges=long, cuts=1, use_grid_fill=False)
            bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
        bm.verts.ensure_lookup_table(); bm.normal_update()
        s = Vector((self.seed * 7.13, self.seed * 3.77, self.seed * 5.31))
        ew = {}
        for v in bm.verts:
            a = 0.0
            for e in v.link_edges:
                if len(e.link_faces) == 2:
                    a = max(a, e.calc_face_angle(0.0))
            ew[v.index] = min(1.0, a / edge_ang)
        ew2 = {}
        for v in bm.verts:
            m = ew[v.index]
            for e in v.link_edges:
                m = max(m, ew[e.other_vert(v).index] * 0.7)
            ew2[v.index] = m
        wa, wf = warp; ca, cf = chip; fa, ff = fine
        for v in bm.verts:
            p = v.co
            if pin_z0 and p.z <= 0.002:
                continue
            n = v.normal
            d = wa * noise.noise(p * wf + s)
            c = max(0.0, noise.noise(p * cf + s * 1.7) + 0.15)
            d -= ca * ew2[v.index] * (0.25 + c * 1.1)
            d += fa * noise.noise(p * ff + s * 2.3)
            v.co = p + n * d
        if hook:
            hook(bm)
        bm.normal_update()

    def shade(self, sharp_angle=0.75):
        bm = self.bm
        for f in bm.faces:
            f.smooth = True
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > sharp_angle:
                e.smooth = False

    def to_object(self, name, coll=None):
        bm = self.bm
        used = sorted(set(f.material_index for f in bm.faces))
        remap = {m: i for i, m in enumerate(used)}
        # GATE-1 (M6): persistent per-face zone id = ORIGINAL global zone (M_STONE..M_EMBER), independent of slot order.
        # Survives bake (material slots get replaced), save/reopen and subdivision; slots can always be rebuilt from it.
        zl = bm.faces.layers.int.get(ZONE_ATTR) or bm.faces.layers.int.new(ZONE_ATTR)
        for f in bm.faces:
            f[zl] = f.material_index
        for f in bm.faces:
            f.material_index = remap[f.material_index]
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        for m in used:
            me.materials.append(bpy.data.materials[SRC_MATS[m]])
        for p in me.polygons:
            p.use_smooth = True
        obj = bpy.data.objects.new(name, me)
        (coll or bpy.context.scene.collection).objects.link(obj)
        bm.free()
        return obj


# ----------------------------------------------------------------------------
# UVs + texel density
# ----------------------------------------------------------------------------
def activate(obj):
    bpy.context.view_layer.update()
    for o in list(bpy.context.view_layer.objects):
        if o is not None:
            o.select_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def smart_uv(obj, angle=66.0, margin=0.003):
    activate(obj)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=margin, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')


def uv_stats(obj):
    me = obj.data
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    verts = np.empty(len(me.vertices) * 3, dtype=np.float32); me.vertices.foreach_get('co', verts); verts = verts.reshape(-1, 3)
    uvl = me.uv_layers.active.data
    uv = np.empty(len(uvl) * 2, dtype=np.float32); uvl.foreach_get('uv', uv); uv = uv.reshape(-1, 2)
    tri_v = np.empty(nt * 3, dtype=np.int32); me.loop_triangles.foreach_get('vertices', tri_v); tri_v = tri_v.reshape(-1, 3)
    tri_l = np.empty(nt * 3, dtype=np.int32); me.loop_triangles.foreach_get('loops', tri_l); tri_l = tri_l.reshape(-1, 3)
    p = verts[tri_v]
    a3 = 0.5 * np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1).sum()
    q = uv[tri_l]
    d1 = q[:, 1] - q[:, 0]; d2 = q[:, 2] - q[:, 0]
    a2 = 0.5 * np.abs(d1[:, 0] * d2[:, 1] - d1[:, 1] * d2[:, 0]).sum()
    return float(a3), float(a2), nt


def pick_res(a3, a2, target_px_per_m, cap=4096, floor=256):
    for r in (256, 512, 1024, 2048, 4096):
        if r < floor:
            continue
        if r * math.sqrt(a2 / a3) >= target_px_per_m * 0.9 or r >= cap:
            return r, r * math.sqrt(a2 / a3)
    return cap, cap * math.sqrt(a2 / a3)


# ----------------------------------------------------------------------------
# Procedural source shaders (bake-only; never exported as nodes)
# ----------------------------------------------------------------------------
def _set(sock, v):
    if isinstance(v, bpy.types.NodeSocket):
        sock.node.id_data.links.new(v, sock)
    else:
        sock.default_value = v


class NB:
    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.n = 0

    def node(self, typ, **props):
        nd = self.nt.nodes.new(typ)
        nd.location = ((self.n % 12) * 220, -(self.n // 12) * 260)
        self.n += 1
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def math(self, op, a, b=None, c=None, clamp=False):
        nd = self.node('ShaderNodeMath', operation=op, use_clamp=clamp)
        _set(nd.inputs[0], a)
        if b is not None: _set(nd.inputs[1], b)
        if c is not None: _set(nd.inputs[2], c)
        return nd.outputs[0]

    def vmath(self, op, a, b=None):
        nd = self.node('ShaderNodeVectorMath', operation=op)
        _set(nd.inputs[0], a)
        if b is not None: _set(nd.inputs[1], b)
        return nd

    def mix(self, fac, a, b):
        nd = self.node('ShaderNodeMix', data_type='RGBA', blend_type='MIX')
        _set(nd.inputs[0], fac); _set(nd.inputs[6], a); _set(nd.inputs[7], b)
        return nd.outputs[2]

    def mul_col(self, col, f):
        nd = self.node('ShaderNodeMix', data_type='RGBA', blend_type='MULTIPLY')
        nd.inputs[0].default_value = 1.0
        _set(nd.inputs[6], col)
        _set(nd.inputs[7], f)
        return nd.outputs[2]

    def ramp(self, fac, stops):
        nd = self.node('ShaderNodeValToRGB')
        cr = nd.color_ramp
        while len(cr.elements) > 1:
            cr.elements.remove(cr.elements[-1])
        cr.elements[0].position, cr.elements[0].color = stops[0]
        for pos, col in stops[1:]:
            e = cr.elements.new(pos); e.color = col
        _set(nd.inputs[0], fac)
        return nd.outputs[0]

    def maprange(self, v, a0, a1, b0, b1, clamp=True):
        nd = self.node('ShaderNodeMapRange', clamp=clamp)
        _set(nd.inputs[0], v)
        nd.inputs[1].default_value = a0; nd.inputs[2].default_value = a1
        nd.inputs[3].default_value = b0; nd.inputs[4].default_value = b1
        return nd.outputs[0]

    def noise(self, vec, scale, detail=4.0, rough=0.55, dist=0.0):
        nd = self.node('ShaderNodeTexNoise', noise_dimensions='3D')
        _set(nd.inputs['Vector'], vec)
        nd.inputs['Scale'].default_value = scale
        nd.inputs['Detail'].default_value = detail
        nd.inputs['Roughness'].default_value = rough
        nd.inputs['Distortion'].default_value = dist
        return nd.outputs['Fac']


def _common_inputs(nb, seed_off=0.0):
    """Shared coordinate / mask network. Returns dict of value sockets."""
    tc = nb.node('ShaderNodeTexCoord')
    oi = nb.node('ShaderNodeObjectInfo')
    off = nb.node('ShaderNodeCombineXYZ')
    nb.nt.links.new(nb.math('MULTIPLY', oi.outputs['Random'], 37.1), off.inputs[0])
    nb.nt.links.new(nb.math('MULTIPLY', oi.outputs['Random'], 53.7), off.inputs[1])
    nb.nt.links.new(nb.math('MULTIPLY', oi.outputs['Random'], 29.3), off.inputs[2])
    mp = nb.node('ShaderNodeMapping', vector_type='POINT')
    nb.nt.links.new(tc.outputs['Object'], mp.inputs['Location']) if False else None
    nb.nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nb.nt.links.new(off.outputs[0], mp.inputs['Location'])
    P = mp.outputs[0]
    geo = nb.node('ShaderNodeNewGeometry')
    sep = nb.node('ShaderNodeSeparateXYZ')
    nb.nt.links.new(tc.outputs['Object'], sep.inputs[0])
    Z = sep.outputs['Z']
    # object-level knobs (custom props on the object)
    def objprop(name):
        a = nb.node('ShaderNodeAttribute', attribute_type='OBJECT', attribute_name=name)
        return a.outputs['Fac']
    # AO (crevices) + bevel (edges)
    ao = nb.node('ShaderNodeAmbientOcclusion', samples=8, inside=False)
    ao.inputs['Distance'].default_value = 0.30
    bev = nb.node('ShaderNodeBevel', samples=6)
    bev.inputs['Radius'].default_value = 0.035
    dot = nb.vmath('DOT_PRODUCT', bev.outputs['Normal'], geo.outputs['Normal'])
    edge_raw = nb.math('SUBTRACT', 1.0, dot.outputs['Value'])
    n_hi = nb.noise(P, 55.0, 6.0, 0.6)
    n_lo = nb.noise(P, 0.55, 5.0, 0.55, 0.35)
    n_mid = nb.noise(P, 2.3, 4.0, 0.55)
    n_a = nb.noise(P, 9.0, 3.0, 0.5)
    n_crk = nb.noise(P, 0.9, 3.0, 0.5)
    up = nb.vmath('DOT_PRODUCT', geo.outputs['Normal'], (0.0, 0.0, 1.0))
    top = nb.maprange(up.outputs['Value'], 0.55, 0.95, 0.0, 1.0)
    vor = nb.node('ShaderNodeTexVoronoi', feature='DISTANCE_TO_EDGE', voronoi_dimensions='3D')
    nb.nt.links.new(P, vor.inputs['Vector']); vor.inputs['Scale'].default_value = 1.15; vor.inputs['Randomness'].default_value = 1.0
    crack_line = nb.maprange(vor.outputs['Distance'], 0.0, 0.028, 1.0, 0.0)
    crack_mask = nb.maprange(n_crk, 0.58, 0.74, 0.0, 1.0)
    cracks = nb.math('MULTIPLY', crack_line, crack_mask)
    tone = nb.node('ShaderNodeAttribute', attribute_type='GEOMETRY', attribute_name='blocktone').outputs['Fac']
    return dict(P=P, Z=Z, ao=ao.outputs['AO'], edge_raw=edge_raw, n_hi=n_hi, n_lo=n_lo, n_mid=n_mid, n_a=n_a,
                top=top, cracks=cracks, tone=tone, objprop=objprop, geo=geo)


def _finish_principled(nb, base, rough, metal=0.0, bump_h=None, bump_str=0.5, bump_dist=0.03, emission=None):
    pb = nb.node('ShaderNodeBsdfPrincipled')
    out = nb.node('ShaderNodeOutputMaterial')
    nb.nt.links.new(pb.outputs[0], out.inputs['Surface'])
    _set(pb.inputs['Base Color'], base)
    _set(pb.inputs['Roughness'], rough)
    _set(pb.inputs['Metallic'], metal)
    pb.inputs['Specular IOR Level'].default_value = 0.4
    if bump_h is not None:
        bp = nb.node('ShaderNodeBump')
        bp.inputs['Strength'].default_value = bump_str
        bp.inputs['Distance'].default_value = bump_dist
        _set(bp.inputs['Height'], bump_h)
        nb.nt.links.new(bp.outputs['Normal'], pb.inputs['Normal'])
    if emission is not None:
        _set(pb.inputs['Emission Color'], emission)
        pb.inputs['Emission Strength'].default_value = 1.0
    return pb


def make_src_materials():
    for nm in SRC_MATS:
        if nm in bpy.data.materials:
            bpy.data.materials.remove(bpy.data.materials[nm])
    # ---- warm stone ---------------------------------------------------------
    def stone(name, stops_hex, charcoal=False):
        mat = bpy.data.materials.new(name); mat.use_fake_user = True
        nb = NB(mat); c = _common_inputs(nb)
        vmult = c['objprop']('value_mult')       # per-object value (floor quieter than walls)
        wmult = c['objprop']('wear_mult')
        dmult = c['objprop']('damp_mult')
        tvar = c['objprop']('tone_var')          # per-slab quarry-tone variation (floors low)
        dirt_k = c['objprop']('dirt_mult')       # crevice/damp grime strength (floors low contrast)
        vm = nb.math('ADD', nb.math('MULTIPLY', vmult, 1.0), 0.0)
        # painterly variation: large patches + medium patches + per-block quarry tone
        V = nb.math('ADD', nb.math('MULTIPLY', c['n_lo'], 0.55), nb.math('MULTIPLY', c['n_mid'], 0.25))
        V = nb.math('ADD', V, nb.math('MULTIPLY', c['n_a'], 0.08))
        V = nb.math('ADD', V, nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('SUBTRACT', c['tone'], 0.5), 0.55), tvar))
        # contrast-stretch the painterly fields on structures (tone_var 0.3 => floors unchanged; 1.0 => 1.8x)
        stretch = nb.math('ADD', 1.0, nb.math('MULTIPLY', nb.math('MAXIMUM', 0.0, nb.math('SUBTRACT', tvar, 0.3)), 1.15))
        V = nb.math('ADD', 0.5, nb.math('MULTIPLY', nb.math('SUBTRACT', V, 0.5), stretch))
        col = nb.ramp(V, [(0.00, hexc(stops_hex[0])), (0.30, hexc(stops_hex[1])),
                          (0.55, hexc(stops_hex[2])), (0.80, hexc(stops_hex[3])), (1.0, hexc(stops_hex[4]))])
        col = nb.mul_col(col, nb.math('MULTIPLY', vmult, 1.0))
        # rising damp / base staining (height driven, broken by noise)
        zz = nb.math('ADD', c['Z'], nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_mid'], 0.5), 0.9))
        damp = nb.maprange(zz, 0.15, 1.5, 1.0, 0.0)
        damp = nb.math('MULTIPLY', damp, dmult)
        # crevice dirt (AO) + edge wear (bevel) + cracks
        crev = nb.maprange(c['ao'], 0.35, 1.0, 1.0, 0.0)
        edge = nb.maprange(nb.math('MULTIPLY', c['edge_raw'], wmult), 0.02, 0.35, 0.0, 1.0)
        edge = nb.math('MULTIPLY', edge, nb.maprange(c['n_hi'], 0.35, 0.65, 0.35, 1.0))
        dirt = nb.math('MINIMUM', 1.0, nb.math('ADD', nb.math('ADD', nb.math('MULTIPLY', crev, 0.85),
                       nb.math('MULTIPLY', damp, 0.68)), nb.math('MULTIPLY', c['cracks'], 0.9)))
        dirt = nb.math('MULTIPLY', dirt, dirt_k)
        dark = hexc('#1E1B18') if not charcoal else hexc('#121110')
        col = nb.mix(nb.math('MULTIPLY', dirt, 0.62), col, dark)
        # sun-bleached / dusty top faces, chalky exposed edges (cause: weather, impacts)
        bleach = hexc('#B3A387') if not charcoal else hexc('#5A544C')
        col = nb.mix(nb.math('MULTIPLY', c['top'], 0.22), col, bleach)
        chalk = hexc('#A8977C') if not charcoal else hexc('#4B463F')
        col = nb.mix(nb.math('MULTIPLY', edge, 0.55), col, chalk)
        rough = nb.math('ADD', 0.80, nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.28))
        rough = nb.math('ADD', rough, nb.math('MULTIPLY', edge, 0.08))
        rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', damp, 0.10))
        rough = nb.math('ADD', rough, nb.math('MULTIPLY', c['cracks'], 0.12))
        rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', c['top'], 0.07))
        rough = nb.math('MAXIMUM', 0.38, nb.math('MINIMUM', 1.0, rough))
        h = nb.math('ADD', nb.math('MULTIPLY', c['n_hi'], 0.35), nb.math('MULTIPLY', c['n_a'], 0.40))
        h = nb.math('SUBTRACT', nb.math('ADD', h, nb.math('MULTIPLY', c['n_mid'], 0.25)), nb.math('MULTIPLY', c['cracks'], 0.9))
        _finish_principled(nb, col, rough, 0.0, bump_h=h, bump_str=0.55, bump_dist=0.04)
        return mat
    stone(SRC_MATS[0], ['#2E2820', '#4F4434', '#756850', '#8C7D62', '#A39373'])
    stone(SRC_MATS[1], ['#14110F', '#221E1B', '#322D28', '#403A33', '#4E4740'], charcoal=True)

    # ---- bronze -------------------------------------------------------------
    mat = bpy.data.materials.new(SRC_MATS[2]); mat.use_fake_user = True
    nb = NB(mat); c = _common_inputs(nb)
    base = nb.ramp(nb.math('ADD', c['n_mid'], nb.math('MULTIPLY', c['n_lo'], 0.5)),
                   [(0.0, hexc('#3F2A17')), (0.5, hexc('#7A5129')), (1.0, hexc('#A87A42'))])
    crev = nb.maprange(c['ao'], 0.4, 1.0, 1.0, 0.0)
    edge = nb.maprange(c['edge_raw'], 0.02, 0.30, 0.0, 1.0)
    patina = nb.math('MINIMUM', 1.0, nb.math('ADD', nb.math('MULTIPLY', crev, 0.9), nb.math('MULTIPLY', nb.maprange(c['n_a'], 0.55, 0.8, 0.0, 0.5), 1.0)))
    base = nb.mix(nb.math('MULTIPLY', patina, 0.75), base, hexc('#2C2A19'))   # dark olive-brown (not teal)
    base = nb.mix(nb.math('MULTIPLY', edge, 0.7), base, hexc('#C79A5A'))      # burnished edges
    rough = nb.math('ADD', 0.42, nb.math('ADD', nb.math('MULTIPLY', patina, 0.30), nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.2)))
    rough = nb.math('SUBTRACT', rough, nb.math('MULTIPLY', edge, 0.18))
    metal = nb.math('SUBTRACT', 1.0, nb.math('MULTIPLY', patina, 0.55))
    h = nb.math('ADD', nb.math('MULTIPLY', c['n_hi'], 0.5), nb.math('MULTIPLY', c['n_a'], 0.5))
    _finish_principled(nb, base, nb.math('MAXIMUM', 0.2, rough), metal, bump_h=h, bump_str=0.25, bump_dist=0.02)

    # ---- gold (accent only) ------------------------------------------------
    mat = bpy.data.materials.new(SRC_MATS[3]); mat.use_fake_user = True
    nb = NB(mat); c = _common_inputs(nb)
    base = nb.ramp(c['n_mid'], [(0.0, hexc('#6B4D1C')), (0.5, hexc('#B38A3A')), (1.0, hexc('#D9B466'))])
    crev = nb.maprange(c['ao'], 0.4, 1.0, 1.0, 0.0)
    edge = nb.maprange(c['edge_raw'], 0.02, 0.30, 0.0, 1.0)
    base = nb.mix(nb.math('MULTIPLY', crev, 0.7), base, hexc('#3A2A10'))
    base = nb.mix(nb.math('MULTIPLY', edge, 0.4), base, hexc('#E5C77E'))
    rough = nb.math('ADD', 0.36, nb.math('ADD', nb.math('MULTIPLY', crev, 0.25), nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.18)))
    h = nb.math('MULTIPLY', c['n_hi'], 0.6)
    _finish_principled(nb, base, rough, 1.0, bump_h=h, bump_str=0.2, bump_dist=0.015)

    # ---- crimson cloth -------------------------------------------------------
    mat = bpy.data.materials.new(SRC_MATS[4]); mat.use_fake_user = True
    nb = NB(mat); c = _common_inputs(nb)
    base = nb.ramp(nb.math('ADD', c['n_mid'], nb.math('MULTIPLY', c['n_lo'], 0.6)),
                   [(0.0, hexc('#3A0A09')), (0.55, hexc('#5E1411')), (1.0, hexc('#7A2018'))])
    zz = nb.math('ADD', c['Z'], nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_mid'], 0.5), 0.6))
    fade = nb.maprange(zz, -1.4, 0.2, 0.0, 1.0)  # lower hem soiled / sun-faded top handled via object-space Z
    crev = nb.maprange(c['ao'], 0.5, 1.0, 1.0, 0.0)
    base = nb.mix(nb.math('MULTIPLY', crev, 0.6), base, hexc('#1C0504'))
    base = nb.mix(nb.math('MULTIPLY', fade, 0.35), base, hexc('#2A1A12'))
    weave = nb.noise(c['P'], 160.0, 2.0, 0.6)
    _finish_principled(nb, base, nb.math('ADD', 0.82, nb.math('MULTIPLY', nb.math('SUBTRACT', c['n_a'], 0.5), 0.1)), 0.0,
                       bump_h=nb.math('ADD', nb.math('MULTIPLY', weave, 0.7), nb.math('MULTIPLY', c['n_a'], 0.3)), bump_str=0.4, bump_dist=0.01)

    # ---- ember (selective warm emissive: sacred brazier / altar core; hue ~25deg, never cyan) -----
    mat = bpy.data.materials.new(SRC_MATS[5]); mat.use_fake_user = True
    nb = NB(mat); c = _common_inputs(nb)
    heat = nb.math('ADD', nb.math('MULTIPLY', c['n_mid'], 0.7), nb.math('MULTIPLY', c['n_a'], 0.45))
    em = nb.ramp(heat, [(0.35, hexc('#2A0A02')), (0.6, hexc('#A33A08')), (0.85, hexc('#F0801C')), (1.0, hexc('#FFC060'))])
    _finish_principled(nb, hexc('#0E0603'), 0.7, 0.0, emission=em)


# ----------------------------------------------------------------------------
# Baking
# ----------------------------------------------------------------------------
def setup_cycles(samples=32):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.samples = samples
    cy.use_denoising = False
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        cy.device = 'GPU'
    except Exception as ex:
        print('GPU setup failed, CPU bake:', ex)
        cy.device = 'CPU'


def _principled(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED':
            return n
    return None


def _out(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'OUTPUT_MATERIAL':
            return n


class _EmitRewire:
    """Temporarily route a Principled input into an Emission shader so Cycles EMIT bake returns it raw."""

    def __init__(self, obj, input_name, scale=1.0):
        self.items = []
        for slot in obj.material_slots:
            mat = slot.material
            nt = mat.node_tree; pb = _principled(mat); out = _out(mat)
            surf = out.inputs['Surface']
            old = surf.links[0].from_socket if surf.links else None
            em = nt.nodes.new('ShaderNodeEmission')
            inp = pb.inputs[input_name]
            if inp.links:
                src = inp.links[0].from_socket
                if src.type == 'VALUE':
                    cmb = nt.nodes.new('ShaderNodeCombineColor')
                    for i in range(3):
                        nt.links.new(src, cmb.inputs[i])
                    nt.links.new(cmb.outputs[0], em.inputs['Color'])
                    self.items.append((mat, em, old, cmb))
                    nt.links.new(em.outputs[0], surf)
                    continue
                nt.links.new(src, em.inputs['Color'])
            else:
                dv = inp.default_value
                try:
                    col = (dv[0], dv[1], dv[2], 1.0)
                except TypeError:
                    col = (dv, dv, dv, 1.0)
                # Principled's default Emission Color is white; it only matters if Emission Strength > 0
                if input_name == 'Emission Color' and not pb.inputs['Emission Strength'].links \
                        and pb.inputs['Emission Strength'].default_value <= 0.0:
                    col = (0.0, 0.0, 0.0, 1.0)
                em.inputs['Color'].default_value = col
            nt.links.new(em.outputs[0], surf)
            self.items.append((mat, em, old, None))

    def restore(self):
        for mat, em, old, extra in self.items:
            nt = mat.node_tree; out = _out(mat)
            if old:
                nt.links.new(old, out.inputs['Surface'])
            nt.nodes.remove(em)
            if extra:
                nt.nodes.remove(extra)


def _new_img(name, res, color=True, alpha=False):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name, res, res, alpha=alpha, float_buffer=False)
    img.colorspace_settings.name = 'sRGB' if color else 'Non-Color'
    return img


def _bake(obj, img, btype, margin=10, **kw):
    nodes_added = []
    for slot in obj.material_slots:
        nt = slot.material.node_tree
        tn = nt.nodes.new('ShaderNodeTexImage'); tn.image = img
        nt.nodes.active = tn; tn.select = True
        nodes_added.append((nt, tn))
    activate(obj)
    bpy.ops.object.bake(type=btype, margin=margin, margin_type='EXTEND', use_clear=True,
                        target='IMAGE_TEXTURES', **kw)
    for nt, tn in nodes_added:
        nt.nodes.remove(tn)


def bake_maps(obj, res, out_dir, prefix, tex_samples=(32, 16, 4)):
    """Bakes BaseColor(albedo), Roughness, Metallic, AO, Normal, Emission(if any). Returns dict name->image."""
    sc = bpy.context.scene
    imgs = {}
    # base colour via emission rewire (Cycles diffuse-colour pass drops metals)
    sc.cycles.samples = tex_samples[0]
    img = _new_img(prefix + '_BaseColor', res); rw = _EmitRewire(obj, 'Base Color')
    _bake(obj, img, 'EMIT'); rw.restore(); imgs['BaseColor'] = img
    sc.cycles.samples = tex_samples[1]
    img = _new_img(prefix + '_Rough', res, False); _bake(obj, img, 'ROUGHNESS'); imgs['Rough'] = img
    sc.cycles.samples = tex_samples[2]
    img = _new_img(prefix + '_Metal', res, False); rw = _EmitRewire(obj, 'Metallic')
    _bake(obj, img, 'EMIT'); rw.restore(); imgs['Metal'] = img
    sc.cycles.samples = tex_samples[1] * 2
    img = _new_img(prefix + '_AO', res, False); _bake(obj, img, 'AO'); imgs['AO'] = img
    sc.cycles.samples = tex_samples[2]
    img = _new_img(prefix + '_Normal', res, False)
    _bake(obj, img, 'NORMAL', normal_space='TANGENT'); imgs['Normal'] = img
    if any('Ember' in s.material.name for s in obj.material_slots):
        img = _new_img(prefix + '_Emission', res); rw = _EmitRewire(obj, 'Emission Color')
        _bake(obj, img, 'EMIT'); rw.restore(); imgs['Emission'] = img
    return imgs


# ----------------------------------------------------------------------------
# Image post-process (numpy) : painterly filter + channel packing
# ----------------------------------------------------------------------------
def img_to_np(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32); img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def np_to_img(arr, name, color=True, alpha=False):
    h, w, _ = arr.shape
    img = _new_img(name, w, color, alpha)
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    return img


def kuwahara(rgb, r):
    """Edge-preserving painterly smoothing (generalised Kuwahara, 4 sectors, integral images)."""
    H, W, C = rgb.shape
    pad = np.pad(rgb, ((r, r), (r, r), (0, 0)), mode='reflect').astype(np.float64)
    lum = pad.mean(axis=2)

    def integ(a):
        I = np.zeros((a.shape[0] + 1, a.shape[1] + 1) + a.shape[2:], dtype=np.float64)
        I[1:, 1:] = a.cumsum(0).cumsum(1)
        return I
    I1, I2 = integ(pad), integ(lum * lum); IL = integ(lum)
    n = (r + 1) ** 2

    def bs(I, y0, y1, x0, x1):  # inclusive offsets relative to pixel, pixel at (y+r,x+r) in pad
        ya, yb, xa, xb = r + y0, r + y1 + 1, r + x0, r + x1 + 1
        return I[yb:yb + H, xb:xb + W] - I[ya:ya + H, xb:xb + W] - I[yb:yb + H, xa:xa + W] + I[ya:ya + H, xa:xa + W]
    best_var = None; best = np.zeros_like(rgb, dtype=np.float64)
    for (y0, y1, x0, x1) in ((-r, 0, -r, 0), (-r, 0, 0, r), (0, r, -r, 0), (0, r, 0, r)):
        m = bs(I1, y0, y1, x0, x1) / n
        ml = bs(IL, y0, y1, x0, x1) / n
        var = bs(I2, y0, y1, x0, x1) / n - ml * ml
        if best_var is None:
            best_var, best = var, m
        else:
            sel = var < best_var
            best = np.where(sel[..., None], m, best); best_var = np.where(sel, var, best_var)
    return best.astype(np.float32)


def painterly(rgb, r, mix):
    k = kuwahara(rgb, r)
    return rgb * (1 - mix) + k * mix


def pack_mask(metal, ao, rough):
    """URP-Lit friendly: R=metallic, G=occlusion, B=0, A=smoothness."""
    h, w, _ = metal.shape
    out = np.zeros((h, w, 4), dtype=np.float32)
    out[..., 0] = metal[..., 0]
    out[..., 1] = ao[..., 0]
    out[..., 3] = 1.0 - rough[..., 0]
    return out

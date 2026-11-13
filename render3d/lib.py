"""3D toolkit for our Shorts (runs inside Blender).

Toy-style world built from bevelled/subdivided primitives: characters with pivots you can
pose every frame, props with live 3D text, town/interior sets, lighting rigs and a
camera that eases between poses. Z is up; characters face -Y (towards the camera).
"""
import math
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "render", "fonts")


# ---------------------------------------------------------------- math
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u):
    u = clamp(u)
    return u * u * u * (u * (u * 6 - 15) + 10)


def prog(t, t0, t1):
    return ease((t - t0) / (t1 - t0)) if t1 > t0 else float(t >= t1)


def pop(t, t0, dur=0.42):
    if t < t0:
        return 0.0
    u = (t - t0) / dur
    return 1.0 if u > 2.5 else 1 - math.exp(-5.5 * u) * math.cos(7.5 * u)


def vlerp(a, b, u):
    return tuple(lerp(x, y, u) for x, y in zip(a, b))


# ---------------------------------------------------------------- scene reset
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    _FONTS.clear()


def coll():
    return bpy.context.scene.collection


# ---------------------------------------------------------------- materials
_MATS = {}


def mat(rgb, rough=0.55, emit=0.0, metal=0.0, name=None):
    key = (tuple(round(c, 3) for c in rgb), rough, emit, metal)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name or f"m{len(_MATS)}")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    _MATS[key] = m
    return m


def hexc(h):
    """sRGB hex -> linear rgb tuple (Blender colours are linear)."""
    h = h.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


C = {k: hexc(v) for k, v in dict(
    skin="#F2C3A0", red="#D23A2E", plaid_d="#8E1E18", jeans="#3D5A99", beard="#7A4A26",
    white="#F7F3EA", black="#1A1414", wood="#B9773F", wood_d="#7E4C26", wood_l="#E0B07A",
    roof="#B4462F", grass="#6DB54C", road="#C9B48A", money="#7CC27A", money_d="#3F8C4A",
    steel="#7E8794", gold="#F4C02A", emerald="#1E8A5A", purple="#7D4CB0", grey="#9A9AA6",
    grey_d="#5C5E6B", cream="#F6E9CD", bread="#D99A4E", sky="#8CC8F0", brick="#C8735A",
    egg="#F8F1E2", stone="#D9D3C5", pink="#F2A7B5", blue="#5AA9E6", yellow="#F7D046",
    sepia="#C9A77C", orange="#E8833A", leaf="#3E9A5A", leaf_d="#2C7A46").items()}


def finish(o, m, bevel=0.0, subsurf=0, smooth=True):
    if m is not None:
        o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bevel", "BEVEL")
        b.width = bevel
        b.segments = 3
        b.limit_method = "ANGLE"
    if subsurf:
        s = o.modifiers.new("sub", "SUBSURF")
        s.levels = s.render_levels = subsurf
    if smooth and hasattr(o.data, "polygons"):
        for p in o.data.polygons:
            p.use_smooth = True
    return o


def _active():
    return bpy.context.active_object


def parent(o, p):
    if p is not None:
        o.parent = p
    return o


def empty(loc=(0, 0, 0), par=None, rot=(0, 0, 0)):
    o = bpy.data.objects.new("e", None)
    coll().objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    return parent(o, par)


def box(loc, size, m, bevel=0.05, par=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
    o = _active()
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(scale=True)
    o.location = loc
    o.rotation_euler = rot
    finish(o, m, bevel, smooth=False)
    return parent(o, par)


def ball(loc, r, m, scale=(1, 1, 1), par=None, seg=32):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=seg, ring_count=seg // 2)
    o = _active()
    o.location = loc
    o.scale = scale
    finish(o, m)
    return parent(o, par)


def cyl(loc, r, depth, m, rot=(0, 0, 0), par=None, verts=32, bevel=0.03, r2=None):
    if r2 is None:
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=depth, vertices=verts)
    else:
        bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=r2, depth=depth, vertices=verts)
    o = _active()
    o.location = loc
    o.rotation_euler = rot
    finish(o, m, bevel)
    return parent(o, par)


def capsule(a, b, r, m, par=None):
    """Rounded limb from point a to point b (local coords of par)."""
    ax, ay, az = a
    bx, by, bz = b
    dx, dy, dz = bx - ax, by - ay, bz - az
    L = math.sqrt(dx * dx + dy * dy + dz * dz) or 1e-6
    o = cyl(((ax + bx) / 2, (ay + by) / 2, (az + bz) / 2), r, L, m, par=par, verts=24, bevel=0)
    o.rotation_mode = "QUATERNION"
    from mathutils import Vector
    o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(Vector((dx, dy, dz)))
    for p in (a, b):
        ball(p, r, m, par=par, seg=20)
    return o


def torus(loc, R, r, m, rot=(0, 0, 0), par=None):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=40,
                                     minor_segments=14)
    o = _active()
    o.location = loc
    o.rotation_euler = rot
    finish(o, m)
    return parent(o, par)


def cone(loc, r, depth, m, par=None, verts=24, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(radius1=r, depth=depth, vertices=verts)
    o = _active()
    o.location = loc
    o.rotation_euler = rot
    finish(o, m, 0.03)
    return parent(o, par)


_FONTS = {}


def text(body, loc, size, m, par=None, font="cap", rot=(math.pi / 2, 0, 0), extrude=0.04,
         align="CENTER"):
    path = os.path.join(FONTS, {"cap": "LuckiestGuy-Regular.ttf", "sign": "Rye-Regular.ttf"}[font])
    if font not in _FONTS:
        _FONTS[font] = bpy.data.fonts.load(path) if os.path.exists(path) else None
    cu = bpy.data.curves.new("t", "FONT")
    cu.body = body
    if _FONTS[font]:
        cu.font = _FONTS[font]
    cu.size = size
    cu.extrude = extrude
    cu.bevel_depth = extrude * 0.25
    cu.align_x = align
    cu.align_y = "CENTER"
    o = bpy.data.objects.new("text", cu)
    coll().objects.link(o)
    o.location = loc
    o.rotation_euler = rot
    o.data.materials.append(m)
    return parent(o, par)


def show(o, visible):
    o.hide_render = not visible
    for ch in o.children_recursive:
        ch.hide_render = not visible


def scale_all(o, s):
    s = max(1e-4, s)
    o.scale = (s, s, s)


# ---------------------------------------------------------------- characters
KINDS = {
    #        height scale, body col, legs col, head col extras
    "boss": dict(h=1.0, w=1.15, body="emerald", legs="grey_d", hair="beard"),
    "gus": dict(h=1.25, w=1.35, body="red", legs="jeans"),
    "mo": dict(h=1.1, w=0.8, body="purple", legs="black"),
    "pike": dict(h=1.35, w=0.75, body="grey", legs="grey_d"),
    "baker": dict(h=1.0, w=1.1, body="white", legs="grey_d"),
    "barber": dict(h=1.0, w=0.95, body="blue", legs="black"),
    "kid1": dict(h=0.65, w=0.9, body="yellow", legs="grey_d"),
    "kid2": dict(h=0.6, w=0.9, body="pink", legs="jeans"),
    "kid3": dict(h=0.62, w=0.9, body="blue", legs="wood_d"),
    "folk1": dict(h=0.95, w=1.0, body="orange", legs="jeans"),
    "folk2": dict(h=0.95, w=1.0, body="blue", legs="grey_d"),
    "folk3": dict(h=0.95, w=1.0, body="yellow", legs="wood_d"),
}


class Person:
    """Toy figure: root (feet) -> hips/legs, body, shoulders/arms, neck/head + face."""

    def __init__(self, kind="boss", loc=(0, 0, 0), rot_z=0.0, scale=1.0):
        k = KINDS[kind]
        self.kind = kind
        self.root = empty(loc, rot=(0, 0, rot_z))
        self.root.scale = (scale, scale, scale)
        h, w = k["h"], k["w"]
        self.h = h
        body_m = mat(C[k["body"]], 0.65)
        legs_m = mat(C[k["legs"]], 0.75)
        skin = mat(C["skin"], 0.6)
        leg_len = 0.62 * h
        self.legs = []
        for x in (-0.2 * w, 0.2 * w):
            hip = empty((x, 0, leg_len + 0.1), self.root)
            capsule((0, 0, 0), (0, 0, -leg_len + 0.12), 0.13 * w ** 0.5, legs_m, hip)
            barefoot = kind == "gus"
            ball((0, -0.06, -leg_len + 0.06), 0.13, skin if barefoot else mat(C["black"], 0.4),
                 (1.0, 1.5, 0.6), hip)
            self.legs.append(hip)
        torso_z = leg_len + 0.1 + 0.42 * h
        self.torso = empty((0, 0, torso_z), self.root)
        ball((0, 0, 0), 0.5, body_m, (w, 0.82 * w, 1.0 * h), self.torso)
        if kind == "gus":
            for z in (-0.25, 0.0, 0.25):
                torus((0, 0, z * h), 0.5 * w * math.cos(z * 1.2) * 0.98, 0.02,
                      mat(C["plaid_d"], 0.7), par=self.torso).scale = (1, 0.82, 0.6)
        if kind == "boss":
            for z in (0.12, -0.05, -0.22):
                ball((0, -0.41 * w, z), 0.045, mat(C["gold"], 0.25, metal=0.8), par=self.torso)
            ball((0, -0.3, 0.32), 0.13, mat(C["white"], 0.5), (1, 0.6, 0.9), self.torso)
        if kind == "baker":
            ball((0, -0.12, -0.05), 0.42, mat(C["white"], 0.6), (w * 0.9, 0.6, 1.0), self.torso)
        self.arms = []
        for side in (-1, 1):
            sh = empty((side * 0.5 * w, 0, 0.22 * h), self.torso)
            capsule((0, 0, 0), (0, 0, -0.55 * h), 0.1 * w ** 0.5, body_m, sh)
            hand = ball((0, 0, -0.6 * h), 0.12 * w ** 0.5, skin, par=sh)
            self.arms.append(sh)
        self.hand_r = self.arms[1].children[-1]
        self.hand_l = self.arms[0].children[-1]
        self.neck = empty((0, 0, 0.5 * h + 0.38), self.torso)
        hr = 0.42
        self.head = ball((0, 0, 0), hr, skin, par=self.neck)
        eye_w = mat(C["white"], 0.2)
        eye_b = mat(C["black"], 0.15)
        self.pupils = []
        self.eyes = []
        for x in (-0.15, 0.15):
            e = ball((x, -hr * 0.9, 0.05), 0.085, eye_w, (1, 0.6, 1.15), self.neck)
            p = ball((x, -hr * 0.97, 0.04), 0.045, eye_b, (1, 0.6, 1.1), self.neck)
            self.eyes.append(e)
            self.pupils.append(p)
        self.mouth = ball((0, -hr * 0.92, -0.17), 0.08, mat(C["plaid_d"], 0.4), (1.4, 0.5, 0.5),
                          self.neck)
        for x in (-0.25, 0.25):
            ball((x, -hr * 0.8, -0.07), 0.07, mat(C["pink"], 0.7), (1, 0.4, 0.7), self.neck)
        ball((0, -hr * 1.0, -0.04), 0.06, skin, par=self.neck)  # nose
        if kind == "gus":
            ball((0, -0.12, -0.18), 0.36, mat(C["beard"], 0.9), (1.05, 0.75, 0.7), self.neck)
            ball((0, 0, 0.22), 0.44, mat(C["red"], 0.8), (1, 1, 0.62), self.neck)
            ball((0, 0, 0.52), 0.1, mat(C["white"], 0.9), par=self.neck)
        elif kind == "boss":
            ball((0, 0.05, 0.22), 0.42, mat(C["beard"], 0.5), (1.02, 1, 0.55), self.neck)
        elif kind == "mo":
            ball((0, 0.05, 0.24), 0.41, mat(C["black"], 0.5), (1, 1, 0.5), self.neck)
            for s in (-1, 1):
                ball((s * 0.13, -hr * 0.92, -0.1), 0.1, mat(C["black"], 0.6), (1.6, 0.5, 0.5),
                     self.neck)
                ball((s * 0.27, -hr * 0.88, -0.03), 0.05, mat(C["black"], 0.6), par=self.neck)
        elif kind == "pike":
            cyl((0, 0, 0.55), 0.3, 0.6, mat(C["grey_d"], 0.5), par=self.neck)
            cyl((0, 0, 0.27), 0.48, 0.05, mat(C["grey_d"], 0.5), par=self.neck)
            ring = torus((0.3, -0.35, -0.6), 0.25, 0.035, mat(C["wood_d"], 0.4),
                         rot=(math.pi / 2, 0, 0), par=self.arms[1])
            ring.location = (0.15, -0.1, -0.85)
            cyl((0.15, -0.1, -0.85), 0.24, 0.02, mat(C["sky"], 0.05), rot=(math.pi / 2, 0, 0),
                par=self.arms[1])
        elif kind == "baker":
            cyl((0, 0, 0.45), 0.3, 0.35, mat(C["white"], 0.8), par=self.neck)
            ball((0, 0, 0.66), 0.36, mat(C["white"], 0.8), (1, 1, 0.55), self.neck)
        elif kind == "barber":
            ball((0, 0.05, 0.22), 0.41, mat(C["black"], 0.5), (1, 1, 0.5), self.neck)
        elif kind.startswith("kid") or kind.startswith("folk"):
            col = {"kid1": "wood_d", "kid2": "orange", "kid3": "black"}.get(kind, "beard")
            ball((0, 0.05, 0.22), 0.42, mat(C[col], 0.6), (1.02, 1, 0.55), self.neck)
        self._mouth_rest = tuple(self.mouth.scale)

    # posing --------------------------------------------------------------
    def pose(self, t, walk=0.0, arms=(10, 10), look=0.0, mouth="smile", bounce=0.0,
             blink=True, nod=0.0, lean=0.0):
        ph = t * 8.5
        for i, hip in enumerate(self.legs):
            hip.rotation_euler = (math.sin(ph + i * math.pi) * 0.55 * walk, 0, 0)
        bob = abs(math.sin(ph)) * 0.08 * walk + math.sin(t * 2.2) * 0.015 + bounce
        self.torso.delta_location = (0, 0, bob)
        self.torso.rotation_euler = (lean, 0, math.sin(t * 1.3) * 0.03)
        for i, sh in enumerate(self.arms):
            side = -1 if i == 0 else 1
            swing = math.sin(ph + (i + 1) * math.pi) * 0.6 * walk
            # arms hang along -Z; +Y rotation swings toward -X, so mirror per side
            sh.rotation_euler = (swing, -side * math.radians(arms[i]), 0)
        self.neck.rotation_euler = (nod + math.sin(t * 1.7) * 0.03, 0, look * 0.6)
        b = 1.0
        if blink:
            pb = (t + hash(self.kind) % 5 * 0.41) % 3.3
            if pb < 0.14:
                b = 0.15
        for e in self.eyes + self.pupils:
            e.scale.z = (1.15 if e in self.eyes else 1.1) * b
        shape = {"smile": (1.4, 0.5, 0.35), "grin": (1.7, 0.5, 0.7), "o": (0.7, 0.5, 0.9),
                 "flat": (1.2, 0.5, 0.15), "sad": (1.1, 0.5, 0.25),
                 "laugh": (1.6, 0.5, 0.6 + 0.3 * abs(math.sin(t * 14)))}[mouth]
        self.mouth.scale = shape


# ---------------------------------------------------------------- props
def tree(loc, s=1.0, m=None):
    x, y, z = loc
    cyl((x, y, z + 0.6 * s), 0.18 * s, 1.2 * s, mat(C["wood_d"], 0.8))
    m = m or mat(C["leaf"], 0.75)
    for i, (r, h) in enumerate(((1.25, 1.6), (1.0, 1.4), (0.72, 1.2))):
        cone((x, y, z + (1.6 + i * 0.85) * s), r * s, h * s, m)


def house(loc, w=3.2, d=2.6, h=2.8, col="wood", roof="roof", door=True, sign=None,
          rot_z=0.0, win_emit=0.0):
    root = empty(loc, rot=(0, 0, rot_z))
    box((0, 0, h / 2), (w, d, h), mat(C[col], 0.7), 0.06, root)
    r = cone((0, 0, h + 0.75), w * 0.82, 1.5, mat(C[roof], 0.6), root, verts=4,
             rot=(0, 0, math.pi / 4))
    r.scale = (1, d / w, 1)
    if door:
        box((0, -d / 2 - 0.03, 0.85), (0.8, 0.08, 1.7), mat(C["wood_d"], 0.6), 0.03, root)
        ball((0.25, -d / 2 - 0.09, 0.85), 0.05, mat(C["gold"], 0.3, metal=0.8), par=root)
    wm = mat(C["yellow"], 0.2, emit=win_emit) if win_emit else mat(C["sky"], 0.1)
    for x in (-w * 0.32, w * 0.32):
        box((x, -d / 2 - 0.02, h * 0.62), (0.75, 0.06, 0.7), wm, 0.02, root)
        box((x, -d / 2 - 0.05, h * 0.62), (0.85, 0.04, 0.08), mat(C["white"], 0.5), 0, root)
    if sign:
        box((0, -d / 2 - 0.12, h + 0.15), (w * 0.8, 0.12, 0.6), mat(C["cream"], 0.6), 0.04, root)
        text(sign, (0, -d / 2 - 0.19, h + 0.15), 0.38, mat(C["black"], 0.5), root, font="sign")
    return root


class Press:
    """Little porch printing press that spits out bills."""

    def __init__(self, loc, s=1.0, rot_z=0.0):
        self.root = empty(loc, rot=(0, 0, rot_z))
        self.root.scale = (s, s, s)
        box((0, 0, 0.45), (1.0, 0.7, 0.9), mat(C["steel"], 0.35, metal=0.4), 0.05, self.root)
        self.roller = cyl((0, -0.1, 0.95), 0.18, 0.9, mat(C["grey_d"], 0.3, metal=0.5),
                          rot=(0, math.pi / 2, 0), par=self.root)
        self.wheel = cyl((0.58, 0, 0.6), 0.3, 0.08, mat(C["grey_d"], 0.3, metal=0.5),
                         rot=(0, math.pi / 2, 0), par=self.root)
        self.bills = [box((0, -0.4, 0.6), (0.5, 0.25, 0.015), mat(C["money"], 0.6), 0.005,
                          self.root) for _ in range(5)]

    def update(self, t, speed=1.0):
        self.roller.rotation_euler = (t * 6 * speed, math.pi / 2, 0)
        self.wheel.rotation_euler = (t * 3 * speed, math.pi / 2, 0)
        for i, b in enumerate(self.bills):
            u = ((t * speed * 0.9) + i / len(self.bills)) % 1.0
            b.location = (math.sin(i * 2.1) * 0.5 * u, -0.4 - u * 1.4, 0.6 + math.sin(u * math.pi) * 0.9)
            b.rotation_euler = (u * 3 + i, u * 2, i)
            show(b, speed > 0)


class CashStack:
    def __init__(self, loc, footprint=(0.9, 0.5), rot_z=0.0):
        self.root = empty(loc, rot=(0, 0, rot_z))
        self.fp = footprint
        self.bundles = []
        mm, band = mat(C["money"], 0.6), mat(C["white"], 0.5)
        for i in range(40):
            row, col_ = divmod(i, 4)
            b = box(((col_ % 2 - 0.5) * footprint[0] * 0.5, (col_ // 2 - 0.5) * footprint[1] * 0.5,
                     0.06 + row * 0.12), (footprint[0] * 0.48, footprint[1] * 0.48, 0.11), mm, 0.01,
                    self.root)
            box((0, 0, 0), (0.06, footprint[1] * 0.49, 0.115), band, 0, b)
            self.bundles.append(b)

    def set_level(self, n):
        for i, b in enumerate(self.bundles):
            show(b, i < n)


def loaf(loc, par=None, s=1.0):
    o = ball(loc, 0.5 * s, mat(C["bread"], 0.7), (1.4, 0.75, 0.6), par)
    for k in (-0.3, 0, 0.3):
        ball((loc[0] + k * s, loc[1] - 0.05 * s, loc[2] + 0.22 * s), 0.12 * s, mat(C["cream"], 0.8),
             (0.4, 1.5, 0.3), par)
    return o


class PriceTag:
    def __init__(self, loc, value="$1", par=None, s=1.0):
        self.root = empty(loc, par)
        self.root.scale = (s, s, s)
        box((0, 0, 0), (1.3, 0.06, 0.6), mat(C["white"], 0.5), 0.04, self.root)
        cyl((-0.55, -0.02, 0.18), 0.05, 0.08, mat(C["black"], 0.5), rot=(math.pi / 2, 0, 0),
            par=self.root)
        self.txt = text(value, (0.08, -0.06, -0.02), 0.36, mat(C["red"], 0.4), self.root)

    def set(self, value):
        self.txt.data.body = value


def chicken(loc, s=1.0, rot_z=0.0):
    root = empty(loc, rot=(0, 0, rot_z))
    root.scale = (s, s, s)
    wm = mat(C["white"], 0.8)
    body = ball((0, 0, 0.45), 0.35, wm, (1.2, 0.9, 0.9), root)
    ball((0.35, 0, 0.35), 0.2, wm, (1, 0.7, 1.4), root)  # tail
    head = empty((-0.32, 0, 0.8), root)
    ball((0, 0, 0), 0.18, wm, par=head)
    for z in (0.16, 0.2, 0.16):
        ball((0.05 * (z - 0.18) * 20, 0, z + 0.03), 0.06, mat(C["red"], 0.6), par=head)
    cone((-0.18, 0, 0), 0.06, 0.16, mat(C["orange"], 0.5), head, rot=(0, -math.pi / 2, 0))
    ball((-0.08, -0.12, 0.05), 0.035, mat(C["black"], 0.2), par=head)
    ball((-0.08, 0.12, 0.05), 0.035, mat(C["black"], 0.2), par=head)
    for y in (-0.1, 0.1):
        cyl((0, y, 0.12), 0.025, 0.25, mat(C["orange"], 0.5), par=root)
    return root, head


def egg_basket(loc):
    root = empty(loc)
    cyl((0, 0, 0.2), 0.55, 0.4, mat(C["wood_l"], 0.8), par=root, r2=0.45)
    torus((0, 0, 0.75), 0.45, 0.04, mat(C["wood_l"], 0.8), rot=(math.pi / 2, 0, 0), par=root)
    for i in range(7):
        a = i / 7 * math.tau
        ball((math.cos(a) * 0.28, math.sin(a) * 0.28, 0.45), 0.14, mat(C["egg"], 0.6),
             (0.85, 0.85, 1.1), root)
    return root


def wheelbarrow(loc, rot_z=0.0):
    root = empty(loc, rot=(0, 0, rot_z))
    cyl((0.9, 0, 0.3), 0.3, 0.12, mat(C["black"], 0.6), rot=(math.pi / 2, 0, 0), par=root)
    tray = box((0, 0, 0.75), (1.6, 1.0, 0.5), mat(C["red"], 0.5), 0.06, root)
    for y in (-0.4, 0.4):
        capsule((0.2, y, 0.55), (-1.4, y, 0.85), 0.05, mat(C["wood_d"], 0.6), root)
    for i in range(14):
        box((-0.5 + (i % 4) * 0.33, -0.3 + (i // 4 % 2) * 0.6, 1.05 + (i // 8) * 0.13),
            (0.32, 0.4, 0.12), mat(C["money"], 0.6), 0.01, root,
            rot=(0, 0, (i * 0.37) % 0.5 - 0.25))
    return root


# ---------------------------------------------------------------- sets & lighting
def ground(m=None, size=200):
    bpy.ops.mesh.primitive_plane_add(size=size)
    return finish(_active(), m or mat(C["grass"], 0.95))


def road(y=-1.5, width=3.0):
    box((0, y, 0.005), (200, width, 0.01), mat(C["road"], 0.95), 0)


def world(top="sky", strength=1.0, rgb=None):
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*(rgb or C[top]), 1)
    bg.inputs[1].default_value = strength


def sun(rot=(50, 0, 30), energy=3.5, color=(1, 0.96, 0.9), angle=6):
    bpy.ops.object.light_add(type="SUN", rotation=tuple(math.radians(a) for a in rot))
    s = _active()
    s.data.energy = energy
    s.data.color = color
    s.data.angle = math.radians(angle)
    return s


def area(loc, rot, energy=400, size=6, color=(1, 1, 1)):
    bpy.ops.object.light_add(type="AREA", location=loc,
                             rotation=tuple(math.radians(a) for a in rot))
    a = _active()
    a.data.energy = energy
    a.data.size = size
    a.data.color = color
    return a


def point(loc, energy=200, color=(1, 0.8, 0.5), radius=0.2):
    bpy.ops.object.light_add(type="POINT", location=loc)
    p = _active()
    p.data.energy = energy
    p.data.color = color
    p.data.shadow_soft_size = radius
    return p


def lighting(env):
    if env == "day":
        world(rgb=hexc("#9CCFF2"), strength=0.9)
        sun((52, 0, 35), 4.0, (1, 0.95, 0.86))
        area((6, -10, 8), (55, 0, 30), 500, 10, (0.85, 0.9, 1))
    elif env == "sunrise":
        world(rgb=hexc("#F2B88C"), strength=0.8)
        sun((72, 0, -40), 3.5, (1, 0.78, 0.55))
        area((-6, -10, 6), (60, 0, -30), 400, 10, (1, 0.85, 0.75))
    elif env == "night":
        world(rgb=hexc("#1C2450"), strength=0.5)
        sun((60, 0, 20), 0.6, (0.6, 0.7, 1.0))
        area((5, -9, 7), (55, 0, 30), 150, 10, (0.6, 0.7, 1))
    elif env == "interior":
        world(rgb=hexc("#E8C9A0"), strength=0.5)
        area((0, -6, 5), (60, 0, 0), 900, 8, (1, 0.93, 0.85))
        area((-4, -2, 4), (50, 0, -60), 300, 4, (1, 0.85, 0.7))
        point((2, 1, 3.5), 250, (1, 0.85, 0.6), 0.5)
    elif env == "sepia":
        world(rgb=hexc("#D9B98A"), strength=0.7)
        sun((48, 0, 25), 3.0, (1, 0.85, 0.65))
        area((4, -9, 6), (55, 0, 20), 300, 8, (1, 0.9, 0.75))


class Cam:
    """Camera aimed at a target empty; both ease between start/end poses."""

    def __init__(self, lens=32, dof=None):
        bpy.ops.object.camera_add()
        self.cam = _active()
        self.cam.data.lens = lens
        self.target = empty()
        c = self.cam.constraints.new("TRACK_TO")
        c.target = self.target
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        bpy.context.scene.camera = self.cam
        if dof:
            self.cam.data.dof.use_dof = True
            self.cam.data.dof.focus_object = self.target
            self.cam.data.dof.aperture_fstop = dof

    def set(self, pos, look, t=0.0, drift=1.0):
        x, y, z = pos
        self.cam.location = (x + math.sin(t * 0.6) * 0.06 * drift, y,
                             z + math.sin(t * 0.5 + 1) * 0.04 * drift)
        self.target.location = look

    def move(self, a, b, u, la, lb, t=0.0):
        self.set(vlerp(a, b, ease(u)), vlerp(la, lb, ease(u)), t)


def setup_render(width, height, samples=16):
    sc = bpy.context.scene
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    try:
        sc.eevee.taa_render_samples = samples
    except AttributeError:
        pass
    for attr, val in (("use_shadows", True), ("use_gtao", True), ("use_raytracing", False)):
        if hasattr(sc.eevee, attr):
            setattr(sc.eevee, attr, val)
    sc.render.resolution_x, sc.render.resolution_y = width, height
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.film_transparent = False
    vt = [t.identifier for t in
          bpy.types.ColorManagedViewSettings.bl_rna.properties["view_transform"].enum_items_static]
    sc.view_settings.view_transform = "AgX" if "AgX" in vt else "Filmic"
    try:
        sc.view_settings.look = "AgX - Punchy" if "AgX" in vt else "Medium High Contrast"
    except TypeError:
        pass
    sc.view_settings.exposure = 0.3

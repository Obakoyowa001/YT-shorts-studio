"""Channel branding in 3D: Gus avatar (profile picture) and channel banner.

blender -b --python render3d/branding.py -- OUT_DIR [SAMPLES]
Writes avatar.png (1080x1080) and banner.png (2560x1440, YouTube banner size).
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lib  # noqa: E402
from lib import (C, CashStack, Person, area, ball, box, chicken, cyl, ground, house, mat, text,  # noqa: E402
                 tree, world)

argv = sys.argv[sys.argv.index("--") + 1:]
OUT = argv[0]
SAMPLES = int(argv[1]) if len(argv) > 1 else 96
os.makedirs(OUT, exist_ok=True)


def cycles(w, h):
    sc = bpy.context.scene
    lib.setup_render(w, h)
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 6


def camera(loc, look, lens, fit="AUTO", dof=None):
    bpy.ops.object.camera_add(location=loc)
    cam = bpy.context.active_object
    cam.data.lens = lens
    cam.data.sensor_fit = fit
    tgt = lib.empty(look)
    c = cam.constraints.new("TRACK_TO")
    c.target = tgt
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    bpy.context.scene.camera = cam
    if dof:
        cam.data.dof.use_dof = True
        cam.data.dof.focus_object = tgt
        cam.data.dof.aperture_fstop = dof
    return cam


def render(name):
    bpy.context.view_layer.update()
    bpy.context.scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)


def coin_disc(loc, r, tilt=0.6):
    o = cyl(loc, r, r * 0.22, mat(C["gold"], 0.25, metal=0.9), rot=(math.pi / 2 - tilt, tilt * 0.5, 0))
    cyl((0, 0, r * 0.12), r * 0.7, r * 0.04, mat(C["gold"], 0.35, metal=0.9), par=o)
    return o


def happy_mouth(p):
    """Open smile with teeth (branding close-ups only; video model unchanged)."""
    p.mouth.data.materials[0] = mat(lib.hexc("#5A1E1E"), 0.5)
    p.mouth.scale = (1.9, 0.5, 0.75)
    ball(tuple(p.mouth.location + type(p.mouth.location)((0, -0.035, 0.03))), 0.08,
         mat(C["white"], 0.3), (1.6, 0.35, 0.28), p.neck)


def flying_cash(n, x_range, z_range, y=0.6, seed=3):
    import random
    r = random.Random(seed)
    for i in range(n):
        b = box((r.uniform(*x_range), y + r.uniform(-0.4, 1.2), r.uniform(*z_range)),
                (0.42, 0.2, 0.012), mat(C["money"], 0.6), 0.005)
        b.rotation_euler = (r.uniform(0, 3), r.uniform(0, 3), r.uniform(0, 3))


# ---------------------------------------------------------------- avatar
lib.reset()
world(rgb=lib.hexc("#F7C948"), strength=1.0)
box((0, 3.5, 2.5), (20, 0.2, 12), mat(lib.hexc("#F4B728"), 0.9), 0)          # gold backdrop
ground(mat(lib.hexc("#F4B728"), 0.9))
lib.sun((55, 0, 25), 3.2, (1, 0.96, 0.9), 8)
area((-3, -5, 4), (60, 0, -35), 900, 5, (1, 0.95, 0.9))                         # key
area((3.5, 2, 4), (60, 0, 150), 700, 3, (1, 0.9, 0.75))                         # rim
gus = Person("gus", (0, 0, 0))
gus.pose(0.35, arms=(25, 150), mouth="grin", look=0.0, blink=False)
happy_mouth(gus)
gus.neck.rotation_euler = (0.05, 0.12, 0.08)
camera((0.15, -4.2, 2.75), (0.12, 0, 2.45), 70)
cycles(1080, 1080)
render("avatar.png")

# ---------------------------------------------------------------- banner
lib.reset()
world(rgb=lib.hexc("#9CCFF2"), strength=1.0)
ground()
lib.road(-0.3, 2.6)
lib.sun((50, 0, 30), 4.0, (1, 0.95, 0.86), 6)
area((0, -9, 6), (60, 0, 0), 900, 12, (1, 0.97, 0.92))
for i, x in enumerate((-9, -5.2, -1.4, 2.4, 6.2, 10)):
    house((x, 8, 0), col=("wood", "brick", "wood_l", "stone", "wood", "brick")[i])
for x, y, s in ((-11, 12, 1.3), (-3.5, 13, 1.2), (4.5, 12.5, 1.4), (11.5, 11, 1.2)):
    tree((x, y, 0), s)
# key elements inside the safe band (centre 1546x423 px of 2560x1440)
gus = Person("gus", (-1.55, 0.2, 0))
gus.pose(0.35, arms=(30, 155), mouth="grin", look=0.25, blink=False)
happy_mouth(gus)
title = text("ASK GUS", (0.62, 0, 2.52), 0.66, mat(C["gold"], 0.25, metal=0.3), extrude=0.09)
title_shadow = text("ASK GUS", (0.66, 0.05, 2.48), 0.66, mat(C["black"], 0.6), extrude=0.09)
box((0.62, 0.06, 2.0), (2.7, 0.06, 0.36), mat(lib.hexc("#2B1D16"), 0.6), 0.06)      # ribbon
text("HOW MONEY REALLY WORKS", (0.62, 0, 1.99), 0.2, mat(C["gold"], 0.3), extrude=0.02)
ch, head = chicken((2.75, -0.2, 1.05), 0.6, rot_z=0.5)
st = CashStack((-3.3, 0.6, 0), (1.0, 0.6))
st.set_level(26)
flying_cash(22, (-4.5, 4.5), (2.9, 4.2))
for i, (x, z) in enumerate(((-2.6, 2.95), (2.0, 3.05), (-0.4, 3.25), (3.3, 2.7))):
    coin_disc((x, -0.1, z), 0.16, tilt=0.6 + i * 0.4)
camera((0, -10, 2.4), (0, 0, 2.4), 50, fit="HORIZONTAL", dof=5.6)
cycles(2560, 1440)
render("banner.png")
print("BRANDING DONE", flush=True)

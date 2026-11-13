"""3D shots for Short #002 (runs inside Blender). SHOTS[i](d) builds shot i's set and
returns update(t) which poses everything for time t (seconds into the shot)."""
import math

import bpy

from lib import (C, Cam, CashStack, Person, Press, PriceTag, ball, box, chicken, cone, cyl,
                 egg_basket, empty, ground, house, lerp, lighting, loaf, mat, point, pop, prog,
                 road, scale_all, show, text, torus, tree, wheelbarrow)

HOUSE_X = (-10, -5, 0, 5, 10)
HOUSE_COLS = ("wood", "brick", "wood_l", "stone", "wood")


def town(night=False, presses=True):
    ground()
    road(-0.8, 3.2)
    ps = []
    for i, x in enumerate(HOUSE_X):
        house((x, 4.5, 0), col=HOUSE_COLS[i], win_emit=4.0 if night else 0.0)
        if presses:
            ps.append(Press((x + 0.9, 2.1, 0), 0.9))
            if night:
                point((x + 0.9, 1.2, 2.0), 120, (1, 0.8, 0.5), 0.4)
    for x, y, s in ((-13, 9, 1.2), (-7, 10, 1.0), (3, 11, 1.3), (8, 9.5, 1.1), (13, 10, 1.2),
                    (-2, 13, 1.4)):
        tree((x, y, 0), s)
    return ps


def bakery_interior():
    ground(mat(C["wood_l"], 0.8))
    box((0, 3.5, 3), (16, 0.3, 6), mat(C["cream"], 0.85), 0)        # back wall
    for x in (-3, 0, 3):
        box((x, 3.25, 2.6), (2.2, 0.4, 0.12), mat(C["wood_d"], 0.6), 0.02)
        for k in (-0.6, 0, 0.6):
            loaf((x + k, 3.15, 2.85), s=0.45)
    box((0, 0.8, 0.55), (5.2, 1.0, 1.1), mat(C["wood"], 0.6), 0.06)  # counter
    box((0, 0.8, 1.13), (5.4, 1.1, 0.08), mat(C["wood_l"], 0.5), 0.03)
    box((0, 3.3, 4.6), (4, 0.15, 0.9), mat(C["cream"], 0.6), 0.04)
    text("BAKERY", (0, 3.2, 4.6), 0.6, mat(C["roof"], 0.5), font="sign")


# 1 ------------------------------------------------------------------------
def s01(d):
    lighting("sunrise")
    ps = town()
    cam = Cam(30)

    def update(t):
        for i, p in enumerate(ps):
            p.update(t + i * 0.3, 1.0 if t > 0.3 + i * 0.25 else 0.0)
        cam.move((0, -16, 13), (0.5, -11, 3.8), t / d, (0, 3, 3.5), (0.3, 3, 1.8), t)
    return update


# 2 ------------------------------------------------------------------------
def s02(d):
    lighting("day")
    town(presses=False)
    press = Press((-0.6, 1.7, 0), 1.0)
    stack = CashStack((-2.2, 1.2, 0), (1.0, 0.6))
    boss = Person("boss", (1.3, 0.7, 0))
    cam = Cam(35, dof=2.8)

    def update(t):
        press.update(t, 1.4)
        stack.set_level(int(lerp(4, 40, prog(t, 0, d))))
        u = pop(t, 0.35)
        boss.pose(t, arms=(lerp(15, 150, min(1, u)), lerp(15, 150, min(1, u))), mouth="grin",
                  bounce=abs(math.sin(t * 7)) * 0.08 * min(1, u), look=0.2)
        cam.move((1.5, -5.6, 2.3), (0.8, -4.4, 1.9), t / d, (0, 1.2, 1.4), (-0.2, 1.2, 1.3), t)
    return update


# 3 ------------------------------------------------------------------------
def s03(d):
    lighting("day")
    town(presses=False)
    for i, x in enumerate(HOUSE_X[:-1]):
        st = CashStack((x + 1.2, 2.0, 0), (0.9, 0.5))
        st.set_level(18 + i * 5)
        Person(("folk1", "folk2", "folk3", "boss")[i], (x - 0.4, 1.7, 0)).pose(0.4 * i,
                                                                                arms=(30, 120))
    big = CashStack((10.6, 1.6, 0), (1.2, 0.8))
    scale_all(big.root, 1.6)
    big.set_level(40)
    gus = Person("gus", (9.4, 0.8, 0), rot_z=-0.4)
    cam = Cam(32)

    def update(t):
        u = prog(t, 0, d * 0.85)
        gus.pose(t, arms=(55, 75), mouth="grin", lean=-0.12, look=-0.4)
        cam.set((lerp(-9, 8.5, u), -5.5, 2.4), (lerp(-8.5, 9.8, u), 1.5, 1.6), t)
    return update


# 4 ------------------------------------------------------------------------
def s04(d):
    lighting("day")
    town(presses=False)
    boss = Person("boss", (-7, -0.8, 0), rot_z=math.pi / 2)
    case = box((0, -0.15, -0.25), (0.5, 0.18, 0.38), mat(C["wood_d"], 0.5), 0.03, boss.hand_r)
    box((0, 0, 0.0), (0.42, 0.2, 0.3), mat(C["money"], 0.6), 0.01, case)
    cam = Cam(30, dof=3.5)

    def update(t):
        x = lerp(-7, 6, t / d)
        boss.root.location.x = x
        boss.pose(t * 1.5, walk=1.4, arms=(20, 20), mouth="grin", lean=0.2)
        cam.set((x - 0.5, -7.2, 1.7), (x + 0.6, -0.8, 1.1), t)
    return update


# 5 ------------------------------------------------------------------------
def s05(d):
    lighting("interior")
    bakery_interior()
    baker = Person("baker", (0.6, 2.0, 0))
    gus = Person("gus", (0.4, -0.3, 0), rot_z=math.pi * 0.9)
    pile = CashStack((-0.6, 0.85, 1.17), (1.2, 0.7))
    pile.set_level(40)
    boss = Person("boss", (-6, -0.6, 0), rot_z=-math.pi / 2)
    cam = Cam(30, dof=4)

    def update(t):
        baker.pose(t, arms=(20, 20), mouth="o", look=0.3)
        gus.pose(t, arms=(40, 20), mouth="grin", look=-0.3)
        u = prog(t, 0.0, d * 0.7)
        boss.root.location.x = lerp(-6, -2.4, u)
        boss.pose(t * 1.4, walk=1.2 * (1 - prog(t, d * 0.6, d * 0.75)), arms=(20, 20),
                  mouth="o" if u > 0.9 else "smile", look=0.4 if u > 0.9 else 0)
        cam.move((-1.2, -7.5, 2.8), (-0.6, -6.3, 2.5), t / d, (-0.6, 0.8, 1.5), (-0.6, 0.8, 1.4), t)
    return update


# 6 ------------------------------------------------------------------------
def s06(d):
    lighting("interior")
    bakery_interior()
    loaf((0, 0.75, 1.42), s=0.9)
    tag = PriceTag((0.55, 0.15, 1.55), "$1", s=0.8)
    tag.root.rotation_euler = (0, 0, -0.15)
    Person("baker", (1.6, 2.0, 0)).pose(0.0, arms=(20, 60), mouth="smile", look=-0.5)
    cam = Cam(45, dof=1.6)
    flip = d * 0.45

    def update(t):
        u = prog(t, flip - 0.2, flip + 0.25)
        tag.root.rotation_euler = (u * math.tau, 0, -0.15)
        tag.set("$1" if t < flip else "$1,000")
        s = 0.8 * (1 + 0.25 * math.sin(min(1.0, max(0.0, (t - flip) / 0.4)) * math.pi))
        scale_all(tag.root, s)
        cam.move((0.2, -2.4, 1.9), (0.3, -1.7, 1.75), t / d, (0.3, 0.6, 1.45), (0.4, 0.4, 1.5), t)
    return update


# 7 ------------------------------------------------------------------------
def s07(d):
    lighting("day")
    ground()
    house((0, 2, 0), w=4.5, d=3.0, h=3.0, col="brick", sign="BAKERY")
    for x in (-6, 6):
        tree((x, 5, 0), 1.2)
    bal = empty((0, 1.2, 4.5))
    ball((0, 0, 0), 1.0, mat(C["red"], 0.25), par=bal)
    cone((0, 0, -1.05), 0.15, 0.25, mat(C["red"], 0.3), bal, rot=(math.pi, 0, 0))
    text("PRICES", (0, -1.02, 0.05), 0.42, mat(C["white"], 0.4), bal)
    string = cyl((0, 1.2, 3.2), 0.015, 2.4, mat(C["white"], 0.6))
    cam = Cam(32)

    def update(t):
        s = lerp(0.3, 2.1, prog(t, 0.0, d * 0.9)) * (1 + 0.03 * math.sin(t * 9))
        scale_all(bal, s)
        bal.location.z = 3.6 + s * 1.3
        string.location.z = 1.8 + s * 0.6
        string.scale.z = 0.4 + s * 0.6
        bal.rotation_euler = (0, math.sin(t * 2) * 0.08, math.sin(t * 1.3) * 0.15)
        cam.move((0, -13, 3.5), (0, -11.5, 3.2), t / d, (0, 1, 4.5), (0, 1, 5.5), t)
    return update


# 8 ------------------------------------------------------------------------
def s08(d):
    lighting("night")
    ps = town(night=True)
    ball((-6, 40, 22), 2.0, mat(C["cream"], 0.5, emit=3.0))  # moon
    cam = Cam(30)

    def update(t):
        for i, p in enumerate(ps):
            p.update(t * 1.6 + i * 0.3, 1.6)
        cam.move((-7, -10, 3.2), (4, -8.5, 2.6), t / d, (-4, 3, 1.6), (5, 3, 1.5), t)
    return update


# 9 ------------------------------------------------------------------------
def s09(d):
    lighting("day")
    ground()
    road(-0.5, 3.2)
    house((9, 4, 0), w=4.5, d=3.0, h=3.0, col="brick", sign="BAKERY")
    for x, y in ((-8, 6), (-3, 7), (3, 8)):
        tree((x, y, 0), 1.1)
    boss = Person("boss", (-6, -0.5, 0), rot_z=math.pi / 2)
    wb = wheelbarrow((-4.4, -0.5, 0), rot_z=0)
    cam = Cam(30, dof=4)

    def update(t):
        x = lerp(-6, 1.5, t / d)
        boss.root.location.x = x
        wb.location.x = x + 1.9
        wb.rotation_euler = (0, math.sin(t * 6) * 0.03, 0)
        boss.pose(t * 0.9, walk=0.8, arms=(5, 5), mouth="sad", lean=0.25)
        for a in boss.arms:
            a.rotation_euler.x = -1.1
        cam.set((x + 0.3, -7.5, 2.2), (x + 1.5, -0.5, 1.0), t)
    return update


# 10 -----------------------------------------------------------------------
def s10(d):
    lighting("interior")
    bakery_interior()
    loaf((0, 0.75, 1.42), s=0.9)
    tag = PriceTag((0, 0.0, 2.3), "$1,000", s=1.6)
    cam = Cam(40, dof=2.2)

    def update(t):
        u = prog(t, 0.1, d - 0.25)
        v = int(10 ** lerp(3, 6, u))
        v = int(round(v, -len(str(v)) + 2)) if v > 1000 else v
        tag.set(f"${v:,}")
        tag.root.rotation_euler = (math.sin(t * 5) * 0.05, 0, math.sin(t * 3) * 0.12)
        scale_all(tag.root, 1.6 + 0.15 * u)
        cam.move((0, -4.6, 2.5), (0, -3.6, 2.4), t / d, (0, 0, 2.2), (0, 0, 2.3), t)
    return update


# 11 -----------------------------------------------------------------------
def s11(d):
    lighting("sepia")
    ground(mat(C["stone"], 0.9))
    for i, x in enumerate((-7, -3, 1, 5, 9)):
        house((x, 5, 0), w=3.6, d=3, h=4.2, col=("sepia", "stone", "sepia", "grey", "stone")[i],
              roof="grey_d", door=True)
    box((0, 3.2, 5.2), (4.4, 0.15, 0.8), mat(C["cream"], 0.6), 0.03)
    text("BERLIN 1923", (0, 3.1, 5.2), 0.48, mat(C["black"], 0.5), font="sign")
    tower = CashStack((0, 0.6, 0), (0.9, 0.6))
    kids = [Person("kid1", (-1.2, 0.2, 0), rot_z=-0.5), Person("kid2", (1.2, 0.2, 0), rot_z=0.5),
            Person("kid3", (0.1, -0.7, 0), rot_z=0.0)]
    cam = Cam(32, dof=3)

    def update(t):
        tower.set_level(int(lerp(6, 40, prog(t, 0, d * 0.9))))
        for i, k in enumerate(kids):
            k.pose(t + i, arms=(140, 140) if i < 2 else (30, 150), mouth="grin",
                   bounce=abs(math.sin(t * 6 + i)) * 0.06)
        a = lerp(-0.35, 0.25, t / d)
        cam.set((math.sin(a) * 6, -math.cos(a) * 6, 2.4), (0, 0.6, 1.8), t)
    return update


# 12 -----------------------------------------------------------------------
def s12(d):
    lighting("interior")
    ground(mat(C["wood_l"], 0.8))
    box((0, 3, 3), (14, 0.3, 6), mat(C["cream"], 0.85), 0)
    box((0, 2.8, 4.6), (4.6, 0.12, 0.7), mat(C["cream"], 0.6), 0.03)
    text("ZIMBABWE 2008", (0, 2.72, 4.6), 0.42, mat(C["black"], 0.5), font="sign")
    box((-1.6, 2.7, 2.5), (1.8, 0.15, 2.0), mat(C["white"], 0.6), 0.04)
    box((-1.6, 2.6, 3.25), (1.8, 0.12, 0.5), mat(C["red"], 0.5), 0.03)
    day = text("1", (-1.6, 2.55, 2.3), 1.1, mat(C["black"], 0.5))
    box((1.8, 2.7, 2.5), (2.6, 0.15, 2.0), mat(C["grey_d"], 0.5), 0.04)
    text("BREAD", (1.8, 2.6, 3.05), 0.42, mat(C["white"], 0.4))
    price = text("$100", (1.8, 2.6, 2.2), 0.62, mat(C["gold"], 0.3, emit=0.6))
    cam = Cam(34)
    step = 0.35

    def update(t):
        k = int(t / step)
        day.data.body = str(1 + k)
        price.data.body = f"${100 * 2 ** k:,}"
        u = (t % step) / step
        price.scale = (1 + 0.15 * (1 - u), 1 + 0.15 * (1 - u), 1)
        cam.move((0, -6.5, 2.9), (0, -5.4, 2.8), t / d, (0, 2.6, 2.7), (0, 2.6, 2.7), t)
    return update


# 13 -----------------------------------------------------------------------
def s13(d):
    lighting("interior")
    bakery_interior()
    baker = Person("baker", (0, 2.0, 0))
    pile = CashStack((-0.8, 0.85, 1.17), (1.0, 0.6))
    pile.set_level(20)
    basket = egg_basket((1.6, 0.8, 1.17))
    cam = Cam(32, dof=4)

    def update(t):
        push = prog(t, 0.4, 1.1)
        pile.root.location.x = lerp(-0.8, -3.6, push)
        pile.root.location.z = 1.17 - max(0.0, push - 0.75) * 4
        pile.root.rotation_euler = (0, -max(0.0, push - 0.75) * 2.5, 0)
        point_u = prog(t, 1.2, 1.6)
        baker.pose(t, arms=(lerp(20, 75, push * (1 - point_u)), lerp(20, 95, point_u)),
                   mouth="flat", look=math.sin(t * 9) * 0.5 * (1 - point_u) + point_u * 0.5)
        scale_all(basket, 1 + 0.12 * math.sin(min(1, max(0, (t - 1.3) / 0.4)) * math.pi))
        cam.move((0, -6.2, 2.6), (0.3, -5.4, 2.4), t / d, (0, 0.8, 1.6), (0.4, 0.8, 1.5), t)
    return update


# 14 -----------------------------------------------------------------------
def s14(d):
    lighting("interior")
    ground(mat(C["white"], 0.7))
    box((0, 3, 3), (14, 0.3, 6), mat(C["blue"], 0.8), 0)
    box((0, 2.84, 3.6), (2.8, 0.06, 1.4), mat(C["sky"], 0.05, metal=0.6), 0.02)   # mirror
    cyl((-2.6, 2.4, 1.6), 0.2, 3.2, mat(C["white"], 0.5))
    for k in range(4):
        torus((-2.6, 2.4, 0.4 + k * 0.8), 0.21, 0.05, mat(C["red"], 0.5), rot=(0, 0, 0))
    box((-0.2, 0.9, 0.45), (1.3, 1.1, 0.9), mat(C["red"], 0.4), 0.1)       # barber chair
    cyl((-0.2, 0.9, 0.2), 0.25, 0.4, mat(C["steel"], 0.3, metal=0.6))
    gus = Person("gus", (-0.2, 0.8, 0.0), rot_z=0)
    barber = Person("barber", (1.5, 1.3, 0), rot_z=0.7)
    sc = empty((0, 0, 0), barber.hand_r)
    blades = [box((0.15, 0, 0), (0.35, 0.03, 0.06), mat(C["steel"], 0.2, metal=0.9), 0.01, sc)
              for _ in range(2)]
    ch, head = chicken((0, 0, 0), 0.75)
    cam = Cam(32, dof=4)

    def update(t):
        snip = abs(math.sin(t * 11)) * 0.5
        blades[0].rotation_euler = (0, 0, snip)
        blades[1].rotation_euler = (0, 0, -snip)
        give = prog(t, d * 0.45, d * 0.75)
        gus.pose(t, arms=(lerp(40, 70, give), lerp(40, 80, give)), mouth="grin", look=0.4)
        barber.pose(t, arms=(20, lerp(120, 60, give)), mouth="o" if give > 0.5 else "smile",
                    look=-0.5)
        bpy.context.view_layer.update()
        ga, gb = gus.hand_r.matrix_world.translation, barber.hand_l.matrix_world.translation
        p = [lerp(ga[i], gb[i], give) for i in range(3)]
        ch.location = (p[0], p[1] - 0.35, p[2] - 0.35)
        head.rotation_euler = (0, math.sin(t * 13) * 0.35, 0)
        cam.move((0.6, -6, 2.6), (0.5, -5, 2.4), t / d, (0.4, 1, 1.9), (0.6, 1, 1.8), t)
    return update


# 15 -----------------------------------------------------------------------
def s15(d):
    lighting("interior")
    bakery_interior()
    ch, head = chicken((0, 0.8, 1.17), 1.1, rot_z=0.4)
    label = text("BARTER", (0, 0.6, 2.75), 0.7, mat(C["gold"], 0.25, metal=0.3, emit=0.4))
    cam = Cam(42, dof=1.8)

    def update(t):
        head.rotation_euler = (0, math.sin(t * 8) * 0.3 + (0.4 if (t % 1.2) < 0.15 else 0), 0)
        ch.rotation_euler = (0, 0, 0.4 + math.sin(t * 1.5) * 0.15)
        scale_all(label, max(0.001, min(1.0, pop(t, 0.3)) * 1.0))
        label.rotation_euler = (math.pi / 2, 0, math.sin(t * 2) * 0.1)
        cam.move((0.2, -3.6, 2.2), (0.1, -3.0, 2.1), t / d, (0, 0.8, 1.85), (0, 0.8, 1.95), t)
    return update


# 16/17 --------------------------------------------------------------------
def central_bank():
    lighting("day")
    ground()
    st = mat(C["stone"], 0.6)
    for k in range(3):
        box((0, -0.4 - k * 0.45, 0.15 + k * 0.0), (9 + k * 0.8, 1.2 + k * 0.9, 0.3 - 0 * k), st,
            0.03)
    box((0, 2.5, 2.6), (8.5, 5, 5), st, 0.05)
    for x in (-3.4, -2.0, -0.7, 0.7, 2.0, 3.4):
        cyl((x, -0.5, 2.7), 0.32, 4.8, mat(C["white"], 0.45), verts=24)
    box((0, -0.3, 5.4), (9.0, 1.4, 0.6), st, 0.03)
    roof = cone((0, 1.0, 6.6), 5.4, 1.8, st, verts=3, rot=(math.pi / 2, 0, 0))
    roof.scale = (1, 0.42, 1.6)
    text("CENTRAL BANK", (0, -1.02, 5.4), 0.52, mat(C["grey_d"], 0.4), font="sign")
    box((0, -0.05, 1.6), (2.4, 0.1, 2.2), mat(C["sky"], 0.05, metal=0.2), 0.02)
    p = Press((0, 0.6, 0.3), 1.0)
    pike = Person("pike", (1.6, -1.3, 0.45), rot_z=0.3)
    for x in (-8, 8):
        tree((x, 4, 0), 1.3)
    return p, pike


def s16(d):
    p, pike = central_bank()
    cam = Cam(30)

    def update(t):
        p.update(t, 0.25)
        pike.pose(t, arms=(15, 25), mouth="flat", look=-0.3)
        cam.move((0, -20, 3.5), (0, -14, 3.0), t / d, (0, 1, 3.4), (0, 1, 3.2), t)
    return update


def s17(d):
    p, pike = central_bank()
    cam = Cam(40)

    def update(t):
        p.update(t, 0.25)
        pike.pose(t, arms=(15, 25), mouth="smile", look=-0.3)
        cam.move((0, -11, 4.4), (0, -6.5, 5.1), t / d, (0, 0, 5.0), (0, 0, 5.35), t)
    return update


# 18 -----------------------------------------------------------------------
def s18(d):
    lighting("interior")
    ground(mat(C["wood_l"], 0.8))
    box((0, 3, 3), (14, 0.3, 6), mat(C["pink"], 0.85), 0)
    box((0, 2.84, 3.3), (1.8, 0.06, 1.3), mat(C["wood_d"], 0.6), 0.03)      # picture frame
    box((0, 2.80, 3.3), (1.5, 0.04, 1.0), mat(C["money"], 0.6), 0.01)
    box((0, 1.4, 0.45), (2.6, 1.4, 0.9), mat(C["emerald"], 0.8), 0.15)     # armchair
    box((0, 2.0, 1.3), (2.6, 0.4, 1.6), mat(C["emerald"], 0.8), 0.15)
    gus = Person("gus", (0, 0.5, 0), rot_z=0)
    ch, head = chicken((0, 0, 0), 0.7, rot_z=0.3)
    cam = Cam(36, dof=3)

    def update(t):
        gus.pose(t, arms=(35, 35), mouth="smile" if t < d * 0.6 else "grin",
                 look=0.3 * math.sin(t * 0.8))
        bpy.context.view_layer.update()
        a, b = gus.hand_l.matrix_world.translation, gus.hand_r.matrix_world.translation
        ch.location = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 0.4, (a[2] + b[2]) / 2 - 0.2)
        head.rotation_euler = (0, math.sin(t * 6) * 0.3, 0)
        cam.move((0.4, -6.4, 2.5), (0.2, -5.0, 2.3), t / d, (0, 0.5, 2.0), (0, 0.5, 2.1), t)
    return update


SHOTS = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15, s16, s17,
         s18]

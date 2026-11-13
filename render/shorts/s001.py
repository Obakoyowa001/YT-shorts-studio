"""Short #001 — If You Opened a Bank in 1837 (see scripts/001_wildcat_banks_1837.md).

Each segment = one shot: narration text, background, draw(c, t, d) and audio(m, T, d)
where T is the shot's absolute start time in the final mix and d its duration.
"""
import math

import numpy as np

from engine import (CREAM, GOLD, GREY, INK, MUD, RED, STEEL, WHITE, WOOD, WOOD_D, WOOD_L,
                    back_wall, badge, banknote, barrel, bear, book, cloud, coin, crowd_person,
                    dog, ease, floor, ground, hills, lerp, moon, person, pony, pop, press, prog,
                    shack, sign, sparkle, strongbox, sun, tint, tree, wildcat, wobble)

VOICE = "en-US-GuyNeural"
RATE = "+40%"
GOLD_WORDS = {"michigan", "legally", "dog", "gold", "silver", "nobody", "wildcats",
              "wildcat", "inspector", "rich", "nails", "glass", "coins", "beautiful",
              "gus", "boots", "laughs", "cents", "town", "run", "money", "bank"}

# Character vocal FX generated with the TTS engine at render time: tag -> (text, voice, rate, pitch)
VOCALS = {
    "laugh": ("Ha! Ha ha ha ha!", "en-US-ChristopherNeural", "+10%", "+30Hz"),
    "chant1": ("We want gold! We want gold!", "en-US-EricNeural", "+5%", "-10Hz"),
    "chant2": ("We want gold! We want gold!", "en-US-RogerNeural", "+0%", "+0Hz"),
    "chant3": ("We want our gold!", "en-US-JennyNeural", "+5%", "+0Hz"),
    "hm": ("Hm?", "en-US-EricNeural", "+0%", "+0Hz"),
    "whoa": ("Whoa!", "en-US-GuyNeural", "+0%", "-20Hz"),
}

HAZE_DAY = (205, 228, 238)
HAZE_FOREST = (214, 232, 222)
FG_TREE = (40, 104, 60)


# ---------------------------------------------------------------- shared set dressing
def outdoor(c, gy, t, haze=HAZE_DAY, n_mid=10, mid_off=0.0, far_off=0.0, clouds=True,
            hill_col=(150, 196, 132), tree_col=(84, 150, 98)):
    with c.layer(0.25, blur=6, haze=haze, haze_a=0.45):
        if clouds:
            cloud(c, 120 + t * 6, 420, 1.1)
            cloud(c, 760 + t * 4, 300, 0.85)
        hills(c, gy - 70, hill_col, far_off, w=380, h=190)
    with c.layer(0.55, blur=2.6, haze=haze, haze_a=0.22):
        for i in range(-3, n_mid):
            tree(c, i * 170 + 60 + mid_off % 170, gy - 40, 0.62, tree_col)
    ground(c, gy)


def foreground_bushes(c, gy=1700, left=True, right=True, col=FG_TREE):
    with c.layer(1.45, blur=5):
        if left:
            tree(c, -60, gy + 380, 1.6, col)
        if right:
            tree(c, 1140, gy + 380, 1.6, col)


def interior(c, wall_col=(214, 170, 118), floor_y=1500, floor_col=WOOD_L):
    with c.layer(0.85, blur=1.4):
        back_wall(c, col=wall_col, bottom=floor_y + 10)
    floor(c, floor_y, floor_col)


def counter(c, y=1250):
    c.box3d(-260, y, 1340, y + 1400, 70, WOOD, top=WOOD_L, side=WOOD_D)


def press_hits(d, end_pad=0.0):
    out, k = [], 0
    while True:
        tt = (2 * math.pi * k) / 5 + math.pi / 5
        if tt >= d - end_pad:
            return out
        out.append(tt)
        k += 1


# 1 ------------------------------------------------------------------------
def s01(c, t, d):
    c.cam(lerp(1.0, 1.14, ease(t / d)), lerp(500, 600, ease(t / d)), 1150)
    with c.layer(0.25, blur=6, haze=HAZE_DAY, haze_a=0.45):
        cloud(c, 140 + t * 8, 420, 1.0)
        cloud(c, 760 + t * 5, 330, 0.8)
        hills(c, 1440, (164, 204, 130), w=380, h=190)
    with c.layer(0.6, blur=2.4, haze=HAZE_DAY, haze_a=0.25):
        shack(c, 80, 1470, 0.45, None, depth=180)
        shack(c, 1000, 1470, 0.42, None, depth=180)
    ground(c, 1500)
    shack(c, 520, 1560, 1.0, "BANK", sign_sc=min(1.0, pop(t, 0.25)))
    swing = 0.5 + 0.5 * math.sin(t * 11)
    person(c, 860, 1600, 1.0, "boss", t, arm_l=10, arm_r=100 + swing * 70, mouth="grin",
           hold_r="hammer", look=-0.6)
    s = pop(t, 0.6)
    if s > 0.01:
        c.box3d(230 - 90 * s, 1180 - 110 * s, 230 + 90 * s, 1180 + 110 * s, 16, WHITE, r=10)
        c.rect(230 - 90 * s, 1180 - 110 * s, 230 + 90 * s, 1180 - 60 * s, RED, 10, "v", True,
               False)
        c.text(230, 1200, "1837", 64 * s, INK)
    foreground_bushes(c, right=False)


def a01(m, T, d):
    tt = (math.pi / 2) / 11
    while tt < d:
        m.sfx("hammer", T + tt)
        tt += 2 * math.pi / 11
    m.sfx("pop", T + 0.25)
    m.sfx("paper", T + 0.6)


# 2 ------------------------------------------------------------------------
def s02(c, t, d):
    c.cam(lerp(1.0, 1.12, ease(t / d)), lerp(470, 560, ease(t / d)), 1050)
    interior(c)
    s = pop(t, 0.1)
    if s > 0.01:
        with c.layer(0.85):
            c.box3d(540 - 360 * s, 520 - 120 * s, 540 + 360 * s, 520 + 120 * s, 12, CREAM, r=20)
            c.text(540, 480, "MICHIGAN GENERAL", 50 * s, INK)
            c.text(540, 560, "BANKING LAW · 1837", 50 * s, INK)
    press(c, 480, 1500, 1.0, t)
    for i in range(6):
        u = t * 1.2 - i * 0.38
        if u < 0:
            continue
        u = u % 2.3
        banknote(c, 620 + u * 250, 1330 - u * 170 - math.sin(u * 2.6) * 50, 220)


def a02(m, T, d):
    for tt in press_hits(d):
        m.sfx("press", T + tt)
        m.sfx("paper", T + tt + 0.12, -4)
    m.sfx("pop", T + 0.1)


# 3 ------------------------------------------------------------------------
def s03(c, t, d):
    c.cam(1.08, lerp(420, 660, ease(t / d)), 1120)
    interior(c)
    counter(c, 1250)
    banknote(c, 220, 1180, 300, "BANK OF YOU", "$5", "name", sc=min(1.0, pop(t, 0.05)))
    banknote(c, 560, 1180, 300, "BANK OF YOU", "$5", "face", sc=min(1.0, pop(t, 0.6)))
    banknote(c, 900, 1180, 300, "BANK OF YOU", "$10", "dog", sc=min(1.0, pop(t, 1.2)))
    if t > 1.45:
        dog(c, 1120, 1250, 0.9 * min(1.0, pop(t, 1.45)), t)


def a03(m, T, d):
    for tt in (0.05, 0.6, 1.2):
        m.sfx("paper", T + tt)
    m.sfx("bark", T + 1.55)


# 4 ------------------------------------------------------------------------
def s04(c, t, d):
    c.cam(lerp(1.02, 1.1, ease(t / d)), 540, 1050)
    interior(c)
    with c.layer(0.85):
        sign(c, 540, 520, 420, 140, "ONE RULE", 76, sc=min(1.0, pop(t, 0.2)))
    person(c, 760, 1340, 1.1, "boss", t, arm_l=20, arm_r=20, mouth="flat", look=-1)
    counter(c, 1180)
    u = prog(t, 0.2, 1.6)
    hx = lerp(-120, 420, u)
    c.tube([(-300, 1270), (hx - 60, 1205)], (90, 140, 170), 60)
    c.circle(hx - 40, 1200, 30, (241, 198, 160), "sphere", True, False)
    banknote(c, hx + 80, 1150, 260)


def a04(m, T, d):
    m.sfx("pop", T + 0.2)
    m.sfx("paper", T + 0.3, 2)
    m.sfx("cloth", T + 0.25)


# 5 ------------------------------------------------------------------------
def s05(c, t, d):
    c.cam(lerp(1.0, 1.12, ease(t / d)), 540, 1150)
    with c.layer(0.8, blur=1.5):
        floor(c, 600, WOOD_L)
    person(c, 540, 1000, 1.25, "boss", t, arm_l=40, arm_r=40, mouth="o", sweat=True, brows=1)
    strongbox(c, 540, 1420, 1.5, "RESERVES", coins=0)
    bounce = abs(math.sin(t * 6)) * max(0.0, 1 - t)
    coin(c, 540, 1225 - bounce * 70, 30)
    sparkle(c, 590, 1190, 22, t)


def a05(m, T, d):
    m.sfx("latch", T + 0.05)
    m.sfx("clink", T + 0.25)
    m.sfx("clink", T + 0.55, -6)
    m.sfx("huh", T + 0.9)


# 6 ------------------------------------------------------------------------
def s06(c, t, d):
    off = t * 160
    c.cam(1.0, 540, 1000)
    outdoor(c, 1500, t, mid_off=-off * 0.55, far_off=-off * 0.25)
    for i in range(-1, 8):
        x = (i * 260 - off) % 1820 - 300
        tree(c, x, 1520, 0.55)
    c.box3d(150, 1505, 650, 1540, 60, WOOD_D)
    shack(c, 400, 1505, 0.6, "BANK", depth=160)
    hands = person(c, 860, 1600, 1.05, "boss", t, arm_l=95, arm_r=95, mouth="grin", walk=1.0,
                   look=0.6)
    c.line([(650, 1500), hands["l"]], WOOD_D, 8)
    with c.layer(1.5, blur=5):
        for i in range(3):
            x = (i * 700 - off * 1.5) % 2100 - 400
            tree(c, x, 2330, 1.7, FG_TREE)
    badge(c, t, "STEP 1", 0.05)


def _scrape(d):
    from audio import SR, lowpass_fast
    n = int(d * SR)
    x = np.random.default_rng(4).normal(0, 1, n).astype("float32")
    x = lowpass_fast(x, 30) * (0.6 + 0.4 * np.sin(np.arange(n) / SR * 2 * np.pi * 2.7))
    return x / (np.abs(x).max() + 1e-9)


def a06(m, T, d):
    m.sfx("pop", T + 0.05)
    m.steps(T + 0.1, T + d, 0.37, "grass")
    m.sfx("creak", T + 0.2)
    m.add(_scrape(d), T, -20)


# 7 ------------------------------------------------------------------------
def s07(c, t, d):
    c.cam(1.0, lerp(330, 760, ease(t / d)), 1050)
    outdoor(c, 1500, t, HAZE_FOREST, n_mid=12)
    bear(c, 200, 1520, 0.9, t)
    sign(c, 520, 1240, 330, 90, "TOWN ← 40 MI", 46, post=230)
    shack(c, 980, 1530, 0.7, "BANK", depth=200)
    for i, (x, y) in enumerate(((870, 1170), (980, 1110), (1090, 1170))):
        sc = min(1.0, pop(t, 0.6 + i * 0.25))
        if sc > 0.01:
            wildcat(c, x, y + 40, 0.55 * sc, t + i, 1 if i % 2 else -1)
    with c.layer(1.45, blur=5):
        for x in (-150, 1300, 1500):
            tree(c, x, 1900, 1.5, FG_TREE)


def a07(m, T, d):
    m.sfx("growl", T + 0.25, rate=0.62)
    for i in range(3):
        m.sfx("meow", T + 0.65 + i * 0.25, -4, rate=0.85 + i * 0.12)


# 8 ------------------------------------------------------------------------
def s08(c, t, d):
    c.cam(lerp(1.0, 1.16, ease(t / d)), 540, 1150)
    outdoor(c, 1500, t, HAZE_FOREST, n_mid=10)
    for x, s in ((300, 1.0), (800, 1.1)):
        tree(c, x, 1560, s)
    look = math.sin(t * 4.2)
    hands = person(c, 540, 1620, 1.1, "folk2", t, arm_l=20, arm_r=120, mouth="o", look=look,
                   brows=0.6)
    banknote(c, hands["r"][0] + 40, hands["r"][1] - 60, 200)
    if t > 0.5:
        c.text(700, 900, "?", 160, WHITE, kind="cap", stroke=8, scale=pop(t, 0.5))
    if t > 0.8:
        c.text(380, 950, "?", 110, WHITE, kind="cap", stroke=6, scale=pop(t, 0.8))
    with c.layer(1.45, blur=5):
        tree(c, -40, 1950, 1.7, FG_TREE)
        tree(c, 1120, 1950, 1.8, FG_TREE)


def a08(m, T, d):
    m.steps(T + 0.05, T + d, 0.45, "grass", -4)
    m.add(m.vox.get("hm"), T + 0.5, -6)


# 9 ------------------------------------------------------------------------
def s09(c, t, d):
    c.cam(lerp(1.35, 1.0, ease(t / d)), 540, 1080)
    outdoor(c, 1550, t, HAZE_FOREST)
    shack(c, 540, 1560, 1.0, "WILDCAT BANK", sign_size=50)
    wildcat(c, 540, 1028, 0.7, t)
    foreground_bushes(c, 1750)


def a09(m, T, d):
    m.add(m.whoosh, T, -18)
    m.sfx("meow", T + 0.4, -2, rate=0.8)


# 10 -----------------------------------------------------------------------
def s10(c, t, d):
    c.cam(1.0, lerp(470, 560, ease(t / d)), 1050)
    outdoor(c, 1500, t, HAZE_FOREST)
    x = lerp(-250, 470, prog(t, 0.0, 1.8))
    run = 1.0 - prog(t, 1.5, 2.0)
    pony(c, x, 1560, 1.25, t, (120, 90, 70), run)
    person(c, x - 10, 1360, 0.95, "pike", t, arm_l=40, arm_r=160, mouth="flat",
           hold_r="magnifier", look=0.8)
    s = pop(t, 1.0)
    if s > 0.01:
        c.box3d(800 - 150 * s, 1080 - 180 * s, 800 + 150 * s, 1080 + 180 * s, 18, WOOD_L, r=12)
        c.rect(800 - 120 * s, 1080 - 140 * s, 800 + 120 * s, 1080 + 160 * s, WHITE, 4, "v",
               True, False)
        c.text(800, 1020, "GOLD", 56 * s, INK)
        c.text(800, 1100, "INSPECTION", 40 * s, INK)
    badge(c, t, "STEP 2", 0.05)
    foreground_bushes(c, right=False)


def a10(m, T, d):
    m.sfx("pop", T + 0.05)
    m.gallop(T, T + 1.8, -2, 1.2)
    m.sfx("paper", T + 1.0)


# 11 -----------------------------------------------------------------------
def s11(c, t, d):
    c.cam(lerp(1.0, 1.06, ease(t / d)), 540, 1000)
    with c.layer(0.85, blur=1.4):
        c.rect(-400, -400, 540, 2400, (214, 176, 126), 0, "v", False, False)
        c.rect(540, -400, 1500, 2400, (200, 190, 220), 0, "v", False, False)
    floor(c, 1500)
    c.rect(530, -400, 550, 2400, INK, 0, "flat", False, False)
    strongbox(c, 270, 1340, 0.85, "EMPTY")
    mx, my = 270 + math.sin(t * 3) * 60, 1150 - t * 110
    flap = abs(math.sin(t * 20))
    c.ellipse(mx - 18, my, 20, 8 + flap * 9, GREY, "v", False, False)
    c.ellipse(mx + 18, my, 20, 8 + flap * 9, GREY, "v", False, False)
    strongbox(c, 800, 1340, 0.85, "GOLD", coins=14)
    pat = abs(math.sin(t * 8)) * 25
    person(c, 820, 1140, 0.8, "mo", t, arm_l=110 - pat, arm_r=20, mouth="grin", look=-0.5)
    for i in range(3):
        sparkle(c, 700 + i * 90, 1150, 20, t, i)


def a11(m, T, d):
    m.add(m.chime, T + 1.2, -18)
    for k in range(4):
        m.sfx("clink", T + 1.3 + k * 0.39, -6)


# 12 -----------------------------------------------------------------------
def s12(c, t, d):
    mo_x = lerp(150, 1500, t / d)
    c.cam(1.0, mo_x - 80, 1050)
    outdoor(c, 1500, t, HAZE_FOREST, n_mid=18)
    for i, txt in enumerate(("MONDAY", "TUESDAY", "WEDNESDAY")):
        sign(c, 500 + i * 650, 1300, 300, 80, txt, 40, post=190)
    px = mo_x - 650
    pony(c, px, 1520, 0.5, t, (120, 90, 70), 0.6)
    person(c, px, 1440, 0.4, "pike", t, arm_l=30, arm_r=150, mouth="flat", hold_r="magnifier")
    seat = pony(c, mo_x, 1560, 0.9, t, (200, 160, 120), 1.0)
    person(c, seat[0] - 10, seat[1] + 120, 0.7, "mo", t, arm_l=150, arm_r=150, mouth="grin")
    strongbox(c, seat[0] - 10, seat[1] - 230, 0.35, "GOLD", coins=7)
    with c.layer(1.5, blur=6):
        for i in range(5):
            tree(c, 200 + i * 640, 2330, 1.7, FG_TREE)


def a12(m, T, d):
    m.gallop(T, T + d, 0, 1.35)
    m.gallop(T + 0.2, T + d, -14, 1.1)
    m.sfx("coins", T + 0.6, -8)


# 13 -----------------------------------------------------------------------
def s13(c, t, d):
    k = min(2, int(t / (d / 3)))
    tl = t - k * d / 3
    names = ("BANK OF YOU", "MO'S BANK", "BANK OF BEARS")
    walls = ((214, 170, 118), (196, 186, 220), (190, 214, 170))
    c.cam(lerp(1.03, 1.09, ease(tl / (d / 3))), 540 + (k - 1) * 40, 1050)
    interior(c, walls[k])
    with c.layer(0.85):
        sign(c, 540, 500, 560, 120, names[k], 60)
    person(c, 830, 1200, 0.9, "pike", tl, arm_l=30, arm_r=150, mouth="smile",
           hold_r="magnifier", look=-0.7)
    counter(c, 1250)
    strongbox(c, 400, 1150, 0.7, None, coins=14)
    c.rect(520, 1110, 680, 1170, (250, 240, 120), 6, "v", True, False)
    c.text(600, 1140, "PROPERTY OF MO", 18, INK)
    s = pop(tl, 0.25)
    if s > 0.01:
        c.rect(540 - 200 * s, 1450 - 60 * s, 540 + 200 * s, 1450 + 60 * s, None, 10, "flat",
               (40, 150, 70), False)
        c.text(540, 1452, "APPROVED", 66 * s, (40, 150, 70), kind="cap")


def a13(m, T, d):
    for k in range(3):
        m.sfx("stamp", T + k * d / 3 + 0.25)
        m.add(m.whoosh, T + k * d / 3, -24)


# 14 -----------------------------------------------------------------------
def s14(c, t, d):
    c.cam(lerp(1.0, 1.12, ease(t / d)), 540, 1150)
    outdoor(c, 1450, t, HAZE_FOREST)
    sink = prog(t, 0.0, d) * 90
    c.ellipse(540, 1640, 520, 120, MUD, "v", False, False)
    c.ellipse(540, 1620, 470, 80, (130, 92, 58), "v", False, False)
    pony(c, 540, 1560 + sink, 1.1, t * 0.3, (200, 160, 120), 0.2)
    person(c, 500, 1420 + sink, 0.8, "mo", t, arm_l=150, arm_r=150, mouth="sad", sweat=True,
           brows=-1)
    strongbox(c, 780, 1520 + sink * 1.5, 0.4, "GOLD", coins=5)
    c.ellipse(540, 1700, 560, 90, tint(MUD, -0.1), "v", False, False)
    badge(c, t, "STEP 3", 0.05)


def a14(m, T, d):
    m.sfx("pop", T + 0.05)
    for k in range(3):
        m.sfx("squelch", T + 0.2 + k * 0.5, rate=0.75)
    m.add(m.vox.get("whoa"), T + 0.4, -8)


# 15 -----------------------------------------------------------------------
def s15(c, t, d):
    c.cam(lerp(1.03, 1.1, ease(t / d)), 540, 1150)
    interior(c, floor_y=1550)
    barrel(c, 460, 1400, 1.2, "GOLD")
    person(c, 840, 1640, 1.0, "boss", t, arm_l=20, arm_r=150, mouth="grin", look=-0.7)
    bx, by = 700, 950
    c.box3d(bx - 70, by - 60, bx + 70, by + 60, 40, STEEL)
    for i in range(14):
        u = ((t * 1.6) + i * 0.13) % 1.0
        x = lerp(bx - 40, 460 + (i % 5 - 2) * 30, u)
        y = lerp(by + 40, 1100, u * u)
        if i % 3 == 0:
            c.poly([(x, y - 18), (x + 14, y + 10), (x - 12, y + 6)], (190, 230, 240, 220),
                   "flat", True, False)
        else:
            c.tube([(x - 4, y - 22), (x + 4, y + 22)], (130, 134, 144), 7)


def a15(m, T, d):
    t, i = 0.05, 0
    while t < d:
        m.sfx("metal" if i % 3 else "glass", T + t, -4)
        t += 0.11
        i += 1


# 16 -----------------------------------------------------------------------
def s16(c, t, d):
    c.cam(lerp(1.0, 1.06, ease(t / d)), 540, 1050)
    with c.layer(0.8, blur=2):
        floor(c, -400, WOOD_L)
    c.circle(540, 1050, 420, WOOD_D, "sphere", True, True)
    c.circle(540, 1050, 380, (80, 80, 90), "v", True, False)
    for i in range(30):
        a, r = i * 2.4, 40 + (i * 37) % 300
        c.tube([(540 + math.cos(a) * r, 1050 + math.sin(a) * r),
                (540 + math.cos(a) * r + 30, 1050 + math.sin(a) * r + 12)], (150, 154, 164), 7)
    n = 0
    for ring, cnt in ((0, 1), (110, 6), (220, 12), (320, 18)):
        for j in range(cnt):
            a = j / cnt * math.tau
            coin(c, 540 + math.cos(a) * ring, 1050 + math.sin(a) * ring, 52,
                 sc=min(1.0, pop(t, 0.05 + n * 0.045, 0.3)))
            n += 1
    for i in range(5):
        sparkle(c, 300 + i * 120, 800 + (i % 2) * 450, 26, t, i)


def a16(m, T, d):
    for n in range(0, 37, 2):
        tt = 0.05 + n * 0.045
        if tt < d:
            m.sfx("clink", T + tt, -6)
    m.add(m.chime, T + 1.6, -16)


# 17 -----------------------------------------------------------------------
def s17(c, t, d):
    c.cam(lerp(1.04, 1.12, ease(t / d)), 540, 1100)
    interior(c, floor_y=1550)
    barrel(c, 360, 1400, 1.0, "GOLD", top_fill=GOLD)
    c.glow(360, 1150, 200, (255, 220, 120), 0.35)
    ok = prog(t, 0.6, 0.9)
    person(c, 760, 1640, 1.0, "pike", t, arm_l=20, arm_r=lerp(160, 120, ok),
           mouth="smile" if ok > 0.5 else "flat", hold_r="magnifier", look=-0.9)
    s = pop(t, 0.75)
    if s > 0.01:
        c.rect(540 - 220 * s, 700 - 70 * s, 540 + 220 * s, 700 + 70 * s, None, 10, "flat",
               (40, 150, 70), False)
        c.text(540, 702, "APPROVED", 74 * s, (40, 150, 70), kind="cap")


def a17(m, T, d):
    m.sfx("creak", T + 0.1, -4)
    m.sfx("stamp", T + 0.75)
    m.sfx("ding", T + 0.85)


# 18 -----------------------------------------------------------------------
def s18(c, t, d):
    c.cam(lerp(1.0, 1.07, ease(t / d)), 540, 1100)
    outdoor(c, 1550, t, HAZE_FOREST)
    c.cylinder(290, 1480, 1560, 90, WOOD, WOOD_L, 30)
    swing = 0 if t > 0.9 else (0.5 + 0.5 * math.sin(t * 9 - 1.5)) * 90
    hands = person(c, 360, 1620, 1.0, "gus", t, arm_l=20, arm_r=60 + swing,
                   mouth="grin" if t > 1.2 else "smile", hold_r="axe" if t < 0.9 else None,
                   look=0.6)
    bh = person(c, 820, 1620, 0.95, "boss", t, arm_l=15, arm_r=80, mouth="grin", look=-1)
    u = prog(t, 0.9, 1.5)
    nx = lerp(bh["l"][0], hands["r"][0] + 40, u)
    ny = lerp(bh["l"][1], hands["r"][1] - 40, u) - math.sin(u * math.pi) * 60
    banknote(c, nx, ny, 220, "WILDCAT BANK", "$5")
    foreground_bushes(c, left=False)


def a18(m, T, d):
    tt = (math.pi + 1.5) / 9
    while tt < 0.9:
        m.sfx("chop", T + tt)
        tt += 2 * math.pi / 9
    m.sfx("paper", T + 1.0, 2)


# 19 -----------------------------------------------------------------------
def s19(c, t, d):
    u = t / d
    phase = (u * 2) % 1.0
    night = 0.5 - 0.5 * math.cos(u * 2 * math.tau)
    c.cam(1.0, 540, 1000)
    top = tuple(int(lerp(a, b, night)) for a, b in zip((112, 182, 230), (16, 24, 60)))
    c.rect(-900, -900, 2000, 1500, top, 0, "v", False, False)
    ang = math.pi * (1 - phase)
    bx, by = 540 + math.cos(ang) * 420, 900 - math.sin(ang) * 520
    with c.layer(0.2):
        (moon if int(u * 2) % 2 else sun)(c, bx, by)
    off = t * 220
    with c.layer(0.4, blur=4):
        hills(c, 1380, (110, 160, 100), -off * 0.3, w=380, h=190)
    with c.layer(0.7, blur=1.5):
        hills(c, 1440, (120, 172, 104), -off * 0.6)
    ground(c, 1500)
    sign(c, (900 - off) % 1600 - 200, 1300, 300, 80, "CITY → 2 DAYS", 38, post=200)
    person(c, 520, 1640, 1.0, "gus", t, arm_l=25, arm_r=25, mouth="smile", walk=1.0, look=0.7)
    with c.layer(1.4, blur=5):
        for i in range(3):
            x = (i * 800 - off * 1.4) % 2400 - 400
            tree(c, x, 2330, 1.6, FG_TREE)


def a19(m, T, d):
    m.steps(T + 0.05, T + d, 0.37, "grass")
    m.add(m.whoosh, T + d * 0.25, -20)
    m.add(m.whoosh, T + d * 0.75, -20)


# 20 -----------------------------------------------------------------------
def s20(c, t, d):
    c.cam(lerp(1.0, 1.1, ease(t / d)), 540, 1100)
    with c.layer(0.85, blur=1.4):
        back_wall(c, col=(196, 206, 176))
        for row in range(2):
            c.box3d(-100, 560 + row * 260, 1200, 590 + row * 260, 60, WOOD_D)
            for i in range(6):
                x = 60 + i * 190
                c.poly([(x, 550 + row * 260), (x + 40, 550 + row * 260),
                        (x + 40, 470 + row * 260), (x + 20, 450 + row * 260),
                        (x, 450 + row * 260)], (90, 60, 40), "v", True, True)
                c.rect(x, 520 + row * 260, x + 90, 550 + row * 260, (90, 60, 40), 10, "v",
                       True, False)
    floor(c, 1400)
    lift = prog(t, 0.2, 1.1)
    person(c, 540, 1250, 1.0, "shop", t, arm_l=lerp(40, 120, lift), arm_r=lerp(40, 120, lift),
           mouth="flat", squash=wobble(t, 1.2))
    counter(c, 1250)
    book(c, 540, 1180, 0.8, open_u=prog(t, 1.2, 1.5))
    if t > 1.3:
        for i in range(8):
            a = i / 8 * math.tau
            r = (t - 1.3) * 400
            c.circle(540 + math.cos(a) * r, 1150 + math.sin(a) * r * 0.5,
                     max(1, 40 - (t - 1.3) * 20),
                     (220, 210, 190, max(0, int(180 - (t - 1.3) * 160))), "sphere", False, False)


def a20(m, T, d):
    m.sfx("book_place", T + 0.3, -4)
    m.sfx("thud", T + 1.2, -2)
    m.sfx("book_open", T + 1.25)
    m.add(m.whoosh, T + 1.3, -18)


# 21 -----------------------------------------------------------------------
def s21(c, t, d):
    c.cam(lerp(1.0, 1.08, ease(t / d)), 540, lerp(980, 1060, ease(t / d)))
    c.rect(-400, -400, 1500, 2400, (124, 40, 40), 0, "v", False, False)
    c.box3d(60, 300, 1020, 1350, 30, CREAM, r=10)
    rows = (("BANK OF MICHIGAN", "GOOD"), ("MO'S BANK", "50¢"), ("FARMERS BANK", "80¢"),
            ("WILDCAT BANK", "3¢"))
    for i, (n, v) in enumerate(rows):
        y = 430 + i * 230
        c.text(110, y, n, 50, INK, anchor="lm")
        c.text(960, y, v, 56, RED if i == 3 else INK, anchor="rm")
        c.line([(100, y + 70), (980, y + 70)], (190, 180, 160), 4)
    s = pop(t, 0.3)
    if s > 0.01:
        c.ellipse(540, 1120, 470 * s, 100 * s, None, "flat", RED, False)
    if t > 0.9:
        c.text(230, 1420, "HA HA!", 84, WHITE, kind="cap", stroke=8, scale=pop(t, 0.9))
    gx, gy = 540, 1560
    with c.layer(1.15):
        c.circle(gx, gy + 60, 120, (241, 198, 160), "sphere", True, True)
        shrink = prog(t, 1.6, 2.4)
        if shrink < 1:
            banknote(c, gx, gy - 40, 320 * (1 - shrink) + 1, "WILDCAT BANK", "$5")
        else:
            for i in range(3):
                coin(c, gx - 50 + i * 50, gy - 20 - i * 6, 22, sc=0.6)


def a21(m, T, d):
    m.sfx("book_flip", T + 0.05)
    m.add(m.vox.get("laugh"), T + 0.85, -4)
    m.add(m.whoosh, T + 1.6, -16)
    m.sfx("clink", T + 2.35, -2)


# 22 -----------------------------------------------------------------------
def s22(c, t, d):
    c.cam(lerp(1.0, 1.06, ease(t / d)), lerp(500, 600, ease(t / d)), 1050)
    with c.layer(0.15):
        moon(c, 860, 360)
    outdoor(c, 1500, t, (40, 50, 90), clouds=False, hill_col=(40, 70, 70),
            tree_col=(30, 70, 50))
    shack(c, 1100, 1520, 0.8, "WILDCAT BANK", sign_size=40, depth=200)
    march = t * 90
    order = [(-250, 1.0, False, None), (-60, 0.9, True, None),
             (120, 0.95, False, "WE WANT GOLD"), (300, 0.85, True, None),
             (-420, 0.85, True, "GOLD!"), (470, 0.8, False, None)]
    for i, (x, s, lan, txt) in sorted(enumerate(order), key=lambda p: p[1][1]):
        crowd_person(c, x + march, 1600 + (1 - s) * -150, s, t, i, lan, txt)
    person(c, 520 + march, 1680, 1.05, "gus", t, arm_l=150, arm_r=25, mouth="o", walk=1.0,
           look=0.8)
    with c.layer(1.45, blur=5):
        tree(c, -60, 2000, 1.7, (20, 60, 40))


def a22(m, T, d):
    m.steps(T, T + d, 0.21, "grass", -2)
    m.steps(T + 0.1, T + d, 0.29, "grass", -6)
    m.add(m.vox.get("chant1"), T + 0.2, -10)
    m.add(m.vox.get("chant2"), T + 0.32, -11)
    m.add(m.vox.get("chant3"), T + 0.5, -13)


# 23 -----------------------------------------------------------------------
def s23(c, t, d):
    c.cam(lerp(1.22, 1.3, ease(t / d)), 540, 1150)
    with c.layer(0.85, blur=2):
        back_wall(c)
    person(c, 700, 1500, 1.2, "boss", t, arm_l=60, arm_r=60, mouth="o", sweat=True, look=-1,
           brows=1)
    barrel(c, 400, 1450, 1.1, None, top_fill=(130, 134, 144))
    y = lerp(900, 1180, prog(t, 0.1, 0.5))
    c.tube([(420, y - 30), (426, y + 30)], (130, 134, 144), 9)


def a23(m, T, d):
    m.sfx("metal", T + 0.5, 4, rate=1.3)


# 24 -----------------------------------------------------------------------
def s24(c, t, d):
    c.cam(lerp(1.0, 1.05, ease(t / d)), 540, 1050)
    interior(c, floor_y=1550)
    c.rect(60, 1000, 300, 1550, (34, 22, 16), 4, "v", True, False)
    with c.layer(0.85):
        sign(c, 820, 700, 300, 100, "CLOSED", 60, bg=RED, fg=WHITE, sc=min(1.0, pop(t, 0.15)))
    bx = lerp(700, -200, prog(t, 0.1, 1.2))
    person(c, bx, 1640, 1.0, "boss", t, arm_l=80, arm_r=80, mouth="o", walk=1.0, look=-1)
    for i in range(4):
        x = lerp(1400, 900 - i * 120, prog(t, 0.3 + i * 0.1, 1.5))
        crowd_person(c, x, 1660, 0.9, t, i, i % 2 == 0)
    badge(c, t, "BANK RUN", 0.2)


def a24(m, T, d):
    m.sfx("door_close", T + 0.1)
    m.steps(T + 0.1, T + 1.2, 0.17, "wood", 2)
    m.steps(T + 0.3, T + d, 0.13, "wood", -2)
    m.sfx("pop", T + 0.2)
    m.sfx("door_open", T + 0.35, -2)


# 25 -----------------------------------------------------------------------
def s25(c, t, d):
    if t > d - 0.7:  # match-cut back to the opening for the loop
        s01(c, 0.0, 3.0)
        return
    c.cam(lerp(1.25, 1.0, ease(t / (d - 0.7))), 540, 1100)
    with c.layer(0.85, blur=1.5):
        c.rect(-900, -900, 2000, 1550, (230, 236, 240), 0, "v", False, False)
    floor(c, 1550, (184, 190, 200), planks=False)
    press(c, 300, 1550, 1.0, t)
    for i in range(4):
        u = ((t * 1.2) - i * 0.4) % 2.0
        banknote(c, 420 + u * 160, 1350 - u * 120, 160, "", "$1", "modern", col=(200, 214, 196))
    hands = person(c, 780, 1680, 1.05, "gus", t, arm_l=20, arm_r=140, mouth="grin", boots=True,
                   look=-0.4)
    banknote(c, hands["r"][0] + 20, hands["r"][1] - 70, 220, "", "$1", "modern",
             col=(200, 214, 196))


def a25(m, T, d):
    for tt in press_hits(d, 0.7):
        m.sfx("press", T + tt, -6)
    m.add(m.whoosh, T + d - 0.7, -14)
    m.sfx("hammer", T + d - 0.55)


SEGMENTS = [
    dict(text="If you opened a bank in Michigan in 1837, congratulations.", bg="day",
         draw=s01, audio=a01),
    dict(text="You're legally allowed to print your own money.", bg="interior", draw=s02,
         audio=a02),
    dict(text="Your name, your face, a picture of your dog. Anything.", bg="interior",
         draw=s03, audio=a03),
    dict(text="There's just one rule. If someone brings your paper money back,",
         bg="interior", draw=s04, audio=a04),
    dict(text="you have to swap it for real gold or silver.", bg="interior", draw=s05,
         audio=a05),
    dict(text="So, step one, you build your bank where nobody can find it.", bg="day",
         draw=s06, audio=a06),
    dict(text="Deep in the woods, past the bears, right next to the wildcats.", bg="forest",
         draw=s07, audio=a07),
    dict(text="Nobody can cash out if nobody can find the door.", bg="forest", draw=s08,
         audio=a08),
    dict(text="This is called a wildcat bank.", bg="forest", draw=s09, audio=a09),
    dict(text="Step two, the inspector is coming to count your gold.", bg="forest",
         draw=s10, audio=a10),
    dict(text="You don't have any gold. But the bank next door does.", bg="interior",
         draw=s11, audio=a11),
    dict(text="So one box of gold rides through the forest, one day ahead of the inspector.",
         bg="forest", draw=s12, audio=a12),
    dict(text="Every bank he visits looks rich.", bg="interior", draw=s13, audio=a13),
    dict(text="Step three, the box doesn't show up.", bg="forest", draw=s14, audio=a14),
    dict(text="So you fill a barrel with nails and broken glass,", bg="interior", draw=s15,
         audio=a15),
    dict(text="and put one layer of coins on top.", bg="interior", draw=s16, audio=a16),
    dict(text="The inspector opens it. Beautiful.", bg="interior", draw=s17, audio=a17),
    dict(text="Then Gus gets paid in your money.", bg="forest", draw=s18, audio=a18),
    dict(text="He walks two days into the city to buy boots.", bg="day", draw=s19, audio=a19),
    dict(text="The shopkeeper opens a giant book listing every bank in America,", bg="shop",
         draw=s20, audio=a20),
    dict(text="finds yours, and laughs. Gus's dollar is now worth a few cents.", bg="shop",
         draw=s21, audio=a21),
    dict(text="Then the whole town shows up at once, wanting their gold.", bg="night",
         draw=s22, audio=a22),
    dict(text="You have nails.", bg="interior", draw=s23, audio=a23),
    dict(text="This is called a bank run.", bg="interior", draw=s24, audio=a24),
    dict(text="And that's basically why you're not allowed to print your own money anymore.",
         bg="modern", draw=s25, audio=a25),
]

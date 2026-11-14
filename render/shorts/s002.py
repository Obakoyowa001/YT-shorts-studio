"""Short #002 — What If Everyone Printed Money? (see scripts/002_everyone_prints_money.md)

Story + sound side of the Short. The 3D visuals for each shot live in
render3d/scenes/s002.py (same order). No music: sound effects and ambience only.
"""
MUSIC = False
AMBIENCE = False      # no wind/room-tone bed: narration + sound effects only
WORD_POPS = True      # soft pop on every gold caption word
CUT_WHOOSH_DB = -22   # audible whoosh on every cut
VOICE = "en-US-GuyNeural"
RATE = "+40%"
GOLD_WORDS = {"machine", "minute", "legal", "rich", "problem", "everyone", "millionaire", "gus", "million", "dollar", "thousand", "inflation", "wheelbarrow",
              "hyperinflation", "germany", "towers", "zimbabwe", "doubled", "eggs", "chicken",
              "barter", "bank", "slowly", "money"}

VOCALS = {
    "chicken": ("Bawk! Bawk bawk, ba-gawk!", "en-US-AnaNeural", "+25%", "+60Hz"),
    "chicken2": ("Bok bok?", "en-US-AnaNeural", "+10%", "+80Hz"),
    "yay": ("Woo-hoo!", "en-US-GuyNeural", "+0%", "+10Hz"),
    "nope": ("Nope.", "en-US-ChristopherNeural", "+0%", "-10Hz"),
    "kids": ("Higher! Higher!", "en-US-AnaNeural", "+10%", "+20Hz"),
}


def a01(m, T, d):
    m.sfx("ding", T + 0.0, 2)               # cha-ching on frame one
    m.sfx("coins", T + 0.05, 0)
    m.add(m.whoosh, T + 0.0, -12)           # camera rush
    for k in range(int(d / 0.16)):          # machine firing bills
        m.sfx("press" if k % 3 == 0 else "paper", T + 0.15 + k * 0.16, -6 if k % 3 == 0 else -4)


def a02(m, T, d):
    m.sfx("thud", T + 0.05, 0)              # lands in the cash pile
    for k in range(6):
        m.sfx("paper", T + 0.1 + k * 0.15, -2)
    m.add(m.vox.get("yay"), T + 0.35, -6)
    m.add(m.chime, T + 0.2, -12)


def a03(m, T, d):
    m.sfx("stamp", T + 0.05, -4)            # record-scratch style hit on "one problem"
    m.add(m.whoosh, T + 0.2, -12)
    for k in range(5):
        m.sfx("coins", T + 0.4 + k * 0.35, -8)
    m.sfx("cloth", T + d - 0.6, 0)


def a04(m, T, d):
    m.sfx("pop", T + 0.05)
    m.steps(T + 0.05, T + d, 0.2, "grass", 0)
    m.add(m.whoosh, T + 0.4, -20)


def a05(m, T, d):
    m.sfx("bell", T + 0.1, 4)
    m.sfx("door_open", T + 0.05, -4)
    m.steps(T + 0.2, T + 1.2, 0.3, "wood", -2)
    m.sfx("thud", T + 1.0, -4)


def a06(m, T, d):
    m.sfx("paper", T + 0.2, -6)
    flip = d * 0.45
    m.add(m.whoosh, T + flip, -14)
    m.sfx("ding", T + flip + 0.3, -2)


def a07(m, T, d):
    m.add(m.stretch, T + 0.05, -10)


def a08(m, T, d):
    m.sfx("pop", T + 0.05)
    for k in range(int(d / 0.3)):
        m.sfx("press", T + 0.2 + k * 0.3, -12)


def a09(m, T, d):
    t = 0.1
    while t < d:
        m.add(m.squeak, T + t, -20)
        t += 0.55
    m.steps(T + 0.05, T + d, 0.42, "grass", -4)


def a10(m, T, d):
    t = 0.05
    while t < d - 0.2:
        m.add(m.tick, T + t, -8)
        t += 0.09
    m.sfx("ding", T + d - 0.25, 0)


def a11(m, T, d):
    for k in range(int(d / 0.35)):
        m.sfx("paper", T + 0.1 + k * 0.35, -4)
    m.add(m.vox.get("kids"), T + 0.4, -12)


def a12(m, T, d):
    for k in range(int(d / 0.35)):
        m.sfx("book_flip", T + 0.05 + k * 0.35, -6)
        m.add(m.tick, T + 0.1 + k * 0.35, -10)


def a13(m, T, d):
    m.sfx("pop", T + 0.05)
    m.sfx("paper", T + 0.6, 2)
    m.add(m.vox.get("nope"), T + 0.7, -6)
    m.sfx("creak", T + d - 0.8, -4)


def a14(m, T, d):
    for k in range(5):
        m.sfx("snip", T + 0.1 + k * 0.28, -4)
    m.add(m.vox.get("chicken"), T + d * 0.5, -6)


def a15(m, T, d):
    m.add(m.vox.get("chicken2"), T + 0.1, -6)
    m.sfx("pop", T + 0.35)


def a16(m, T, d):
    m.sfx("door_close", T + 0.2, -2)
    for k in range(int(d / 1.2)):
        m.sfx("press", T + 0.6 + k * 1.2, -10)


def a17(m, T, d):
    m.sfx("stamp", T + 0.3, -2)
    m.add(m.chime, T + 0.4, -18)


def a18(m, T, d):
    m.add(m.vox.get("chicken2"), T + 0.3, -8)
    m.sfx("cloth", T + 1.0, -6)


SEGMENTS = [
    dict(text="You have a machine that prints a million dollars a minute, and it's totally legal.",
         bg="interior", audio=a01),
    dict(text="Congratulations. You're rich.", bg="day", audio=a02),
    dict(text="There's just one problem. So is everyone else. Including Gus.", bg="day",
         audio=a03),
    dict(text="Step one, you grab a million and run to the store.", bg="day", audio=a04,
         badge=("STEP 1", 0.05)),
    dict(text="But Gus printed ten million, and he got there first.", bg="interior", audio=a05),
    dict(text="The shopkeeper isn't dumb. If everyone has a million, a loaf of bread isn't worth "
              "one dollar anymore. It's worth a thousand.", bg="interior", audio=a06),
    dict(text="This is called inflation.", bg="day", audio=a07),
    dict(text="Step two, everyone prints more to keep up. The printers run all night.",
         bg="night", audio=a08, badge=("STEP 2", 0.05)),
    dict(text="By Friday, one loaf costs a wheelbarrow of cash.", bg="day", audio=a09),
    dict(text="This is called hyperinflation, and it really happened.", bg="interior",
         audio=a10),
    dict(text="In Germany in 1923, kids built towers out of money.", bg="sepia", audio=a11),
    dict(text="In Zimbabwe, prices doubled every day.", bg="interior", audio=a12),
    dict(text="Step three, the shopkeeper stops taking money at all. He wants eggs.",
         bg="interior", audio=a13, badge=("STEP 3", 0.05)),
    dict(text="Gus pays for a haircut with a chicken.", bg="interior", audio=a14),
    dict(text="This is called barter.", bg="interior", audio=a15),
    dict(text="So countries made one rule. Only one bank gets to print money, and it has to "
              "print slowly.", bg="day", audio=a16),
    dict(text="This is called a central bank.", bg="day", audio=a17),
    dict(text="Gus still has the chicken. And that's basically why you're not allowed to print "
              "your own money.", bg="interior", audio=a18),
]

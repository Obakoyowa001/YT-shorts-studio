"""2.5D paper-diorama drawing engine (Cairo).

Scenes are written in a 1080x1920 "base" space and scaled to the output size,
so the same scene renders at preview resolution or 4K.

2.5D comes from:
  * parallax depth layers (c.layer(k, blur)) - far layers move less, get haze + depth-of-field blur
  * one-point perspective for boxes/buildings/floors - vanishing point follows the camera,
    so sides of objects turn as the camera moves
  * volumetric shading - spheres, cylinders, tubes and lit faces instead of flat fills
  * soft drop/contact shadows and a constant gentle camera float
"""
import math
import os
from contextlib import contextmanager
from functools import lru_cache

import cairo
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE_W, BASE_H = 1080, 1920
SCENE_LIFT = -200       # lift scenes so captions sit on clear ground below the action
CAPTION_Y = 1480        # ~77% down the frame, clear of signs and of the Shorts UI
HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")
FONT_FILES = {"sign": "Rye-Regular.ttf", "cap": "LuckiestGuy-Regular.ttf"}
FALLBACKS = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Arial Bold.ttf"]

# ---------------------------------------------------------------- palette
SKIN = (241, 198, 160)
INK = (45, 32, 28)
WHITE = (252, 248, 238)
CREAM = (246, 233, 205)
GOLD = (245, 192, 40)
GOLD_D = (196, 140, 20)
EMERALD = (22, 128, 84)
MONEY = (172, 212, 152)
MONEY_D = (82, 140, 92)
WOOD = (176, 114, 64)
WOOD_D = (125, 76, 40)
WOOD_L = (212, 158, 100)
RED = (214, 64, 52)
PURPLE = (124, 76, 166)
GREY = (146, 146, 156)
GREY_D = (92, 94, 106)
STEEL = (120, 128, 140)
GRASS = (124, 182, 84)
TREE = (56, 128, 74)
MUD = (110, 74, 44)
ROOF = (158, 74, 54)


# ---------------------------------------------------------------- math helpers
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def lerp(a, b, u):
    return a + (b - a) * u


def ease(u):
    """Smooth in-out (quintic smootherstep) for camera and moves."""
    u = clamp(u)
    return u * u * u * (u * (u * 6 - 15) + 10)


def ease_out(u):
    u = clamp(u)
    return 1 - (1 - u) ** 3


def prog(t, t0, t1):
    if t1 <= t0:
        return 1.0 if t >= t1 else 0.0
    return ease((t - t0) / (t1 - t0))


def pop(t, t0, dur=0.42):
    """Springy pop-in: 0 before t0, overshoots, settles to 1 (damped)."""
    if t < t0:
        return 0.0
    u = (t - t0) / dur
    if u >= 2.5:
        return 1.0
    return 1 - math.exp(-5.5 * u) * math.cos(7.5 * u)


def wobble(t, t0, amp=0.08, dur=0.6):
    """Squash/stretch factor after an event at t0 (1.0 = rest)."""
    if t < t0 or t > t0 + dur:
        return 1.0
    u = (t - t0) / dur
    return 1 + amp * math.exp(-4 * u) * math.sin(u * 18)


def tint(c, k):
    """k>0 lightens toward white, k<0 darkens toward black (alpha kept)."""
    if k >= 0:
        out = tuple(int(v + (255 - v) * k) for v in c[:3])
    else:
        out = tuple(int(v * (1 + k)) for v in c[:3])
    return out + tuple(c[3:4])


def mix(c1, c2, u):
    return tuple(int(lerp(a, b, clamp(u))) for a, b in zip(c1[:3], c2[:3]))


def _rgba(c, a=None):
    al = (c[3] / 255 if len(c) > 3 else 1.0) if a is None else a
    return c[0] / 255, c[1] / 255, c[2] / 255, al


# ---------------------------------------------------------------- fonts / text sprites
@lru_cache(maxsize=512)
def font(kind, px):
    px = max(4, int(px))
    for p in [os.path.join(FONT_DIR, FONT_FILES.get(kind, ""))] + FALLBACKS:
        if p and os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def _pil_to_surface(img):
    arr = np.asarray(img.convert("RGBA")).astype(np.uint16)
    a = arr[:, :, 3:4]
    pre = (arr[:, :, :3] * a // 255).astype(np.uint8)
    bgra = np.dstack([pre[:, :, 2], pre[:, :, 1], pre[:, :, 0], a[:, :, 0].astype(np.uint8)])
    h, w = bgra.shape[:2]
    buf = bytearray(np.ascontiguousarray(bgra).tobytes())
    return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, w, h, w * 4)


@lru_cache(maxsize=3000)
def text_sprite(s, px, color, kind="sign", stroke=0, stroke_color=INK, shadow=0):
    f = font(kind, px)
    l, t, r, b = f.getbbox(s, stroke_width=stroke)
    pad = 4 + shadow * 2
    w, h = r - l + pad * 2, b - t + pad * 2
    img = Image.new("RGBA", (max(1, w), max(1, h)), (0, 0, 0, 0))
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + shadow, pad - t + shadow * 1.4), s, font=f,
                                fill=(0, 0, 0, 120), stroke_width=stroke,
                                stroke_fill=(0, 0, 0, 120))
        img = sh.filter(ImageFilter.GaussianBlur(shadow * 0.6))
    d = ImageDraw.Draw(img)
    d.text((pad - l, pad - t), s, font=f, fill=tuple(color[:3]) + (255,),
           stroke_width=stroke, stroke_fill=tuple(stroke_color[:3]) + (255,))
    return _pil_to_surface(img), w, h


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, surf, S, W, H, t=0.0):
        self.surf, self.S, self.W, self.H = surf, S, W, H
        self.ctx = cairo.Context(surf)
        self.ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        self.ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        self.k = 1.0
        self.t = t
        self.shadows = True
        self.cam()

    # camera ---------------------------------------------------------------
    def cam(self, z=1.0, fx=540.0, fy=960.0, drift=1.0):
        """Set the shot camera; adds a slow float so parallax layers always breathe."""
        t = self.t
        self.z = z * (1 + 0.012 * drift * math.sin(t * 0.45 + 0.7))
        self.fx = fx + 9 * drift * math.sin(t * 0.62)
        self.fy = fy + 6 * drift * math.sin(t * 0.51 + 1.3)

    def _eff(self):
        k = self.k
        return (1 + (self.z - 1) * k, 540 + (self.fx - 540) * k, 960 + (self.fy - 960) * k)

    def P(self, x, y):
        z, fx, fy = self._eff()
        return (((x - fx) * z + 540) * self.S, ((y - fy) * z + 960 + SCENE_LIFT) * self.S)

    def L(self, v):
        return v * self._eff()[0] * self.S

    def vp(self):
        """Vanishing point in world coords: above the camera centre (we look slightly down)."""
        z, fx, fy = self._eff()
        return fx, fy - 1300

    @contextmanager
    def layer(self, k=0.5, blur=0.0, haze=None, haze_a=0.0):
        """Parallax depth layer. k<1 = far (moves less), k>1 = foreground.
        blur (base px) = depth-of-field; haze = colour washed over the layer."""
        old_ctx, old_k, old_shadows = self.ctx, self.k, self.shadows
        self.k = k
        if blur > 0 or haze is not None:
            sc = 0.5 if blur > 0 else 1.0
            w, h = max(1, int(self.W * sc)), max(1, int(self.H * sc))
            tmp = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
            ctx = cairo.Context(tmp)
            ctx.scale(sc, sc)
            ctx.set_line_cap(cairo.LINE_CAP_ROUND)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)
            self.ctx = ctx
            if k < 0.8:
                self.shadows = False
            try:
                yield
            finally:
                if haze is not None and haze_a > 0:
                    ctx.set_operator(cairo.OPERATOR_ATOP)
                    ctx.set_source_rgba(*_rgba(haze, haze_a))
                    ctx.paint()
                    ctx.set_operator(cairo.OPERATOR_OVER)
                src = _blur_surface(tmp, blur * self.S * sc) if blur > 0 else tmp
                old_ctx.save()
                old_ctx.scale(1 / sc, 1 / sc)
                old_ctx.set_source_surface(src, 0, 0)
                old_ctx.get_source().set_filter(cairo.FILTER_BILINEAR)
                old_ctx.paint()
                old_ctx.restore()
                self.ctx, self.k, self.shadows = old_ctx, old_k, old_shadows
        else:
            try:
                yield
            finally:
                self.k = old_k

    # paths ----------------------------------------------------------------
    def _path_rect(self, x0, y0, x1, y1, r=0):
        ctx = self.ctx
        a, b = self.P(x0, y0), self.P(x1, y1)
        X0, Y0, X1, Y1 = min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])
        rr = min(self.L(r), (X1 - X0) / 2, (Y1 - Y0) / 2) if r else 0
        ctx.new_path()
        if rr <= 0.5:
            ctx.rectangle(X0, Y0, X1 - X0, Y1 - Y0)
        else:
            ctx.arc(X1 - rr, Y0 + rr, rr, -math.pi / 2, 0)
            ctx.arc(X1 - rr, Y1 - rr, rr, 0, math.pi / 2)
            ctx.arc(X0 + rr, Y1 - rr, rr, math.pi / 2, math.pi)
            ctx.arc(X0 + rr, Y0 + rr, rr, math.pi, 1.5 * math.pi)
            ctx.close_path()
        return X0, Y0, X1, Y1

    def _path_ellipse(self, cx, cy, rx, ry):
        ctx = self.ctx
        X, Y = self.P(cx, cy)
        RX, RY = max(0.5, self.L(rx)), max(0.5, self.L(ry))
        ctx.new_path()
        ctx.save()
        ctx.translate(X, Y)
        ctx.scale(RX, RY)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        return X - RX, Y - RY, X + RX, Y + RY

    def _path_poly(self, pts):
        ctx = self.ctx
        ctx.new_path()
        P = [self.P(x, y) for x, y in pts]
        ctx.move_to(*P[0])
        for p in P[1:]:
            ctx.line_to(*p)
        ctx.close_path()
        xs, ys = [p[0] for p in P], [p[1] for p in P]
        return min(xs), min(ys), max(xs), max(ys)

    # shading --------------------------------------------------------------
    def _source(self, color, shade, box):
        X0, Y0, X1, Y1 = box
        a = color[3] / 255 if len(color) > 3 else 1.0
        if shade == "flat":
            return cairo.SolidPattern(*_rgba(color))
        if shade == "v":
            g = cairo.LinearGradient(X0, Y0, X0, Y1)
            g.add_color_stop_rgba(0, *_rgba(tint(color, 0.16), a))
            g.add_color_stop_rgba(1, *_rgba(tint(color, -0.16), a))
            return g
        if shade == "cyl":
            g = cairo.LinearGradient(X0, Y0, X1, Y0)
            g.add_color_stop_rgba(0.0, *_rgba(tint(color, -0.28), a))
            g.add_color_stop_rgba(0.28, *_rgba(tint(color, 0.2), a))
            g.add_color_stop_rgba(0.6, *_rgba(color, a))
            g.add_color_stop_rgba(1.0, *_rgba(tint(color, -0.36), a))
            return g
        if shade == "sphere":
            cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2
            r = max(X1 - X0, Y1 - Y0) / 2
            g = cairo.RadialGradient(cx - r * 0.35, cy - r * 0.42, r * 0.05, cx, cy, r * 1.15)
            g.add_color_stop_rgba(0.0, *_rgba(tint(color, 0.42), a))
            g.add_color_stop_rgba(0.45, *_rgba(color, a))
            g.add_color_stop_rgba(1.0, *_rgba(tint(color, -0.38), a))
            return g
        if shade == "side":
            g = cairo.LinearGradient(X0, Y0, X1, Y1)
            g.add_color_stop_rgba(0, *_rgba(tint(color, -0.12), a))
            g.add_color_stop_rgba(1, *_rgba(tint(color, -0.32), a))
            return g
        if shade == "top":
            g = cairo.LinearGradient(X0, Y1, X0, Y0)
            g.add_color_stop_rgba(0, *_rgba(tint(color, 0.22), a))
            g.add_color_stop_rgba(1, *_rgba(tint(color, 0.05), a))
            return g
        return cairo.SolidPattern(*_rgba(color))

    def _finish(self, path_fn, color, shade, outline, shadow, args):
        ctx = self.ctx
        if color is None and not outline:
            return
        if shadow and self.shadows and color is not None:
            for off, al in ((5, 0.11), (10, 0.07), (17, 0.04)):
                ctx.save()
                ctx.translate(self.L(off * 0.55), self.L(off))
                path_fn(*args)
                ctx.set_source_rgba(0.16, 0.09, 0.04, al)
                ctx.fill()
                ctx.restore()
        box = path_fn(*args)
        if color is not None:
            ctx.set_source(self._source(color, shade, box))
            if outline:
                ctx.fill_preserve()
            else:
                ctx.fill()
        if outline:
            col = INK if outline is True else outline
            ctx.set_source_rgba(*_rgba(col, 0.55 if outline is True else 1.0))
            ctx.set_line_width(max(1.0, self.L(3.2 if outline is True else 5)))
            ctx.stroke()

    # primitives -----------------------------------------------------------
    def rect(self, x0, y0, x1, y1, color, r=0, shade="v", outline=True, shadow=True):
        self._finish(self._path_rect, color, shade, outline, shadow, (x0, y0, x1, y1, r))

    def ellipse(self, cx, cy, rx, ry, color, shade="sphere", outline=True, shadow=True):
        self._finish(self._path_ellipse, color, shade, outline, shadow, (cx, cy, rx, ry))

    def circle(self, cx, cy, r, color, shade="sphere", outline=True, shadow=True):
        self.ellipse(cx, cy, r, r, color, shade, outline, shadow)

    def poly(self, pts, color, shade="v", outline=True, shadow=True):
        self._finish(self._path_poly, color, shade, outline, shadow, (pts,))

    def line(self, pts, color, w=6, alpha=None):
        ctx = self.ctx
        ctx.new_path()
        P = [self.P(x, y) for x, y in pts]
        ctx.move_to(*P[0])
        for p in P[1:]:
            ctx.line_to(*p)
        ctx.set_source_rgba(*_rgba(color, alpha))
        ctx.set_line_width(max(1.0, self.L(w)))
        ctx.stroke()

    def tube(self, pts, color, w=20):
        """Shaded cylinder along a polyline (limbs, rods, tails)."""
        self.line(pts, tint(color, -0.45), w + 3.5)
        self.line(pts, tint(color, -0.18), w)
        off = w * 0.16
        self.line([(x - off, y - off) for x, y in pts], color, w * 0.62)
        self.line([(x - off * 1.6, y - off * 1.6) for x, y in pts], tint(color, 0.3), w * 0.2)

    def contact(self, x, y, rx, ry=None, a=0.38):
        """Soft contact shadow (radial falloff ellipse)."""
        ry = ry or rx * 0.22
        ctx = self.ctx
        X, Y = self.P(x, y)
        RX, RY = max(1, self.L(rx)), max(1, self.L(ry))
        ctx.save()
        ctx.translate(X, Y)
        ctx.scale(RX, RY)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0.13, 0.07, 0.03, a)
        g.add_color_stop_rgba(0.6, 0.13, 0.07, 0.03, a * 0.5)
        g.add_color_stop_rgba(1, 0.13, 0.07, 0.03, 0)
        ctx.set_source(g)
        ctx.new_path()
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.fill()
        ctx.restore()

    def glow(self, x, y, r, color, a=0.5):
        ctx = self.ctx
        X, Y = self.P(x, y)
        R = max(1, self.L(r))
        g = cairo.RadialGradient(X, Y, 0, X, Y, R)
        g.add_color_stop_rgba(0, *_rgba(color, a))
        g.add_color_stop_rgba(1, *_rgba(color, 0))
        ctx.set_source(g)
        ctx.new_path()
        ctx.arc(X, Y, R, 0, 2 * math.pi)
        ctx.fill()

    def text(self, x, y, s, size, color=INK, kind="sign", anchor="mm", stroke=0,
             stroke_color=INK, shadow=0, scale=1.0):
        if not s or scale <= 0.01:
            return
        px = int(round(self.L(size)))
        if px < 3:
            return
        surf, w, h = text_sprite(s, px, tuple(color[:3]), kind, int(round(self.L(stroke))),
                                 tuple(stroke_color[:3]), int(round(self.L(shadow))))
        X, Y = self.P(x, y)
        ox = {"l": 0, "m": w / 2, "r": w}[anchor[0]]
        ctx = self.ctx
        ctx.save()
        ctx.translate(X, Y)
        ctx.scale(scale, scale)
        ctx.set_source_surface(surf, -ox, -h / 2)
        ctx.paint()
        ctx.restore()

    # 2.5D solids ------------------------------------------------------------
    def _back(self, x, y, depth):
        vx, vy = self.vp()
        f = depth / (depth + 2600.0)
        return x + (vx - x) * f, y + (vy - y) * f

    def box3d(self, x0, y0, x1, y1, depth, color, top=None, side=None, r=0, front=True,
              outline=True):
        """Box whose front face is (x0,y0)-(x1,y1); top/side faces recede to the vanishing point."""
        vx, vy = self.vp()
        tl, tr, bl, br = (x0, y0), (x1, y0), (x0, y1), (x1, y1)
        btl, btr, bbl, bbr = (self._back(*p, depth) for p in (tl, tr, bl, br))
        if self.shadows:
            self.contact((x0 + x1) / 2 + depth * 0.15, y1 + 4, (x1 - x0) * 0.62 + depth * 0.3,
                         18 + depth * 0.12, 0.33)
        if vy < y0:
            self.poly([tl, tr, btr, btl], top or color, "top", outline, False)
        if vx > x1:
            self.poly([tr, br, bbr, btr], side or color, "side", outline, False)
        elif vx < x0:
            self.poly([tl, bl, bbl, btl], side or color, "side", outline, False)
        if front:
            self.rect(x0, y0, x1, y1, color, r, "v", outline, False)

    def cylinder(self, cx, ytop, ybot, rx, color, top_color=None, ry=None):
        ry = ry or rx * 0.28
        if self.shadows:
            self.contact(cx + 10, ybot + 6, rx * 1.15, ry * 1.3, 0.35)
        self.ellipse(cx, ybot, rx, ry, tint(color, -0.25), "flat", True, False)
        self.rect(cx - rx, ytop, cx + rx, ybot, color, 0, "cyl", False, False)
        self.line([(cx - rx, ytop), (cx - rx, ybot)], INK, 3.2, 0.55)
        self.line([(cx + rx, ytop), (cx + rx, ybot)], INK, 3.2, 0.55)
        self.ellipse(cx, ytop, rx, ry, top_color or tint(color, 0.15), "top", True, False)


def _blur_surface(surf, radius):
    surf.flush()
    w, h, stride = surf.get_width(), surf.get_height(), surf.get_stride()
    arr = np.ndarray((h, stride // 4, 4), np.uint8, buffer=surf.get_data())[:, :w].copy()
    img = Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(max(0.5, radius)))
    out = bytearray(np.ascontiguousarray(np.asarray(img)).tobytes())
    return cairo.ImageSurface.create_for_data(out, cairo.FORMAT_ARGB32, w, h, w * 4)


# ---------------------------------------------------------------- frame setup / finish
SKIES = {
    "day": ((112, 182, 230), (220, 238, 244)),
    "forest": ((140, 196, 200), (230, 238, 214)),
    "night": ((14, 22, 56), (58, 64, 112)),
    "interior": ((150, 110, 74), (226, 196, 150)),
    "shop": ((150, 170, 140), (220, 228, 200)),
    "modern": ((196, 208, 222), (240, 243, 246)),
}


def sky(c, kind):
    top, bot = SKIES[kind]
    ctx = c.ctx
    g = cairo.LinearGradient(0, 0, 0, c.H)
    g.add_color_stop_rgb(0, *[v / 255 for v in top])
    g.add_color_stop_rgb(1, *[v / 255 for v in bot])
    ctx.set_source(g)
    ctx.paint()


@lru_cache(maxsize=4)
def _overlay(W, H, seed=7):
    """Multiply layer: paper grain + fibres + warm vignette."""
    rng = np.random.default_rng(seed)
    coarse = rng.normal(0, 1, (H // 24 + 1, W // 24 + 1)).astype(np.float32)
    coarse = np.array(Image.fromarray(coarse).resize((W, H), Image.BICUBIC))
    fine = rng.normal(0, 1, (H, W)).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    v = (xx / W - 0.5) ** 2 + ((yy / H - 0.45) ** 2) * 0.8
    base = 252 - coarse * 3.5 - fine * 4 - v * 110
    r = np.clip(base, 0, 255)
    g = np.clip(base - 3, 0, 255)
    b = np.clip(base - 10, 0, 255)
    a = np.full_like(r, 255)
    bgra = np.dstack([b, g, r, a]).astype(np.uint8)
    buf = bytearray(np.ascontiguousarray(bgra).tobytes())
    return cairo.ImageSurface.create_for_data(buf, cairo.FORMAT_ARGB32, W, H, W * 4)


def finish(c):
    ctx = c.ctx
    ctx.save()
    ctx.set_operator(cairo.OPERATOR_MULTIPLY)
    ctx.set_source_surface(_overlay(c.W, c.H), 0, 0)
    ctx.paint()
    ctx.restore()


def draw_caption(c, word, age, gold):
    """Single-word pop caption (screen space)."""
    sc = 0.55 + 0.45 * min(1.0, pop(age, 0.0, 0.22))
    S = c.S
    surf, w, h = text_sprite(word, int(104 * S), (255, 215, 0) if gold else (255, 255, 255),
                             "cap", int(11 * S), (0, 0, 0), int(7 * S))
    ctx = c.ctx
    ctx.save()
    ctx.translate(540 * S, CAPTION_Y * S)
    ctx.scale(sc, sc)
    ctx.set_source_surface(surf, -w / 2, -h / 2)
    ctx.paint()
    ctx.restore()


# ---------------------------------------------------------------- scenery
def ground(c, y, col=GRASS, tufts=True, seed=1):
    c.rect(-1400, y, 2500, 3200, col, 0, "flat", False, False)
    g = cairo.LinearGradient(0, c.P(0, y)[1], 0, c.P(0, y + 900)[1])
    g.add_color_stop_rgba(0, *_rgba(tint(col, 0.22), 1))
    g.add_color_stop_rgba(0.12, *_rgba(col, 0))
    g.add_color_stop_rgba(1, *_rgba(tint(col, -0.25), 0.7))
    c._path_rect(-1400, y, 2500, 3200)
    c.ctx.set_source(g)
    c.ctx.fill()
    if tufts:
        rng = np.random.default_rng(seed)
        dc = tint(col, -0.22)
        for _ in range(55):
            x = rng.uniform(-900, 2000)
            yy = y + rng.uniform(20, 700)
            s = 0.6 + (yy - y) / 700
            c.line([(x - 8 * s, yy), (x - 12 * s, yy - 18 * s)], dc, 3 * s)
            c.line([(x, yy), (x + 1 * s, yy - 24 * s)], dc, 3 * s)
            c.line([(x + 8 * s, yy), (x + 13 * s, yy - 17 * s)], dc, 3 * s)


def floor(c, y, col=WOOD_L, planks=True):
    """Perspective plank floor: board lines converge to the vanishing point."""
    c.rect(-1400, y, 2500, 3200, col, 0, "flat", False, False)
    vx, vy = c.vp()
    if planks:
        u = (y - vy) / (2600 - vy)
        for i in range(-14, 30):
            x = i * 110
            xt = vx + (x - vx) * u
            c.line([(xt, y), (x, 2600)], tint(col, -0.2), 4)
    g = cairo.LinearGradient(0, c.P(0, y)[1], 0, c.P(0, y + 120)[1])
    g.add_color_stop_rgba(0, 0, 0, 0, 0.35)
    g.add_color_stop_rgba(1, 0, 0, 0, 0)
    c._path_rect(-1400, y, 2500, y + 120)
    c.ctx.set_source(g)
    c.ctx.fill()


def back_wall(c, top=-900, bottom=1500, col=(214, 170, 118)):
    c.rect(-1400, top, 2500, bottom, col, 0, "v", False, False)
    for i in range(-14, 30):
        c.line([(i * 90, top), (i * 90, bottom)], tint(col, -0.16), 5)
        c.line([(i * 90 + 6, top), (i * 90 + 6, bottom)], tint(col, 0.1), 2)


def hills(c, y, col=(160, 200, 120), off=0, n=8, w=330, h=160):
    for i in range(-4, n):
        cx = i * (w * 1.27) + (off % (w * 1.27))
        c.ellipse(cx, y, w, h, col, "v", False, False)


def cloud(c, x, y, s=1.0):
    for dx, dy, r in ((0, 8, 58), (52, -26, 56), (108, 4, 58), (56, 18, 62)):
        c.circle(x + dx * s, y + dy * s, r * s, (255, 255, 255, 235), "sphere", False, False)


def tree(c, x, y, s=1.0, col=TREE):
    if c.shadows:
        c.contact(x + 12 * s, y + 4 * s, 110 * s, 22 * s, 0.3)
    c.rect(x - 16 * s, y - 125 * s, x + 16 * s, y, WOOD_D, 0, "cyl", True, False)
    for i, (w, h) in enumerate(((122, 165), (102, 145), (78, 125))):
        top = y - 112 * s - i * 86 * s
        apex = (x, top - h * s * 1.2)
        c.poly([(x - w * s, top), (x, top + 14 * s), apex], tint(col, 0.08), "v", True, False)
        c.poly([(x, top + 14 * s), (x + w * s, top), apex], tint(col, -0.2), "v", True, False)


def sun(c, x, y, r=70):
    c.glow(x, y, r * 2.6, (255, 236, 160), 0.55)
    c.circle(x, y, r, (255, 216, 96), "sphere", False, False)


def moon(c, x, y, r=60):
    c.glow(x, y, r * 2.4, (220, 230, 255), 0.35)
    c.circle(x, y, r, (240, 240, 222), "sphere", False, False)
    c.circle(x - r * 0.3, y - r * 0.2, r * 0.18, (214, 214, 196), "flat", False, False)
    c.circle(x + r * 0.25, y + r * 0.3, r * 0.12, (214, 214, 196), "flat", False, False)


def sign(c, x, y, w, h, txt, size=60, bg=CREAM, fg=INK, post=0, kind="sign", sc=1.0,
         thick=14):
    if sc <= 0.01:
        return
    w, h, size, thick = w * sc, h * sc, size * sc, thick * sc
    if post:
        c.rect(x - 11, y + h / 2 - 6, x + 11, y + h / 2 + post, WOOD_D, 0, "cyl", True, True)
    c.box3d(x - w / 2, y - h / 2, x + w / 2, y + h / 2, thick, bg, side=tint(bg, -0.3), r=8)
    c.text(x, y + 2 * sc, txt, size, fg, kind=kind)


def badge(c, t, txt, t0=0.0, x=540, y=560):
    s = pop(t, t0)
    if s <= 0.01:
        return
    with c.layer(1.0):
        c.rect(x - 195 * s, y - 64 * s, x + 195 * s, y + 64 * s, RED, 32 * s, "v", WHITE, True)
        c.text(x, y + 4 * s, txt, 76 * s, WHITE, kind="cap", shadow=3)


def shack(c, x, y, s=1.0, sign_txt="BANK", sign_sc=1.0, door_open=False, sign_size=None,
          depth=260):
    w, h = 300 * s, 460 * s
    d = depth * s
    c.box3d(x - w, y - h, x + w, y, d, WOOD, top=ROOF, side=tint(WOOD, -0.25))
    for i in range(1, 9):
        yy = y - i * h / 9
        c.line([(x - w, yy), (x + w, yy)], tint(WOOD, -0.25), 4)
        c.line([(x - w, yy + 4), (x + w, yy + 4)], tint(WOOD, 0.12), 2)
    # gabled roof: front triangle + roof plane receding to the vanishing point
    apex = (x, y - h - 200 * s)
    el, er = (x - w - 44 * s, y - h + 6 * s), (x + w + 44 * s, y - h + 6 * s)
    bapex, bel, ber = c._back(*apex, d), c._back(*el, d), c._back(*er, d)
    vx, _ = c.vp()
    if vx >= x:
        c.poly([apex, er, ber, bapex], ROOF, "side", True, False)
    else:
        c.poly([apex, el, bel, bapex], ROOF, "side", True, False)
    c.poly([el, er, apex], tint(ROOF, 0.08), "v", True, False)
    c.poly([(x - w * 0.82, y - h + 4 * s), (x + w * 0.82, y - h + 4 * s), (x, y - h - 150 * s)],
           tint(WOOD, -0.05), "v", True, False)
    c.rect(x - 64 * s, y - 214 * s, x + 64 * s, y, (34, 22, 16) if door_open else WOOD_D,
           6 * s, "v", True, False)
    if not door_open:
        c.circle(x + 36 * s, y - 104 * s, 9 * s, GOLD, "sphere", False, False)
    for wx in (-170, 170):
        c.rect(x + (wx - 62) * s, y - 336 * s, x + (wx + 62) * s, y - 222 * s, (176, 214, 232),
               4 * s, "v", WOOD_D, False)
        c.line([(x + (wx - 40) * s, y - 330 * s), (x + (wx - 10) * s, y - 228 * s)],
               (255, 255, 255), 5 * s, 0.5)
    if sign_txt:
        sign(c, x, y - h + 64 * s, 390 * s, 104 * s, sign_txt, sign_size or 66 * s, sc=sign_sc)
    return apex


def banknote(c, x, y, w=300, label="BANK OF YOU", amount="$5", portrait="face", sc=1.0,
             col=MONEY):
    if sc <= 0.01:
        return
    w = w * sc
    h = w * 0.46
    lift = 6 * sc
    c.rect(x - w / 2 + lift, y - h / 2 + lift, x + w / 2 + lift, y + h / 2 + lift,
           tint(col, -0.35), 8 * sc, "flat", False, True)
    c.rect(x - w / 2, y - h / 2, x + w / 2, y + h / 2, col, 8 * sc, "v", MONEY_D, False)
    c.rect(x - w / 2 + 12 * sc, y - h / 2 + 12 * sc, x + w / 2 - 12 * sc, y + h / 2 - 12 * sc,
           None, 6 * sc, "flat", MONEY_D, False)
    c.text(x - w * 0.31, y - h * 0.2, amount, 40 * w / 300, (30, 80, 40))
    if label:
        c.text(x + w * 0.02, y + h * 0.28, label, 22 * w / 300, (30, 80, 40))
    px, py, pr = x + w * 0.2, y - h * 0.05, h * 0.27
    c.ellipse(px, py, pr * 1.1, pr, (226, 238, 214), "v", MONEY_D, False)
    if portrait == "face":
        c.circle(px, py + 2 * sc, pr * 0.55, SKIN, "sphere", False, False)
        c.ellipse(px, py - pr * 0.45, pr * 0.55, pr * 0.22, (70, 46, 34), "sphere", False, False)
    elif portrait == "dog":
        c.circle(px, py + 2 * sc, pr * 0.55, (176, 124, 82), "sphere", False, False)
        for side in (-1, 1):
            c.ellipse(px + side * pr * 0.5, py - pr * 0.1, pr * 0.18, pr * 0.35, (110, 70, 40),
                      "sphere", False, False)
        c.circle(px, py + pr * 0.15, pr * 0.12, INK, "flat", False, False)
    elif portrait == "name":
        c.text(px, py, "YOU", 22 * w / 300, (30, 80, 40))
    elif portrait == "modern":
        c.circle(px, py, pr * 0.55, (150, 162, 150), "sphere", False, False)


def coin(c, x, y, r=26, sc=1.0, edge=True):
    if sc <= 0.01:
        return
    r *= sc
    if edge:
        c.ellipse(x + r * 0.08, y + r * 0.16, r, r, GOLD_D, "flat", True, True)
    c.circle(x, y, r, GOLD, "sphere", GOLD_D, False)
    c.circle(x, y, r * 0.62, None, "flat", GOLD_D, False)


def sparkle(c, x, y, r, t, phase=0.0):
    k = 0.5 + 0.5 * math.sin(t * 7 + phase)
    r = r * (0.45 + 0.75 * k)
    c.glow(x, y, r * 1.6, (255, 246, 190), 0.6 * k)
    c.poly([(x, y - r), (x + r * 0.22, y - r * 0.22), (x + r, y), (x + r * 0.22, y + r * 0.22),
            (x, y + r), (x - r * 0.22, y + r * 0.22), (x - r, y), (x - r * 0.22, y - r * 0.22)],
           (255, 250, 214), "flat", False, False)


def strongbox(c, x, y, s=1.0, label="RESERVES", coins=0, lid=True):
    w, h = 260 * s, 170 * s
    c.box3d(x - w, y - h, x + w, y + h, 200 * s, (92, 96, 112), top=(70, 74, 88),
            side=(64, 68, 82), r=14 * s)
    c.rect(x - w + 26 * s, y - h + 8 * s, x + w - 26 * s, y - h + 52 * s, (38, 38, 46), 4 * s,
           "v", False, False)
    for i in range(coins):
        cx = x - w + 72 * s + (i % 7) * 62 * s
        cy = y - h + 24 * s - (i // 7) * 26 * s
        coin(c, cx, cy, 28 * s)
    for bx in (-0.55, 0.55):
        c.rect(x + bx * w - 15 * s, y - h, x + bx * w + 15 * s, y + h, STEEL, 0, "cyl", True,
               False)
    if lid:
        c.poly([(x - w, y - h), (x + w, y - h), (x + w - 34 * s, y - h - 124 * s),
                (x - w + 34 * s, y - h - 124 * s)], (76, 80, 94), "top", True, False)
    if label:
        c.rect(x - 152 * s, y + 18 * s, x + 152 * s, y + 102 * s, CREAM, 8 * s, "v", True, False)
        c.text(x, y + 62 * s, label, 48 * s, INK)


def barrel(c, x, y, s=1.0, label="GOLD", top_fill=None):
    w, h = 170 * s, 250 * s
    c.cylinder(x, y - h, y + h, w, WOOD, top_color=WOOD_D, ry=42 * s)
    for k in (-0.62, 0.62):
        c.rect(x - w - 3, y + k * h - 9 * s, x + w + 3, y + k * h + 9 * s, STEEL, 3, "cyl",
               True, False)
    c.ellipse(x, y - h, w - 16 * s, 31 * s, top_fill or (60, 40, 25), "v", True, False)
    if label:
        c.text(x, y + 10 * s, label, 92 * s, (64, 38, 20))


def book(c, x, y, s=1.0, open_u=0.0):
    w, h = 300 * s, 200 * s
    if open_u < 0.5:
        c.box3d(x - w, y - h, x + w, y + h, 70 * s, (124, 40, 40), top=CREAM, side=CREAM,
                r=10 * s)
        c.rect(x - w + 22 * s, y - h + 22 * s, x + w - 22 * s, y + h - 22 * s, None, 8 * s,
               "flat", GOLD, False)
        c.text(x, y - 30 * s, "BANK NOTE", 52 * s, GOLD)
        c.text(x, y + 40 * s, "REPORTER", 52 * s, GOLD)
    else:
        c.box3d(x - w * 1.9, y - h, x + w * 1.9, y + h, 30 * s, (124, 40, 40), r=10 * s)
        c.rect(x - w * 1.8, y - h + 14 * s, x - 6 * s, y + h - 14 * s, CREAM, 4, "v", True,
               False)
        c.rect(x + 6 * s, y - h + 14 * s, x + w * 1.8, y + h - 14 * s, CREAM, 4, "v", True,
               False)
        for i in range(6):
            yy = y - h + 60 * s + i * 50 * s
            c.line([(x - w * 1.7, yy), (x - 40 * s, yy)], (176, 166, 146), 4)
            c.line([(x + 40 * s, yy), (x + w * 1.7, yy)], (176, 166, 146), 4)


def press(c, x, y, s=1.0, t=0.0):
    c.box3d(x - 200 * s, y - 420 * s, x + 200 * s, y, 180 * s, (74, 74, 86), r=12 * s)
    c.rect(x - 170 * s, y - 380 * s, x + 170 * s, y - 250 * s, (46, 46, 54), 6, "v", True, False)
    ang = t * 5
    cx, cy = x + 240 * s, y - 300 * s
    c.circle(cx, cy, 74 * s, STEEL, "sphere", True, True)
    for k in range(4):
        a = ang + k * math.pi / 2
        c.tube([(cx, cy), (cx + math.cos(a) * 66 * s, cy + math.sin(a) * 66 * s)], GREY_D,
               12 * s)
    c.circle(cx, cy, 18 * s, GREY_D, "sphere", True, False)
    ry = y - 300 * s + (0.5 - 0.5 * math.cos(t * 5)) * 60 * s
    c.box3d(x - 140 * s, ry, x + 140 * s, ry + 40 * s, 120 * s, STEEL)
    c.box3d(x - 220 * s, y - 140 * s, x + 220 * s, y - 100 * s, 200 * s, (96, 96, 108))


# ---------------------------------------------------------------- characters
KINDS = {
    #        legs torsoH torsoW headR  coat          pants           shirt
    "boss": (72, 128, 162, 66, EMERALD, (72, 62, 74), WHITE),
    "gus": (118, 188, 224, 74, RED, (70, 92, 146), RED),
    "mo": (128, 142, 106, 58, PURPLE, (62, 52, 72), WHITE),
    "pike": (152, 204, 106, 56, GREY, GREY_D, WHITE),
    "shop": (96, 142, 142, 62, (92, 124, 166), (82, 72, 62), WHITE),
    "folk1": (96, 138, 142, 60, (184, 122, 62), (82, 72, 92), WHITE),
    "folk2": (96, 138, 142, 60, (92, 144, 176), (72, 62, 52), WHITE),
    "folk3": (96, 138, 142, 60, (204, 172, 92), (92, 72, 62), WHITE),
    "folk4": (96, 138, 142, 60, (154, 92, 124), (62, 72, 82), WHITE),
    "modern": (118, 188, 224, 74, (72, 112, 172), (52, 62, 92), WHITE),
}
_BLINK_SEED = {k: i * 0.53 for i, k in enumerate(KINDS)}


def _arc_stroke(c, cx, cy, rx, ry, a0, a1, w):
    ctx = c.ctx
    ctx.new_path()
    X, Y = c.P(cx, cy)
    ctx.save()
    ctx.translate(X, Y)
    ctx.scale(max(0.5, c.L(rx)), max(0.5, c.L(ry)))
    ctx.arc(0, 0, 1, math.radians(a0), math.radians(a1))
    ctx.restore()
    ctx.set_source_rgba(*_rgba(INK))
    ctx.set_line_width(max(1.0, c.L(w)))
    ctx.stroke()


def person(c, x, y, s=1.0, kind="boss", t=0.0, arm_l=15, arm_r=15, mouth="smile",
           walk=0.0, look=0.0, blink=True, sweat=False, boots=False, hold_r=None, hold_l=None,
           squash=1.0, brows=0.0):
    legs, th, tw, hr, coat, pants, shirt = KINDS[kind]
    legs, th, tw, hr = legs * s, th * s, tw * s, hr * s
    ph = t * 8.5
    bob = (abs(math.sin(ph)) * 9 * s * walk) + math.sin(t * 2.2) * 2.2 * s
    y0 = y - bob
    if c.shadows:
        c.contact(x + 8 * s, y + 4 * s, tw * 0.75, 20 * s, 0.38)
    # legs (shaded tubes) with smooth swing + foot lift
    lw = (25 if kind not in ("mo", "pike") else 17) * s
    for dx, k in ((-tw * 0.22, 1), (tw * 0.22, -1)):
        sw = math.sin(ph) * 24 * s * walk * k
        lift = max(0.0, math.sin(ph) * k) * 12 * s * walk
        fx = x + dx + sw
        c.tube([(x + dx, y0 - legs), (fx, y0 - 8 * s - lift)], pants, lw * 1.5)
        if kind == "gus" and not boots:
            c.ellipse(fx + 10 * s, y0 - 6 * s - lift, 27 * s, 13 * s, SKIN, "sphere", True, False)
        else:
            c.ellipse(fx + 10 * s, y0 - 8 * s - lift, 31 * s, 15 * s, (52, 38, 32), "sphere",
                      True, False)
    sq = squash
    top = y0 - legs - th * sq
    # torso
    if kind == "pike":
        c.poly([(x - tw / 2, top), (x + tw / 2, top), (x + tw * 0.72, y0 - legs * 0.4),
                (x - tw * 0.72, y0 - legs * 0.4)], coat, "v", True, True)
    else:
        hw = tw / 2 / sq ** 0.5
        c.rect(x - hw, top, x + hw, y0 - legs + 10 * s, coat, tw * 0.36, "cyl", True, True)
    if kind == "boss":
        c.poly([(x - tw * 0.18, top + 4 * s), (x + tw * 0.18, top + 4 * s), (x, top + th * 0.55)],
               shirt, "v", False, False)
        c.line([(x - tw * 0.3, top + th * 0.55), (x, top + th * 0.68),
                (x + tw * 0.3, top + th * 0.55)], GOLD, 5 * s)
        for i in range(3):
            c.circle(x, top + th * (0.62 + i * 0.12), 6.5 * s, GOLD, "sphere", False, False)
    elif kind == "gus":
        for i in range(1, 5):
            c.line([(x - tw / 2 + 10 * s, top + i * th / 5),
                    (x + tw / 2 - 10 * s, top + i * th / 5)], (150, 36, 30), 6 * s, 0.85)
        for i in range(1, 4):
            c.line([(x - tw / 2 + i * tw / 4, top + 12 * s), (x - tw / 2 + i * tw / 4, y0 - legs)],
                   (150, 36, 30), 6 * s, 0.85)
    elif kind in ("mo", "pike", "shop"):
        c.poly([(x - tw * 0.16, top + 4 * s), (x + tw * 0.16, top + 4 * s), (x, top + th * 0.4)],
               shirt, "v", False, False)
        if kind == "shop":
            c.rect(x - tw * 0.38, top + th * 0.35, x + tw * 0.38, y0 - legs + 6 * s,
                   (238, 232, 216), 10 * s, "v", True, False)
    elif kind == "modern":
        c.poly([(x - tw * 0.2, top + 4 * s), (x + tw * 0.2, top + 4 * s), (x, top + th * 0.3)],
               shirt, "v", False, False)
    # arms (shaded tubes) + hands (spheres)
    alen = th * 0.86
    hands = {}
    aw = (27 if kind == "gus" else 21) * s
    for side, ang in ((-1, arm_l), (1, arm_r)):
        sx, sy = x + side * tw * 0.42, top + 28 * s
        a = math.radians(ang)
        ex, ey = sx + side * math.sin(a) * alen * 0.5, sy + math.cos(a) * alen * 0.5
        a2 = math.radians(ang + 14)
        hx, hy = ex + side * math.sin(a2) * alen * 0.5, ey + math.cos(a2) * alen * 0.5
        c.tube([(sx, sy), (ex, ey), (hx, hy)], coat, aw)
        c.circle(hx, hy, (19 if kind == "gus" else 15.5) * s, SKIN, "sphere", True, False)
        hands["l" if side < 0 else "r"] = (hx, hy)
    # head (sphere); features shift with `look` to fake a head turn
    hx, hy = x, top - hr * 0.86
    turn = look * hr * 0.22
    c.circle(hx - turn * 1.6, hy + 4 * s, hr * 0.98, tint(SKIN, -0.1), "sphere", False, False)
    c.circle(hx, hy, hr, SKIN, "sphere", True, True)
    fx_ = hx + turn
    if kind == "gus":
        c.ellipse(fx_, hy + hr * 0.56, hr * 0.86, hr * 0.5, (152, 92, 52), "sphere", False, False)
        c.ellipse(hx, hy - hr * 0.55, hr * 1.03, hr * 0.64, RED, "sphere", True, False)
        c.rect(hx - hr * 1.03, hy - hr * 0.42, hx + hr * 1.03, hy - hr * 0.2, (172, 40, 34),
               6 * s, "cyl", True, False)
        c.circle(hx, hy - hr * 1.17, hr * 0.21, WHITE, "sphere", False, False)
    elif kind == "boss":
        c.ellipse(hx - hr * 0.1 - turn * 0.3, hy - hr * 0.62, hr * 0.96, hr * 0.5, (64, 42, 30),
                  "sphere", False, False)
    elif kind == "mo":
        c.ellipse(hx, hy - hr * 0.72, hr * 0.92, hr * 0.42, (40, 30, 30), "sphere", False, False)
    elif kind == "pike":
        c.box3d(hx - hr * 0.75, hy - hr * 1.95, hx + hr * 0.75, hy - hr * 0.62, 26 * s,
                (60, 62, 72), r=4 * s)
        c.ellipse(hx, hy - hr * 0.64, hr * 1.18, hr * 0.15, (52, 54, 64), "v", True, False)
    elif kind == "shop":
        c.ellipse(hx, hy - hr * 0.72, hr * 0.82, hr * 0.36, (206, 206, 206), "sphere", False,
                  False)
    elif kind.startswith("folk"):
        c.ellipse(hx, hy - hr * 0.68, hr * 1.28, hr * 0.28, (112, 82, 52), "v", True, False)
        c.rect(hx - hr * 0.7, hy - hr * 1.22, hx + hr * 0.7, hy - hr * 0.66, (112, 82, 52),
               8 * s, "cyl", True, False)
    elif kind == "modern":
        c.ellipse(hx, hy - hr * 0.55, hr * 1.03, hr * 0.64, (232, 122, 42), "sphere", False,
                  False)
    # eyes: white + pupil + catch-light, smooth blink
    bl = 1.0
    if blink:
        ph_b = (t + _BLINK_SEED.get(kind, 0)) % 3.4
        if ph_b < 0.16:
            bl = abs(ph_b - 0.08) / 0.08
    ex = hr * 0.36
    for side in (-1, 1):
        ecx, ecy = fx_ + side * ex, hy - 4 * s
        if bl < 0.25:
            c.line([(ecx - 9 * s, ecy), (ecx + 9 * s, ecy)], INK, 4 * s)
        else:
            c.ellipse(ecx, ecy, 11 * s, 13 * s * bl, WHITE, "flat", (60, 40, 30), False)
            c.circle(ecx + look * 4 * s, ecy + 1 * s, 7 * s * min(1, bl * 1.2), INK, "flat",
                     False, False)
            c.circle(ecx + look * 4 * s - 2.5 * s, ecy - 2.5 * s, 2.4 * s, WHITE, "flat", False,
                     False)
        if brows:
            c.line([(ecx - 11 * s, ecy - 20 * s + side * brows * 6 * s),
                    (ecx + 11 * s, ecy - 20 * s - side * brows * 6 * s)], INK, 4 * s)
    c.glow(fx_ - hr * 0.62, hy + hr * 0.26, hr * 0.22, (244, 140, 130), 0.55)
    c.glow(fx_ + hr * 0.62, hy + hr * 0.26, hr * 0.22, (244, 140, 130), 0.55)
    my = hy + hr * 0.38
    if kind == "mo":
        for side in (-1, 1):
            c.ellipse(fx_ + side * hr * 0.45, my - hr * 0.12, hr * 0.5, hr * 0.15, (40, 30, 30),
                      "sphere", False, False)
            c.circle(fx_ + side * hr * 0.93, my - hr * 0.27, hr * 0.13, (40, 30, 30), "sphere",
                     False, False)
    elif kind == "pike":
        c.ellipse(fx_, my - hr * 0.1, hr * 0.38, hr * 0.1, (116, 116, 116), "sphere", False,
                  False)
    if mouth == "smile":
        _arc_stroke(c, fx_, my - hr * 0.05, hr * 0.3, hr * 0.2, 15, 165, 5 * s)
    elif mouth in ("grin", "laugh"):
        oy = hr * (0.2 if mouth == "grin" else 0.27)
        c.ellipse(fx_, my, hr * 0.33, oy, (126, 30, 42), "v", INK, False)
        c.rect(fx_ - hr * 0.26, my - oy + 2 * s, fx_ + hr * 0.26, my - oy * 0.25, WHITE, 3 * s,
               "flat", False, False)
    elif mouth == "o":
        c.ellipse(fx_, my + hr * 0.04, hr * 0.13, hr * 0.16, (126, 30, 42), "v", INK, False)
    elif mouth == "flat":
        c.line([(fx_ - hr * 0.22, my), (fx_ + hr * 0.22, my)], INK, 5 * s)
    elif mouth == "sad":
        _arc_stroke(c, fx_, my + hr * 0.15, hr * 0.26, hr * 0.16, 200, 340, 5 * s)
    if sweat:
        dy = (t * 110) % (hr * 1.2)
        c.ellipse(hx + hr * 0.98, hy - hr * 0.3 + dy, 9 * s, 14 * s, (150, 206, 244), "sphere",
                  False, False)
    # props in hands
    if hold_r == "magnifier":
        mx, my2 = hands["r"]
        c.tube([(mx, my2), (mx + 30 * s, my2 - 72 * s)], WOOD_D, 13 * s)
        c.circle(mx + 52 * s, my2 - 122 * s, 64 * s, (200, 232, 248, 140), "flat",
                 (156, 124, 60), False)
        c.line([(mx + 22 * s, my2 - 150 * s), (mx + 40 * s, my2 - 168 * s)], WHITE, 7 * s, 0.7)
    if hold_r == "hammer":
        mx, my2 = hands["r"]
        c.tube([(mx, my2), (mx + 10 * s, my2 - 72 * s)], WOOD_D, 11 * s)
        c.box3d(mx - 22 * s, my2 - 96 * s, mx + 42 * s, my2 - 64 * s, 18 * s, STEEL, r=4 * s)
    if hold_r == "axe":
        mx, my2 = hands["r"]
        c.tube([(mx, my2), (mx + 22 * s, my2 - 124 * s)], WOOD_D, 13 * s)
        c.poly([(mx + 22 * s, my2 - 124 * s), (mx + 78 * s, my2 - 140 * s),
                (mx + 72 * s, my2 - 86 * s), (mx + 24 * s, my2 - 98 * s)], STEEL, "v", True, True)
    if hold_l == "lantern":
        mx, my2 = hands["l"]
        c.glow(mx, my2 + 32 * s, 120 * s, (255, 210, 110), 0.45)
        c.rect(mx - 15 * s, my2 + 12 * s, mx + 15 * s, my2 + 52 * s, (255, 224, 126), 4 * s,
               "v", INK, False)
    return hands


def bear(c, x, y, s=1.0, t=0.0, wave=True):
    col = (134, 86, 54)
    if c.shadows:
        c.contact(x + 10 * s, y + 4 * s, 110 * s, 24 * s)
    c.ellipse(x, y - 122 * s, 96 * s, 126 * s, col, "sphere", True, True)
    c.ellipse(x, y - 100 * s, 56 * s, 72 * s, (180, 134, 94), "sphere", False, False)
    c.circle(x, y - 272 * s, 72 * s, col, "sphere", True, True)
    for side in (-1, 1):
        c.circle(x + side * 56 * s, y - 328 * s, 25 * s, tint(col, -0.2), "sphere", True, False)
    c.ellipse(x, y - 252 * s, 31 * s, 23 * s, (182, 136, 96), "sphere", False, False)
    c.circle(x, y - 264 * s, 9.5 * s, INK, "sphere", False, False)
    c.circle(x - 25 * s, y - 292 * s, 7.5 * s, INK, "flat", False, False)
    c.circle(x + 25 * s, y - 292 * s, 7.5 * s, INK, "flat", False, False)
    a = math.radians(150 + (math.sin(t * 7) * 24 if wave else -110))
    sx, sy = x + 82 * s, y - 192 * s
    c.tube([(sx, sy), (sx + math.sin(a) * 112 * s, sy + math.cos(a) * 112 * s)], col, 40 * s)


def wildcat(c, x, y, s=1.0, t=0.0, flip=1):
    col, str_ = (216, 152, 82), (152, 92, 42)
    if c.shadows:
        c.contact(x, y + 2 * s, 100 * s, 16 * s, 0.3)
    tail = math.sin(t * 3.2) * 22 * s
    c.tube([(x - flip * 84 * s, y - 52 * s), (x - flip * 112 * s, y - 80 * s),
            (x - flip * 132 * s, y - 104 * s + tail)], col, 17 * s)
    c.ellipse(x, y - 46 * s, 92 * s, 46 * s, col, "sphere", True, False)
    for i in range(-2, 3):
        c.line([(x + i * 30 * s, y - 88 * s), (x + i * 30 * s, y - 62 * s)], str_, 6 * s)
    breathe = 1 + 0.03 * math.sin(t * 2.5)
    hx = x + flip * 80 * s
    hy = y - 96 * s * breathe
    for side in (-1, 1):
        c.poly([(hx + side * 40 * s, hy - 24 * s), (hx + side * 30 * s, hy - 70 * s),
                (hx + side * 8 * s, hy - 36 * s)], col, "v", True, False)
    c.circle(hx, hy, 46 * s, col, "sphere", True, False)
    for side in (-1, 1):
        c.ellipse(hx + side * 16 * s, hy - 4 * s, 7 * s, 9 * s, (60, 120, 40), "flat", False,
                  False)
        c.ellipse(hx + side * 16 * s, hy - 4 * s, 2.5 * s, 8 * s, INK, "flat", False, False)
        c.line([(hx + side * 30 * s, hy + 14 * s), (hx + side * 62 * s, hy + 10 * s)], INK, 2 * s)


def dog(c, x, y, s=1.0, t=0.0):
    col = (176, 124, 82)
    if c.shadows:
        c.contact(x, y + 2 * s, 90 * s, 18 * s)
    wag = math.sin(t * 13) * 26 * s
    c.tube([(x - 64 * s, y - 72 * s), (x - 108 * s, y - 112 * s + wag)], col, 15 * s)
    c.ellipse(x, y - 62 * s, 72 * s, 62 * s, col, "sphere", True, True)
    c.circle(x + 10 * s, y - 152 * s, 56 * s, col, "sphere", True, False)
    for side in (-1, 1):
        c.ellipse(x + 10 * s + side * 46 * s, y - 150 * s, 18 * s, 42 * s, (112, 72, 42),
                  "sphere", True, False)
    c.circle(x - 6 * s, y - 162 * s, 7 * s, INK, "flat", False, False)
    c.circle(x + 26 * s, y - 162 * s, 7 * s, INK, "flat", False, False)
    c.circle(x + 10 * s, y - 136 * s, 10 * s, INK, "sphere", False, False)


def pony(c, x, y, s=1.0, t=0.0, col=(200, 160, 120), run=0.0, flip=1):
    ph = t * 11
    bob = abs(math.sin(ph)) * 10 * s * run
    yb = y - bob
    if c.shadows:
        c.contact(x, y + 4 * s, 150 * s, 24 * s)
    legs = []
    for i, lx in enumerate((-72, -42, 42, 72)):
        sw = math.sin(ph + i * 1.6) * 30 * s * run
        legs.append(((x + lx * s, yb - 122 * s), (x + lx * s + sw, y - 6 * s)))
    for a, b in legs[::2]:
        c.tube([a, b], tint(col, -0.25), 19 * s)
    c.tube([(x - flip * 116 * s, yb - 160 * s), (x - flip * 152 * s, yb - 100 * s)],
           (92, 62, 42), 17 * s)
    c.ellipse(x, yb - 152 * s, 122 * s, 62 * s, col, "sphere", True, True)
    for a, b in legs[1::2]:
        c.tube([a, b], col, 19 * s)
    hx = x + flip * 122 * s
    c.tube([(x + flip * 82 * s, yb - 170 * s), (hx, yb - 252 * s)], col, 46 * s)
    c.ellipse(hx + flip * 26 * s, yb - 262 * s, 52 * s, 31 * s, col, "sphere", True, False)
    c.tube([(x + flip * 70 * s, yb - 202 * s), (hx - flip * 10 * s, yb - 282 * s)],
           (92, 62, 42), 14 * s)
    c.circle(hx + flip * 26 * s, yb - 270 * s, 6 * s, INK, "flat", False, False)
    return (x, yb - 212 * s)


def crowd_person(c, x, y, s, t, i, lantern=False, sign_txt=None):
    k = ["folk1", "folk2", "folk3", "folk4"][i % 4]
    hands = person(c, x, y, s, k, t + i * 0.37, arm_l=25, arm_r=160 if sign_txt else 30,
                   mouth="o" if i % 2 else "flat", walk=1.0,
                   hold_l="lantern" if lantern else None)
    if sign_txt:
        hx, hy = hands["r"]
        c.tube([(hx, hy), (hx, hy - 122 * s)], WOOD_D, 11 * s)
        sign(c, hx, hy - 172 * s, 300 * s, 90 * s, sign_txt, 44 * s)

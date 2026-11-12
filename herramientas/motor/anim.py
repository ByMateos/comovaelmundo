"""Animated explainer for video 1 (Cómo Va el Mundo), simple-language version.

Each scene = list of beats (one narration sentence each). When a beat starts,
its elements animate in over ANIM seconds, then the frame holds until the next
beat. Frames are written once and timed with an ffmpeg concat list.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, os, sys, json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_brand_v2 as brand

S = 2
W, H = 1920, 1080
FPS = 25
ANIM = 0.8
WPS = 2.4  # narration speed, words per second

BGC = (10, 14, 30)
CYAN, VIOLET, YELLOW = (34, 211, 238), (139, 92, 246), (255, 214, 10)
WHITE, MUTED, DIM = (240, 244, 255), (150, 168, 205), (60, 72, 110)
RED, GREEN, ORANGE = (248, 113, 113), (52, 199, 120), (251, 146, 60)
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
_fc = {}


def F(path, size):
    k = (path, round(size, 1))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, max(1, int(size * S)))
    return _fc[k]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(p):
    p = max(0.0, min(1.0, p))
    return 1 - (1 - p) ** 3


def back(p):
    p = max(0.0, min(1.0, p))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def fmt(v, dec=0):
    s = f"{v:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


_BG = None


def background():
    global _BG
    if _BG is None:
        bg = brand.radial_bg(W * S, H * S, W * S * 0.45, H * S * 0.42, W * S * 0.7)
        d = ImageDraw.Draw(bg)
        for y in range(24, H, 48):
            for x in range(24, W, 48):
                d.ellipse([(x - 1.4) * S, (y - 1.4) * S, (x + 1.4) * S, (y + 1.4) * S], fill=(24, 32, 62))
        _BG = bg
    return _BG.copy()


class Fr:
    """One frame. All coordinates in 1920x1080 units."""

    def __init__(self):
        self.im = background()
        self.d = ImageDraw.Draw(self.im)
        self.gl = Image.new("RGB", self.im.size, (0, 0, 0))
        self.gd = ImageDraw.Draw(self.gl)

    def P(self, *v):
        return [x * S for x in v]

    def c(self, col, o):
        return lerp(BGC, col, max(0, min(1, o)))

    # -- primitives (o = opacity/progress 0..1) --
    def t(self, x, y, s, size, color=WHITE, font=FX, anchor="ls", o=1, glow=False, slide=24):
        if o <= 0:
            return
        y = y + (1 - ease(o)) * slide
        col = self.c(color, ease(o))
        self.d.text((x * S, y * S), s, font=F(font, size), fill=col, anchor=anchor)
        if glow:
            self.gd.text((x * S, y * S), s, font=F(font, size), fill=lerp((0, 0, 0), color, ease(o)), anchor=anchor)

    def tw(self, s, size, font=FX):
        return self.d.textlength(s, font=F(font, size)) / S

    def wrap(self, x, y, s, size, maxw, color=MUTED, font=FS, o=1, lh=1.32, anchor="ls"):
        words, lines, line = s.split(), [], ""
        for w in words:
            tst = (line + " " + w).strip()
            if self.tw(tst, size, font) > maxw and line:
                lines.append(line)
                line = w
            else:
                line = tst
        lines.append(line)
        for i, ln in enumerate(lines):
            self.t(x, y + i * size * lh, ln, size, color, font, anchor, o)
        return y + len(lines) * size * lh

    def header(self, kicker, title, o):
        if o <= 0:
            return
        self.d.rounded_rectangle(self.P(120, 82, 128, 116), radius=2 * S, fill=self.c(CYAN, ease(o)))
        self.t(144, 112, kicker.upper(), 26, CYAN, FB, o=o, slide=0)
        if title:
            self.t(120, 210, title, 74, WHITE, FX, o=o)

    def box(self, x0, y0, x1, y1, color, o=1, fill=None, r=22, w=3, glow=True):
        if o <= 0:
            return
        col = self.c(color, ease(o))
        self.d.rounded_rectangle(self.P(x0, y0, x1, y1), radius=r * S, outline=col, width=w * S, fill=fill)
        if glow:
            self.gd.rounded_rectangle(self.P(x0, y0, x1, y1), radius=r * S, outline=lerp((0, 0, 0), color, ease(o)), width=w * S)

    def bar(self, x0, base, x1, h, color, o=1, label=None, lsize=60):
        hh = h * ease(o)
        if hh < 2:
            return
        self.d.rounded_rectangle(self.P(x0, base - hh, x1, base), radius=14 * S, fill=color)
        self.gd.rounded_rectangle(self.P(x0, base - hh, x1, base), radius=14 * S, fill=lerp((0, 0, 0), color, 0.7))
        if label:
            self.t((x0 + x1) / 2, base - hh - 24, label, lsize, WHITE, FX, "ms", o, slide=0)

    def arrow(self, x0, y0, x1, y1, color=YELLOW, w=10, head=36, o=1, glow=True):
        e = ease(o)
        if e <= 0.02:
            return
        xe, ye = x0 + (x1 - x0) * e, y0 + (y1 - y0) * e
        for dr in [self.d] + ([self.gd] if glow else []):
            dr.line(self.P(x0, y0, xe, ye), fill=color, width=int(w * S))
            if e > 0.6:
                a = math.atan2(y1 - y0, x1 - x0)
                hd = head * min(1, (e - 0.6) / 0.4)
                tip = (xe + math.cos(a) * hd * 0.5, ye + math.sin(a) * hd * 0.5)
                l = (tip[0] - hd * math.cos(a - 0.5), tip[1] - hd * math.sin(a - 0.5))
                r = (tip[0] - hd * math.cos(a + 0.5), tip[1] - hd * math.sin(a + 0.5))
                dr.polygon([(v[0] * S, v[1] * S) for v in (tip, l, r)], fill=color)

    def disc(self, cx, cy, r, color, o=1, glyph=None, label=None, lsize=30, gcol=None):
        """Icon in a glowing circle that pops in."""
        if o <= 0:
            return
        k = back(o)
        rr = r * k
        col = color
        self.d.ellipse(self.P(cx - rr, cy - rr, cx + rr, cy + rr), outline=col, width=4 * S, fill=(12, 18, 40))
        self.gd.ellipse(self.P(cx - rr, cy - rr, cx + rr, cy + rr), outline=col, width=4 * S)
        if glyph and k > 0.3:
            glyph(self, cx, cy, rr * 0.5, gcol or col)
        if label:
            self.t(cx, cy + r + 50, label, lsize, WHITE, FS, "ms", o)

    def big(self, x, y, s, size, color=YELLOW, anchor="ls", o=1):
        """Big number with glow."""
        self.t(x, y, s, size, color, FBK, anchor, o, glow=True, slide=0)

    def count(self, x, y, a, b, o, size, dec=0, pre="", suf="", color=YELLOW, anchor="ls"):
        if o <= 0:
            return
        v = a + (b - a) * ease(o)
        self.big(x, y, f"{pre}{fmt(v, dec)}{suf}", size, color, anchor, min(1, o * 3))

    def done(self):
        self.t(1800, 1030, "CÓMO VA EL MUNDO", 20, DIM, FB, "rs", slide=0)
        g = self.gl.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize(self.im.size, Image.BILINEAR)
        g = ImageChops.multiply(g, Image.new("RGB", g.size, (170, 170, 170)))
        out = ImageChops.add(self.im, g)
        return out.resize((W, H), Image.LANCZOS)



def add_mark(f, cx, cy, r):
    """Channel globe mark, added with light (works for both frame classes)."""
    m = brand.compose_mark(Image.new("RGB", (W * S, H * S), (0, 0, 0)), cx * S, cy * S, r * S, S)
    if hasattr(f, "addl"):
        f.addl = m if f.addl is None else ImageChops.add(f.addl, m)
    else:
        f.im = ImageChops.add(f.im, m)
        f.d = ImageDraw.Draw(f.im)


# ------------------------------------------------------------------ glyphs
def poly(f, pts, c, w=None, fill=False):
    pp = [(x * S, y * S) for x, y in pts]
    if fill:
        f.d.polygon(pp, fill=c)
    else:
        f.d.line(pp + [pp[0]], fill=c, width=int((w or 5) * S), joint="curve")


def g_cart(f, cx, cy, r, c, w=5):
    f.d.line(f.P(cx - r * 1.1, cy - r * 0.8, cx - r * 0.7, cy - r * 0.8, cx - r * 0.4, cy + r * 0.4, cx + r * 0.9, cy + r * 0.4, cx + r * 1.1, cy - r * 0.4, cx - r * 0.55, cy - r * 0.4), fill=c, width=int(w * S), joint="curve")
    for x in (cx - r * 0.25, cx + r * 0.7):
        f.d.ellipse(f.P(x - r * 0.15, cy + r * 0.62, x + r * 0.15, cy + r * 0.92), fill=c)


def g_bolt(f, cx, cy, r, c):
    poly(f, [(cx + r * 0.2, cy - r * 1.1), (cx - r * 0.6, cy + r * 0.15), (cx - r * 0.05, cy + r * 0.15), (cx - r * 0.25, cy + r * 1.1), (cx + r * 0.6, cy - r * 0.2), (cx + r * 0.05, cy - r * 0.2)], c, fill=True)


def g_house(f, cx, cy, r, c):
    poly(f, [(cx - r, cy - r * 0.05), (cx, cy - r), (cx + r, cy - r * 0.05)], c)
    f.d.rectangle(f.P(cx - r * 0.7, cy - r * 0.05, cx + r * 0.7, cy + r * 0.9), outline=c, width=5 * S)
    f.d.rectangle(f.P(cx - r * 0.18, cy + r * 0.35, cx + r * 0.18, cy + r * 0.9), fill=c)


def g_bread(f, cx, cy, r, c):
    f.d.rounded_rectangle(f.P(cx - r, cy - r * 0.5, cx + r, cy + r * 0.6), radius=int(r * 0.5 * S), outline=c, width=5 * S)
    for k in (-0.45, 0, 0.45):
        f.d.line(f.P(cx + k * r - r * 0.15, cy - r * 0.2, cx + k * r + r * 0.15, cy + r * 0.2), fill=c, width=4 * S)


def g_car(f, cx, cy, r, c):
    f.d.rounded_rectangle(f.P(cx - r, cy - r * 0.1, cx + r, cy + r * 0.5), radius=int(r * 0.2 * S), outline=c, width=5 * S)
    f.d.line(f.P(cx - r * 0.6, cy - r * 0.1, cx - r * 0.35, cy - r * 0.55, cx + r * 0.35, cy - r * 0.55, cx + r * 0.6, cy - r * 0.1), fill=c, width=5 * S)
    for x in (cx - r * 0.55, cx + r * 0.55):
        f.d.ellipse(f.P(x - r * 0.18, cy + r * 0.4, x + r * 0.18, cy + r * 0.76), fill=c)


def g_truck(f, cx, cy, r, c):
    f.d.rectangle(f.P(cx - r, cy - r * 0.6, cx + r * 0.25, cy + r * 0.4), outline=c, width=5 * S)
    f.d.line(f.P(cx + r * 0.25, cy - r * 0.25, cx + r * 0.7, cy - r * 0.25, cx + r, cy + r * 0.1, cx + r, cy + r * 0.4, cx + r * 0.25, cy + r * 0.4), fill=c, width=5 * S)
    for x in (cx - r * 0.6, cx + r * 0.6):
        f.d.ellipse(f.P(x - r * 0.18, cy + r * 0.3, x + r * 0.18, cy + r * 0.66), fill=c)


def g_fridge(f, cx, cy, r, c):
    f.d.rounded_rectangle(f.P(cx - r * 0.6, cy - r, cx + r * 0.6, cy + r), radius=int(r * 0.12 * S), outline=c, width=5 * S)
    f.d.line(f.P(cx - r * 0.6, cy - r * 0.25, cx + r * 0.6, cy - r * 0.25), fill=c, width=5 * S)
    f.d.line(f.P(cx + r * 0.35, cy - r * 0.7, cx + r * 0.35, cy - r * 0.45), fill=c, width=5 * S)
    f.d.line(f.P(cx + r * 0.35, cy + r * 0.0, cx + r * 0.35, cy + r * 0.35), fill=c, width=5 * S)


def g_shirt(f, cx, cy, r, c):
    poly(f, [(cx - r * 0.4, cy - r), (cx - r, cy - r * 0.55), (cx - r * 0.75, cy - r * 0.1), (cx - r * 0.5, cy - r * 0.25), (cx - r * 0.5, cy + r), (cx + r * 0.5, cy + r), (cx + r * 0.5, cy - r * 0.25), (cx + r * 0.75, cy - r * 0.1), (cx + r, cy - r * 0.55), (cx + r * 0.4, cy - r)], c)


def g_pump(f, cx, cy, r, c):
    f.d.rounded_rectangle(f.P(cx - r * 0.7, cy - r, cx + r * 0.3, cy + r), radius=int(r * 0.15 * S), outline=c, width=5 * S)
    f.d.rectangle(f.P(cx - r * 0.5, cy - r * 0.75, cx + r * 0.1, cy - r * 0.3), fill=c)
    f.d.line(f.P(cx + r * 0.3, cy - r * 0.4, cx + r * 0.8, cy - r * 0.1, cx + r * 0.8, cy + r * 0.6), fill=c, width=5 * S)


def g_factory(f, cx, cy, r, c):
    poly(f, [(cx - r, cy + r * 0.8), (cx - r, cy - r * 0.2), (cx - r * 0.4, cy + r * 0.15), (cx - r * 0.4, cy - r * 0.2), (cx + r * 0.2, cy + r * 0.15), (cx + r * 0.2, cy - r), (cx + r * 0.6, cy - r), (cx + r * 0.6, cy + r * 0.8)], c)


def g_ship(f, cx, cy, r, c):
    poly(f, [(cx - r, cy + r * 0.1), (cx + r, cy + r * 0.1), (cx + r * 0.7, cy + r * 0.7), (cx - r * 0.7, cy + r * 0.7)], c)
    for x in (-0.6, -0.15, 0.3):
        f.d.rectangle(f.P(cx + x * r, cy - r * 0.45, cx + (x + 0.38) * r, cy + r * 0.1), outline=c, width=4 * S)


def g_euro(f, cx, cy, r, c):
    f.d.text((cx * S, (cy + r * 0.62) * S), "€", font=F(FX, r * 1.9), fill=c, anchor="ms")


def g_person(f, cx, cy, r, c):
    f.d.ellipse(f.P(cx - r * 0.34, cy - r * 0.95, cx + r * 0.34, cy - r * 0.27), fill=c)
    f.d.chord(f.P(cx - r * 0.75, cy - r * 0.1, cx + r * 0.75, cy + r * 1.3), 180, 360, fill=c)


def g_ticket(f, cx, cy, r, c):
    f.d.rectangle(f.P(cx - r * 0.6, cy - r, cx + r * 0.6, cy + r), outline=c, width=5 * S)
    for k in (-0.55, -0.15, 0.25):
        f.d.line(f.P(cx - r * 0.35, cy + k * r, cx + r * 0.35, cy + k * r), fill=c, width=4 * S)


def g_olive(f, cx, cy, r, c):
    f.d.rectangle(f.P(cx - r * 0.25, cy - r * 0.55, cx + r * 0.25, cy - r * 0.35), fill=c)
    f.d.rounded_rectangle(f.P(cx - r * 0.5, cy - r * 0.35, cx + r * 0.5, cy + r), radius=int(r * 0.25 * S), outline=c, width=5 * S)
    f.d.ellipse(f.P(cx - r * 0.22, cy + r * 0.15, cx + r * 0.22, cy + r * 0.6), fill=c)


def g_bank(f, cx, cy, r, c):
    poly(f, [(cx - r, cy - r * 0.35), (cx, cy - r), (cx + r, cy - r * 0.35)], c, fill=True)
    for k in (-0.65, -0.22, 0.22, 0.65):
        f.d.rectangle(f.P(cx + k * r - r * 0.1, cy - r * 0.25, cx + k * r + r * 0.1, cy + r * 0.6), fill=c)
    f.d.rectangle(f.P(cx - r, cy + r * 0.7, cx + r, cy + r * 0.9), fill=c)


def banknote(f, cx, cy, w, o=1, alpha_col=None):
    """Green 100 € note centred at cx,cy, width w."""
    if o <= 0:
        return
    h = w * 0.52
    g1 = f.c((52, 168, 104), ease(o))
    g2 = f.c((180, 240, 200), ease(o))
    f.d.rounded_rectangle(f.P(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=int(h * 0.07 * S), fill=g1)
    f.d.rounded_rectangle(f.P(cx - w / 2 + w * 0.04, cy - h / 2 + h * 0.08, cx + w / 2 - w * 0.04, cy + h / 2 - h * 0.08), radius=int(h * 0.05 * S), outline=g2, width=max(1, int(h * 0.02 * S)))
    f.d.text(((cx - w * 0.4) * S, (cy + h * 0.05) * S), "100", font=F(FBK, h * 0.42), fill=f.c((240, 255, 245), ease(o)), anchor="ls")
    f.d.text(((cx + w * 0.25) * S, (cy + h * 0.2) * S), "€", font=F(FBK, h * 0.5), fill=f.c((240, 255, 245), ease(o)), anchor="ms")
    f.d.text(((cx - w * 0.4) * S, (cy + h * 0.33) * S), "EURO", font=F(FBK, h * 0.15), fill=g2, anchor="ls")


ITEM_COLS = [(239, 68, 68), (34, 197, 94), (250, 204, 21), (59, 130, 246), (236, 72, 153), (249, 115, 22), (168, 85, 247), (20, 184, 166)]
SLOTS = [(-0.55, 0.0), (-0.15, 0.0), (0.25, 0.0), (0.62, 0.0), (-0.35, -0.42), (0.05, -0.42), (0.45, -0.42), (-0.1, -0.82)]


def cart_full(f, cx, cy, r, o_cart, items_p, n=8, color=WHITE):
    """Cart outline + items falling in. items_p = progress 0..1 of the drop."""
    if o_cart <= 0:
        return
    for i in range(n):
        pi = max(0, min(1, items_p * n * 0.6 - i * 0.45))
        if pi <= 0:
            continue
        sx, sy = SLOTS[i]
        x = cx + sx * r
        ty = cy + sy * r - r * 0.12
        y = ty - (1 - ease(pi)) * 320
        f.d.rounded_rectangle(f.P(x - r * 0.19, y - r * 0.38, x + r * 0.19, y + r * 0.02), radius=int(r * 0.05 * S), fill=ITEM_COLS[i])
    col = f.c(color, ease(o_cart))
    w = r * 0.07
    f.d.line(f.P(cx - r * 1.25, cy - r * 0.95, cx - r * 0.95, cy - r * 0.95, cx - r * 0.7, cy + r * 0.35, cx + r * 0.85, cy + r * 0.35, cx + r * 1.05, cy - r * 0.25), fill=col, width=int(w * S), joint="curve")
    f.d.line(f.P(cx - r * 0.85, cy - r * 0.25, cx + r * 1.05, cy - r * 0.25), fill=col, width=int(w * S))
    for x in (cx - r * 0.45, cx + r * 0.6):
        f.d.ellipse(f.P(x - r * 0.13, cy + r * 0.5, x + r * 0.13, cy + r * 0.76), fill=col)


def stamp(f, cx, cy, text, size, color, o):
    if o <= 0:
        return
    k = 1 + (1 - back(o)) * 0.8 if o < 1 else 1
    tw = f.tw(text, size * k, FBK)
    lay = Image.new("RGBA", (int((tw + 80) * S), int((size * k + 70) * S)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([6 * S, 6 * S, lay.size[0] - 6 * S, lay.size[1] - 6 * S], radius=18 * S, outline=color, width=8 * S)
    ld.text((lay.size[0] / 2, lay.size[1] / 2 + size * k * 0.36 * S), text, font=F(FBK, size * k), fill=color, anchor="ms")
    lay = lay.rotate(-10, resample=Image.BICUBIC, expand=True)
    a = lay.split()[3].point(lambda v: int(v * min(1, o * 2)))
    lay.putalpha(a)
    f.im.paste(lay, (int(cx * S - lay.size[0] / 2), int(cy * S - lay.size[1] / 2)), lay)


# ------------------------------------------------------------------ scenes
# Each scene: dict(kicker, title, beats=[narration...], draw=fn(f, p)) where p(i) is
# the 0..1 progress of beat i (1 once finished, 0 before it starts).
SC = []


def scene(kicker, title, beats):
    def deco(fn):
        SC.append(dict(kicker=kicker, title=title, beats=beats, draw=fn))
        return fn
    return deco


@scene("Lo que nadie te explica", None, [
    "Imagina que vas al súper con 100 euros.",
    "En 2020, con esos 100 euros llenabas el carro.",
    "Hoy, para llevarte exactamente lo mismo, necesitas unos 126.",
    "No has comprado más. Las cosas, simplemente, cuestan más.",
    "Hoy te explico por qué pasa esto, tan fácil que se lo podrías contar a tu abuela.",
])
def sc01(f, p):
    banknote(f, 480, 520, 520 * (0.6 + 0.4 * back(p(0))) if p(0) > 0 else 0, p(0))
    f.t(480, 330, "Tu dinero", 40, MUTED, FS, "ms", p(0))
    cart_full(f, 1350, 560, 210, p(1), p(1))
    if p(2) <= 0:
        f.t(1350, 265, "2020", 52, WHITE, FX, "ms", p(1))
    else:
        f.count(480, 860, 100, 126, p(2), 140, suf=" €", anchor="ms")
        f.t(1350, 265, "2026", 52, YELLOW, FX, "ms", p(2), slide=0)
    f.t(960, 990, "Mismo carro. Más dinero.", 44, WHITE, FB, "ms", p(3))
    if p(4) > 0:
        f.box(560, 120, 1360, 220, CYAN, p(4))
        f.t(960, 185, "Explicado fácil, paso a paso", 44, CYAN, FB, "ms", p(4), slide=0)


@scene("Paso 1", "¿Qué es la inflación?", [
    "Esto tiene un nombre: inflación.",
    "Inflación significa que los precios suben.",
    "Y si los precios suben, tu dinero compra menos. Es como si tu billete encogiera.",
    "Ojo: tu billete sigue poniendo 100. Lo que cambia es lo que puedes comprar con él.",
])
def sc02(f, p):
    f.header("Paso 1", "¿Qué es la inflación?", p(0))
    f.t(960, 420, "INFLACIÓN", 140, YELLOW, FBK, "ms", p(0), glow=True)
    if p(1) > 0:
        f.t(960, 520, "= los precios suben", 56, WHITE, FB, "ms", p(1))
    if p(2) > 0:
        w = 520 * (1 - 0.45 * ease(p(2)))
        banknote(f, 960, 780, w, 1)
        f.arrow(1300, 700, 1300 - 120 * ease(p(2)) - 1, 700, CYAN, 8, 30, p(2))
        f.arrow(620, 860, 620 + 120 * ease(p(2)) + 1, 860, CYAN, 8, 30, p(2))
    f.t(960, 1010, "El billete pone 100… pero compra menos", 40, CYAN, FB, "ms", p(3))


@scene("Paso 2", "¿Quién lo mide?", [
    "¿Y quién decide cuánto suben los precios? Nadie lo decide: se mide.",
    "En España lo mide el INE, la oficina de estadística.",
    "Cada mes mira los precios de una cesta enorme con las cosas que compramos todos: comida, luz, gasolina, ropa, alquiler.",
    "A esa medida se le llama IPC. Si el IPC sube un 5 %, lo que antes costaba 100 euros ahora cuesta 105.",
])
def sc03(f, p):
    f.header("Paso 2", "¿Quién lo mide?", p(0))
    f.t(120, 300, "El INE: la oficina de estadística de España", 40, MUTED, FS, o=p(1))
    items = [("Comida", g_bread), ("Luz", g_bolt), ("Gasolina", g_pump), ("Ropa", g_shirt), ("Alquiler", g_house)]
    for i, (lab, gl) in enumerate(items):
        pi = max(0, min(1, p(2) * 2.2 - i * 0.28))
        f.disc(330 + i * 315, 520, 95, lerp(CYAN, VIOLET, i / 4), pi, gl, lab)
    if p(3) > 0:
        f.box(400, 760, 1520, 960, YELLOW, p(3))
        f.t(470, 880, "IPC +5 %", 64, YELLOW, FBK, o=p(3), slide=0)
        f.t(860, 880, "100 €", 64, WHITE, FX, o=p(3), slide=0)
        f.arrow(1080, 858, 1230, 858, YELLOW, 8, 30, p(3))
        f.count(1270, 880, 100, 105, p(3), 64, suf=" €")


@scene("Paso 3", "Como una bola de nieve", [
    "Lo peligroso es que se va sumando, como una bola de nieve.",
    "Un año sube un poco, al siguiente otro poco más.",
    "Y los precios casi nunca vuelven a bajar.",
    "Por eso, entre finales de 2020 y mediados de 2026, los precios en España han subido un 26 % en total.",
])
def sc04(f, p):
    f.header("Paso 3", "Como una bola de nieve", p(0))
    if p(0) > 0:
        r = 40 + 90 * ease(p(0)) + 50 * ease(p(1))
        cx = 330 + 140 * ease(p(1))
        f.d.ellipse(f.P(cx - r, 820 - 2 * r, cx + r, 820), fill=(225, 235, 255))
        f.gd.ellipse(f.P(cx - r, 820 - 2 * r, cx + r, 820), fill=(90, 110, 140))
        f.d.line(f.P(120, 822, 1000, 822), fill=DIM, width=4 * S)
    for i in range(4):
        pi = max(0, min(1, p(1) * 2.4 - i * 0.45))
        f.bar(1000 + i * 190, 880, 1150 + i * 190, 120 + i * 110, lerp(CYAN, VIOLET, i / 3), pi)
    f.t(1380, 980, "…y no vuelve a bajar", 38, MUTED, FS, "ms", p(2))
    stamp(f, 1380, 300, "+26 %", 110, YELLOW, p(3))
    f.t(1380, 450, "dic. 2020 → jun. 2026", 32, WHITE, FS, "ms", p(3))


@scene("¿Por qué empezó? Causa 1", "La pandemia", [
    "¿Y por qué empezó todo? Vamos por partes.",
    "Primero, la pandemia. El mundo se paró: fábricas cerradas, barcos parados.",
    "Cuando todo volvió a abrir, todos quisimos comprar a la vez.",
    "Pero no había cosas para todos. Y cuando mucha gente quiere algo que escasea, el precio sube.",
    "Es como las entradas de un concierto muy famoso: si hay pocas y todos las quieren, se encarecen.",
])
def sc05(f, p):
    f.header("¿Por qué empezó? Causa 1", "La pandemia", p(0))
    f.disc(330, 520, 110, DIM, p(1), g_factory, "Fábricas paradas", gcol=MUTED)
    f.disc(650, 520, 110, DIM, p(1), g_ship, "Barcos parados", gcol=MUTED)
    for i in range(6):
        pi = max(0, min(1, p(2) * 2.5 - i * 0.25))
        f.disc(1050 + (i % 3) * 170, 430 + (i // 3) * 190, 70, CYAN, pi, g_person)
    if p(3) > 0:
        f.t(1520, 800, "Mucha gente + pocas cosas =", 40, WHITE, FB, "rs", p(3))
        f.arrow(1590, 830, 1590, 690, YELLOW, 12, 44, p(3))
        f.t(1640, 790, "Precio", 46, YELLOW, FX, o=p(3), glow=True)
    if p(4) > 0:
        f.box(340, 880, 1600, 1000, VIOLET, p(4))
        f.disc(420, 940, 40, VIOLET, p(4), g_ticket)
        f.t(490, 955, "Como las entradas de un concierto: pocas y todos las quieren", 34, WHITE, FS, o=p(4), slide=0)


@scene("Causa 2", "La energía", [
    "Segundo: la energía. En 2022 empezó la guerra de Ucrania y el gas y la luz se dispararon.",
    "Y aquí está el truco: casi todo lo que compras necesita energía.",
    "Para fabricarlo, para transportarlo en camión y para tenerlo en la nevera del súper.",
    "Si la energía sube, todo eso sube. Y al final, lo paga quien compra: tú.",
])
def sc06(f, p):
    f.header("Causa 2", "La energía", p(0))
    f.disc(330, 600, 150, YELLOW, p(0), g_bolt, "Gas y luz")
    f.t(330, 380, "2022", 40, YELLOW, FB, "ms", p(0))
    f.t(1000, 330, "Casi todo necesita energía", 44, WHITE, FB, "ms", p(1))
    tg = [(860, 470, "Fabricar", g_factory), (860, 650, "Transportar", g_truck), (860, 830, "Conservar", g_fridge)]
    for i, (x, y, lab, gl) in enumerate(tg):
        pi = max(0, min(1, p(2) * 2.2 - i * 0.4))
        f.arrow(490, 600, x - 90, y, YELLOW, 6, 26, pi)
        f.disc(x, y, 70, CYAN, pi, gl)
        f.t(x + 100, y + 14, lab, 40, WHITE, FB, o=pi)
    for i, (x, y, lab, gl) in enumerate(tg):
        f.arrow(x + 330, y, 1450, 650, VIOLET, 6, 26, p(3))
    f.disc(1580, 650, 120, VIOLET, p(3), g_person, "Tú pagas")


@scene("Causa 3", "La comida", [
    "La comida fue de lo que más subió: un 28 % entre 2021 y finales de 2024.",
    "El aceite de oliva es el ejemplo más famoso. Por la sequía, hubo menos aceitunas.",
    "Menos aceite para la misma gente que lo quiere: su precio llegó a subir un 150 %.",
])
def sc07(f, p):
    f.header("Causa 3", "La comida", p(0))
    f.bar(220, 900, 520, 440 * 28 / 150, ORANGE, p(0))
    f.count(370, 900 - 440 * 28 / 150 * ease(p(0)) - 30, 0, 28, p(0), 110, pre="+", suf=" %", anchor="ms")
    f.t(370, 960, "Alimentos 2021–2024", 32, WHITE, FS, "ms", p(0))
    f.disc(900, 560, 130, GREEN, p(1), g_olive, "Sequía: menos aceitunas")
    f.bar(1250, 900, 1550, 440, YELLOW, p(2))
    f.count(1400, 900 - 440 * ease(p(2)) - 30, 0, 150, p(2), 110, pre="+", suf=" %", anchor="ms")
    f.t(1400, 960, "Aceite de oliva (máximo)", 32, WHITE, FS, "ms", p(2))
    f.t(120, 1040, "Fuente: Eurostat, vía The Objective", 20, DIM, FM, o=p(0), slide=0)


@scene("Paso 4", "¿Y mi sueldo?", [
    "Vale, los precios suben. ¿Pero no suben también los sueldos?",
    "Sí, pero no lo suficiente. Lo importante no es cuánto dinero ganas, sino cuántas cosas puedes comprar con él.",
    "A eso se le llama salario real.",
    "Y según la OCDE, el salario real en España todavía está un 2 % por debajo de 2021.",
    "Dicho fácil: trabajas lo mismo, pero te llevas un poco menos a casa.",
])
def sc08(f, p):
    f.header("Paso 4", "¿Y mi sueldo?", p(0))
    f.wrap(120, 320, "No importa cuánto ganas, sino cuánto puedes comprar.", 44, 1100, WHITE, FB, p(1))
    f.box(120, 420, 760, 540, CYAN, p(2))
    f.t(440, 500, "SALARIO REAL", 60, CYAN, FBK, "ms", p(2), slide=0)
    f.count(440, 780, 0, -2, p(3), 200, suf=" %", color=RED, anchor="ms")
    f.t(440, 850, "frente a 2021 (OCDE)", 34, WHITE, FS, "ms", p(3))
    cart_full(f, 1400, 600, 200, p(1), p(1), 8)
    if p(3) > 0:
        # one item pops out
        e = ease(p(3))
        f.d.rounded_rectangle(f.P(1380 - 38, 450 - 76 - e * 260, 1380 + 38, 450 - e * 260), radius=10 * S, fill=f.c(ITEM_COLS[7], 1 - e))
    f.t(1400, 980, "Trabajas lo mismo, te llevas un poco menos", 40, YELLOW, FB, "ms", p(4))


@scene("2026", "La carrera que pierde tu sueldo", [
    "En 2026 ha vuelto a pasar.",
    "En la primera mitad del año, los sueldos subieron un 2,5 %…",
    "…pero los precios subieron un 3 %.",
    "Es una carrera en la que tu sueldo va siempre un poquito por detrás.",
])
def sc09(f, p):
    f.header("2026 · enero a junio", "La carrera que pierde tu sueldo", p(0))
    base, k = 900, 170
    f.bar(560, base, 860, 2.5 * k, CYAN, p(1))
    f.count(710, base - 2.5 * k * ease(p(1)) - 30, 0, 2.5, p(1), 72, dec=1, pre="+", suf=" %", color=WHITE, anchor="ms")
    f.t(710, base + 60, "Sueldos", 40, CYAN, FB, "ms", p(1))
    f.bar(1060, base, 1360, 3.0 * k, VIOLET, p(2))
    f.count(1210, base - 3.0 * k * ease(p(2)) - 30, 0, 3.0, p(2), 72, dec=1, pre="+", suf=" %", color=WHITE, anchor="ms")
    f.t(1210, base + 60, "Precios", 40, VIOLET, FB, "ms", p(2))
    f.t(1520, 520, "Tu sueldo,", 40, WHITE, FB, o=p(3))
    f.t(1520, 570, "siempre detrás", 40, YELLOW, FB, o=p(3), glow=True)
    f.t(120, 1040, "Fuente: Agencia Tributaria e INE, vía Vozpópuli", 20, DIM, FM, o=p(1), slide=0)


@scene("Paso 5", "La casa", [
    "Y luego está la casa.",
    "En julio, alquilar en España costaba de media 15,3 euros por metro cuadrado, el precio más alto de la historia.",
    "Para que te hagas una idea: un piso de 70 metros saldría por unos 1.070 euros al mes.",
    "Y es un 6,8 % más que hace solo un año.",
])
def sc10(f, p):
    f.header("Paso 5", "La casa", p(0))
    f.disc(400, 600, 190, CYAN, p(0), g_house)
    f.count(760, 520, 0, 15.3, p(1), 150, dec=1, suf=" €/m²")
    f.t(764, 590, "Alquiler medio, julio 2026 · récord", 36, WHITE, FS, o=p(1))
    f.box(760, 650, 1560, 790, VIOLET, p(2))
    f.t(800, 740, "Piso de 70 m² ≈", 44, WHITE, FB, o=p(2), slide=0)
    f.count(1170, 740, 0, 1070, p(2), 56, suf=" €/mes", color=YELLOW)
    stamp(f, 1680, 250, "+6,8 %", 70, CYAN, p(3))
    f.t(1680, 340, "en un año", 32, WHITE, FS, "ms", p(3))
    f.t(120, 1040, "Fuente: idealista. Cálculo del piso de 70 m²: ejemplo aproximado", 20, DIM, FM, o=p(1), slide=0)


@scene("¿Por qué ahora?", "Vuelve a subir", [
    "Ahora la pregunta: si lo peor ya había pasado, ¿por qué vuelve a subir?",
    "En septiembre, la inflación llegó al 4,9 %. La más alta desde principios de 2023.",
    "El culpable principal: la gasolina y la energía, que están un 21,6 % más caras que hace un año.",
    "Y no es solo eso: la comida fresca también ha subido un 5,8 %.",
])
def sc11(f, p):
    f.header("¿Por qué ahora?", "Vuelve a subir", p(0))
    f.count(120, 520, 0, 4.9, p(1), 220, dec=1, suf=" %")
    f.t(124, 590, "Inflación, septiembre 2026", 38, WHITE, FB, o=p(1))
    f.t(124, 640, "La más alta desde 2023", 34, MUTED, FS, o=p(1))
    f.disc(1080, 480, 110, YELLOW, p(2), g_pump)
    f.count(1230, 510, 0, 21.6, p(2), 100, dec=1, pre="+", suf=" %")
    f.t(1234, 560, "Gasolina y energía", 34, WHITE, FS, o=p(2))
    f.disc(1080, 780, 110, GREEN, p(3), g_bread)
    f.count(1230, 810, 0, 5.8, p(3), 100, dec=1, pre="+", suf=" %", color=GREEN)
    f.t(1234, 860, "Comida fresca", 34, WHITE, FS, o=p(3))
    f.t(120, 1040, "Fuente: INE", 20, DIM, FM, o=p(1), slide=0)


@scene("Un detalle", "El efecto escalón", [
    "Hay un detalle que casi nadie explica: el efecto escalón.",
    "La inflación compara cada mes con el mismo mes del año anterior.",
    "En septiembre del año pasado, la gasolina bajó. Este septiembre, ha subido.",
    "Así que, al compararlos, la diferencia parece todavía más grande.",
])
def sc12(f, p):
    f.header("Un detalle", "El efecto escalón", p(0))
    f.wrap(120, 320, "Se compara cada mes con el mismo mes del año anterior.", 40, 1500, MUTED, FS, p(1))
    for i, (yr, up) in enumerate([("Sept. 2025", False), ("Sept. 2026", True)]):
        cx = 560 + i * 640
        pi = max(0, min(1, p(2) * 2 - i * 0.8))
        f.box(cx - 250, 430, cx + 250, 820, DIM, pi, glow=False)
        if up:
            f.arrow(cx - 110, 740, cx + 110, 520, YELLOW, 14, 50, pi)
        else:
            f.arrow(cx - 110, 520, cx + 110, 740, CYAN, 14, 50, pi)
        f.t(cx, 880, yr, 40, WHITE, FB, "ms", pi)
        f.t(cx, 480, "Gasolina sube" if up else "Gasolina baja", 30, MUTED, FS, "ms", pi)
    if p(3) > 0:
        f.t(960, 980, "La diferencia parece aún más grande", 42, RED, FB, "ms", p(3))


@scene("¿Y ahora qué?", "Depende del petróleo", [
    "¿Y ahora qué? Depende sobre todo del petróleo.",
    "Si se calma, los precios deberían subir más despacio en los próximos meses.",
    "Si sigue subiendo, el Banco Central Europeo podría mantener o subir los tipos de interés.",
    "Y eso significa hipotecas y préstamos más caros.",
    "Nadie sabe seguro qué pasará. Son escenarios, no predicciones.",
])
def sc13(f, p):
    f.header("¿Y ahora qué?", "Depende del petróleo", p(0))
    f.disc(300, 640, 120, DIM, p(0), g_pump, "Petróleo", gcol=WHITE)
    f.arrow(430, 600, 680, 470, CYAN, 8, 30, p(1))
    f.arrow(430, 680, 680, 810, RED, 8, 30, p(2))
    f.box(720, 380, 1780, 560, CYAN, p(1))
    f.t(760, 450, "Se calma", 44, CYAN, FB, o=p(1), slide=0)
    f.t(760, 515, "Los precios suben más despacio", 36, WHITE, FS, o=p(1), slide=0)
    f.box(720, 720, 1780, 960, RED, p(2))
    f.t(760, 790, "Sigue subiendo", 44, RED, FB, o=p(2), slide=0)
    f.t(760, 850, "El BCE podría mantener o subir los tipos", 36, WHITE, FS, o=p(2), slide=0)
    f.t(760, 910, "→ hipotecas y préstamos más caros", 36, YELLOW, FB, o=p(3), slide=0)
    f.t(1250, 300, "Escenarios, no predicciones", 30, MUTED, FS, "ms", p(4))


@scene("Para ti", "Una regla muy simple", [
    "¿Qué significa todo esto para ti? Una regla muy simple:",
    "Compara siempre tu dinero con la inflación.",
    "Si te suben el sueldo un 2 % y los precios suben un 3 %, en realidad has perdido.",
    "Y si tu dinero está quieto, cada año compra un poco menos.",
])
def sc14(f, p):
    f.header("Para ti", "Una regla muy simple", p(0))
    f.t(960, 360, "Compara tu dinero con la inflación", 56, YELLOW, FX, "ms", p(1), glow=True)
    if p(2) > 0:
        tilt = 60 * ease(p(2))
        cx, cy = 960, 640
        f.d.line(f.P(cx - 420, cy - tilt / 2, cx + 420, cy + tilt / 2), fill=MUTED, width=8 * S)
        poly(f, [(cx, cy - 10), (cx - 50, cy + 190), (cx + 50, cy + 190)], MUTED, fill=True)
        f.box(cx - 620, cy - tilt / 2 - 130, cx - 240, cy - tilt / 2 - 10, CYAN, 1)
        f.t(cx - 430, cy - tilt / 2 - 55, "Sueldo +2 %", 44, CYAN, FB, "ms", 1, slide=0)
        f.box(cx + 240, cy + tilt / 2 - 130, cx + 620, cy + tilt / 2 - 10, VIOLET, 1)
        f.t(cx + 430, cy + tilt / 2 - 55, "Precios +3 %", 44, VIOLET, FB, "ms", 1, slide=0)
        f.t(960, 900, "= has perdido", 48, RED, FB, "ms", p(2))
    f.t(960, 990, "Dinero quieto = cada año compra un poco menos", 38, WHITE, FS, "ms", p(3))


@scene("Resumen", "En 20 segundos", [
    "Resumen en 20 segundos:",
    "Uno: la inflación es que los precios suben y tu dinero compra menos.",
    "Dos: desde 2020 todo ha subido un 26 %, por la pandemia, la energía y la comida.",
    "Tres: los sueldos no han seguido el ritmo.",
    "Y cuatro: ahora vuelve a subir, sobre todo por la gasolina.",
])
def sc15(f, p):
    f.header("Resumen", "En 20 segundos", p(0))
    pts = ["Precios suben = tu dinero compra menos", "Desde 2020: +26 % (pandemia, energía, comida)", "Los sueldos no han seguido el ritmo", "Ahora vuelve a subir, sobre todo por la gasolina"]
    for i, s in enumerate(pts):
        y = 360 + i * 160
        o = p(i + 1)
        f.disc(210, y, 50, lerp(CYAN, VIOLET, i / 3), o)
        f.t(210, y + 22, str(i + 1), 56, WHITE, FBK, "ms", o, slide=0)
        f.t(300, y + 18, s, 50, WHITE, FB, o=o)


@scene("Gracias por ver", None, [
    "¿Qué es lo que más has notado que ha subido? Cuéntamelo en los comentarios.",
    "Si te ha servido, suscríbete a Cómo Va el Mundo.",
    "En el próximo vídeo: por qué los jóvenes no pueden comprarse una casa.",
])
def sc16(f, p):
    if p(0) > 0:
        f.t(960, 220, "¿Qué es lo que más has notado que ha subido?", 52, WHITE, FX, "ms", p(0))
        f.t(960, 290, "Cuéntamelo en los comentarios 👇".replace(" 👇", ""), 38, MUTED, FS, "ms", p(0))
    if p(1) > 0:
        add_mark(f, 960, 520, 130 * back(p(1)))
        f.t(960, 760, "Cómo Va el Mundo", 76, WHITE, FX, "ms", p(1))
        f.d.rounded_rectangle(f.P(790, 800, 1130, 876), radius=38 * S, fill=f.c((220, 38, 38), ease(p(1))))
        f.t(960, 852, "SUSCRÍBETE", 34, WHITE, FX, "ms", p(1), slide=0)
    f.t(960, 970, "Próximo: ¿Por qué los jóvenes no pueden comprarse una casa?", 36, YELLOW, FB, "ms", p(2))


# ------------------------------------------------------------------ timeline
def beat_dur(text):
    return max(2.6, len(text.split()) / WPS + 0.7)


def timeline():
    out, t = [], 0.0
    for si, sc in enumerate(SC):
        for bi, b in enumerate(sc["beats"]):
            d = beat_dur(b)
            out.append(dict(scene=si, beat=bi, start=t, dur=d, text=b))
            t += d
    return out, t


def render_scene(si, outdir):
    sc = SC[si]
    nb = len(sc["beats"])
    os.makedirs(outdir, exist_ok=True)
    entries = []
    nanim = int(ANIM * FPS)
    for bi in range(nb):
        dur = beat_dur(sc["beats"][bi])
        for k in range(nanim + 1):
            prog = k / nanim

            def p(i, bi=bi, prog=prog):
                return 1.0 if i < bi else (prog if i == bi else 0.0)

            f = Fr()
            sc["draw"](f, p)
            img = f.done()
            name = f"s{si + 1:02d}_b{bi}_{k:02d}.jpg"
            img.save(os.path.join(outdir, name), quality=93)
            d = 1 / FPS if k < nanim else max(0.1, dur - ANIM)
            entries.append((name, d))
    with open(os.path.join(outdir, f"s{si + 1:02d}.json"), "w") as fh:
        json.dump(entries, fh)
    print("scene", si + 1, "frames", len(entries), flush=True)


if __name__ == "__main__":
    outdir = sys.argv[1]
    which = [int(x) for x in sys.argv[2:]] if len(sys.argv) > 2 else range(len(SC))
    for si in which:
        render_scene(si, outdir)

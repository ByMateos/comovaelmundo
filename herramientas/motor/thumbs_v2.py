"""Modern YouTube thumbnails (1280x720) for video 1, Cómo Va el Mundo."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import make_brand_v2 as brand

S = 2
W, H = 1280, 720
OUT = "/home/claude/canal/video1/"
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
if not os.path.exists(FBK):
    FBK = FX
YELLOW, WHITE, BLACK = (255, 214, 10), (255, 255, 255), (8, 8, 14)
RED, CYAN, VIOLET = (239, 68, 68), (34, 211, 238), (139, 92, 246)
_fc = {}


def F(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size * S))
    return _fc[k]


def P(*v):
    return [x * S for x in v]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial(c_in, c_out, cx, cy, R):
    sm = Image.new("RGB", (W // 4, H // 4))
    px = sm.load()
    for y in range(sm.height):
        for x in range(sm.width):
            d = math.hypot(x * 4 - cx, y * 4 - cy) / R
            px[x, y] = lerp(c_in, c_out, min(1, d))
    return sm.resize((W * S, H * S), Image.BICUBIC)


def shadow_text(im, xy, s, size, fill, font=FBK, anchor="ls", stroke=10, rot=0):
    """Bold text with black outline + drop shadow (current YouTube style)."""
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.text(P(x + 8, y + 10), s, font=F(font, size), fill=(0, 0, 0, 170), anchor=anchor, stroke_width=stroke * S, stroke_fill=(0, 0, 0, 170))
    layer = layer.filter(ImageFilter.GaussianBlur(6 * S))
    d = ImageDraw.Draw(layer)
    d.text(P(x, y), s, font=F(font, size), fill=fill, anchor=anchor, stroke_width=stroke * S, stroke_fill=BLACK)
    if rot:
        layer = layer.rotate(rot, resample=Image.BICUBIC, center=(x * S, y * S))
    im.paste(layer, (0, 0), layer)


def glow_paste(im, layer, radius=16):
    g = layer.convert("RGB").filter(ImageFilter.GaussianBlur(radius * S))
    return ImageChops.add(im, g)


def badge(im):
    """Small channel mark top-left: same position in every thumbnail = series look."""
    m = Image.new("RGB", im.size, (0, 0, 0))
    m = brand.compose_mark(m, 82 * S, 82 * S, 38 * S, S)
    mask = m.convert("L").point(lambda v: 255 if v > 18 else 0)
    im.paste(m, (0, 0), mask)


def save(im, name):
    im.resize((W, H), Image.LANCZOS).save(OUT + name)
    print("saved", name)


# ---------------------------------------------------------------- A: receipt
def thumb_ticket():
    im = radial((76, 29, 149), (6, 4, 18), 380, 360, 900)
    d = ImageDraw.Draw(im)
    # receipt
    rw, rh = 380, 640
    rec = Image.new("RGBA", (rw * S, rh * S), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rec)
    teeth = 16
    pts = [(0, 0)]
    for i in range(teeth + 1):
        pts.append((i * rw / teeth, rh - (14 if i % 2 else 0)))
    pts.append((rw, 0))
    rd.polygon([(x * S, y * S) for x, y in pts], fill=(250, 250, 245))
    rd.text(P(rw / 2, 64), "TICKET", font=F(FBK, 34), fill=BLACK, anchor="ms")
    rd.line(P(30, 90, rw - 30, 90), fill=(180, 180, 180), width=3 * S)
    items = ["PAN", "LECHE", "ACEITE", "LUZ", "GASOLINA", "ALQUILER"]
    for i, it in enumerate(items):
        y = 140 + i * 58
        rd.text(P(36, y), it, font=F(FB, 30), fill=(40, 40, 40), anchor="ls")
        tx, ty = rw - 52, y - 12
        rd.polygon([(tx * S, (ty - 16) * S), ((tx - 16) * S, (ty + 12) * S), ((tx + 16) * S, (ty + 12) * S)], fill=RED)
    rd.line(P(30, 500, rw - 30, 500), fill=(40, 40, 40), width=4 * S)

    rec = rec.rotate(7, resample=Image.BICUBIC, expand=True)
    sh = Image.new("RGBA", rec.size, (0, 0, 0, 0))
    sh.paste((0, 0, 0, 160), (0, 0), rec.split()[3])
    sh = sh.filter(ImageFilter.GaussianBlur(14 * S))
    ox, oy = 150 * S, 40 * S
    im.paste(sh, (ox + 18 * S, oy + 22 * S), sh)
    im.paste(rec, (ox, oy), rec)
    # red stamp
    st = Image.new("RGBA", (360 * S, 150 * S), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle(P(8, 8, 352, 142), radius=18 * S, outline=RED, width=10 * S)
    sd.text(P(180, 104), "+26 %", font=F(FBK, 84), fill=RED, anchor="ms")
    st = st.rotate(-14, resample=Image.BICUBIC, expand=True)
    im.paste(st, (200 * S, 490 * S), st)
    # text
    shadow_text(im, (1230, 300), "TODO", 170, WHITE, anchor="rs")
    shadow_text(im, (1230, 500), "SUBE", 200, YELLOW, anchor="rs")
    shadow_text(im, (1230, 620), "¿POR QUÉ?", 72, WHITE, anchor="rs", stroke=8)
    badge(im)
    save(im, "miniatura_v2_A_ticket.png")


# ---------------------------------------------------------------- B: banknote
def banknote(w, h, alpha=255):
    b = Image.new("RGBA", (int(w * S), int(h * S)), (0, 0, 0, 0))
    d = ImageDraw.Draw(b)
    g1, g2 = (52, 168, 104), (20, 110, 70)
    mask = Image.new("L", b.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, b.size[0] - 1, b.size[1] - 1], radius=int(h * 0.06 * S), fill=alpha)
    grad = Image.new("RGBA", b.size)
    gd = ImageDraw.Draw(grad)
    for x in range(b.size[0]):
        gd.line([x, 0, x, b.size[1]], fill=lerp(g1, g2, x / b.size[0]) + (255,))
    b.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(b)
    d.rounded_rectangle([int(w * 0.04 * S), int(h * 0.08 * S), int(w * 0.96 * S), int(h * 0.92 * S)], radius=int(h * 0.05 * S), outline=(190, 240, 205, alpha), width=max(2, int(h * 0.015 * S)))
    for k in range(5):
        r = h * (0.18 + k * 0.06)
        cx, cy = w * 0.68, h * 0.5
        d.ellipse([int((cx - r) * S), int((cy - r) * S), int((cx + r) * S), int((cy + r) * S)], outline=(150, 220, 175, alpha), width=max(1, int(h * 0.008 * S)))
    d.text((int(w * 0.08 * S), int(h * 0.42 * S)), "100", font=F(FBK, h * 0.34), fill=(240, 255, 245, alpha), anchor="ls")
    d.text((int(w * 0.08 * S), int(h * 0.78 * S)), "EURO", font=F(FBK, h * 0.16), fill=(210, 245, 220, alpha), anchor="ls")
    d.text((int(w * 0.68 * S), int(h * 0.62 * S)), "€", font=F(FBK, h * 0.42), fill=(240, 255, 245, alpha), anchor="ms")
    return b


def thumb_billete():
    im = radial((14, 72, 96), (4, 8, 18), 400, 380, 900)
    sizes = [(520, 270, 70), (400, 208, 140), (300, 156, 255)]
    xs = [40, 360, 640]
    for (w, h, a), x in zip(sizes, xs):
        b = banknote(w, h)
        if a < 255:
            alpha = b.split()[3].point(lambda v: v * a // 255)
            b.putalpha(alpha)
        b = b.rotate(-6, resample=Image.BICUBIC, expand=True)
        y = 470 - h / 2
        im.paste(b, (int(x * S), int(y * S)), b)
    # motion arrows (shrinking)
    d = ImageDraw.Draw(im)
    shadow_text(im, (640, 150), "TU SUELDO", 120, WHITE, anchor="ms")
    shadow_text(im, (1240, 690), "VALE MENOS", 132, YELLOW, anchor="rs")
    badge(im)
    save(im, "miniatura_v2_B_billete.png")


# ---------------------------------------------------------------- C: split
def cart(d, cx, cy, r, color, n_items):
    # items inside
    cols = [(239, 68, 68), (34, 197, 94), (250, 204, 21), (59, 130, 246), (236, 72, 153), (249, 115, 22), (168, 85, 247), (20, 184, 166)]
    slots = [(-0.55, 0.0), (-0.15, 0.0), (0.25, 0.0), (0.62, 0.0), (-0.35, -0.42), (0.05, -0.42), (0.45, -0.42), (-0.1, -0.82)]
    for i in range(n_items):
        sx, sy = slots[i]
        x, y = cx + sx * r, cy + sy * r - r * 0.12
        d.rounded_rectangle(P(x - r * 0.19, y - r * 0.38, x + r * 0.19, y + r * 0.02), radius=int(r * 0.05 * S), fill=cols[i])
    w = int(r * 0.09)
    d.line(P(cx - r * 1.25, cy - r * 0.95, cx - r * 0.95, cy - r * 0.95, cx - r * 0.7, cy + r * 0.35, cx + r * 0.85, cy + r * 0.35, cx + r * 1.05, cy - r * 0.25), fill=color, width=w * S, joint="curve")
    d.line(P(cx - r * 0.85, cy - r * 0.25, cx + r * 1.05, cy - r * 0.25), fill=color, width=w * S)
    for x in (cx - r * 0.45, cx + r * 0.6):
        d.ellipse(P(x - r * 0.14, cy + r * 0.5, x + r * 0.14, cy + r * 0.78), fill=color)


def thumb_split():
    left = radial((22, 78, 120), (6, 14, 30), 300, 420, 700)
    right = radial((130, 24, 36), (24, 4, 10), 980, 420, 700)
    im = left.copy()
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).polygon(P(690, 0, 1280, 0, 1280, 720, 590, 720), fill=255)
    im.paste(right, (0, 0), mask)
    d = ImageDraw.Draw(im)
    d.line(P(690, 0, 590, 720), fill=YELLOW, width=12 * S)
    cart(d, 300, 420, 165, WHITE, 8)
    cart(d, 990, 420, 165, WHITE, 3)
    shadow_text(im, (300, 140), "2020", 110, WHITE, anchor="ms")
    shadow_text(im, (990, 140), "2026", 110, YELLOW, anchor="ms")
    shadow_text(im, (640, 700), "MISMO DINERO", 92, WHITE, anchor="ms", stroke=9)
    badge(im)
    save(im, "miniatura_v2_C_antes_despues.png")


thumb_ticket()
thumb_billete()
thumb_split()

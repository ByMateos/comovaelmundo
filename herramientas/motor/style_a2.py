"""Style A v2: refined, modern big-caption Short design. Builds still frames (hook, data, CTA)."""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import make_brand_v2 as brand

W, H = 1080, 1920
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
for p in (FXB, FM):
    if not os.path.exists(p):
        pass
_f = {}


def F(p, s):
    if not os.path.exists(p):
        p = FB
    if (p, s) not in _f:
        _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]


INK = (7, 9, 18)
WHITE = (246, 247, 251)
SOFT = (168, 176, 200)
DIM = (92, 100, 128)
YEL = (255, 210, 63)
AMB = (255, 158, 44)
CYAN = (56, 225, 255)
VIO = (132, 94, 255)
OUT = "/home/claude/canal/short/disenos"
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(3)


def mesh_bg(seed=0, accent=(VIO, CYAN)):
    """Dark mesh gradient with two soft colour blobs and fine grain."""
    im = Image.new("RGB", (W, H), INK)
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    a, b = accent
    d.ellipse([-260, 180, 700, 1140], fill=tuple(int(c * 0.42) for c in a))
    d.ellipse([520, 1000, 1380, 1860], fill=tuple(int(c * 0.30) for c in b))
    layer = layer.filter(ImageFilter.GaussianBlur(220))
    im = ImageChops.add(im, layer)
    # vignette
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.55 * (((xx - W / 2) / (W * 0.8)) ** 2 + ((yy - H / 2) / (H * 0.75)) ** 2)
    arr = np.asarray(im).astype(np.float32) * np.clip(v, 0.35, 1)[..., None]
    # grain
    arr += rng.normal(0, 3.2, arr.shape[:2])[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def gradient_text(im, xy, txt, font, c1, c2, anchor="mm", glow=0.55):
    """Vertical gradient fill text with a soft colour glow."""
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).text(xy, txt, font=font, fill=255, anchor=anchor)
    bbox = mask.getbbox()
    if not bbox:
        return im
    x0, y0, x1, y1 = bbox
    g = Image.new("RGB", im.size, c1)
    gd = ImageDraw.Draw(g)
    for y in range(y0, y1 + 1):
        t = (y - y0) / max(1, y1 - y0)
        gd.line([(x0, y), (x1, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    if glow:
        gl = Image.new("RGB", im.size, (0, 0, 0))
        gl.paste(Image.new("RGB", im.size, c2), mask=mask)
        gl = gl.filter(ImageFilter.GaussianBlur(40))
        gl = Image.eval(gl, lambda v: int(v * glow))
        im = ImageChops.add(im, gl)
    im.paste(g, mask=mask)
    return im


def glass(im, box, radius=44, tint=(255, 255, 255), alpha=0.06, border=0.14):
    x0, y0, x1, y1 = [int(v) for v in box]
    region = im.crop((x0, y0, x1, y1)).filter(ImageFilter.GaussianBlur(30))
    over = Image.new("RGB", region.size, tint)
    region = Image.blend(region, over, alpha)
    m = Image.new("L", region.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, region.width - 1, region.height - 1], radius=radius, fill=255)
    im.paste(region, (x0, y0), m)
    d = ImageDraw.Draw(im)
    bc = tuple(int(255 * border + c * (1 - border)) for c in (20, 24, 40))
    d.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=bc, width=2)
    return im


def logo_mark(r):
    """Logo on a generous canvas with a soft radial edge, so glows never hit a hard border."""
    ss = 2
    size = int(r * 4.0 * ss)
    big = Image.new("RGB", (size, size), (0, 0, 0))
    m = brand.compose_mark(big, size / 2, size / 2, r * ss, ss)
    m = m.resize((size // ss, size // ss), Image.LANCZOS)
    a = m.convert("L").point(lambda v: min(255, v * 3))
    n = m.width
    yy, xx = np.mgrid[0:n, 0:n]
    rr = np.sqrt((xx - n / 2) ** 2 + (yy - n / 2) ** 2) / (n / 2)
    fade = np.clip((1.0 - rr) / 0.25, 0, 1)
    a = Image.fromarray((np.asarray(a).astype(np.float32) * fade).astype(np.uint8))
    return m, a


def paste_logo(im, cx, cy, r):
    m, a = logo_mark(r)
    im.paste(m, (int(cx - m.width / 2), int(cy - m.height / 2)), a)
    return im


def tracked(d, xy, txt, font, fill, track=6, anchor="mm"):
    total = sum(d.textlength(ch, font=font) for ch in txt) + track * (len(txt) - 1)
    x, y = xy
    if anchor[0] == "m":
        x -= total / 2
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill, anchor="l" + anchor[1])
        x += d.textlength(ch, font=font) + track


def chrome(im, progress, seg=6, tag="EXPLICADO FÁCIL", topic="Economía"):
    d = ImageDraw.Draw(im)
    # segmented progress, stories style
    gap, x0, x1, y = 10, 64, W - 64, 74
    sw = (x1 - x0 - gap * (seg - 1)) / seg
    for i in range(seg):
        sx = x0 + i * (sw + gap)
        d.rounded_rectangle([sx, y, sx + sw, y + 7], radius=4, fill=(52, 58, 84))
        fill = min(1, max(0, progress * seg - i))
        if fill > 0:
            d.rounded_rectangle([sx, y, sx + sw * fill, y + 7], radius=4, fill=WHITE)
    # header: logo + channel + series pill
    im = paste_logo(im, 104, 160, 30)
    d = ImageDraw.Draw(im)
    d.text((152, 146), "Cómo Va el Mundo", font=F(FB, 32), fill=WHITE, anchor="lm")
    d.text((152, 182), topic, font=F(FM, 26), fill=SOFT, anchor="lm")
    tw = d.textlength(tag, font=F(FB, 24)) + 6 * len(tag) + 44
    d.rounded_rectangle([W - 64 - tw, 136, W - 64, 186], radius=25, outline=(90, 98, 130), width=2)
    tracked(d, (W - 64 - tw / 2, 161), tag, F(FB, 24), WHITE, track=4)
    return im


def kicker(d, y, txt, col=CYAN):
    f = F(FB, 30)
    tracked(d, (W / 2, y), txt, f, col, track=8)


def frame_hook():
    im = mesh_bg()
    im = chrome(im, 0.12)
    d = ImageDraw.Draw(im)
    kicker(d, 640, "EL EURÍBOR NO PARA", CYAN)
    d.text((W / 2, 780), "Tu hipoteca", font=F(FXB, 112), fill=WHITE, anchor="mm")
    # current word: gradient pill behind, refined (not a flat box)
    word = "sube"
    fw = F(FBK, 168)
    tw = d.textlength(word, font=fw)
    pill = Image.new("RGB", (W, H), (0, 0, 0))
    pd = ImageDraw.Draw(pill)
    pd.rounded_rectangle([W / 2 - tw / 2 - 40, 852, W / 2 + tw / 2 + 40, 1046], radius=36, fill=(255, 196, 48))
    pill_soft = pill.filter(ImageFilter.GaussianBlur(50))
    im = ImageChops.add(im, Image.eval(pill_soft, lambda v: int(v * 0.35)))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle([W / 2 - tw / 2 - 40, 852, W / 2 + tw / 2 + 40, 1046], radius=36, fill=255)
    g = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(g)
    for x in range(W):
        t = x / W
        gd.line([(x, 0), (x, H)], fill=tuple(int(YEL[i] * (1 - t) + AMB[i] * t) for i in range(3)))
    im.paste(g, mask=m)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 946), word, font=fw, fill=INK, anchor="mm")
    d.text((W / 2, 1130), "y esto es lo que pagas de más", font=F(FS, 46), fill=SOFT, anchor="mm")
    # swipe-up / continue hint
    d.text((W / 2, 1520), "Datos del BCE · 29 oct 2026", font=F(FM, 28), fill=DIM, anchor="mm")
    return im


def frame_data():
    im = mesh_bg(accent=(AMB, VIO))
    im = chrome(im, 0.55)
    d = ImageDraw.Draw(im)
    kicker(d, 520, "TU HIPOTECA", YEL)
    im = gradient_text(im, (W / 2, 760), "+85 €", F(FBK, 270), (255, 226, 110), AMB, glow=0.45)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 930), "al mes", font=F(FXB, 92), fill=WHITE, anchor="mm")
    # glass comparison card
    im = glass(im, (110, 1060, W - 110, 1420))
    d = ImageDraw.Draw(im)
    rows = [("Hace un año", 650, "2,19 %", (88, 96, 126)), ("Ahora", 735, "3,23 %", YEL)]
    for i, (lab, v, eur, col) in enumerate(rows):
        y = 1150 + i * 130
        d.text((160, y), lab, font=F(FS, 34), fill=SOFT, anchor="lm")
        d.text((160, y + 44), f"Euríbor {eur}", font=F(FM, 26), fill=DIM, anchor="lm")
        bx0, bx1 = 470, W - 270
        bw = (bx1 - bx0) * (v - 500) / 300
        d.rounded_rectangle([bx0, y - 4, bx1, y + 26], radius=15, fill=(36, 40, 62))
        d.rounded_rectangle([bx0, y - 4, bx0 + bw, y + 26], radius=15, fill=col)
        d.text((W - 160, y + 11), f"{v} €", font=F(FXB, 40), fill=WHITE, anchor="rm")
    d.text((W / 2, 1490), "150.000 € a 25 años · euríbor + 1 %", font=F(FM, 30), fill=DIM, anchor="mm")
    return im


def frame_cta():
    im = mesh_bg(accent=(CYAN, VIO))
    im = chrome(im, 1.0)
    im = paste_logo(im, W / 2, 760, 150)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1010), "Una noticia al día,", font=F(FXB, 70), fill=WHITE, anchor="mm")
    d.text((W / 2, 1094), "explicada fácil", font=F(FXB, 70), fill=WHITE, anchor="mm")
    # subscribe button: soft red glow + clean pill
    bw, by = 440, 1220
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle([W / 2 - bw / 2, by, W / 2 + bw / 2, by + 104], radius=52, fill=(255, 40, 70))
    im = ImageChops.add(im, Image.eval(glow.filter(ImageFilter.GaussianBlur(45)), lambda v: int(v * 0.5)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([W / 2 - bw / 2, by, W / 2 + bw / 2, by + 104], radius=52, fill=(240, 36, 64))
    tracked(d, (W / 2, by + 52), "SUSCRÍBETE", F(FBK, 40), WHITE, track=5)
    d.text((W / 2, 1400), "Información, no asesoramiento financiero", font=F(FM, 28), fill=DIM, anchor="mm")
    return im


if __name__ == "__main__":
    frames = [frame_hook(), frame_data(), frame_cta()]
    for i, f in enumerate(frames):
        f.save(f"{OUT}/estiloA2_{i + 1}.png")
    sheet = Image.new("RGB", (3 * 540 + 4 * 40, 960 + 140), (16, 18, 26))
    ds = ImageDraw.Draw(sheet)
    for i, f in enumerate(frames):
        x = 40 + i * 580
        sheet.paste(f.resize((540, 960), Image.LANCZOS), (x, 110))
        ds.text((x + 270, 56), ["1 · Gancho", "2 · Dato", "3 · Cierre"][i], font=F(FXB, 38), fill=WHITE, anchor="mm")
    sheet.save(f"{OUT}/estiloA2_comparativa.png")
    print("ok")

"""Three Short design styles, same content, as still frames for the user to choose."""
import sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import make_brand_v2 as brand

W, H = 1080, 1920
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
_f = {}


def F(p, s):
    if (p, s) not in _f:
        _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]


YEL, CYAN, VIO, WHITE, MUTED, RED = (255, 214, 10), (34, 211, 238), (139, 92, 246), (245, 247, 252), (150, 160, 185), (230, 57, 70)
OUT = "/home/claude/canal/short/disenos"
os.makedirs(OUT, exist_ok=True)


def grad(top, bot):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - t) + bot[i] * t) for i in range(3)))
    return im


def glow(im, draw_fn, radius=28, strength=1.0):
    layer = Image.new("RGB", im.size, (0, 0, 0))
    draw_fn(ImageDraw.Draw(layer))
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    if strength != 1.0:
        g = Image.eval(g, lambda v: int(min(255, v * strength)))
    im = ImageChops.add(im, g)
    draw_fn(ImageDraw.Draw(im))
    return im


def logo(im, cx, cy, r):
    ss = 2
    big = Image.new("RGB", (int(r * 2.6 * ss), int(r * 2.6 * ss)), (0, 0, 0))
    m = brand.compose_mark(big, big.width / 2, big.height / 2, r * ss, ss)
    m = m.resize((big.width // ss, big.height // ss), Image.LANCZOS)
    box = (int(cx - m.width / 2), int(cy - m.height / 2))
    region = im.crop((box[0], box[1], box[0] + m.width, box[1] + m.height))
    im.paste(ImageChops.add(region, m), box)
    return im


def ctext(d, y, txt, font, fill, anchor="mm"):
    d.text((W / 2, y), txt, font=font, fill=fill, anchor=anchor)


# ---------- A: big animated captions ----------
def style_a():
    im = grad((14, 18, 40), (6, 8, 18))
    d = ImageDraw.Draw(im)
    # soft radial accent
    acc = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(acc).ellipse([140, 520, 940, 1320], fill=(60, 40, 120))
    im = ImageChops.add(im, acc.filter(ImageFilter.GaussianBlur(180)))
    d = ImageDraw.Draw(im)
    # progress bar
    d.rounded_rectangle([60, 70, W - 60, 82], radius=6, fill=(40, 46, 72))
    d.rounded_rectangle([60, 70, 60 + (W - 120) * 0.42, 82], radius=6, fill=YEL)
    # series tag
    ctext(d, 150, "EXPLICADO FÁCIL", F(FBK, 34), CYAN)
    # captions, karaoke style: current word highlighted with a box
    ctext(d, 720, "TU HIPOTECA", F(FBK, 104), WHITE)
    word = "SUBE"
    fw = F(FBK, 150)
    tw = d.textlength(word, font=fw)
    d.rounded_rectangle([W / 2 - tw / 2 - 34, 790, W / 2 + tw / 2 + 34, 960], radius=28, fill=YEL)
    ctext(d, 875, word, fw, (12, 14, 26))
    im = glow(im, lambda dd: dd.text((W / 2, 1110), "+85 €", font=F(FBK, 230), fill=YEL, anchor="mm"), 36, 0.8)
    d = ImageDraw.Draw(im)
    ctext(d, 1250, "AL MES", F(FBK, 90), WHITE)
    ctext(d, 1360, "Hipoteca de 150.000 € a 25 años", F(FS, 40), MUTED)
    # subscribe nudge
    d.rounded_rectangle([W / 2 - 220, 1620, W / 2 + 220, 1712], radius=46, fill=RED)
    ctext(d, 1666, "SUSCRÍBETE", F(FBK, 44), WHITE)
    im = logo(im, W / 2, 1810, 46)
    return im


# ---------- B: modern TV news ----------
def style_b():
    im = grad((10, 14, 28), (8, 10, 20))
    d = ImageDraw.Draw(im)
    # top strip
    d.rectangle([0, 0, W, 150], fill=(16, 22, 44))
    d.rectangle([0, 150, W, 156], fill=CYAN)
    im = logo(im, 110, 76, 40)
    d = ImageDraw.Draw(im)
    d.text((180, 52), "CÓMO VA EL MUNDO", font=F(FBK, 40), fill=WHITE)
    d.text((180, 100), "Economía · 29 de octubre", font=F(FS, 28), fill=MUTED)
    d.rounded_rectangle([W - 210, 52, W - 50, 100], radius=8, fill=RED)
    d.text((W - 130, 76), "● EN DIRECTO", font=F(FBK, 22), fill=WHITE, anchor="mm")
    # chart panel
    x0, y0, x1, y1 = 80, 300, W - 80, 1060
    d.rounded_rectangle([x0, y0, x1, y1], radius=28, fill=(18, 24, 46), outline=(44, 56, 92), width=3)
    d.text((x0 + 50, y0 + 50), "Euríbor a 12 meses", font=F(FB, 40), fill=WHITE)
    d.text((x0 + 50, y0 + 104), "Media mensual, %", font=F(FS, 28), fill=MUTED)
    pts = [2.19, 2.25, 2.31, 2.45, 2.52, 2.6, 2.71, 2.83, 2.95, 3.04, 3.12, 3.18, 3.23]
    gx0, gx1, gy0, gy1 = x0 + 60, x1 - 60, y0 + 200, y1 - 120
    for k in range(5):
        yy = gy1 - (gy1 - gy0) * k / 4
        d.line([gx0, yy, gx1, yy], fill=(36, 46, 78), width=2)
    xy = [(gx0 + (gx1 - gx0) * i / (len(pts) - 1), gy1 - (p - 2.0) / 1.4 * (gy1 - gy0)) for i, p in enumerate(pts)]
    poly = xy + [(gx1, gy1), (gx0, gy1)]
    fill = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(fill).polygon(poly, fill=(20, 80, 100))
    im = ImageChops.add(im, fill)
    im = glow(im, lambda dd: dd.line(xy, fill=CYAN, width=10, joint="curve"), 18, 0.9)
    d = ImageDraw.Draw(im)
    lx, ly = xy[-1]
    d.ellipse([lx - 16, ly - 16, lx + 16, ly + 16], fill=YEL)
    d.text((lx - 20, ly - 40), "3,23 %", font=F(FBK, 56), fill=YEL, anchor="rs")
    d.text((gx0, gy1 + 50), "oct 2025", font=F(FS, 28), fill=MUTED, anchor="lm")
    d.text((gx1, gy1 + 50), "oct 2026", font=F(FS, 28), fill=MUTED, anchor="rm")
    # lower third
    d.rectangle([0, 1200, W, 1460], fill=(250, 250, 252))
    d.rectangle([0, 1200, 26, 1460], fill=YEL)
    d.rectangle([60, 1230, 340, 1286], fill=(12, 16, 32))
    d.text((200, 1258), "TU HIPOTECA", font=F(FBK, 30), fill=YEL, anchor="mm")
    d.text((60, 1340), "Pagas unos 85 € más al mes", font=F(FBK, 58), fill=(12, 16, 32), anchor="lm")
    d.text((60, 1410), "Hipoteca de 150.000 € a 25 años con euríbor + 1 %", font=F(FS, 32), fill=(70, 80, 100), anchor="lm")
    # ticker
    d.rectangle([0, 1560, W, 1640], fill=(16, 22, 44))
    d.rectangle([0, 1560, 210, 1640], fill=RED)
    d.text((105, 1600), "AHORA", font=F(FBK, 34), fill=WHITE, anchor="mm")
    d.text((240, 1600), "BCE mantiene tipos al 2,50 %  ·  Lagarde dejará el BCE en febrero  ·  Fed", font=F(FB, 32), fill=WHITE, anchor="lm")
    ctext(d, 1760, "Suscríbete para más noticias explicadas fácil", F(FS, 32), MUTED)
    return im


# ---------- C: minimal data ----------
def style_c():
    im = Image.new("RGB", (W, H), (8, 9, 14))
    d = ImageDraw.Draw(im)
    d.text((80, 120), "01 / 05", font=F(FS, 32), fill=MUTED)
    d.text((W - 80, 120), "CÓMO VA EL MUNDO", font=F(FB, 30), fill=MUTED, anchor="ra")
    d.line([80, 190, W - 80, 190], fill=(36, 40, 56), width=2)
    d.text((80, 520), "Lo que pagas de más", font=F(FB, 56), fill=WHITE)
    d.text((80, 600), "al mes por tu hipoteca", font=F(FB, 56), fill=MUTED)
    im = glow(im, lambda dd: dd.text((60, 1010), "+85€", font=F(FBK, 330), fill=YEL, anchor="lm"), 40, 0.5)
    d = ImageDraw.Draw(im)
    # mini comparison bars
    for i, (lab, v, col) in enumerate([("Hace un año", 650, (70, 76, 96)), ("Hoy", 735, YEL)]):
        y = 1290 + i * 120
        d.text((80, y), lab, font=F(FS, 34), fill=MUTED, anchor="lm")
        bw = (W - 480) * v / 800
        d.rounded_rectangle([360, y - 22, 360 + bw, y + 22], radius=22, fill=col)
        d.text((380 + bw, y), f"{v} €", font=F(FBK, 36), fill=WHITE, anchor="lm")
    d.text((80, 1560), "150.000 € a 25 años · euríbor + 1 %", font=F(FS, 30), fill=MUTED)
    d.text((80, 1606), "Euríbor: 2,19 % → 3,23 %", font=F(FS, 30), fill=MUTED)
    d.line([80, 1700, W - 80, 1700], fill=(36, 40, 56), width=2)
    d.text((80, 1770), "Síguenos · una noticia al día", font=F(FB, 32), fill=WHITE, anchor="lm")
    im = logo(im, W - 130, 1770, 44)
    return im


ims = {"A_subtitulos": style_a(), "B_telediario": style_b(), "C_minimalista": style_c()}
for k, im in ims.items():
    im.save(f"{OUT}/estilo_{k}.png")
# comparison sheet
sheet = Image.new("RGB", (3 * 540 + 4 * 40, 960 + 160), (20, 22, 30))
ds = ImageDraw.Draw(sheet)
for i, (k, im) in enumerate(ims.items()):
    x = 40 + i * (540 + 40)
    sheet.paste(im.resize((540, 960), Image.LANCZOS), (x, 120))
    ds.text((x + 270, 60), ["A · Subtítulos grandes", "B · Telediario moderno", "C · Minimalista"][i], font=F(FBK, 40), fill=WHITE, anchor="mm")
sheet.save(f"{OUT}/comparativa_estilos.png")
print("ok")

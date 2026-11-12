"""Vertical Short thumbnails (1080x1920) in the channel's A2 style."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import style_a2 as S

W, H = 1080, 1920
F, FBK, FXB, FB, FS, FM = S.F, S.FBK, S.FXB, S.FB, S.FS, S.FM
INK, WHITE, SOFT, DIM, YEL, AMB, CYAN, VIO = S.INK, S.WHITE, S.SOFT, S.DIM, S.YEL, S.AMB, S.CYAN, S.VIO
RED = (240, 54, 78)
OUT = "/home/claude/canal/short/miniaturas"
os.makedirs(OUT, exist_ok=True)


def fit_font(d, txt, path, maxw, start):
    s = start
    while s > 40 and d.textlength(txt, font=F(path, s)) > maxw:
        s -= 4
    return F(path, s)


def pill(im, cy, txt, c1=YEL, c2=AMB, ink=INK, maxw=940, start=190):
    d = ImageDraw.Draw(im)
    f = fit_font(d, txt, FBK, maxw - 90, start)
    tw = d.textlength(txt, font=f)
    asc, desc = f.getmetrics()
    h = asc * 0.95 + 56
    box = [W / 2 - tw / 2 - 46, cy - h / 2, W / 2 + tw / 2 + 46, cy + h / 2]
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(box, radius=44, fill=c1)
    im = ImageChops.add(im, Image.eval(glow.filter(ImageFilter.GaussianBlur(70)), lambda v: int(v * 0.4)))
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, radius=44, fill=255)
    g = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(g)
    for x in range(W):
        t = x / W
        gd.line([(x, 0), (x, H)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    im.paste(g, mask=m)
    ImageDraw.Draw(im).text((W / 2, cy + 6), txt, font=f, fill=ink, anchor="mm")
    return im


def headline(im, cy, txt, size=150, col=WHITE):
    d = ImageDraw.Draw(im)
    f = fit_font(d, txt, FXB, 960, size)
    # soft shadow for legibility on any feed
    sh = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(sh).text((W / 2, cy + 8), txt, font=f, fill=(0, 0, 0), anchor="mm")
    d.text((W / 2, cy), txt, font=f, fill=col, anchor="mm")
    return im


def kicker(im, cy, txt, col=CYAN):
    d = ImageDraw.Draw(im)
    f = F(FB, 40)
    tw = sum(d.textlength(c, font=f) for c in txt) + 8 * (len(txt) - 1)
    box = [W / 2 - tw / 2 - 34, cy - 36, W / 2 + tw / 2 + 34, cy + 36]
    d.rounded_rectangle(box, radius=36, outline=col, width=3)
    S.tracked(d, (W / 2, cy), txt, f, col, track=8)
    return im


def brand(im):
    im = S.paste_logo(im, W / 2, 1560, 70)
    d = ImageDraw.Draw(im)
    S.tracked(d, (W / 2, 1700), "CÓMO VA EL MUNDO", F(FXB, 40), WHITE, track=6)
    return im


def chips(im, cy, items):
    d = ImageDraw.Draw(im)
    f = F(FB, 38)
    ws = [d.textlength(t, font=f) + 56 for t in items]
    gap = 18
    total = sum(ws) + gap * (len(ws) - 1)
    x = W / 2 - total / 2
    for t, w in zip(items, ws):
        d.rounded_rectangle([x, cy - 34, x + w, cy + 34], radius=34, fill=(26, 30, 52), outline=(120, 130, 170), width=2)
        d.text((x + w / 2, cy), t, font=f, fill=WHITE, anchor="mm")
        x += w + gap
    return im


def ribbon(im, cx, cy, s=1.0, col=(235, 236, 242)):
    """Awareness ribbon: one smooth stroke with a loop on top and two crossed tails."""
    ctrl = [(-95, 165), (-40, 60), (0, -10), (40, -95), (38, -170), (0, -205), (-38, -170), (-40, -95), (0, -10), (40, 60), (95, 165)]
    pts = []
    P = [ctrl[0]] + ctrl + [ctrl[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for k in range(12):
            t = k / 12
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            pts.append((cx + x * s, cy + y * s))
    pts.append((cx + ctrl[-1][0] * s, cy + ctrl[-1][1] * s))
    ss = 3
    big = Image.new("L", (W * ss, H * ss), 0)
    bd = ImageDraw.Draw(big)
    w = int(38 * s * ss)
    sp = [(x * ss, y * ss) for x, y in pts]
    bd.line(sp, fill=255, width=w, joint="curve")
    for x, y in sp[::3]:
        bd.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=255)
    m = big.resize((W, H), Image.LANCZOS)
    # cut both tail ends diagonally like a real ribbon
    md = ImageDraw.Draw(m)
    for sx in (-1, 1):
        ex, ey = cx + sx * 95 * s, cy + 165 * s
        md.polygon([(ex - 40 * s, ey + 2 * s), (ex + 40 * s, ey + 2 * s), (ex, ey - 26 * s)], fill=0)
        md.rectangle([ex - 60 * s, ey + 2 * s, ex + 60 * s, ey + 80 * s], fill=0)
    im.paste(Image.new("RGB", (W, H), col), mask=m)
    return im


def bg(accent):
    return S.mesh_bg(accent=accent)


def t_mundo():
    im = bg((VIO, CYAN))
    im = kicker(im, 470, "EL MUNDO EN 60 SEGUNDOS")
    im = headline(im, 680, "Hackeo récord")
    im = pill(im, 880, "en cripto")
    im = chips(im, 1110, ["Israel", "Lula", "BCE", "Petróleo"])
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1230), "Resumen del 30 de octubre", font=F(FS, 42), fill=SOFT, anchor="mm")
    return brand(im)


def t_binance():
    im = bg((AMB, VIO))
    im = kicker(im, 430, "CRIPTO · ÚLTIMA HORA", YEL)
    im = headline(im, 630, "Binance", 200)
    im = pill(im, 850, "¿hackeo?")
    im = S.gradient_text(im, (W / 2, 1110), "6.300 M$", F(FBK, 200), (255, 228, 115), AMB, glow=0.45)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1260), "robados, según Binance", font=F(FS, 46), fill=SOFT, anchor="mm")
    return brand(im)


def t_bce():
    im = bg((VIO, CYAN))
    im = kicker(im, 430, "BCE · 29 DE OCTUBRE")
    im = headline(im, 640, "Lagarde", 200)
    im = pill(im, 860, "se va")
    im = S.gradient_text(im, (W / 2, 1110), "2,50 %", F(FBK, 200), (255, 228, 115), AMB, glow=0.45)
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1260), "Los tipos no se mueven. ¿Y tu hipoteca?", font=F(FS, 44), fill=SOFT, anchor="mm")
    return brand(im)


def t_fed():
    im = bg((CYAN, VIO))
    im = kicker(im, 430, "FED Y BCE")
    im = headline(im, 640, "Tu hipoteca", 170)
    im = pill(im, 860, "en juego")
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1070), "Dos bancos centrales,", font=F(FXB, 70), fill=WHITE, anchor="mm")
    d.text((W / 2, 1160), "dos días clave", font=F(FXB, 70), fill=WHITE, anchor="mm")
    return brand(im)


def t_caro():
    im = bg((AMB, VIO))
    im = kicker(im, 430, "EXPLICADO FÁCIL", YEL)
    im = headline(im, 650, "¿Por qué está todo", 130)
    im = pill(im, 870, "más caro?")
    d = ImageDraw.Draw(im)
    d.text((W / 2, 1100), "Te lo explicamos en 20 segundos", font=F(FS, 46), fill=SOFT, anchor="mm")
    return brand(im)


def sober_bg():
    im = S.mesh_bg(accent=((70, 74, 96), (40, 44, 64)))
    return im


def t_urda(day2=False):
    im = sober_bg()
    im = kicker(im, 380, "ACCIDENTE DE URDA (TOLEDO)", (235, 120, 130))
    im = ribbon(im, W / 2, 720, 1.3)
    d = ImageDraw.Draw(im)
    if day2:
        d.text((W / 2, 1020), "Lo que se sabe hoy", font=F(FXB, 104), fill=WHITE, anchor="mm")
        d.text((W / 2, 1130), "La investigación y las cifras oficiales", font=F(FS, 44), fill=SOFT, anchor="mm")
    else:
        d.text((W / 2, 1020), "Lo que se sabe", font=F(FXB, 110), fill=WHITE, anchor="mm")
        d.text((W / 2, 1130), "Datos oficiales y teléfonos para familias", font=F(FS, 44), fill=SOFT, anchor="mm")
    return brand(im)


JOBS = {
    "Q7hrK0VY490_mundo60": t_mundo,
    "SxkeA8x5LfE_binance": t_binance,
    "QlXmIWqgiKs_bce": t_bce,
    "cT_eoWpZ4sk_urda_hoy": lambda: t_urda(True),
    "I65Xtc_3aOI_fed": t_fed,
    "2SyuU7w3Buo_urda": t_urda,
    "jBJZnzFYWUw_caro": t_caro,
}

if __name__ == "__main__":
    ims = {}
    for k, fn in JOBS.items():
        im = fn()
        im.save(f"{OUT}/{k}.jpg", quality=90)
        ims[k] = im
    sheet = Image.new("RGB", (7 * 300 + 8 * 20, 533 + 40), (14, 16, 22))
    for i, im in enumerate(ims.values()):
        sheet.paste(im.resize((300, 533), Image.LANCZOS), (20 + i * 320, 20))
    sheet.save(f"{OUT}/todas.jpg", quality=88)
    print("ok", [os.path.getsize(f"{OUT}/{k}.jpg") // 1024 for k in ims])

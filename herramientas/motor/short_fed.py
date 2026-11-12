"""Short: Fed today 19:00 + ECB tomorrow, what it means for you. Reuses the Urda short layout engine."""
import math, os
from PIL import Image, ImageDraw

D = os.path.dirname(os.path.abspath(__file__))
src = open(f"{D}/short_urda2.py").read()
src = src[: src.rindex("\nmain()")]
ns = {"__name__": "base"}
exec(compile(src, "short_urda2", "exec"), ns)
g = ns

# channel palette instead of breaking-news red
g["ACCENT"] = (34, 190, 230)
g["RED"] = (255, 214, 10)  # key figures in channel yellow
g["OUT"] = "/home/claude/canal/short/short_fed_bce_previa.mp4"
Ill, F, FB, FBK, FS, SS = g["Ill"], g["F"], g["FB"], g["FBK"], g["FS"], g["SS"]
WHITE, MUTED, CYAN, AMBER = g["WHITE"], g["MUTED"], g["CYAN"], g["AMBER"]
VIOLET = (139, 92, 246)
YEL = (255, 214, 10)


def bank(c, cx, cy, s, col, label):
    c.d.polygon(c.pts([(cx - 150 * s, cy - 90 * s), (cx, cy - 170 * s), (cx + 150 * s, cy - 90 * s)]), fill=col)
    for k in (-0.75, -0.25, 0.25, 0.75):
        x = cx + k * 140 * s
        c.d.rectangle(c.P(x - 16 * s, cy - 80 * s, x + 16 * s, cy + 60 * s), fill=col)
    c.d.rectangle(c.P(cx - 160 * s, cy + 66 * s, cx + 160 * s, cy + 86 * s), fill=col)
    c.d.text((cx * SS, (cy + 150 * s) * SS), label, font=F(FB, 46 * SS), fill=WHITE, anchor="ms")


def ill_two_banks():
    c = Ill()
    w, h = c.w, c.h
    bank(c, w * 0.3, h * 0.5, 1.15, CYAN, "Fed · EE. UU.")
    bank(c, w * 0.7, h * 0.5, 1.15, VIOLET, "BCE · Europa")
    c.d.text((w * 0.3 * SS, (h * 0.5 - 230) * SS), "HOY 19:00", font=F(FBK, 52 * SS), fill=YEL, anchor="ms")
    c.d.text((w * 0.7 * SS, (h * 0.5 - 230) * SS), "MAÑANA", font=F(FBK, 52 * SS), fill=YEL, anchor="ms")
    return c.done()


def ill_odds():
    c = Ill()
    w, h = c.w, c.h
    x0, x1, y = 160, w - 160, h * 0.5
    split = x0 + (x1 - x0) * 0.906
    c.d.rounded_rectangle(c.P(x0, y - 60, x1, y + 60), radius=30 * SS, fill=VIOLET)
    c.d.rounded_rectangle(c.P(x0, y - 60, split, y + 60), radius=30 * SS, fill=CYAN)
    c.d.text(((x0 + split) / 2 * SS, (y + 18) * SS), "Mantener 90,6 %", font=F(FBK, 50 * SS), fill=(10, 14, 26), anchor="ms")
    c.d.text((x1 * SS, (y + 130) * SS), "Subir 9,4 %", font=F(FB, 40 * SS), fill=VIOLET, anchor="rs")
    c.d.text((w / 2 * SS, (y - 120) * SS), "Lo que espera el mercado", font=F(FB, 44 * SS), fill=MUTED, anchor="ms")
    return c.done()


def ill_pressure():
    c = Ill()
    w, h = c.w, c.h
    # oil barrel + rising line
    bx, by = w * 0.3, h * 0.52
    c.d.rounded_rectangle(c.P(bx - 110, by - 160, bx + 110, by + 160), radius=30 * SS, fill=(40, 46, 70), outline=AMBER, width=6 * SS)
    for k in (-70, 70):
        c.d.line(c.P(bx - 110, by + k, bx + 110, by + k), fill=AMBER, width=6 * SS)
    c.d.text((bx * SS, (by + 20) * SS), "~100 $", font=F(FBK, 52 * SS), fill=WHITE, anchor="ms")
    pts = [(w * 0.55, h * 0.72), (w * 0.64, h * 0.62), (w * 0.71, h * 0.66), (w * 0.8, h * 0.45), (w * 0.88, h * 0.32)]
    c.d.line(c.pts(pts), fill=YEL, width=12 * SS, joint="curve")
    c.d.text((w * 0.75 * SS, (h * 0.85) * SS), "Inflación EE. UU. 3,7 %", font=F(FB, 40 * SS), fill=WHITE, anchor="ms")
    return c.done()


def ill_house():
    c = Ill()
    w, h = c.w, c.h
    cx, cy = w / 2, h * 0.55
    c.d.polygon(c.pts([(cx - 240, cy - 40), (cx, cy - 260), (cx + 240, cy - 40)]), fill=CYAN)
    c.d.rectangle(c.P(cx - 190, cy - 40, cx + 190, cy + 220), fill=(30, 40, 66))
    c.d.rectangle(c.P(cx - 40, cy + 80, cx + 40, cy + 220), fill=CYAN)
    c.d.text((cx * SS, (cy + 40) * SS), "€", font=F(FBK, 110 * SS), fill=YEL, anchor="ms")
    return c.done()


def ill_watch():
    c = Ill()
    w, h = c.w, c.h
    items = [("$", "Dólar"), ("⛽", "Gasolina"), ("%", "Euríbor")]
    for i, (sym, lab) in enumerate(items):
        x = w * (0.2 + 0.3 * i)
        y = h * 0.48
        c.d.ellipse(c.P(x - 110, y - 110, x + 110, y + 110), outline=[CYAN, AMBER, VIOLET][i], width=8 * SS, fill=(18, 26, 46))
        if sym == "⛽":
            c.d.rounded_rectangle(c.P(x - 40, y - 60, x + 25, y + 60), radius=8 * SS, outline=AMBER, width=8 * SS)
            c.d.line(c.P(x + 25, y - 20, x + 60, y, x + 60, y + 40), fill=AMBER, width=8 * SS)
        else:
            c.d.text((x * SS, (y + 40) * SS), sym, font=F(FBK, 120 * SS), fill=WHITE, anchor="ms")
        c.d.text((x * SS, (y + 190) * SS), lab, font=F(FB, 44 * SS), fill=WHITE, anchor="ms")
    return c.done()


def ill_logo():
    import sys
    sys.path.insert(0, D)
    import make_brand_v2 as brand
    c = Ill((10, 14, 30), (6, 8, 16))
    w, h = c.w, c.h
    from PIL import ImageChops
    m = brand.compose_mark(Image.new("RGB", c.im.size, (0, 0, 0)), w / 2 * SS, h / 2 * SS, 220 * SS, SS)
    c.im = ImageChops.add(c.im, m)
    return c.done()


g["CARDS"] = [
    (5.0, ill_two_banks, [("big", "Hoy decide la Fed. Mañana, el BCE"), ("small", "Los dos bancos centrales que mueven tu dinero")]),
    (6.0, ill_odds, [("tag", "FED · HOY 19:00"), ("mid", "Tipos del 3,75 % al 4 %. El mercado espera que los mantenga"), ("small", "Probabilidad según los futuros sobre tipos")]),
    (6.0, ill_pressure, [("mid", "¿Por qué podría subirlos?"), ("small", "Inflación del 3,7 % en septiembre y petróleo cerca de 100 dólares")]),
    (6.0, ill_two_banks, [("tag", "BCE · MAÑANA"), ("mid", "Ya subió los tipos en septiembre"), ("small", "Facilidad de depósito: 2,50 %")]),
    (6.5, ill_house, [("tag", "TU HIPOTECA"), ("red", "+94 € al mes"), ("small", "Euríbor del 2,17 % al 3,22 % en un año. Hipoteca de 150.000 € a 25 años")]),
    (6.0, ill_watch, [("mid", "Si suben los tipos, suelen subir el euríbor y las hipotecas"), ("small", "Y si se fortalece el dólar, el petróleo nos sale más caro")]),
    (5.0, ill_logo, [("mid", "Esta tarde y mañana te contamos qué deciden"), ("small", "Información, no asesoramiento financiero")]),
]
g["STYLE"]["red"] = (FBK, 110, YEL)

# header / footer for this short
base_card_src = g["base_card"]


def header(im):
    d = ImageDraw.Draw(im)
    W = g["W"]
    d.rectangle([0, 0, W, 205], fill=g["BG"])
    d.rectangle([120, 204, W - 120, 205], fill=(40, 52, 80))
    d.rectangle([0, 0, W, 10], fill=g["ACCENT"])
    t = "ECONOMÍA"
    w = d.textlength(t, font=F(FBK, 34)) + 60
    d.rectangle([W / 2 - w / 2, 64, W / 2 + w / 2, 118], fill=g["ACCENT"])
    d.text((W / 2, 91), t, font=F(FBK, 34), fill=(10, 14, 26), anchor="mm")
    d.text((W / 2, 150), "Fed y BCE · 28 y 29 de octubre", font=F(FS, 30), fill=MUTED, anchor="mt")


g["header"] = header
_bc = g["base_card"]


def base_card(items):
    im = _bc(items)
    d = ImageDraw.Draw(im)
    W = g["W"]
    d.rectangle([0, 1720, W, 1820], fill=g["BG"])
    d.text((W / 2, 1735), "Datos del 28/10/2026 · fuentes en la descripción", font=F(FS, 28), fill=MUTED, anchor="mt")
    d.text((W / 2, 1785), "CÓMO VA EL MUNDO", font=F(FB, 26), fill=(90, 104, 136), anchor="mt")
    return im


g["base_card"] = base_card
# music file name separate
g["main"].__globals__.update(g)
src_main = g["main"]
import subprocess
_orig_run = subprocess.run


def run(cmd, *a, **k):
    cmd = [x.replace("ambient_urda.wav", "ambient_fed.wav") for x in cmd]
    return _orig_run(cmd, *a, **k)


subprocess.run = run
_orig_popen = subprocess.Popen


def popen(cmd, *a, **k):
    cmd = [x.replace("ambient_urda.wav", "ambient_fed.wav") for x in cmd]
    return _orig_popen(cmd, *a, **k)


subprocess.Popen = popen
g["subprocess"] = subprocess
src_main()

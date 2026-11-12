"""Channel trailer for Cómo Va el Mundo, built with the same animation engine."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim
from anim import *  # noqa: F401,F403
from PIL import Image, ImageChops, ImageDraw

anim.SC = []
scene = anim.scene


def g_news(f, cx, cy, r, c):
    f.d.rectangle(f.P(cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), outline=c, width=5 * S)
    f.d.rectangle(f.P(cx - r * 0.75, cy - r * 0.55, cx - r * 0.05, cy + r * 0.05), fill=c)
    for k in (-0.5, -0.2, 0.1, 0.4):
        f.d.line(f.P(cx + r * 0.15, cy + k * r, cx + r * 0.75, cy + k * r), fill=c, width=4 * S)
    f.d.line(f.P(cx - r * 0.75, cy + r * 0.45, cx + r * 0.75, cy + r * 0.45), fill=c, width=4 * S)


def g_question(f, cx, cy, r, c):
    f.d.text((cx * S, (cy + r * 0.7) * S), "?", font=F(FBK, r * 2.1), fill=c, anchor="ms")


def g_noadvice(f, cx, cy, r, c):
    g_euro(f, cx, cy, r, c)
    f.d.ellipse(f.P(cx - r * 1.15, cy - r * 1.15, cx + r * 1.15, cy + r * 1.15), outline=RED, width=7 * S)
    f.d.line(f.P(cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=RED, width=7 * S)


def g_compare(f, cx, cy, r, c):
    f.d.rectangle(f.P(cx - r * 0.8, cy - r * 0.2, cx - r * 0.2, cy + r * 0.8), fill=c)
    f.d.rectangle(f.P(cx + r * 0.2, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=c)


@scene("", None, [
    "¿Por qué todo es cada vez más caro?",
    "¿Por qué no bajan los alquileres?",
    "¿Qué está pasando en el mundo… y cómo te afecta a ti?",
])
def t01(f, p):
    f.t(960, 360, "¿Por qué todo es cada vez más caro?", 70, WHITE, FX, "ms", p(0))
    f.t(960, 520, "¿Por qué no bajan los alquileres?", 70, CYAN, FX, "ms", p(1), glow=True)
    f.t(960, 680, "¿Qué está pasando en el mundo…", 70, WHITE, FX, "ms", p(2))
    f.t(960, 800, "…y cómo te afecta a ti?", 70, YELLOW, FX, "ms", p(2), glow=True)


@scene("", None, [
    "Bienvenido a Cómo Va el Mundo.",
    "Aquí te explicamos la economía y la actualidad como nadie te la ha explicado: fácil, claro y sin palabras raras.",
])
def t02(f, p):
    if p(0) > 0:
        m = brand.compose_mark(Image.new("RGB", f.im.size, (0, 0, 0)), 960 * S, 420 * S, 190 * S * back(p(0)), S)
        f.im = ImageChops.add(f.im, m)
        f.d = ImageDraw.Draw(f.im)
        f.t(960, 760, "Cómo Va el Mundo", 104, WHITE, FX, "ms", p(0))
    f.t(960, 850, "Lo que pasa en el mundo, y lo que significa para tu bolsillo", 38, MUTED, FS, "ms", p(0))
    for i, w in enumerate(["Fácil", "Claro", "Sin palabras raras"]):
        pi = max(0, min(1, p(1) * 2.2 - i * 0.4))
        x = 540 + i * 420
        f.box(x - 195, 910, x + 195, 990, YELLOW, pi)
        f.t(x, 963, w, 34, YELLOW, FB, "ms", pi, slide=0)


@scene("Cada semana", "Cuatro tipos de vídeos", [
    "Cada semana vas a encontrar cuatro tipos de vídeos.",
    "Noticias explicadas: lo que ha pasado esta semana y lo que significa para tu bolsillo.",
    "Por qué pasa: los precios, la vivienda, la luz o los sueldos.",
    "Historias de empresas: cómo nacieron, cómo crecieron… y cómo cayeron.",
    "Y el mundo comparado: sueldos, precios y países, cara a cara.",
])
def t03(f, p):
    f.header("Cada semana", "Cuatro tipos de vídeos", p(0))
    cards = [
        ("Noticias explicadas", "Qué ha pasado y cómo te afecta", g_news, CYAN),
        ("Por qué pasa", "Precios, vivienda, luz, sueldos", g_question, YELLOW),
        ("Historias de empresas", "Cómo nacieron… y cómo cayeron", g_factory, VIOLET),
        ("El mundo comparado", "Países, sueldos y precios", g_compare, GREEN),
    ]
    for i, (name, sub, gl, col) in enumerate(cards):
        o = p(i + 1)
        x0 = 120 + i * 430
        f.box(x0, 330, x0 + 400, 900, col, o)
        f.disc(x0 + 200, 500, 95, col, o, gl)
        f.wrap(x0 + 200, 700, name, 40, 340, WHITE, FB, o, anchor="ms")
        f.wrap(x0 + 200, 810, sub, 28, 340, MUTED, FS, o, anchor="ms")


@scene("Nuestra promesa", "Datos reales, siempre", [
    "Todo con datos reales y las fuentes en cada vídeo.",
    "Sin consejos de inversión: solo entender cómo va el mundo.",
])
def t04(f, p):
    f.header("Nuestra promesa", "Datos reales, siempre", p(0))
    f.disc(560, 580, 150, CYAN, p(0), g_ticket, "Fuentes en cada vídeo", lsize=42)
    f.disc(1360, 580, 150, VIOLET, p(1), g_noadvice, "Sin consejos de inversión", lsize=42)
    f.t(960, 960, "Solo entender cómo va el mundo", 48, YELLOW, FB, "ms", p(1), glow=True)


@scene("", None, [
    "Si quieres entender qué pasa con tu dinero, suscríbete.",
    "Nuevo vídeo cada semana.",
])
def t05(f, p):
    m = brand.compose_mark(Image.new("RGB", f.im.size, (0, 0, 0)), 960 * S, 380 * S, 160 * S, S)
    f.im = ImageChops.add(f.im, m)
    f.d = ImageDraw.Draw(f.im)
    f.t(960, 680, "Cómo Va el Mundo", 92, WHITE, FX, "ms", 1, slide=0)
    if p(0) > 0:
        k = back(p(0))
        w, h = 200 * k, 46 * k
        f.d.rounded_rectangle(f.P(960 - w, 790 - h, 960 + w, 790 + h), radius=int(h * S), fill=(220, 38, 38))
        f.t(960, 806, "SUSCRÍBETE", 46 * k, WHITE, FX, "ms", 1, slide=0)
    f.t(960, 940, "Nuevo vídeo cada semana", 44, YELLOW, FB, "ms", p(1), glow=True)


if __name__ == "__main__":
    outdir = sys.argv[1]
    if len(sys.argv) > 2 and sys.argv[2] == "preview":
        os.makedirs(outdir, exist_ok=True)
        for i, sc in enumerate(anim.SC):
            fr = anim.Fr(); sc["draw"](fr, lambda k: 1.0); fr.done().resize((640, 360)).save(f"{outdir}/t{i + 1:02d}.jpg")
        tl, total = anim.timeline(); print("estimated seconds", round(total, 1))
    else:
        for si in range(len(anim.SC)):
            anim.render_scene(si, outdir)

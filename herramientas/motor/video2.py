"""Video 2 (16:9): ¿Por qué no puedo comprar una casa? Style A2, synced per sentence.
usage: video2.py timing.json out.mp4 [first_par last_par]
timing.json: {"dur": seconds, "pars": [[t_sentence0, t_sentence1, ...], ...]}  (absolute seconds)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import style_a2 as S
import short_a2 as A

W, H, FPS = 1920, 1080, 25
F, FBK, FXB, FB, FS, FM = S.F, S.FBK, S.FXB, S.FB, S.FS, S.FM
INK, WHITE, SOFT, DIM, YEL, AMB, CYAN, VIO = S.INK, S.WHITE, S.SOFT, S.DIM, S.YEL, S.AMB, S.CYAN, S.VIO
RED = (240, 70, 90)
GREEN = (70, 220, 150)
ease, eback = A.ease_out, A.ease_back
rgba_text = A.rgba_text


# ---------------- primitives ----------------
class El:
    def __init__(self, img, cx, cy, t0, kind="rise", dur=0.45, anchor="c"):
        self.img, self.cx, self.cy, self.t0, self.kind, self.dur, self.anchor = img, cx, cy, t0, kind, dur, anchor

    def draw(self, fr, t):
        u = (t - self.t0) / self.dur
        if u <= 0:
            return
        img = self.img
        dy = dx = 0
        if u < 1:
            a = ease(u)
            if self.kind == "pop":
                s = 0.55 + 0.45 * eback(u)
                img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
            elif self.kind == "left":
                dx = -(1 - a) * 60
            else:
                dy = (1 - a) * 40
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda v: int(v * a)))
        x = self.cx - (img.width / 2 if self.anchor == "c" else 0) + dx
        y = self.cy - img.height / 2 + dy
        fr.alpha_composite(img, (int(x), int(y)))


def T(txt, size, col=WHITE, font=None, glow=None, track=0):
    return rgba_text(txt, F(font or FXB, size), col, glow=glow, track=track)


def lines_els(lines, x, y0, t0, size=64, col=WHITE, font=None, gap=1.25, step=0.18, anchor="l"):
    els = []
    f = F(font or FXB, size)
    lh = sum(f.getmetrics()) * gap
    for i, ln in enumerate(lines):
        els.append(El(T(ln, size, col, font), x, y0 + i * lh, t0 + i * step, anchor=anchor, kind="left" if anchor == "l" else "rise"))
    return els


def kicker(txt, x, y, t0, col=CYAN, anchor="l"):
    return El(T(txt, 30, col, FB, track=7), x, y, t0, anchor=anchor)


class Counter:
    def __init__(self, cx, cy, a, b, t0, dur=1.2, dec=0, pre="", suf="", size=200, c1=(255, 228, 115), c2=AMB, anchor="c"):
        self.__dict__.update(locals())
        self.cache = {}

    def fmt(self, v):
        return self.pre + f"{v:,.{self.dec}f}".replace(",", "X").replace(".", ",").replace("X", ".") + self.suf

    def draw(self, fr, t):
        if t < self.t0:
            return
        v = self.a + (self.b - self.a) * ease((t - self.t0) / self.dur)
        s = self.fmt(v)
        if s not in self.cache:
            self.cache[s] = rgba_text(s, F(FBK, self.size), (self.c1, self.c2), glow=self.c2, glow_r=40, glow_k=0.4)
        img = self.cache[s]
        al = ease((t - self.t0) / 0.3)
        if al < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda q: int(q * al)))
        x = self.cx - (img.width / 2 if self.anchor == "c" else 0)
        fr.alpha_composite(img, (int(x), int(self.cy - img.height / 2)))


class Bars:
    """Horizontal bars inside a glass card. rows: (label, value, shown_text, color)."""

    def __init__(self, box, rows, t0, vmax=None, stagger=0.35, title=None):
        self.box, self.rows, self.t0, self.st, self.title = box, rows, t0, stagger, title
        self.vmax = vmax or max(r[1] for r in rows)

    def draw(self, fr, t):
        a = ease((t - self.t0) / 0.4)
        if a <= 0:
            return
        x0, y0, x1, y1 = self.box
        card = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        d = ImageDraw.Draw(card)
        d.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=40, fill=(255, 255, 255, int(14 * a)), outline=(255, 255, 255, int(38 * a)), width=2)
        top = 60
        if self.title:
            d.text((50, 50), self.title, font=F(FB, 32), fill=SOFT + (int(255 * a),), anchor="lm")
            top = 120
        n = len(self.rows)
        rh = (card.height - top - 30) / n
        lw = max(d.textlength(r[0], font=F(FS, 36)) for r in self.rows) + 80
        for i, (lab, val, shown, col) in enumerate(self.rows):
            ry = top + rh * i + rh / 2
            ta = ease((t - self.t0 - 0.2 - i * self.st) / 0.3)
            d.text((50, ry), lab, font=F(FS, 36), fill=SOFT + (int(255 * ta),), anchor="lm")
            bx0, bx1 = 50 + lw, card.width - 300
            d.rounded_rectangle([bx0, ry - 17, bx1, ry + 17], radius=17, fill=(40, 44, 68, int(255 * a)))
            g = ease((t - self.t0 - 0.35 - i * self.st) / 0.9)
            bw = (bx1 - bx0) * val / self.vmax * g
            if bw > 6:
                d.rounded_rectangle([bx0, ry - 17, bx0 + bw, ry + 17], radius=17, fill=col + (255,))
            d.text((card.width - 50, ry), shown, font=F(FXB, 50), fill=WHITE + (int(255 * ta),), anchor="rm")
        fr.alpha_composite(card, (x0, int(y0 + (1 - a) * 30)))


class Waffle:
    """10x10 dots, first n lit."""

    def __init__(self, cx, cy, lit, t0, cell=46, col=YEL):
        self.cx, self.cy, self.lit, self.t0, self.cell, self.col = cx, cy, lit, t0, cell, col

    def draw(self, fr, t):
        if t < self.t0:
            return
        d = ImageDraw.Draw(fr)
        c = self.cell
        x0, y0 = self.cx - 5 * c, self.cy - 5 * c
        for i in range(100):
            r, k = divmod(i, 10)
            appear = ease((t - self.t0 - i * 0.008) / 0.25)
            if appear <= 0:
                continue
            rad = c * 0.36 * appear
            x, y = x0 + k * c + c / 2, y0 + r * c + c / 2
            on = i < self.lit and t > self.t0 + 1.0 + i * 0.05
            col = self.col if on else (58, 64, 92)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=col + (255,))


def house_icon(size=300, col=CYAN, fill=(26, 34, 60)):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    s = size
    d.polygon([(s * 0.08, s * 0.48), (s * 0.5, s * 0.1), (s * 0.92, s * 0.48)], fill=col + (255,))
    d.rectangle([s * 0.18, s * 0.46, s * 0.82, s * 0.92], fill=fill + (255,), outline=col + (255,), width=max(3, s // 40))
    d.rectangle([s * 0.42, s * 0.64, s * 0.58, s * 0.92], fill=col + (255,))
    d.rectangle([s * 0.26, s * 0.56, s * 0.36, s * 0.66], fill=YEL + (255,))
    d.rectangle([s * 0.64, s * 0.56, s * 0.74, s * 0.66], fill=YEL + (255,))
    g = im.filter(ImageFilter.GaussianBlur(s // 14))
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.alpha_composite(Image.eval(g, lambda v: int(v * 0.5)))
    out.alpha_composite(im)
    return out


def card_icon(title, sub, emoji_draw, w=400, h=330, col=CYAN):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=36, fill=(255, 255, 255, 16), outline=(255, 255, 255, 44), width=2)
    emoji_draw(d, w / 2, 95, col)
    d.text((w / 2, 190), title, font=F(FXB, 38), fill=WHITE + (255,), anchor="mm")
    d.text((w / 2, 240), sub, font=F(FM, 26), fill=SOFT + (255,), anchor="mm")
    return im


def ic_land(d, cx, cy, col):
    d.rectangle([cx - 70, cy + 10, cx + 70, cy + 40], fill=col + (255,))
    d.line([cx - 50, cy + 10, cx - 50, cy - 50], fill=col + (255,), width=6)
    d.polygon([(cx - 50, cy - 50), (cx + 10, cy - 35), (cx - 50, cy - 20)], fill=YEL + (255,))


def ic_doc(d, cx, cy, col):
    d.rounded_rectangle([cx - 45, cy - 60, cx + 45, cy + 50], radius=10, outline=col + (255,), width=6)
    for k in range(3):
        d.line([cx - 25, cy - 30 + k * 25, cx + 25, cy - 30 + k * 25], fill=col + (255,), width=5)
    d.ellipse([cx + 15, cy + 15, cx + 65, cy + 65], fill=YEL + (255,))
    d.line([cx + 40, cy + 28, cx + 40, cy + 42, cx + 50, cy + 48], fill=INK + (255,), width=4)


def ic_worker(d, cx, cy, col):
    d.pieslice([cx - 45, cy - 70, cx + 45, cy - 10], 180, 360, fill=YEL + (255,))
    d.rectangle([cx - 55, cy - 42, cx + 55, cy - 34], fill=YEL + (255,))
    d.ellipse([cx - 30, cy - 34, cx + 30, cy + 20], fill=col + (255,))
    d.rounded_rectangle([cx - 55, cy + 24, cx + 55, cy + 70], radius=20, fill=col + (255,))


def ic_suitcase(d, cx, cy, col):
    d.rounded_rectangle([cx - 60, cy - 30, cx + 60, cy + 55], radius=14, fill=col + (255,))
    d.rounded_rectangle([cx - 25, cy - 55, cx + 25, cy - 25], radius=8, outline=col + (255,), width=6)
    d.line([cx - 60, cy + 5, cx + 60, cy + 5], fill=INK + (255,), width=5)
    d.text((cx, cy + 32), "€", font=F(FBK, 40), fill=YEL + (255,), anchor="mm")


# ---------------- scenes (one per paragraph) ----------------
# Each builder gets s = list of sentence start times RELATIVE to the paragraph start, returns (items, chip, source)
L = 140  # left margin
RX = 1340  # right visual centre


def sc_title(s):
    it = [El(house_icon(360), RX, 540, 0.1, kind="pop", dur=0.6)]
    it += [kicker("EXPLICADO FÁCIL", L, 330, 0.0)]
    it += lines_els(["¿Por qué no", "puedo comprar", "una casa?"], L, 440, 0.15, size=104)
    return it, "VIVIENDA", None


def sc_intro(s):
    it = [kicker("NO ES UNA SENSACIÓN", L, 300, s[0])]
    it += lines_els(["Trabajas.", "Ahorras."], L, 420, s[1], size=96)
    it += [El(T("Y comprar sigue pareciendo imposible.", 52, SOFT, FS), L, 650, s[1] + 1.0, anchor="l", kind="left")]
    it += [El(T("Los datos lo confirman", 56, YEL, FXB), L, 790, s[min(3, len(s) - 1)], anchor="l", kind="left")]
    it += [El(house_icon(300, col=SOFT), RX, 520, s[0] + 0.3, kind="pop")]
    return it, "INTRODUCCIÓN", None


def sc_price(s):
    it = [kicker("PRECIO DE LA VIVIENDA EN UN AÑO", L, 300, s[0], YEL)]
    it += [Counter(L, 520, 0, 12.2, s[0] + 0.3, dec=1, pre="+", suf=" %", size=260, anchor="l")]
    it += [El(T("Más de una década subiendo", 52, WHITE, FXB), L, 720, s[min(2, len(s) - 1)], anchor="l", kind="left")]
    it += [El(house_icon(320, col=AMB), 1620, 520, s[0] + 0.2, kind="pop")]
    return it, "1 · EL PRECIO", "Fuente: INE, Índice de Precios de Vivienda, 2.º trimestre de 2026"


def sc_wages(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("DESDE 2013", L, 250, s[0], YEL)]
    it += [Bars((L, 290, 1180, 600), [("Vivienda", 108, "+108 %", AMB), ("Sueldos", 30, "+30 %", CYAN)], k(2), title="Subida acumulada 2013–2026")]
    it += [El(T("100.000 €  →  208.000 €", 52, YEL, FXB), L, 730, k(4), anchor="l", kind="left")]
    it += [El(T("Un piso de entonces, hoy", 32, SOFT, FM), L, 790, k(4) + 0.2, anchor="l", kind="left")]
    it += [El(T("20.000 €  →  26.000 €", 52, CYAN, FXB), L, 880, k(5), anchor="l", kind="left")]
    it += [El(T("Un sueldo de entonces, hoy", 32, SOFT, FM), L, 940, k(5) + 0.2, anchor="l", kind="left")]
    it += [El(T("La casa corre.", 70, AMB, FXB), 1560, 400, k(6), kind="pop")]
    it += [El(T("Tu sueldo camina.", 70, CYAN, FXB), 1560, 520, k(6) + 0.6, kind="pop")]
    return it, "2 · LOS SUELDOS", "Fuentes: informe de CCOO (2.º trim. 2013–2026) · INE, costes laborales"


def sc_effort(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("PARA COMPRAR UNA VIVIENDA MEDIA", L, 290, s[0], YEL)]
    it += [Counter(L, 470, 0, 8.4, k(1), dec=1, size=240, anchor="l")]
    it += [El(T("años de sueldo íntegro", 60, WHITE, FXB), L, 640, k(1) + 0.6, anchor="l", kind="left")]
    it += [El(T("El máximo desde 2011", 44, SOFT, FS), L, 720, k(3), anchor="l", kind="left")]
    it += [Counter(RX, 470, 0, 38, k(4), suf=" %", size=200, c1=(255, 255, 255), c2=CYAN)]
    it += [El(T("de los ingresos de un hogar", 40, SOFT, FS), RX, 610, k(4) + 0.5)]
    it += [El(T("se va en la primera cuota", 40, SOFT, FS), RX, 665, k(4) + 0.7)]
    return it, "3 · EL ESFUERZO", "Fuente: Banco de España, indicadores de accesibilidad a la vivienda"


def sc_rent(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("ALQUILER · MEDIA DE ESPAÑA", L, 290, k(1), YEL)]
    it += [Counter(L, 460, 0, 15.1, k(2), dec=1, suf=" €/m²", size=160, anchor="l")]
    it += [El(T("Más de 1.200 € al mes por 80 m²", 54, WHITE, FXB), L, 640, k(3), anchor="l", kind="left")]
    it += [Bars((1060, 300, 1820, 800), [("Madrid", 21.6, "21,6 €", AMB), ("Baleares", 20.2, "20,2 €", AMB), ("España", 15.1, "15,1 €", CYAN)], k(4), title="€/m² al mes, septiembre", stagger=0.25)]
    return it, "4 · EL ALQUILER", "Fuente: idealista, informe de precios de alquiler, septiembre de 2026"


def sc_youth(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("JÓVENES DE 16 A 29 AÑOS", L, 290, s[0], YEL)]
    it += [Counter(L, 450, 0, 14.5, k(1), dec=1, suf=" %", size=220, anchor="l")]
    it += [El(T("vive fuera de casa de sus padres", 50, WHITE, FXB), L, 600, k(1) + 0.6, anchor="l", kind="left")]
    it += [El(T("Edad media para irse: casi 30 años", 44, SOFT, FS), L, 720, k(3), anchor="l", kind="left")]
    it += [El(T("Alquilar solo: casi el 100 % del sueldo", 44, AMB, FXB), L, 800, k(5), anchor="l", kind="left")]
    it += [Waffle(RX + 40, 540, 15, k(1), cell=50)]
    return it, "5 · LOS JÓVENES", "Fuente: Consejo de la Juventud de España, Observatorio de Emancipación"


def sc_supply(s):
    it = [kicker("LA CLAVE", L, 330, s[0])]
    it += lines_els(["Oferta y", "demanda"], L, 450, s[0] + 0.2, size=110)
    it += [El(T("Más gente buscando casa", 44, SOFT, FS), L, 720, s[min(1, len(s) - 1)], anchor="l", kind="left"), El(T("que casas disponibles", 44, SOFT, FS), L, 780, s[min(1, len(s) - 1)] + 0.2, anchor="l", kind="left")]
    # balance scale
    def scale(fr, t, t0=s[0] + 0.4):
        a = ease((t - t0) / 0.6)
        if a <= 0:
            return
        d = ImageDraw.Draw(fr)
        cx, cy = 1450, 560
        tilt = 0.35 * ease((t - t0 - 0.6) / 1.0)
        al = int(255 * a)
        d.polygon([(cx - 60, cy + 200), (cx + 60, cy + 200), (cx, cy - 20)], fill=(58, 64, 92, al))
        dx, dy = 260 * math.cos(tilt), 260 * math.sin(tilt)
        d.line([cx - dx, cy - 20 + dy, cx + dx, cy - 20 - dy], fill=WHITE + (al,), width=10)
        for sx, lab, col in ((-1, "Demanda", AMB), (1, "Oferta", CYAN)):
            px, py = cx + sx * dx, cy - 20 - sx * dy
            d.line([px, py, px, py + 80], fill=WHITE + (al,), width=4)
            d.rounded_rectangle([px - 100, py + 80, px + 100, py + 130], radius=20, fill=col + (al,))
            d.text((px, py + 105), lab, font=F(FXB, 34), fill=INK + (al,), anchor="mm")
    it.append(type("Dyn", (), {"draw": lambda self, fr, t: scale(fr, t)})())
    return it, "6 · POR QUÉ PASA", None


def sc_deficit(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("ESPAÑA, 2025", L, 250, s[0], YEL)]
    it += [Bars((L, 290, 1080, 640), [("Hogares", 240, "240.000", AMB), ("Viviendas", 92, "92.000", CYAN)], k(1), title="Hogares nuevos y viviendas terminadas")]
    it += [El(T("Ni la mitad", 60, YEL, FXB), L, 720, k(3), anchor="l", kind="left")]
    it += [kicker("FALTAN (2021–2025)", 1500, 300, k(5), YEL, anchor="c")]
    it += [Counter(1500, 420, 0, 750000, k(5), size=150)]
    it += [El(T("viviendas", 52, WHITE, FXB), 1500, 530, k(5) + 0.6)]
    provs = ["Madrid", "Barcelona", "Valencia", "Alicante", "Málaga", "Murcia"]
    for i, p in enumerate(provs):
        x = 1500 - 270 + (i % 3) * 270
        y = 680 + (i // 3) * 90
        pill = Image.new("RGBA", (250, 70), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pill)
        pd.rounded_rectangle([0, 0, 249, 69], radius=35, fill=(255, 255, 255, 18), outline=(255, 255, 255, 60), width=2)
        pd.text((125, 35), p, font=F(FB, 34), fill=WHITE + (255,), anchor="mm")
        it.append(El(pill, x, y, k(6) + 0.12 * i, kind="pop"))
    it.append(El(T("La mitad del déficit, en 6 provincias", 34, SOFT, FS), 1500, 880, k(6) + 0.9))
    return it, "6 · POR QUÉ PASA", "Fuente: Banco de España (estimación de déficit 2021–2025)"


def sc_causes(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("¿POR QUÉ NO SE CONSTRUYE MÁS?", 960, 250, s[0], YEL, anchor="c")]
    cards = [("Falta suelo", "listo para edificar", ic_land, k(2)), ("Trámites", "urbanísticos lentos", ic_doc, k(2) + 1.2),
             ("Falta mano", "de obra", ic_worker, k(3)), ("Turísticos", "e inversores", ic_suitcase, k(4))]
    for i, (a, b, ic, t0) in enumerate(cards):
        it.append(El(card_icon(a, b, ic), 330 + i * 420, 560, t0, kind="pop"))
    return it, "7 · LAS CAUSAS", "Fuente: Banco de España, Informe Anual"


def sc_measures(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("DECRETO DE VIVIENDA · OCTUBRE 2026", L, 260, s[0], YEL)]
    items = [("Alquiler: subida máxima del 2 % hasta 2027", k(1)), ("Límites a los pisos turísticos", k(1) + 2.6),
             ("Freno a grandes compradores y fondos", k(1) + 4.6), ("Más dinero para vivienda pública", k(1) + 7.2),
             ("Plan Estatal: 7.000 M€ hasta 2030", k(2))]
    for i, (txt, t0) in enumerate(items):
        row = Image.new("RGBA", (1500, 90), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        rd.ellipse([0, 15, 60, 75], fill=GREEN + (255,))
        rd.line([16, 45, 27, 57, 46, 32], fill=INK + (255,), width=7)
        rd.text((90, 45), txt, font=F(FXB, 48), fill=WHITE + (255,), anchor="lm")
        it.append(El(row, L, 380 + i * 110, t0, anchor="l", kind="left"))
    return it, "8 · QUÉ SE HACE", "Fuentes: BOE (decreto de 7/10/2026), Civio, Ministerio de Vivienda"


def sc_outlook(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [El(T("¿Bajarán los precios?", 100, WHITE, FXB), 960, 400, s[0], kind="pop")]
    it += [El(T("A corto plazo, la mayoría de expertos cree que no", 50, SOFT, FS), 960, 540, k(1))]
    it += [El(A.pill_word("construir más", F(FBK, 110)), 960, 720, k(3), kind="pop")]
    return it, "9 · ¿Y AHORA?", None


def sc_summary(s):
    k = lambda i: s[min(i, len(s) - 1)]
    it = [kicker("RESUMEN", L, 260, s[0], YEL)]
    pts = [("La vivienda sube más rápido que los sueldos", k(1)), ("Comprar exige más de 8 años de salario", k(2)),
           ("El alquiler está en máximos", k(3)), ("En el fondo: faltan casas", k(4))]
    for i, (txt, t0) in enumerate(pts):
        row = Image.new("RGBA", (1600, 100), (0, 0, 0, 0))
        rd = ImageDraw.Draw(row)
        rd.rounded_rectangle([0, 18, 64, 82], radius=18, fill=YEL + (255,))
        rd.text((32, 50), str(i + 1), font=F(FBK, 40), fill=INK + (255,), anchor="mm")
        rd.text((96, 50), txt, font=F(FXB, 56), fill=WHITE + (255,), anchor="lm")
        it.append(El(row, L, 400 + i * 130, t0, anchor="l", kind="left"))
    return it, "RESUMEN", None


def sc_cta(s):
    k = lambda i: s[min(i, len(s) - 1)]
    m, a = S.logo_mark(150)
    lg = m.convert("RGBA")
    lg.putalpha(a)
    it = [El(lg, 960, 330, s[0], kind="pop", dur=0.6)]
    it += [El(T("Economía explicada fácil, con datos reales", 56, WHITE, FXB), 960, 540, s[0] + 0.4)]
    # subscribe button
    bw, bh, gl = 520, 116, 120
    b = Image.new("RGBA", (bw + 2 * gl, bh + 2 * gl), (0, 0, 0, 0))
    mk = Image.new("L", b.size, 0)
    ImageDraw.Draw(mk).rounded_rectangle([gl, gl, gl + bw, gl + bh], radius=58, fill=255)
    glow = Image.new("RGBA", b.size, (255, 40, 70, 0))
    glow.putalpha(mk.filter(ImageFilter.GaussianBlur(45)).point(lambda v: int(v * 0.55)))
    b = Image.alpha_composite(b, glow)
    solid = Image.new("RGBA", b.size, (240, 36, 64, 255))
    solid.putalpha(mk)
    b = Image.alpha_composite(b, solid)
    lab = rgba_text("SUSCRÍBETE", F(FBK, 46), WHITE, track=6)
    b.alpha_composite(lab, (int(b.width / 2 - lab.width / 2), int(b.height / 2 - lab.height / 2) + 2))
    it.append(El(b, 960, 690, s[0] + 0.8, kind="pop"))
    it.append(El(T("¿Alquilas, compraste o sigues en casa de tus padres?", 44, YEL, FXB), 960, 880, k(2)))
    it.append(El(T("Cuéntamelo en los comentarios", 34, SOFT, FS), 960, 940, k(2) + 0.4))
    return it, "CÓMO VA EL MUNDO", None


SCENES = [sc_title, sc_intro, sc_price, sc_wages, sc_effort, sc_rent, sc_youth, sc_supply, sc_deficit, sc_causes, sc_measures, sc_outlook, sc_summary, sc_cta]
ACC = [(VIO, CYAN), (VIO, CYAN), (AMB, VIO), (AMB, VIO), (CYAN, VIO), (VIO, AMB), (AMB, VIO), (CYAN, VIO), (AMB, VIO), (VIO, CYAN), (CYAN, VIO), (VIO, AMB), (VIO, CYAN), (CYAN, VIO)]


def make_bg(acc):
    old = (S.W, S.H)
    S.W, S.H = W + 100, H + 100
    im = S.mesh_bg(accent=acc)
    S.W, S.H = old
    return im


def chrome_layer(chip):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m, a = S.logo_mark(30)
    lg = m.convert("RGBA")
    lg.putalpha(a)
    im.alpha_composite(lg, (100 - lg.width // 2, 90 - lg.height // 2))
    d = ImageDraw.Draw(im)
    d.text((145, 75), "Cómo Va el Mundo", font=F(FB, 32), fill=WHITE + (255,), anchor="lm")
    d.text((145, 110), "Explicado fácil", font=F(FM, 24), fill=SOFT + (255,), anchor="lm")
    if chip:
        tag = rgba_text(chip, F(FB, 24), WHITE, track=4)
        tw = tag.width + 30
        d.rounded_rectangle([W - 70 - tw, 66, W - 70, 114], radius=24, outline=(90, 98, 130, 255), width=2)
        im.alpha_composite(tag, (int(W - 70 - tw / 2 - tag.width / 2), int(90 - tag.height / 2)))
    return im


def main():
    timing = json.load(open(sys.argv[1]))
    out = sys.argv[2]
    p0 = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    p1 = int(sys.argv[4]) if len(sys.argv) > 4 else len(SCENES) - 1
    pars = timing["pars"]
    dur = timing["dur"]
    starts = [p[0] for p in pars] + [dur]
    starts[0] = 0.0
    built = []
    for i, fn in enumerate(SCENES):
        rel = [t - starts[i] for t in pars[i]]
        rel[0] = max(rel[0], 0.0)
        items, chip, src = fn(rel)
        built.append((items, chrome_layer(chip), rgba_text(src, F(FM, 24), DIM) if src else None))
    bgs = {}
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    XF = 0.4
    f0 = int(round(starts[p0] * FPS))
    f1 = int(round(starts[p1 + 1] * FPS))
    for fi in range(f0, f1):
        gt = fi / FPS
        i = max(j for j in range(len(SCENES)) if starts[j] <= gt + 1e-6)
        t = gt - starts[i]
        if i not in bgs:
            bgs[i] = make_bg(ACC[i])
        ox = int(50 + 40 * math.sin(gt * 0.25))
        oy = int(50 + 40 * math.cos(gt * 0.2))
        bg = bgs[i].crop((ox, oy, ox + W, oy + H))
        if i > 0 and t < XF:
            if i - 1 not in bgs:
                bgs[i - 1] = make_bg(ACC[i - 1])
            bg = Image.blend(bgs[i - 1].crop((ox, oy, ox + W, oy + H)), bg, ease(t / XF))
        fr = bg.convert("RGBA")
        if i > 0 and t < XF:
            ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            prev_len = starts[i] - starts[i - 1]
            for it in built[i - 1][0]:
                it.draw(ghost, prev_len)
            a = 1 - t / XF
            ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * a)))
            fr.alpha_composite(ghost)
        for it in built[i][0]:
            it.draw(fr, t)
        fr.alpha_composite(built[i][1])
        if built[i][2] is not None:
            src = built[i][2]
            fr.alpha_composite(src, (int(W / 2 - src.width / 2), H - 70))
        d = ImageDraw.Draw(fr)
        d.rectangle([0, H - 6, W * gt / dur, H], fill=YEL + (255,))
        ff.stdin.write(fr.convert("RGB").tobytes())
    ff.stdin.close()
    ff.wait()
    print("ok", out, f0, f1)


if __name__ == "__main__":
    main()

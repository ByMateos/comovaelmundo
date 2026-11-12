"""Render the 17 scenes of video 1 (Cómo Va el Mundo) as 1920x1080 PNGs."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math, os, sys

sys.path.insert(0, os.path.dirname(__file__))
import make_brand_v2 as brand  # reuses the logo mark

S = 2
W, H = 1920, 1080
OUT = "/home/claude/canal/video1/escenas/"
os.makedirs(OUT, exist_ok=True)

BG_IN, BG_OUT = (16, 24, 52), (4, 6, 14)
CYAN, VIOLET, YELLOW = (34, 211, 238), (139, 92, 246), (255, 214, 10)
WHITE, MUTED, DIM = (240, 244, 255), (140, 160, 200), (60, 72, 110)
RED = (248, 113, 113)
FX = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
_fc = {}


def F(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, int(size * S))
    return _fc[k]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def p(*v):
    return [x * S for x in v]


_BG = None


def background():
    global _BG
    if _BG is None:
        bg = brand.radial_bg(W * S, H * S, W * S * 0.45, H * S * 0.45, W * S * 0.7)
        d = ImageDraw.Draw(bg)
        step = 48
        for y in range(step // 2, H, step):
            for x in range(step // 2, W, step):
                d.ellipse(p(x - 1.4, y - 1.4, x + 1.4, y + 1.4), fill=(24, 32, 62))
        _BG = bg
    return _BG.copy()


class Scene:
    def __init__(self):
        self.im = background()
        self.d = ImageDraw.Draw(self.im)
        self.glowl = Image.new("RGB", self.im.size, (0, 0, 0))
        self.gd = ImageDraw.Draw(self.glowl)

    # text -------------------------------------------------------------
    def t(self, x, y, s, size, color=WHITE, font=FX, anchor="ls", glow=False):
        self.d.text(p(x, y), s, font=F(font, size), fill=color, anchor=anchor)
        if glow:
            self.gd.text(p(x, y), s, font=F(font, size), fill=color, anchor=anchor)

    def tw(self, s, size, font=FX):
        return self.d.textlength(s, font=F(font, size)) / S

    def grad_t(self, x, y, s, size, c1=CYAN, c2=VIOLET, font=FX, anchor="ls"):
        mask = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(mask).text(p(x, y), s, font=F(font, size), fill=255, anchor=anchor)
        bb = mask.getbbox()
        g = Image.new("RGB", self.im.size)
        gd = ImageDraw.Draw(g)
        for xx in range(bb[0], bb[2] + 1):
            gd.line([xx, bb[1], xx, bb[3]], fill=lerp(c1, c2, (xx - bb[0]) / max(1, bb[2] - bb[0])))
        self.im.paste(g, (0, 0), mask)
        self.glowl.paste(g, (0, 0), mask)

    def kicker(self, s, color=CYAN, y=120):
        self.d.rounded_rectangle(p(120, y - 30, 120 + 8, y + 4), radius=2 * S, fill=color)
        self.t(144, y, s.upper(), 26, color, FB)

    def wrap(self, x, y, s, size, maxw, color=MUTED, font=FS, lh=1.35):
        words, line, yy = s.split(), "", y
        for w in words:
            tst = (line + " " + w).strip()
            if self.tw(tst, size, font) > maxw and line:
                self.t(x, yy, line, size, color, font)
                yy += size * lh
                line = w
            else:
                line = tst
        if line:
            self.t(x, yy, line, size, color, font)
        return yy

    def source(self, s):
        txt = "Fuente: " + s
        w = self.tw(txt, 20, FM)
        self.d.rounded_rectangle(p(120, 980, 120 + w + 36, 1022), radius=21 * S, outline=DIM, width=2 * S)
        self.t(138, 1008, txt, 20, MUTED, FM)

    # shapes -----------------------------------------------------------
    def box(self, x0, y0, x1, y1, color=DIM, fill=None, r=20, width=2, glow=False):
        self.d.rounded_rectangle(p(x0, y0, x1, y1), radius=r * S, outline=color, width=width * S, fill=fill)
        if glow:
            self.gd.rounded_rectangle(p(x0, y0, x1, y1), radius=r * S, outline=color, width=width * S)

    def bar(self, x0, y0, x1, y1, c1, c2=None, glow=True):
        c2 = c2 or c1
        mask = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(p(x0, y0, x1, y1), radius=14 * S, fill=255)
        g = Image.new("RGB", self.im.size)
        gd = ImageDraw.Draw(g)
        for yy in range(int(y0 * S), int(y1 * S) + 1):
            gd.line([x0 * S, yy, x1 * S, yy], fill=lerp(c2, c1, (yy - y0 * S) / max(1, (y1 - y0) * S)))
        self.im.paste(g, (0, 0), mask)
        if glow:
            self.glowl.paste(g, (0, 0), mask)

    def arrow(self, x0, y0, x1, y1, color=YELLOW, w=10, head=34, glow=True):
        for dr in ([self.d] + ([self.gd] if glow else [])):
            dr.line(p(x0, y0, x1, y1), fill=color, width=int(w * S))
            a = math.atan2(y1 - y0, x1 - x0)
            tip = (x1 + math.cos(a) * head * 0.5, y1 + math.sin(a) * head * 0.5)
            l = (tip[0] - head * math.cos(a - 0.5), tip[1] - head * math.sin(a - 0.5))
            r = (tip[0] - head * math.cos(a + 0.5), tip[1] - head * math.sin(a + 0.5))
            dr.polygon([tuple(v * S for v in tip), tuple(v * S for v in l), tuple(v * S for v in r)], fill=color)

    def icon_circle(self, cx, cy, r, label, color=CYAN, glyph=None):
        self.d.ellipse(p(cx - r, cy - r, cx + r, cy + r), outline=color, width=3 * S, fill=(12, 18, 40))
        self.gd.ellipse(p(cx - r, cy - r, cx + r, cy + r), outline=color, width=3 * S)
        if glyph:
            glyph(self, cx, cy, r * 0.5, color)
        self.t(cx, cy + r + 44, label, 28, WHITE, FS, anchor="ms")

    def brand_tag(self):
        self.t(1800, 1008, "CÓMO VA EL MUNDO", 20, DIM, FB, anchor="rs")

    def save(self, name):
        self.brand_tag()
        g = self.glowl.filter(ImageFilter.GaussianBlur(14 * S))
        out = ImageChops.add(self.im, ImageChops.multiply(g, Image.new("RGB", g.size, (150, 150, 150))))
        out = out.resize((W, H), Image.LANCZOS)
        out.save(OUT + name)
        print("saved", name)


# glyphs --------------------------------------------------------------------
def g_cart(s, cx, cy, r, c, w=5):
    d = s.d
    d.line(p(cx - r * 1.1, cy - r * 0.8, cx - r * 0.7, cy - r * 0.8, cx - r * 0.4, cy + r * 0.4, cx + r * 0.9, cy + r * 0.4, cx + r * 1.1, cy - r * 0.4, cx - r * 0.55, cy - r * 0.4), fill=c, width=w * S, joint="curve")
    for x in (cx - r * 0.25, cx + r * 0.7):
        d.ellipse(p(x - r * 0.15, cy + r * 0.65, x + r * 0.15, cy + r * 0.95), fill=c)


def g_bolt(s, cx, cy, r, c):
    s.d.polygon([tuple(v * S for v in pt) for pt in [(cx + r * 0.2, cy - r * 1.1), (cx - r * 0.6, cy + r * 0.15), (cx - r * 0.05, cy + r * 0.15), (cx - r * 0.25, cy + r * 1.1), (cx + r * 0.6, cy - r * 0.2), (cx + r * 0.05, cy - r * 0.2)]], fill=c)


def g_house(s, cx, cy, r, c):
    s.d.polygon([tuple(v * S for v in pt) for pt in [(cx - r, cy - r * 0.05), (cx, cy - r), (cx + r, cy - r * 0.05)]], outline=c, width=5 * S)
    s.d.rectangle(p(cx - r * 0.7, cy - r * 0.05, cx + r * 0.7, cy + r * 0.9), outline=c, width=5 * S)


def g_bread(s, cx, cy, r, c):
    s.d.rounded_rectangle(p(cx - r, cy - r * 0.5, cx + r, cy + r * 0.6), radius=int(r * 0.5 * S), outline=c, width=5 * S)
    for k in (-0.45, 0, 0.45):
        s.d.line(p(cx + k * r - r * 0.15, cy - r * 0.2, cx + k * r + r * 0.15, cy + r * 0.2), fill=c, width=4 * S)


def g_car(s, cx, cy, r, c):
    s.d.rounded_rectangle(p(cx - r, cy - r * 0.1, cx + r, cy + r * 0.5), radius=int(r * 0.2 * S), outline=c, width=5 * S)
    s.d.line(p(cx - r * 0.6, cy - r * 0.1, cx - r * 0.35, cy - r * 0.55, cx + r * 0.35, cy - r * 0.55, cx + r * 0.6, cy - r * 0.1), fill=c, width=5 * S)
    for x in (cx - r * 0.55, cx + r * 0.55):
        s.d.ellipse(p(x - r * 0.18, cy + r * 0.4, x + r * 0.18, cy + r * 0.76), fill=c)


def g_shirt(s, cx, cy, r, c):
    pts = [(cx - r * 0.4, cy - r), (cx - r, cy - r * 0.55), (cx - r * 0.75, cy - r * 0.1), (cx - r * 0.5, cy - r * 0.25), (cx - r * 0.5, cy + r), (cx + r * 0.5, cy + r), (cx + r * 0.5, cy - r * 0.25), (cx + r * 0.75, cy - r * 0.1), (cx + r, cy - r * 0.55), (cx + r * 0.4, cy - r)]
    s.d.polygon([tuple(v * S for v in pt) for pt in pts], outline=c, width=5 * S)


def g_pump(s, cx, cy, r, c):
    s.d.rounded_rectangle(p(cx - r * 0.7, cy - r, cx + r * 0.3, cy + r), radius=int(r * 0.15 * S), outline=c, width=5 * S)
    s.d.rectangle(p(cx - r * 0.5, cy - r * 0.75, cx + r * 0.1, cy - r * 0.3), fill=c)
    s.d.line(p(cx + r * 0.3, cy - r * 0.4, cx + r * 0.8, cy - r * 0.1, cx + r * 0.8, cy + r * 0.6), fill=c, width=5 * S)


def g_factory(s, cx, cy, r, c):
    pts = [(cx - r, cy + r * 0.8), (cx - r, cy - r * 0.2), (cx - r * 0.4, cy + r * 0.15), (cx - r * 0.4, cy - r * 0.2), (cx + r * 0.2, cy + r * 0.15), (cx + r * 0.2, cy - r), (cx + r * 0.6, cy - r), (cx + r * 0.6, cy + r * 0.8)]
    s.d.polygon([tuple(v * S for v in pt) for pt in pts], outline=c, width=5 * S)


def g_ship(s, cx, cy, r, c):
    s.d.polygon([tuple(v * S for v in pt) for pt in [(cx - r, cy + r * 0.1), (cx + r, cy + r * 0.1), (cx + r * 0.7, cy + r * 0.7), (cx - r * 0.7, cy + r * 0.7)]], outline=c, width=5 * S)
    for i, x in enumerate((-0.6, -0.15, 0.3)):
        s.d.rectangle(p(cx + x * r, cy - r * 0.45, cx + (x + 0.38) * r, cy + r * 0.1), outline=c, width=4 * S)


def g_euro(s, cx, cy, r, c):
    s.t(cx, cy + r * 0.62, "€", r * 1.9, c, FX, anchor="ms")


def g_people(s, cx, cy, r, c):
    for dx in (-0.45, 0.45):
        s.d.ellipse(p(cx + dx * r - r * 0.25, cy - r * 0.8, cx + dx * r + r * 0.25, cy - r * 0.3), outline=c, width=4 * S)
        s.d.arc(p(cx + dx * r - r * 0.45, cy - r * 0.15, cx + dx * r + r * 0.45, cy + r * 0.95), 180, 360, fill=c, width=4 * S)


# scenes ---------------------------------------------------------------------
def s01():
    s = Scene()
    s.kicker("Lo que nadie te explica")
    s.t(960, 300, "Lo que hace 5 años costaba", 44, MUTED, FS, anchor="ms")
    s.t(470, 620, "100 €", 200, WHITE, FX, anchor="ms")
    s.arrow(790, 555, 1040, 555)
    s.grad_t(1410, 620, "126 €", 200, YELLOW, (255, 170, 0), anchor="ms")
    s.t(470, 700, "finales de 2020", 32, MUTED, FS, anchor="ms")
    s.t(1410, 700, "junio de 2026", 32, MUTED, FS, anchor="ms")
    s.source("Estrategias de Inversión con datos del INE (subida acumulada del 26 %)")
    s.save("01_100_a_126.png")


def s02():
    s = Scene()
    s.kicker("Inflación en España · septiembre 2026")
    s.grad_t(120, 560, "4,9 %", 300, YELLOW, (255, 170, 0))
    s.t(124, 680, "La más alta desde febrero de 2023", 48, WHITE, FB)
    s.wrap(124, 750, "Los precios vuelven a acelerar cuando parecía que lo peor había pasado.", 34, 900)
    # stylised rising line on the right (illustrative, no values)
    pts = [(1180, 760), (1290, 700), (1380, 730), (1480, 640), (1570, 670), (1700, 470)]
    s.d.line([tuple(v * S for v in pt) for pt in pts], fill=CYAN, width=8 * S, joint="curve")
    s.gd.line([tuple(v * S for v in pt) for pt in pts], fill=CYAN, width=8 * S)
    s.arrow(1700, 470, 1740, 420, CYAN, 8, 40)
    s.source("INE, IPC septiembre 2026")
    s.save("02_inflacion_4_9.png")


def s03():
    s = Scene()
    s.kicker("Lo básico")
    s.t(120, 260, "¿Qué es el IPC?", 96, WHITE, FX)
    s.wrap(124, 330, "Una cesta con cientos de productos y servicios que compramos todos. Mide cuánto suben los precios de media en un año.", 34, 1500)
    items = [("Comida", g_bread), ("Luz", g_bolt), ("Transporte", g_car), ("Vivienda", g_house), ("Ropa", g_shirt)]
    for i, (lab, gl) in enumerate(items):
        cx = 330 + i * 315
        s.icon_circle(cx, 640, 100, lab, lerp(CYAN, VIOLET, i / 4), gl)
    s.source("INE")
    s.save("03_que_es_ipc.png")


def s04():
    s = Scene()
    s.kicker("El problema es que se acumula")
    s.t(120, 260, "Año a año, se suma", 84, WHITE, FX)
    steps = ["+5 %", "+8 %", "+3 %", "+4 %"]
    base_y = 880
    for i, lab in enumerate(steps):
        x0 = 160 + i * 290
        h = 150 + i * 120
        s.bar(x0, base_y - h, x0 + 220, base_y, lerp(CYAN, VIOLET, i / 3))
        s.t(x0 + 110, base_y - h - 30, lab, 56, WHITE, FX, anchor="ms")
    s.t(1590, 560, "= ¼ más caro", 64, YELLOW, FX, anchor="ms", glow=True)
    s.t(1590, 615, "en pocos años", 34, MUTED, FS, anchor="ms")
    s.t(960, 950, "Ejemplo ilustrativo", 24, DIM, FM, anchor="ms")
    s.save("04_se_acumula.png")


def s05():
    s = Scene()
    s.kicker("2020–2021 · La reapertura")
    s.t(120, 260, "Todos quieren comprar a la vez", 80, WHITE, FX)
    s.icon_circle(400, 600, 120, "Más demanda", CYAN, g_cart)
    s.icon_circle(960, 600, 120, "Menos oferta", VIOLET, g_ship)
    s.icon_circle(1520, 600, 120, "Precios más altos", YELLOW, g_euro)
    s.t(680, 615, "+", 90, MUTED, FX, anchor="ms")
    s.arrow(1130, 600, 1360, 600)
    s.wrap(124, 880, "Fábricas y barcos no daban abasto tras la pandemia.", 34, 1500)
    s.save("05_reapertura.png")


def s06():
    s = Scene()
    s.kicker("2022 · Crisis de la energía")
    s.t(120, 260, "Cuando sube la energía, sube todo", 76, WHITE, FX)
    s.icon_circle(400, 620, 140, "Gas y electricidad", YELLOW, g_bolt)
    targets = [(1150, 420, "Fábricas", g_factory), (1150, 640, "Transporte", g_car), (1150, 860, "Supermercado", g_cart)]
    for (x, y, lab, gl) in targets:
        s.arrow(560, 620, x - 110, y - 20, YELLOW, 6, 26)
        s.d.ellipse(p(x - 80, y - 100, x + 80, y + 60), outline=CYAN, width=3 * S, fill=(12, 18, 40))
        gl(s, x, y - 20, 40, CYAN)
        s.t(x + 120, y, lab, 40, WHITE, FB)
    s.save("06_energia.png")


def s07():
    s = Scene()
    s.kicker("La comida, de lo que más subió")
    s.grad_t(120, 470, "+28 %", 220, YELLOW, (255, 170, 0))
    s.t(124, 550, "Alimentos en España, 2021 a finales de 2024", 38, WHITE, FS)
    s.box(1150, 300, 1800, 700, VIOLET, glow=True)
    s.t(1475, 420, "Aceite de oliva", 44, WHITE, FB, anchor="ms")
    s.t(1475, 560, "+150 %", 120, VIOLET, FX, anchor="ms", glow=True)
    s.t(1475, 630, "en su peor momento, por la sequía", 28, MUTED, FS, anchor="ms")
    s.source("The Objective con datos de Eurostat")
    s.save("07_alimentos.png")


def s08():
    s = Scene()
    s.kicker("Diciembre 2020 → junio 2026")
    s.t(120, 260, "Los precios no vuelven atrás", 84, WHITE, FX)
    base = 900
    s.bar(420, base - 400, 720, base, MUTED, DIM, glow=False)
    s.bar(1100, base - 504, 1400, base, YELLOW, (255, 170, 0))
    s.t(570, base - 430, "100", 72, WHITE, FX, anchor="ms")
    s.t(1250, base - 534, "126", 72, YELLOW, FX, anchor="ms", glow=True)
    s.t(570, base + 50, "2020", 36, MUTED, FB, anchor="ms")
    s.t(1250, base + 50, "2026", 36, MUTED, FB, anchor="ms")
    s.t(1560, 560, "+26 %", 96, YELLOW, FX, glow=True)
    s.wrap(1564, 620, "Que la inflación baje solo significa que suben más despacio.", 30, 330)
    s.source("Estrategias de Inversión con datos del INE")
    s.save("08_acumulado_26.png")


def s09():
    s = Scene()
    s.kicker("Salario real")
    s.t(120, 260, "No importa cuánto ganas,", 76, WHITE, FX)
    s.t(120, 350, "sino lo que puedes comprar", 76, CYAN, FX, glow=True)
    s.grad_t(120, 700, "−2 %", 240, RED, (255, 160, 120))
    s.wrap(124, 790, "Los salarios reales en España siguen por debajo de 2021.", 40, 800, WHITE, FS)
    s.icon_circle(1400, 640, 150, "Tu compra en 2026", VIOLET, g_cart)
    s.source("OCDE, vía Vozpópuli (agosto 2026)")
    s.save("09_salario_real.png")


def s10():
    s = Scene()
    s.kicker("Enero a junio de 2026")
    s.t(120, 260, "Los sueldos vuelven a ir por detrás", 76, WHITE, FX)
    base, k = 880, 150
    s.bar(520, base - 2.5 * k, 820, base, CYAN)
    s.bar(1100, base - 3.0 * k, 1400, base, VIOLET)
    s.t(670, base - 2.5 * k - 30, "+2,5 %", 72, WHITE, FX, anchor="ms")
    s.t(1250, base - 3.0 * k - 30, "+3,0 %", 72, WHITE, FX, anchor="ms")
    s.t(670, base + 55, "Sueldos", 38, CYAN, FB, anchor="ms")
    s.t(1250, base + 55, "Precios", 38, VIOLET, FB, anchor="ms")
    s.source("Agencia Tributaria e INE, vía Vozpópuli")
    s.save("10_sueldos_vs_precios.png")


def s11():
    s = Scene()
    s.kicker("Vivienda · julio 2026")
    s.t(120, 260, "El alquiler, en máximo histórico", 76, WHITE, FX)
    s.grad_t(120, 600, "15,3 €/m²", 190, YELLOW, (255, 170, 0))
    s.t(124, 690, "Alquiler medio en España", 40, WHITE, FS)
    s.box(1300, 430, 1780, 690, CYAN, glow=True)
    s.t(1540, 570, "+6,8 %", 110, CYAN, FX, anchor="ms", glow=True)
    s.t(1540, 640, "en un año", 34, MUTED, FS, anchor="ms")
    s.source("idealista, vía Bolsamanía")
    s.save("11_alquiler.png")


def s12():
    s = Scene()
    s.kicker("¿Por qué vuelve a subir?")
    s.t(120, 260, "El culpable: la energía", 84, WHITE, FX)
    s.icon_circle(460, 620, 170, "Carburantes", YELLOW, g_pump)
    s.grad_t(820, 650, "+21,6 %", 220, YELLOW, (255, 170, 0))
    s.t(826, 730, "Productos energéticos, septiembre 2026", 36, WHITE, FS)
    s.source("INE (dato adelantado), vía Euronews")
    s.save("12_energia_21_6.png")


def s13():
    s = Scene()
    s.kicker("La subida se extiende")
    s.t(120, 260, "No es solo la gasolina", 84, WHITE, FX)
    for i, (num, lab, sub, c) in enumerate([("+5,8 %", "Alimentos frescos", "septiembre 2026", CYAN), ("3,1 %", "Inflación subyacente", "sin energía ni frescos", VIOLET)]):
        x0 = 160 + i * 820
        s.box(x0, 400, x0 + 740, 820, c, glow=True)
        s.t(x0 + 370, 610, num, 150, c, FX, anchor="ms", glow=True)
        s.t(x0 + 370, 700, lab, 44, WHITE, FB, anchor="ms")
        s.t(x0 + 370, 760, sub, 30, MUTED, FS, anchor="ms")
    s.source("INE")
    s.save("13_se_extiende.png")


def s14():
    s = Scene()
    s.kicker("Un detalle importante")
    s.t(120, 260, "El efecto escalón", 84, WHITE, FX)
    s.wrap(124, 330, "Comparamos con hace un año: si entonces los carburantes bajaron y ahora suben, el dato sale peor.", 34, 1600)
    for i, (yr, up) in enumerate([("Sept. 2025", False), ("Sept. 2026", True)]):
        cx = 600 + i * 720
        s.box(cx - 280, 470, cx + 280, 880, DIM)
        if up:
            s.arrow(cx - 120, 790, cx + 120, 580, YELLOW, 14, 50)
        else:
            s.arrow(cx - 120, 580, cx + 120, 790, CYAN, 14, 50)
        s.t(cx, 940, yr, 40, WHITE, FB, anchor="ms")
        s.t(cx, 530, "Carburantes bajan" if not up else "Carburantes suben", 30, MUTED, FS, anchor="ms")
    s.save("14_efecto_escalon.png")


def s15():
    s = Scene()
    s.kicker("¿Qué puede pasar ahora?")
    s.t(120, 260, "Depende del petróleo", 84, WHITE, FX)
    s.box(120, 400, 900, 860, CYAN, glow=True)
    s.box(1020, 400, 1800, 860, RED, glow=True)
    s.t(510, 500, "Si la energía se calma", 42, CYAN, FB, anchor="ms")
    s.wrap(170, 600, "La inflación debería moderarse en los próximos meses.", 38, 680, WHITE, FS)
    s.t(1410, 500, "Si sigue subiendo", 42, RED, FB, anchor="ms")
    s.wrap(1070, 600, "El BCE podría mantener o subir los tipos de interés: afecta a hipotecas y préstamos.", 38, 680, WHITE, FS)
    s.t(960, 950, "Escenarios posibles, no predicciones", 24, DIM, FM, anchor="ms")
    s.save("15_escenarios.png")


def s16():
    s = Scene()
    s.kicker("Qué significa para ti")
    s.t(960, 300, "Compara siempre con la inflación", 76, WHITE, FX, anchor="ms")
    cx, cy = 960, 640
    s.d.line(p(cx - 420, cy - 60, cx + 420, cy + 20), fill=MUTED, width=8 * S)
    s.d.polygon([tuple(v * S for v in pt) for pt in [(cx, cy - 20), (cx - 50, cy + 180), (cx + 50, cy + 180)]], fill=MUTED)
    s.box(cx - 640, cy - 200, cx - 260, cy - 70, CYAN, glow=True)
    s.t(cx - 450, cy - 118, "Tu dinero", 48, CYAN, FB, anchor="ms")
    s.box(cx + 260, cy - 120, cx + 640, cy + 10, VIOLET, glow=True)
    s.t(cx + 450, cy - 38, "Los precios", 48, VIOLET, FB, anchor="ms")
    s.t(960, 920, "Si tu dinero sube menos que los precios, estás perdiendo.", 40, YELLOW, FB, anchor="ms", glow=True)
    s.save("16_compara.png")


def s17():
    s = Scene()
    m = brand.compose_mark(s.im, 960 * S, 380 * S, 170 * S, S)
    s.im.paste(m)
    s.d = ImageDraw.Draw(s.im)
    s.t(960, 690, "Cómo Va el Mundo", 92, WHITE, FX, anchor="ms")
    s.d.rounded_rectangle(p(780, 740, 1140, 820), radius=40 * S, fill=(220, 38, 38))
    s.t(960, 795, "SUSCRÍBETE", 36, WHITE, FX, anchor="ms")
    s.t(960, 900, "Próximo vídeo: ¿Por qué los jóvenes no pueden comprarse una casa?", 34, MUTED, FS, anchor="ms")
    s.save("17_cierre.png")


SCENES = [s01, s02, s03, s04, s05, s06, s07, s08, s09, s10, s11, s12, s13, s14, s15, s16, s17]
if __name__ == "__main__":
    only = sys.argv[1:]
    for i, fn in enumerate(SCENES, 1):
        if not only or str(i) in only:
            fn()

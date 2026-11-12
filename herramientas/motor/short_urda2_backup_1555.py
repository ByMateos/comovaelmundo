"""Breaking-news Short v2: illustration on top (slow push-in), text card below, calm ambient music."""
import math, subprocess
from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageFilter

D = "/tmp/claude-0/-home-claude/3f8f79a9-c46c-53fb-baec-2bfb3165bcc1/scratchpad"
W, H, FPS = 1080, 1920, 25
OUT = "/home/claude/canal/short/short_accidente_urda_v2.mp4"
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
BG, CARD = (9, 14, 26), (17, 25, 44)
ACCENT = (214, 40, 57)
WHITE, MUTED, RED, AMBER, STEEL, CYAN = (244, 246, 250), (150, 162, 186), (232, 72, 85), (226, 184, 92), (120, 135, 165), (96, 176, 214)
IW, IH = 1080, 830  # illustration area (top)
ILL_Y = 225
PANEL_Y = 1150
SS = 2
_f = {}


def F(p, s):
    if (p, s) not in _f:
        _f[(p, s)] = ImageFont.truetype(p, int(s))
    return _f[(p, s)]


class Ill:
    """Illustration canvas, 15% larger than the area so it can push in."""
    def __init__(self, top=(18, 24, 40), bottom=(10, 12, 20)):
        self.w, self.h = int(IW * 1.15), int(IH * 1.15)
        self.im = Image.new("RGB", (self.w * SS, self.h * SS))
        d = ImageDraw.Draw(self.im)
        for y in range(self.h * SS):
            t = y / (self.h * SS)
            d.line([0, y, self.w * SS, y], fill=tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)))
        self.d = d

    def P(self, *v):
        return [x * SS for x in v]

    def pts(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def done(self):
        return self.im.resize((self.w, self.h), Image.LANCZOS)


# --- Spain map --------------------------------------------------------------
SPAIN = [(-9.3, 43.1), (-8.0, 43.7), (-5.8, 43.6), (-3.8, 43.45), (-1.8, 43.4), (-1.4, 43.05), (0.7, 42.8), (3.2, 42.4), (3.1, 41.9),
         (2.1, 41.3), (0.9, 41.0), (0.0, 40.0), (-0.3, 39.4), (0.2, 38.8), (-0.5, 38.3), (-0.8, 37.6), (-1.6, 37.2), (-2.2, 36.7),
         (-4.4, 36.7), (-5.6, 36.0), (-6.3, 36.8), (-7.4, 37.2), (-7.0, 38.0), (-7.3, 38.5), (-7.0, 39.0), (-7.5, 39.6),
         (-6.9, 40.2), (-6.8, 41.0), (-6.2, 41.6), (-6.6, 41.95), (-8.1, 41.8), (-8.9, 42.1)]
CITIES = {"Madrid": (-3.70, 40.42), "Toledo": (-4.02, 39.86), "Urda": (-3.71, 39.41), "Ciudad Real": (-3.93, 38.99), "Córdoba": (-4.78, 37.89), "Sevilla": (-5.98, 37.39)}


def ill_map(focus=False):
    c = Ill()
    w, h = c.w, c.h
    if focus:  # zoom centred on Urda
        clon, clat = -4.25, 38.95
        sx = w / 6.2
    else:  # whole peninsula, fitted and centred
        lons, lats = [p[0] for p in SPAIN], [p[1] for p in SPAIN]
        clon, clat = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
        sx = min(w * 0.94 / (max(lons) - min(lons)), h * 0.9 / ((max(lats) - min(lats)) * 1.25))
    sy = sx * 1.25

    def XY(lon, lat):
        return (w / 2 + (lon - clon) * sx, h / 2 - (lat - clat) * sy)
    c.d.polygon(c.pts([XY(*p) for p in SPAIN]), fill=(34, 42, 64), outline=(70, 84, 120))
    line = [XY(*CITIES[k]) for k in ("Madrid", "Toledo", "Urda", "Ciudad Real", "Córdoba", "Sevilla")]
    line[1] = XY(-3.95, 39.95)  # line passes near Toledo
    c.d.line(c.pts(line), fill=STEEL, width=8 * SS, joint="curve")
    for name in ("Madrid", "Ciudad Real", "Córdoba", "Sevilla"):
        x, y = XY(*CITIES[name])
        c.d.ellipse(c.P(x - 9, y - 9, x + 9, y + 9), fill=WHITE)
        if name == "Ciudad Real":  # label on the left so it never touches Urda's
            c.d.text(((x - 24) * SS, (y + 44) * SS), name, font=F(FS, 34 * SS), fill=MUTED, anchor="rs")
        else:
            c.d.text(((x + 22) * SS, (y + 12) * SS), name, font=F(FS, 34 * SS), fill=MUTED)
    x, y = XY(*CITIES["Urda"])
    for r, a in ((46, 60), (30, 120)):
        c.d.ellipse(c.P(x - r, y - r, x + r, y + r), outline=RED + (a,), width=5 * SS)
    c.d.ellipse(c.P(x - 14, y - 14, x + 14, y + 14), fill=RED)
    c.d.text(((x + 30) * SS, (y + 14) * SS), "Urda (Toledo)", font=F(FB, 40 * SS), fill=WHITE)
    return c.done()


def train(c, x, y, length, col, nose_right=True):
    h = 70
    c.d.rounded_rectangle(c.P(x, y - h, x + length, y), radius=18 * SS, fill=col)
    c.d.rectangle(c.P(x, y - 22, x + length, y - 14), fill=(250, 250, 250))
    for k in range(int(length // 70) - 1):
        wx = x + 40 + k * 70
        c.d.rounded_rectangle(c.P(wx, y - 58, wx + 44, y - 34), radius=6 * SS, fill=(26, 32, 50))
    if nose_right:
        c.d.polygon(c.pts([(x + length - 4, y - h), (x + length + 70, y - 12), (x + length - 4, y)]), fill=col)


def ill_trains():
    c = Ill((22, 26, 46), (12, 14, 24))
    w, h = c.w, c.h
    for k in range(60):  # hills
        pass
    c.d.polygon(c.pts([(0, h * 0.62)] + [(x, h * 0.6 + 30 * math.sin(x / 140)) for x in range(0, w + 1, 20)] + [(w, h), (0, h)]), fill=(28, 34, 52))
    ty = h * 0.72
    c.d.rectangle(c.P(0, ty + 6, w, ty + 14), fill=(90, 100, 125))
    c.d.rectangle(c.P(0, ty + 26, w, ty + 34), fill=(90, 100, 125))
    for x in range(0, w, 36):
        c.d.rectangle(c.P(x, ty + 2, x + 14, ty + 40), fill=(60, 66, 84))
    train(c, -40, ty, 430, (120, 30, 60))      # Iryo-like colour, no logo
    train(c, 520, ty, 420, (220, 225, 235))    # AVE-like colour, no logo
    c.d.text((w / 2 * SS, (h * 0.2) * SS), "Línea Madrid – Sevilla", font=F(FB, 46 * SS), fill=MUTED, anchor="ms")
    return c.done()


def ill_question():
    c = Ill()
    w, h = c.w, c.h
    c.d.ellipse(c.P(w / 2 - 190, h / 2 - 190, w / 2 + 190, h / 2 + 190), outline=AMBER, width=10 * SS)
    c.d.text((w / 2 * SS, (h / 2 + 110) * SS), "?", font=F(FBK, 300 * SS), fill=AMBER, anchor="ms")
    return c.done()


def ill_station():
    c = Ill((20, 26, 44), (12, 14, 22))
    w, h = c.w, c.h
    c.d.rounded_rectangle(c.P(160, 170, w - 160, h - 170), radius=26 * SS, fill=(18, 20, 30), outline=(70, 80, 110), width=4 * SS)
    c.d.text((w / 2 * SS, 250 * SS), "ALTA VELOCIDAD", font=F(FB, 44 * SS), fill=AMBER, anchor="ma")
    rows = [("Madrid", "Ciudad Real"), ("Ciudad Real", "Andalucía")]
    for i, (a, b) in enumerate(rows):
        y = 360 + i * 150
        c.d.text((w / 2 * SS, y * SS), f"{a}  →  {b}", font=F(FB, 46 * SS), fill=WHITE, anchor="ma")
        c.d.text((w / 2 * SS, (y + 62) * SS), "INTERRUMPIDO", font=F(FB, 38 * SS), fill=RED, anchor="ma")
    return c.done()


def ill_station_help():
    c = Ill()
    w, h = c.w, c.h
    names = ["Madrid-Atocha", "Sevilla-Santa Justa", "Córdoba"]
    for i, n in enumerate(names):
        y = 230 + i * 180
        c.d.rounded_rectangle(c.P(w / 2 - 330, y - 60, w / 2 + 330, y + 60), radius=24 * SS, fill=(22, 30, 52), outline=CYAN, width=4 * SS)
        c.d.ellipse(c.P(w / 2 - 290, y - 22, w / 2 - 246, y + 22), fill=CYAN)
        c.d.text(((w / 2 + 20) * SS, (y + 16) * SS), n, font=F(FB, 46 * SS), fill=WHITE, anchor="ms")
    return c.done()


def ill_phone():
    c = Ill()
    w, h = c.w, c.h
    cx, cy = w / 2, h / 2
    c.d.rounded_rectangle(c.P(cx - 150, cy - 270, cx + 150, cy + 270), radius=40 * SS, outline=CYAN, width=10 * SS)
    c.d.rounded_rectangle(c.P(cx - 50, cy - 240, cx + 50, cy - 225), radius=6 * SS, fill=CYAN)
    c.d.ellipse(c.P(cx - 24, cy + 200, cx + 24, cy + 248), outline=CYAN, width=6 * SS)
    c.d.text((cx * SS, (cy + 60) * SS), "112", font=F(FBK, 130 * SS), fill=WHITE, anchor="ms")
    for r in (220, 300):
        c.d.arc(c.P(cx + 120 - r / 3, cy - 150 - r / 3, cx + 120 + r / 3, cy - 150 + r / 3), -70, 20, fill=CYAN, width=8 * SS)
    return c.done()


def ill_blood():
    c = Ill()
    w, h = c.w, c.h
    cx, cy = w / 2 - 170, h / 2 + 20
    pts = [(cx + 150 * math.sin(a) * (1 if a < math.pi else 1), cy + 60 - 150 * math.cos(a)) for a in [i / 40 * 2 * math.pi for i in range(41)]]
    pts = [(cx, cy - 250)] + [(cx + 150 * math.cos(a), cy + 60 + 150 * math.sin(a)) for a in [math.radians(-30 + i * 6) for i in range(41)]]
    c.d.polygon(c.pts(pts), fill=RED)
    hx, hy = w / 2 + 200, h / 2 + 20
    c.d.rounded_rectangle(c.P(hx - 150, hy - 150, hx + 150, hy + 150), radius=30 * SS, outline=WHITE, width=10 * SS)
    c.d.rectangle(c.P(hx - 30, hy - 100, hx + 30, hy + 100), fill=WHITE)
    c.d.rectangle(c.P(hx - 100, hy - 30, hx + 100, hy + 30), fill=WHITE)
    return c.done()


def ill_ribbon():
    c = Ill((14, 16, 26), (6, 7, 12))
    w, h = c.w, c.h
    cx, cy = w / 2, h / 2 - 20
    col = (225, 225, 230)
    wdt = 52
    # two crossing bands forming an awareness ribbon (light ribbon on dark)
    c.d.line(c.pts([(cx - 150, cy + 260), (cx - 20, cy + 20), (cx + 40, cy - 120), (cx, cy - 210), (cx - 70, cy - 150), (cx - 20, cy + 20)]), fill=col, width=wdt * SS, joint="curve")
    c.d.line(c.pts([(cx + 150, cy + 260), (cx + 20, cy + 20), (cx - 40, cy - 120), (cx, cy - 210), (cx + 70, cy - 150), (cx + 20, cy + 20)]), fill=(190, 190, 198), width=wdt * SS, joint="curve")
    return c.done()


CARDS = [
    (5.0, ill_map, [("big", "Choque de dos trenes en Urda (Toledo)"), ("small", "Miércoles 28 de octubre · hacia las 8:54")]),
    (6.0, ill_trains, [("mid", "El AVE 2080 alcanzó por detrás al Iryo 6076 en la línea Madrid–Sevilla"), ("small", "Descarrilaron los dos últimos coches del Iryo · Ministerio de Transportes")]),
    (5.5, lambda: ill_map(True), [("red", "Al menos 64 fallecidos"), ("mid", "y 58 heridos"), ("small", "Gobierno de Castilla-La Mancha y García-Page, 14:20. Cifras provisionales")]),
    (5.0, ill_question, [("mid", "La causa aún se investiga"), ("small", "Óscar Puente: el sistema de seguridad LZB falló hacia las 8:30 en un tramo de 69 km")]),
    (5.5, ill_station, [("tag", "SI VIAJAS"), ("mid", "Circulación interrumpida entre Madrid, Ciudad Real y Andalucía"), ("small", "Renfe: cambios y anulaciones gratis · Iryo cancela sus trenes al sur")]),
    (6.0, ill_station_help, [("tag", "FAMILIAS"), ("mid", "Puntos de atención de Adif en Madrid-Atocha, Sevilla-Santa Justa y Córdoba")]),
    (6.5, ill_phone, [("tag", "TELÉFONOS"), ("mid", "Emergencias 112: 900 122 112"), ("mid", "Renfe (afectados): 900 10 10 20"), ("mid", "Iryo: 655 28 69 75")]),
    (5.5, ill_blood, [("mid", "No acudas a urgencias de Toledo, Ciudad Real y Mancha Centro salvo extrema urgencia"), ("mid", "Se pide donar sangre")]),
    (5.0, ill_ribbon, [("mid", "Nuestro recuerdo para las víctimas y sus familias")]),
]
STYLE = {"tag": (FB, 34, AMBER), "big": (FBK, 74, WHITE), "mid": (FB, 50, WHITE), "red": (FBK, 88, RED), "small": (FS, 34, MUTED)}


def wrap(d, text, font, maxw):
    out, line = [], ""
    for w in text.split():
        t = (line + " " + w).strip()
        if d.textlength(t, font=font) > maxw and line:
            out.append(line)
            line = w
        else:
            line = t
    out.append(line)
    return out


def base_card(items):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    blocks = []
    for kind, text in items:
        font, size, col = STYLE[kind]
        f = F(font, size)
        blocks.append((wrap(d, text, f, W - 200), f, size, col, kind))
    gap = 34
    total = sum(len(l) * s * 1.28 for l, f, s, c, k in blocks) + gap * (len(blocks) - 1)
    top = PANEL_Y
    # panel with thin accent rule on top
    d.rectangle([70, top - 56, W - 70, top + total + 56], fill=CARD)
    d.rectangle([70, top - 56, W - 70, top - 50], fill=ACCENT)
    y = top
    for lines, f, size, col, kind in blocks:
        for ln in lines:
            d.text((W / 2, y), ln, font=f, fill=col, anchor="mt")
            y += size * 1.28
        y += gap
    d.text((W / 2, 1735), "Fuentes: Gobierno de CLM, Mº de Transportes, Adif y Renfe · 15:55", font=F(FS, 28), fill=MUTED, anchor="mt")
    d.text((W / 2, 1785), "CÓMO VA EL MUNDO", font=F(FB, 26), fill=(90, 104, 136), anchor="mt")
    return im


def header(im):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 205], fill=BG)
    d.rectangle([120, 204, W - 120, 205], fill=(40, 52, 80))
    d.rectangle([0, 0, W, 10], fill=ACCENT)
    w = d.textlength("ÚLTIMA HORA", font=F(FBK, 34)) + 60
    d.rectangle([W / 2 - w / 2, 64, W / 2 + w / 2, 118], fill=ACCENT)
    d.text((W / 2, 91), "ÚLTIMA HORA", font=F(FBK, 34), fill=WHITE, anchor="mm")
    d.text((W / 2, 150), "Accidente ferroviario · Urda (Toledo)", font=F(FS, 30), fill=MUTED, anchor="mt")


def frame(card, ill, u):
    z = 1.0 + 0.12 * u
    cw, ch = ill.width / z, ill.height / z
    box = ((ill.width - cw) / 2, (ill.height - ch) / 2, (ill.width + cw) / 2, (ill.height + ch) / 2)
    part = ill.resize((IW, IH), Image.BILINEAR, box=box)
    # fade illustration bottom into background
    g = Image.linear_gradient("L").resize((IW, IH))
    mask = ImageChops.multiply(g.point(lambda v: 255 if v < 190 else int(255 * (255 - v) / 65)),
                               g.point(lambda v: 255 if v > 30 else int(255 * v / 30)))
    out = card.copy()
    out.paste(part, (0, ILL_Y), mask)
    header(out)
    return out


def main():
    total = sum(c[0] for c in CARDS)
    subprocess.run(["python3", f"{D}/ambient.py", str(total + 0.5), f"{D}/ambient_urda.wav"], check=True)
    prepared = [(dur, base_card(items), ill()) for dur, ill, items in CARDS]
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-i", f"{D}/ambient_urda.wav", "-filter:a", "volume=0.55", "-shortest",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    prev = Image.new("RGB", (W, H), BG)
    fade = int(0.4 * FPS)
    for i, (dur, card, ill) in enumerate(prepared):
        n = int(dur * FPS)
        last = None
        for k in range(n):
            img = frame(card, ill, k / n)
            if k < fade:
                img = Image.blend(prev, img, k / fade)
            ff.stdin.write(img.tobytes())
            last = img
            if k == n // 2:
                img.resize((360, 640)).save(f"{D}/urda2_{i}.jpg")
        prev = last
    ff.stdin.close()
    ff.wait()
    print("ok", total)


main()

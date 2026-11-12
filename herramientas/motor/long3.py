"""Long video 3 (16:9): Pexels clips background + data cards + karaoke captions + voice.
usage: long3.py bg   -> builds bg.mp4 from clips
       long3.py ov t0 t1 out.mp4 -> renders composited segment
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style_a2 as S
from style_a2 import F, FBK, FXB, FB, FS, FM, WHITE, SOFT, DIM, YEL, AMB, CYAN, VIO

D = "/home/claude/canal/video3/"
W, H, FPS = 1920, 1080, 30
T = json.load(open(D + "timing.json"))
P = T["paras"]; END = T["end"] + 1.2
WORDS = json.load(open(D + "words_all.json"))
pe = P[1:] + [END]
C = lambda n: D + "clips/" + n

# clips per paragraph (split evenly)
CLIPS = [
    ["01_red_sunset.mp4", "10_ciudad_noche.mp4"],
    ["04_central_aerea.mp4", "17_central_equipo.mp4"],
    ["02_red_silueta.mp4", "16_monedas.mp4"],
    ["17_central_equipo.mp4", "06_eolica.mp4", "04_central_aerea.mp4"],
    ["07_llama_gas.mp4", "08_barco_carga.mp4", "09_barcos_mar.mp4"],
    ["09_barcos_mar.mp4", "07_llama_gas.mp4"],
    ["11_huerto_solar.mp4", "05_casa_solar.mp4", "10_ciudad_noche.mp4"],
    ["16_monedas.mp4", "05_casa_solar.mp4", "01_red_sunset.mp4"],
    ["02_red_silueta.mp4"],
    ["15_gasolinera.mp4", "07_llama_gas.mp4"],
    ["13_lavadora.mp4", "12_coche_carga.mp4", "14_termostato.mp4", "10_ciudad_noche.mp4"],
    ["08_barco_carga.mp4", "09_barcos_mar.mp4"],
    ["11_huerto_solar.mp4", "10_ciudad_noche.mp4"],
    ["01_red_sunset.mp4"],
]


def build_bg():
    os.makedirs(D + "bgparts", exist_ok=True)
    lst = []
    k = 0
    for i, cl in enumerate(CLIPS):
        dur = pe[i] - P[i]
        piece = dur / len(cl)
        for j, c in enumerate(cl):
            out = D + f"bgparts/{k:03d}.mp4"; k += 1
            d = piece if j < len(cl) - 1 else dur - piece * (len(cl) - 1)
            vf = (f"fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},"
                  f"eq=brightness=-0.10:saturation=0.85")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", C(c), "-t", f"{d:.3f}",
                            "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", out], check=True)
            lst.append(out)
    with open(D + "bglist.txt", "w") as f:
        for p in lst: f.write(f"file '{p}'\n")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", D + "bglist.txt", "-c", "copy", D + "bg.mp4"], check=True)
    print("bg ok", len(lst))


# ---------------- overlay drawing ----------------
def ease(x):
    x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3


def card(w, h, alpha=0.66):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 36, fill=(10, 14, 30, int(255 * alpha)), outline=(140, 220, 255, 90), width=2)
    return im


def gtext(im, xy, txt, font, c1=YEL, c2=AMB, anchor="mm"):
    rgb = Image.new("RGB", im.size, (0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).text(xy, txt, font=font, fill=255, anchor=anchor)
    bb = m.getbbox()
    if not bb: return
    g = Image.new("RGB", im.size, c1); gd = ImageDraw.Draw(g)
    for y in range(bb[1], bb[3] + 1):
        t = (y - bb[1]) / max(1, bb[3] - bb[1])
        gd.line([(bb[0], y), (bb[2], y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)))
    glow = m.filter(ImageFilter.GaussianBlur(28)).point(lambda v: int(v * 0.5))
    gl = Image.new("RGBA", im.size, c2 + (0,)); gl.putalpha(glow)
    im.alpha_composite(gl)
    layer = g.convert("RGBA"); layer.putalpha(m)
    im.alpha_composite(layer)


def kick(d, x, y, txt, col=CYAN, anchor="lm"):
    S.tracked(d, (x, y), txt, F(FB, 30), col, track=5, anchor="mm" if anchor == "mm" else "mm") if anchor == "mm" else d.text((x, y), " ".join(txt), font=F(FB, 28), fill=col, anchor=anchor)


def big_card(kicker, value, note, sub=None, c1=YEL, c2=AMB, w=1100):
    h = 400 if sub else 340
    im = card(w, h)
    d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 62), kicker, F(FB, 30), (170, 230, 255), track=5)
    gtext(im, (w / 2, 175), value, F(FBK, 150), c1, c2)
    d = ImageDraw.Draw(im)
    d.text((w / 2, 285), note, font=F(FS, 38), fill=(220, 226, 240), anchor="mm")
    if sub:
        d.text((w / 2, 345), sub, font=F(FM, 32), fill=SOFT, anchor="mm")
    return im


def title_card(kicker, title, sub=None, w=1300):
    ft = F(FXB, 76)
    lines = S_wrap(title, ft, w - 120)
    h = 130 + 92 * len(lines) + (70 if sub else 20)
    im = card(w, h)
    d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 62), kicker, F(FB, 30), (170, 230, 255), track=5)
    for i, l in enumerate(lines):
        d.text((w / 2, 140 + 92 * i), l, font=ft, fill=WHITE, anchor="mm")
    if sub:
        d.text((w / 2, 140 + 92 * len(lines) + 10), sub, font=F(FS, 36), fill=SOFT, anchor="mm")
    return im


def S_wrap(txt, font, maxw):
    out, cur = [], ""
    for w in txt.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) > maxw and cur:
            out.append(cur); cur = w
        else:
            cur = t
    out.append(cur); return out


def bars_card(kicker, rows, unit="", w=1200, maxv=None, dec=0):
    h = 150 + 110 * len(rows)
    im = card(w, h)
    d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 62), kicker, F(FB, 30), (170, 230, 255), track=5)
    mv = maxv or max(r[1] for r in rows)
    return im, mv


def draw_bars(im, rows, mv, prog, unit="", dec=0, x0=340, x1=None):
    w = im.width; x1 = x1 or w - 200
    d = ImageDraw.Draw(im)
    for i, (lab, v, hl) in enumerate(rows):
        y = 140 + 110 * i
        u = ease((prog - i * 0.12) / 0.6)
        d.text((60, y + 22), lab, font=F(FB, 40), fill=WHITE if hl else (215, 220, 235), anchor="lm")
        d.rounded_rectangle((x0, y + 4, x1, y + 40), 18, fill=(255, 255, 255, 26))
        bw = (x1 - x0) * (v / mv) * u
        if bw > 8:
            d.rounded_rectangle((x0, y + 4, x0 + bw, y + 40), 18, fill=(YEL + (255,)) if hl else (120, 200, 255, 230))
        val = (f"{v * u:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")) + unit
        d.text((w - 50, y + 22), val, font=F(FXB, 40), fill=YEL if hl else WHITE, anchor="rm")


def list_card(kicker, items, w=1250):
    h = 140 + 96 * len(items)
    im = card(w, h)
    d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 62), kicker, F(FB, 30), (170, 230, 255), track=5)
    return im


# Paragraph overlays: list of (t_rel_start, builder) ; builder(prog)->RGBA image ; placed centered at y
def merit_card(prog):
    w, h = 1400, 470
    im = card(w, h); d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 60), "CÓMO SE FIJA EL PRECIO", F(FB, 30), (170, 230, 255), track=5)
    items = [("Solar", (255, 210, 63), 0.12), ("Eólica", (120, 220, 255), 0.18), ("Nuclear", (160, 140, 255), 0.3), ("Gas", (255, 110, 90), 0.85)]
    x = 80
    for i, (n, col, hgt) in enumerate(items):
        u = ease((prog - i * 0.15) / 0.5)
        bh = 260 * hgt * u
        d.rounded_rectangle((x, 400 - bh, x + 260, 400), 16, fill=col + (230,))
        d.text((x + 130, 430), n, font=F(FB, 36), fill=WHITE, anchor="mm")
        x += 310
    if prog > 0.7:
        a = int(255 * ease((prog - 0.7) / 0.25))
        d.line((70, 400 - 260 * 0.85, w - 70, 400 - 260 * 0.85), fill=(255, 110, 90, a), width=4)
        d.text((w - 80, 400 - 260 * 0.85 - 30), "La última marca el precio de todas", font=F(FXB, 36), fill=(255, 170, 150, a), anchor="rm")
    return im


def daynight_card(prog):
    w, h = 1300, 440
    im = card(w, h); d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 60), "PRECIO DE LA LUZ EN UN DÍA", F(FB, 30), (170, 230, 255), track=5)
    pts = []
    for k in range(25):
        hr = k
        v = 0.55 + 0.25 * math.cos((hr - 3) / 24 * 2 * math.pi) - 0.55 * math.exp(-((hr - 14) / 3.2) ** 2) + 0.38 * math.exp(-((hr - 21) / 2.2) ** 2)
        pts.append((90 + k * (w - 180) / 24, 360 - 230 * max(0.02, min(1, v))))
    n = max(2, int(len(pts) * ease(prog / 0.8)))
    d.line(pts[:n], fill=(255, 210, 63, 255), width=7, joint="curve")
    d.line((90, 362, w - 90, 362), fill=(255, 255, 255, 60), width=2)
    for hr, lab in [(0, "0 h"), (6, "6 h"), (12, "12 h"), (18, "18 h"), (24, "24 h")]:
        d.text((90 + hr * (w - 180) / 24, 395), lab, font=F(FM, 28), fill=SOFT, anchor="mm")
    if prog > 0.55:
        a = int(255 * ease((prog - 0.55) / 0.2))
        d.text((90 + 14 * (w - 180) / 24, 300), "☀ casi 0 €", font=F(FXB, 38), fill=(140, 255, 170, a), anchor="mm")
        d.text((90 + 21 * (w - 180) / 24, 110), "noche: hasta 300 €", font=F(FXB, 36), fill=(255, 150, 130, a), anchor="mm")
    return im


def tips_card(prog, upto):
    items = ["1. Usa la luz en las horas baratas", "2. Revisa la potencia contratada", "3. Compara tarifas con tu factura", "4. Termostato a 20 °C y nada en espera"]
    w = 1250; im = list_card("QUÉ PUEDES HACER TÚ", items, w); d = ImageDraw.Draw(im)
    for i, it in enumerate(items[:upto]):
        d.text((80, 150 + 96 * i), it, font=F(FXB, 50), fill=WHITE if i == upto - 1 else (200, 206, 225), anchor="lm")
    return im


def summary_card(prog):
    items = ["La luz está cara porque el gas está caro", "Crisis en Oriente Medio y menos reservas", "Faltan baterías para la energía solar"]
    w = 1400; im = list_card("RESUMEN", items, w); d = ImageDraw.Draw(im)
    for i, it in enumerate(items):
        u = ease((prog - i * 0.22) / 0.25)
        if u > 0:
            d.text((80 + (1 - u) * 40, 150 + 96 * i), "✓  " + it, font=F(FXB, 48), fill=(255, 255, 255, int(255 * u)), anchor="lm")
    return im


def scen_card(prog):
    w, h = 1400, 380
    im = card(w, h); d = ImageDraw.Draw(im)
    S.tracked(d, (w / 2, 60), "¿QUÉ PUEDE PASAR?", F(FB, 30), (170, 230, 255), track=5)
    d.text((90, 160), "▼  Podría bajar", font=F(FXB, 56), fill=(140, 255, 170), anchor="lm")
    d.text((90, 225), "si se normaliza Ormuz o llega más gas licuado", font=F(FS, 34), fill=SOFT, anchor="lm")
    if prog > 0.4:
        d.text((90, 295), "▲  Podría subir", font=F(FXB, 56), fill=(255, 150, 130), anchor="lm")
        d.text((90, 350), "si el invierno es frío y las reservas caen", font=F(FS, 34), fill=SOFT, anchor="lm")
    return im


def cta_card(prog):
    w, h = 1100, 460
    im = card(w, h, 0.72); d = ImageDraw.Draw(im)
    m, a = S.logo_mark(70); lg = m.convert("RGBA"); lg.putalpha(a)
    im.alpha_composite(lg, (w // 2 - lg.width // 2, 120 - lg.height // 2))
    d.text((w / 2, 250), "Una noticia al día, explicada fácil", font=F(FXB, 52), fill=WHITE, anchor="mm")
    pulse = 1 + 0.04 * math.sin(prog * 25)
    bw, bh = 460 * pulse, 104 * pulse
    d.rounded_rectangle((w / 2 - bw / 2, 360 - bh / 2, w / 2 + bw / 2, 360 + bh / 2), 52, fill=(240, 36, 64, 255))
    d.text((w / 2, 360), "SUSCRÍBETE", font=F(FBK, 46), fill=WHITE, anchor="mm")
    return im


def at(word_text, after=0):
    """absolute time of first word matching (case-insensitive prefix) after time `after`"""
    for w in WORDS:
        if w["start"] >= after and w["text"].lower().strip("¿?¡!.,:;").startswith(word_text.lower()):
            return w["start"]
    return after


# overlay timeline: list of (abs_start, abs_end, builder(prog, t_rel))
TL = []
def add(t0, t1, fn, y=420):
    TL.append((t0, t1, fn, y))

add(P[0] + 0.0, P[1] - 0.2, lambda p, r: big_card("RECIBO MEDIO DE LUZ · OCTUBRE", "112 €", "+32 % que hace un año", "Tarifa regulada (PVPC) · FACUA"))
add(P[1] + 0.3, P[2] - 0.2, lambda p, r: big_card("MERCADO MAYORISTA · OCTUBRE", "166,65 €", "por megavatio hora", "Máximo desde 2022 · oct. 2025: 75,78 €"))
_r3 = [("Febrero", 16.41, False), ("Julio", 104.75, False), ("Agosto", 118.25, False), ("Octubre", 166.65, True)]
def b3(p, r):
    im, mv = bars_card("PRECIO MEDIO DEL MES (€/MWh)", _r3); draw_bars(im, _r3, mv, p * 2.2, ""); return im
add(P[2] + 0.2, P[3] - 0.2, b3)
add(P[3] + 0.2, P[4] - 0.2, lambda p, r: merit_card(min(1, p * 1.6)))
t5b = at("la", P[4] + 8)  # razón principal ...
add(P[4] + 0.2, at("razón", P[4]) - 0.1, lambda p, r: big_card("GAS EN EUROPA", "×3", "cerca de 100 € por MWh", "El triple que hace un año"))
add(at("razón", P[4]), P[5] - 0.2, lambda p, r: title_card("ESTRECHO DE ORMUZ", "Por aquí pasa 1/5 del gas licuado y del petróleo del mundo", "La crisis en Oriente Medio dispara el precio"))
_r6 = [("Hace un año", 82.86, False), ("Ahora", 74.96, True)]
def b6(p, r):
    im, mv = bars_card("RESERVAS DE GAS EN LA UE (%)", _r6); draw_bars(im, _r6, 100, p * 2.5, " %", 1); return im
add(P[5] + 0.2, P[6] - 0.2, b6)
add(P[6] + 0.2, at("detalle", P[6]) - 0.1, lambda p, r: big_card("ENERGÍA SOLAR EN 2026", "+17 %", "más producción que el año pasado", c1=(140, 255, 170), c2=(56, 225, 255)))
add(at("detalle", P[6]), at("falta", P[6]) - 0.1, lambda p, r: daynight_card(min(1, p * 1.5)))
add(at("falta", P[6]), P[7] - 0.2, lambda p, r: title_card("LO QUE FALTA", "Baterías para guardar la energía del mediodía", "Y usarla por la noche"))
_r8 = [("Oct. 2025", 84.83, False), ("Oct. 2026", 111.75, True)]
def b8(p, r):
    im, mv = bars_card("RECIBO MEDIO PVPC · FACUA (€)", _r8); draw_bars(im, _r8, 120, p * 3, " €", 2); return im
add(P[7] + 0.2, at("mercado", P[7] + 20) - 0.1, b8)
add(at("mercado", P[7] + 20), P[8] - 0.2, lambda p, r: title_card("MERCADO LIBRE", "Con precio fijo quizá no lo notes aún", "Pero al renovar, es probable que te suban"))
add(P[8] + 0.2, P[9] - 0.2, lambda p, r: big_card("IVA DE LA LUZ EN NOVIEMBRE", "21 %", "La rebaja al 10 % no se activa", "Solo si la luz sube más de un 15 % en un año"))
_r10 = [("Gasolina 95", 1.722, False), ("Diésel", 1.896, True)]
def b10(p, r):
    im, mv = bars_card("PRECIO POR LITRO (3 NOV.)", _r10); draw_bars(im, _r10, 2.0, p * 3, " €", 3); return im
add(P[9] + 0.2, at("aun", P[9]) - 0.1, lambda p, r: big_card("REBAJA EN CARBURANTES", "20 cént.", "por litro, también en noviembre", "Gasolina +27,5 % y diésel +34 % en un año"))
add(at("aun", P[9]), at("bombona", P[9]) - 0.1, b10)
add(at("bombona", P[9]), P[10] - 0.2, lambda p, r: big_card("BOMBONA DE BUTANO", "19,55 €", "precio máximo", "Congelado hasta junio de 2027"))
tt = [at("primero", P[10]), at("segundo", P[10]), at("tercero", P[10]), at("cuarto", P[10])]
for k in range(4):
    add(tt[k], (tt[k + 1] if k < 3 else P[11]) - 0.1, (lambda kk: (lambda p, r: tips_card(p, kk + 1)))(k))
add(P[11] + 0.2, P[12] - 0.2, lambda p, r: scen_card(p * 1.8))
add(P[12] + 0.2, P[13] - 0.2, lambda p, r: summary_card(p * 1.3))
add(P[13] + 0.2, END, lambda p, r: cta_card(r))

# ---------------- captions ----------------
GROUPS, cur = [], []
for i, w in enumerate(WORDS):
    cur.append(i)
    end = w["text"].rstrip()[-1:] in ".,?!:;…"
    gap = i + 1 < len(WORDS) and WORDS[i + 1]["start"] - w["end"] > 0.35
    if len(cur) >= 7 or end or gap:
        GROUPS.append(cur); cur = []
if cur: GROUPS.append(cur)
CF = F(FB, 46)


def caption_layer(t):
    g = None
    for gi, G in enumerate(GROUPS):
        nxt = GROUPS[gi + 1][0] if gi + 1 < len(GROUPS) else None
        tend = WORDS[nxt]["start"] - 0.05 if nxt is not None else WORDS[G[-1]]["end"] + 0.5
        if WORDS[G[0]]["start"] - 0.08 <= t < tend:
            g = G; break
    if g is None: return None
    toks = [WORDS[j]["text"].strip() for j in g]
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    sp = d0.textlength(" ", font=CF)
    ws = [d0.textlength(s, font=CF) for s in toks]
    tot = sum(ws) + sp * (len(ws) - 1)
    lay = Image.new("RGBA", (W, 140), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((W / 2 - tot / 2 - 30, 20, W / 2 + tot / 2 + 30, 110), 26, fill=(0, 0, 0, 150))
    x = W / 2 - tot / 2
    for j, s, wd in zip(g, toks, ws):
        wo = WORDS[j]
        col = (255, 214, 72) if wo["start"] - 0.03 <= t < wo["end"] + 0.05 else ((255, 255, 255) if t >= wo["end"] else (200, 205, 220))
        d.text((x, 65), s, font=CF, fill=col, anchor="lm")
        x += wd + sp
    return lay


# static chrome: vignette + logo + series tag
def chrome():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    g = np.clip((r - 0.55) / 0.7, 0, 1) * 170
    g += np.clip((yy - H * 0.72) / (H * 0.28), 0, 1) * 110
    v = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8))
    sh = Image.new("RGBA", (W, H), (4, 6, 14, 255)); sh.putalpha(v)
    im.alpha_composite(sh)
    m, a = S.logo_mark(30); lg = m.convert("RGBA"); lg.putalpha(a)
    im.alpha_composite(lg, (90 - lg.width // 2, 80 - lg.height // 2))
    d = ImageDraw.Draw(im)
    d.text((132, 66), "Cómo Va el Mundo", font=F(FB, 32), fill=WHITE, anchor="lm")
    d.text((132, 100), "Explicado fácil", font=F(FM, 24), fill=SOFT, anchor="lm")
    return im
CHROME = chrome()

_cache = {}
def overlay(t):
    im = CHROME.copy()
    for (t0, t1, fn, y) in TL:
        if t0 <= t < t1:
            dur = t1 - t0
            rel = t - t0
            p = rel / max(0.1, min(dur, 3.0))
            a = ease(rel / 0.45) * (1 - ease((t - (t1 - 0.35)) / 0.35))
            key = (t0, round(min(p, 1.0) * 30) if p < 1.05 else 30, int(rel * 3) if fn.__name__ == "<lambda>" and t0 >= P[13] else 0)
            c = _cache.get(key)
            if c is None:
                c = fn(min(p, 1.0), rel); _cache[key] = c
                if len(_cache) > 400: _cache.clear()
            if a < 0.999:
                c = c.copy(); c.putalpha(c.getchannel("A").point(lambda v: int(v * a)))
            im.alpha_composite(c, (int(W / 2 - c.width / 2), int(y - c.height / 2 + (1 - a) * 30)))
    cap = caption_layer(t)
    if cap is not None:
        im.alpha_composite(cap, (0, H - 175))
    return im


def render(t0, t1, out):
    n0, n1 = int(round(t0 * FPS)), int(round(t1 * FPS))
    dec = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-ss", f"{t0:.3f}", "-i", D + "bg.mp4", "-t", f"{t1 - t0:.3f}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    fb = W * H * 3
    last = None
    for n in range(n0, n1):
        raw = dec.stdout.read(fb)
        if len(raw) < fb:
            raw = last if last is not None else bytes(fb)
        last = raw
        bg = np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32)
        ov = np.asarray(overlay(n / FPS), dtype=np.float32)
        a = ov[..., 3:4] / 255.0
        fr = bg * (1 - a) + ov[..., :3] * a
        enc.stdin.write(fr.astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.kill(); dec.wait()


def _main():
    if sys.argv[1] == "bg60":
        build_bg60(); return
    if sys.argv[1] == "ovl":
        render_overlay(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]); return
    if sys.argv[1] == "bg":
        build_bg()
    elif sys.argv[1] == "still":
        t = float(sys.argv[2]); overlay(t).save(sys.argv[3])
    else:
        render(float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])


# ================= 60 fps pipeline =================
XF = 0.6  # crossfade seconds

def build_bg60():
    os.makedirs(D + "bg60", exist_ok=True)
    pieces = []
    for i, cl in enumerate(CLIPS):
        dur = pe[i] - P[i]
        piece = dur / len(cl)
        for j, c in enumerate(cl):
            d = piece if j < len(cl) - 1 else dur - piece * (len(cl) - 1)
            pieces.append((c, d))
    outs = []
    for k, (c, d) in enumerate(pieces):
        L = d + (XF if k < len(pieces) - 1 else 0)
        out = D + f"bg60/{k:03d}.mp4"
        vf = f"fps=60,scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-stream_loop", "-1", "-i", C(c), "-t", f"{L:.3f}", "-vf", vf, "-an",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", out], check=True)
        outs.append((out, d))
    # xfade chain + cinematic grade + light grain
    args = ["ffmpeg", "-loglevel", "error", "-y"]
    for o, _ in outs: args += ["-i", o]
    fc, prev, acc = [], "[0:v]", 0.0
    for k in range(1, len(outs)):
        acc += outs[k - 1][1]
        lab = f"[x{k}]"
        fc.append(f"{prev}[{k}:v]xfade=transition=fade:duration={XF}:offset={acc:.3f}{lab}")
        prev = lab
    fc.append(f"{prev}eq=brightness=-0.07:contrast=1.05:saturation=0.9,"
              f"colorbalance=rs=-0.03:gs=0.0:bs=0.05:rh=0.04:gh=0.01:bh=-0.03,"
              f"noise=alls=5:allf=t,format=yuv420p[v]")
    args += ["-filter_complex", ";".join(fc), "-map", "[v]", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", D + "bg60.mp4"]
    subprocess.run(args, check=True)
    print("bg60 ok", len(outs))


def render_overlay(t0, t1, out, fps=30):
    n0, n1 = int(round(t0 * fps)), int(round(t1 * fps))
    enc = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
                            "-c:v", "qtrle", out], stdin=subprocess.PIPE)
    for n in range(n0, n1):
        enc.stdin.write(overlay(n / fps).tobytes())
    enc.stdin.close(); enc.wait()


if __name__ == "__main__":
    _main()

"""Long video 4 (16:9): elecciones 29N. usage: long4.py timing.json out.mp4 [workers]
timing.json: {"starts":[t per para], "end": t}
"""
import json, os, sys, subprocess, math, glob
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = "/home/claude/canal/video4/"
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FXB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
FM = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
_f = {}
def F(p, s):
    if (p, s) not in _f: _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]
W, H, FPS = 1920, 1080, 30
INK = (7, 9, 18); WHITE = (246, 247, 251); SOFT = (176, 184, 206); DIM = (110, 118, 146)
YEL = (255, 210, 63); CYAN = (56, 225, 255); VIO = (132, 94, 255)

STARTS = []
G = json.load(open(D + "guion.json"))
P = G["paras"]
SECS = ["VIVIENDA", "IMPUESTOS", "SUELDOS", "PENSIONES", "ENERGÍA"]
PHOT = {
    "INTRO": ["6_", "66_", "11_"], "VIVIENDA": ["12_", "19_", "14_", "20_", "16_", "12_"],
    "IMPUESTOS": ["31_", "24_", "25_", "32_", "29_", "24_"], "SUELDOS": ["36_", "37_", "31_", "36_", "37_", "32_"],
    "PENSIONES": ["42_", "45_", "42_", "45_", "32_", "42_"], "ENERGÍA": ["48_", "54_", "61_", "56_", "65_", "55_"],
    "RESUMEN": ["69_", "6_"],
}
F2 = sorted(glob.glob(D + "fotos2/*.jpg"))
def P2(*pre): return [f for f in F2 if any(os.path.basename(f).startswith(x) for x in pre)]
FOTOS = {os.path.basename(f).split("_")[0] + "_": f for f in glob.glob(D + "fotos/*.jpg")}
LOGO = Image.open("/home/claude/canal/logo_sinfondo_512.png").convert("RGBA").resize((64, 64), Image.LANCZOS)
FOOT = "Fuentes: programa del PP · Infobae · Forbes · Telecinco · Demócrata · Fotocasa · webs de los partidos · 12/11/2026"

def eo(t): t = min(1, max(0, t)); return 1 - (1 - t) ** 3

_bg = {}
def photo(key):
    if key not in _bg:
        if len(_bg) > 12: _bg.pop(next(iter(_bg)))
        im = Image.open(FOTOS[key] if key in FOTOS else key).convert("RGB")
        s = max(2112 / im.width, 1188 / im.height); im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
        x, y = (im.width - 2112) // 2, (im.height - 1188) // 2; im = im.crop((x, y, x + 2112, y + 1188))
        a = np.asarray(im).astype(np.float32)
        g = a.mean(axis=2, keepdims=True); a = g + (a - g) * 0.75  # desaturate
        yy, xx = np.mgrid[0:1188, 0:2112]
        v = 0.36 - 0.15 * (xx / 2112)  # darker on the right where cards live
        a = a * v[..., None] + np.array(INK, np.float32) * (1 - v[..., None]) * 0.6
        _bg[key] = Image.fromarray(a.clip(0, 255).astype(np.uint8))
    return _bg[key]

def kb(key, t, dur, seed):
    """smooth sub-pixel Ken Burns (float crop box, bicubic)"""
    im = photo(key); p = min(1.0, max(0.0, t / max(dur, 1)))
    z = 1.0 + 0.07 * p if seed % 2 == 0 else 1.07 - 0.07 * p
    w, h = 2112 / z, 1188 / z
    dx = (2112 - w) * (0.5 + 0.35 * math.sin(seed * 1.7)); dy = (1188 - h) * (0.5 + 0.25 * math.cos(seed * 1.3))
    return im.resize((W, H), Image.BICUBIC, box=(dx, dy, dx + w, dy + h))

def text_img(txt, font, fill):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); w = d.textlength(txt, font=font); a, de = font.getmetrics()
    im = Image.new("RGBA", (int(w) + 4, a + de + 4), (0, 0, 0, 0)); ImageDraw.Draw(im).text((2, 2), txt, font=font, fill=fill)
    return im

def wrap(txt, font, maxw):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); out, cur = [], ""
    for wd in txt.split():
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: out.append(cur); cur = wd
    if cur: out.append(cur)
    return out

def paste(base, im, x, y, a=1.0):
    if a <= 0: return
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    base.alpha_composite(im, (int(x), int(y)))

def rrect(w, h, r, fill, outline=None, width=0):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); ImageDraw.Draw(im).rounded_rectangle([0, 0, w - 1, h - 1], r, fill=fill, outline=outline, width=width); return im

# ---------- static chrome ----------
def chrome(sec):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    im.alpha_composite(LOGO, (64, 40))
    d.text((142, 46), "Cómo Va el Mundo", font=F(FB, 26), fill=WHITE)
    d.text((142, 78), "ELECCIONES 29N · QUÉ PROPONE CADA PARTIDO", font=F(FS, 18), fill=SOFT)
    x = W - 64
    for i, s in reversed(list(enumerate(SECS))):
        f = F(FB, 18); tw = d.textlength(s, font=f); on = (s == sec)
        bw = int(tw + 36); x -= bw
        d.rounded_rectangle([x, 50, x + bw, 88], 19, fill=(255, 210, 63, 255) if on else (255, 255, 255, 22), outline=None)
        d.text((x + 18, 58), s, font=f, fill=INK if on else SOFT); x -= 10
    d.text((64, H - 44), FOOT, font=F(FM, 17), fill=DIM)
    d.text((W - 64 - d.textlength("Información, no recomendación de voto", font=F(FM, 17)), H - 44), "Información, no recomendación de voto", font=F(FM, 17), fill=DIM)
    return im
CHROME = {}
def get_chrome(sec):
    if sec not in CHROME: CHROME[sec] = chrome(sec)
    return CHROME[sec]

# ---------- scene builders: return list of (img, x, y, t_in, kind) ----------
def els_title(p, dur):
    E = []
    E.append((text_img("DOMINGO 29 DE NOVIEMBRE · ELECCIONES GENERALES", F(FB, 30), CYAN), 140, 300, 0.1, "up"))
    for i, l in enumerate(["¿Qué propone cada partido", "para tu bolsillo?"]):
        E.append((text_img(l, F(FBK, 96), WHITE if i == 0 else YEL), 132, 360 + i * 118, 0.25 + i * 0.15, "up"))
    x = 140
    for i, n in enumerate(["PP", "PSOE", "Vox", "Sumar", "Podemos"]):
        t = text_img(n, F(FB, 40), WHITE); c = rrect(t.width + 56, 76, 38, (255, 255, 255, 26), (255, 255, 255, 70), 2); c.alpha_composite(t, (28, 10))
        E.append((c, x, 680, 1.2 + i * 0.35, "pop")); x += c.width + 18
    return E

def els_text(p, dur, kicker, big):
    E = [(text_img(kicker, F(FB, 30), CYAN), 140, 330, 0.0, "up")]
    lines = wrap(big, F(FXB, 64), 1500)
    y = 390
    for i, l in enumerate(lines):
        E.append((text_img(l, F(FXB, 64), WHITE), 136, y, 0.15 + i * 0.12, "up")); y += 84
    return E

def els_section(p, dur, n, sec, sub):
    E = [(text_img(f"TEMA {n} DE 5", F(FB, 32), CYAN), 140, 360, 0.0, "up"),
         (text_img(sec.capitalize() if sec != "ENERGÍA" else "Luz y energía", F(FBK, 150), WHITE), 128, 410, 0.15, "up")]
    if sub:
        for i, l in enumerate(wrap(sub, F(FS, 40), 1500)):
            E.append((text_img(l, F(FS, 40), SOFT), 140, 610 + i * 56, 0.6 + 0.15 * i, "up"))
    return E

def els_party(p, dur):
    E = []
    name = p["party"]
    E.append((text_img("PROPONE", F(FB, 28), CYAN), 140, 360, 0.0, "up"))
    E.append((text_img(name, F(FBK, 128), WHITE), 132, 395, 0.1, "up"))
    bar = rrect(120, 10, 5, YEL + (255,)); E.append((bar, 140, 560, 0.35, "grow"))
    if name in ("PSOE", "Sumar", "Podemos"):
        E.append((text_img("Programa completo aún no publicado", F(FM, 26), SOFT), 140, 600, 0.5, "up"))
    pts = p.get("pts", []); n = len(pts)
    cw, rh = 860, 92; ch = n * rh + 48
    card = rrect(cw, ch, 28, (12, 15, 30, 205), (255, 255, 255, 40), 2)
    cx, cy = 900, (H - ch) // 2 + 20
    E.append((card, cx, cy, 0.2, "fade"))
    sp = max(1.0, dur - 0.9); pos = p.get("pos") or [i / max(n, 1) for i in range(n)]
    for i, s in enumerate(pts):
        row = Image.new("RGBA", (cw - 60, rh), (0, 0, 0, 0)); d = ImageDraw.Draw(row)
        d.ellipse([0, 33, 18, 51], fill=YEL)
        f = F(FB, 34) if len(s) < 40 else F(FB, 30)
        d.text((40, 22), s, font=f, fill=WHITE)
        E.append((row, cx + 40, cy + 24 + i * rh, max(0.35, pos[i] * sp - 0.3), "left"))
    return E

def els_summary(p, dur):
    E = [(text_img("EN RESUMEN", F(FB, 30), CYAN), 140, 250, 0.0, "up")]
    cols = [("PP y Vox", ["Bajar impuestos", "Construir más", "Derogar la ley de vivienda"]),
            ("PSOE, Sumar y Podemos", ["Regular el alquiler", "Subir el salario mínimo", "Reducir la jornada", "(con distintos grados)"])]
    for j, (h, items) in enumerate(cols):
        x = 140 + j * 840
        card = rrect(780, 520, 28, (12, 15, 30, 205), (255, 255, 255, 40), 2)
        E.append((card, x, 320, 0.2 + j * 2.5, "fade"))
        E.append((text_img(h, F(FBK, 56), YEL), x + 44, 356, 0.3 + j * 2.5, "up"))
        for i, s in enumerate(items):
            E.append((text_img("·  " + s, F(FB, 40) if "(" not in s else F(FM, 32), WHITE if "(" not in s else SOFT), x + 44, 470 + i * 78, 0.7 + j * 2.5 + i * 0.5, "left"))
    return E

def els_cta(p, dur):
    E = [(LOGO.resize((180, 180), Image.LANCZOS), W // 2 - 90, 250, 0.0, "pop")]
    for i, l in enumerate(["Compara y decide tú"]):
        t = text_img(l, F(FBK, 92), WHITE); E.append((t, (W - t.width) // 2, 470, 0.3, "up"))
    t = text_img("Lo actualizaremos cuando PSOE, Sumar y Podemos publiquen su programa", F(FS, 36), SOFT); E.append((t, (W - t.width) // 2, 600, 0.8, "up"))
    t = text_img("Cada día, la economía que te afecta, explicada fácil", F(FB, 40), YEL); E.append((t, (W - t.width) // 2, 700, 2.5, "up"))
    b = rrect(420, 96, 48, (238, 36, 66, 255)); bt = text_img("SUSCRÍBETE", F(FBK, 44), WHITE); b.alpha_composite(bt, ((420 - bt.width) // 2, 18))
    E.append((b, (W - 420) // 2, 800, 3.0, "pop"))
    return E

SUBS = {"VIVIENDA": "Alquiler, compra y vivienda pública", "IMPUESTOS": "IRPF, IVA y quién paga más",
        "SUELDOS": "Salario mínimo: 1.221 € en 14 pagas · Jornada máxima: 40 h",
        "PENSIONES": "Pensión media de jubilación: ≈1.576 €/mes (Gobierno)", "ENERGÍA": "Nucleares, renovables e impuestos de la luz"}

def build(i, dur):
    p = P[i]; sec = p["sec"]
    if p["id"] == "intro1": return els_title(p, dur)
    if p["id"] == "intro2": return els_text(p, dur, "CÓMO LO VAMOS A VER", "5 partidos · 5 temas · siempre el mismo orden (escaños de 2023) · sin opinar")
    if p["id"] == "intro3": return els_text(p, dur, "AVISO", "PP: programa completo. Vox: plan económico. PSOE, Sumar y Podemos: lo anunciado hasta el 12 de noviembre.")
    if p["id"].endswith("0") and sec in SECS: return els_section(p, dur, SECS.index(sec) + 1, sec, SUBS[sec])
    if "party" in p: return els_party(p, dur)
    if p["id"] == "fin1": return els_summary(p, dur)
    return els_cta(p, dur)

def draw(base, E, t):
    for im, x, y, t0, kind in E:
        k = eo((t - t0) / 0.5)
        if k <= 0: continue
        if kind == "up": paste(base, im, x, y + 30 * (1 - k), k)
        elif kind == "left": paste(base, im, x - 40 * (1 - k), y, k)
        elif kind == "fade": paste(base, im, x, y, k)
        elif kind == "grow":
            w = max(1, int(im.width * k)); paste(base, im.crop((0, 0, w, im.height)), x, y, 1)
        elif kind == "pop":
            s = 0.85 + 0.15 * k; j = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
            paste(base, j, x + (im.width - j.width) / 2, y + (im.height - j.height) / 2, k)

def scene_photo(i):
    sec = P[i]["sec"]; lst = PHOT[sec]
    if "party" in P[i]: return lst[0]  # same neutral photo for every party in a topic
    idx = [j for j in range(len(P)) if P[j]["sec"] == sec and "party" not in P[j]].index(i)
    return lst[(idx + 1) % len(lst)] if sec in SECS else lst[idx % len(lst)]

def render_seg(args):
    i, t0, t1, out = args
    dur = t1 - t0; E = build(i, dur); key = scene_photo(i); sec = P[i]["sec"]
    ch = get_chrome(sec if sec in SECS else None)
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", os.environ.get("PRESET","veryfast"), "-crf", os.environ.get("CRF","20"), *(["-tune","stillimage"] if os.environ.get("STATIC") else []), "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    nf = int(round(t1 * FPS)) - int(round(t0 * FPS))
    for f in range(nf):
        t = f / FPS
        base = kb(key, t, dur, i).convert("RGBA")
        base.alpha_composite(ch)
        draw(base, E, t)
        # fade in from black at very start / crossfade feel
        if i == 0 and t < 0.6:
            base = Image.blend(Image.new("RGBA", (W, H), INK + (255,)), base, t / 0.6)
        pr.stdin.write(base.convert("RGB").tobytes())
    pr.stdin.close(); pr.wait(); return out



V1 = lambda *k: [FOTOS[x] for x in k]
POOL = {
    "INTRO": P2("GEN_75_") + V1("6_") + P2("GEN_80_") + V1("66_", "11_"),
    "VIVIENDA": P2("VIV_0_", "VIV_5_", "VIV_10_") + V1("12_") + P2("VIV_6_", "VIV_11_") + V1("19_", "14_") + P2("VIV_13_", "VIV_7_", "VIV_14_") + V1("16_", "20_"),
    "IMPUESTOS": P2("IMP_21_") + V1("24_") + P2("IMP_20_") + V1("29_", "31_") + P2("IMP_22_", "IMP_19_") + V1("32_", "25_"),
    "SUELDOS": P2("SUE_30_", "SUE_41_", "SUE_31_", "SUE_38_") + V1("36_") + P2("SUE_33_", "SUE_42_", "SUE_39_", "SUE_34_") + V1("37_"),
    "PENSIONES": P2("PEN_50_") + V1("42_") + P2("SUE_45_") + V1("45_") + P2("SUE_41_", "IMP_20_", "SUE_42_"),
    "ENERGÍA": P2("ENE_56_") + V1("48_", "54_") + P2("ENE_55_", "ENE_60_") + V1("61_", "56_") + P2("ENE_57_", "ENE_62_") + V1("65_", "55_"),
    "RESUMEN": P2("GEN_86_", "GEN_88_") + V1("69_") + P2("GEN_89_", "GEN_85_") + V1("6_"),
}
SEG = 4.2  # seconds per background photo
def plan(i, dur):
    """photos for scene i: keep rotating through the topic pool across scenes"""
    sec = P[i]["sec"]; pool = POOL[sec]
    before = [j for j in range(i) if P[j]["sec"] == sec]
    used = sum(max(1, int(round((STARTS[j + 1] - STARTS[j]) / SEG))) for j in before)
    n = max(1, int(round(dur / SEG)))
    return [pool[(used + k) % len(pool)] for k in range(n)]

def bg_at(i, t, dur):
    ph = plan(i, dur); n = len(ph); L = dur / n
    k = min(n - 1, int(t // L)); tl = t - k * L
    a = kb(ph[k], tl + k * 0.0, L + 0.8, i * 7 + k)
    XF = 0.7
    if k > 0 and tl < XF:
        b = kb(ph[k - 1], L + tl, L + 0.8, i * 7 + k - 1)
        e = tl / XF; e = e * e * (3 - 2 * e)
        a = Image.blend(b, a, e)
    return a

def frame_at(i, t, dur, E, ch):
    base = bg_at(i, t, dur).convert("RGBA"); base.alpha_composite(ch); draw(base, E, t); return base

def render_seg2(args):
    i, t0, t1, out = args
    dur = t1 - t0; E = build(i, dur); sec = P[i]["sec"]; ch = get_chrome(sec if sec in SECS else None)
    prev = None
    if i > 0:
        pd = STARTS[i] - STARTS[i - 1]; ps = P[i - 1]["sec"]
        prev = frame_at(i - 1, pd - 1.0 / FPS, pd, build(i - 1, pd), get_chrome(ps if ps in SECS else None))
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    nf = int(round(t1 * FPS)) - int(round(t0 * FPS))
    XS = 0.45
    for f in range(nf):
        t = f / FPS
        img = frame_at(i, t, dur, E, ch)
        if prev is not None and t < XS:
            e = t / XS; e = e * e * (3 - 2 * e); img = Image.blend(prev, img, e)
        if i == 0 and t < 0.6:
            img = Image.blend(Image.new("RGBA", (W, H), INK + (255,)), img, t / 0.6)
        pr.stdin.write(img.convert("RGB").tobytes())
    pr.stdin.close(); pr.wait(); return out


if __name__ == "__main__":
    T = json.load(open(sys.argv[1])); out = sys.argv[2]; nw = int(sys.argv[3]) if len(sys.argv) > 3 else os.cpu_count()
    st = T["starts"] + [T["end"]]
    STARTS[:] = st
    only = [int(x) for x in sys.argv[4].split(",")] if len(sys.argv) > 4 else None
    SD = os.environ.get("SEGDIR", "segs"); os.makedirs(D + SD, exist_ok=True)
    jobs = [(i, st[i], st[i + 1], D + f"{SD}/s{i:02d}.mp4") for i in range(len(P)) if only is None or i in only]
    with Pool(nw) as pool:
        for r in pool.imap_unordered(render_seg2, jobs): print("ok", r, flush=True)
    if only is None:
        open(D + SD + "/list.txt", "w").write("".join(f"file 's{i:02d}.mp4'\n" for i in range(len(P))))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", D + SD + "/list.txt", "-c", "copy", out], check=True)
        print("video ok", out)


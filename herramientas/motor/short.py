"""Vertical promo Short (1080x1920) for Cómo Va el Mundo.

usage: python3 short.py <out.mp4> [beats.json]   (beats.json = synced beat starts; else estimated)
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim
from anim import (S, F, FX, FBK, FB, FS, CYAN, VIOLET, YELLOW, WHITE, MUTED, GREEN, RED,
                  ease, back, g_factory, g_house, g_pump, g_euro, add_mark)
import trailer  # glyphs g_news, g_compare, g_question (also swaps anim.SC; not used here)

D = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 25
anim.W, anim.H = W, H  # so add_mark builds a canvas of the right size
NANIM = int(anim.ANIM * FPS)


class VF(anim.Fr):
    def __init__(self):
        self.im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.gl = Image.new("RGB", self.im.size, (0, 0, 0))
        self.gd = ImageDraw.Draw(self.gl)
        self.addl = None

    def c(self, col, o):
        return tuple(col[:3]) + (int(255 * max(0.0, min(1.0, o))),)

    def done(self):
        ov = self.im.resize((W, H), Image.LANCZOS)
        g = self.gl.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
        g = ImageChops.multiply(g, Image.new("RGB", g.size, (170, 170, 170)))
        if self.addl is not None:
            g = ImageChops.add(g, self.addl.resize((W, H), Image.LANCZOS))
        return ov, g


BEATS = [
    ("¿Por qué todo es más caro?", "B_ciudad"),
    ("¿Por qué no bajan los alquileres?", "B_ciudad"),
    ("¿Y qué tiene que ver contigo lo que pasa en el mundo?", "G_graficos"),
    ("En Cómo Va el Mundo te lo explicamos fácil.", "G_graficos"),
    ("Noticias, precios, empresas y países, en pocos minutos.", "A_super"),
    ("Con datos reales y sin palabras raras.", "A_super"),
    ("Síguenos: nuevo vídeo cada semana.", "B_ciudad"),
]


def draw(f, p):
    # hook questions (beats 0-2), cleared from beat 3
    if p(3) < 1:
        k = 1 - ease(p(3))
        f.wrap(540, 560, "¿Por qué todo es más caro?", 92, 920, WHITE, FBK, p(0) * k, anchor="ms")
        f.wrap(540, 880, "¿Por qué no bajan los alquileres?", 92, 920, CYAN, FBK, p(1) * k, anchor="ms")
        f.wrap(540, 1200, "¿Qué tiene que ver contigo lo que pasa en el mundo?", 76, 940, YELLOW, FBK, p(2) * k, anchor="ms")
    if p(3) > 0 and p(4) < 1:
        k = 1 - ease(p(4))
        add_mark(f, 540, 760, 260 * back(p(3)) * max(0.01, k))
        f.t(540, 1180, "Cómo Va", 120, WHITE, FBK, "ms", p(3) * k)
        f.t(540, 1320, "el Mundo", 120, CYAN, FBK, "ms", p(3) * k, glow=True)
        f.t(540, 1440, "La economía, explicada fácil", 52, MUTED, FS, "ms", p(3) * k)
    if p(4) > 0 and p(6) < 1:
        k = 1 - ease(p(6))
        items = [("Noticias", trailer.g_news, CYAN), ("Precios", g_euro, YELLOW), ("Empresas", g_factory, VIOLET), ("Países", trailer.g_compare, GREEN)]
        for i, (lab, gl, col) in enumerate(items):
            pi = max(0, min(1, p(4) * 2.4 - i * 0.35)) * k
            y = 360 + i * 240
            f.disc(250, y, 95, col, pi, gl)
            f.t(400, y + 30, lab, 84, WHITE, FBK, o=pi)
        f.t(540, 1290, "en pocos minutos", 60, MUTED, FB, "ms", p(4) * k)
        f.box(110, 1350, 970, 1520, YELLOW, p(5) * k)
        f.t(540, 1420, "Datos reales", 60, YELLOW, FB, "ms", p(5) * k, slide=0)
        f.t(540, 1495, "Sin palabras raras", 60, YELLOW, FB, "ms", p(5) * k, slide=0)
    if p(6) > 0:
        add_mark(f, 540, 640, 200 * back(p(6)))
        f.t(540, 1000, "Cómo Va el Mundo", 92, WHITE, FBK, "ms", p(6))
        kk = back(p(6))
        w, h = 300 * kk, 70 * kk
        f.d.rounded_rectangle(f.P(540 - w, 1150 - h, 540 + w, 1150 + h), radius=int(h * S), fill=(220, 38, 38, 255))
        f.t(540, 1175, "SUSCRÍBETE", 70 * kk, WHITE, FBK, "ms", 1, slide=0)
        f.t(540, 1400, "Nuevo vídeo", 76, YELLOW, FBK, "ms", p(6), glow=True)
        f.t(540, 1500, "cada semana", 76, YELLOW, FBK, "ms", p(6), glow=True)


_bd = {}


def backdrop(name):
    if name not in _bd:
        im = Image.open(f"{D}/backdrops/{name}.png").convert("RGB").filter(ImageFilter.GaussianBlur(3))
        im = ImageChops.multiply(im, Image.new("RGB", im.size, (84, 84, 98)))
        _bd[name] = im
    return _bd[name]


def camera(name, t):
    bd = backdrop(name)
    bw, bh = bd.size
    ch = bh / (1.0 + 0.04 * math.sin(t * 0.3) + 0.04)
    cw = ch * W / H
    cx = bw / 2 + (bw - cw) / 2 * 0.7 * math.sin(t * 0.12)
    cy = bh / 2
    cx = min(max(cx, cw / 2), bw - cw / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return bd.resize((W, H), Image.BILINEAR, box=box)


random.seed(5)
PARTS = [dict(x=random.uniform(0, W), y=random.uniform(0, H), vy=random.uniform(10, 40), r=random.uniform(1.5, 3.5),
              ph=random.uniform(0, 6.3), col=random.choice([CYAN, VIOLET, YELLOW])) for _ in range(90)]


def compose(name, t, ov, g):
    base = camera(name, t)
    d = ImageDraw.Draw(base)
    for p in PARTS:
        y = (p["y"] - p["vy"] * t) % H
        tw = 0.35 + 0.35 * math.sin(t * 2 + p["ph"])
        d.ellipse([p["x"] - p["r"], y - p["r"], p["x"] + p["r"], y + p["r"]], fill=tuple(int(v * tw) for v in p["col"]))
    base = ImageChops.add(base, g).convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def main():
    out = sys.argv[1]
    if len(sys.argv) > 2:
        starts = json.load(open(sys.argv[2]))["beat_starts"]
        end = json.load(open(sys.argv[2]))["end"]
    else:
        starts, t = [], 0.3
        for txt, _ in BEATS:
            starts.append(t)
            t += max(2.2, len(txt.split()) / 2.6 + 0.6)
        end = t + 1.2
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", out], stdin=subprocess.PIPE)
    key, val, prev_bg, fade_from = None, None, None, None
    for n in range(int(end * FPS)):
        t = n / FPS
        bi = max([i for i, s in enumerate(starts) if s <= t] or [0])
        k = min(NANIM, max(0, int((t - starts[bi]) / anim.ANIM * NANIM))) if t >= starts[0] else 0
        if (bi, k) != key:
            key = (bi, k)
            f = VF()
            draw(f, lambda i: 1.0 if i < bi else ((k / NANIM if t >= starts[0] else 0) if i == bi else 0.0))
            val = f.done()
        img = compose(BEATS[bi][1], t, *val)
        ff.stdin.write(img.tobytes())
        if n in (int(starts[i] * FPS) + NANIM + 5 for i in range(len(BEATS))):
            img.resize((360, 640)).save(f"{D}/short_prev_{bi}.jpg")
    ff.stdin.close()
    ff.wait()
    print("ok", out, round(end, 1), "s")


if __name__ == "__main__":
    main()

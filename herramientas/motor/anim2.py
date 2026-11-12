"""Layered renderer: illustrated backdrops with camera drift + particles,
animated overlay from anim.py scenes, crossfades, synced beat times.

usage: python3 anim2.py <beats.json> <audio_dur> <first_scene> <last_scene> <out_segment.mp4>
"""
import json, math, os, random, subprocess, sys
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim

D = os.path.dirname(os.path.abspath(__file__))
S, W, H, FPS = anim.S, anim.W, anim.H, anim.FPS
NANIM = int(anim.ANIM * FPS)
TRANS = 0.4
SCENE_BG = ["A_super", "G_graficos", "A_super", "G_graficos", "C_puerto", "D_energia", "E_olivar", "B_ciudad",
            "G_graficos", "B_ciudad", "F_gasolinera", "F_gasolinera", "D_energia", "A_super", "G_graficos", "B_ciudad"]
PAN = [(1, 0), (-1, 0), (0, 1), (1, 1), (-1, 0), (1, 0), (0, -1), (-1, 1), (1, 0), (0, 1), (-1, 0), (1, -1), (0, 1), (-1, 0), (1, 0), (0, -1)]


class Fr2(anim.Fr):
    def __init__(self):
        self.im = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.gl = Image.new("RGB", self.im.size, (0, 0, 0))
        self.gd = ImageDraw.Draw(self.gl)
        self.addl = None

    def c(self, col, o):
        return tuple(col[:3]) + (int(255 * max(0.0, min(1.0, o))),)

    def done(self):
        self.t(1800, 1030, "CÓMO VA EL MUNDO", 20, anim.DIM, anim.FB, "rs", slide=0)
        ov = self.im.resize((W, H), Image.LANCZOS)
        g = self.gl.resize((W // 4, H // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
        g = ImageChops.multiply(g, Image.new("RGB", g.size, (170, 170, 170)))
        if self.addl is not None:
            g = ImageChops.add(g, self.addl.resize((W, H), Image.LANCZOS))
        return ov, g


_bd = {}


def backdrop(name):
    if name not in _bd:
        im = Image.open(f"{D}/backdrops/{name}.png").convert("RGB")
        im = im.filter(ImageFilter.GaussianBlur(2.2))
        im = ImageChops.multiply(im, Image.new("RGB", im.size, (92, 92, 104)))  # dim ~36%
        # vignette
        vg = Image.new("L", (im.width // 8, im.height // 8))
        px = vg.load()
        for y in range(vg.height):
            for x in range(vg.width):
                dx, dy = (x / vg.width - 0.5) * 2, (y / vg.height - 0.5) * 2
                px[x, y] = int(255 * max(0.35, 1 - 0.55 * (dx * dx + dy * dy)))
        vg = vg.resize(im.size, Image.BILINEAR)
        im = Image.composite(im, Image.new("RGB", im.size, (4, 6, 14)), vg)
        _bd[name] = im
    return _bd[name]


def camera(si, u):
    u = min(1.0, max(0.0, u))
    bd = backdrop(SCENE_BG[si])
    bw, bh = bd.size
    z = 1.0 + 0.10 * u
    cw, ch = bw / z, bh / z
    px, py = PAN[si]
    cx = bw / 2 + px * (bw - cw) / 2 * (u * 2 - 1) * 0.8
    cy = bh / 2 + py * (bh - ch) / 2 * (u * 2 - 1) * 0.8
    cx = min(max(cx, cw / 2), bw - cw / 2)
    cy = min(max(cy, ch / 2), bh - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return bd.resize((W, H), Image.BILINEAR, box=box)


random.seed(11)
PARTS = [dict(x=random.uniform(0, W), y=random.uniform(0, H), vy=random.uniform(8, 30), vx=random.uniform(-6, 6),
              r=random.uniform(1.2, 3.2), ph=random.uniform(0, 6.28), col=random.choice([anim.CYAN, anim.VIOLET, anim.YELLOW, (200, 210, 255)]))
         for _ in range(70)]


def particles(img, t):
    d = ImageDraw.Draw(img)
    for p in PARTS:
        x = (p["x"] + p["vx"] * t) % W
        y = (p["y"] - p["vy"] * t) % H
        tw = 0.35 + 0.35 * math.sin(t * 1.7 + p["ph"])
        c = tuple(int(v * tw) for v in p["col"])
        r = p["r"]
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)


def overlay(si, bi, k):
    sc = anim.SC[si]
    prog = k / NANIM

    def p(i):
        return 1.0 if i < bi else (prog if i == bi else 0.0)

    f = Fr2()
    sc["draw"](f, p)
    return f.done()


def compose(si, u, t, ov, g):
    base = camera(si, u)
    particles(base, t)
    base = ImageChops.add(base, g).convert("RGBA")
    base.alpha_composite(ov)
    return base.convert("RGB")


def main():
    beats_file, audio_dur, first, last, out = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
    starts = json.load(open(beats_file))["beat_starts"]
    starts = [max(0.0, s - 0.1) for s in starts]
    starts[0] = 0.0
    # beat index ranges per scene
    idx, ranges = 0, []
    for sc in anim.SC:
        ranges.append((idx, idx + len(sc["beats"])))
        idx += len(sc["beats"])
    scene_start = [starts[a] for a, b in ranges]
    end_all = audio_dur + 1.5
    scene_end = scene_start[1:] + [end_all]

    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    prev_last = None
    if first > 0:  # final frame of the previous scene, for the crossfade
        ps = first - 1
        a, b = ranges[ps]
        ov, g = overlay(ps, b - a - 1, NANIM)
        prev_last = compose(ps, 1.0, scene_end[ps], ov, g)
    for si in range(first, last + 1):
        a, b = ranges[si]
        n0, n1 = round(scene_start[si] * FPS), round(scene_end[si] * FPS)
        cache_key, cache_val = None, None
        last_img = None
        for n in range(n0, n1):
            t = n / FPS
            u = (t - scene_start[si]) / max(0.1, scene_end[si] - scene_start[si])
            bi = 0
            for j in range(a, b):
                if starts[j] <= t + 1e-6:
                    bi = j - a
            prog = (t - starts[a + bi]) / anim.ANIM
            k = min(NANIM, max(0, int(prog * NANIM)))
            key = (bi, k)
            if key != cache_key:
                cache_key, cache_val = key, overlay(si, bi, k)
            img = compose(si, u, t, *cache_val)
            tin = t - scene_start[si]
            if prev_last is not None and tin < TRANS:
                img = Image.blend(prev_last, img, tin / TRANS)
            ff.stdin.write(img.tobytes())
            last_img = img
        prev_last = last_img
        print("scene", si + 1, "done", flush=True)
    ff.stdin.close()
    ff.wait()


if __name__ == "__main__":
    main()

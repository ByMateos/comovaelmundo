"""Reel-style '¿Sabías que?' Short: AI images + Ken Burns + HUD + karaoke captions.
usage: reel.py spec.json [p0 p1]   (renders frames p0..p1 seconds, default all)
spec: {out, voice, words (json list of {text,start,end}), dur, images:[{file,t0,pan}],
       overlays:[{t0,t1,kind:'num'|'tag', ...}], cta_t0}"""
import json, math, subprocess, sys, random
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from style_a2 import F, FBK, FXB, FB, FS, FM, WHITE, SOFT, DIM, YEL, CYAN, VIO, AMB, gradient_text, glass, paste_logo, tracked

W, H, FPS = 1080, 1920, 30
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
spec = json.load(open(sys.argv[1]))
words = json.load(open(spec["words"]))
words = [w for w in words if w["text"].strip()]
DUR = spec["dur"]
p0 = float(sys.argv[2]) if len(sys.argv) > 2 else 0
p1 = float(sys.argv[3]) if len(sys.argv) > 3 else DUR
out = spec["out"] if len(sys.argv) <= 4 else sys.argv[4]

def ease(x):
    x = max(0, min(1, x)); return 1 - (1 - x) ** 3

# ---------- images, pre-scaled
_cache = {}
def load(f):
    if f not in _cache:
        src = Image.open(f).convert("RGB")
        s = max(H / src.height, W / src.width)
        big = src.resize((int(src.width * s), int(src.height * s)), Image.LANCZOS)
        _cache[f] = big.filter(ImageFilter.UnsharpMask(2, 60, 2))
    return _cache[f]
IMGS = [(m, load(m["file"])) for m in spec["images"]]

def bg_at(t):
    idx = 0
    for i, (m, _) in enumerate(IMGS):
        if t >= m["t0"]: idx = i
    m, big = IMGS[idx]
    t1 = IMGS[idx + 1][0]["t0"] if idx + 1 < len(IMGS) else DUR
    u = ease((t - m["t0"]) / max(0.1, t1 - m["t0"]) * 0.8 + 0.2 * (t - m["t0"]) / max(0.1, t1 - m["t0"]))
    z = m.get("z0", 1.0) + m.get("dz", 0.14) * u
    px = m.get("pan", 0)                      # -1..1 horizontal drift
    fx = m.get("fx", 0.5)                     # focus x (0..1)
    sw, sh = W / z, H / z
    cx = big.width * fx + px * 260 * (u - 0.5)
    cx = max(sw / 2, min(big.width - sw / 2, cx))
    cy = big.height / 2
    crop = big.crop((int(cx - sw / 2), int(cy - sh / 2), int(cx + sw / 2), int(cy + sh / 2))).resize((W, H), Image.BILINEAR)
    # flash-zoom transition in the first 0.25 s of each image
    k = t - m["t0"]
    if idx > 0 and k < 0.28:
        a = 1 - k / 0.28
        crop = Image.blend(crop, Image.new("RGB", (W, H), (235, 245, 255)), 0.55 * a)
    return crop

# ---------- static layers
def make_static():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    # vignette + bottom/top gradients
    g = Image.new("L", (1, H))
    for y in range(H):
        v = 0
        if y < 330: v = int(150 * (1 - y / 330) ** 1.4)
        if y > 1000: v = int(225 * ((y - 1000) / 920) ** 1.2)
        g.putpixel((0, y), min(255, v))
    shade = Image.new("RGBA", (W, H), (4, 6, 14, 255)); shade.putalpha(g.resize((W, H)))
    L = Image.alpha_composite(L, shade)
    d = ImageDraw.Draw(L)
    # grid
    for x in range(0, W, 90): d.line([(x, 0), (x, H)], fill=(120, 200, 255, 14))
    for y in range(0, H, 90): d.line([(0, y), (W, y)], fill=(120, 200, 255, 14))
    # corner brackets
    c, m, ln = (90, 230, 255, 200), 54, 70
    for (x, y, sx, sy) in [(m, 250, 1, 1), (W - m, 250, -1, 1), (m, H - 300, 1, -1), (W - m, H - 300, -1, -1)]:
        d.line([(x, y), (x + sx * ln, y)], fill=c, width=5)
        d.line([(x, y), (x, y + sy * ln)], fill=c, width=5)
    return L
STATIC = make_static()

def hud(base, t):
    im = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # header
    paste_logo(im, 104, 140, 34)
    d.text((156, 122), "Cómo Va el Mundo", font=F(FXB, 34), fill=WHITE)
    d.text((156, 162), "@ComoVaElMundo", font=F(FM, 24), fill=SOFT)
    pill_w = 330
    d.rounded_rectangle((W - 60 - pill_w, 112, W - 60, 172), 30, fill=(255, 210, 63, 235))
    d.text((W - 60 - pill_w / 2, 142), "¿SABÍAS QUE?", font=F(FBK, 32), fill=(12, 12, 20), anchor="mm")
    # discreet topic label
    d.ellipse((86, 293, 98, 305), fill=(56, 225, 255, 230))
    d.text((112, 299), spec.get("topic", "TECNOLOGÍA"), font=F(FS, 24), fill=(200, 236, 255, 220), anchor="lm")
    # progress bar
    d.rounded_rectangle((60, H - 70, W - 60, H - 62), 4, fill=(255, 255, 255, 40))
    d.rounded_rectangle((60, H - 70, 60 + (W - 120) * t / DUR, H - 62), 4, fill=(255, 210, 63, 230))
    base.alpha_composite(im)

# ---------- karaoke captions (clean: sentence case, Inter Bold, soft shadow)
import re as _re
GROUPS, k = [], 0
for n in spec["phrases"]:
    GROUPS.append(list(range(k, k + n))); k += n

def tok(s):
    s = s.strip()
    s = _re.sub(r"[,.:;…]+$", "", s)
    return s

CF = F(FB, 80)
def captions(base, t, y=1300):
    g = None
    for G in GROUPS:
        nxt = GROUPS.index(G) + 1
        end = GROUPS[nxt][0] if nxt < len(GROUPS) else None
        t_end = words[end]["start"] - 0.05 if end is not None else words[G[-1]]["end"] + 0.4
        if words[G[0]]["start"] - 0.1 <= t < t_end:
            g = G
    if g is None: return
    toks = [tok(words[j]["text"]) if i == len(g) - 1 else words[j]["text"].strip() for i, j in enumerate(g)]
    d0 = ImageDraw.Draw(base)
    sp = d0.textlength(" ", font=CF)
    widths = [d0.textlength(s, font=CF) for s in toks]
    lines, line, lw = [], [], 0
    for i, wdt in enumerate(widths):
        if line and lw + sp + wdt > W - 180:
            lines.append(line); line, lw = [], 0
        lw += (sp if line else 0) + wdt; line.append(i)
    lines.append(line)
    pop = ease((t - words[g[0]]["start"] + 0.1) / 0.18)
    txt = Image.new("RGBA", base.size, (0, 0, 0, 0)); dt = ImageDraw.Draw(txt)
    sh = Image.new("L", base.size, 0); ds = ImageDraw.Draw(sh)
    for li, ln in enumerate(lines):
        tot = sum(widths[i] for i in ln) + sp * (len(ln) - 1)
        x = (W - tot) / 2
        yy = y + li * 100 + (1 - pop) * 18
        for i in ln:
            wd = words[g[i]]
            active = wd["start"] - 0.04 <= t < wd["end"] + 0.06
            said = t >= wd["end"]
            if active: col = (255, 214, 72, 255)
            elif said: col = (255, 255, 255, 255)
            else: col = (255, 255, 255, 175)
            dt.text((x, yy), toks[i], font=CF, fill=col)
            ds.text((x, yy + 4), toks[i], font=CF, fill=235)
            x += widths[i] + sp
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    shadow = Image.new("RGBA", base.size, (0, 0, 0, 255)); shadow.putalpha(sh.point(lambda v: int(v * pop)))
    base.alpha_composite(shadow)
    txt.putalpha(txt.getchannel("A").point(lambda v: int(v * (0.3 + 0.7 * pop))))
    base.alpha_composite(txt)

# ---------- overlays (big numbers / tags) — work on RGB frames
def panel(img, box, radius=46, tint=(10, 16, 34), alpha=0.62, border=0.4):
    L = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(L).rounded_rectangle(box, radius, fill=tint + (int(255 * alpha),), outline=(140, 230, 255, int(255 * border)), width=3)
    return Image.alpha_composite(img.convert("RGBA"), L).convert("RGB")

def overlays(im, t):
    for o in spec["overlays"]:
        if not (o["t0"] <= t < o["t1"]): continue
        fin = o.get("in", 0.3)
        a = (ease((t - o["t0"]) / fin) if fin > 0 else 1) * (1 - ease((t - (o["t1"] - 0.25)) / 0.25))
        if a <= 0.01: continue
        y = o.get("y", 720) + (1 - a) * 40
        lay = im.copy()
        if o["kind"] == "num":
            lay = panel(lay, (90, y - 170, W - 90, y + 170))
            d = ImageDraw.Draw(lay)
            tracked(d, (W / 2, y - 112), o["label"], F(FS, 28), (170, 230, 255), track=3)
            if "to" in o:
                u = ease((t - o["t0"]) / o.get("count", 0.9))
                v = o.get("from", 0) + (o["to"] - o.get("from", 0)) * u
                txt = o.get("fmt", "{}").format(f"{int(round(v)):,}".replace(",", "."))
            else:
                txt = o["text"]
            lay = gradient_text(lay, (W / 2, y + 10), txt, F(FBK, o.get("size", 120)), tuple(o.get("c1", YEL)), tuple(o.get("c2", AMB)))
            ImageDraw.Draw(lay).text((W / 2, y + 112), o.get("note", ""), font=F(FM, 30), fill=(196, 204, 224), anchor="mm")
        elif o["kind"] == "tag":
            f = F(FBK, 50)
            tw = ImageDraw.Draw(lay).textlength(o["text"], font=f)
            L = Image.new("RGBA", lay.size, (0, 0, 0, 0))
            ImageDraw.Draw(L).rounded_rectangle((W / 2 - tw / 2 - 44, y - 50, W / 2 + tw / 2 + 44, y + 50), 50, fill=tuple(o.get("bg", (255, 60, 80, 240))))
            lay = Image.alpha_composite(lay.convert("RGBA"), L).convert("RGB")
            ImageDraw.Draw(lay).text((W / 2, y), o["text"], font=f, fill=WHITE, anchor="mm")
        im = Image.blend(im, lay, a)
    return im

def cta(im, t):
    t0 = spec["cta_t0"]
    if t < t0: return im
    a = ease((t - t0) / 0.4)
    y = 900
    lay = panel(im.copy(), (110, y - 230, W - 110, y + 330), radius=50, alpha=0.72)
    d = ImageDraw.Draw(lay)
    paste_logo(lay, W // 2, y - 110, 62)
    d.text((W / 2, y + 10), "Sígueme para más", font=F(FXB, 52), fill=WHITE, anchor="mm")
    lay = gradient_text(lay, (W / 2, y + 95), "¿SABÍAS QUE?", F(FBK, 80), YEL, AMB)
    d = ImageDraw.Draw(lay)
    pulse = 1 + 0.04 * math.sin((t - t0) * 7)
    bw, bh = 440 * pulse, 100 * pulse
    d.rounded_rectangle((W / 2 - bw / 2, y + 230 - bh / 2, W / 2 + bw / 2, y + 230 + bh / 2), 50, fill=(255, 40, 60))
    d.text((W / 2, y + 230), "SUSCRÍBETE", font=F(FBK, 46), fill=WHITE, anchor="mm")
    return Image.blend(im, lay, a)

def frame(t):
    im = bg_at(t).convert("RGBA")
    im.alpha_composite(STATIC)
    hud(im, t)
    im = im.convert("RGB")
    im = overlays(im, t)
    im = cta(im, t)
    im = im.convert("RGBA")
    if t < spec["cta_t0"]:
        captions(im, t)
    return im.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 5 and sys.argv[5] == "still":
        frame(p0).save(out); sys.exit()
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    n0, n1 = int(round(p0 * FPS)), int(round(p1 * FPS))
    for n in range(n0, n1):
        ff.stdin.write(frame(n / FPS).tobytes())
    ff.stdin.close(); ff.wait()

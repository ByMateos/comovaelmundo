"""Animated Short renderer, style A2 (refined big captions).
usage: short_a2.py spec.json
spec: {"out": path, "topic": "Economía", "series": "EXPLICADO FÁCIL", "music": mp3, "music_start": 22,
       "footer": "...", "scenes": [ {type, dur, ...}, ... ]}
scene types:
  hook  : kicker, line, pill, sub
  text  : kicker, title, sub
  big   : kicker, from, to, decimals, prefix, suffix, unit, note
  bars  : kicker, rows:[[label, value, sublabel, highlight]], unit, note
  cta   : line1, line2, note
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import style_a2 as S

W, H, FPS = S.W, S.H, 25
F, FBK, FXB, FB, FS, FM = S.F, S.FBK, S.FXB, S.FB, S.FS, S.FM
INK, WHITE, SOFT, DIM, YEL, AMB, CYAN, VIO = S.INK, S.WHITE, S.SOFT, S.DIM, S.YEL, S.AMB, S.CYAN, S.VIO
ACCENTS = [(S.VIO, S.CYAN), (S.AMB, S.VIO), (S.CYAN, S.VIO), (S.VIO, S.AMB)]
MARGIN = 96
TEXT_W = W - 2 * MARGIN


def ease_out(t):
    t = min(1, max(0, t))
    return 1 - (1 - t) ** 3


def ease_back(t, s=1.6):
    t = min(1, max(0, t))
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


# ---------- element builders (RGBA, tightly cropped) ----------
def rgba_text(txt, font, fill, glow=None, glow_r=34, glow_k=0.5, track=0):
    pad = glow_r * 2 if glow else 8
    tmp = Image.new("L", (10, 10))
    dd = ImageDraw.Draw(tmp)
    if track:
        w = sum(dd.textlength(c, font=font) for c in txt) + track * (len(txt) - 1)
    else:
        w = dd.textlength(txt, font=font)
    asc, desc = font.getmetrics()
    h = asc + desc
    im = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
    mask = Image.new("L", im.size, 0)
    md = ImageDraw.Draw(mask)
    if track:
        x = pad
        for c in txt:
            md.text((x, pad), c, font=font, fill=255)
            x += md.textlength(c, font=font) + track
    else:
        md.text((pad, pad), txt, font=font, fill=255)
    if glow:
        g = mask.filter(ImageFilter.GaussianBlur(glow_r)).point(lambda v: int(v * glow_k))
        gl = Image.new("RGBA", im.size, glow + (0,))
        gl.putalpha(g)
        im = Image.alpha_composite(im, gl)
    if isinstance(fill, tuple) and len(fill) == 2 and isinstance(fill[0], tuple):
        c1, c2 = fill
        bb = mask.getbbox() or (0, 0, 1, 1)
        grad = Image.new("RGBA", im.size)
        gd = ImageDraw.Draw(grad)
        for y in range(im.height):
            t = min(1, max(0, (y - bb[1]) / max(1, bb[3] - bb[1])))
            gd.line([(0, y), (im.width, y)], fill=tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(3)) + (255,))
        solid = grad
    else:
        solid = Image.new("RGBA", im.size, fill + (255,))
    solid.putalpha(mask)
    return Image.alpha_composite(im, solid)


def wrap(txt, font, maxw):
    dd = ImageDraw.Draw(Image.new("L", (1, 1)))
    lines, cur = [], ""
    for w in txt.split(" "):
        t = (cur + " " + w).strip()
        if dd.textlength(t, font=font) > maxw and cur:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    return lines


def pill_word(txt, font):
    dd = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = dd.textlength(txt, font=font)
    asc, desc = font.getmetrics()
    padx, pady, gl = 42, 22, 110
    bw, bh = int(tw + 2 * padx), int(asc + desc * 0.4 + 2 * pady)
    im = Image.new("RGBA", (bw + 2 * gl, bh + 2 * gl), (0, 0, 0, 0))
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([gl, gl, gl + bw, gl + bh], radius=36, fill=255)
    glow = Image.new("RGBA", im.size, (255, 190, 40, 0))
    glow.putalpha(m.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.45)))
    im = Image.alpha_composite(im, glow)
    grad = Image.new("RGBA", im.size)
    gd = ImageDraw.Draw(grad)
    for x in range(im.width):
        t = x / im.width
        gd.line([(x, 0), (x, im.height)], fill=tuple(int(YEL[i] * (1 - t) + AMB[i] * t) for i in range(3)) + (255,))
    grad.putalpha(m)
    im = Image.alpha_composite(im, grad)
    ImageDraw.Draw(im).text((gl + bw / 2, gl + bh / 2 + 4), txt, font=font, fill=INK + (255,), anchor="mm")
    return im


class El:
    """An animated element: RGBA image placed by centre, appearing at t0."""

    def __init__(self, img, cx, cy, t0, kind="rise", dur=0.38):
        self.img, self.cx, self.cy, self.t0, self.kind, self.dur = img, cx, cy, t0, kind, dur

    def draw(self, frame, t):
        u = (t - self.t0) / self.dur
        if u <= 0:
            return
        img = self.img
        if u < 1:
            a = ease_out(u)
            if self.kind == "pop":
                s = 0.6 + 0.4 * ease_back(u)
                img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.BILINEAR)
                dy = 0
            else:
                dy = (1 - a) * 46
            alpha = img.getchannel("A").point(lambda v: int(v * a))
            img = img.copy()
            img.putalpha(alpha)
        else:
            dy = 0
        frame.alpha_composite(img, (int(self.cx - img.width / 2), int(self.cy - img.height / 2 + dy)))


def word_line_els(txt, font, fill, cy, t0, stagger=0.07, maxw=TEXT_W, line_gap=1.18):
    """Split into lines, each word an element appearing one after another."""
    lines = wrap(txt, font, maxw)
    dd = ImageDraw.Draw(Image.new("L", (1, 1)))
    asc, desc = font.getmetrics()
    lh = (asc + desc) * line_gap
    y0 = cy - lh * (len(lines) - 1) / 2
    els, k = [], 0
    space = dd.textlength(" ", font=font)
    for li, ln in enumerate(lines):
        words = ln.split(" ")
        widths = [dd.textlength(w.replace("\u00a0", " "), font=font) for w in words]
        total = sum(widths) + space * (len(words) - 1)
        x = W / 2 - total / 2
        for w, wd in zip(words, widths):
            img = rgba_text(w.replace("\u00a0", " "), font, fill)
            els.append(El(img, x + wd / 2, y0 + li * lh, t0 + k * stagger))
            x += wd + space
            k += 1
    return els, y0 + lh * (len(lines) - 1) / 2 + lh / 2, t0 + k * stagger


def kicker_el(txt, cy, t0, col=CYAN):
    return El(rgba_text(txt, F(FB, 30), col, track=8), W / 2, cy, t0)


# ---------- scenes ----------
class Scene:
    def __init__(self, spec, idx):
        self.spec, self.dur = spec, spec["dur"]
        self.accent = ACCENTS[idx % len(ACCENTS)]
        if spec.get("accent") == "warm":
            self.accent = (S.AMB, S.VIO)
        if spec.get("accent") == "sober":
            self.accent = ((70, 78, 110), (44, 50, 74))
        self.els, self.dyn = [], None
        getattr(self, "build_" + spec["type"])(spec)

    def build_hook(self, s):
        self.els.append(kicker_el(s["kicker"], 640, 0.05))
        ls = 112
        while ls > 64 and F(FXB, ls).getlength(s["line"]) > 760:
            ls -= 4
        e, _, t = word_line_els(s["line"], F(FXB, ls), WHITE, 780, 0.15)
        self.els += e
        ps = 168
        while ps > 60 and F(FBK, ps).getlength(s["pill"]) > 760:
            ps -= 6
        self.els.append(El(pill_word(s["pill"], F(FBK, ps)), W / 2, 950, t + 0.1, kind="pop", dur=0.42))
        if s.get("sub"):
            e, _, _ = word_line_els(s["sub"], F(FS, 46), SOFT, 1140, t + 0.5, stagger=0.04)
            self.els += e

    def build_text(self, s):
        ft, fs_ = F(FXB, 92), F(FS, 42)
        nt = len(wrap(s["title"], ft, TEXT_W))
        lh_t = sum(ft.getmetrics()) * 1.18
        ns = len(wrap(s["sub"], fs_, TEXT_W)) if s.get("sub") else 0
        lh_s = sum(fs_.getmetrics()) * 1.18
        total = 50 + 60 + nt * lh_t + (50 + ns * lh_s if ns else 0)
        top = 900 - total / 2
        self.els.append(kicker_el(s["kicker"], top + 25, 0.05, s.get("kcol") and tuple(s["kcol"]) or CYAN))
        tcy = top + 110 + nt * lh_t / 2 - lh_t / 2 + lh_t / 2
        e, _, t = word_line_els(s["title"], ft, WHITE, top + 110 + (nt * lh_t) / 2, 0.15, stagger=0.07)
        self.els += e
        if ns:
            scy = top + 110 + nt * lh_t + 50 + ns * lh_s / 2
            e, _, _ = word_line_els(s["sub"], fs_, SOFT, scy, t + 0.25, stagger=0.035)
            self.els += e

    def build_big(self, s):
        self.els.append(kicker_el(s["kicker"], 560, 0.05, YEL))
        self.count = (s["from"], s["to"], s.get("decimals", 0), s.get("prefix", ""), s.get("suffix", ""))
        self.count_t = (0.2, 1.1)
        a_, b_, dec_, pre_, suf_ = self.count
        widest = pre_ + f"{b_:,.{dec_}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suf_
        self.cfs = 250
        while self.cfs > 120 and F(FBK, self.cfs).getlength(widest) > 900:
            self.cfs -= 10
        self.dyn = self.draw_count
        if s.get("unit"):
            self.els.append(El(rgba_text(s["unit"], F(FXB, 92), WHITE), W / 2, 960, 0.55))
        if s.get("note"):
            e, _, _ = word_line_els(s["note"], F(FM, 36), SOFT, 1080, 0.9, stagger=0.03)
            self.els += e
        self._cache = {}

    def draw_count(self, frame, t):
        a, b, dec, pre, suf = self.count
        t0, t1 = self.count_t
        u = ease_out((t - t0) / (t1 - t0)) if t > t0 else 0
        if t < t0:
            return
        v = a + (b - a) * u
        txt = pre + f"{v:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".") + suf
        if txt not in self._cache:
            self._cache[txt] = rgba_text(txt, F(FBK, getattr(self, 'cfs', 250)), ((255, 228, 115), AMB), glow=AMB, glow_r=40, glow_k=0.45)
        img = self._cache[txt]
        al = ease_out((t - t0) / 0.3)
        if al < 1:
            img = img.copy()
            img.putalpha(img.getchannel("A").point(lambda q: int(q * al)))
        frame.alpha_composite(img, (int(W / 2 - img.width / 2), int(770 - img.height / 2)))

    def build_bars(self, s):
        self.els.append(kicker_el(s["kicker"], 600, 0.05, YEL))
        if s.get("title"):
            e, _, _ = word_line_els(s["title"], F(FXB, 72), WHITE, 720, 0.12, stagger=0.06)
            self.els += e
        self.rows = s["rows"]
        self.unit = s.get("unit", "")
        self.dec = s.get("decimals", 0)
        self.pre = s.get("prefix", "")
        self.vmax = max(r[1] for r in self.rows)
        self.dyn = self.draw_bars
        self.card_box = (110, 860, W - 110, 860 + 100 + 150 * len(self.rows))
        if s.get("note"):
            e, _, _ = word_line_els(s["note"], F(FM, 30), DIM, self.card_box[3] + 70, 1.0, stagger=0.02)
            self.els += e

    def draw_bars(self, frame, t):
        a = ease_out((t - 0.2) / 0.35)
        if a <= 0:
            return
        x0, y0, x1, y1 = self.card_box
        card = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, card.width - 1, card.height - 1], radius=44, fill=(255, 255, 255, int(16 * a)), outline=(255, 255, 255, int(40 * a)), width=2)
        for i, (lab, val, sub, hi) in enumerate(self.rows):
            ry = 90 + i * 150
            ta = ease_out((t - 0.35 - i * 0.18) / 0.3)
            cd.text((50, ry), lab, font=F(FS, 36), fill=SOFT + (int(255 * ta),), anchor="lm")
            if sub:
                cd.text((50, ry + 46), sub, font=F(FM, 26), fill=DIM + (int(255 * ta),), anchor="lm")
            bx0, bx1 = 340, card.width - 280
            cd.rounded_rectangle([bx0, ry - 8, bx1, ry + 24], radius=16, fill=(40, 44, 68, int(255 * a)))
            g = ease_out((t - 0.45 - i * 0.25) / 0.7)
            bw = (bx1 - bx0) * (val / self.vmax) * g
            if bw > 4:
                col = YEL if hi else (96, 104, 136)
                cd.rounded_rectangle([bx0, ry - 8, bx0 + bw, ry + 24], radius=16, fill=col + (255,))
            shown = val * g
            cd.text((card.width - 50, ry + 8), self.pre + f"{shown:,.{self.dec}f}".replace(",", "X").replace(".", ",").replace("X", ".") + self.unit, font=F(FXB, 42), fill=WHITE + (int(255 * ta),), anchor="rm")
        frame.alpha_composite(card, (x0, int(y0 + (1 - a) * 40)))

    def build_cta(self, s):
        self.els.append(El(S.logo_mark(150)[0].convert("RGBA"), W / 2, 740, 0.05, kind="pop", dur=0.5))
        m, al = S.logo_mark(150)
        lg = m.convert("RGBA")
        lg.putalpha(al)
        self.els[-1].img = lg
        e, _, t = word_line_els(s["line1"], F(FXB, 70), WHITE, 1000, 0.35)
        self.els += e
        e, _, t = word_line_els(s["line2"], F(FXB, 70), WHITE, 1084, t)
        self.els += e
        if not s.get('no_button'):  # subscribe button
            bw, bh, gl = 440, 104, 120
            b = Image.new("RGBA", (bw + 2 * gl, bh + 2 * gl), (0, 0, 0, 0))
            m = Image.new("L", b.size, 0)
            ImageDraw.Draw(m).rounded_rectangle([gl, gl, gl + bw, gl + bh], radius=52, fill=255)
            glow = Image.new("RGBA", b.size, (255, 40, 70, 0))
            glow.putalpha(m.filter(ImageFilter.GaussianBlur(40)).point(lambda v: int(v * 0.55)))
            b = Image.alpha_composite(b, glow)
            solid = Image.new("RGBA", b.size, (240, 36, 64, 255))
            solid.putalpha(m)
            b = Image.alpha_composite(b, solid)
            lab = rgba_text("SUSCRÍBETE", F(FBK, 40), WHITE, track=5)
            b.alpha_composite(lab, (int(b.width / 2 - lab.width / 2), int(b.height / 2 - lab.height / 2) + 2))
            self.els.append(El(b, W / 2, 1272, t + 0.15, kind="pop", dur=0.45))
        note_y = 1420
        if s.get("next"):
            nx = rgba_text(s.get("next_label", "Mañana: ") + s["next"], F(FXB, 42), YEL)
            self.els.append(El(nx, W / 2, 1420, t + 0.45, kind="pop"))
            note_y = 1500
        if s.get("note"):
            self.els.append(El(rgba_text(s["note"], F(FM, 28), DIM), W / 2, note_y, t + 0.6))

    def render(self, frame, t):
        for e in self.els:
            e.draw(frame, t)
        if self.dyn:
            self.dyn(frame, t)


# ---------- chrome ----------
def header_layer(topic, series):
    im = Image.new("RGBA", (W, 230), (0, 0, 0, 0))
    m, a = S.logo_mark(30)
    lg = m.convert("RGBA")
    lg.putalpha(a)
    im.alpha_composite(lg, (104 - lg.width // 2, 160 - lg.height // 2))
    d = ImageDraw.Draw(im)
    d.text((152, 146), "Cómo Va el Mundo", font=F(FB, 32), fill=WHITE, anchor="lm")
    d.text((152, 182), topic, font=F(FM, 26), fill=SOFT, anchor="lm")
    tag = rgba_text(series, F(FB, 24), WHITE, track=4)
    tw = tag.width + 30
    d.rounded_rectangle([W - 64 - tw, 136, W - 64, 186], radius=25, outline=(90, 98, 130, 255), width=2)
    im.alpha_composite(tag, (int(W - 64 - tw / 2 - tag.width / 2), int(161 - tag.height / 2)))
    return im


def draw_progress(frame, scene_i, n, u):
    d = ImageDraw.Draw(frame)
    gap, x0, x1, y = 10, 64, W - 64, 74
    sw = (x1 - x0 - gap * (n - 1)) / n
    for i in range(n):
        sx = x0 + i * (sw + gap)
        d.rounded_rectangle([sx, y, sx + sw, y + 7], radius=4, fill=(52, 58, 84, 255))
        f = 1 if i < scene_i else (u if i == scene_i else 0)
        if f > 0:
            d.rounded_rectangle([sx, y, sx + max(8, sw * f), y + 7], radius=4, fill=WHITE + (255,))


def big_bg(accent):
    # slightly oversized so we can drift the camera
    old = (S.W, S.H)
    S.W, S.H = W + 80, H + 80
    im = S.mesh_bg(accent=accent)
    S.W, S.H = old
    return im


def photo_bg(sc):
    """Real photo (licensed) as background: cover-crop, darken, blend with the brand mesh."""
    from PIL import ImageOps, ImageEnhance
    BW, BH = W + 80, H + 80
    ph = Image.open(sc.spec["photo"]).convert("RGB")
    ph = ImageOps.fit(ph, (BW, BH), Image.LANCZOS, centering=tuple(sc.spec.get("photo_center", (0.5, 0.5))))
    ph = ImageEnhance.Color(ph).enhance(0.8)
    ph = ImageEnhance.Brightness(ph).enhance(0.62)
    mesh = big_bg(sc.accent).convert("RGB").resize((BW, BH))
    im = Image.blend(ph, mesh, 0.2)
    # darker band behind the text block
    g = Image.new("L", (1, BH))
    for y in range(BH):
        c = abs(y - BH * 0.45) / (BH * 0.45)
        g.putpixel((0, y), int(165 * max(0, 1 - c) ** 1.1))
    shade = Image.new("RGB", (BW, BH), (6, 8, 16))
    im = Image.composite(shade, im, g.resize((BW, BH)))
    return im.convert(big_bg(sc.accent).mode)


def main(spec_path):
    spec = json.load(open(spec_path))
    scenes = [Scene(s, i) for i, s in enumerate(spec["scenes"])]
    bgs = [photo_bg(sc) if sc.spec.get('photo') else big_bg(sc.accent) for sc in scenes]
    head = header_layer(spec.get("topic", "Economía"), spec.get("series", "EXPLICADO FÁCIL"))
    footer = spec.get("footer")
    foot = rgba_text(footer, F(FM, 26), DIM) if footer else None
    total = sum(sc.dur for sc in scenes)
    out = spec["out"]
    tmpv = out + ".video.mp4"
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmpv], stdin=subprocess.PIPE)
    XF = 0.28
    t_start = 0
    for i, sc in enumerate(scenes):
        n = int(round(sc.dur * FPS))
        for k in range(n):
            t = k / FPS
            gt = t_start + t
            # camera drift on background
            ox = int(40 + 30 * math.sin(gt * 0.35))
            oy = int(40 + 30 * math.cos(gt * 0.27))
            bg = bgs[i].crop((ox, oy, ox + W, oy + H))
            if i > 0 and t < XF:
                prev = bgs[i - 1].crop((ox, oy, ox + W, oy + H))
                bg = Image.blend(prev, bg, ease_out(t / XF))
            frame = bg.convert("RGBA")
            # previous scene content fades out quickly at start of this one
            if i > 0 and t < XF * 0.8:
                ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                scenes[i - 1].render(ghost, scenes[i - 1].dur)
                a = 1 - t / (XF * 0.8)
                ghost.putalpha(ghost.getchannel("A").point(lambda v: int(v * a)))
                frame.alpha_composite(ghost, (0, int(-30 * (1 - a))))
            sc.render(frame, t - (XF * 0.5 if i > 0 else -spec.get("hook_head_start", 0.75)))
            frame.alpha_composite(head)
            draw_progress(frame, i, len(scenes), t / sc.dur)
            if foot:
                frame.alpha_composite(foot, (int(W / 2 - foot.width / 2), 1650))
            ff.stdin.write(frame.convert("RGB").tobytes())
        # keyframe preview
        prev = Image.new("RGBA", (W, H))
        t_start += sc.dur
    ff.stdin.close()
    ff.wait()
    # music bed
    ms = spec.get("music_start", 0)
    vol = spec.get("music_volume", 0.8)
    fo = max(0, total - 1.6)
    if spec.get("voice"):
        vd = int(spec.get("voice_delay", 0.15) * 1000)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmpv, "-ss", str(ms), "-t", str(total), "-i", spec["music"], "-i", spec["voice"],
                        "-filter_complex", f"[1:a]afade=t=in:st=0:d=0.25,afade=t=out:st={fo}:d=1.6,volume={vol}[m];[2:a]adelay={vd}|{vd}[v];[v][m]amix=inputs=2:duration=first:normalize=0,apad[a]",
                        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(total), "-movflags", "+faststart", out], check=True)
    else:
      subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", tmpv, "-ss", str(ms), "-t", str(total), "-i", spec["music"],
                    "-filter_complex", f"[1:a]afade=t=in:st=0:d=0.25,afade=t=out:st={fo}:d=1.6,volume={vol}[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], check=True)
    os.remove(tmpv)
    print("ok", out, round(total, 1), "s")


if __name__ == "__main__":
    main(sys.argv[1])

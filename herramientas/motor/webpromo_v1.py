"""Promo Short: new website. usage: webpromo.py total outro_start out.mp4 [voice.wav]"""
import sys, os, glob, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import style_a2 as S
W, H, FPS = 1080, 1920, 30
F = lambda p, s: ImageFont.truetype(p, s)
INK, WHITE, SOFT, YEL, CYAN, VIO, RED = S.INK, S.WHITE, S.SOFT, S.YEL, S.CYAN, S.VIO, (238, 36, 66)
TOTAL, OUTRO = float(sys.argv[1]), float(sys.argv[2])
OUT = sys.argv[3]
VOICE = sys.argv[4] if len(sys.argv) > 4 else None
FR = sorted(glob.glob(os.path.join(D, "webframes", "f*.jpg")))
LOGO = Image.open("/home/claude/canal/logo_comovaelmundo_v2_circular.png").convert("RGBA")

def eo(t): t = min(1, max(0, t)); return 1 - (1 - t) ** 3
def eb(t, s=1.5):
    t = min(1, max(0, t)) - 1; return t * t * ((s + 1) * t + s) + 1

# background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
bg = np.zeros((H, W, 3), np.float32) + np.array(INK, np.float32)
for cx, cy, r, col, k in [(180, 300, 900, VIO, .35), (950, 1500, 950, CYAN, .18), (900, 200, 600, YEL, .08)]:
    g = np.exp(-((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * (r / 2) ** 2))[..., None]
    bg += g * (np.array(col, np.float32) - bg) * k
BG = Image.fromarray(bg.clip(0, 255).astype(np.uint8))
gd = ImageDraw.Draw(BG)
for x in range(0, W, 90): gd.line([(x, 0), (x, H)], fill=(255, 255, 255, 0), width=1)
BG = Image.blend(Image.fromarray(bg.clip(0, 255).astype(np.uint8)), BG, 0.06)

def text_img(txt, font, fill, track=0, glow=None):
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    w = sum(d.textlength(c, font=font) for c in txt) + track * (len(txt) - 1) if track else d.textlength(txt, font=font)
    a, de = font.getmetrics(); pad = 40
    m = Image.new("L", (int(w) + 2 * pad, a + de + 2 * pad), 0); md = ImageDraw.Draw(m)
    if track:
        x = pad
        for c in txt: md.text((x, pad), c, font=font, fill=255); x += md.textlength(c, font=font) + track
    else: md.text((pad, pad), txt, font=font, fill=255)
    im = Image.new("RGBA", m.size, fill + (0,))
    if glow:
        gl = m.filter(ImageFilter.GaussianBlur(18)).point(lambda v: int(v * .55))
        gi = Image.new("RGBA", m.size, glow + (0,)); gi.putalpha(gl); im = Image.alpha_composite(im, gi)
    ti = Image.new("RGBA", m.size, fill + (0,)); ti.putalpha(m)
    return Image.alpha_composite(im, ti)

def paste_c(base, im, cx, cy, alpha=1.0, scale=1.0):
    if scale != 1.0: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.LANCZOS)
    if alpha < 1: a = im.getchannel("A").point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def pill(txt, font, fg, bgc, padx=46, pady=22, border=None):
    d = ImageDraw.Draw(Image.new("L", (1, 1))); w = d.textlength(txt, font=font); a, de = font.getmetrics()
    im = Image.new("RGBA", (int(w + 2 * padx), a + de + 2 * pady), (0, 0, 0, 0)); dd = ImageDraw.Draw(im)
    dd.rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius=im.height // 2, fill=bgc, outline=border, width=3 if border else 0)
    dd.text((padx, pady), txt, font=font, fill=fg); return im

KICK = text_img("NUEVO  ·  CÓMO VA EL MUNDO", F(S.FB, 34), CYAN, track=6)
HEAD1 = text_img("¡Estrenamos", F(S.FBK, 118), WHITE)
HEAD2 = text_img("página web!", F(S.FBK, 118), YEL, glow=(255, 160, 40))
URLP = pill("comovaelmundo.pages.dev", F(S.FXB, 52), WHITE, (20, 24, 44, 235), border=CYAN)
# phone
PW, PH = 640, 1280
mask = Image.new("L", (PW, PH), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, PW - 1, PH - 1], 56, fill=255)
BEZ = Image.new("RGBA", (PW + 36, PH + 36), (0, 0, 0, 0)); bd = ImageDraw.Draw(BEZ)
bd.rounded_rectangle([0, 0, BEZ.width - 1, BEZ.height - 1], 72, fill=(28, 32, 52, 255), outline=(90, 100, 140, 255), width=3)
SH = Image.new("RGBA", (BEZ.width + 200, BEZ.height + 200), (0, 0, 0, 0))
ImageDraw.Draw(SH).rounded_rectangle([100, 100, 100 + BEZ.width, 100 + BEZ.height], 72, fill=(120, 90, 255, 140))
SH = SH.filter(ImageFilter.GaussianBlur(50))
_cache = {}
def phone(t):
    i = min(len(FR) - 1, max(0, int((t - 0.3) * FPS)))
    if i in _cache: return _cache[i]
    s = Image.open(FR[i]).convert("RGB").resize((PW, PH), Image.LANCZOS)
    ph = Image.new("RGBA", (SH.width, SH.height), (0, 0, 0, 0)); ph.alpha_composite(SH)
    ph.alpha_composite(BEZ, (100, 100)); scr = Image.new("RGBA", (PW, PH)); scr.paste(s, (0, 0)); scr.putalpha(mask)
    ph.alpha_composite(scr, (118, 118))
    # notch
    _cache.clear(); _cache[i] = ph; return ph

# outro elements
LOGOB = LOGO.resize((300, 300), Image.LANCZOS)
O1 = text_img("Entra ya en", F(S.FXB, 70), SOFT)
O2 = text_img("comovaelmundo", F(S.FBK, 120), WHITE, glow=(132, 94, 255))
O3 = text_img(".pages.dev", F(S.FBK, 120), YEL, glow=(255, 160, 40))
O4 = pill("Enlace en el perfil", F(S.FB, 50), WHITE, RED + (255,))

def frame(t):
    im = BG.convert("RGBA").copy()
    o = eo((t - OUTRO) / 0.6)  # outro progress
    if o < 1:
        a = 1 - o
        paste_c(im, KICK, W / 2, 130 - 30 * (1 - eo(t / .5)), alpha=a * eo(t / .5))
        paste_c(im, HEAD1, W / 2, 235, alpha=a * eo((t - .15) / .5), scale=0.85 + 0.15 * eb((t - .15) / .5))
        paste_c(im, HEAD2, W / 2, 355, alpha=a * eo((t - .35) / .5), scale=0.85 + 0.15 * eb((t - .35) / .5))
        ph = phone(t); k = eb((t - .3) / .8)
        cy = 455 + ph.height / 2 - 100 + (1 - k) * 900 + o * 300
        paste_c(im, ph, W / 2, cy, alpha=a * min(1, k + .001), scale=1 - .15 * o)
        paste_c(im, URLP, W / 2, 1812 + (1 - eo((t - 1) / .6)) * 120, alpha=a * eo((t - 1) / .6))
    if o > 0:
        p = lambda d: eo((t - OUTRO - d) / .6)
        paste_c(im, LOGOB, W / 2, 560, alpha=p(0), scale=.7 + .3 * eb((t - OUTRO) / .7))
        paste_c(im, O1, W / 2, 820 + 40 * (1 - p(.15)), alpha=p(.15))
        paste_c(im, O2, W / 2, 960, alpha=p(.3), scale=.9 + .1 * eb((t - OUTRO - .3) / .6))
        paste_c(im, O3, W / 2, 1095, alpha=p(.45), scale=.9 + .1 * eb((t - OUTRO - .45) / .6))
        pul = 1 + .04 * math.sin((t - OUTRO) * 6) * p(.7)
        paste_c(im, O4, W / 2, 1330, alpha=p(.7), scale=pul)
    return im.convert("RGB")

if __name__ == "__main__":
    if len(sys.argv) > 5:
        for tt in map(float, sys.argv[5].split(",")): frame(tt).save(os.path.join(D, f"wp_{tt}.jpg"), quality=85)
        sys.exit()
    vid = OUT + ".v.mp4"
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", vid], stdin=subprocess.PIPE)
    for f in range(int(TOTAL * FPS)): p.stdin.write(frame(f / FPS).tobytes())
    p.stdin.close(); p.wait()
    mus = os.path.join(D, "music", "nebula.mp3")
    if VOICE:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-i", VOICE, "-ss", "20", "-i", mus, "-filter_complex",
               "[1:a]adelay=500|500,volume=1.0[v];[2:a]volume=0.10,afade=t=out:st=%.2f:d=1.2[m];[v][m]amix=inputs=2:duration=longest:normalize=0[a]" % (TOTAL - 1.3),
               "-map", "0:v", "-map", "[a]", "-t", str(TOTAL), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", OUT]
    else:
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", vid, "-ss", "20", "-i", mus, "-map", "0:v", "-map", "1:a", "-t", str(TOTAL), "-c:v", "copy", "-c:a", "aac", OUT]
    subprocess.run(cmd, check=True); os.remove(vid); print("ok", OUT)

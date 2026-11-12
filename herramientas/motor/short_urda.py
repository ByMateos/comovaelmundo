"""Sober breaking-news Short (1080x1920, text only) on the Urda (Toledo) train accident."""
import subprocess
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 25
OUT = "/home/claude/canal/short/short_accidente_urda.mp4"
FBK = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
BG, CARD = (12, 14, 22), (24, 28, 40)
WHITE, MUTED, RED, AMBER = (240, 242, 248), (160, 168, 186), (220, 60, 60), (240, 190, 70)
_f = {}


def F(p, s):
    if (p, s) not in _f:
        _f[(p, s)] = ImageFont.truetype(p, s)
    return _f[(p, s)]


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


# each card: (seconds, list of (kind, text)) ; kinds: big, mid, small, red
CARDS = [
    (4.5, [("tag", "ÚLTIMA HORA"), ("big", "Choque de dos trenes en Urda (Toledo)"), ("small", "Miércoles 28 de octubre · hacia las 8:54")]),
    (5.0, [("mid", "Un tren Iryo y un AVE de Renfe, ambos en la línea Madrid–Sevilla"), ("small", "Dos vagones cayeron por un terraplén")]),
    (5.5, [("red", "Al menos 10 fallecidos"), ("mid", "y varios heridos"), ("small", "Gobierno de Castilla-La Mancha, 11:15. La cifra puede aumentar")]),
    (5.0, [("mid", "La causa aún no está confirmada"), ("small", "Desconfía de cifras y vídeos sin fuente que circulan en redes")]),
    (5.5, [("tag", "SI VIAJAS"), ("mid", "Circulación interrumpida entre Madrid, Ciudad Real y Andalucía"), ("small", "Renfe: cambios y anulaciones gratis")]),
    (6.5, [("tag", "TELÉFONOS"), ("mid", "Emergencias 112: 900 122 112"), ("mid", "Renfe: 900 10 10 20"), ("mid", "Iryo: 655 28 69 75")]),
    (5.5, [("mid", "No acudas a urgencias de Toledo, Ciudad Real y Mancha Centro salvo extrema urgencia"), ("mid", "Se pide donar sangre")]),
    (4.5, [("small", "Nuestro recuerdo para las víctimas y sus familias"), ("small", "Cómo Va el Mundo")]),
]

STYLE = {"tag": (FB, 40, AMBER), "big": (FBK, 86, WHITE), "mid": (FB, 58, WHITE), "red": (FBK, 92, RED), "small": (FS, 40, MUTED)}


def render_card(items):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    # top bar
    d.rectangle([0, 0, W, 14], fill=RED)
    d.text((80, 210), "ÚLTIMA HORA · ACCIDENTE FERROVIARIO", font=F(FB, 32), fill=MUTED)
    blocks = []
    for kind, text in items:
        font, size, col = STYLE[kind]
        f = F(font, size)
        lines = wrap(d, text, f, W - 220)
        blocks.append((lines, f, size, col, kind))
    total = sum(len(l) * s * 1.3 + 46 for l, f, s, c, k in blocks)
    y = max(380, (H - total) / 2 - 80)
    d.rounded_rectangle([60, y - 70, W - 60, y + total + 30], radius=36, fill=CARD)
    for lines, f, size, col, kind in blocks:
        for ln in lines:
            y += size
            d.text((110, y), ln, font=f, fill=col)
            y += size * 0.3
        y += 46
    d.text((80, H - 360), "Datos oficiales a las 11:15 del 28/10/2026", font=F(FS, 30), fill=MUTED)
    return im


def main():
    cards = [(dur, render_card(items)) for dur, items in CARDS]
    ff = subprocess.Popen(["ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-shortest",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    black = Image.new("RGB", (W, H), BG)
    for i, (dur, img) in enumerate(cards):
        n = int(dur * FPS)
        fade = int(0.35 * FPS)
        for k in range(n):
            if k < fade:
                frame = Image.blend(black if i == 0 else cards[i - 1][1], img, k / fade)
            else:
                frame = img
            ff.stdin.write(frame.tobytes())
        img.resize((360, 640)).save(f"/tmp/claude-0/-home-claude/3f8f79a9-c46c-53fb-baec-2bfb3165bcc1/scratchpad/urda_{i}.jpg")
    ff.stdin.close()
    ff.wait()
    print("ok", sum(d for d, _ in CARDS), "s")


main()

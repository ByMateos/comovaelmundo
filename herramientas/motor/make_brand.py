from PIL import Image, ImageDraw, ImageFont
import math

NAVY = (11, 27, 51)
NAVY2 = (20, 44, 80)
WHITE = (245, 247, 250)
GRID = (120, 150, 190)
YELLOW = (255, 201, 60)
FONT_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
OUT = "/home/claude/canal/"


def draw_mark(d, cx, cy, r, s):
    """Globe with meridians + rising arrow. s = line scale."""
    # globe outline
    lw = int(r * 0.07)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=lw)
    thin = max(2, int(r * 0.035))
    # meridians (ellipses)
    for k in (0.38, 0.75):
        d.ellipse([cx - r * k, cy - r, cx + r * k, cy + r], outline=GRID, width=thin)
    d.line([cx, cy - r + lw, cx, cy + r - lw], fill=GRID, width=thin)
    # parallels
    for f in (-0.5, 0, 0.5):
        y = cy + f * r
        ri = r - lw; half = math.sqrt(max(0, ri * ri - (f * r) ** 2))
        d.line([cx - half, y, cx + half, y], fill=GRID, width=thin)
    # rising zigzag arrow crossing the globe
    pts = [(-1.05, 0.55), (-0.45, 0.05), (-0.05, 0.35), (0.75, -0.55)]
    P = [(cx + x * r, cy + y * r) for x, y in pts]
    aw = int(r * 0.14)
    d.line(P, fill=YELLOW, width=aw, joint="curve")
    for p in P[:-1]:
        d.ellipse([p[0] - aw / 2, p[1] - aw / 2, p[0] + aw / 2, p[1] + aw / 2], fill=YELLOW)
    # arrow head
    (x1, y1), (x2, y2) = P[-2], P[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    L = r * 0.42
    tip = (x2 + math.cos(ang) * L * 0.55, y2 + math.sin(ang) * L * 0.55)
    left = (tip[0] - L * math.cos(ang - 0.5), tip[1] - L * math.sin(ang - 0.5))
    right = (tip[0] - L * math.cos(ang + 0.5), tip[1] - L * math.sin(ang + 0.5))
    d.polygon([tip, left, right], fill=YELLOW)


def logo(size=800, ss=4):
    S = size * ss
    im = Image.new("RGB", (S, S), NAVY)
    d = ImageDraw.Draw(im)
    # subtle radial-ish inner disc
    d.ellipse([S * 0.08, S * 0.08, S * 0.92, S * 0.92], fill=NAVY2)
    draw_mark(d, S / 2, S / 2, S * 0.30, ss)
    im = im.resize((size, size), Image.LANCZOS)
    im.save(OUT + "logo_comovaelmundo_800.png")
    # circular preview (how YouTube crops it)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    prev = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    prev.paste(im, (0, 0), mask)
    prev.save(OUT + "logo_comovaelmundo_circular.png")


def banner(ss=2):
    W, H = 2560 * ss, 1440 * ss
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    # faint world grid lines across the banner
    for i in range(0, W, 160 * ss):
        d.line([i, 0, i, H], fill=(16, 36, 66), width=2 * ss)
    for j in range(0, H, 160 * ss):
        d.line([0, j, W, j], fill=(16, 36, 66), width=2 * ss)
    # safe area 1546x423 centred
    sx0 = (W - 1546 * ss) / 2
    cy = H / 2
    r = 150 * ss
    mx = sx0 + r + 20 * ss
    d.ellipse([mx - r * 1.25, cy - r * 1.25, mx + r * 1.25, cy + r * 1.25], fill=NAVY2)
    draw_mark(d, mx, cy, r, ss)
    f1 = ImageFont.truetype(FONT_BOLD, 120 * ss)
    f2 = ImageFont.truetype(FONT_MED, 44 * ss)
    tx = mx + r * 1.25 + 60 * ss
    d.text((tx, cy - 20 * ss), "Cómo Va el Mundo", font=f1, fill=WHITE, anchor="ls")
    d.text((tx, cy + 60 * ss), "Lo que pasa en el mundo, y lo que", font=f2, fill=GRID, anchor="ls")
    d.text((tx, cy + 120 * ss), "significa para tu bolsillo", font=f2, fill=YELLOW, anchor="ls")
    im = im.resize((2560, 1440), Image.LANCZOS)
    im.save(OUT + "banner_comovaelmundo_2560x1440.png")
    # check text fits inside safe area
    right = (tx + d.textlength("Cómo Va el Mundo", font=f1)) / ss
    print("text right edge:", right, "safe right:", (2560 + 1546) / 2)


logo()
banner()
print("done")

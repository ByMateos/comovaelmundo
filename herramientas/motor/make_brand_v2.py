from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import math

BG_IN = (16, 24, 52)
BG_OUT = (4, 6, 14)
CYAN = (34, 211, 238)
VIOLET = (139, 92, 246)
YELLOW = (255, 214, 10)
WHITE = (240, 244, 255)
MUTED = (140, 160, 200)
F_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
F_XB = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_MED = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
OUT = "/home/claude/canal/"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def radial_bg(W, H, cx, cy, R):
    bg = Image.new("RGB", (W, H), BG_OUT)
    small = Image.new("RGB", (W // 8, H // 8))
    px = small.load()
    for y in range(small.height):
        for x in range(small.width):
            d = math.hypot(x * 8 - cx, y * 8 - cy) / R
            px[x, y] = lerp(BG_IN, BG_OUT, min(1, d) ** 0.8)
    return small.resize((W, H), Image.BICUBIC)


def glow(layer, radius):
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    return ImageChops.add(g, g)


def mark_layer(W, H, cx, cy, r):
    """Returns RGB layer (black bg) with dot globe, orbit and arrow."""
    L = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(L)
    tilt = math.radians(22)
    rot = math.radians(-30)
    dot = r * 0.028
    # orbit ring (back half first, dimmer)
    ring = []
    for i in range(361):
        a = math.radians(i)
        x, y = 1.42 * math.cos(a), 0.36 * math.sin(a)
        ang = math.radians(-18)
        xr, yr = x * math.cos(ang) - y * math.sin(ang), x * math.sin(ang) + y * math.cos(ang)
        ring.append((cx + xr * r, cy + yr * r, math.sin(a)))
    for i in range(len(ring) - 1):
        x1, y1, z = ring[i]
        x2, y2, _ = ring[i + 1]
        c = lerp(VIOLET, CYAN, (math.cos(math.radians(i)) + 1) / 2)
        if z < 0:
            c = tuple(int(v * 0.35) for v in c)
        d.line([x1, y1, x2, y2], fill=c, width=max(2, int(r * 0.018)))
    # dot-matrix sphere
    for lat in range(-80, 81, 10):
        n = max(6, int(36 * math.cos(math.radians(lat))))
        for k in range(n):
            lon = 2 * math.pi * k / n + rot
            la = math.radians(lat)
            x = math.cos(la) * math.sin(lon)
            y = math.sin(la)
            z = math.cos(la) * math.cos(lon)
            # tilt around x axis
            y2 = y * math.cos(tilt) - z * math.sin(tilt)
            z2 = y * math.sin(tilt) + z * math.cos(tilt)
            if z2 < -0.05:
                continue
            t = (x + 1) / 2
            c = lerp(CYAN, VIOLET, t)
            b = 0.35 + 0.65 * max(0, z2)
            c = tuple(int(v * b) for v in c)
            s = dot * (0.45 + 0.75 * max(0, z2))
            px, py = cx + x * r, cy - y2 * r
            d.ellipse([px - s, py - s, px + s, py + s], fill=c)
    # sphere rim
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=lerp(CYAN, VIOLET, 0.5), width=max(2, int(r * 0.012)))
    return L


def arrow_layer(W, H, cx, cy, r):
    A = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(A)
    pts = [(-1.15, 0.62), (-0.42, -0.02), (0.02, 0.30), (0.78, -0.58)]
    P = [(cx + x * r, cy + y * r) for x, y in pts]
    w = int(r * 0.075)
    d.line(P, fill=YELLOW, width=w, joint="curve")
    for p in P[1:-1]:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=YELLOW)
    (x1, y1), (x2, y2) = P[-2], P[-1]
    ang = math.atan2(y2 - y1, x2 - x1)
    Lh = r * 0.30
    tip = (x2 + math.cos(ang) * Lh * 0.6, y2 + math.sin(ang) * Lh * 0.6)
    left = (tip[0] - Lh * math.cos(ang - 0.45), tip[1] - Lh * math.sin(ang - 0.45))
    right = (tip[0] - Lh * math.cos(ang + 0.45), tip[1] - Lh * math.sin(ang + 0.45))
    d.polygon([tip, left, right], fill=YELLOW)
    # start node: small ring
    s = w * 1.1
    p0 = P[0]
    d.ellipse([p0[0] - s, p0[1] - s, p0[0] + s, p0[1] + s], fill=YELLOW)
    return A


def compose_mark(base, cx, cy, r, ss):
    W, H = base.size
    m = mark_layer(W, H, cx, cy, r)
    a = arrow_layer(W, H, cx, cy, r)
    out = ImageChops.add(base, glow(m, 18 * ss))
    out = ImageChops.add(out, m)
    out = ImageChops.add(out, glow(a, 22 * ss))
    # arrow painted on top solidly
    mask = a.convert("L").point(lambda v: 255 if v > 10 else 0)
    out.paste(a, (0, 0), mask)
    return out


def logo(size=800, ss=3):
    S = size * ss
    base = radial_bg(S, S, S / 2, S / 2, S * 0.62)
    # thin outer tech ring
    d = ImageDraw.Draw(base)
    out = compose_mark(base, S / 2, S / 2 + S * 0.01, S * 0.27, ss)
    d = ImageDraw.Draw(out)
    R = S * 0.44
    for i in range(0, 360, 3):
        a1, a2 = math.radians(i), math.radians(i + 1.4)
        c = lerp(CYAN, VIOLET, (math.sin(math.radians(i)) + 1) / 2)
        c = tuple(int(v * 0.45) for v in c)
        d.arc([S / 2 - R, S / 2 - R, S / 2 + R, S / 2 + R], i, i + 1.4, fill=c, width=int(3 * ss))
    im = out.resize((size, size), Image.LANCZOS)
    im.save(OUT + "logo_comovaelmundo_v2_800.png")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    prev = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    prev.paste(im, (0, 0), mask)
    prev.save(OUT + "logo_comovaelmundo_v2_circular.png")


def gradient_text(img, xy, text, font, c1, c2):
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255, anchor="ls")
    bbox = mask.getbbox()
    grad = Image.new("RGB", (W, H))
    gd = ImageDraw.Draw(grad)
    x0, x1 = bbox[0], bbox[2]
    for x in range(x0, x1 + 1):
        gd.line([x, bbox[1], x, bbox[3]], fill=lerp(c1, c2, (x - x0) / max(1, x1 - x0)))
    img.paste(grad, (0, 0), mask)
    return bbox


def banner(ss=2):
    W, H = 2560 * ss, 1440 * ss
    base = radial_bg(W, H, W * 0.38, H / 2, W * 0.55)
    d = ImageDraw.Draw(base)
    # subtle dot grid
    step = 48 * ss
    for y in range(step // 2, H, step):
        for x in range(step // 2, W, step):
            d.ellipse([x - 1.6 * ss, y - 1.6 * ss, x + 1.6 * ss, y + 1.6 * ss], fill=(26, 34, 64))
    sx0 = (W - 1546 * ss) / 2
    cy = H / 2
    r = 140 * ss
    mx = sx0 + r * 1.42 + 10 * ss
    out = compose_mark(base, mx, cy, r, ss)
    d = ImageDraw.Draw(out)
    f1 = ImageFont.truetype(F_XB, 116 * ss)
    f2 = ImageFont.truetype(F_MED, 42 * ss)
    tx = mx + r * 1.42 + 70 * ss
    d.text((tx, cy - 22 * ss), "Cómo Va", font=f1, fill=WHITE, anchor="ls")
    wv = d.textlength("Cómo Va ", font=f1)
    bb = gradient_text(out, (tx + wv, cy - 22 * ss), "el Mundo", f1, CYAN, VIOLET)
    d.text((tx, cy + 56 * ss), "Lo que pasa en el mundo, y lo que significa", font=f2, fill=MUTED, anchor="ls")
    d.text((tx, cy + 112 * ss), "para ", font=f2, fill=MUTED, anchor="ls")
    wp = d.textlength("para ", font=f2)
    d.text((tx + wp, cy + 112 * ss), "tu bolsillo", font=f2, fill=YELLOW, anchor="ls")
    right = max(bb[2], tx + d.textlength("Lo que pasa en el mundo, y lo que significa", font=f2)) / ss
    print("right edge", right, "safe", (2560 + 1546) / 2, "left", (mx - r * 1.42) / ss, "safe left", (2560 - 1546) / 2)
    out.resize((2560, 1440), Image.LANCZOS).save(OUT + "banner_comovaelmundo_v2_2560x1440.png")


if __name__ == "__main__":
    logo()
    banner()
    print("ok")

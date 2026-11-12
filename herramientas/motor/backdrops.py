"""Illustrated backdrops (2304x1296, 20% larger than the frame so the camera can drift)."""
from PIL import Image, ImageDraw, ImageFilter
import math, random, os

BW, BH = 2304, 1296
SS = 2  # supersampling
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backdrops")
os.makedirs(OUT, exist_ok=True)

CYAN, VIOLET, YELLOW = (34, 211, 238), (139, 92, 246), (255, 214, 10)
NAVY, NIGHT = (14, 22, 52), (5, 8, 20)
PROD = [(239, 68, 68), (34, 197, 94), (250, 204, 21), (59, 130, 246), (236, 72, 153), (249, 115, 22), (168, 85, 247), (20, 184, 166), (240, 240, 240)]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class C:
    def __init__(self, top, bottom):
        self.im = Image.new("RGB", (BW * SS, BH * SS))
        self.d = ImageDraw.Draw(self.im)
        for y in range(BH * SS):
            self.d.line([0, y, BW * SS, y], fill=lerp(top, bottom, y / (BH * SS)))
        self.glow = Image.new("RGB", self.im.size, (0, 0, 0))
        self.g = ImageDraw.Draw(self.glow)

    def P(self, *v):
        return [x * SS for x in v]

    def rect(self, x0, y0, x1, y1, fill, glow=False, r=0):
        if r:
            self.d.rounded_rectangle(self.P(x0, y0, x1, y1), radius=r * SS, fill=fill)
        else:
            self.d.rectangle(self.P(x0, y0, x1, y1), fill=fill)
        if glow:
            self.g.rectangle(self.P(x0, y0, x1, y1), fill=fill)

    def line(self, pts, fill, w, glow=False):
        pp = [(x * SS, y * SS) for x, y in pts]
        self.d.line(pp, fill=fill, width=int(w * SS), joint="curve")
        if glow:
            self.g.line(pp, fill=fill, width=int(w * SS * 2))

    def ell(self, x0, y0, x1, y1, fill, glow=False):
        self.d.ellipse(self.P(x0, y0, x1, y1), fill=fill)
        if glow:
            self.g.ellipse(self.P(x0, y0, x1, y1), fill=fill)

    def poly(self, pts, fill, glow=False):
        pp = [(x * SS, y * SS) for x, y in pts]
        self.d.polygon(pp, fill=fill)
        if glow:
            self.g.polygon(pp, fill=fill)

    def save(self, name):
        g = self.glow.resize((BW // 4, BH // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(10)).resize(self.im.size, Image.BILINEAR)
        from PIL import ImageChops
        out = ImageChops.add(self.im, g)
        out = out.resize((BW, BH), Image.LANCZOS)
        out.save(os.path.join(OUT, name + ".png"))
        print("saved", name)


def supermarket():
    random.seed(1)
    c = C((20, 26, 56), (8, 10, 24))
    # ceiling light strips
    for i in range(5):
        x = 200 + i * 470
        c.rect(x, 40, x + 300, 56, (220, 240, 255), glow=True, r=8)
    # floor
    c.poly([(0, 1000), (BW, 1000), (BW, BH), (0, BH)], (16, 20, 40))
    for i in range(-10, 30):
        c.line([(BW / 2, 1000), (BW / 2 + i * 260, BH)], (28, 34, 64), 2)
    # shelving units
    for u, (x0, x1) in enumerate([(60, 720), (800, 1500), (1580, 2250)]):
        c.rect(x0 - 12, 170, x1 + 12, 1000, (36, 44, 84))
        c.rect(x0, 180, x1, 990, (22, 28, 58))
        for s in range(5):
            y = 330 + s * 150
            c.rect(x0, y, x1, y + 16, (120, 140, 190))
            # products
            x = x0 + 12
            while x < x1 - 50:
                w = random.choice([38, 46, 54, 62])
                h = random.choice([70, 90, 110, 120])
                col = random.choice(PROD)
                if random.random() < 0.35:  # bottle
                    c.rect(x + w * 0.3, y - h - 18, x + w * 0.7, y - h + 4, col, r=4)
                    c.rect(x, y - h, x + w, y, col, r=10)
                else:
                    c.rect(x, y - h, x + w, y, col, r=4)
                    c.rect(x + 6, y - h + 14, x + w - 6, y - h + 26, (255, 255, 255))
                x += w + 8
            # price tags
            for k in range(4):
                tx = x0 + 40 + k * (x1 - x0 - 80) / 3
                c.rect(tx, y + 18, tx + 44, y + 40, YELLOW, glow=True, r=3)
    c.save("A_super")


def city():
    random.seed(2)
    c = C((8, 12, 34), (26, 20, 60))
    for _ in range(160):
        x, y = random.uniform(0, BW), random.uniform(0, 600)
        r = random.uniform(1, 2.6)
        c.ell(x - r, y - r, x + r, y + r, (200, 210, 255))
    c.ell(1820, 120, 1960, 260, (240, 240, 210), glow=True)
    c.ell(1850, 120, 1990, 250, (8, 12, 34))
    for layer, (base_col, hmin, hmax, win) in enumerate([((24, 30, 66), 300, 650, 0.25), ((14, 18, 44), 380, 820, 0.45)]):
        x = -40
        while x < BW:
            w = random.randint(110, 230)
            h = random.randint(hmin, hmax)
            top = BH - h
            c.rect(x, top, x + w, BH, base_col)
            if random.random() < 0.3:
                c.rect(x + w * 0.4, top - 60, x + w * 0.45, top, base_col)
            for wy in range(int(top + 30), BH - 30, 46):
                for wx in range(int(x + 18), int(x + w - 28), 38):
                    if random.random() < win:
                        col = random.choice([YELLOW, (255, 236, 160), CYAN, (255, 190, 120)])
                        c.rect(wx, wy, wx + 20, wy + 26, col, glow=True)
            x += w + random.randint(4, 24)
    c.save("B_ciudad")


def port():
    random.seed(3)
    c = C((16, 30, 72), (10, 40, 70))
    c.ell(1500, 160, 1800, 460, (255, 170, 80), glow=True)
    c.rect(0, 860, BW, BH, (8, 30, 58))
    for i in range(14):
        y = 900 + i * 28
        c.line([(random.uniform(0, 300), y), (BW - random.uniform(0, 300), y)], (22, 60, 100), 3)
    # cranes
    for x in (300, 900, 1500):
        col = (240, 140, 60)
        c.line([(x, 860), (x, 260)], col, 18)
        c.line([(x + 140, 860), (x + 140, 260)], col, 18)
        c.line([(x - 120, 260), (x + 420, 260)], col, 22)
        c.line([(x, 260), (x + 70, 160), (x + 140, 260)], col, 10)
        c.line([(x + 330, 260), (x + 330, 520)], (180, 190, 210), 4)
    # container stacks
    for s in range(3):
        bx = 120 + s * 640
        for row in range(4):
            for k in range(5 - row // 2):
                col = random.choice(PROD[:8])
                x = bx + k * 104 + (row % 2) * 20
                y = 860 - (row + 1) * 54
                c.rect(x, y, x + 98, y + 50, col)
                for v in range(6):
                    c.line([(x + 10 + v * 15, y + 8), (x + 10 + v * 15, y + 42)], lerp(col, (0, 0, 0), 0.3), 2)
    # ship
    c.poly([(1700, 880), (2280, 880), (2220, 990), (1760, 990)], (30, 34, 50))
    for k in range(5):
        for r in range(2):
            c.rect(1760 + k * 90, 820 - r * 50, 1840 + k * 90, 866 - r * 50, random.choice(PROD[:8]))
    c.save("C_puerto")


def energy():
    random.seed(4)
    c = C((10, 14, 40), (30, 16, 50))
    # factory
    c.rect(1500, 760, 2200, BH, (26, 30, 56))
    for k in range(6):
        c.poly([(1500 + k * 117, 760), (1500 + k * 117 + 58, 690), (1500 + k * 117 + 117, 760)], (26, 30, 56))
    for x in (1600, 1780, 1960):
        c.rect(x, 380, x + 70, 760, (40, 44, 74))
        c.rect(x, 420, x + 70, 440, (240, 70, 70))
        for j in range(5):
            r = 50 + j * 30
            c.ell(x + 35 - r + j * 40, 330 - j * 70 - r, x + 35 + r + j * 40, 330 - j * 70 + r, (60, 64, 96))
    for wy in range(820, 1200, 70):
        for wx in range(1540, 2160, 90):
            c.rect(wx, wy, wx + 50, wy + 34, YELLOW, glow=True)
    # pylons
    def pylon(x, base, h):
        top = base - h
        col = (150, 170, 220)
        c.line([(x - 90, base), (x - 20, top), (x + 20, top), (x + 90, base)], col, 6)
        for k in range(7):
            y1 = base - h * k / 7
            y2 = base - h * (k + 1) / 7
            w1 = 90 - 70 * k / 7
            w2 = 90 - 70 * (k + 1) / 7
            c.line([(x - w1, y1), (x + w2, y2)], col, 3)
            c.line([(x + w1, y1), (x - w2, y2)], col, 3)
        for arm in (0.18, 0.38):
            y = top + h * arm
            c.line([(x - 150, y), (x + 150, y)], col, 6)
        return top
    tops = [(x, pylon(x, 1100, h)) for x, h in ((220, 760), (760, 700), (1260, 640))]
    for arm in (0.18, 0.38):
        for (xa, ta), (xb, tb), h in zip(tops, tops[1:], (760, 700)):
            for dx in (-150, 150):
                ya = ta + 760 * arm if xa == 220 else ta + 700 * arm
                yb = tb + 700 * arm if xb == 760 else tb + 640 * arm
                pts = [(xa + dx + (xb - xa) * t, ya + (yb - ya) * t + 60 * math.sin(math.pi * t)) for t in [i / 20 for i in range(21)]]
                c.line(pts, CYAN, 3, glow=True)
    # lightning
    c.line([(980, 0), (930, 140), (990, 160), (920, 330)], YELLOW, 8, glow=True)
    c.rect(0, 1100, BW, BH, (12, 14, 30))
    c.save("D_energia")


def olives():
    random.seed(5)
    c = C((70, 40, 60), (180, 100, 50))
    c.ell(1450, 160, 1850, 560, (255, 214, 120), glow=True)
    c.poly([(0, 760)] + [(x, 700 + 50 * math.sin(x / 300)) for x in range(0, BW + 1, 40)] + [(BW, BH), (0, BH)], (120, 80, 50))
    c.poly([(0, 900)] + [(x, 860 + 40 * math.sin(x / 220 + 1)) for x in range(0, BW + 1, 40)] + [(BW, BH), (0, BH)], (150, 100, 56))
    # cracked earth
    for _ in range(40):
        x, y = random.uniform(0, BW), random.uniform(980, BH)
        pts = [(x, y)]
        for k in range(4):
            x += random.uniform(-60, 60)
            y += random.uniform(-20, 30)
            pts.append((x, y))
        c.line(pts, (110, 70, 40), 3)
    # olive trees in rows
    for row, (y, s) in enumerate([(760, 0.6), (900, 0.85), (1080, 1.15)]):
        for k in range(9):
            x = 80 + k * 280 + (row % 2) * 140
            c.line([(x, y), (x - 10 * s, y - 90 * s), (x + 8 * s, y - 140 * s)], (80, 60, 40), 16 * s)
            for j in range(5):
                rx = x + random.uniform(-70, 70) * s
                ry = y - 160 * s + random.uniform(-40, 30) * s
                r = random.uniform(45, 70) * s
                c.ell(rx - r, ry - r * 0.8, rx + r, ry + r * 0.8, random.choice([(110, 128, 70), (96, 116, 62), (128, 140, 84)]))
    c.save("E_olivar")


def gas():
    random.seed(6)
    c = C((8, 10, 30), (20, 14, 44))
    for _ in range(80):
        x, y = random.uniform(0, BW), random.uniform(0, 400)
        c.ell(x - 1.5, y - 1.5, x + 1.5, y + 1.5, (200, 210, 255))
    # road
    c.rect(0, 1080, BW, BH, (24, 26, 40))
    for k in range(10):
        c.rect(80 + k * 240, 1180, 220 + k * 240, 1196, (220, 220, 220))
    # canopy
    c.rect(300, 330, 2000, 430, (230, 236, 250))
    c.rect(300, 420, 2000, 446, CYAN, glow=True)
    for k in range(8):
        c.rect(360 + k * 210, 446, 460 + k * 210, 458, (255, 255, 230), glow=True)
    c.poly([(300, 458), (2000, 458), (2100, 1080), (200, 1080)], (30, 34, 62))
    for x in (520, 1060, 1600):
        c.rect(x, 446, x + 40, 1080, (200, 206, 224))
        # pump
        c.rect(x + 90, 720, x + 250, 1080, (220, 60, 60), r=14)
        c.rect(x + 112, 760, x + 228, 860, (16, 20, 40), r=8)
        c.rect(x + 124, 780, x + 216, 800, YELLOW, glow=True)
        c.rect(x + 124, 816, x + 190, 836, YELLOW, glow=True)
        c.line([(x + 250, 900), (x + 300, 920), (x + 300, 1000)], (30, 30, 30), 8)
    # price sign
    c.rect(2080, 200, 2260, 760, (26, 30, 56), r=12)
    for k in range(4):
        c.rect(2100, 240 + k * 120, 2240, 330 + k * 120, (10, 12, 26), r=6)
        c.poly([(2170, 255 + k * 120), (2140, 310 + k * 120), (2200, 310 + k * 120)], (248, 113, 113), glow=True)
    # car
    c.rect(700, 960, 1100, 1060, (40, 120, 220), r=30)
    c.poly([(770, 960), (840, 890), (980, 890), (1040, 960)], (40, 120, 220))
    c.poly([(800, 955), (850, 905), (900, 905), (900, 955)], (150, 200, 240))
    c.poly([(915, 955), (915, 905), (970, 905), (1015, 955)], (150, 200, 240))
    for x in (790, 1010):
        c.ell(x - 42, 1020, x + 42, 1104, (16, 16, 20))
    c.save("F_gasolinera")


def charts():
    random.seed(7)
    c = C((10, 8, 34), (40, 14, 70))
    hz = 760
    c.rect(0, hz, BW, BH, (12, 8, 30))
    for k in range(0, 30):
        y = hz + (k / 30) ** 2 * (BH - hz)
        c.line([(0, y), (BW, y)], (90, 40, 150), 2)
    for k in range(-24, 25):
        c.line([(BW / 2 + k * 40, hz), (BW / 2 + k * 260, BH)], (90, 40, 150), 2)
    # bar mountains
    x = 40
    h = 140
    while x < BW - 60:
        h = max(80, min(560, h + random.randint(-50, 90)))
        col = lerp(CYAN, VIOLET, x / BW)
        c.rect(x, hz - h, x + 60, hz, lerp(col, (10, 10, 30), 0.55))
        c.rect(x, hz - h, x + 60, hz - h + 8, col, glow=True)
        x += 76
    # glowing line chart
    pts, y = [], 640
    for i in range(24):
        y = max(140, y - random.uniform(-30, 60))
        pts.append((80 + i * 92, y))
    c.line(pts, YELLOW, 8, glow=True)
    c.save("G_graficos")


if __name__ == "__main__":
    for fn in (supermarket, city, port, energy, olives, gas, charts):
        fn()

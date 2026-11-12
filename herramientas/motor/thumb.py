import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import scenes as sc
from PIL import ImageDraw, ImageFilter, ImageChops, Image

sc.OUT = "/home/claude/canal/video1/"


def thumb(name, top, big, big_color):
    s = sc.Scene()
    # big cart with glow on the left
    cx, cy, r = 430, 540, 290
    s.d.ellipse(sc.p(cx - r, cy - r, cx + r, cy + r), outline=sc.CYAN, width=8 * sc.S, fill=(10, 16, 38))
    s.gd.ellipse(sc.p(cx - r, cy - r, cx + r, cy + r), outline=sc.CYAN, width=10 * sc.S)
    sc.g_cart(s, cx - 20, cy, 170, sc.WHITE, 16)
    s.arrow(700, 860, 960, 330, sc.YELLOW, 34, 110)
    s.t(1450, 470, top, 190, sc.WHITE, sc.FX, anchor="ms")
    s.grad_t(1450, 760, big, 270, big_color, (255, 160, 0), anchor="ms")
    g = s.glowl.filter(ImageFilter.GaussianBlur(18 * sc.S))
    out = ImageChops.add(s.im, ImageChops.multiply(g, Image.new("RGB", g.size, (170, 170, 170))))
    out.resize((1280, 720), Image.LANCZOS).save(sc.OUT + name, quality=95)
    print("saved", name)


thumb("miniatura_A_todo_26.png", "TODO", "+26 %", sc.YELLOW)
thumb("miniatura_B_por_que.png", "¿POR", "QUÉ?", sc.YELLOW)

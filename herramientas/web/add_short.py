"""Añade un Short a la web y regenera deploy/ + zip.
uso: python3 add_short.py ID "Título" "Etiqueta" miniatura.jpg [--max 10]
"""
import sys, json, base64, io, os, subprocess
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
vid, title, tag, thumb = sys.argv[1:5]
MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 10

im = Image.open(thumb).convert("RGB").resize((300, 533), Image.LANCZOS)
buf = io.BytesIO(); im.save(buf, "JPEG", quality=80, optimize=True)
img = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

d = json.load(open("data.json"))
d["shorts"] = [s for s in d["shorts"] if s["id"] != vid]
d["shorts"].insert(0, {"id": vid, "t": title, "img": img, "tag": tag})
d["shorts"] = d["shorts"][:MAX]
json.dump(d, open("data.json", "w"), ensure_ascii=False)

t = open("template.html").read()
dd = dict(d); logo = dd.pop("logo"); fav = dd.pop("favicon")
out = t.replace("__LOGO__", logo).replace("__FAVICON__", fav).replace("__DATA__", json.dumps(dd, ensure_ascii=False))
open("como-va-el-mundo.html", "w").write(out)
open("deploy/index.html", "w").write(out)

files = ["index.html", "og.jpg", "robots.txt", "sitemap.xml", "google31f3dc5707d05670.html", "logo.png", "favicon.png", "hipoteca/index.html", "privacidad/index.html", "condiciones/index.html"]
if os.path.exists("comovaelmundo-web.zip"): os.remove("comovaelmundo-web.zip")
subprocess.run(["zip", "-q", "../comovaelmundo-web.zip", *files], cwd="deploy", check=True)
print("ok:", [s["id"] for s in d["shorts"]])

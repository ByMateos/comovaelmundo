import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim
os.makedirs("prev", exist_ok=True)
for i, sc in enumerate(anim.SC):
    f = anim.Fr(); sc["draw"](f, lambda k: 1.0); f.done().resize((640,360)).save(f"prev/{i+1:02d}.jpg")
tl, total = anim.timeline(); print("total s", round(total,1), "beats", len(tl))

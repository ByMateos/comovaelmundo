"""Estimated timing from script text (for previews before the voice exists)."""
import re, json, sys
txt = open(sys.argv[1]).read().strip()
pars = [p.strip() for p in txt.split("\n\n") if p.strip()]
WPS = 2.55
t = 0.4
out = []
for p in pars:
    sents = [s for s in re.split(r'(?<=[.?!])\s+', p) if s]
    ts = []
    for s in sents:
        ts.append(round(t, 2))
        t += len(s.split()) / WPS + 0.45
    t += 0.5
    out.append(ts)
json.dump({"dur": round(t + 0.5, 2), "pars": out}, open(sys.argv[2], "w"))
print(len(pars), "pars", round(t, 1), "s", [len(p) for p in out])

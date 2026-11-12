"""Align script sentences to the narration (silencedetect + DP) -> timing.json for video2.py.
usage: sync_v2.py script.txt voice.mp3 timing.json"""
import json, re, subprocess, sys
from align import align

script, voice, out = sys.argv[1:4]
txt = open(script).read().strip()
pars = [p.strip() for p in txt.split("\n\n") if p.strip()]
sents, owner = [], []
for pi, p in enumerate(pars):
    for s in [x for x in re.split(r'(?<=[.?!])\s+', p) if x]:
        sents.append(s)
        owner.append(pi)
r = subprocess.run(["ffmpeg", "-i", voice, "-af", "silencedetect=noise=-35dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
ss = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r)]
se = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r)]
dur = float(re.findall(r"time=(\d+):(\d+):([\d.]+)", r)[-1][2]) + 60 * float(re.findall(r"time=(\d+):(\d+):([\d.]+)", r)[-1][1])
pauses = [(a, b) for a, b in zip(ss, se) if a > 0.05]
lead = se[0] if ss and ss[0] < 0.05 else 0.0
speech_end = ss[-1] if len(ss) > len(se) else dur
starts, rate = align([len(s) for s in sents], pauses, speech_end)
starts[0] = lead
out_p = [[] for _ in pars]
for t, o in zip(starts, owner):
    out_p[o].append(round(t, 2))
json.dump({"dur": round(dur + 0.8, 2), "pars": out_p}, open(out, "w"))
print(len(sents), "sentences", len(pauses), "pauses", "dur", round(dur, 1), "rate", round(rate, 1))
for pi, p in enumerate(out_p):
    print(pi, p[:3])

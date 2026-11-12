"""Align animation beats to the ElevenLabs voice track and build the final video."""
import json, re, subprocess, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim

D = os.path.dirname(os.path.abspath(__file__))
FR = D + "/frames"
AUDIO = sys.argv[1]
OUT = "/home/claude/canal/video1/video1_final_con_voz.mp4"

dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUDIO]))
sil = json.load(open(D + "/sil.json"))
speech_end = sil[-1][0] if sil[-1][1] >= dur - 0.3 else dur

voice = open("/home/claude/canal/video1/voz_elevenlabs_video1_sin_pausas.txt").read()


def sents(t):
    t = t.replace("...", "…")
    return [p for p in re.split(r"(?<=[\.\?\!:…])\s+", t.strip()) if p.strip()]


vs = sents(voice)
beats = [(si, bi, b) for si, sc in enumerate(anim.SC) for bi, b in enumerate(sc["beats"])]
# char offset (in the spoken text) where each beat starts
offs, k = [], 0
lens = [len(s) for s in vs]
total_chars = sum(lens)
for si, bi, b in beats:
    offs.append(sum(lens[:k]))
    k += len(sents(b))

starts = [max(0.0, t - 0.1) for t in json.load(open(D + "/beats_v1.json"))["beat_starts"]]
ends = starts[1:] + [dur + 1.5]
beat_d = [e - s for s, e in zip(starts, ends)]

# rebuild concat with new hold durations
lines, total, last = [], 0.0, None
bi_global = 0
for si in range(len(anim.SC)):
    entries = json.load(open(f"{FR}/s{si + 1:02d}.json"))
    nb = len(anim.SC[si]["beats"])
    per = len(entries) // nb
    for b in range(nb):
        chunk = entries[b * per:(b + 1) * per]
        bd = beat_d[bi_global]
        anim_t = (len(chunk) - 1) / anim.FPS
        if bd < anim_t + 0.2:  # very short beat: keep fewer anim frames
            step = max(1, int(len(chunk) / max(2, bd * anim.FPS * 0.6)))
            chunk = chunk[::step][:-1] + [chunk[-1]]
            anim_t = (len(chunk) - 1) / anim.FPS
        for j, (name, _) in enumerate(chunk):
            d = 1 / anim.FPS if j < len(chunk) - 1 else max(0.08, bd - anim_t)
            lines.append(f"file '{FR}/{name}'\nduration {d:.4f}")
            total += d
            last = name
        bi_global += 1
lines.append(f"file '{FR}/{last}'")
open(f"{FR}/concat_sync.txt", "w").write("\n".join(lines) + "\n")
print("audio", round(dur, 1), "video", round(total, 1), "beats", len(beats))
json.dump([dict(scene=s + 1, beat=b, start=round(t, 2), text=x) for (s, b, x), t in zip(beats, starts)], open(D + "/sync_map_v2.json", "w"), ensure_ascii=False, indent=1)

subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{FR}/concat_sync.txt", "-i", AUDIO,
                "-vf", "fps=25,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
                "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT], check=True)
print("ok", OUT)

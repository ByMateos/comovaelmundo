"""Original calm ambient pad (A minor, slow), written to WAV. usage: ambient.py <seconds> <out.wav>"""
import sys, wave
import numpy as np

SR = 48000
dur = float(sys.argv[1])
out = sys.argv[2]
t = np.arange(int(SR * dur)) / SR
# chord progression Am - F - C - Em, 6 s each (frequencies in Hz)
CH = [[220.0, 261.63, 329.63], [174.61, 220.0, 261.63], [196.0, 261.63, 329.63], [164.81, 196.0, 246.94]]
seg = 6.0
sig = np.zeros_like(t)
for i in range(int(dur // seg) + 2):
    chord = CH[i % len(CH)]
    t0 = i * seg - 1.5
    env = np.clip((t - t0) / 2.5, 0, 1) * np.clip((t0 + seg + 3.0 - t) / 2.5, 0, 1)
    env = env ** 1.5
    for k, f in enumerate(chord):
        det = 1 + 0.0015 * np.sin(2 * np.pi * 0.11 * t + k)
        tone = np.sin(2 * np.pi * f * det * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t + 0.3) + 0.08 * np.sin(2 * np.pi * 3 * f * t)
        sig += env * tone / 3
    bass = chord[0] / 2
    sig += 0.35 * env * np.sin(2 * np.pi * bass * t)
# soft "reverb": a few decaying delays
rev = sig.copy()
for dly, g in ((0.11, 0.35), (0.23, 0.25), (0.37, 0.18), (0.53, 0.12)):
    n = int(dly * SR)
    rev[n:] += g * sig[:-n]
# low-pass-ish smoothing
kern = np.ones(24) / 24
rev = np.convolve(rev, kern, mode="same")
# global fade in/out
fade = np.clip(t / 2.0, 0, 1) * np.clip((dur - t) / 3.0, 0, 1)
rev *= fade
rev = rev / np.max(np.abs(rev)) * 0.5
st = np.stack([rev, np.roll(rev, int(0.012 * SR))], axis=1)
pcm = (st * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok", out)

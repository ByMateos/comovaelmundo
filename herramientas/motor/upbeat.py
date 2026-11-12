"""Original upbeat news/explainer bed: 118 BPM, kick/clap/hats, bass, pluck arpeggio, pad.
usage: upbeat.py <seconds> <out.wav>"""
import sys, wave
import numpy as np

SR = 48000
dur = float(sys.argv[1])
out = sys.argv[2]
N = int(SR * dur)
BPM = 118
beat = 60 / BPM
step = beat / 4  # 16th
rng = np.random.default_rng(7)
L = np.zeros(N)
R = np.zeros(N)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: N - i] * gain
    L[i:i + len(s)] += s * (1 - max(pan, 0))
    R[i:i + len(s)] += s * (1 + min(pan, 0))


def env(n, a=0.002, d=0.2):
    t = np.arange(n) / SR
    return np.minimum(t / a, 1) * np.exp(-t / d)


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 35)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 9) * 1.0


def clap():
    n = int(0.25 * SR)
    nz = rng.standard_normal(n)
    # band-limit noise
    nz = np.convolve(nz, np.ones(6) / 6, "same") - np.convolve(nz, np.ones(40) / 40, "same")
    t = np.arange(n) / SR
    e = np.exp(-t * 18) + 0.6 * np.exp(-np.maximum(t - 0.012, 0) * 30) * (t > 0.012)
    return nz * e * 0.9


def hat(open_=False):
    n = int((0.18 if open_ else 0.05) * SR)
    nz = rng.standard_normal(n)
    nz = nz - np.convolve(nz, np.ones(4) / 4, "same")
    return nz * env(n, 0.001, 0.06 if open_ else 0.012) * 0.35


def saw(f, n, det=0.0):
    t = np.arange(n) / SR
    x = 0
    for k in range(1, 12):
        x = x + np.sin(2 * np.pi * f * (1 + det) * k * t) / k
    return x * 0.5


def pluck(f, n):
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) + 0.2 * np.sin(2 * np.pi * 3 * f * t)
    return tone * env(n, 0.002, 0.12)


def bass(f, n):
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sign(np.sin(2 * np.pi * f * t)) * 0.4
    e = np.minimum(t / 0.005, 1) * np.clip((n / SR - t) / 0.02, 0, 1)
    return x * e


def lp(x, k=8):
    return np.convolve(x, np.ones(k) / k, "same")


# progression (C major feel, bright): C - G - Am - F, one bar (4 beats) each
mid = lambda m: 440 * 2 ** ((m - 69) / 12)
CHORDS = [[60, 64, 67], [55, 59, 62], [57, 60, 64], [53, 57, 60]]
ROOTS = [36, 43, 45, 41]
bar = 4 * beat
nbars = int(dur / bar) + 2
K, C, Hc, Ho = kick(), clap(), hat(), hat(True)
for b in range(nbars):
    t0 = b * bar
    ch = CHORDS[b % 4]
    root = ROOTS[b % 4]
    intro = b < 1  # first bar lighter
    for s in range(16):
        ts = t0 + s * step
        if s % 4 == 0 and not intro:
            add(K, ts, 0.9)
        if s in (4, 12) and not intro:
            add(lp(C,3), ts, 0.4, 0.05)
        if s % 2 == 1:
            add(lp(Hc,2), ts, 0.22 if s % 4 == 3 else 0.14, -0.3)
        if s == 14 and not intro:
            add(lp(Ho,2), ts, 0.18, -0.3)
        # bass: offbeat 8ths, octave jumps
        if s % 2 == 0 and not intro:
            f = mid(root + (12 if s in (6, 14) else 0))
            add(lp(bass(f, int(step * 1.8 * SR)), 6), ts, 0.26)
        # arpeggio 16ths
        notes = ch + [ch[0] + 12, ch[1] + 12]
        arp = notes[[0, 2, 1, 3, 2, 4, 3, 2][s % 8]] + 12
        add(pluck(mid(arp), int(0.22 * SR)), ts, 0.17 if not intro else 0.13, 0.25 if s % 2 else -0.25)
    # pad chord whole bar
    n = int(bar * SR)
    pad = sum(lp(saw(mid(m), n, 0.003) + saw(mid(m), n, -0.003), 30) for m in ch)
    tt = np.arange(n) / SR
    pe = np.minimum(tt / 0.3, 1) * np.clip((bar - tt) / 0.3, 0, 1)
    # sidechain pump on each beat
    pump = 1 - 0.55 * np.exp(-((tt % beat) / 0.09))
    add(pad * pe * pump, t0, 0.035)

mix = np.stack([L, R], axis=1)
t = np.arange(N) / SR
fade = np.clip(t / 0.5, 0, 1) * np.clip((dur - t) / 2.0, 0, 1)
mix *= fade[:, None]
mix = np.tanh(mix * 1.3)  # soft clip / glue
mix = mix / np.max(np.abs(mix)) * 0.8
pcm = (mix * 32767).astype(np.int16)
with wave.open(out, "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("ok", out)

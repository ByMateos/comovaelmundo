"""Global alignment of sentences to detected pauses (dynamic programming).

Each boundary between consecutive sentences is assigned to one detected pause,
in order. Cost favours a steady speaking rate (chars per second of speech) and
longer pauses at sentence ends (commas give short pauses, full stops longer).
Returns the time each sentence starts speaking.
"""
import math


def align(sent_lens, pauses, speech_end, lam=3.0, iters=3):
    n, m = len(sent_lens), len(pauses)
    nb = n - 1  # boundaries
    total_chars = sum(sent_lens)
    speech = speech_end - sum(e - s for s, e in pauses)
    r = total_chars / speech  # chars per second
    starts = None
    for _ in range(iters):
        INF = float("inf")
        # cost[b][j]: best cost with boundary b assigned to pause j
        cost = [[INF] * m for _ in range(nb)]
        back = [[-1] * m for _ in range(nb)]

        def seg_cost(i, t0, t1, internal):
            dur = (t1 - t0) - internal
            if dur <= 0.2:
                return INF
            return math.log(dur / (sent_lens[i] / r)) ** 2

        # prefix of silence time to subtract internal pauses inside a sentence
        pref = [0.0]
        for s, e in pauses:
            pref.append(pref[-1] + (e - s))

        def internal(j0, j1):  # pauses strictly between pause j0 and j1 (j0 may be -1)
            return pref[j1] - pref[j0 + 1] if j1 > j0 + 1 else 0.0

        for j in range(m):
            c = seg_cost(0, 0.0, pauses[j][0], pref[j])
            cost[0][j] = c - lam * min(0.9, pauses[j][1] - pauses[j][0])
        for b in range(1, nb):
            for j in range(b, m):
                best, arg = INF, -1
                tj = pauses[j][0]
                for k in range(b - 1, j):
                    if cost[b - 1][k] == INF:
                        continue
                    c = cost[b - 1][k] + seg_cost(b, pauses[k][1], tj, internal(k, j))
                    if c < best:
                        best, arg = c, k
                if arg >= 0:
                    cost[b][j] = best - lam * min(0.9, pauses[j][1] - pauses[j][0])
                    back[b][j] = arg
        # last sentence
        best, arg = INF, -1
        for k in range(m):
            if cost[nb - 1][k] == INF:
                continue
            ints = sum(e - s for s, e in pauses[k + 1:] if e <= speech_end)
            c = cost[nb - 1][k] + seg_cost(n - 1, pauses[k][1], speech_end, ints)
            if c < best:
                best, arg = c, k
        assign = [0] * nb
        j = arg
        for b in range(nb - 1, -1, -1):
            assign[b] = j
            j = back[b][j]
        starts = [0.0] + [pauses[j][1] for j in assign]
        # re-estimate rate from the alignment
        durs = []
        for i in range(n):
            t0 = starts[i]
            t1 = pauses[assign[i]][0] if i < nb else speech_end
            durs.append(t1 - t0)
        r = total_chars / sum(durs)
    return starts, r

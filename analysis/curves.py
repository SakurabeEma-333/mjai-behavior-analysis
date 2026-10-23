"""三条曲线对比：人类 / 被实锤 / 现有机制（模拟）"""
import json, math, random
import numpy as np

base = r"."
D = [json.loads(l) for l in open(base + r"\review4\qdata.jsonl", encoding="utf-8")]
random.seed(101)

BINS = [(0, .1), (.1, .3), (.3, .6), (.6, 1.2), (1.2, 2.5), (2.5, 99)]
HUM = [56.7, 51.3, 48.1, 32.7, 14.6, 2.7]
CAUGHT = [45.5, 33.8, 17.0, 8.5, 1.4, 1.1]

CAP_BASE, CAP_BL, P_BL = 0.5, 1.5, 0.02


def sim(trials=25):
    res = [[] for _ in BINS]
    for rec in D:
        q, m = rec["q"], rec["m"]
        legal = [(i, float(q[i])) for i in range(min(len(q), len(m))) if m[i] and math.isfinite(float(q[i]))]
        if len(legal) < 2:
            continue
        srt = sorted(legal, key=lambda t: -t[1])
        best = srt[0][1]
        gap = best - srt[1][1]
        bi = next((k for k, (lo, hi) in enumerate(BINS) if lo <= gap < hi), None)
        if bi is None:
            continue
        for _ in range(trials):
            cap = CAP_BL if random.random() < P_BL else CAP_BASE * random.uniform(0.5, 1.5)
            cands = [(i, v) for i, v in legal if v >= best - cap]
            pick = best
            if len(cands) > 1:
                ws = [math.exp(v - best) for _, v in cands]
                r = random.random() * sum(ws)
                acc = 0.0
                for (i, v), w in zip(cands, ws):
                    acc += w
                    if r < acc:
                        pick = v
                        break
            res[bi].append(0 if abs(pick - best) < 1e-9 else 1)
    return res


res = sim()
print(f"{'gap桶':>12}{'人类':>8}{'被实锤':>8}{'现有机制':>10}")
tot = []
for k, (lo, hi) in enumerate(BINS):
    ours = np.mean(res[k]) * 100 if res[k] else 0
    tot.extend(res[k])
    print(f"{lo:>5.1f}~{hi:<5.1f}{HUM[k]:>7.1f}%{CAUGHT[k]:>7.1f}%{ours:>9.1f}%")
print(f"\n整体失误率：人类 20.07%  被实锤 8.58%  现有机制 {np.mean(tot)*100:.1f}%")



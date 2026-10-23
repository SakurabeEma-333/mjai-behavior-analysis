import json, glob, math, statistics as st

base = r".\soul-logs"

dec = []
for p in glob.glob(base + r"\decisions_*.jsonl"):
    for line in open(p, encoding="utf-8"):
        dec.append(json.loads(line))

games = []
for p in glob.glob(base + r"\games_*.jsonl"):
    for line in open(p, encoding="utf-8"):
        games.append(json.loads(line))

print(f"人类：{len(games)} 局 / {len(dec)} 决策")
hit = sum(1 for d in dec if d["match"])
print(f"本地一致率（v4 口径）= {hit/len(dec)*100:.2f}%")
miss = [d["cost"] for d in dec if not d["match"]]
print(f"失误数 {len(miss)}，平均成本 {st.mean(miss):.3f}，中位 {st.median(miss):.3f}")

print("\n=== 人类失误成本分布 ===")
bins = [0, .2, .4, .6, .8, .9, .95, 1.0001]
labels = ["0~0.2", "0.2~0.4", "0.4~0.6", "0.6~0.8", "0.8~0.9", "0.9~0.95", "0.95~1.0"]
for i in range(len(bins) - 1):
    n = sum(1 for c in miss if bins[i] <= c < bins[i+1])
    print(f"  {labels[i]:<10} {n:>5}  {n/len(miss)*100:5.1f}%")

print("\n=== 每局失误次数 ===")
per_game = [sum(1 for d in dec if d["file"] == g["file"] and not d["match"]) for g in games]
n_dec = [g["n"] for g in games]
print(f"  每局失误次数：均值 {st.mean(per_game):.1f}  sd {st.stdev(per_game):.1f}  范围 {min(per_game)}~{max(per_game)}")
print(f"  每局决策数：均值 {st.mean(n_dec):.0f}")
print(f"  失误率：合并 {len(miss)/len(dec)*100:.2f}%")

# 我们 bot 的成本分布（用 qdata.jsonl：a 是 bot 实际选择）
print("\n=== Kaguya bot 的同一指标（v4 自身 q）===")
Q = [json.loads(l) for l in open(r".\review4\qdata.jsonl", encoding="utf-8")]
b_miss, b_hit = [], 0
for rec in Q:
    q, m, a = rec["q"], rec["m"], rec["a"]
    n = min(len(q), len(m))
    legal = [(i, q[i]) for i in range(n) if m[i] and math.isfinite(q[i])]
    if len(legal) < 2:
        continue
    legal.sort(key=lambda kv: -kv[1])
    best, bestq = legal[0]
    qmin = legal[-1][1]
    if a == best:
        b_hit += 1
    else:
        qa = q[a] if m[a] else qmin
        b_miss.append((qa - qmin) / max(bestq - qmin, 1e-6))
tot = b_hit + len(b_miss)
print(f"  决策 {tot}，偏差率 {len(b_miss)/tot*100:.2f}%，平均成本 {st.mean(b_miss):.3f}，中位 {st.median(b_miss):.3f}")
for i in range(len(bins) - 1):
    n = sum(1 for c in b_miss if bins[i] <= c < bins[i+1])
    print(f"  {labels[i]:<10} {n:>5}  {n/len(b_miss)*100:5.1f}%")


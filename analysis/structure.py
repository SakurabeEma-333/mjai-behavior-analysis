import json, glob, math
import statistics as st

base = r".\soul-logs"
rows = []
for p in glob.glob(base + r"\feat_*.jsonl"):
    for line in open(p, encoding="utf-8"):
        rows.append(json.loads(line))

print("决策总数", len(rows))
def rate(sub):
    if not sub:
        return 0, 0, 0
    n = len(sub); m = sum(1 for d in sub if not d["match"])
    se = math.sqrt((m / n) * (1 - m / n) / n) * 100
    return n, m / n * 100, se

print("\n=== 按动作类型 ===")
for t in ["dahai", "pass", "reach", "pon", "kan", "hora"]:
    sub = [d for d in rows if d["type"] == t]
    n, r, se = rate(sub)
    if n:
        print(f"  {t:<7} n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

print("\n=== 按 top1-top2 q 差（决策难度）===")
bins = [(0, 0.1), (0.1, 0.3), (0.3, 0.6), (0.6, 1.2), (1.2, 2.5), (2.5, 99)]
for lo, hi in bins:
    sub = [d for d in rows if lo <= d["gap12"] < hi]
    n, r, se = rate(sub)
    if n:
        print(f"  {lo:>4}~{hi:<4} n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

print("\n=== 按巡目 ===")
for lo, hi in [(0, 3), (3, 6), (6, 9), (9, 12), (12, 99)]:
    sub = [d for d in rows if lo <= d["junme"] < hi]
    n, r, se = rate(sub)
    if n:
        print(f"  第 {lo:>2}~{hi if hi < 99 else '末'} 巡 n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

print("\n=== 按对手立直数 ===")
for k in (0, 1, 2):
    sub = [d for d in rows if (d["opp_riichi"] == k if k < 2 else d["opp_riichi"] >= 2)]
    n, r, se = rate(sub)
    if n:
        print(f"  {k if k < 2 else '2+'} 家立直 n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

print("\n=== 按合法动作数 ===")
for lo, hi in [(1, 3), (3, 6), (6, 10), (10, 99)]:
    sub = [d for d in rows if lo <= d["nlegal"] < hi]
    n, r, se = rate(sub)
    if n:
        print(f"  {lo}~{hi if hi < 99 else '+'} 个 n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

print("\n=== 按 q 区间宽度（局面重要性）===")
for lo, hi in [(0, 1), (1, 3), (3, 6), (6, 10), (10, 99)]:
    sub = [d for d in rows if lo <= d["rng"] < hi]
    n, r, se = rate(sub)
    if n:
        print(f"  {lo}~{hi if hi < 99 else '+'} n={n:>5}  失误率={r:5.1f}% ±{1.96*se:.1f}")

# 失误的质量分（cost 是质量，1=最优）
miss = [d["cost"] for d in rows if not d["match"]]
print(f"\n失误 {len(miss)} 个，质量均值 {st.mean(miss):.3f}")
print(f"  质量<0.2 占比 {sum(1 for c in miss if c < 0.2)/len(miss)*100:.1f}%")
print(f"  质量>0.8 占比 {sum(1 for c in miss if c > 0.8)/len(miss)*100:.1f}%")


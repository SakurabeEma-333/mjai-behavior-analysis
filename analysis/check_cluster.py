"""检验 1：人类失误是否成簇（lag-1 自相关）
检验 2：方案 B 的局间方差能否对上人类
"""
import json, glob, math, random
import statistics as st

base = r".\soul-logs"

# ---------- 人类：逐局失误序列 ----------
by_game = {}
for p in glob.glob(base + r"\decisions_*.jsonl"):
    for line in open(p, encoding="utf-8"):
        d = json.loads(line)
        by_game.setdefault(d["file"], []).append(0 if d["match"] else 1)  # 1 = 失误


def acf1(seq):
    n = len(seq)
    if n < 40:
        return None
    m = sum(seq) / n
    num = sum((seq[i] - m) * (seq[i + 1] - m) for i in range(n - 1)) / (n - 1)
    var = sum((x - m) ** 2 for x in seq) / n
    return num / var if var > 0 else None


vals, ns = [], []
for f, seq in by_game.items():
    a = acf1(seq)
    if a is not None:
        vals.append(a); ns.append(len(seq))

print("=== 1. 人类失误的 lag-1 自相关 ===")
print(f"  局数={len(vals)}  决策/局均值={st.mean(ns):.0f}")
print(f"  acf1 均值={st.mean(vals):+.4f}  中位={st.median(vals):+.4f}  sd={st.stdev(vals):.4f}")
print(f"  理论上 i.i.d. 的期望值 ≈ {-1/st.mean(ns):+.4f}")
print(f"  正自相关（成簇）的局占比: {sum(1 for v in vals if v>0)/len(vals)*100:.1f}%")

# ---------- 方案 B 的模拟：同长度、独立随机 ----------
D = [json.loads(l) for l in open(r"review4/qdata.jsonl", encoding="utf-8")]
NG = 12
pg = len(D) // NG
random.seed(3)

CAP_BASE, P_DEEP = 1.3, 0.010


def sim_game(rows):
    state = random.uniform(0.5, 1.5)
    seq = []
    losses = []
    for rec in rows:
        q, m = rec["q"], rec["m"]
        legal = [(i, q[i]) for i in range(min(len(q), len(m))) if m[i] and math.isfinite(q[i])]
        if not legal:
            continue
        best = max(v for _, v in legal)
        if random.random() < P_DEEP:
            pool = [x for x in legal if (best - x[1]) >= 0.8 * (best - min(v for _, v in legal))]
            if len(pool) > 1:
                i, v = random.choice(pool)
                seq.append(0 if v == best else 1); losses.append(best - v); continue
        cap = CAP_BASE * state
        cand = [x for x in legal if (best - x[1]) <= cap]
        if len(cand) > 1:
            w = [math.exp((v - best) * 2) for _, v in cand]
            tw = sum(w); r = random.random() * tw; acc = 0
            for (i, v), ww in zip(cand, w):
                acc += ww
                if r < acc:
                    seq.append(0 if v == best else 1); losses.append(best - v); break
            else:
                seq.append(0); losses.append(0.0)
        else:
            seq.append(0); losses.append(0.0)
    return seq, losses


print("\n=== 2. 方案 B 模拟（12 局，每局约 123 决策）===")
accs, sim_acf = [], []
for g in range(NG):
    seq, losses = sim_game(D[g * pg:(g + 1) * pg])
    accs.append(100 * (1 - sum(seq) / len(seq)))
    a = acf1(seq)
    if a is not None:
        sim_acf.append(a)
print(f"  逐局一致率均值={st.mean(accs):.2f}%  sd={st.stdev(accs):.2f}pp")
print(f"  lag-1 自相关均值={st.mean(sim_acf):+.4f}")
print(f"  参考：人类 sd={3.67:.2f}pp，人类 acf1={st.mean(vals):+.4f}")


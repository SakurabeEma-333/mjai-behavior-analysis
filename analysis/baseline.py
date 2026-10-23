import json, statistics as st, math

rows = []
for line in open(r"soul-logs/meta.csv", encoding="utf-8"):
    if line.startswith("file,"):
        continue
    p = line.rstrip("\n").split(",")
    if len(p) < 11:
        continue
    try:
        rows.append(dict(file=p[0], dir=p[1], rule=p[2], dan=p[3], player=int(p[4]),
                         length=p[5], rating=float(p[6]), hits=int(p[7]),
                         decisions=int(p[8]), acc=float(p[9]), kyoku=int(p[10]),
                         gen=p[11]))
    except Exception:
        pass

print(f"有效对局 {len(rows)} 局，合计 {sum(r['decisions'] for r in rows)} 个决策\n")

def blk(sub, name):
    accs = [r["acc"] for r in sub]
    N = sum(r["decisions"] for r in sub)
    H = sum(r["hits"] for r in sub)
    p = H / N * 100
    se = math.sqrt(p/100*(1-p/100)/N) * 100
    q = sorted(accs)
    print(f"{name:<6} n={len(sub):>2}  决策={N:>5}  合并={p:6.2f}%±{1.96*se:4.2f}  "
          f"逐局均值={st.mean(accs):6.2f}%  sd={st.stdev(accs):4.2f}  "
          f"中位={st.median(accs):5.2f}  10%~90%={q[int(.1*len(q))]:.1f}~{q[int(.9*len(q))]:.1f}")
    return p, se

all_p, all_se = blk(rows, "全体")
print()
for d in ("魂3", "魂4", "魂9", "魂13"):
    sub = [r for r in rows if r["dir"] == d]
    if sub:
        blk(sub, d)

# 决策数与一致率的关系（局长度效应）
xs = [r["decisions"] for r in rows]
ys = [r["acc"] for r in rows]
mx, my = st.mean(xs), st.mean(ys)
num = sum((x-mx)*(y-my) for x, y in zip(xs, ys))
den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
print(f"\n相关系数 r(决策数, 一致率) = {num/den:+.3f}")

# 按决策数分层
print("\n按局长度分层：")
for lo, hi, name in ((0,120,"<120 决策"), (120,160,"120~160"), (160,999,">160 决策")):
    sub = [r for r in rows if lo <= r["decisions"] < hi]
    if len(sub) >= 3:
        blk(sub, name)

# 段位与一致率排序
print("\n=== 段位 vs 一致率（合并）===")
for d in ("魂3", "魂4", "魂9", "魂13"):
    sub = [r for r in rows if r["dir"] == d]
    if not sub:
        continue
    N = sum(r["decisions"] for r in sub); H = sum(r["hits"] for r in sub)
    print(f"  {d:<5} {H:>5}/{N:<5} = {H/N*100:6.2f}%   平均决策 {N/len(sub):.0f}")

# rating 分布（作者已声明不可靠，仅记录）
print(f"\nrating：均值 {st.mean([r['rating'] for r in rows]):.2f}  "
      f"sd {st.stdev([r['rating'] for r in rows]):.2f}  "
      f"范围 {min(r['rating'] for r in rows):.2f}~{max(r['rating'] for r in rows):.2f}")

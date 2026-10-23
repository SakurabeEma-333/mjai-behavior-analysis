import json, glob, statistics as st

rows = []
for p in glob.glob(r"soul-logs\feat_*.jsonl"):
    for line in open(p, encoding="utf-8"):
        rows.append(json.loads(line))

EDGES = [0, 0.1, 0.25, 0.5, 0.9, 1.5, 2.5, 99]


def bink(g):
    for i in range(len(EDGES) - 1):
        if EDGES[i] <= g < EDGES[i + 1]:
            return i
    return len(EDGES) - 2


CALL = ("pass", "pon", "kan", "chi")
disc = [r for r in rows if r["type"] not in CALL]
print("打牌决策", len(disc))
pes = []
for i in range(len(EDGES) - 1):
    sub = [r for r in disc if bink(r["gap12"]) == i]
    err = [r for r in sub if not r["match"]]
    pe = len(err) / len(sub) if sub else 0.0
    pes.append(round(pe, 4))
    qs = [round(x, 3) for x in st.quantiles([e["cost"] for e in err], n=10)] if len(err) >= 11 else []
    print(f"  bin{i} n={len(sub):5d} p_err={pe:.4f} q10..q90={qs}")

print("P_ERR_DISCARD =", pes)
call = [r for r in rows if r["type"] in CALL]
print("鸣牌窗口", len(call), "偏离率", round(sum(1 for r in call if not r["match"]) / len(call), 4))


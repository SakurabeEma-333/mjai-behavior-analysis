"""通用提取器：从检讨报告 HTML 提取元数据 + 牌谱（可指定目录与输出前缀）"""
import json, os, re, glob, sys

src = sys.argv[1]
prefix = sys.argv[2]

RE_JSON = re.compile(r"#json=([^']+)")
RE = {
    "model": re.compile(r"model tag<dd>([^<]+)"),
    "length": re.compile(r"对局长度<dd>([^<]+)"),
    "player": re.compile(r"玩家 ID<dd>([^<]+)"),
    "rating": re.compile(r"rating<dd>([\d.]+)"),
    "acc": re.compile(r"AI 一致率<dd>(\d+)</dd><dd>(\d+)</dd>"),
    "acc2": re.compile(r"AI 一致率<dd>(\d+)/(\d+)"),
    "gen": re.compile(r"生成时间<dd>([^<]+)"),
}

games = []
meta = []
for path in sorted(glob.glob(os.path.join(src, "**", "*.html"), recursive=True)):
    raw = open(path, encoding="utf-8", errors="replace").read()
    m = {k: (r.search(raw).group(1) if r.search(raw) else "") for k, r in RE.items()}
    hits = tot = 0
    a = RE["acc"].search(raw)
    if a:
        hits, tot = int(a.group(1)), int(a.group(2))
    else:
        a = RE["acc2"].search(raw)
        if a:
            hits, tot = int(a.group(1)), int(a.group(2))
    blobs = RE_JSON.findall(raw)
    kyoku, dan, rule = [], [], ""
    for b in blobs:
        try:
            o = json.loads(b.replace('\\"', '"'))
        except Exception:
            continue
        if isinstance(o.get("log"), list):
            kyoku.extend(o["log"])
        if o.get("dan"):
            dan = o["dan"]
        if o.get("rule", {}).get("disp"):
            rule = o["rule"]["disp"]
    rel = os.path.relpath(path, src)
    meta.append(dict(file=os.path.basename(path), dir=os.path.relpath(os.path.dirname(path), src),
                     rule=rule, dan=";".join(dan), player=m["player"], rating=m["rating"],
                     acc=(hits / tot * 100 if tot else 0), hits=hits, decisions=tot,
                     kyoku=len(kyoku), gen=m["gen"]))
    games.append(dict(file=os.path.basename(path), dir=os.path.relpath(os.path.dirname(path), src),
                      rule=rule, dan=dan, log=kyoku,
                      meta=dict(player=m["player"], rating=m["rating"], hits=hits,
                                decisions=tot, acc=(hits / tot * 100 if tot else 0))))

base = r".\soul-logs"
with open(os.path.join(base, prefix + "_games.jsonl"), "w", encoding="utf-8") as f:
    for g in games:
        f.write(json.dumps(g, ensure_ascii=False) + "\n")
with open(os.path.join(base, prefix + "_meta.csv"), "w", encoding="utf-8") as f:
    f.write("file,dir,rule,dan,player,rating,hits,decisions,acc,kyoku,gen\n")
    for m in meta:
        f.write(",".join(str(m[k]).replace(",", ";") for k in
                         ["file", "dir", "rule", "dan", "player", "rating", "hits",
                          "decisions", "acc", "kyoku", "gen"]) + "\n")

print(f"{len(games)} 局")
for m in meta:
    print(f"  {m['file'][:14]} 段位={m['dan']:<20} 玩家={m['player']} 局数={m['kyoku']:>2} "
          f"决策={m['decisions']:>3} 一致率={m['acc']:5.1f}% rating={m['rating']} 时间={m['gen']}")


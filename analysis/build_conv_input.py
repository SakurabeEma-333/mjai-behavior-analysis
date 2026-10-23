import json, os

SRC = r"soul-logs/games.jsonl"
OUT = r"soul-logs/conv-input.jsonl"
MAP = r"soul-logs/conv-map.jsonl"

n = 0
with open(SRC, encoding="utf-8") as f, open(OUT, "w", encoding="utf-8") as o, open(MAP, "w", encoding="utf-8") as m:
    for i, line in enumerate(f):
        g = json.loads(line)
        rule_disp = g.get("rule") or ""
        obj = {
            "log": g["log"],
            "name": ["A", "B", "C", "D"],
            "rule": {"disp": rule_disp, "aka": 0, "aka51": 1, "aka52": 1, "aka53": 1},
            "dan": g.get("dan") or [],
        }
        o.write(json.dumps(obj, ensure_ascii=False) + "\n")
        meta = g.get("meta") or {}
        m.write(json.dumps({
            "idx": i, "file": g["file"], "dir": g["dir"], "rule": rule_disp,
            "player": int(meta["player"]) if meta.get("player") else 0,
            "decisions": int(meta["decisions"]) if meta.get("decisions") else None,
            "hits": int(meta["hits"]) if meta.get("hits") else None,
            "acc": float(meta["acc"]) if meta.get("acc") else None,
            "rating": float(meta["rating"]) if meta.get("rating") else None,
            "kyoku": len(g["log"]),
        }, ensure_ascii=False) + "\n")
        n += 1

print(f"写出 {n} 局 -> {OUT}")

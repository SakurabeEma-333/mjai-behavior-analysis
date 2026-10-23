"""逐决策特征提取：动作类型、q差、区间宽度、巡目、立直状态、合法动作数"""
import os, sys, json, math

BASE = os.path.dirname(os.path.abspath(__file__))
WK = os.path.join(BASE, "review4")
sys.path.insert(0, WK)
os.chdir(WK)

import torch
from config import config
from model import Brain, DQN
from engine import MortalEngine
from libriichi.mjai import Bot

state = torch.load(config["control"]["state_file"], weights_only=True, map_location="cpu")
cfg = state["config"]
V = cfg["control"]["version"]
brain = Brain(version=V, num_blocks=cfg["resnet"]["num_blocks"],
              conv_channels=cfg["resnet"]["conv_channels"]).eval()
dqn = DQN(version=V).eval()
brain.load_state_dict(state["mortal"])
dqn.load_state_dict(state["current_dqn"])

H = ["E", "S", "W", "N", "P", "F", "C"]
AKA = {"5mr": 34, "5pr": 35, "5sr": 36}
ACT_TYPE = {37: "reach", 41: "pon", 42: "kan", 43: "hora", 45: "pass"}


def tile_idx(name):
    if name in AKA:
        return AKA[name]
    if name and name[-1] in "mps":
        return "mps".index(name[-1]) * 9 + int(name[0]) - 1
    if name in H:
        return 27 + H.index(name)
    return None


def event_to_action(e):
    t = e.get("type")
    if t == "dahai":
        return tile_idx(e.get("pai"))
    if t == "reach":
        return 37
    if t in ("chi", "pon", "daiminkan", "ankan", "kakan"):
        return 41
    if t == "hora":
        return 43
    return None


class Eng(MortalEngine):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rec = None

    def react_batch(self, obs, masks, invisible_obs):
        r = super().react_batch(obs, masks, invisible_obs)
        self.rec = (r[1][0], r[2][0])
        return r


def analyze(path, pid):
    events = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    eng = Eng(brain, dqn, version=V, is_oracle=False, device=torch.device("cpu"),
              enable_amp=False, enable_quick_eval=True,
              enable_rule_based_agari_guard=True, name="f")
    bot = Bot(eng, pid)
    out = []
    junme = 0
    riichi = set()
    for i, e in enumerate(events):
        t = e.get("type")
        if t == "start_kyoku":
            junme = 0
            riichi = set()
        bot.react(json.dumps(e, separators=(",", ":")))
        rec = eng.rec
        eng.rec = None
        if rec is not None:
            q, m = rec
            n = min(len(q), len(m))
            legal = [(k, float(q[k])) for k in range(n) if m[k] and math.isfinite(float(q[k]))]
            if legal:
                best = max(v for _, v in legal)
                lo = min(v for _, v in legal)
                vals = sorted((v for _, v in legal), reverse=True)
                gap12 = (vals[0] - vals[1]) if len(vals) > 1 else 0.0
                rng = best - lo
                nxt = events[i + 1] if i + 1 < len(events) else {}
                act = 45
                if nxt.get("actor") == pid:
                    a = event_to_action(nxt)
                    if a is not None:
                        act = a
                hit = act < n and m[act] and math.isfinite(float(q[act]))
                qa = float(q[act]) if hit else lo
                cost = (qa - lo) / rng if rng > 1e-6 else 1.0
                out.append(dict(
                    type=ACT_TYPE.get(act, "dahai"),
                    gap12=round(gap12, 4), rng=round(rng, 4), nlegal=len(legal),
                    cost=round(cost, 4), match=bool(hit and abs(qa - best) < 1e-9),
                    junme=junme, opp_riichi=len(riichi - {pid}),
                ))
        if t == "reach_accepted":
            riichi.add(e.get("actor"))
        if t == "dahai" and e.get("actor") == pid:
            junme += 1
    return out


if __name__ == "__main__":
    maps = [json.loads(l) for l in open(os.path.join(BASE, "soul-logs", "conv-map.jsonl"), encoding="utf-8")]
    a, b = int(sys.argv[1]), int(sys.argv[2])
    rows = []
    for rec in maps[a:b]:
        p = os.path.join(BASE, "soul-logs", "mjai-out", "%03d.mjai.jsonl" % rec["idx"])
        try:
            ds = analyze(p, rec["player"])
        except Exception as ex:
            print("ERR", rec["file"], ex)
            continue
        for d in ds:
            d["file"] = rec["file"]
            d["dir"] = rec["dir"]
        rows.extend(ds)
    with open(os.path.join(BASE, "soul-logs", "feat_%d_%d.jsonl" % (a, b)), "w", encoding="utf-8") as f:
        for d in rows:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print("rows", len(rows))

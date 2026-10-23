"""逐决策取 q 值并判定人类实际动作（含“过”窗口）"""
import os, sys, json, math, statistics as st

WK = os.path.abspath("review4")
sys.path.insert(0, WK)
os.chdir(WK)

import torch
from config import config
from model import Brain, DQN
from engine import MortalEngine
from libriichi.mjai import Bot

state = torch.load(config["control"]["state_file"], weights_only=True, map_location="cpu")
cfg = state["config"]; V = cfg["control"]["version"]
brain = Brain(version=V, num_blocks=cfg["resnet"]["num_blocks"],
              conv_channels=cfg["resnet"]["conv_channels"]).eval()
dqn = DQN(version=V).eval()
brain.load_state_dict(state["mortal"]); dqn.load_state_dict(state["current_dqn"])

H = ["E", "S", "W", "N", "P", "F", "C"]
AKA = {"5mr": 34, "5pr": 35, "5sr": 36}
PASS = 45


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
    if t == "chi":
        return 38
    if t == "pon":
        return 41
    if t in ("daiminkan", "ankan", "kakan"):
        return 42
    if t == "hora":
        return 43
    if t == "ryukyoku":
        return 44
    return None


class Cap(MortalEngine):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.rec = None

    def react_batch(self, obs, masks, invisible_obs):
        r = super().react_batch(obs, masks, invisible_obs)
        self.rec = (r[1][0], r[2][0])
        return r


def analyze(path, pid):
    events = []
    for line in open(path, encoding="utf-8", errors="replace"):
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except Exception:
                pass

    eng = Cap(brain, dqn, version=V, is_oracle=False, device=torch.device("cpu"),
              enable_amp=False, enable_quick_eval=True,
              enable_rule_based_agari_guard=True, name="v4")
    bot = Bot(eng, pid)
    out = []
    for i, e in enumerate(events):
        bot.react(json.dumps(e, ensure_ascii=True, separators=(",", ":")))
        if not eng.rec:
            continue
        q, m = eng.rec
        eng.rec = None
        # 人类实际动作 = 紧接着的下一个事件（若不是我方动作，则为“过”）
        act = None
        if i + 1 < len(events):
            nx = events[i + 1]
            if nx.get("actor") == pid:
                act = event_to_action(nx)
        if act is None:
            act = PASS
        n = min(len(q), len(m))
        legal = [(k, q[k]) for k in range(n) if m[k] and math.isfinite(q[k])]
        if len(legal) < 2:
            continue
        legal.sort(key=lambda kv: -kv[1])
        best, bestq = legal[0]
        qmin = legal[-1][1]
        idx = act if (0 <= act < n and m[act]) else None
        if idx is None:
            qa = qmin
        else:
            qa = q[idx]
        cost = (qa - qmin) / max(bestq - qmin, 1e-6)
        out.append(dict(match=(idx == best), cost=cost, gap=bestq - qa, act=act, best=best))
    return out


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    base = r".\soul-logs"
    maps = [json.loads(l) for l in open(os.path.join(base, "conv-map.jsonl"), encoding="utf-8")]
    rows = []
    for rec in maps[:limit]:
        path = os.path.join(base, "mjai-out", f"{rec['idx']:03}.mjai.jsonl")
        ds = analyze(path, rec["player"])
        acc_local = sum(1 for d in ds if d["match"]) / len(ds) * 100 if ds else 0
        costs = [d["cost"] for d in ds if not d["match"]]
        print(f"{rec['file'][:12]} {rec['dir']:<4} 本地={len(ds):>3} reviewer={rec['decisions']:>3} "
              f"本地一致率={acc_local:5.1f}% reviewer={rec['acc']:5.1f}% "
              f"均值成本={st.mean(costs) if costs else 1:.3f} 中位成本={st.median(costs) if costs else 1:.3f}")
    print(f"\n完成 {min(limit, len(maps))} 局")


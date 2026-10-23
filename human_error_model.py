"""Reference implementation of the observed human error structure.

Given the q-values of all legal actions in a decision, this samples an action
the way the measured human population behaves:

  1. If the decision is a call window (chi/pon/kan/pass), deviate with a fixed
     probability and take the opposite side (call <-> pass).
  2. If it is a discard, look up the error rate for the "gap" bucket
     (gap = best q - second best q) and, on deviation, sample a target quality
     from that bucket's empirical quantiles and pick the closest action.
  3. Otherwise take the best action.

Quality of an action is defined as (q - min_q) / (max_q - min_q) over the
legal actions, i.e. 1.0 = the best action, 0.0 = the worst.

No dependency on any game client, engine runtime, or network.
"""
from __future__ import annotations

import random
from typing import Iterable, List, Optional, Sequence, Tuple

# ----------------------------------------------------------------------------
# Empirical tables, fitted on the measured population (see results/gap_bins.csv)
# ----------------------------------------------------------------------------

# Upper bounds of the gap buckets (q units)
GAP_EDGES = (0.0, 0.1, 0.25, 0.5, 0.9, 1.5, 2.5)

# Deviation rate per bucket (fraction of decisions)
P_ERR = (0.5500, 0.4975, 0.4550, 0.3639, 0.2137, 0.1119, 0.0171)

# Quality quantiles (0.1 .. 0.9) of the deviations, per bucket
QUAL_Q = (
    (0.882, 0.938, 0.986, 0.990, 0.992, 0.992, 0.994, 0.996, 0.998),
    (0.878, 0.947, 0.971, 0.974, 0.976, 0.979, 0.982, 0.984, 0.986),
    (0.856, 0.919, 0.940, 0.949, 0.954, 0.957, 0.961, 0.965, 0.968),
    (0.781, 0.869, 0.897, 0.907, 0.914, 0.921, 0.927, 0.932, 0.939),
    (0.733, 0.807, 0.842, 0.855, 0.865, 0.873, 0.880, 0.888, 0.895),
    (0.633, 0.722, 0.754, 0.772, 0.788, 0.804, 0.814, 0.826, 0.845),
    (0.467, 0.583, 0.631, 0.654, 0.690, 0.714, 0.723, 0.749, 0.753),
)

# Call-window deviation rate
P_CALL_DEV = 0.1092

# Guarded action indices in the mjai 46-action space: 43 = win, 44 = draw
GUARDED = (43, 44)


def _bin_index(gap: float) -> int:
    idx = 0
    for i, edge in enumerate(GAP_EDGES):
        if gap >= edge:
            idx = i
    return min(idx, len(P_ERR) - 1)


def _quality(v: float, lo: float, hi: float) -> float:
    if hi - lo <= 1e-12:
        return 1.0
    return (v - lo) / (hi - lo)


def _sample_quality(qs: Sequence[float], rng: random.Random) -> float:
    """Uniform sample inside the empirical quantile ladder."""
    if not qs:
        return 1.0
    x = rng.random() * (len(qs) + 1)
    k = int(x)
    if k <= 0:
        return qs[0]
    if k >= len(qs):
        return qs[-1]
    frac = x - k
    return qs[k - 1] + (qs[k] - qs[k - 1]) * frac


def choose_action(
    q_values: Sequence[float],
    legal_mask: Sequence[bool],
    rng: Optional[random.Random] = None,
    state: float = 1.0,
) -> Tuple[int, dict]:
    """Pick an action index following the measured human error structure.

    Args:
        q_values:   per-action q values (46 entries for the mjai action space).
        legal_mask: which actions are legal at this decision.
        rng:        optional Random instance for reproducibility.
        state:      per-game scaling of the deviation rate (1.0 = nominal).

    Returns:
        (action_index, info) where info records the branch taken.
    """
    rng = rng or random.Random()
    n = min(len(q_values), len(legal_mask))
    legal: List[Tuple[int, float]] = [
        (i, float(q_values[i])) for i in range(n)
        if legal_mask[i] and q_values[i] == q_values[i]  # skip NaN
    ]
    if not legal:
        raise ValueError("no legal action")
    legal.sort(key=lambda kv: -kv[1])

    best_i, best_v = legal[0]
    if best_i in GUARDED:                       # never deviate from a win
        return best_i, {"branch": "guarded"}

    lo = legal[-1][1]
    gap = best_v - legal[1][1] if len(legal) > 1 else float("inf")

    is_call = any(i == 45 or 38 <= i <= 42 for i, _ in legal)
    if is_call:
        if rng.random() >= P_CALL_DEV * state:
            return best_i, {"branch": "call-keep"}
        alt = [x for x in legal if 38 <= x[0] <= 42] if best_i == 45 \
            else [x for x in legal if x[0] == 45]
        if not alt:
            return best_i, {"branch": "call-noalt"}
        return alt[0][0], {"branch": "call-flip"}

    b = _bin_index(gap)
    if rng.random() >= P_ERR[b] * state:
        return best_i, {"branch": "keep", "bin": b}

    target = _sample_quality(QUAL_Q[b], rng)
    best_pick, best_d, best_q = None, None, None
    for i, v in legal[1:]:
        q = _quality(v, lo, best_v)
        d = abs(q - target)
        if best_d is None or d < best_d:
            best_pick, best_d, best_q = i, d, q
    if best_pick is None:
        return best_i, {"branch": "keep", "bin": b}
    return best_pick, {"branch": "deviate", "bin": b, "target": round(target, 4),
                       "quality": round(best_q, 4), "loss": round(best_v - legal[0][1], 4)}


if __name__ == "__main__":
    # Toy demo: 13 legal discards, best q = 0, second = -0.35 (close call)
    import statistics as st

    q = [-9.0] * 46
    legal = [False] * 46
    for k, v in enumerate([0.0, -0.35, -0.6, -1.2, -2.0, -3.5, -5.0, -6.0, -6.5, -7.0, -7.5, -8.0, -8.5]):
        q[k] = v
        legal[k] = True

    rng = random.Random(0)
    picks = [choose_action(q, legal, rng) for _ in range(2000)]
    dev = [p for p, info in picks if info["branch"] == "deviate"]
    print(f"deviations: {len(dev)/len(picks)*100:.1f}% (table value for this gap: "
          f"{P_ERR[_bin_index(0.35)]*100:.1f}%)")
    if dev:
        print(f"mean quality of deviations: {st.mean([p[1]['quality'] for p in picks if p[1]['branch']=='deviate']):.3f}")

# mjai-behavior-analysis

[简体中文](README.md) | **English** | [日本語](README.ja.md)

A measurement study of **human decision consistency** in mahjong, using [Mortal](https://github.com/Equim-chan/Mortal) as the reference engine. The focus is on the **structure of human errors**: how often players deviate from the AI's top choice, and how that rate depends on how clear-cut the decision is.

This repository contains measurement and modelling code only. It does not include any game client automation, auto-play, or anti-cheat bypass.

## Key findings

Measured on 71 high-level games (10,585 decisions):

| Metric | Value |
|---|---|
| Agreement with AI top choice | **80.4%** (between-game sd 3.67pp) |
| Error rate | 19.62% |
| Errors that are "near-equivalent" (quality > 0.8) | **73.9%** |
| Errors that are "deep blunders" (quality < 0.2) | 11.5% |

**1. Error rate is a strong function of decision clarity**

Binned by the q-value gap between the best and second-best action:

| gap | decisions | error rate |
|---|---|---|
| 0 – 0.1 (close call) | 423 | **56.7%** |
| 0.3 – 0.6 | 1,013 | 48.1% |
| 1.2 – 2.5 | 2,396 | 14.6% |
| ≥ 2.5 (obvious) | 4,349 | **2.7%** |

**2. Agreement barely correlates with rank**

Tier 13 (81.6%), Tier 9 (83.3%), Tier 4 (80.1%), Tier 3 (79.2%) — the differences are far smaller than within-group variance and not statistically significant. Agreement measures stylistic similarity to the reference AI, not skill.

**3. Deep blunders come almost entirely from call decisions**

Discard errors cluster at quality 0.78–0.99 (swapping between near-equivalent tiles). Decisions with quality < 0.2 occur mostly on chi/pon/kan trade-offs (call-window deviation rate: 10.9%).

**4. Errors are approximately independent**

Lag-1 autocorrelation of the per-game error sequence is +0.021 (i.i.d. expectation −0.007).

**5. Game length has no effect on agreement**

Correlation between decisions-per-game and agreement: r = +0.034.

## Method

```
review report (HTML)  →  extract.py        metadata + game log
                      →  convcli           tenhou format → mjai events
                      →  analyze_human.py  per-decision q values, actual action
                      →  features.py       gap12 / legal actions / turn / riichi state
                      →  structure.py      binned statistics
                      →  table_gen.py      human behaviour table
```

`human_error_model.py` provides a reference implementation of the resulting model: given a q-value vector and a legal-action mask, it samples an action according to the fitted human behaviour table.

## Layout

```
analysis/    data pipeline and statistics
convcli/     tenhou → mjai converter CLI (built on convlog)
results/     aggregate results (CSV/JSON, no raw logs)
human_error_model.py   reference sampling implementation
PARAMETERS.md          parameter meanings and calibration
docs/findings.md       full findings and methodology
```

## Reproducing

You need your own Mortal weights and `libriichi` (not bundled). Point the scripts at them:

```python
MODEL_PATH = "./runtime/mortal.pth"   # provide your own
DATA_DIR   = "./data"                 # review report HTML files
```

## Data & privacy

No raw game logs are included. Everything under `results/` is aggregate statistics (binned rates and quantiles) that cannot be traced back to individual players. Ranks are anonymised as Tier-N.

## License

AGPL-3.0. Derived from [Mortal](https://github.com/Equim-chan/Mortal) (AGPL-3.0); it uses Mortal's `libriichi` runtime and the mjai protocol implementation, hence the same license.

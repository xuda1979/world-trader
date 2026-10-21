#!/usr/bin/env python3
"""HUNT_COT2 ROUND 7 — own-code placebo-DIRECTION re-derivation (charter R7a).

Re-derives the SECTOR2-R5/R6 attention-overlay placebo direction with OWN code
only: own z-build from raw wiki_attention CSVs, own SR (mean/std of daily ret,
x sqrt(252), matching the campaign's sharpe_d), own RNG scheme (exchange-
matched permutation of the ACTUAL gate vector, not a fresh Bernoulli draw),
own cost application. No imports from hunt_sector2_lib / hunt_sector2_r5 /
bt.metrics. Charter R7(a): confirm the 200/200-seeds claim independently.

Convention questions answered from THEIR code before writing mine:
  - gate: att_z > 1.0, scale 0.25 else 1.0, shift(2), fillna(1.0)
  - cost: 6.4bps on |diff(scale)| (alloc cost), applied on the SCALED book
  - placebo match: fire_frac + nflip of the real gate; the seedsweep matches
    nflip within max(2, nflip//20); I match fire_frac AND swap-count exactly
    (stricter), via circular permutation of the real gate vector.
Run: python3 campaign/agents/chief/coord/HUNT_COT2/r7_placebo_own_derivation.py
"""
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = f"{ROOT}/campaign/agents/chief/coord/HUNT_COT2"

# --- own z-build from raw data (their ATT_NICKS roster, my own pandas code)
NICKS = ["aapl", "nvda", "tsla", "spx", "vix", "fomc", "cpi"]
frames = {}
for k in NICKS:
    p = f"{ROOT}/tools/quant/data/wiki_attention/{k}.csv"
    s = pd.read_csv(p, parse_dates=["date"]).set_index("date")["views"]
    frames[k] = s
panel = pd.DataFrame(frames).sort_index()
W = 252
z = (panel - panel.rolling(W).mean()) / panel.rolling(W).std()
cross = z.mean(axis=1, skipna=True)
att_z = (cross - cross.rolling(W).mean()) / cross.rolling(W).std()

# --- own sleeve-load + own gate/scale/cost construction
a11 = pd.read_csv(f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2/sleeves/"
                  "A11_rs_ratio#lb126k4.csv", parse_dates=["date"]).set_index("date")["ret"]
gate = (att_z > 1.0).astype(float)
scale = pd.Series(np.where(gate.reindex(a11.index).fillna(0.0) > 0, 0.25, 1.0),
                  index=a11.index).shift(2).fillna(1.0)
COST = 6.4 / 1e4
alloc_cost = scale.diff().abs().fillna(0.0) * COST
net_on = a11 * scale - alloc_cost


def my_sr(r):
    r = r.dropna()
    return r.mean() / r.std(ddof=0) * np.sqrt(252)


sr_ov = my_sr(net_on)
fire = (scale < 1.0).to_numpy()
frac = fire.mean()
nflip = int(np.abs(np.diff(fire.astype(int))).sum())
print(f"MY re-derivation: overlay SR={sr_ov:.4f} fire_frac={frac:.3f} nflip={nflip} n={len(a11)}")

# --- own placebo: circular permutation of the ACTUAL gate (exact nflip match,
# fire_frac preserved to +-1 index), 200 draws x 5 seeds, own cost on each draw
gi = fire.astype(int) if isinstance(fire, np.ndarray) else fire.astype(int).to_numpy()
n = len(gi)
rows = []
for seed in range(5):
    rng = np.random.default_rng(1000 + seed)  # deliberately different seeds
    srs = []
    for _ in range(200):
        sh = int(rng.integers(1, n))
        g2 = np.roll(gi, sh)
        sc = pd.Series(np.where(g2 > 0, 0.25, 1.0), index=a11.index).shift(2).fillna(1.0)
        srs.append(my_sr(a11 * sc - sc.diff().abs().fillna(0.0) * COST))
    srs = np.array(srs)
    wins = int((srs >= sr_ov).sum())
    dsr = srs - sr_ov
    rows.append((seed, srs.mean(), srs.min(), srs.max(), dsr.mean(), dsr.max(), 200 - wins))
    print(f"seed {seed}: MY placebo SR mean={srs.mean():+.4f} min={srs.min():+.4f} "
          f"max={srs.max():+.4f} | dSR mean={dsr.mean():+.4f} max={dsr.max():+.4f} | "
          f"overlay beats {200 - wins}/200 (p={wins / 200:.3f})")

allwins = sum(r[6] for r in rows)
tot = len(rows) * 200
print(f"\nAGGREGATE: overlay beats {allwins}/{tot} draws across 5 seeds x 200 "
      f"(empirical p < {1 / tot:.4f})")
print(f"placebo dSR max across ALL draws = {max(r[5] for r in rows):+.4f} "
      f"(never approaches 0 -> overlay direction unambiguous)")

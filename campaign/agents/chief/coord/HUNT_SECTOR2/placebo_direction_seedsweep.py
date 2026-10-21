#!/usr/bin/env python3
"""R6 placebo-DIRECTION check (row-141 audit correction, independently verified).

The row-141 fraud-catch audit (CAMP_SHORT-owned row, "DEAD_IDEAS curation R6")
corrected this agent's R5 prose: placebo_p = beats/200, so p=0.000 means the
attention overlay BEAT all 200 matched random de-risk gates — NOT that the
random gates reproduce the lift. This script re-derives the engine's exact
placebo block (same inputs, same matching rule) across seeds 0..4 and prints
the direction and magnitude per seed, so the correction is verifiable from a
saved script rather than trusted from prose.

Expected: overlay beats 200/200 at every seed; placebo SR mean ~ +0.20 (dSR
mean ~ -0.47 vs overlay); row-141's quoted mean -0.473 / max -0.108 are in dSR
space and match this construction's dSR mean (-0.467 at seed 0).

Run: python3 placebo_direction_seedsweep.py   # from anywhere; paths absolute
"""
import statistics
import sys

import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
HERE = f"{ROOT}/campaign/agents/chief/coord/HUNT_SECTOR2"
for p in (ROOT, f"{ROOT}/tools", f"{ROOT}/campaign", f"{ROOT}/campaign/scripts", HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

import bt.metrics as bmetrics   # noqa: E402
import hunt_sector2_lib as L    # noqa: E402
import hunt_sector2_r5 as R5    # noqa: E402


def main():
    panel = R5.load_attention()
    att = R5.attention_z(panel)
    a11_csv = f"{HERE}/sleeves/A11_rs_ratio#lb126k4.csv"
    net_base = pd.read_csv(a11_csv, parse_dates=["date"]).set_index("date")["ret"]
    gate = (att > 1.0).astype(float)
    scale = pd.Series(np.where(gate.reindex(net_base.index).fillna(0.0) > 0, 0.25, 1.0),
                      index=net_base.index).shift(2).fillna(1.0)

    def alloc_cost(sc):
        return sc.diff().abs().fillna(0.0) * L.COST / 1e4

    net_on = net_base * scale - alloc_cost(scale)
    sr_ov = bmetrics.sharpe_d(net_on)

    fire = (scale < 1.0).to_numpy()
    frac = fire.mean()
    nflip = int(np.abs(np.diff(fire.astype(int))).sum())
    print(f"overlay SR={sr_ov:.4f}  fire_frac={frac:.3f}  nflip={nflip}  n={len(net_base)}")

    for seed in range(5):
        rng = np.random.default_rng(seed)
        srs = []
        for _ in range(200):
            g = (rng.random(len(net_base)) < frac).astype(int)
            for _try in range(50):
                if abs(int(np.abs(np.diff(g)).sum()) - nflip) <= max(2, nflip // 20):
                    break
                g = (rng.random(len(net_base)) < frac).astype(int)
            gs = pd.Series(g, index=net_base.index).shift(2).fillna(0.0)
            sc = pd.Series(np.where(gs > 0, 0.25, 1.0), index=net_base.index)
            srs.append(bmetrics.sharpe_d(net_base * sc - alloc_cost(sc)))
        wins = sum(1 for s in srs if s >= sr_ov)
        dsrs = [s - sr_ov for s in srs]
        print(f"seed {seed}: placebo SR mean={statistics.mean(srs):+.4f} "
              f"min={min(srs):+.4f} max={max(srs):+.4f} | dSR mean="
              f"{statistics.mean(dsrs):+.4f} max={max(dsrs):+.4f} | overlay beats "
              f"{200 - wins}/200 (p={wins / 200:.3f})")
    print("row-141 quote: mean -0.473, max -0.108, z 5.04 (dSR space, own seed)")


if __name__ == "__main__":
    main()

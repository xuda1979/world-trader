"""pairs_blend_check.py -- interrogate the reversal+momentum blend candidate.

The blend (5/10 reversal + 20/20 momentum, within-sector, 3.8 bps) was the
only result passing the paired scramble falsification (t~2.07) but it fails
subsample stability (0 in first half, +2 in second).  Before calling it a
regime bet, three checks:

  A. Parameter neighborhood: does a NEIGHBORHOOD of (form,hold,k) survive,
     or just the one lucky point?
  B. Sector decomposition: leave-one-sector-out -- is the effect one sector
     (e.g. Technology)?
  C. Vol regime: is the second half just a high-vol regime where the fixed
     3.8 bps cost drag shrinks relative to the gross edge?  Report SPY vol
     and cross-sectional dispersion per half, plus cost sensitivity.
"""
from __future__ import annotations
import sys, math, statistics, random, json, time

sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import pairs_crosssec as pc

COST_BPS = 3.8
N_SEEDS = 8
OUT = __import__("os").path.join(pc._HERE, "reports", "pairs_blend_check.json")


def blend_series(cal, m, secs, f1, h1, f2, h2, k, scramble=False, seed=0):
    rng = random.Random(seed) if scramble else None
    _, g1 = pc.run_book(cal, m, secs, f1, h1, top_k=k, scramble=scramble,
                        rng=rng)
    _, g2 = pc.run_book(cal, m, secs, f2, h2, top_k=k, scramble=scramble,
                        momentum=True, rng=rng)
    return [(a + b) / 2 for a, b in zip(g1, g2)]


def main():
    t0 = time.time()
    secs = {k: v for k, v in pc.v4.SECTORS.items() if k != "ETFs"}
    cal, m, _ = pc.build_matrix(secs)
    n = len(cal)
    half = n // 2

    # ---------- C: vol regime per half
    spy = None
    import csv as _csv
    p = __import__("os").path.join(pc._HERE, "data", "polygon", "SPY.csv")
    if __import__("os").path.exists(p):
        closes = []
        with open(p) as f:
            for r in _csv.DictReader(f):
                try:
                    closes.append(float(r["close"]))
                except (ValueError, KeyError):
                    continue
        vol_half = []
        for lo, hi in ((50, half), (half, n)):
            seg = closes[lo:hi]
            rets = [seg[i] / seg[i - 1] - 1 for i in range(1, len(seg))]
            vol_half.append(statistics.pstdev(rets) * math.sqrt(252))
        print(f"SPY ann vol: first half {vol_half[0]*100:.1f}%  "
              f"second half {vol_half[1]*100:.1f}%")

    # ---------- A: parameter neighborhood (gross, no costs for speed of
    # comparison; report net at 3.8 for the base cells)
    print("\n== A. parameter neighborhood (gross Sharpe, real vs 8-seed scram) ==")
    cells = [
        ("5/10+20/20 k2 (base)", 5, 10, 20, 20, 2),
        ("5/10+20/20 k1", 5, 10, 20, 20, 1),
        ("3/10+20/20 k2", 3, 10, 20, 20, 2),
        ("10/10+20/20 k2", 10, 10, 20, 20, 2),
        ("5/5+20/20 k2", 5, 5, 20, 20, 2),
        ("5/20+20/20 k2", 5, 20, 20, 20, 2),
        ("5/10+10/10 k2", 5, 10, 10, 10, 2),
        ("5/10+40/20 k2", 5, 10, 40, 20, 2),
        ("5/10+20/10 k2", 5, 10, 20, 10, 2),
    ]
    results = []
    for name, f1, h1, f2, h2, k in cells:
        real = blend_series(cal, m, secs, f1, h1, f2, h2, k)
        scram = [blend_series(cal, m, secs, f1, h1, f2, h2, k,
                              scramble=True, seed=5000 + s)
                 for s in range(N_SEEDS)]
        rg = pc.metrics(real)
        sg = [pc.metrics(x)["sharpe"] for x in scram]
        mu_s = statistics.fmean(sg)
        sd_s = statistics.pstdev(sg) if N_SEEDS > 1 else 0.0
        z = (rg["sharpe"] - mu_s) / sd_s if sd_s > 0 else 0.0
        # paired daily-diff t
        ts = []
        for x in scram:
            d = [a - b for a, b in zip(real, x)]
            m_ = statistics.fmean(d)
            sd_ = statistics.pstdev(d) if len(d) > 1 else 1.0
            ts.append(m_ / sd_ * math.sqrt(len(d)) if sd_ > 0 else 0.0)
        # half-split of real
        h1m = pc.metrics(real[:half]); h2m = pc.metrics(real[half:])
        results.append((name, rg, mu_s, sd_s, z, statistics.fmean(ts),
                        h1m["sharpe"], h2m["sharpe"]))
        print(f"{name:22s} gross={rg['sharpe']:+.2f}  scram {mu_s:+.2f}+-{sd_s:.2f}  "
              f"z={z:+.2f}  t_paired={statistics.fmean(ts):+.2f}  "
              f"halves {h1m['sharpe']:+.2f}/{h2m['sharpe']:+.2f}")

    # ---------- B: leave-one-sector-out (base cell)
    print("\n== B. leave-one-sector-out (gross, base cell) ==")
    for excl in sorted(secs):
        sub = {k2: v2 for k2, v2 in secs.items() if k2 != excl}
        real = blend_series(cal, m, sub, 5, 10, 20, 20, 2)
        rg = pc.metrics(real)
        print(f"  exclude {excl:16s} gross={rg['sharpe']:+.2f} "
              f"({rg['mean_bps']:+.2f} bps/d)")

    # ---------- cost sensitivity (base cell)
    print("\n== cost sensitivity (base cell, net Sharpe) ==")
    for cb in (0.0, 3.8, 7.6, 15.2):
        real_n = pc.run_book(cal, m, secs, 5, 10, top_k=2, scramble=False,
                             cost_bps=cb)[0]
        real_n2 = pc.run_book(cal, m, secs, 20, 20, top_k=2, scramble=False,
                              momentum=True, cost_bps=cb)[0]
        rn = [(a + b) / 2 for a, b in zip(real_n, real_n2)]
        mm = pc.metrics(rn)
        print(f"  cost {cb:5.1f} bps: net Sharpe={mm['sharpe']:+.2f}")

    with open(OUT, "w") as f:
        json.dump({
            "cells": [{"name": c[0], "real_gross": c[1], "scram_mean": c[2],
                       "scram_sd": c[3], "z": c[4], "t_paired": c[5],
                       "half1": c[6], "half2": c[7]} for c in results],
            "cost_sens": [
                (cb, pc.metrics([(a + b) / 2 for a, b in zip(
                    pc.run_book(cal, m, secs, 5, 10, top_k=2, scramble=False,
                                cost_bps=cb)[0],
                    pc.run_book(cal, m, secs, 20, 20, top_k=2, scramble=False,
                                momentum=True, cost_bps=cb)[0])])["sharpe"])
                for cb in (0.0, 3.8, 7.6, 15.2)]},
            f, indent=1, default=str)
    print(f"\nWrote {OUT} in {time.time()-t0:.0f}s", file=sys.stderr)


if __name__ == "__main__":
    main()

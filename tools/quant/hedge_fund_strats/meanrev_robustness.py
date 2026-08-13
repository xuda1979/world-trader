"""Parameter-robustness of the mean-reversion crash-sleeve (2026-08-13 loop).

Prior fires: reversal profits in flagship's loss episodes (2020 +32%, 2018Q4
+23%), validated PASS on signal-scramble Editions. THIS fire tests whether that
crash-insurance value is ROBUST to the (k, n) choice (not a knife-edge artifact
of picking winners). Sweep k in {3,5,8,10} x n in {10,20,30,40} and report the
flagship-loss-episode totals + full-window SR for each. We judge robustness by
HOW CONSISTENTLY the sleeve is positive in the 2020 COVID / 2018 Q4 episodes
(the two the flagship bleeds most in) across the grid.

Usage: python tools/quant/hedge_fund_strats/meanrev_robustness.py
"""
import json
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from tools.quant.hedge_fund_strats.meanrev_episode_research import load_prices_rets, backtest

RES = Path(__file__).resolve().parent / "results"
KS = [3, 5, 8, 10]
NS = [10, 20, 30, 40]
EPS = {"2018 Q4": ("2018-10-10", "2019-08-07"), "2020 COVID": ("2020-02-24", "2020-04-17"),
       "2011 Euro": ("2011-07-27", "2012-01-13"), "2022-24 bear": ("2022-01-05", "2024-02-29")}


def main():
    prices, rets = load_prices_rets()
    print("=" * 76)
    print("MEAN-REVERSION CRASH-SLEEVE — PARAMETER ROBUSTNESS (k x n)")
    print("=" * 76)
    out = {}
    # header
    print(f"{'k':>2} {'n':>3} | {'fullSR':>6} | " +
          " ".join(f"{e:>8}" for e in EPS), flush=True)
    pos_2020 = 0
    pos_2018 = 0
    total_cells = 0
    for k in KS:
        for n in NS:
            r = backtest(prices, rets, k, n)
            sr = r.mean() / r.std() * np.sqrt(252)
            e2020 = float(r[(r.index >= EPS["2020 COVID"][0]) & (r.index <= EPS["2020 COVID"][1])].sum() * 100)
            e2018 = float(r[(r.index >= EPS["2018 Q4"][0]) & (r.index <= EPS["2018 Q4"][1])].sum() * 100)
            e2011 = float(r[(r.index >= EPS["2011 Euro"][0]) & (r.index <= EPS["2011 Euro"][1])].sum() * 100)
            e2224 = float(r[(r.index >= EPS["2022-24 bear"][0]) & (r.index <= EPS["2022-24 bear"][1])].sum() * 100)
            total_cells += 1
            if e2020 > 0:
                pos_2020 += 1
            if e2018 > 0:
                pos_2018 += 1
            print(f"{k:>2} {n:>3} | {sr:>6.2f} | {e2020:>8.1f} {e2018:>8.1f} "
                  f"{e2011:>8.1f} {e2224:>8.1f}", flush=True)
            out[f"k{k}_n{n}"] = {"full_sr": round(float(sr), 3),
                                 "2020_covid_pct": round(e2020, 2), "2018_q4_pct": round(e2018, 2),
                                 "2011_euro_pct": round(e2011, 2), "2022_24_pct": round(e2224, 2)}
    print(f"\n2020 COVID positive in {pos_2020}/{total_cells} cells")
    print(f"2018 Q4 positive in {pos_2018}/{total_cells} cells")
    out["_summary"] = {"n_cells": total_cells, "2020_positive": pos_2020,
                       "2018_positive": pos_2018}
    with open(RES / "meanrev_robustness.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print("\nWrote results/meanrev_robustness.json")


if __name__ == "__main__":
    main()

"""Multi-strategy blend variants at the current TRADING_COST_BPS.

At the user's real cost (6 bps/side = 12 bps round-trip), the stat-arb
leg of the classic 4-stream blend is a net drag (it is -0.85 SR alone).
This script compares:

  1. 4-stream EW   (L/S 130/30 + CTA futures + Global Macro + StatArb)
  2. 3-stream EW   (same minus StatArb)
  3. 3-stream Sharpe-weighted (in-sample weight = SR / sum(SR))
  4. 3-stream vol-parity (inverse-vol weights)

and reports full-window + sub-period geometric Sharpe for each.

Usage:  python tools/quant/hedge_fund_strats/blend_variants.py
        (run after run_all.py + run_extras.py at the target cost)
"""

import glob
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from core import compute_performance  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
RISK_FREE = 0.02

PERIODS = [
    ("2008-2012", "2008-01-01", "2012-12-31"),
    ("2013-2017", "2013-01-01", "2017-12-31"),
    ("2018-2022", "2018-01-01", "2022-12-31"),
    ("2023-2026", "2023-01-01", "2026-12-31"),
]

STREAMS = {
    "ls": "equity_L_S_130_30.csv",
    "cta": "equity_CTA_Futures_multi_21d.csv",
    "macro": "equity_Global_Macro.csv",
    "statarb": "equity_StatArb_40pairs_z15.csv",
}


def geom_sharpe(r: pd.Series) -> float:
    g = np.log1p(r.dropna())
    return (g.mean() * 252 - RISK_FREE) / (g.std() * np.sqrt(252)) if g.std() > 0 else np.nan


def full_stats(r: pd.Series):
    eq = (1 + r.dropna()).cumprod()
    p = compute_performance(r.dropna(), eq, benchmark_returns=None)
    return p.sharpe, p.annual_return, p.max_drawdown


def main():
    curves = {}
    for key, fn in STREAMS.items():
        path = os.path.join(RESULTS, fn)
        if not os.path.exists(path):
            print(f"  MISSING {fn} — run run_all.py/run_extras.py first")
            continue
        eq = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        curves[key] = eq.pct_change()

    df = pd.DataFrame(curves).dropna()
    print(f"window: {df.index.min().date()}..{df.index.max().date()} ({len(df)} days)\n")

    variants = {
        "4-stream EW": df.mean(axis=1),
        "3-stream EW": df[["ls", "cta", "macro"]].mean(axis=1),
    }
    # Sharpe-weighted: weights ∝ full-sample geometric SR of each leg
    srs = {k: geom_sharpe(df[k]) for k in ["ls", "cta", "macro"]}
    w = pd.Series(srs).clip(lower=0)
    w = w / w.sum()
    variants["3-stream Sharpe-wtd"] = df[["ls", "cta", "macro"]].mul(w, axis=1).sum(axis=1)
    # Vol parity
    vols = {k: df[k].std() for k in ["ls", "cta", "macro"]}
    v = 1 / pd.Series(vols)
    v = v / v.sum()
    variants["3-stream vol-parity"] = df[["ls", "cta", "macro"]].mul(v, axis=1).sum(axis=1)

    out = {}
    for name, r in variants.items():
        sr, ret, mdd = full_stats(r)
        subs = [geom_sharpe(r.loc[s:e]) for _, s, e in PERIODS]
        out[name] = {"Sharpe": sr, "AnnRet": ret, "MaxDD": mdd}
        print(f"{name:24s} SR {sr:+.2f}  ret {ret*100:+.1f}%  MaxDD {mdd*100:.1f}%  | "
              + "  ".join(f"{v:+.2f}" for v in subs))
        print(f"{'':24s}  sub-period SR: {[p[0] for p in PERIODS]}")

    pd.DataFrame(out).T.round(4).to_csv(os.path.join(RESULTS, "blend_variants_12rt.csv"))
    print("\nsaved -> results/blend_variants_12rt.csv")


if __name__ == "__main__":
    main()

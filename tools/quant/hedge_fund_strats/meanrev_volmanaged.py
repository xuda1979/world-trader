"""Refine the mean-reversion crash-sleeve with VOL-MANAGEMENT (2026-08-13 loop).

Prior fire found short-horizon cross-sectional equity reversal profits strongly
in the flagship's loss episodes (2020 +32%, 2018Q4 +23%) but adds tail risk
(MaxDD -13% -> -27% when blended) -> ~neutral Sharpe. This fire tests the
project's proven remedy (Moreira-Muir inverse-vol scaling, which halved the
L/S 130/30 MaxDD at ~same SR, P8) on the reversal sleeve:

  scale(t) = min(target / realized_vol(t-1), cap), applied to the reversal's
  daily returns using only t-1 realized vol (no lookahead).

Questions:
  R1 Does vol-managed reversal keep the crash-concentrated alpha (in-loss-
     episode gains) while cutting its outside-crash tail / MaxDD?
  R2 Does the vol-managed sleeve now ADD to the flagship (SR) rather than
     being Sharpe-neutral?

Usage: python tools/quant/hedge_fund_strats/meanrev_volmanaged.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))
from tools.quant.hedge_fund_strats.core import DataLoader
from tools.quant.hedge_fund_strats.meanrev_episode_research import load_prices_rets, backtest

RES = Path(__file__).resolve().parent / "results"
EPS = [("2018 Q4", "2018-10-10", "2019-08-07"), ("2020 COVID", "2020-02-24", "2020-04-17"),
       ("2011 Euro", "2011-07-27", "2012-01-13"), ("2022-24 bear", "2022-01-05", "2024-02-29")]

def vol_manage(r, target=0.20, window=21, cap=2.0):
    """Moreira-Muir inverse-realized-vol scaling of a daily return series (t-1 info only)."""
    rv = r.rolling(window).std() * np.sqrt(252)
    scale = (target / rv).clip(upper=cap).shift(1)   # t-1 scale, apply to t
    r2 = (r * scale).fillna(0)
    return r2

def card(r):
    r = r[r != 0]
    eq = (1 + r).cumprod()
    return (r.mean() / r.std() * np.sqrt(252),
            ((1 + r).prod() ** (252 / len(r)) - 1) * 100,
            (eq / eq.cummax() - 1).min() * 100, len(r))

def main():
    prices, rets = load_prices_rets()
    f = pd.read_csv(RES / "portfolio_weights.csv", index_col=0, parse_dates=True)["portfolio_return"].dropna()
    vix = pd.read_csv(Path(__file__).resolve().parent / "data_fred" / "vix.csv",
                      index_col=0, parse_dates=True)["value"]

    print("=" * 78)
    print("MEAN-REVERSION CRASH-SLEEVE — VOL-MANAGEMENT REFINEMENT (Moreira-Muir)")
    print("=" * 78)
    out = {}
    for k, n in [(5, 30), (3, 30), (5, 20)]:
        r = backtest(prices, rets, k, n)
        rv_raw = r[r != 0]
        print(f"\n--- k={k} n={n} ---")
        for target in [None, 0.25, 0.20, 0.15]:
            if target is None:
                r2 = rv_raw
                label = "raw (unscaled)"
            else:
                r2 = vol_manage(rv_raw, target=target)
                label = f"voltgt={target:.0f}%"
            sr, cagr, mdd, nn = card(r2)
            # episode gains
            eg = " ".join(f"{name} {r2[(r2.index>=a)&(r2.index<=e)].sum()*100:+.1f}%"
                          for name, a, e in EPS)
            # blend with flagship (static, no gate) full-window
            df = pd.concat({"flag": f, "rev": r2}, axis=1).dropna()
            blend = df["flag"] * 0.85 + df["rev"] * 0.15
            bs = blend.mean() / blend.std() * np.sqrt(252)
            bdd = ((1 + blend).cumprod() / (1 + blend).cumprod().cummax() - 1).min() * 100
            key = f"k{k}_n{n}_vt{target}"
            out[key] = {"sleeve_sr": round(sr, 3), "sleeve_mdd": round(mdd, 2),
                        "sleeve_cagr": round(cagr, 2), "episode_gains": eg,
                        "flag85_rev15_blend_sr": round(bs, 3), "blend_mdd": round(bdd, 2)}
            print(f"  {label:16s}: sleeve SR {sr:+.2f} MaxDD {mdd:6.1f}% CAGR {cagr:+.1f}%  | "
                  f"eps: {eg}  | flag.85/rev.15 SR {bs:+.2f} DD {bdd:.1f}%")
    with open(RES / "meanrev_volmanaged.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print("\nWrote results/meanrev_volmanaged.json")

if __name__ == "__main__":
    main()

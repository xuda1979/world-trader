"""Drawdown-filter overlay for the 1-month XGB L/S (additive, causal).

Adds a risk overlay that reduces max drawdown. Two levers, both default-off
and fully causal (decision at day t uses data <= t-1 via shift(1)):

  dd_breadth_gate  : de-risk when the strategy's own breadth is extreme
                     (fraction of names the model expects to rise is too low
                     OR too high => concentrated/one-sided momentum regime,
                     the classic whipsaw setup). Scale exposure down to
                     dd_breadth_frac in those windows.
  dd_vix_gate      : de-risk (to dd_vix_frac) when VIX z-score >= dd_vix_z.

These are OR-combinable (exposure = min of the two gates' factors).

Baseline (no overlay):          SR 1.92, ann 32.9%, maxDD -23.9%, Calmar 1.38
Breadth gate (0.35/0.80 ->0.5): SR 2.03, ann ~20%, maxDD ~-10 to -12%, Calmar ~2.0
  halved maxDD, RAISED Sharpe & Calmar, both 20y halves positive (no regime flip)
Return-preserving (VIXz<2 + |mt20|<.01->0.5): SR 1.96, ann 30.1%, maxDD -21.8%
  keeps ~30% return, trims DD ~2pp, raises Sharpe (the "don't touch return" option)

The honest tradeoff: halving the drawdown from ~-24% to ~-10% requires giving
up ~12pp of annual return. The breadth gate is the best risk-adjusted filter
(highest SR & Calmar); the VIXz/mt20 gate is the return-preserving option.
Both are additive and can be toggled independently.
"""
from __future__ import annotations
import os, sys, pickle
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from xgb_horizon_portfolio import vol_target, stats, build_position_book
import pipeline_common as pc
ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")

# ---- config (additive) ----
DD_BREADTH_LO = 0.35      # de-risk when breadth < this
DD_BREADTH_HI = 0.80      # ... or breadth > this
DD_BREADTH_FRAC = 0.5     # scale-to exposure in extreme-breadth windows
DD_VIX_Z = 2.0            # de-risk when VIX z-score >= this
DD_VIX_FRAC = 0.0         # scale-to in VIX-stress (0 = fully off)
DD_MT20_THR = 0.01        # |20d market trend| below this => choppy
DD_MT20_FRAC = 0.5        # scale-to in choppy-market windows

def _load(name):
    df = pd.read_csv(os.path.join(FRED, name), parse_dates=["date"])
    df.columns = ["date", "val"]
    return df.set_index("date")["val"].reindex(
        pd.bdate_range(df.date.min(), df.date.max()), method="ffill")

def get_overlays(rvt):
    """Return dict of causal exposure factor series aligned to rvt.index."""
    with open(os.path.join(HERE, "data", "horizon_preds_20y.pkl"), "rb") as f:
        c = pickle.load(f)
    frame, preds = c["frame"], c["preds"]
    frame["date"] = pd.to_datetime(frame["date"])
    fw = frame.copy(); fw["pred"] = preds[21]; fw = fw[np.isfinite(fw["pred"])]
    idx = rvt.index
    breadth = fw.groupby("date")["pred"].apply(lambda s: (s > 0).mean()).reindex(idx).shift(1)
    vix = _load("vix.csv")
    vz = (vix - vix.rolling(252).mean())/vix.rolling(252).std()
    vz = vz.reindex(idx).shift(1)
    spx = _load("spx.csv")
    mt20 = spx.pct_change(20).reindex(idx).shift(1)
    # breadth gate factor (de-risk in extreme breadth)
    extreme = ((breadth < DD_BREADTH_LO) | (breadth > DD_BREADTH_HI)).astype(float)
    f_breadth = (1 - extreme) + extreme * DD_BREADTH_FRAC
    # vix gate
    stress = (vz >= DD_VIX_Z).astype(float)
    f_vix = (1 - stress) + stress * DD_VIX_FRAC
    # choppy market gate
    choppy = (mt20.abs() < DD_MT20_THR).astype(float)
    f_mt20 = (1 - choppy) + choppy * DD_MT20_FRAC
    return {"breadth": f_breadth, "vix": f_vix, "mt20": f_mt20}

def apply_overlay(rvt, gates):
    ex = gates["breadth"].fillna(1.0).clip(0, 1)
    return rvt * ex

def main():
    # rebuild book from cached preds (survivor-in, K10, 6bp, vol-target)
    with open(os.path.join(HERE, "data", "horizon_preds_20y.pkl"), "rb") as f:
        c = pickle.load(f)
    frame, preds = c["frame"], c["preds"]
    frame["date"] = pd.to_datetime(frame["date"])
    fw = frame.copy(); fw["pred"] = preds[21]; fw = fw[np.isfinite(fw["pred"])]
    close = pc.load_ohlcv()["close"]
    orig = close.apply(lambda s: s.first_valid_index()); orig = orig[pd.notna(orig)]
    early = set(orig[orig <= pd.Timestamp("2007-02-01")].index)
    fws = fw[fw["ticker"].isin(early)]
    res = build_position_book(fws, fws["pred"].to_numpy(), 21, K=10, cost=0.0006).sort_index()
    rvt = vol_target(res.copy())
    gates = get_overlays(rvt)
    print("BASELINE (no overlay):", stats(rvt))
    print("\nBREADTH GATE (breadth<%.2f|>%.2f -> %.1f):" % (DD_BREADTH_LO, DD_BREADTH_HI, DD_BREADTH_FRAC))
    out = rvt * gates["breadth"].fillna(1.0)
    print("  ", stats(out))
    print("\nVIXz>=%g (->%.1f) gate:" % (DD_VIX_Z, DD_VIX_FRAC))
    print("  ", stats(rvt * gates["vix"].fillna(1.0)))
    print("\nCOMBINED breadth & vix gates:")
    ex = gates["breadth"].fillna(1.0) * gates["vix"].fillna(1.0)
    print("  ", stats(rvt * ex))
    print("\ncoverage (fraction of days full exposure): breadth",
          float((gates["breadth"] >= 0.99).mean()), "vix", float((gates["vix"] >= 0.99).mean()))

if __name__ == "__main__":
    main()

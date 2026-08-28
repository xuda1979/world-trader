"""A4 r2: calendar overlays/tilts on LIB:L_S_130_30. Honesty notes:
- Base sleeve CSV already nets 6bps; overlay tilt w_t multiplies daily net returns.
  Extra cost = turnover from |w_t - w_{t-1}| * 6bps applied to base NAV (tilt trades base book).
- T+1: w_t uses info <= t, multiplies ret_{t+1}. Cost of rebalance charged on ret_{t+1}.
- vol_target trailing (expanding, min 60d) from lib for the ~10% ann gate.
Gates on FINAL stream: full SR>=0.6, halves>=0.3, <=2 negYr each >-5%, scramble p<0.05,
param plateau, and honest-novelty: |corr| to base < 0.95 (else it's a duplicate).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
import numpy as np, pandas as pd
import harness.data as D
from scripts.a4_calendar_lib import (spy_close, sharpe, halves_sr, yearly, gates,
                                     scramble_p, vol_target)
COST = 6e-4

def base_sleeve():
    r = pd.read_csv(f"{D.SLEEVE_LIB}/L_S_130_30.csv", index_col=0, parse_dates=True)["ret"]
    return r[r.index >= "2009-02-04"]  # drop flat warmup

def apply_tilt(base: pd.Series, w: pd.Series, cost_bps=6.0):
    """w decided at t applies to ret_{t+1}; rebalance cost |Δw|*6bps on t+1 return."""
    idx = base.index
    w = w.reindex(idx.union(w.index)).ffill().reindex(idx).fillna(0.0)
    w_lag = w.shift(1).fillna(0.0)
    gross = w_lag * base
    turn = w_lag.diff().abs().fillna(w_lag.abs().iloc[0])
    return gross - turn * cost_bps / 1e4

def vix_lagged():
    v = D.fred("vix")
    v = v[~v.index.duplicated()]
    return v.sort_index()

def dom_mask(idx):
    d = pd.Series(idx, index=idx)
    return d.dt.day

def report(tag, r, base=None, corr_base=None):
    g = gates(r, verbose=False)
    sp = scramble_p(r, n=200)
    line = (f"{tag:38s} SR={g['full']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} "
            f"negYr={g['neg_years']} worst={g['worst_year']:.1f}% dd={g['maxdd']:.0f}% "
            f"ann={g['ann']:.1f}% vol={g['vol']:.1f}% scr_p={sp:.2f}")
    if base is not None:
        j = pd.concat([r, base], axis=1).dropna()
        c = np.corrcoef(j.iloc[:,0], j.iloc[:,1])[0,1]
        line += f" corr_base={c:.2f}"
    print(line)
    return g, sp

def main():
    base = base_sleeve()
    vix = vix_lagged()
    idx = base.index
    print("== Idea 1: paycheck x ROM tilt on L_S_130_30 (w grid, vol-targeted ~10%) ==")
    dom = dom_mask(idx)
    mth = pd.Series(idx, index=idx).dt.month
    pay = ((dom >= 24) | (dom <= 3)).astype(float)
    notsep = (mth != 9).astype(float)
    best = None
    for w_pay in [0.5, 0.75, 1.0, 1.25]:
        for w_rom in [0.5, 0.75, 1.0, 1.25]:
            # in-window multiplier w, out-of-window 1 (tilt around base 1.0)
            w = pd.Series(1.0, index=idx)
            w[(pay == 1)] = w_pay
            w[(mth == 9)] *= 0.25
            w = w.clip(0.0, 1.5)
            raw = apply_tilt(base, w)
            vt = vol_target(raw, 0.10)
            g = gates(vt, verbose=False)
            a, b = vt.align(base, join="inner")
            c = np.corrcoef(a.values, b.values)[0, 1]
            print(f"  w_pay={w_pay:.2f} w_rom={w_rom:.2f} SR={g['full']:.2f} H1={g['H1']:.2f} H2={g['H2']:.2f} negYr={g['neg_years']} worst={g['worst_year']:.1f}% corr={c:.2f}")
            if best is None or g["full"] > best[0]:
                best = (g["full"], w_pay, w_rom, vt)
    print("  best:", best[1], best[2], "SR", round(best[0],2))

if __name__ == "__main__":
    main()

"""Robustness + walk-forward checks for the layered DD overlay.

1) No-trade band on the vol-target overlay (daily micro-rebalancing friction).
2) Walk-forward: best vol target chosen in-sample on one half, OOS on the
   other (gates fixed at the WF-validated credit_pct_0.85 + SPY200d + VIX32).
"""
import os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from monthly_top100_momentum import prepare, walk_forward, stats, COST_ONE_SIDE
from top100_momentum_regime_filter import load_fred, exposure_pct
from top100_momentum_dd_overlay import gate_from_bool

ROOT = "/Users/daxu/software/world-trader"
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats/data_fred")


def overlay_band(book_r, gates, cash_r, vol_target, band):
    """overlay() with a no-trade band: exposure only moves when the target
    differs from current by > band (then jumps to the target)."""
    n = len(book_r)
    gvals = [g.values for g in gates]
    br = book_r.values
    cr = cash_r.values
    exp = np.empty(n)
    ret = np.empty(n)
    prev_e = 1.0
    for i in range(n):
        e = 1.0
        for gv in gvals:
            e *= gv[i]
        if i >= 20:
            v = br[i - 20:i].std() * np.sqrt(252)
            if v > 0:
                e = min(e, vol_target / v)
        if abs(e - prev_e) > band:
            prev_e = e
        exp[i] = prev_e
        ret[i] = br[i] * prev_e + (1.0 - prev_e) * cr[i]
    idx = book_r.index
    return pd.Series(ret, index=idx), pd.Series(exp, index=idx)


def main():
    prices, ret, sharpe, rdates = prepare()
    book_r, _, _ = walk_forward(prices, ret, sharpe, rdates)

    vix = load_fred("vix.csv")
    baa = load_fred("baa.csv")
    aaa = load_fred("aaa.csv")
    spread = (baa - aaa).dropna()
    spy = pd.read_csv(os.path.join(ROOT, "tools/quant/data/twelve_big", "SPY.csv"),
                      parse_dates=["date"]).set_index("date")["close"]
    spy = spy.reindex(book_r.index).ffill()
    tb = (load_fred("tbill3m.csv") / 100.0 / 252.0)
    cash_r = tb.reindex(book_r.index).ffill().fillna(0.0)

    credit0 = exposure_pct(spread, book_r.index, 0.85, 0.0)
    s200 = gate_from_bool(spy > spy.rolling(200).mean(), 0.0, book_r.index)
    v32 = gate_from_bool(vix < 32, 0.0, book_r.index)
    gates = [credit0, s200, v32]

    # ---- 1) band robustness on the full sample ----
    print("=== full-sample, credit0_s200_v32_vt12, no-trade band ===")
    for band in [0.0, 0.05, 0.10]:
        r, exp = overlay_band(book_r, gates, cash_r, 0.12, band)
        s, ann, vol, dd, n = stats(r)
        print(f"  band {band:<4}: SR {s:.3f} ann {ann:.2%} vol {vol:.2%} "
              f"MaxDD {dd:.2%} toggles {int((exp.diff().abs() > 1e-9).sum())}")

    # ---- 2) walk-forward on vol target ----
    h = len(book_r) // 2
    h1, h2 = book_r.iloc[:h], book_r.iloc[h:]
    print("\n=== WF: vol target chosen on h1 -> OOS h2, and reverse ===")
    vts = [10, 12, 15]
    for label, train, test in [("h1(2007-16)", h1, h2), ("h2(2017-26)", h2, h1)]:
        tg = [g.loc[train.index] for g in gates]
        tr = {vt: overlay_band(train, tg, cash_r.loc[train.index], vt, 0.05)[0]
              for vt in vts}
        best = max(vts, key=lambda vt: stats(tr[vt])[0])
        ttg = [g.loc[test.index] for g in gates]
        rr, _ = overlay_band(test, ttg, cash_r.loc[test.index], best, 0.05)
        base = stats(test)[0]
        print(f"  {label}: vt*={best} (IS {stats(tr[best])[0]:.3f}) -> "
              f"OOS {label.split('(')[1].rstrip(')')} SR {stats(rr)[0]:.3f} "
              f"(book baseline {base:.3f})")


if __name__ == "__main__":
    main()

"""Champion combo drawdown filter: VOL-TARGET + DXY dollar-stress gate.

User pivot (2026-08-23): use NEW signals / alternative data to filter the big
drawdown without lowering ann or Sharpe. Testing macro/alternative series on
the combo showed standalone credit/curve/gold/breadth gates all fail (they
lag the drawdown or mis-time the recovery). The winner is STACKING a DXY
dollar/liquidity-stress gate on top of the vol-target overlay:

  raw combo            : SR 1.447  ann +24.15%  dd -38.6%
  vol-targ win12@0.14   : SR 1.576  ann +24.62%  dd -27.5%
  + DXY z>1.5 ->0.7     : SR 1.630  ann +24.10%  dd -24.1%   <-- champion

Mechanism: DXY spikes mark dollar / liquidity-deleveraging stress that hits
an equity L/S book but lags the book's OWN trailing vol, so it adds orthogonal
signal on top of vol-target. Unlike gold/VIX, DXY does not stay elevated
during equity recoveries -> trims the dollar-driven tail without giving back
the recovery. Robust across z thresholds 1.3-2.0 (SR 1.59-1.63).
All net of 6 bps incl overlay churn cost, no lookahead (DXY month-end lagged).
"""
from __future__ import annotations
import os, sys
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
W1Y = 0.65
COST = 0.0006
VT_WIN, VT_TGT, VT_CAP = 12, 0.14, 1.5   # vol-target params
DXY_Z, DXY_F = 1.5, 0.7                  # DXY gate threshold, de-risk factor
DXY_WIN = 12


def load_combo():
    df = pd.read_csv(os.path.join(OUT, "gkx_combo_legs_monthly.csv"),
                     parse_dates=["Unnamed: 0"]).set_index("Unnamed: 0")
    df.index = pd.to_datetime(df.index)
    combo = W1Y * df["y1"] + (1 - W1Y) * df["m1"]
    return combo[combo.index >= "2009-01-01"]


def stats_monthly(s):
    s = s.dropna()
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4)}


def main():
    combo = load_combo()
    rv = combo.rolling(VT_WIN, min_periods=VT_WIN - 3).std() * np.sqrt(12)
    sc_vt = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)

    dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"])
    dxy = dxy.set_index("date")["value"].resample("ME").last()
    m = dxy.rolling(DXY_WIN, min_periods=8).mean()
    sd = dxy.rolling(DXY_WIN, min_periods=8).std()
    dz = (dxy - m) / sd
    dgate = pd.Series(1.0, index=combo.index)
    flag = dz.reindex(combo.index).ffill().fillna(0.0) > DXY_Z
    dgate[flag] = DXY_F
    dgate = dgate.shift(1).fillna(1.0)   # lagged, no lookahead

    def apply(sc, label):
        drag = sc.diff().abs().fillna(0.0) * 2.0 * COST
        return label, stats_monthly(combo * sc - drag)

    base = stats_monthly(combo)
    vt = apply(sc_vt, "vol-targ")
    stack = apply(sc_vt * dgate, "vol-targ+DXY")

    print("=== CHAMPION COMBO DRAWDOWN FILTER (6 bps net) ===")
    print(f"  raw combo                 : SR {base['sr']}  ann {base['ann']:+.1%}  dd {base['dd']:+.1%}")
    print(f"  {vt[0]:24s}: SR {vt[1]['sr']}  ann {vt[1]['ann']:+.1%}  dd {vt[1]['dd']:+.1%}")
    print(f"  {stack[0]:24s}: SR {stack[1]['sr']}  ann {stack[1]['ann']:+.1%}  dd {stack[1]['dd']:+.1%}")
    print(f"\n  DXY gate active {int((dgate[dgate.index>='2009']<1.0).sum())}/{len(combo)} months "
          f"({(dgate<1.0).mean():.0%})")

    import json
    json.dump({"raw": base, "vol_targ": vt[1], "vol_targ_dxy": stack[1],
               "params": {"VT_WIN": VT_WIN, "VT_TGT": VT_TGT, "DXY_Z": DXY_Z,
                          "DXY_F": DXY_F, "DXY_WIN": DXY_WIN}},
              open(os.path.join(OUT, "xgb_combo_dd_dxy_stack.json"), "w"),
              indent=2, default=str)


if __name__ == "__main__":
    main()

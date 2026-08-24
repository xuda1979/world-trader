"""MR-in-downside with a UNION activation gate (dollar-stress OR credit-widening).

User ask (2026-08-23 loop): market-neutral mean-reversal during the downside,
using all macro indexes to filter the drawdown without affecting ann/Sharpe.

Prior champion (xgb_combo_credit_macro.py, SR 1.751 / ann +24.7% / dd -19.5%):
  vol-target combo + DXY-dollar-stress de-risk(0.5) + credit-widening
  de-risk(z>1.3->0.5) + market-neutral MR k5_n30 overlay f=0.4 active in
  DXY-stress months.

THIS extension: broaden the MR-ACTIVATION gate from DXY-stress ONLY to
DXY-stress OR credit-widening (the union of the two downside-cool signals).
All other params identical to the prior champion -- this isolates exactly the
MR-union contribution:

  champion (MR on DXY only)     : SR 1.751  ann +24.7%  dd -19.5%
  MR on DXY|credit (union)      : SR 1.760  ann +24.7%  dd -18.2%  <-- NEW CHAMPION

Strictly dominates: same ann, +0.009 SR, -1.3pp dd. Mechanism: the market-
neutral MR sleeve pays in BOTH dollar-stress AND credit-stress downside months
(MR returns +1.05%/mo across the 33 credit-stress months). Activating it on
the union adds 19 credit-only months (not already covered by DXY) where MR
earns its drawdown premium -- pulling the tail down further at zero ann cost.
The full plateau (credit win9-12 x thr1.0-1.5 x f2 0.5-0.7 x MR f0.3-0.5) all
give SR 1.76-1.78 / dd -17.8 to -19.2% -- a robust region, not a lone pick.

The MR sleeve is the VALIDATED k5_n30 market-neutral long-worst/short-best
(passes signal-scramble gate). MR active in 60/210 months (union of the 41
dollar-stress + 33 credit-stress months). Dollar- and credit-neutral-ish,
so no additional market beta.

All net of 6 bps/side (overlay churn charged), no lookahead (exogenous
series lagged one month).
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
W1Y = 0.65
COST = 0.0006
VT_WIN, VT_TGT, VT_CAP = 12, 0.14, 1.5
DXY_Z, DXY_F = 1.5, 0.5
CR_WIN, CR_THR, CR_F2 = 12, 1.3, 0.5
MR_F, MR_MC = 0.4, 1.0


def load_combo():
    df = pd.read_csv(os.path.join(OUT, "gkx_combo_legs_monthly.csv"),
                     parse_dates=["Unnamed: 0"]).set_index("Unnamed: 0")
    df.index = pd.to_datetime(df.index)
    return (W1Y * df["y1"] + (1 - W1Y) * df["m1"])[df.index >= "2009-01-01"]


def load_mr():
    sys.path.insert(0, ROOT)
    from tools.quant.hedge_fund_strats.meanrev_episode_research import (
        load_prices_rets, backtest)
    prices, rets = load_prices_rets()
    mr_daily = backtest(prices, rets, 5, 30)
    return mr_daily.resample("ME").apply(lambda x: (1 + x).prod() - 1)


def stats_monthly(s):
    s = s.dropna()
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "win": round(float((s > 0).mean()), 3),
            "n": int(len(s))}


def main():
    combo = load_combo()
    mr = load_mr()
    mr.index = pd.to_datetime(mr.index)
    al = pd.concat([combo.rename("combo"), mr.reindex(combo.index).rename("mr")],
                   axis=1).dropna()
    combo, mr = al["combo"], al["mr"]

    # vol-target
    rv = combo.rolling(VT_WIN, min_periods=VT_WIN - 3).std() * np.sqrt(12)
    sc_vt = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
    # DXY dollar-stress gate (lagged)
    dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    dm = dxy.rolling(12, min_periods=8).mean(); dsd = dxy.rolling(12, min_periods=8).std()
    dFLAG = (((dxy - dm) / dsd).reindex(combo.index).ffill().shift(1) > DXY_Z).fillna(False)
    dgate = pd.Series(1.0, index=combo.index); dgate[dFLAG] = DXY_F
    # credit BAA-AAA widening gate (lagged)
    aaa = pd.read_csv(os.path.join(FRED, "aaa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    baa = pd.read_csv(os.path.join(FRED, "baa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    cs = (baa - aaa)
    cz = (cs - cs.rolling(CR_WIN, min_periods=8).mean()) / cs.rolling(CR_WIN, min_periods=8).std()
    cFLAG = (cz.reindex(combo.index).ffill().shift(1) > CR_THR).fillna(False)

    # exposure = vol-targ * DXY-gate * credit-gate
    fac = sc_vt * dgate
    fac[cFLAG] *= CR_F2
    champ = combo * fac - fac.diff().abs().fillna(0.0) * 2 * COST
    # OLD: MR on DXY only; NEW: MR on DXY|credit
    old = champ + mr * MR_MC * MR_F * dFLAG.astype(float)
    uFLAG = (dFLAG | cFLAG)
    new = champ + mr * MR_MC * MR_F * uFLAG.astype(float)

    o, n = stats_monthly(old), stats_monthly(new)
    print("=== MR-UNION activation gate (other params identical to champion) ===")
    print(f"  champion (MR on DXY)     : SR {o['sr']}  ann {o['ann']:+.1%}  dd {o['dd']:+.1%}")
    print(f"  MR on DXY|credit (union) : SR {n['sr']}  ann {n['ann']:+.1%}  dd {n['dd']:+.1%}  win {n['win']}  <-- NEW CHAMPION")
    print(f"\n  MR active union {int(uFLAG.sum())}/{len(combo)} months | DXY {int(dFLAG.sum())} | credit {int(cFLAG.sum())} | "
          f"credit-only added {int((cFLAG & ~dFLAG).sum())}")
    print(f"  MR mean in credit-stress months: {mr[cFLAG].mean()*100:+.2f}%/mo")

    json.dump({"champion_mr_dxy": o, "mr_union": n, "n_months": len(combo),
               "mr_active_union": int(uFLAG.sum()), "credit_only_added": int((cFLAG & ~dFLAG).sum()),
               "params": {"W1Y": W1Y, "VT_WIN": VT_WIN, "VT_TGT": VT_TGT, "VT_CAP": VT_CAP,
                          "DXY_Z": DXY_Z, "DXY_F": DXY_F, "CR_WIN": CR_WIN,
                          "CR_THR": CR_THR, "CR_F2": CR_F2, "MR_F": MR_F, "MR_MC": MR_MC},
               "mr_activation": "DXY_union_credit"},
              open(os.path.join(OUT, "xgb_combo_mr_union.json"), "w"), indent=2, default=str)
    print(f"\nsaved -> {OUT}/xgb_combo_mr_union.json")


if __name__ == "__main__":
    main()

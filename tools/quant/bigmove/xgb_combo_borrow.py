"""Borrow-cost (call-rate) model on the champion L/S stack's SHORT leg.

User ask (2026-08-23): "include trading cost 6 bps per trade and call rate
(interest rate when you borrow stocks) at interactive brokers' level in the
backtesting and reports."

IBKR stock-borrow ("recall/call") rates are paid on the SHORT NOTIONAL. For a
dollar-neutral long/short equity book the short leg still pays the borrow/call
rate on its notional. Model:

  short_notional(m) = short exposure of the combo (fac, ~0.97x avg)
                    + MR-sleeve short when active (0.4*uFLAG*1.0)
  borrow drag(m)    = short_notional(m) * borrow_rate_annual / 12

IBKR-tiered call rates for liquid US names are typically 0.10-0.50%/yr (easy to
borrow); hard-to-borrow names run 1-5%+. We tabulate the champion across the
full range 0-3% and call out the 1.0%/yr blended case as the realistic center.

Champion (w1y=0.75, xgb_combo_w1y_opt.py) - no borrow:
  SR 1.774  ann +24.8%  dd -16.5%
With 1.0%/yr blended borrow on short notional:
  SR ~1.70  ann +23.6%  dd -17.0%   <- still strongly positive, focus for report
"""
from __future__ import annotations
import os, sys, json
import numpy as np, pandas as pd

ROOT = "/Users/daxu/software/world-trader"
OUT = os.path.join(ROOT, "tools/quant/reports", "xgb_horizons")
FRED = os.path.join(ROOT, "tools/quant/hedge_fund_strats", "data_fred")
COST = 0.0006
W1Y = 0.75
BR = (0.0, 0.0025, 0.005, 0.01, 0.015, 0.02, 0.03)  # annual borrow rates
# champion params (identical to xgb_combo_w1y_opt.py)
VT_WIN, VT_TGT, VT_CAP = 12, 0.14, 1.5
DXY_Z, DXY_F = 1.5, 0.5
CR_WIN, CR_THR, CR_F2 = 12, 1.3, 0.5
MR_F, MR_MC = 0.4, 1.0

sys.path.insert(0, ROOT)
from tools.quant.hedge_fund_strats.meanrev_episode_research import load_prices_rets, backtest


def stats_monthly(s):
    s = s.dropna()
    eq = (1 + s).cumprod()
    return {"sr": round(float(s.mean() / s.std() * np.sqrt(12)), 3),
            "ann": round(float((1 + s).prod() ** (12 / len(s)) - 1), 4),
            "dd": round(float((eq / eq.cummax() - 1).min()), 4),
            "win": round(float((s > 0).mean()), 3),
            "n": int(len(s))}


def main():
    legs = pd.read_csv(os.path.join(OUT, "gkx_combo_legs_monthly.csv"),
                       parse_dates=["Unnamed: 0"]).set_index("Unnamed: 0")
    legs.index = pd.to_datetime(legs.index)
    legs = legs.loc[legs.index >= "2009-01-01"]
    combo = W1Y * legs["y1"] + (1 - W1Y) * legs["m1"]

    # MR sleeve (validated k5_n30, dollar-neutral, 6bp net)
    prices, rets = load_prices_rets()
    mr_d = backtest(prices, rets, 5, 30)
    mr = mr_d.resample("ME").apply(lambda x: (1 + x).prod() - 1)
    mr.index = pd.to_datetime(mr.index)
    al = pd.concat([combo.rename("combo"), mr.reindex(combo.index).rename("mr")],
                   axis=1).dropna()
    combo, mr = al["combo"], al["mr"]

    # vol-target
    rv = combo.rolling(VT_WIN, min_periods=VT_WIN - 3).std() * np.sqrt(12)
    sc_vt = (VT_TGT / rv).clip(upper=VT_CAP, lower=0.0).fillna(1.0)
    # DXY gate
    dxy = pd.read_csv(os.path.join(FRED, "dxy.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    dm = dxy.rolling(12, min_periods=8).mean(); dsd = dxy.rolling(12, min_periods=8).std()
    dFLAG = (((dxy - dm) / dsd).reindex(combo.index).ffill().shift(1) > DXY_Z).fillna(False)
    dgate = pd.Series(1.0, index=combo.index); dgate[dFLAG] = DXY_F
    # credit gate
    aaa = pd.read_csv(os.path.join(FRED, "aaa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    baa = pd.read_csv(os.path.join(FRED, "baa.csv"), parse_dates=["date"]).set_index("date")["value"].resample("ME").last()
    cs = (baa - aaa)
    cz = (cs - cs.rolling(CR_WIN, min_periods=8).mean()) / cs.rolling(CR_WIN, min_periods=8).std()
    cFLAG = (cz.reindex(combo.index).ffill().shift(1) > CR_THR).fillna(False)

    fac = sc_vt * dgate
    fac[cFLAG] *= CR_F2
    champ = combo * fac - fac.diff().abs().fillna(0.0) * 2 * COST
    uFLAG = (dFLAG | cFLAG)
    base = champ + mr * MR_MC * MR_F * uFLAG.astype(float)

    # short notional proxy (see module docstring)
    short_notional = fac + MR_F * uFLAG.astype(float) * MR_MC

    print("=== CHAMPION + IBKR stock-borrow (call) rate on SHORT leg ===")
    print(f"short notional: mean {short_notional.mean():.3f} (combo short fac mean "
          f"{fac.mean():.3f}; MR short active mean {(MR_F*uFLAG.astype(float)).mean():.3f})")
    print(f"MR sleeve active {int(uFLAG.sum())}/{len(uFLAG)} months")
    print(f"\n{'borrow/yr':9s} | {'SR':>6s} {'ann':>8s} {'dd':>7s}   (monthly drag)")
    res = {}
    for br in BR:
        borrow = short_notional * br / 12.0
        r = base - borrow
        st = stats_monthly(r)
        res[f"{br*100:.2f}%"] = st
        print(f"{br*100:6.2f}%  | {st['sr']:6.3f} {st['ann']:7.1%} {st['dd']:7.1%}   "
              f"({borrow.mean()*100:.2f}%/mo)")

    out = {"w1y": W1Y, "months": int(len(combo)),
           "short_notional_mean": round(float(short_notional.mean()), 3),
           "results": res,
           "params": {"VT_WIN": VT_WIN, "VT_TGT": VT_TGT, "DXY_Z": DXY_Z,
                      "DXY_F": DXY_F, "CR_WIN": CR_WIN, "CR_THR": CR_THR,
                      "CR_F2": CR_F2, "MR_F": MR_F, "MR_MC": MR_MC},
           "note": "borrow drag on short notional = short_notional * annual_rate / 12"}
    json.dump(out, open(os.path.join(OUT, "xgb_combo_borrow.json"), "w"),
              indent=2, default=str)
    print(f"\nsaved -> {OUT}/xgb_combo_borrow.json")


if __name__ == "__main__":
    main()

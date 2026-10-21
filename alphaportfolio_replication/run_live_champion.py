#!/usr/bin/env python3
"""LIVE SIGNAL for the champion composite (deployment tool).

Prints the CURRENT recommended allocation (as of the last complete
month-end): SPY13MA gate state, vol-target scale, top momentum+tilt
names, and the gold sleeve. No look-ahead: all inputs are month-end
values strictly before the signal date.

Usage:
  python3 run_live_champion.py            # print snapshot + save JSON
Env (optional, defaults = champion): TILT_W, GOLD_W, GATE_LB, MOM_LB,
  G_DIV, VOL_TARGET, VOL_CAP, REV_SLEEVE
"""
from __future__ import annotations
import os, sys, json
import numpy as np
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path: sys.path.insert(0, HERE)
import risk_gate as rg
import run_champion_fund_tilt as R

def main():
    px = R.build_panel()
    fwd = px.pct_change(1).shift(-1)
    comp = sum(px.pct_change(n) for n in R.MOM_LB)/len(R.MOM_LB)
    spy = rg.load_daily("SPY").resample("ME").last()
    gld = pd.read_csv(R.GLD_CSV, index_col=0, parse_dates=True)
    c = "close" if "close" in gld.columns else gld.columns[0]
    gld_m = gld[c].astype(float).resample("ME").last()
    tilts = R.build_fund_tilts(px)
    if R.TILT_MODE in ("value","quality","gm","prof","ag"):
        tilt = tilts[R.TILT_MODE]
    elif R.TILT_MODE == "vq":
        tilt = tilts["value"].mul(R.V_W).add(tilts["quality"].mul(R.Q_W)).div(R.V_W+R.Q_W)
    elif R.TILT_MODE == "vqp":
        tilt = tilts["value"].add(tilts["quality"]).add(tilts["prof"]).div(3)
    else:
        tilt = tilts["value"].add(tilts["quality"]).add(tilts["gm"]).div(3)

    # signal date = last month-end with forward data (strictly before today)
    dt = px.index[-2]
    spy_m = float(spy.asof(dt)); ma13 = float(spy[spy.index<=dt].tail(R.GATE_LB).mean())
    gate_on = spy_m >= ma13
    mom_sig = comp.loc[dt].dropna()
    tt = tilt.loc[dt] if dt in tilt.index else None
    if R.TILT_W > 0 and tt is not None and tt.dropna().shape[0] > 30:
        mz = R.rank_z(mom_sig.reindex(tt.dropna().index).dropna())
        tz = R.rank_z(tt.dropna().reindex(mz.index).dropna())
        c_ = mz.index.intersection(tz.index)
        if len(c_) > 30:
            mom_sig = (1-R.TILT_W)*mz.loc[c_] + R.TILT_W*tz.loc[c_]
    s = mom_sig.dropna(); c = s.index.intersection(fwd.loc[dt].dropna().index)
    G = max(1, len(c)//R.G_DIV)
    top = s.loc[c].sort_values(ascending=False)
    held = top.index[:G].tolist()
    gld_level = float(gld_m.asof(dt))
    out = {
        "as_of": dt.strftime("%Y-%m-%d"),
        "gate": "ON" if gate_on else "OFF",
        "spy": round(spy_m, 1), "spy_13ma": round(ma13, 1),
        "n_held": len(held),
        "top_15": [{"symbol": x, "score": round(float(top.loc[x]), 3)} for x in top.index[:15]],
        "allocation": {
            "book_pct": round((1-R.GOLD_W)*100, 1),
            "gold_pct": round(R.GOLD_W*100, 1),
            "gold_level": round(gld_level, 2),
        },
        "config": {"TILT_MODE": R.TILT_MODE, "TILT_W": R.TILT_W, "GOLD_W": R.GOLD_W,
                   "GATE_LB": R.GATE_LB, "MOM_LB": R.MOM_LB, "G_DIV": R.G_DIV,
                   "VOL_TARGET": R.VOL_TARGET, "VOL_CAP": R.VOL_CAP, "REV_SLEEVE": R.REV_SLEEVE},
    }
    print(f"Champion live signal as of {out['as_of']}:")
    print(f"  Gate: {out['gate']} (SPY {out['spy']} vs 13MA {out['spy_13ma']})")
    print(f"  Holdings: {out['n_held']} names; top: " + ", ".join(x["symbol"] for x in out["top_15"]))
    print(f"  Allocation: {out['allocation']['book_pct']}% book + {out['allocation']['gold_pct']}% GLD")
    print(f"  Config: {json.dumps(out['config'])}")
    with open(os.path.join(HERE, "data", "live_champion.json"), "w") as fh:
        json.dump(out, fh, indent=2)
    # paper-trade history: append this signal for forward tracking
    hist = os.path.join(HERE, "data", "live_champion_history.csv")
    row = pd.DataFrame([{"as_of": out["as_of"], "gate": out["gate"], "n_held": out["n_held"],
                         "spy": out["spy"], "spy_13ma": out["spy_13ma"],
                         "top": ",".join(x["symbol"] for x in out["top_15"])}])
    if os.path.exists(hist):
        old_h = pd.read_csv(hist)
        if old_h["as_of"].astype(str).eq(out["as_of"]).any():
            print(f"  {out['as_of']} already in history (skip)")
        else:
            pd.concat([old_h, row], ignore_index=True).to_csv(hist, index=False)
            print(f"  appended to data/live_champion_history.csv")
    else:
        row.to_csv(hist, index=False)
        print(f"  wrote data/live_champion_history.csv")
    print(f"  saved data/live_champion.json")

if __name__ == "__main__":
    main()

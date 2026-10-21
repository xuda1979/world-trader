"""RES_CALENDAR r1 thin repro — regenerates every headline number in FINDINGS.md round 1.
Run from repo root: python3 campaign/team/agents/RES_CALENDAR/sleeves/repro_r1.py
Data: free/on-disk (more_etf closes; FOMC calendar rebuilt from federalreserve.gov via
direct HTTP — see work/fomc_ann_final.json). Verdict: REJECT (0 sleeves pass all gates).
"""
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../.."))  # repo root
sys.path.insert(0, f"{ROOT}/campaign")
from bt.engine import (lag_signal, vol_target_scale, cost_turnover,  # noqa: E402
                       borrow_cost, margin_cost, cap_leverage)
from bt.gates import run as gates_run  # noqa: E402
from bt.metrics import report  # noqa: E402

ANN = json.load(open(f"{ROOT}/campaign/team/agents/RES_CALENDAR/work/fomc_ann_final.json"))


def panel():
    rets = {}
    d = f"{ROOT}/tools/quant/data/more_etf"
    for f in sorted(os.listdir(d)):
        if not f.endswith(".csv") or f == "manifest.csv":
            continue
        df = pd.read_csv(f"{d}/{f}", index_col=0, parse_dates=True)
        s = pd.to_numeric(df["close"], errors="coerce").dropna()
        rets[f[:-4]] = np.log(s).diff()
    P = pd.DataFrame(rets).clip(-0.25, 0.25)
    P = P[P.index >= "2008-01-01"]
    return P[[c for c in P.columns if P[c].notna().sum() >= 250]]


def book(sig, r):
    pos = lag_signal(sig).fillna(0.0)
    w = cap_leverage((pos * vol_target_scale(r).fillna(1.0)).to_frame("w"), 1.6)
    wc = w["w"]
    net = (wc * r - cost_turnover(w, 6.4) - borrow_cost(w)
           - margin_cost(wc.abs(), 0.045, 1.6)).dropna()
    return net, wc


def main():
    P = panel()
    EW = P.mean(axis=1)
    d_str = pd.Series(EW.index.strftime("%Y-%m-%d"), index=EW.index)
    da = d_str.shift(1).fillna("").isin(ANN)
    x = EW[da]
    print(f"[1] EW82 day-after-FOMC: n={len(x)} mean={x.mean()*1e4:+.2f}bp "
          f"t={x.mean()/x.std()*np.sqrt(len(x)):+.2f} (control {EW[~da].mean()*1e4:+.2f}bp)")
    netA, wA = book(pd.Series(np.where(d_str.isin(ANN), -1.0, 0.0), index=EW.index), EW)
    print(f"[2] A basket-short-day-after: {report(netA)}")
    u = pd.to_numeric(pd.read_csv(f"{ROOT}/tools/quant/data/more_etf/UNG.csv",
                                  index_col=0, parse_dates=True)["close"],
                      errors="coerce").dropna()
    ru = np.log(u).diff()
    ru = ru[ru.index >= "2008-01-01"]
    thu = ru[ru.index.dayofweek == 3]
    print(f"[3] UNG Thursday gross: n={len(thu)} mean={thu.mean()*1e4:+.1f}bp "
          f"t={thu.mean()/thu.std()*np.sqrt(len(thu)):+.2f}")
    netB, wB = book(pd.Series(np.where(ru.index.dayofweek == 2, -1.0, 0.0), index=ru.index), ru)
    print(f"[4] B UNG short-Thu (Wed entry): {report(netB)}")
    champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                        index_col=0, parse_dates=True)["ret"]
    J = netA.index.union(netB.index)
    C = 0.5 * netA.reindex(J).fillna(0) + 0.5 * netB.reindex(J).fillna(0)
    wC = 0.5 * wA.reindex(J).fillna(0) + 0.5 * wB.reindex(J).fillna(0)
    rpu = (C / wC).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    g = gates_run(rpu, ref=champ, sig=wC.reindex(rpu.index).fillna(0).values, scramble_n=200)
    print("[5] C 50/50 gates:", {k: (round(g[k], 3) if isinstance(g[k], float) else g[k])
                                 for k in ["sr", "h1", "h2", "neg_years", "worst",
                                           "uniq", "corr", "scr_p", "leak_ok", "pass"]})


if __name__ == "__main__":
    main()

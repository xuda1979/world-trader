#!/usr/bin/env python3
"""GOVERNED V8 EVAL (2026-09-30) — full daily-ledger comparison, V7 vs V8-GOV vs A4.
Same engine as hardstop_counterfactual.py (A0 recon vs committed ledger = 7.2e-16).
Writes V8GOV_EVAL_2026-09-30.csv. CANDIDATE EVAL ONLY — no system-of-record change.
"""
import os, json
import numpy as np
import pandas as pd

B = "/Users/daxu/software/world-trader/campaign"
OD = os.path.join(B, "work_backtest_oos")
LEV, CALL, COST = 1.6, 0.053, 6.4
IS_END = pd.Timestamp("2017-01-01")
TRAIL2Y = pd.Timestamp("2024-10-01")


def load(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


w7 = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)["w"].astype(float)
w8 = pd.read_csv(os.path.join(OD, "V8GOV_candidate_weights.csv"), index_col=0)["w"].astype(float)

KRW = [s for s in w7.index if "FXD1_KRWTRI" in s][0]
XREV = [s for s in w7.index if "crossasset_rev_L8" in s][0]
w4 = w7.copy(); w4[KRW] = 0.0; w4[XREV] = 0.0
A4_POST = w4 / w4.sum()

all_slv = sorted(set(w7.index) | set(w8.index))
daily = pd.DataFrame({s: load(s) for s in all_slv})
panel = daily[~daily.index.duplicated(keep="last")].sort_index()
panel = panel[panel.index >= "2009-01-01"].fillna(0.0)
dates = panel.index


def build_ledger(w, start_switch=None):
    """Daily ledger, monthly rebalance to static w. If start_switch given, use A4_POST
    weights from that date (zero-HARD-stop arm)."""
    net = pd.Series(0.0, index=dates)
    wl = None
    prev = None
    for d in dates:
        target = w if (start_switch is None or d < start_switch) else A4_POST
        m = (d.month, d.year)
        if wl is None or m != prev:
            if wl is None:
                wl = target.copy()
                net[d] -= float((wl.abs() * COST / 1e4).sum())
            else:
                qty = (target - wl).abs()
                net[d] -= float((qty * COST / 1e4).sum())
                wl = target.copy()
            prev = m
        net[d] += float(LEV * (target * panel.loc[d, target.index]).sum())
        net[d] -= (LEV - 1.0) * CALL / 252
        wl = wl * (1.0 + panel.loc[d, target.index])
    return net


def metrics(net_d):
    net_m = (1 + net_d).resample("ME").prod() - 1
    oos = net_m[net_m.index >= IS_END]
    t2y = net_m[net_m.index >= TRAIL2Y]
    dd = ((1 + net_d).cumprod() / (1 + net_d).cumprod().cummax() - 1).min()
    yrs = net_m.groupby(net_m.index.year).sum()
    oos_yrs = yrs[yrs.index >= 2017]
    halves = net_m.dropna()
    h = len(halves) // 2
    return {
        "full_sr": round(float(net_m.mean() / net_m.std() * np.sqrt(12)), 4),
        "oos_sr": round(float(oos.mean() / oos.std() * np.sqrt(12)), 4),
        "full_ann": round(float(net_m.mean() * 12 * 100), 3),
        "oos_ann": round(float(oos.mean() * 12 * 100), 3),
        "trail2y_sr": round(float(t2y.mean() / t2y.std() * np.sqrt(12)), 4),
        "trail2y_ann": round(float(t2y.mean() * 12 * 100), 3),
        "daily_dd": round(float(dd * 100), 3),
        "neg_years_full": int((yrs < 0).sum()),
        "neg_years_oos": int((oos_yrs < 0).sum()),
        "h1_sr": round(float(halves.iloc[:h].mean() / halves.iloc[:h].std() * np.sqrt(12)), 4),
        "h2_sr": round(float(halves.iloc[h:].mean() / halves.iloc[h:].std() * np.sqrt(12)), 4),
    }


led = pd.read_csv(os.path.join(OD, "OPT_20V7_FULL_LEDGER.csv"), parse_dates=["date"])
g = led.groupby("date")[["pnl", "cost"]].sum().sort_index()
net_committed = (g.pnl - g.cost).sort_index()

out = {}
out["V7_RECORD"] = metrics(build_ledger(w7))
out["A4_ZERO_RENORM"] = metrics(build_ledger(w7, start_switch=TRAIL2Y))
out["V8GOV_18SLV"] = metrics(build_ledger(w8))

j = pd.concat([build_ledger(w7).rename("sim"), net_committed.rename("c")], axis=1, join="inner")
out["V7_RECORD"]["recon_vs_committed"] = float((j.sim - j.c).abs().max())

df = pd.DataFrame(out).T
df.to_csv(os.path.join(OD, "V8GOV_EVAL_2026-09-30.csv"))
import sys
for idx, r in df.iterrows():
    sys.stdout.write("%-14s fullSR=%7.4f oosSR=%7.4f fullAnn=%7.3f oosAnn=%7.3f t2ySR=%7.4f t2yAnn=%7.3f DD=%7.3f H1=%6.2f H2=%6.2f negYr=%d/%d\n" %
                     (idx, r.full_sr, r.oos_sr, r.full_ann, r.oos_ann, r.trail2y_sr, r.trail2y_ann, r.daily_dd, r.h1_sr, r.h2_sr, r.neg_years_full, r.neg_years_oos))
print("\nrecon V7 vs committed ledger:", out["V7_RECORD"]["recon_vs_committed"])

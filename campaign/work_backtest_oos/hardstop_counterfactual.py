#!/usr/bin/env python3
"""HARD-STOP GOVERNANCE COUNTERFACTUAL v2 (2026-09-30) — decision-grade evidence for the
standing V7 governance question: the decay monitor's 2 HARD stops
(FXD1_KRWTRI w 3.0% trail2y -0.52; crossasset_rev_L8 w 8.9% trail2y -0.10).

v2 CORRECTION: v1 simulated on a monthly panel; the committed ledger is DAILY with
drifted-weight monthly-rebalance trade costs (rebuild_v7_ledger.py). v2 replicates
that convention EXACTLY so A0 reconciles with the committed ledger (~1e-12 expected
on the overlap where sleeve files are unchanged), and every arm is a full daily ledger.

PRE-REGISTERED ARMS (unchanged from v1 charter, fixed BEFORE measurement):
  A0 BASELINE   : V7 as committed (weights of record) — control; must recon vs ledger.
  A1 DROP-BOTH  : remove both HARD-stop sleeves, renormalize remaining 18 to sum 1.
  A2 DROP-KRW   : remove FXD1_KRWTRI only, renormalize 19.
  A3 DROP-XREV  : remove crossasset_rev_L8 only, renormalize 19.
  A4 ZERO-2Y    : baseline weights until 2024-09-30; from 2024-10-01 (pre-committed
                  trail2y window start) zero both HARD-stop sleeves + renormalize —
                  the "monitor obeyed on day one" arm.

CONVENTIONS (copied from rebuild_v7_ledger.py — NOT re-derived):
  daily sleeve panel 2009-01+, fillna(0); monthly rebalance to STATIC target w;
  trade cost 6.4bp x |static target - drifted position| at each rebalance;
  daily mark = LEV x w_static x daily ret; margin cost (LEV-1)x5.3%/252 daily;
  position drifts with returns. LEV=1.6.
Metrics: monthly SR, arithmetic ann, daily MaxDD, neg years; OOS = >= 2017-01;
trail2y reporting slice >= 2024-10-01. HONESTY: evidence only, changes nothing.
"""
import os, json
import numpy as np
import pandas as pd

B = "/Users/daxu/software/world-trader/campaign"
OD = os.path.join(B, "work_backtest_oos")
LEV = 1.6
CALL = 0.053
COST = 6.4  # bps per side
IS_END = pd.Timestamp("2017-01-01")
TRAIL2Y = pd.Timestamp("2024-10-01")

w_df = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)
sleeves = list(w_df.index)
w = w_df["w"].astype(float)


def load(rel):
    d = pd.read_csv(os.path.join(B, rel), index_col=0)
    d.index = pd.to_datetime(d.index)
    c = "ret" if "ret" in d.columns else d.columns[0]
    return d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()


daily = pd.DataFrame({s: load(s) for s in sleeves})
daily = daily[~daily.index.duplicated(keep="last")].sort_index()
panel = daily[daily.index >= "2009-01-01"].fillna(0.0)
dates = panel.index

KRW = [s for s in sleeves if "FXD1_KRWTRI" in s][0]
XREV = [s for s in sleeves if "crossasset_rev_L8" in s][0]

a1 = w.drop([KRW, XREV]); A1 = a1 / a1.sum()
a2 = w.drop(KRW);         A2 = a2 / a2.sum()
a3 = w.drop(XREV);        A3 = a3 / a3.sum()
w4 = w.copy(); w4[KRW] = 0.0; w4[XREV] = 0.0
A4_POST = w4 / w4.sum()


def build_ledger(target_fn):
    """target_fn(date) -> static target weight Series for that date.
    Replicates rebuild_v7_ledger.py exactly. Returns daily net return Series."""
    net = pd.Series(0.0, index=dates)
    wl = None
    prev = None
    for d in dates:
        target = target_fn(d)
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
    oos_years = yrs[yrs.index >= 2017]
    return {
        "full_sr": round(float(net_m.mean() / net_m.std() * np.sqrt(12)), 4),
        "oos_sr": round(float(oos.mean() / oos.std() * np.sqrt(12)), 4),
        "full_ann": round(float(net_m.mean() * 12 * 100), 3),
        "oos_ann": round(float(oos.mean() * 12 * 100), 3),
        "trail2y_sr": round(float(t2y.mean() / t2y.std() * np.sqrt(12)), 4),
        "trail2y_ann": round(float(t2y.mean() * 12 * 100), 3),
        "daily_dd": round(float(dd * 100), 3),
        "neg_years_full": int((yrs < 0).sum()),
        "neg_years_oos": int((oos_years < 0).sum()),
        "n_days": int(len(net_d)),
    }


led = pd.read_csv(os.path.join(OD, "OPT_20V7_FULL_LEDGER.csv"), parse_dates=["date"])
g = led.groupby("date")[["pnl", "cost"]].sum().sort_index()
net_committed = (g.pnl - g.cost).sort_index()

out = {}
nets = {}
nets["A0_BASELINE"] = build_ledger(lambda d: w)
nets["A1_DROP_BOTH"] = build_ledger(lambda d: A1)
nets["A2_DROP_KRW"] = build_ledger(lambda d: A2)
nets["A3_DROP_XREV"] = build_ledger(lambda d: A3)
nets["A4_ZERO_FROM_2024-10"] = build_ledger(lambda d: (w if d < TRAIL2Y else A4_POST))

for name, net in nets.items():
    out[name] = metrics(net)

# A0 recon vs committed ledger (daily granularity both sides)
j = pd.concat([nets["A0_BASELINE"].rename("sim"), net_committed.rename("com")], axis=1, join="inner")
out["A0_BASELINE"]["recon_maxdev_vs_committed"] = float((j.sim - j.com).abs().max())

print(json.dumps(out, indent=1))
pd.DataFrame(out).T.to_csv(os.path.join(OD, "HARDSTOP_COUNTERFACTUAL_2026-09-30.csv"))
print("\nwritten: HARDSTOP_COUNTERFACTUAL_2026-09-30.csv (v2 daily-ledger conventions)")

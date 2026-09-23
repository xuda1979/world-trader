#!/usr/bin/env python3
"""REBUILD V7 FULL LEDGER from current sleeve files (2026-09-23).

CONTEXT: OPT_20V7_FULL_LEDGER.csv was frozen 2026-09-21. Four sleeves were refreshed
afterwards (crossasset_rev_L8 revised 8/4-8/13 + extended to 9/22; a6_r2_pair_residmom
appended 7/1-7/31; calendar_vixterm_* extended), so reproduce_v7.py's ledger recon
(marks == 1.6 x gross) broke in 2026 (max 2.5e-3) and OOS SR drifted 4.0983 -> 4.0931.
The refresh is byte-reproducible from generator scripts (verified separately), so the
correct action is to REBUILD the ledger on refreshed data — not to revert data.

CONVENTIONS (reverse-engineered from the committed ledger, verified exact on all 3,845
trade rows / 96,580 mark rows given build-time data):
  mark:    one row per sleeve per union-date d: pnl = 1.6 * w * ret_s(d), ret=0 if absent.
  trade:   on the first union-date of each month (and inception): qty = |w - w_live|,
           cost = qty * 6.4e-4 (one side, first leg; inception qty = w).
           w_live drifts WITHIN the month as raw NAV: w_live_i(t) = w_live_i(t-1)*(1+ret_i(t)),
           NO portfolio renormalization; reset to target at each trade date.
  margin:  one row per union-date: cost = (1.6-1)*0.053/252, pnl = 0.
Union-date calendar = sorted union of all 20 sleeve file dates from 2009-01-01.

Usage: python3 rebuild_v7_ledger.py [--check]
  --check: verify against the COMMITTED ledger on the pre-refresh overlap and exit
           without writing (recon must match to 1e-12 on all rows where the underlying
           sleeve data is unchanged).
"""
import os, sys, argparse
import numpy as np
import pandas as pd

B = "/Users/daxu/software/world-trader/campaign"
OD = os.path.join(B, "work_backtest_oos")
LEV, CALL, COST = 1.6, 0.053, 6.4
START = "2009-01-01"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", default=os.path.join(OD, "OPT_20V7_FULL_LEDGER.csv"))
    a = ap.parse_args()

    w_df = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)
    sleeves = list(w_df.index)
    w = w_df["w"]

    series = {}
    for s in sleeves:
        d = pd.read_csv(os.path.join(B, s), index_col=0)
        d.index = pd.to_datetime(d.index)
        c = "ret" if "ret" in d.columns else d.columns[0]
        series[s] = d[c].astype(float).replace([np.inf, -np.inf], np.nan).dropna()

    union = None
    for s in sleeves:
        i = series[s].index[series[s].index >= START]
        union = i if union is None else union.union(i)
    dates = pd.DatetimeIndex(union)
    panel = pd.DataFrame({s: series[s].reindex(dates) for s in sleeves}).fillna(0.0)

    rows = []
    wl = None
    prev = None
    for d in dates:
        m = (d.month, d.year)
        if wl is None or m != prev:
            if wl is None:  # inception: full deployment
                wl = pd.Series({s: w[s] for s in sleeves})
                for s in sleeves:
                    rows.append((d, "trade", os.path.basename(s), 0.0, float(w[s]) * COST / 1e4))
            else:
                for s in sleeves:
                    qty = abs(float(w[s]) - float(wl[s]))
                    if qty > 0:
                        rows.append((d, "trade", os.path.basename(s), 0.0, qty * COST / 1e4))
                wl = pd.Series({s: float(w[s]) for s in sleeves})
            prev = m
        for s in sleeves:
            rows.append((d, "mark", os.path.basename(s), float(LEV * w[s] * panel.loc[d, s]), 0.0))
        rows.append((d, "margin", "GLOBAL-MARGIN", 0.0, (LEV - 1.0) * CALL / 252))
        wl = wl * (1.0 + panel.loc[d])

    led = pd.DataFrame(rows, columns=["date", "component", "sleeve", "pnl", "cost"])
    led = led.sort_values(["date", "component", "sleeve"], kind="stable").reset_index(drop=True)

    if a.check:
        old = pd.read_csv(os.path.join(OD, "OPT_20V7_FULL_LEDGER.csv"), parse_dates=["date"])
        o = old.set_index(["date", "component", "sleeve"])
        n = led.set_index(["date", "component", "sleeve"])
        common = o.index.intersection(n.index)
        # compare only rows whose date is inside the pre-refresh window (<= 2026-06-30)
        cm = common[common.get_level_values(0) <= "2026-06-30"]
        do = o.loc[cm]; dn = n.loc[cm]
        dev = (do["pnl"] - dn["pnl"]).abs().max(), (do["cost"] - dn["cost"]).abs().max()
        print(f"check: {len(cm)} common rows <=2026-06-30; max|dpnl|={dev[0]:.2e} max|dcost|={dev[1]:.2e}")
        print("CHECK", "PASS" if dev[0] < 1e-12 and dev[1] < 1e-12 else "FAIL")
        return 0 if dev[0] < 1e-12 and dev[1] < 1e-12 else 1

    led.to_csv(a.out, index=False)
    marks = led[led.component == "mark"].groupby("date")["pnl"].sum()
    gross = panel[sleeves].dot(w).reindex(marks.index)
    recon = (marks - LEV * gross).abs().max()
    print(f"wrote {a.out}: {len(led)} rows | recon marks vs 1.6x gross: {recon:.2e}")
    net_d = marks - led[led.component != "mark"].groupby("date")["cost"].sum().reindex(marks.index).fillna(0)
    net_m = (1 + net_d).resample("ME").prod() - 1
    oos = net_m[net_m.index >= "2017-01-01"]
    ann = oos.mean() * 12 * 100
    srm = oos.mean() / oos.std() * np.sqrt(12)
    dd = ((1 + net_d).cumprod() / (1 + net_d).cumprod().cummax() - 1).min() * 100
    yrs = (1 + net_m).groupby(net_m.index.year).prod() - 1
    print(f"ledger OOS (arith): ann={ann:.2f}%  monthlySR={srm:.2f}  dailyDD={dd:.2f}%  negYrs={int((yrs<0).sum())}/{len(yrs)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())

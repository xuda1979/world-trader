#!/usr/bin/env python3
"""REBUILD V7.1 FULL LEDGER (2026-09-29, HARD-STOP act session).

V7.1 = V7.0 weights until 2024-09-30, then the A4 zero+renorm vector (2 decay-monitor
HARD stops zeroed, survivors renormalized by 1/0.880835). Engine identical to
rebuild_v7_ledger.py (monthly rebalance, static-weight marks, 6.4bp/side, margin
(LEV-1)*CALL/252) with a weight-switch date. Cross-checks the A4_ZERO_RENORM row of
V8GOV_EVAL_2026-09-30.csv (net-series metrics to 4dp) and HARDSTOP_COUNTERFACTUAL's
A4 row (same conventions).
"""
import os, sys, argparse
import numpy as np
import pandas as pd

_SD = os.path.dirname(os.path.abspath(__file__))
B = os.path.dirname(_SD)
OD = _SD
LEV = 1.6
CALL = 0.053
COST = 6.4
START = "2009-01-01"
SWITCH = pd.Timestamp("2024-10-01")
IS_END = pd.Timestamp("2017-01-01")
TRAIL2Y = pd.Timestamp("2024-10-01")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(OD, "OPT_20V71_FULL_LEDGER.csv"))
    a = ap.parse_args()

    w7 = pd.read_csv(os.path.join(OD, "OPT_20V7_weights.csv"), index_col=0)["w"].astype(float)
    w71 = pd.read_csv(os.path.join(OD, "OPT_20V71_weights.csv"), index_col=0)["w"].astype(float)
    sleeves = list(w71.index)
    assert list(w7.index) == sleeves

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
        target = w7 if d < SWITCH else w71
        m = (d.month, d.year)
        if wl is None or m != prev:
            if wl is None:  # inception: full deployment
                wl = pd.Series({s: target[s] for s in sleeves})
                for s in sleeves:
                    rows.append((d, "trade", os.path.basename(s), 0.0, float(target[s]) * COST / 1e4))
            else:
                for s in sleeves:
                    qty = abs(float(target[s]) - float(wl[s]))
                    if qty > 0:
                        rows.append((d, "trade", os.path.basename(s), 0.0, qty * COST / 1e4))
                wl = pd.Series({s: float(target[s]) for s in sleeves})
            prev = m
        for s in sleeves:
            rows.append((d, "mark", os.path.basename(s), float(LEV * target[s] * panel.loc[d, s]), 0.0))
        rows.append((d, "margin", "GLOBAL-MARGIN", 0.0, (LEV - 1.0) * CALL / 252))
        wl = wl * (1.0 + panel.loc[d])

    led = pd.DataFrame(rows, columns=["date", "component", "sleeve", "pnl", "cost"])
    led = led.sort_values(["date", "component", "sleeve"], kind="stable").reset_index(drop=True)
    led.to_csv(a.out, index=False)

    marks = led[led.component == "mark"].groupby("date")["pnl"].sum()
    costs = led[led.component != "mark"].groupby("date")["cost"].sum().reindex(marks.index).fillna(0)
    net_d = (marks - costs).sort_index()
    net_m = (1 + net_d).resample("ME").prod() - 1

    def srm(x):
        x = x.dropna()
        return x.mean() / x.std() * np.sqrt(12)

    oos = net_m[net_m.index >= IS_END]
    t2y = net_m[net_m.index >= TRAIL2Y]
    dd = ((1 + net_d).cumprod() / (1 + net_d).cumprod().cummax() - 1).min() * 100
    yrs = net_m.groupby(net_m.index.year).sum()

    print(f"wrote {a.out}: {len(led)} rows")
    print(f"full SR={srm(net_m):.4f}  OOS SR={srm(oos):.4f}  t2y SR={srm(t2y):.4f}")
    print(f"full ann={net_m.mean()*12*100:.3f}%  OOS ann={oos.mean()*12*100:.3f}%  t2y ann={t2y.mean()*12*100:.3f}%")
    print(f"daily DD={dd:.3f}%  negYrs full/OOS={int((yrs<0).sum())}/{int((yrs[yrs.index>=2017]<0).sum())}")

    # cross-check vs committed A4 row of V8GOV_EVAL (net-series engine, 4dp)
    ev = pd.read_csv(os.path.join(OD, "V8GOV_EVAL_2026-09-30.csv"), index_col=0)
    a4 = ev.loc["A4_ZERO_RENORM"]
    checks = [
        ("full_sr", srm(net_m)), ("oos_sr", srm(oos)),
        ("full_ann", net_m.mean()*12*100), ("oos_ann", oos.mean()*12*100),
        ("trail2y_sr", srm(t2y)), ("trail2y_ann", t2y.mean()*12*100),
        ("daily_dd", dd),
    ]
    mx = 0.0
    for k, got in checks:
        want = float(a4[k])
        dev = abs(got - want)
        mx = max(mx, dev)
        print(f"  xcheck {k:12s} ledger={got:10.4f} eval={want:10.4f} |d|={dev:.2e}")
    print("XCHECK", "PASS" if mx < 5e-4 else "FAIL", f"(max|d|={mx:.2e})")
    return 0 if mx < 5e-4 else 1


if __name__ == "__main__":
    sys.exit(main())

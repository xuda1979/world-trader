import numpy as np, pandas as pd, json
from e5lib import *

CFGS = {"SAFE": (0.065, 0.04), "BALANCED": None, "AGGRESSIVE": (0.08, 0.03)}

print("=" * 90)
print("TASK 2: SUB-PERIOD DD AUDIT  (BALANCED headline; flag < -8%)")
print("=" * 90)
# get balanced series
rA, sA, uA = construct20(0.065, 0.04)
rB, sB, uB = construct20(0.08, 0.03)
BAL = ((rA + rB) / 2).dropna()
series = {"SAFE": rA, "BALANCED": BAL, "AGGRESSIVE": rB}

# 8 non-overlapping 3y windows 2007->2026 (7.65y remainder folded into last two)
win_bounds = [("2007-01-01","2009-12-31"),("2010-01-01","2012-12-31"),
              ("2013-01-01","2015-12-31"),("2016-01-01","2018-12-31"),
              ("2019-01-01","2021-12-31"),("2022-01-01","2024-12-31"),
              ("2025-01-01","2026-08-28")]
print("\n-- fixed windows (7 x ~3y) --")
for name, r in series.items():
    dds = [maxdd_in(r, a, b) for a, b in win_bounds]
    worst = min(dds)
    print(f"{name:10s} " + " ".join(f"{d*100:6.1f}" for d in dds) + f"  worst={worst*100:.1f}  FLAG={'YES' if worst < -0.08 else 'no'}")
print("cols:", [a[:4] for a, b in win_bounds])

print("\n-- all rolling 3-year windows (daily step), worst per series --")
for name, r in series.items():
    eq = (1 + r).cumprod()
    dd = eq / eq.cummax() - 1
    worst3, wdate = 0.0, None
    for i in range(756, len(r)):
        w = dd.iloc[i-756:i+1].min()
        if w < worst3: worst3, wdate = w, r.index[i]
    print(f"{name:10s} worst rolling-3y DD = {worst3*100:.1f}%  (trough {wdate.date()})  FLAG={'YES' if worst3 < -0.08 else 'no'}")

print("\n-- calendar years (21): ann return / max DD --")
for name in ["BALANCED"]:
    r = series[name]
    yr = yearly(r)
    print(f"{name}: yearly ret:", " ".join(f"{y}:{v*100:.1f}" for y, v in yr.items()))
    neg = [(y, v) for y, v in yr.items() if v < 0]
    print(f"  neg years: {len(neg)} {neg}")
    dd = dd_series(r)
    ydd = dd.groupby(dd.index.year).min()
    print(f"  yearly maxDD:", " ".join(f"{y}:{v*100:.1f}" for y, v in ydd.items()))
    flags = [(y, v) for y, v in ydd.items() if v < -0.08]
    print(f"  years with intra-yr DD < -8%: {len(flags)} {flags}")
# all three: flag count
for name, r in series.items():
    dd = dd_series(r)
    ydd = dd.groupby(dd.index.year).min()
    flags = [(y, round(v*100,1)) for y, v in ydd.items() if v < -0.08]
    print(f"{name}: years DD<-8%: {len(flags)} {flags}")

print("\n" + "=" * 90)
print("TASK 3: COST STRESS 6 / 8 / 10 bps per side")
print("=" * 90)
rows = {}
for name, (tgt, thr) in [("SAFE", (0.065, 0.04)), ("AGGRESSIVE", (0.08, 0.03))]:
    for c in (6, 8, 10):
        r, _, _ = construct20(tgt, thr, cost_bps=c)
        rows[(name, c)] = stats(r)
        print(f"{name:10s} {c:2d}bps: {rows[(name,c)]}")
for c in (6, 8, 10):
    rA2, _, _ = construct20(0.065, 0.04, cost_bps=c)
    rB2, _, _ = construct20(0.08, 0.03, cost_bps=c)
    b2 = ((rA2 + rB2) / 2).dropna()
    rows[("BALANCED", c)] = stats(b2)
    print(f"{'BALANCED':10s} {c:2d}bps: {rows[('BALANCED', c)]}")
json.dump({f"{k[0]}_{k[1]}": v for k, v in rows.items()},
          open("/Users/daxu/software/world-trader/campaign/agents/E5_champ20y/work/t3_cost.json", "w"), indent=1, default=float)

#!/usr/bin/env python3
"""Pin the coordinator's exact w=0.25 blend convention (target dSR +0.199 / dAnn +4.21 / dMDD +0.05)."""
import numpy as np, pandas as pd, itertools, json
ROOT = "/Users/daxu/software/world-trader"
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0].astype(float)
hb = pd.read_csv(f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
                 index_col=0)
hb.index = pd.to_datetime(hb.index); hb = hb.iloc[:, 0].astype(float)
print('champ dtype:', champ.dtype)

sr = lambda x: x.mean()/x.std(ddof=1)*np.sqrt(252)
def stats(r):
    r = r.dropna()
    return {"sr": sr(r),
            "ann_cagr": float(((1+r).prod()**(252/len(r))-1)*100),
            "ann_arith": float(r.mean()*252*100),
            "mdd": float(((1+r).cumprod()/(1+r).cumprod().cummax()-1).min())*100}

res = []
aligns = {"inner": None, "fill0": "f"}
weights = {"0.25": (0.75, 0.25), "additive": (1.0, 0.25)}
vt = {False: 1.0, True: None}
witems = [("scaling", 0.75, 0.25), ("additive", 1.0, 0.25)]
for al, (wname, wc, wh), volmatch, metric in itertools.product(
        ["inner", "fill0"], witems, [False, True], ["ann_cagr", "ann_arith"]):
    if al == "inner":
        j = pd.concat([champ.rename("c"), hb.rename("h")], axis=1, join="inner").dropna()
        c, h = j.c, j.h
    else:
        idx = champ.index
        c = champ
        h = hb.reindex(idx).fillna(0.0)
    s13 = stats(c)
    scale = (c.std(ddof=1)*np.sqrt(252))/(h[h != 0].std(ddof=1)*np.sqrt(252)) if volmatch else 1.0
    bl = wc*c + wh*scale*h
    s = stats(bl)
    res.append({"align": al, "w": wname,
                "volmatch": volmatch, "metric": metric,
                "dSR": s["sr"]-s13["sr"], "dAnn": s[metric]-s13[metric], "dMDD": s["mdd"]-s13["mdd"]})
tgt = {"dSR": 0.199, "dAnn": 4.21, "dMDD": 0.05}
best = min(res, key=lambda r: abs(r["dSR"]-tgt["dSR"])+abs(r["dAnn"]-tgt["dAnn"])*0.05+abs(r["dMDD"]-tgt["dMDD"]))
for r in sorted(res, key=lambda r: abs(r["dSR"]-tgt["dSR"])):
    tag = " <== CLOSEST" if r is best else ""
    print(f"{r['align']:6s} {r['w']:10s} vt={int(r['volmatch'])} {r['metric']:9s} dSR {r['dSR']:+.4f} dAnn {r['dAnn']:+.4f} dMDD {r['dMDD']:+.4f}{tag}")
print(f"target: dSR {tgt['dSR']} dAnn {tgt['dAnn']} dMDD {tgt['dMDD']}")

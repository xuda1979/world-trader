#!/usr/bin/env python3
"""R6 probe: reconcile coordinator blend arithmetic (dSR +0.199 / dAnn +4.21 / dMDD +0.05
@ w=0.25 fill-0) and CFX4 zero-weight wide14 NaN. Own algebra."""
import numpy as np, pandas as pd, json
ROOT = "/Users/daxu/software/world-trader"
champ = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv",
                    index_col=0, parse_dates=True).iloc[:, 0]
hb = pd.read_csv(f"{ROOT}/campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv",
                 index_col=0)
hb.index = pd.to_datetime(hb.index)
hb = hb.iloc[:, 0].astype(float).dropna()
print(f"hobr raw file rows={len(pd.read_csv(f'{ROOT}/campaign/team/agents/RES_BASIS/sleeves/RB_hobr_crack_hyst_w63_z10_zo10.csv'))} dropna={len(hb)} {hb.index[0].date()}..{hb.index[-1].date()}")

j = pd.concat([champ.rename("c"), hb.rename("h")], axis=1, join="inner").dropna()
sr = lambda x: x.mean()/x.std(ddof=1)*np.sqrt(252)
s13 = sr(j.c)
stats = lambda r: dict(sr=sr(r), ann=float(((1+r).prod()**(252/len(r))-1)*100),
                       mdd=float(((1+r).cumprod()/(1+r).cumprod().cummax()-1).min())*100)

# CFX4 zero-weight check
import sys; sys.path.insert(0, f"{ROOT}/campaign/agents/chief/coord/AUDIT_RECON/r6")
wcsv = pd.read_csv(f"{ROOT}/campaign/results/RAWEW14_HOBR_CANDIDATE_weights.csv", index_col=0).iloc[:,0]
print(f"CFX4 relw={wcsv.get('CFX4')}  RB_hobr relw={wcsv.get('RB_hobr')}")

# A. additive overlay convention: c + w*h (gross 1.6 + 1.6*w*share... no rescale)
out = {}
for w in [0.25]:
    bl = j.c + w*j.h
    s = stats(bl)
    out[f"additive_w{w}"] = {"dSR": s["sr"]-s13, "dAnn": s["ann"]-stats(j.c)["ann"],
                             "dMDD": s["mdd"]-stats(j.c)["mdd"]}
# B. scaling blend (mine): (1-w)c + w*h
for w in [0.25]:
    bl = (1-w)*j.c + w*j.h
    s = stats(bl)
    out[f"scale_w{w}"] = {"dSR": s["sr"]-s13, "dAnn": s["ann"]-stats(j.c)["ann"],
                          "dMDD": s["mdd"]-stats(j.c)["mdd"]}
# C. additive with vol-targeted hobr at champion vol
sc = j.c.std(ddof=1)*np.sqrt(252) / (j.h.std(ddof=1)*np.sqrt(252))
for w in [0.25]:
    bl = j.c + w*sc*j.h
    s = stats(bl)
    out[f"additive_vt_w{w}"] = {"scale": sc, "dSR": s["sr"]-s13,
                                "dAnn": s["ann"]-stats(j.c)["ann"], "dMDD": s["mdd"]-stats(j.c)["mdd"]}
# D. halves at alternative splits (raw sleeve)
for lbl, m in [("2017-01-01", j.index < pd.Timestamp("2017-01-01")),
               ("idx-mid", j.index < j.index[len(j)//2])]:
    print(f"hobr halves @{lbl}: H1 {sr(j.h[m]):.4f} H2 {sr(j.h[~m]):.4f} split {j.index[len(j)//2].date() if lbl=='idx-mid' else '2017-01-01'}")
print(f"hobr IS/OOS @2017: IS {sr(j.h[j.h.index<pd.Timestamp('2017-01-01')]):.4f} OOS {sr(j.h[j.h.index>=pd.Timestamp('2017-01-01')]):.4f}")
print(f"target: coordinator preamble halves H1 2.182 H2 0.753, IS/OOS 2.145/0.807; blend dSR +0.199 dAnn +4.21 dMDD +0.05")
print(json.dumps(out, indent=1, default=float))

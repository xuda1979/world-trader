#!/usr/bin/env python3
"""G1: left-tail / risk-on-off overlay CANDIDATE scan.
Signals measurable at close t -> position t+1 (T+1). Overlays on HONEST11 blend gross.
All: 6bps/side on turnover; trailing vol scale (min 60d, shift1, clip 2).
Family:
  A) risk-on/off binary: VIX 21d z vs 252d mean/std, hysteresis (calm 1 / stressed 0)
  B) downside-trend gate: SPY 21d return < th -> cut to floor
  C) VIX-level de-risk: pos = 1 - w*(VIX-Vlo)/(Vhi-Vlo) clipped
  D) vol-of-vol / VIX spike shock exit
Outputs grid CSV + top by combined objective (ann, mdd).
"""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, ROOT
from overlay_lib import build_overlay, data_vix, data_spx, hysteresis_pos, maxdd_pct, dd_profile
import honest11_build as H

Vn, blend, Sn = honest11_blend()   # gross EW blend (mean of vt10 sleeve returns)
vix = data_vix(); spy = data_spx()
BASE_START = "2008-09-01"

rows = []
def score(tag, pos):
    net, posf = build_overlay(pos, blend)
    net = net[net.index >= BASE_START]
    s_ = H.stats_r(net) if hasattr(H, "stats_r") else None
    from ht_lib import stats_r
    s = stats_r(net)
    rows.append(dict(tag=tag, n=s["n"], ann=s["ann_geo"], srd=s["sr_d"], srm=s["sr_m"],
                     mdd=s["mdd"], w3=dd_profile(net)["w3"], negyr=s["negyr"], worst=s["worst"],
                     turn=posf.diff().abs().mean()*252))
    return rows[-1]

# A) VIX z risk-on/off with hysteresis
for smooth in (1, 5, 21):
    v = vix.rolling(smooth).mean()
    m = v.rolling(252).mean(); sd = v.rolling(252).std()
    z = ((v - m)/sd).reindex(blend.index).ffill()
    for th in (-0.25, 0.0, 0.25, 0.5, 0.75, 1.0):
        for hyst in (0.0, 0.1, 0.25):
            p = hysteresis_pos(z, th, hyst)
            score(f"A_z_sm{smooth}_th{th}_h{hyst}", p)

# B) SPY downside trend gate: 21d / 63d return thresholds
for lb in (21, 42, 63):
    mom = spy.rolling(lb).apply(lambda x: (1+x).prod()-1, raw=True)
    mom = mom.reindex(blend.index)
    for th in (-0.05, -0.08, -0.10, -0.15):
        pos = (mom > th).astype(float)   # 1 unless deep drawdown
        pos[ (mom*0).index.isin([]) ] = pos
        score(f"B_mom{lb}_th{th}", pos)
    # continuous: pos = 1 + mom/th clipped [0.3,1]
    for th in (-0.10, -0.15):
        posc = (1 + mom/th).clip(0.3, 1.0).fillna(1.0)
        score(f"Bc_mom{lb}_th{th}", posc)

# C) VIX-level continuous de-risk
for vlo, vhi in ((15, 25), (18, 30), (20, 35), (16, 28)):
    vv = vix.reindex(blend.index).ffill()
    pos = (1 - 1.0*(vv - vlo)/(vhi - vlo)).clip(0.3, 1.0).fillna(1.0)
    score(f"C_vix_{vlo}_{vhi}", pos)

# D) VIX spike shock: 5d VIX change > +30% => out until z back
dv5 = vix.pct_change(5).reindex(blend.index).ffill()
for th in (0.3, 0.4, 0.5):
    pos = (dv5 < th).astype(float).fillna(1.0)
    score(f"D_dv5_{th}", pos)

df = pd.DataFrame(rows).sort_values("mdd", ascending=False)
df.to_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_TAIL/logs/g1_grid.csv", index=False)
print(df.sort_values(["mdd"], ascending=False).head(20).to_string())
print("--- top by mdd (least negative) ---")
print(df.nlargest(8, "mdd").to_string())
print("--- candidates: mdd>-4.2 & ann>45 ---")
print(df[(df.mdd > -4.2) & (df.ann > 45)].to_string())

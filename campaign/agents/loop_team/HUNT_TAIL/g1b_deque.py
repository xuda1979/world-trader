#!/usr/bin/env python3
"""G1b: rolling-window (Deque) conditional tail overlay + combined signals.
pos(t) in [0.25, 1] multiplicative derisk of the blend, from:
  - rolling min/max VIX z (Deque z252),
  - SPY rolling-window return (31/63d) mapped continuously,
  - combo: avg of the two.
Also: overlay of blend DRAWDOWN itself (throttle exists; try deeper frac).
T+1: every signal series shift(1) inside build_overlay."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, stats_r, ROOT
from overlay_lib import build_overlay, data_vix, data_spx, dd_profile
import honest11_build as H

Vn, blend, Sn = honest11_blend()
vix = data_vix(); spy = data_spx()
BASE_START = "2008-09-01"
rows = []
def score(tag, pos):
    net, posf = build_overlay(pos, blend)
    net = net[net.index >= BASE_START]
    s = stats_r(net)
    rows.append(dict(tag=tag, n=s["n"], ann=s["ann_geo"], srd=s["sr_d"], srm=s["sr_m"],
                     mdd=s["mdd"], w3=dd_profile(net)["w3"], negyr=s["negyr"], worst=s["worst"]))
    return rows[-1]

# rolling min VIX (Deque)
for lb in (63, 126, 252):
    vmin = vix.rolling(lb).min().reindex(blend.index).ffill()
    vv = vix.reindex(blend.index).ffill()
    z = ((vv - vmin) / vmin)  # 0 = at rolling min (euphoria), big = stress
    for th in (0.25, 0.35, 0.5):
        pos = (1 - (z/th).clip(0, 0.75)).fillna(1.0)   # down to 0.25 at stress
        score(f"DQ_min{lb}_th{th}", pos)
        pos2 = (z < th).astype(float).fillna(1.0)
        score(f"DQb_min{lb}_th{th}", pos2)

# continuous SPY rolling return map (smoother than Bc)
for lb in (31, 63):
    mom = spy.rolling(lb).apply(lambda x: (1+x).prod()-1, raw=True).reindex(blend.index)
    for floor, th in ((0.5,-0.08),(0.5,-0.12),(0.25,-0.12),(0.75,-0.08),(0.5,-0.05)):
        pos = (1 + mom/th*(1-floor)).clip(floor, 1.0).fillna(1.0)
        score(f"CC_mom{lb}_f{floor}_th{th}", pos)

# combo: average of DQ_min252 and CC_mom63
vmin252 = vix.rolling(252).min().reindex(blend.index).ffill()
vv = vix.reindex(blend.index).ffill()
zq = ((vv - vmin252)/vmin252)
mom63 = spy.rolling(63).apply(lambda x: (1+x).prod()-1, raw=True).reindex(blend.index)
p1 = (1 - (zq/0.35).clip(0, 0.75)).fillna(1.0)
p2 = (1 + mom63/-0.08*0.5).clip(0.5, 1.0).fillna(1.0)
for w in (0.5, 0.3, 0.7):
    score(f"COMBO_w{w}", (w*p1 + (1-w)*p2))

df = pd.DataFrame(rows)
df.to_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_TAIL/logs/g1b_grid.csv", index=False)
print(df.sort_values("mdd", ascending=False).head(15).to_string())
print("--- mdd > -4.85 & ann > 47 ---")
print(df[(df.mdd > -4.85) & (df.ann > 47)].to_string())

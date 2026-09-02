#!/usr/bin/env python3
"""G2: standalone (own-book) tail engines, and CRASH-day counterposition tests.
A real standalone must have SR_d>=0.6 full-sample etc. Tail engines typically won't;
measured for the record + corr to blend + crash-day overlay value.
Anti-2008: short SPY when VIX z252 > th (T+1). Tested 2008+, full."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, stats_r, ROOT
from overlay_lib import build_overlay, data_vix, data_spx, hysteresis_pos

Vn, blend, Sn = honest11_blend()
vix = data_vix(); spy = data_spx()
BASE_START = "2008-09-01"

v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std()).reindex(blend.index).ffill()

print("== standalone anti-tail books on blend's calendar (SR full, 2008+) ==")
for th in (0.5, 0.75, 1.0, 1.25):
    pos = -(z > th).astype(float)          # short SPY-blend when VIX stressed
    net, posf = build_overlay(pos, blend)
    net08 = net[net.index >= BASE_START]
    s = stats_r(net08)
    print(f"th={th}: SR_d={s['sr_d']:.2f} ann={s['ann_geo']:.1f}% mdd={s['mdd']:.1f}% negyr={s['negyr']}/{s['nyr']}")

print()
print("== crash-day counterposition: in crash (VIX z>1), go LONG next day (squeeze capture) ==")
for th in (0.75, 1.0, 1.25, 1.5):
    pos = ((z > th).astype(float) - (z <= th).astype(float) * 0.0)  # 1 in crash else 0 (long bias in crash)
    net, posf = build_overlay(pos, blend)
    net08 = net[net.index >= BASE_START]
    s = stats_r(net08)
    print(f"th={th} crashlong: SR_d={s['sr_d']:.2f} ann={s['ann_geo']:.1f}% mdd={s['mdd']:.1f}% negyr={s['negyr']}")

print()
print("== what did the blend do on the worst SPY days (concurrent + next day)? ==")
spyr = spy.reindex(blend.index)
worst = spyr.nsmallest(15)
for d, r in worst.items():
    b0 = blend.get(d, np.nan); b1 = blend.get(blend.index[blend.index.get_loc(d)+1], np.nan) if blend.index.get_loc(d)+1 < len(blend) else np.nan
    print(f"{d.date()} SPY {r*100:5.2f}% | blend_t {b0*100:+6.2f}% blend_t1 {b1*100:+6.2f}%")

#!/usr/bin/env python3
"""G5: vol-of-vol / CRASH-carry sleeves with 2008 start (HT_TAILVOV family).
HT_TAILVOV:  ret = -|dvix| with trailing vt10 (build_overlay) on blend calendar.
Gates per CHARTER (SR>=0.6, halves, negyrs, scramble 200x seed7, flatten, corr<0.15 to L16)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, stats_r, sleeve_gates, corr_to, ROOT
from overlay_lib import build_overlay, data_vix

Vn, blend, Sn = honest11_blend()
vix = data_vix()
l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
BASE_START = "2008-09-01"

dvix = vix.diff()
dvix.loc["2008-11-25":"2009-01-02"] = np.nan  # hole ( honesty)
vov = dvix.rolling(21).std()

def run(tag, pos):
    net, posf = build_overlay(pos, blend)
    net = net[net.index >= BASE_START]
    ok, line, ext = sleeve_gates(net, posf.reindex(net.index), blend, seed=7, nperm=200)
    c, nobs = corr_to(net, l16)
    print(f"[{tag}] {line} corrL16={None if c is None else round(c,3)} => {'PASS' if all(ok.values()) else 'FAIL'}")
    return net

for lb in (10, 21, 63):
    v_ = vov.rolling(lb).mean()
    z = ((v_ - v_.rolling(252).mean())/v_.rolling(252).std()).reindex(blend.index).ffill()
    for th in (0.5, 1.0):
        run(f"HT_TAILVOV_z{lb}_>{th}", -(z > th).astype(float).reindex(blend.index))
    # continuous: pos = -clip(z/2, 0, 1)
    run(f"HT_TAILVOV_c{lb}", (-((z/2.0).clip(0,1))).reindex(blend.index))

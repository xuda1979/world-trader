#!/usr/bin/env python3
"""G4: run the FULL charter gate battery on the TAIL candidate sleeve itself.
Candidate HT_TAILBOOST: pos = 1{vix21 z252 > 1.0} on HONEST11 blend gross (T+1, 6bps,
trailing vt10 clip2). Gates: SR>=0.6, H1/H2>=0.3, <=2 negyrs each>-5%, scramble 200x
p<=0.05, flatten gate (uniqR>=0.08, ac1<0.5), |corr|<0.15 to L16 BAL champion.
Also gate-check VIXTERM (vix/vix3m-1)."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import honest11_blend, stats_r, sleeve_gates, corr_to, ROOT
from overlay_lib import build_overlay, data_vix, data_spx

Vn, blend, Sn = honest11_blend()
BASE_START = "2008-09-01"
l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv",
                  index_col=0, parse_dates=True).iloc[:,0]

vix = data_vix()
v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std())

def run(tag, pos):
    net, posf = build_overlay(pos, blend)
    net = net[net.index >= BASE_START]
    posf = posf.reindex(net.index)
    ok, line, ext = sleeve_gates(net, posf, blend, seed=7, nperm=200)
    c, nobs = corr_to(net, l16)
    ok2 = dict(g=(c is not None and abs(c) < 0.15))
    all_ok = all(ok.values()) and ok2['g']
    print(f"[{tag}] {line} corrL16={c if c is None else round(c,3)}(n={nobs}) corr_gate={ok2['g']} => ALL_GATES={'PASS' if all_ok else 'FAIL'}")
    s = stats_r(net)
    return tag, s, ext['sp'], c

run("HT_TAILBOOST_z>1.0", (z > 1.0).astype(float).reindex(blend.index))
run("HT_TAILBOOST_z>0.75", (z > 0.75).astype(float).reindex(blend.index))

# VIX term structure (vix/vix3m - 1)
v3m = pd.read_csv("/Users/daxu/software/world-trader/alphaportfolio_replication/data/vix3m.csv",
                  index_col=0, parse_dates=True).iloc[:,0]
ts = (vix/v3m.reindex(vix.index) - 1.0)
for th in (0.0, 0.02, 0.05):
    run(f"HT_VIXTERM_ts>{th}", (ts > th).astype(float).reindex(blend.index))
for th in (-0.02, -0.05):
    run(f"HT_VIXTERM_ts<{th}_inv", -(ts < th).astype(float).reindex(blend.index))

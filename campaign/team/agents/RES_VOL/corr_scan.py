#!/usr/bin/env python3
"""RES_VOL R1 step 1: decorrelation-FIRST filter on raw candidate SIGNAL series.

Charter FIRST STEP: corr_gate.py on candidate daily 'ret' streams before any backtest.
Here candidates are the vol STATE series themselves (info streams): if the POSITION series
they generate is highly correlated to the champion book, the blend gate can never pass.
Champion pinned sha 4358dfab95679b97 (fresh, this session).
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/team/agents/RES_VOL")

import numpy as np
import pandas as pd
from bt.gates import corr_to
from lib import corr_gate
from vol_r1 import (load_vol, load_px, realized_vol, vrp_series, slope_series,
                    long_book, slope_book)

champ = pd.read_csv(corr_gate.CHAMP, parse_dates=['date'], index_col='date')['ret'].astype(float)
px_s = load_px('SPY'); px_i = load_px('IWM'); px_u = load_px('USO')
vix = load_vol('VIX'); rvx = load_vol('RVX'); vvix = load_vol('VVIX')
v9 = load_vol('VIX9D'); v3 = load_vol('VIX3M'); v6 = load_vol('VIX6M')

cands = {}
for lb in (10, 21, 63):
    cands[f'vrp_spx_rv{lb}'] = vrp_series(vix, realized_vol(px_s, lb))
    cands[f'vrp_iwm_rv{lb}'] = vrp_series(rvx, realized_vol(px_i, lb))
for c in (10, 21, 63):
    vvc = vvix.rolling(c).mean().shift(1)
    cands[f'vov_{c}'] = (vvix - vvc).dropna()          # vol-of-vol deviation
    cands[f'vovdiv_{c}'] = (vvix / vix - 1).dropna()   # VVIX/VIX ratio deviation
cands['slope9d3m'] = slope_series(v9, v3)
cands['slope3m6m'] = slope_series(v3, v6)
cands['slope9d6m'] = slope_series(v9, v6)
cands['spx_gvz'] = (load_vol('VIX') / load_vol('GVZ')).dropna()
cands['oil_ovx'] = (px_u.pct_change().rolling(21).std() * np.sqrt(252)).dropna()

print(f"{'candidate':<16} {'corr_to_champ':>14} {'|corr|<0.15':>12}  span")
for k, s in cands.items():
    # state->position sign is unknown pre-backtest; corr of the SIGNED stream is directional.
    # Decorrelation-first on position series (sign-invariant proxy): corr of s to champ
    # AND of -s (min-abs rule as in charter).
    c1 = corr_to(champ, s)
    c2 = corr_to(champ, -s)
    c = c1 if abs(c1) <= abs(c2) else c2
    print(f"{k:<16} {c1:+14.4f} {'PASS' if abs(c) < 0.15 else 'FAIL':>12}  "
          f"{s.index[0].date()}..{s.index[-1].date()} n={len(s)}")

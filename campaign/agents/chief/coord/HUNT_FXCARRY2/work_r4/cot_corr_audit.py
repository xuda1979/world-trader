#!/usr/bin/env python3
"""R4 audit helper for DEAD_IDEAS row 56 (HUNT_COT_ITER11).

Verifies the row's central mechanism claim: corr(COT pct_oi WEEKLY CHANGE lagged 1wk,
SAME-period market return) = +0.16..+0.22 is a CONTAMINATION artifact, and the honest
NEXT-week (forward) correlation collapses to ~+0.03.
Uses the exact loaders from the cited script cot_delta_momentum.py (no re-tuning).
"""
import sys
sys.path.insert(0, '/Users/daxu/software/world-trader')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/scripts')
import numpy as np, pandas as pd
import cot_delta_momentum as C

rows = []
for m in C.PRICES:
    px = C.load_price(m)
    cot = C.load_cot(m)
    ret = px.pct_change()
    wret = (ret + 1).resample('W-FRI').prod() - 1
    pos = cot.set_index('date')['net_noncomm_pct_oi']
    posw = pos.resample('W-FRI').apply(lambda x: x.iloc[-1] if len(x) else np.nan).ffill()
    delta = posw.diff(1)
    df = pd.DataFrame({'wret': wret, 'd': delta}).dropna()
    same = df['d'].corr(df['wret'])                       # contaminated: same week
    fwd = df['d'].shift(1).corr(df['wret'])               # honest: delta(t-1) vs ret(t)
    rows.append((m, round(same, 3), round(fwd, 3), len(df)))

out = pd.DataFrame(rows, columns=['market', 'same_period_corr', 'forward_corr', 'n'])
print(out.to_string(index=False))
print(f"\nsame-period corr range: [{out.same_period_corr.min():+0.3f}, {out.same_period_corr.max():+0.3f}]"
      f"  median {out.same_period_corr.median():+0.3f}")
print(f"forward     corr range: [{out.forward_corr.min():+0.3f}, {out.forward_corr.max():+0.3f}]"
      f"  median {out.forward_corr.median():+0.3f}")

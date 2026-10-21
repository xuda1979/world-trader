"""recon3: ramp + throttle overlay variants (last overlay family members)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.metrics import sharpe_d, max_dd, neg_years, half_split
from recon2 import eval_m
import recon1

df = recon1.load(); s = recon1.signals(df)
res = []
z = s.ratio_z.clip(-3, 3)
# linear ramp: m = 1 + z/cap clipped to [0,1]  (MORE champion when slope rich)
for cap in [1.0, 2.0]:
    m = (1 + z / cap).clip(0, 1)
    eval_m(m, df, 'RAMP ratio_z/cap%0.1f (risk-on)' % cap, res)
    eval_m((1 - m), df, 'RAMP ratio_z/cap%0.1f (risk-off)' % cap, res)
# throttle-to-0.5 instead of 0
for thr in [0.5, 1.0]:
    m = pd.Series(1.0, index=z.index); m[z > thr] = 0.5
    eval_m(m, df, 'THROTTLE0.5 ratio_z>%0.1f' % thr, res)
    m2 = pd.Series(1.0, index=z.index); m2[z < -thr] = 0.5
    eval_m(m2, df, 'THROTTLE0.5 ratio_z<-%0.1f' % thr, res)
# 2-day confirmation for the dvxv21 q90 off-gate (whipsaw reduction)
d21 = s.dvxv21
thr = d21.quantile(0.9)
gate = (d21 > thr).rolling(2).min()  # need 2 consecutive days
m = pd.Series(1.0, index=z.index); m[gate == 1] = 0.0
eval_m(m, df, 'OFF dvxv21>q90 2day-conf', res)
# inverted: go OFF when slope collapses (backwardation) — classic defensive read
m3 = pd.Series(1.0, index=z.index); m3[s.slope_z < -1.0] = 0.0
eval_m(m3, df, 'OFF slope_z<-1.0', res)
m4 = pd.Series(1.0, index=z.index); m4[s.slope < 0] = 0.0
eval_m(m4, df, 'OFF slope<0 (backward)', res)
R = pd.DataFrame(res).sort_values('dsr', ascending=False)
print(R.to_string(index=False, float_format=lambda v: '%0.4f' % v))

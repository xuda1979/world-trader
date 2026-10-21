"""recon7: honesty checks — (1) slope_z range (degenerate-gate disclosure),
(2) top real overlays re-charged at gross=1.0 (cheapest honest charge)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_VXV_TERM/scratch')
from bt.metrics import sharpe_d
from recon2 import eval_m
import recon1

df = recon1.load(); s = recon1.signals(df)
print('slope_z  = vxv/vix-1 : min %+.4f max %+.4f  (P(v<-0.5)=%.4f)' % (
    s.slope_z.min(), s.slope_z.max(), (s.slope_z < -0.5).mean()))
print('ratio_z (252d z)     : min %+.3f max %+.3f' % (s.ratio_z.min(), s.ratio_z.max()))
print('contango frac        : %.4f' % s.contango.mean())

res = []
z = s.ratio_z
eval_m((z <= 1.0).astype(float), df, 'OFF ratio_z>1.0 @1x', res, gross=1.0)
eval_m((z <= 1.5).astype(float), df, 'OFF ratio_z>1.5 @1x', res, gross=1.0)
m = pd.Series(1.0, index=z.index); m[z > 1.0] = 0.5
eval_m(m, df, 'THROT0.5 ratio_z>1.0 @1x', res, gross=1.0)
m2 = pd.Series(1.0, index=z.index); m2[z < -1.0] = 0.5
eval_m(m2, df, 'THROT0.5 ratio_z<-1.0 @1x', res, gross=1.0)
d21 = s.dvxv21; thr = d21.quantile(0.9)
gate = (d21 > thr).rolling(2).min()
m3 = pd.Series(1.0, index=z.index); m3[gate == 1] = 0.0
eval_m(m3, df, 'OFF dvxv21>q90 2conf @1x', res, gross=1.0)
print(pd.DataFrame(res).to_string(index=False, float_format=lambda v: '%0.4f' % v))
print('bar: dSR > +0.15 — ALL FAIL even at 1x charge.')

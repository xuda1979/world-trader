"""IDEA 2: Cross-industry DISPERSION timing. Does trailing cross-sectional dispersion of 48
industry returns predict momentum/reversal profitability? Build conditional books."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'/Users/daxu/software/world-trader/campaign/scripts')
from c1_lib import kf48, bt
from c1r2_lib import evaluate, weekly_positions

ind = kf48()
rets = ind.iloc[:, :48]
# dispersion signal (data <= t): std ACROSS industries of trailing Ld returns
for L in [5, 21]:
    disp = rets.pow(2).rolling(L).mean().mean(axis=1).pow(0.5)  # cross-industry avg trailing-L RMS daily ret
    dz = (disp - disp.expanding(252).mean()) / disp.expanding(252).std()

# conditional book: 63d momentum top3-bot3, gated by dispersion tercile (trailing expanding)
mom = rets.rolling(63).sum()
rev = -rets.rolling(5).sum()
def book(sig, k=3):
    r = sig.rank(axis=1)
    n = sig.shape[1]
    w = pd.DataFrame(0.0, index=sig.index, columns=sig.columns)
    w[r > n-k] = 1.0/k
    w[r <= k] = -1.0/k
    return w

# 1) unconditional baselines for reference
for nm, sig in [('mom63', mom), ('rev5', rev)]:
    w = book(sig)
    net, _, _ = bt(weekly_positions(w), rets)
    evaluate(net, f'base {nm} weekly')

# 2) dispersion-conditioned: trade momentum only when disp z<0 (low disp), reversal only z>0
w_mom, w_rev = book(mom), book(rev)
hi = (dz > 0.5).reindex(w_mom.index).fillna(False)
lo = (dz < -0.5).reindex(w_mom.index).fillna(False)
w_cond = w_mom.where(lo, 0.0) + w_rev.where(hi, 0.0)
net, _, _ = bt(weekly_positions(w_cond), rets)
evaluate(net, 'cond mom63/lo-disp + rev5/hi-disp w')

# 3) raw dispersion as market-timing: high disp -> short industries EW? Instead: does disp z
#    predict equal-weight industry return (t+1..t+21)? predictive regression check
ew = rets.mean(axis=1)
fwd21 = ew.rolling(21).sum().shift(-21)
for lag in [0, 1, 5, 21]:
    x = dz.shift(lag)
    df = pd.concat([fwd21.rename('y'), x.rename('x')], axis=1).dropna()
    df = df.loc['2008-09-01':'2026-08-31']
    corr = df['y'].corr(df['x'])
    print(f'  corr(disp_z t-{lag}, fwd21d EW industry ret) 2008+: {corr:+.3f}  (n={len(df)})')

# 4) simple timing book: long EW industries when disp z low, flat/short when high
w_t = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
w_t[:] = 1.0/48
w_lo = w_t.where(dz < 0, -w_t)  # sign flip by disp
for nm, sig in [('longEW if z<0 else shortEW', w_lo)]:
    net, _, _ = bt(sig, rets)
    evaluate(net, nm + ' daily')

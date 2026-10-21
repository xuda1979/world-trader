"""IDEA SLATE step 1: mechanics on the overnight (ON) and intraday (IC) cross-sections.
Signal built from info<=t (yesterday's gap, or trailing mean); position decided at t trades t+1.
Reports gross IC t+1 (Spearman-ish via corr of signal rank vs next-day OVN and CC rets)."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
champ=H.load_champion()
cc=on+ic  # approx close-to-close (exact (1+on)(1+ic)-1; use exact for PnL)
O,C=H.load_panel()
r_cc=C/C.shift(1)-1.0
r_cc=r_cc.where(on.notna())          # same validity mask as on
r_on=on.copy()                        # trade t+1 overnight: pos decided at t close earns open_{t+1}/close_t-1
r_ic=ic.copy()

def fwd_ic(sig, ret, tag):
    """mean cross-sectional corr(sig_t, ret_{t+1}) using rank ranks (info<=t vs t+1 ret)."""
    sr=sig.rank(axis=1)
    rr=ret.shift(-1).rank(axis=1)
    both=sr.notna()&rr.notna()
    cs=pd.Series(index=sig.index,dtype=float)
    for t in sig.index[::5]:   # subsample for speed in exploration
        b=both.loc[t]
        if b.sum()>30:
            cs.loc[t]=sr.loc[t][b].corr(rr.loc[t][b])
    cs=cs.dropna()
    cs=cs[cs.index>=pd.Timestamp('2008-01-01')]
    tstat=cs.mean()/cs.std()*np.sqrt(len(cs))
    print(f"{tag}: meanFwdRankIC {cs.mean():+.5f} t~{tstat:+.1f} n={len(cs)} stdIC {cs.std():.4f} frac>0 {(cs>0).mean():.3f}")
    return cs.mean(), tstat

lb_windows=[1,2,3,5,10,21]
# overnight mean (t-lb..t) vs next-day overnight  (continuation) — sign flip = fade
for lb in lb_windows:
    sig=on.rolling(lb,min_periods=max(1,lb//2)).mean()
    fwd_ic(sig,r_on,f"ON-mom lb{lb} -> ON+1")
    fwd_ic(-sig,r_on,f"ON-fade lb{lb} -> ON+1")
print()
# intraday mean vs next-day intraday
for lb in [1,2,3,5,10,21]:
    sig=ic.rolling(lb,min_periods=max(1,lb//2)).mean()
    fwd_ic(sig,r_ic,f"IC-mom lb{lb} -> IC+1")
    fwd_ic(-sig,r_ic,f"IC-fade lb{lb} -> IC+1")
print()
# overnight signal vs next-day INTRADAY and close-close (cross-regime)
for lb in [1,3,10]:
    sig=on.rolling(lb,min_periods=1).mean()
    fwd_ic(sig,r_ic,f"ON lb{lb} -> IC+1")
    fwd_ic(sig,r_cc,f"ON lb{lb} -> CC+1")
    fwd_ic(-sig,r_cc,f"ON-fade lb{lb} -> CC+1")
print()
# overnight-minus-intraday spread book (idea 3): sig = on-ic trailing
for lb in [1,3,10,21]:
    sig=(on-ic).rolling(lb,min_periods=max(1,lb//2)).mean()
    fwd_ic(sig,r_cc,f"ONICspread lb{lb} -> CC+1")
print()
# idea 4: weekday of overnight drift (time-of-week x overnight)
on08=on[on.index>='2008-01-01']
dow=on08.groupby(on08.index.dayofweek).mean()*1e4
print('mean overnight bp/day by weekday (0=Mon):', {int(k):round(float(v),2) for k,v in dow.items()})
ic08=ic[ic.index>='2008-01-01']
dowi=ic08.groupby(ic08.index.dayofweek).mean()*1e4
print('mean intraday bp/day by weekday:', {int(k):round(float(v),2) for k,v in dowi.items()})

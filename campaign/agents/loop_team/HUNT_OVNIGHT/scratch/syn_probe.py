"""Is the ON126 spread an equity-premium proxy? corr to SPY fwd ON, breakdown by decade,
and residual-edge test: does ON126 spread survive demeaning by market ON? (cross-sec purity)"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=H.xs_ls(sig,k=k)
p=pos.shift(1).fillna(0.0)
r1=on.fillna(0.0); r2=ic.fillna(0.0)
raw=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)).dropna()  # gross, no costs (dollar-neutral anyway)
net=raw-(p.diff().abs().sum(axis=1)/2.0).reindex(raw.index).fillna(0)*H.COST

mkt_on=on.mean(axis=1).reindex(raw.index).fillna(0)
print('corr(book gross, equal-wt mkt ON):', round(float(raw.corr(mkt_on)),3))
# market-ON-demeaned book return (cross-sectional purity): subtract beta*mkt_on with beta from rolling
beta=(raw.rolling(252).cov(mkt_on)/mkt_on.rolling(252).var()).shift(1).fillna(0).reindex(raw.index)
resid=raw-beta*mkt_on
n08=resid[resid.index>='2008-01-01']-((p.diff().abs().sum(axis=1)/2.0).reindex(resid.index).fillna(0)*H.COST)[resid.index>='2008-01-01']
print(f'mkt-demeaned: SR {n08.mean()/n08.std()*np.sqrt(252):.3f} (vs raw {raw[raw.index>="2008-01-01"].mean()/raw[raw.index>="2008-01-01"].std()*np.sqrt(252):.3f})')
# per-year SR of book (gross)
raw08=raw[raw.index>='2008-01-01']
print('per-year gross SR:')
yrg=raw08.groupby(raw08.index.year).apply(lambda x: x.mean()/x.std()*np.sqrt(252))
print('  ', {int(a):round(float(b),2) for a,b in yrg.items()})
# decade split
print('2008-2012 SR %.2f | 2013-2019 SR %.2f | 2020+ SR %.2f'%(
    raw08['2008':'2012'].mean()/raw08['2008':'2012'].std()*np.sqrt(252),
    raw08['2013':'2019'].mean()/raw08['2013':'2019'].std()*np.sqrt(252),
    raw08['2020':].mean()/raw08['2020':].std()*np.sqrt(252)))

"""VERIFICATION: OVNCAP lb126 k25 (SR 2.015 naive).
1) brute-force per-name PnL identity: day t PnL == sum_name wexec_{name,t} * ret_{name,t}
   where wexec = pos.shift(1), ret for LONG leg = on, for SHORT-intraday leg = -ic. Exact.
2) T+1 probe: add extra lag -> SR must drop (no same-day info).
3) weekday check of the executed stream.
4) deep-dates check: print worst days, confirm |ret| plausible for an equal-weighted 25+25 book.
"""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
lb,k=126,25
sig=on.rolling(lb,min_periods=lb//3).mean()
pos=H.xs_ls(sig,k=k)
p=pos.shift(1).fillna(0)
r1=on.reindex(p.index).fillna(0); r2=ic.reindex(p.index).fillna(0)
turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0)
bor=p.clip(upper=0).abs().sum(axis=1)*H.BORROW
net=p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*H.COST-bor

# 1) brute force loops on 3 sample dates
import random
random.seed(1)
for t in random.sample(list(p.index[100:]),3):
    manual=sum(p.loc[t,n]*r1.loc[t,n]-p.loc[t,n]*r2.loc[t,n] for n in p.columns)
    tot=net.loc[t]+turn.loc[t]*H.COST+bor.loc[t]
    assert abs(manual-tot)<1e-15, (t,manual,tot)
print('brute-force identity on 3 dates: OK')

# 2) T+1 probe: shift pos by 2 extra days
p2=pos.shift(3).fillna(0)
turn2=(p2.diff().abs().sum(axis=1)/2.0).fillna(0)
bor2=p2.clip(upper=0).abs().sum(axis=1)*H.BORROW
net2=p2.mul(r1).sum(axis=1)-p2.mul(r2).sum(axis=1)-turn2*H.COST-bor2
s1=net[net.index>='2008-01-01']; s2=net2[net2.index>='2008-01-01']
print(f"T+1 as-written SR {s1.mean()/s1.std()*np.sqrt(252):.3f} vs extra-lag SR {s2.mean()/s2.std()*np.sqrt(252):.3f}")

# 3) weekday
nn=net[net.index>='2008-01-01']
print('mean bp/day by weekday:', {int(k2):round(float(v)*1e4,2) for k2,v in nn.groupby(nn.index.dayofweek).mean().items()})

# 4) worst days + max single-day
print('worst 5 days %:', {str(t.date()): round(float(v)*100,2) for t,v in nn.nsmallest(5).items()})
print('best 5 days %:', {str(t.date()): round(float(v)*100,2) for t,v in nn.nlargest(5).items()})
print('max |day| %.2f%%  p99 |day| %.2f%%'%(nn.abs().max()*100, nn.abs().quantile(.99)*100))

# 5) signal timing: confirm sig at t uses only on_{t-125..t} (no same-day leak into ON leg: 
# ON leg earns on_t = open_t/close_{t-1}-1 which is KNOWN at t close... note pos.shift(1) makes us
# earn on_{t+1} with pos_t. sig_t includes on_t (known at t close). OK but check on_t known: open_t 
# happened before close_t, yes.
# Check: does sig_t correlate with on_t+1 beyond on_t (i.e. real prediction)?
onnext=on.shift(-1)
sigv=sig.rank(axis=1)
# regression: onnext ~ a + b1*on_t + b2*(sig rank)
b1=[];b2=[]
for t in sig.index[::10]:
    y=onnext.loc[t]; x1=on.loc[t]; x2=sigv.loc[t]
    m=y.notna()&x1.notna()&x2.notna()
    if m.sum()>30:
        X=np.column_stack([np.ones(m.sum()),x1[m],x2[m]])
        try:
            beta=np.linalg.lstsq(X,y[m],rcond=None)[0]; b1.append(beta[1]); b2.append(beta[2])
        except Exception: pass
b1=np.array(b1);b2=np.array(b2)
print('control: on_{t+1} ~ on_t + rank(sig): t(sig)=%.1f  t(on_t)=%.1f (n=%d subsampled days)'%(
    b2.mean()/b2.std()*np.sqrt(len(b2)), b1.mean()/b1.std()*np.sqrt(len(b1)), len(b2)))

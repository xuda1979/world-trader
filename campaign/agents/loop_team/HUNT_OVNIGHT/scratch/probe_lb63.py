"""Probe: what IS the lb63 overnight-momentum L/S actually earning? Decompose + hypothesis tests."""
import sys, os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd, hunt_lib as H

on,ic=H.onic()
O=pd.read_pickle('scratch/O.pkl'); C=pd.read_pickle('scratch/C.pkl')
r_cc=(C/C.shift(1)-1.0).where(on.notna())
sig=on.rolling(63,min_periods=31).mean()

k=25
pos=H.xs_ls(sig,k=k)
p=pos.shift(1).fillna(0)
r_on=on.reindex(p.index).fillna(0)
r_ic=ic.reindex(p.index).fillna(0)

longs=(p>0); shorts=(p<0)
# gross contribution decomposition (sum over names; unnormalized sums just for sign/scale)
lp=(p.where(longs,0)*r_on).sum(axis=1)
sp=(p.where(shorts,0)*r_on).sum(axis=1)
li=(p.where(longs,0)*r_ic).sum(axis=1)
si=(p.where(shorts,0)*r_ic).sum(axis=1)
def show(t,s):
    s=s[s.index>='2008-01-01']
    print(f"{t}: mean bp/day {s.mean()*1e4:+.2f} t {s.mean()/s.std()*np.sqrt(len(s)):+.1f}")
show('LONG leg overnight', lp); show('SHORT leg overnight', sp)
show('LONG leg intraday', li); show('SHORT leg intraday', si)
tot=(lp+sp+li+si); show('TOTAL', tot)
# overnight vs intraday split of total edge
show('overnight total', lp+sp); show('intraday total', li+si)
# control: equal-wt long-only overnight drift (always long the valid names, 1/n) -- is the
# "edge" just the overnight equity risk premium harvested by a book that is ~net-long on drift days?
w=pd.DataFrame(np.where(on.notna(),1.0,0.0),index=on.index,columns=on.columns).div(on.notna().sum(axis=1),axis=0)
ew_on,_=H.net_of_book(w,on)
show('EW-long overnight drift (control)', ew_on)
corr=pd.concat([tot.rename('s'),ew_on.rename('c')],axis=1,join='inner').dropna()
print('corr(lb63 LS, EW-long-ON) =', round(float(corr['s'].corr(corr['c'])),3))
# net position over time: is the book net long?
pnet=p.sum(axis=1)
print('net position: mean %.3f, frac days net>0 %.2f, p95 %.2f'%(pnet.mean(),(pnet>0).mean(),pnet.quantile(.95)))
print('gross |pos|: mean %.2f'%p.abs().sum(axis=1).mean())
# does lb63 ON mom correlate with plain cross-sec momentum (cc 63d)? 
mom63=C.pct_change(63).where(on.notna())
sr=sig.rank(axis=1); mr=mom63.rank(axis=1)
both=sr.notna()&mr.notna()
rows=[]
for t in sig.index[::21]:
    b=both.loc[t]
    if b.sum()>30: rows.append(sr.loc[t][b].corr(mr.loc[t][b]))
print('corr(sig_ON63, mom63cc) mean =', round(float(np.nanmean(rows)),3))

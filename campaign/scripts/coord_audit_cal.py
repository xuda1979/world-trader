"""Coordinator audit: independent reproduction of C5_ng_weekday_prem + PROPER calendar scramble.
Proper test: circular-shift the return stream by random offsets (breaks weekday alignment,
preserves autocorr/vol); recompute strategy on shifted returns; p = frac(shifted SR >= real).
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader')
import numpy as np, pandas as pd

NEW='/Users/daxu/software/world-trader/tools/quant/data/newdata'
px=pd.read_csv(f'{NEW}/DHHNGSP.csv',index_col=0,parse_dates=True).iloc[:,0]
px=px[px>0]; px=px[~px.index.duplicated(keep='last')].sort_index()

def build(px, calm_k=2.5, vt=True, cost=6e-4):
    lp=np.log(px)
    r=lp.diff()
    sig90=r.rolling(90).std()
    dow=px.index.dayofweek
    pos=pd.Series(0.0,index=px.index)
    # long at Friday close (dow 4) held over weekend; short at Wednesday close (dow 2)
    pos[dow==4]=1.0
    pos[dow==2]=-1.0
    # calm filter: skip when same-day |log ret| > calm_k * trailing 90d sigma (evaluated at t)
    skip=(r.abs() > calm_k*sig90.shift(0))
    pos=pos.where(~skip.shift(0).fillna(False), 0.0)
    # T+1: pnl from t close to t+1 close using position set at t
    fwd=r.shift(-1)
    gross=pos*fwd
    to=pos.diff().abs()
    net=gross-to*cost
    net=net.dropna()
    if vt:
        rc=net.expanding(60).std()*np.sqrt(252)
        net=net*((0.10/rc).clip(upper=3.0))
    return net

def stats(r):
    r=r.dropna(); r=r[r.index>='2008-01-01']
    return dict(sr=r.mean()/r.std()*np.sqrt(252), ann=r.mean()*252, n=len(r), r=r)

real=build(px)
st=stats(real)
print(f"REPRO C5_ng_weekday_prem (vt10): SR={st['sr']:.2f} ann={st['ann']*100:.1f}% n={st['n']}")
print("(saved sleeve eval: SR 0.99; agent meta claims 1.74)")

# PROPER calendar scramble: circular shift of the raw price series by random offsets
rng=np.random.default_rng(42)
vals=px.values; idx=px.index
srs=[]
for k in range(60):
    off=int(rng.integers(1, 800))
    pxs=pd.Series(np.roll(vals,off), index=idx)
    r=build(pxs)
    s=stats(r)['sr']
    srs.append(s)
srs=np.array(srs)
p=(np.sum(srs>=st['sr'])+1)/(len(srs)+1)
print(f"CALENDAR-SCRAMBLE (60 circular shifts): p={p:.3f}  scrambled SRs: 5%={np.percentile(srs,5):.2f} med={np.median(srs):.2f} 95%={np.percentile(srs,95):.2f}")

# weekday-conditioned mean check (the raw effect)
lp=np.log(px); r=lp.diff(); r=r[r.index>='2008-01-01']
byd=r.groupby(r.index.dayofweek).agg(['mean','std','count'])
byd['ann%']=byd['mean']*252*100
print("\nraw daily log-ret by weekday (2008+):")
print(byd[['ann%','count']].round(2))
# t-stat of Fri and Wed effects
for d,name in [(4,'Fri'),(2,'Wed'),(0,'Mon')]:
    x=r[r.index.dayofweek==d]
    t=x.mean()/(x.std()/np.sqrt(len(x)))
    print(f"{name}: mean {x.mean()*252*100:5.1f}%/yr ann, t={t:.2f}, n={len(x)}")

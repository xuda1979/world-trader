#!/usr/bin/env python3
"""RES_STATARB R1 screen 2: theme pairs + ETF-panel decorrelation-first gross-scan.

Pass 1: corr to champion (|corr|>=0.15 => REJECT, printed REJ, no further work).
Pass 2 (survivors): GROSS SR (T+1, no costs) — a candidate whose GROSS SR < ~0.8 cannot
clear the 6.4bps full-turnover + borrow NET gate of SR>=1.5, so it is recorded as DEAD
without running the full battery (saves calls; honest — costs only lower SR).
"""
import sys
sys.path.insert(0,'/Users/daxu/software/world-trader'); sys.path.insert(0,'/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt.metrics import sharpe_d, half_split
from bt.gates import corr_to

ROOT='/Users/daxu/software/world-trader'; SC=f'{ROOT}/campaign/team/agents/RES_STATARB/scratch'
ET=f'{ROOT}/tools/quant/data/more_etf'
champ=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv',parse_dates=['date']).set_index('date')['ret']

def px(t):
    s=pd.read_csv(f'{ET}/{t}.csv',index_col=0,parse_dates=True).iloc[:,0].astype(float)
    return s[~s.index.duplicated(keep='last')].sort_index()

PAIRS=[('GDX','GDXJ'),('KBE','KRE'),('SMH','XLB'),('XLK','IGV'),('XME','XLB'),
       ('XLE','XOP'),('XLU','XLV'),('XLF','KBE'),('XLY','XLP'),('XLI','XLB'),
       ('ITB','XHB'),('COPX','GDX'),('SLV','GLD'),('BNO','USO'),('UNG','BOIL_X')]
def z_state(spread, win, zin, zout):
    m=spread.rolling(win,min_periods=win//2).mean().shift(1)
    s=spread.rolling(win,min_periods=win//2).std().shift(1)
    z=(spread-m)/s.replace(0,np.nan)
    st=np.zeros(len(z)); cur=0.0
    for i,zv in enumerate(z.values):
        if not np.isfinite(zv): st[i]=cur; continue
        if cur==0 and zv>zin: cur=1.0
        elif cur==0 and zv<-zin: cur=-1.0
        elif cur==1 and zv<zout: cur=0.0
        elif cur==-1 and zv>-zout: cur=0.0
        st[i]=cur
    return pd.Series(st,index=z.index)

def pair_gross(a,b,win,zin=2.0,zout=0.5,side='rev'):
    ra=px(a).pct_change(); rb=px(b).pct_change()
    idx=ra.index.intersection(rb.index)
    ra,rb=ra.reindex(idx),rb.reindex(idx)
    spread=np.log(px(a)/px(a).iloc[0]).reindex(idx)+ -np.log(px(b)/px(b).iloc[0]).reindex(idx)
    st=z_state(spread,win,zin,zout)
    sign=-1.0 if side=='rev' else 1.0  # rev: short rich spread => -st on (a-b)
    w=st*sign
    return (w.shift(1).fillna(0)*(ra-rb)).dropna()

print(f"{'pair':12s}{'win':>4s}  corr    grossSR  H1/H2        verdict")
survivors=[]
for a,b in PAIRS:
    if b=='BOIL_X': continue
    for win in (40,63,126):
        for side in ('rev','mom'):
            r=pair_gross(a,b,win,side=side)
            r=r[r.index>='2008-01-01']
            if len(r)<800: continue
            c=corr_to(champ,r)
            sr=sharpe_d(r); h1,h2=half_split(r)
            v='REJ' if abs(c)>=0.15 else ('DEAD' if sr<0.8 else 'ALIVE')
            if v=='ALIVE': survivors.append((a,b,win,side))
            print(f"{a+'/'+b:12s}{win:4d}  {c:+.3f}  {sr:+.2f}   ({h1:+.2f},{h2:+.2f})  {v}")
print('survivors:',survivors)

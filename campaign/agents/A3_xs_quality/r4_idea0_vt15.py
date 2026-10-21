"""r4 idea0 v2: dualmom vt15 with CORRECT vol targeting (trim to active window first, r1 lesson).
Gates at r4 bar (SR>=0.8, halves>=0.4), find max vt passing gate (d)."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd
from campaign.harness import data as D
from engine import month_ends, vol_target, strategy_ret, COST
from r2lib import wbacktest

WIN,BAND,FRAC=200,0.03,1/3
px=D.closes(); rets=px.pct_change(); idx=rets.index
MES=[d for d in month_ends(rets) if d in px.index]
sig=px.shift(21)/px.shift(252)-1.0
ff=D.ff_factors(); mkt=(1+ff["Mkt-RF"]+ff["RF"]).cumprod()
ma=mkt.rolling(WIN,min_periods=WIN).mean()
g=pd.Series(np.where(mkt>ma*(1+BAND),1.0,np.where(mkt<ma*(1-BAND),0.0,np.nan)),index=mkt.index).reindex(px.index).ffill().fillna(0.0)
W=pd.DataFrame(0.0,index=idx,columns=rets.columns)
for t in MES:
    if t not in sig.index or g.loc[t]<=0: continue
    row=sig.loc[t].dropna()
    if len(row)<10: continue
    row=row.sort_values(); nl=max(int(np.floor(len(row)*FRAC)),1)
    for s in row.index[-nl:]: W.loc[t,s]=1.0/nl
net,_,_=wbacktest(W,rets)
nz=W.abs().sum(axis=1); start=nz[nz>0].index[0]

def sret(target):
    r=net[net.index>=start]
    return vol_target(r,target=target).iloc[5:].dropna()
def gates(r):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    mid=r.index[len(r)//2]; h1=r[r.index<=mid];h2=r[r.index>mid]
    return dict(SR=round(r.mean()/r.std()*np.sqrt(252),2),H1=round(h1.mean()/h1.std()*np.sqrt(252),2),H2=round(h2.mean()/h2.std()*np.sqrt(252),2),
        negYr=int((yr<0).sum()),worst=round(yr.min()*100,1),ann=round(r.mean()*252*100,1),vol=round(r.std()*np.sqrt(252)*100,1))

for tgt in (0.10,0.115,0.125,0.15):
    print(f"vt={tgt:.3f}",gates(sret(tgt)))
# max vt with worst-year > -5%
lo,hi=0.10,0.30
for _ in range(12):
    mid=(lo+hi)/2
    if gates(sret(mid))["worst"]>-5.0: lo=mid
    else: hi=mid
print(f"max vt passing gate(d) worst>-5%: {lo:.3f} gates={gates(sret(lo))}")
# fix vt15 with slight band retune? no — charter says verify, not retune. Report verdict.
gg=gates(sret(0.15))
ok=gg['SR']>=0.8 and gg['H1']>=0.4 and gg['H2']>=0.4 and gg['negYr']<=2 and gg['worst']>-5.0
print("IDEA0 vt15 verdict:","PASS" if ok else "FAIL — gate(d) yearly",gg)

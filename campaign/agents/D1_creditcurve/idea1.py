"""IDEA 1: Credit quality-timing. Signal: BAA-AAA spread z (weekly decision, step 5).
Long BAA-synth TR (dur 7) / flat; T+1; 6bps one-side; trailing-only expanding VT10 clip 3.
Window: baa starts 1986 -> use 1986+ overlap with aaa (1983+)."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

baa=yld('baa'); aaa=yld('aaa')
df=pd.concat([baa.rename('baa'),aaa.rename('aaa')],axis=1).dropna()
df=df[df.index>='1986-01-01']
sp=df['baa']-df['aaa']
ex=(df['baa']/252.0-7.0*df['baa'].diff())-rf_daily().reindex(df.index)  # BAA synth excess TR (dur 7)
rfc=rf_daily().reindex(df.index)
def build(w,step,thr,direction):
    z=(sp-sp.rolling(w).mean())/sp.rolling(w).std()
    zz=z.iloc[::step]
    if direction=='rev':   sig=(zz>thr).astype(float)      # wide spreads -> long (mean-revert+carry)
    else:                  sig=(zz<-thr).astype(float)     # spreads tightening -> long (momentum)
    sig=sig.reindex(z.index).ffill().shift(1).fillna(0)     # T+1
    gross=sig*ex
    to=sig.diff().abs().fillna(0)*1.0
    net=gross-to*COST
    return vt(net+rfc*(1-sig)), sig
rows=[]
for w in (126,252,378,504):
    for step in (5,10,21):
        for thr in (0.0,0.5,1.0):
            for d in ('rev','mom'):
                net,sig=build(w,step,thr,d)
                sr=net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
                rows.append((sr,w,step,thr,d,net,sig))
rows.sort(key=lambda t:-t[0])
print("top 12 configs (full net SR):")
for sr,w,step,thr,d,_,_ in rows[:12]:
    print(f"  SR={sr:.2f} w={w} step={step} thr={thr} {d}")
print("bottom 3:", [(round(r[0],2),r[1],r[2],r[3],r[4]) for r in rows[-3:]])
# best config full gates
sr,w,step,thr,d,net,sig=rows[0]
res=gates(net,f"idea1_{d}_w{w}_s{step}_thr{thr}")
print("\nBEST config gates:"); print(res['stats']); 
print({k:v for k,v in res.items() if k not in('stats','gates')}); print(res['gates'],'ALL_PASS=',res['ALL_PASS'])
sr2,w2,s2,t2,d2,n2,_=rows[1]; sr3,w3,s3,t3,d3,n3,_=rows[2]
print("\nrunner-ups:", round(sr2,2),(w2,s2,t2,d2),"|",round(sr3,2),(w3,s3,t3,d3))
print("turnover/day (best):", round(sig.diff().abs().mean(),5))

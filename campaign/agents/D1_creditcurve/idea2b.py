"""IDEA 2 salvage: 2s10s steepener carry + regime filters.
A) carry-on-carry: trade only when trailing-252d realized carry > 0.
B) hiking veto: flat when 3m yield is RISING fast (bear-flattener regime dodged)."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

Da,Db=DUR['DGS2'],DUR['DGS10']
y2,y10,y3m=yld('DGS2'),yld('DGS10'),yld('DGS3MO')
df=pd.concat([y2.rename('a'),y10.rename('b'),y3m.rename('m')],axis=1,sort=True).dropna()
df=df[df.index>='1990-01-01']
w=Db/Da
leg=w*rfn(df['a'],Da)-rfn(df['b'],Db)
rfc=rf_daily().reindex(df.index).fillna(0)
pos0=pd.Series(1.0,index=df.index).shift(1).fillna(0)
raw=vt(pos0*leg-pos0.diff().abs().fillna(0)*(1+w)*COST)

# A) carry-on-carry (trailing realized of gross leg, only past)
realcarry=leg.rolling(252).sum()
for thr in (0.0,):
    sigf=(realcarry>thr).astype(float).shift(1).fillna(0)  # T+1 on filter
    to=pos0.diff().abs().fillna(0)*(1+w)+sigf.diff().abs().fillna(0)*(1+w)
    netA=vt(pos0*sigf*leg-to*COST)
    s=stats(netA)
    print(f"A carry-on-carry: SR={s['sr']:.2f} negy={s['negy']} worst={s['worst']:.1f}% mdd={s['mdd']:.1f}% H1={halves(netA)[0]:.2f} H2={halves(netA)[1]:.2f}")
# B) hiking veto: flat when 3m rose > 25bps over 63d (active tightening)
hike=(df['m'].diff(63)>0.25).astype(float).shift(1).fillna(0)
netB=vt(pos0*(1-hike)*leg-pos0.diff().abs().fillna(0)*(1+hike.diff().abs())*COST*0.5)
s=stats(netB)
print(f"B hiking veto: SR={s['sr']:.2f} negy={s['negy']} worst={s['worst']:.1f}% mdd={s['mdd']:.1f}% H1={halves(netB)[0]:.2f} H2={halves(netB)[1]:.2f}")
# yearly detail for best
for nm,net in (('A',netA),('B',netB)):
    yr={k:round(v*100,1) for k,v in stats(net)['yearly'].items() if v<0}
    print(nm,"negyrs:",yr)

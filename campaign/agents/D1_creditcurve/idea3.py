"""IDEA 3: belly carry — long 5y vs DV01-neutral wings (2y,30y), MONTHLY (step 21) and
weekly (step 5) rebalances, always-on (carry harvest, not z-timing). Gate honest."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

D2,D5,D10,D30=DUR['DGS2'],DUR['DGS5'],DUR['DGS10'],DUR['DGS30']
def belly(start='1990-01-01'):
    y2,y5,y30=yld('DGS2'),yld('DGS5'),yld('DGS30')
    df=pd.concat([y2.rename('y2'),y5.rename('y5'),y30.rename('y30')],axis=1,sort=True).dropna()
    df=df[df.index>=start]
    # wings DV01-neutral vs 1 unit of belly: n5 = 1; wings sum duration = D5
    n2,n30=D5/2/D2, D5/2/D30   # split wing duration equally
    # position: long 1x 5y, short n2 x 2y, short n30 x 30y -> gross = 1+n2+n30
    rf_leg=rfn(df['y5'],D5)-n2*rfn(df['y2'],D2)-n30*rfn(df['y30'],D30)
    rfc=rf_daily().reindex(df.index).fillna(0)
    gn=1+n2+n30
    out={}
    for step in (5,10,21):
        pos=pd.Series(1.0,index=df.index).iloc[::step]
        pos=pos.reindex(df.index).ffill().shift(1).fillna(0)  # set monthly, trade next day
        to=pos.diff().abs().fillna(0)*gn
        net=vt(pos*rf_leg-to*COST)
        out[step]=(net,pos,gn)
    return out

res=belly()
for step,(net,pos,gn) in res.items():
    s=stats(net); h=halves(net); cb=corr_to(net,CHAMP)
    tod=pos.diff().abs().mean()
    print(f"belly long5y short2/30 step{step}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}% H1={h[0]:.2f} H2={h[1]:.2f} corr_champ={cb:.3f} to/d={tod:.4f}")
    yr={k:v for k,v in s['yearly'].items() if v<0}
    print("   neg yrs:", yr)

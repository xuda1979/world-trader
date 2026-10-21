"""IDEA 2: always-on DV01-neutral steepener carry (2s10s, 5s30s) + trailing DD-throttle.
Proper decimal units. Throttle: trailing-126d DD of raw stream; mult=0.5 when DD<thr; T+1."""
import sys; sys.path.insert(0,'.')
import numpy as np, pandas as pd
from d1_lib import *

def steep_carry(a,b,Da,Db,start='1990-01-01'):
    ya,yb=yld(a),yld(b)
    df=pd.concat([ya.rename('a'),yb.rename('b')],axis=1,sort=True).dropna()
    df=df[df.index>=start]
    w=Db/Da
    rf_leg=w*rfn(df['a'],Da)-rfn(df['b'],Db)
    rfc=rf_daily().reindex(df.index).fillna(0)
    pos=pd.Series(1.0,index=df.index).shift(1).fillna(0)
    to=pos.diff().abs().fillna(0)*(1+w)
    net_raw=pos*rf_leg-to*COST
    return net_raw, rf_leg, (1+w), rfc, df.index

def throttled(net_raw, ddwin=126, thr=-0.03, cut=0.5):
    eq=(1+net_raw).cumprod()
    peak=eq.rolling(ddwin,min_periods=20).max()
    dd=eq/peak-1
    mult=pd.Series(np.where(dd<thr,cut,1.0),index=net_raw.index).shift(1).fillna(1.0)
    return vt(net_raw*mult), mult

for nm,(a,b,Da,Db) in {'2s10s':('DGS2','DGS10',1.9,8.5),'5s30s':('DGS5','DGS30',4.4,17.5)}.items():
    raw,leg,gn,rfc,idx=steep_carry(a,b,Da,Db)
    base=vt(raw); s0=stats(base); h0=halves(base)
    cb=corr_to(base,CHAMP)
    print(f"\n== {nm} NO throttle: SR={s0['sr']:.2f} ann={s0['ann']:.1f}% mdd={s0['mdd']:.1f}% negy={s0['negy']} worst={s0['worst']:.1f}% H1={h0[0]:.2f} H2={h0[1]:.2f} corr_champ={cb:.3f}")
    for ddwin in (126,252):
        for thr in (-0.02,-0.03,-0.05):
            net,mult=throttled(raw,ddwin,thr)
            s=stats(net)
            print(f"   throttle {ddwin}d {thr}: SR={s['sr']:.2f} ann={s['ann']:.1f}% mdd={s['mdd']:.1f}% negy={s['negy']} worst={s['worst']:.1f}%")

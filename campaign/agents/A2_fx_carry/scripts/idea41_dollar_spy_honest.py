"""Charter 3 honest: SPY long when DTWEXBGS z<0. Pub-lag: H.10 print t published t+1 -> use z.shift(1) at decision t.
Sweep lookbacks x thresholds for plateau. Then corr to champion + library."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
import numpy as np, pandas as pd

spx=old_s("spx"); ret=spx.pct_change()
R=pd.DataFrame({"SPX":ret}).fillna(0)
exb=new_s("DTWEXBGS")

def build(lb,thr,lag=1,vtg=0.10):
    z=(exb-exb.rolling(lb).mean())/exb.rolling(lb).std()
    z=z.shift(lag)  # pub lag: decision at t uses print t-1
    sig=pd.Series(np.where(z<thr,1.0,0.0),index=z.index).reindex(ret.index).fillna(0)
    pos=pd.DataFrame({"SPX":sig})
    net,to=backtest(pos,R)
    return U.vol_target(net,vtg),pos,net

print("== plateau sweep (lag1) ==")
res={}
for lb in [126,189,252,315,378,504]:
    for thr in [0.0,-0.25,-0.5,0.25,0.5]:
        nv,pos,net=build(lb,thr)
        g=U.gates(nv)
        sr=nv.dropna(); sr=sr.mean()/sr.std()*np.sqrt(252) if len(sr)>500 and sr.std()>0 else np.nan
        res[(lb,thr)]=(sr,g)
        print(f"lb{lb} thr{thr:+.2f}: SR={sr:.2f} {'PASS' if g['pass_'] else g.get('why','')[:50]}")

print()
print("== deep check lb252 thr0 (and neighbors) ==")
for lb,thr in [(252,0.0),(315,0.0)]:
    nv,pos,net=build(lb,thr)
    r=nv.dropna()
    h1,h2=U.halves_ok(r)
    yr=U.yearly(nv); neg=yr[yr<0]
    real,p=scramble_df(pos,R,n=200)
    s,mx=corr_to_library(nv)
    print(f"lb{lb} thr{thr}: SR={r.mean()/r.std()*np.sqrt(252):.2f} H1={h1:.2f} H2={h2:.2f} negyr={len(neg)} worst={neg.min()*100 if len(neg) else 0:.1f}% scrub_p={p:.3f} maxcorr={mx:.2f}")
    print("   yearly:"," ".join(f"{k}:{v*100:+.1f}" for k,v in yr.items()))
    print("   top corr:", s.reindex(s.abs().sort_values().index[-3:]).round(2).to_dict())

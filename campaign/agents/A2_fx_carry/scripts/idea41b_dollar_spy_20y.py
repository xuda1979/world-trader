"""Charter 3 honest FULL test: SPY (twelve_big panel 2006+) long when DTWEXBGS z<0 (pub-lag 1d).
20y window incl 2008. Plateau + full gates + corr to champion/library."""
import sys, os; sys.path.insert(0, os.path.dirname(__file__))
from r7_lib import *
from harness.data import closes
import numpy as np, pandas as pd

spy=closes()[["SPY"]].dropna()
print("SPY window:", spy.index.min().date(), spy.index.max().date())
ret=spy.pct_change(); R=ret.fillna(0); R.columns=["SPY"]
exb=new_s("DTWEXBGS")

def build(lb,thr,lag=1):
    z=(exb-exb.rolling(lb).mean())/exb.rolling(lb).std()
    z=z.shift(lag)
    sig=pd.Series(np.where(z<thr,1.0,0.0),index=z.index).reindex(ret.index).fillna(0)
    return pd.DataFrame({"SPY":sig})

print("== sweep (lag1) ==")
grid={}
for lb in [126,189,252,315,378]:
    for thr in [-0.5,-0.25,0.0,0.25,0.5]:
        pos=build(lb,thr)
        net,to=backtest(pos,R)
        nv=U.vol_target(net,0.10)
        g=U.gates(nv)
        sr=nv.dropna(); sr=sr.mean()/sr.std()*np.sqrt(252)
        grid[(lb,thr)]=sr
        print(f"lb{lb} thr{thr:+.2f}: SR={sr:.2f} {'PASS' if g['pass_'] else g.get('why','')[:55]}")

print()
for lb,thr in [(315,0.0),(252,0.0),(315,0.25)]:
    pos=build(lb,thr)
    net,to=backtest(pos,R)
    nv=U.vol_target(net,0.10)
    r=nv.dropna()
    h1,h2=U.halves_ok(r)
    yr=U.yearly(nv); neg=yr[yr<0]
    real,p=scramble_df(pos,R,n=200)
    s,mx=corr_to_library(nv)
    print(f"lb{lb} thr{thr}: SR={r.mean()/r.std()*np.sqrt(252):.2f} H1={h1:.2f} H2={h2:.2f} negyr={len(neg)} worst={neg.min()*100 if len(neg) else 0:.1f}% p={p:.3f} maxcorr={mx:.2f}")
    print("  yearly:"," ".join(f"{k}:{v*100:+.1f}" for k,v in yr.items()))

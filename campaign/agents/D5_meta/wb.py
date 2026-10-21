import sys, numpy as np, pandas as pd
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
from champion_build import POOL, load, vt, stats
ROOT = "/Users/daxu/software/world-trader"

def construct2(TGT, THROT=None, vts=None):
    """Generalized: THROT = list of (THR,LB,FR) stacked throttles; vts = dict of per-sleeve vt targets (default 0.10)."""
    if THROT is None: THROT = [(0.04,126,0.5)]
    V, S = {}, {}
    for n,p in POOL.items():
        r = load(p)
        v,s = vt(r, 0.10 if vts is None else vts.get(n,0.10))
        V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    blend = Vn.mean(axis=1)
    blend = blend[blend.index >= "2008-09-01"]
    b,_ = vt(blend, TGT)
    b = b.fillna(0)
    dsc_sum = pd.Series(0.0, index=b.index)
    for (THR,LB,FR) in THROT:
        eq = (1+b).cumprod()
        rm = eq.rolling(LB).max().shift(1)
        tdd = eq.shift(1)/rm - 1
        sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
        dsc_sum = dsc_sum + sc.diff().abs()*0.5
        b = b*sc
    tot = tw.reindex(b.index).fillna(0) + dsc_sum
    return (b - tot*(6/10000)).dropna()

def isos(r):
    o = {}
    for tag, m in (("IS", (r.index<"2017-01-01")), ("OOS", (r.index>="2017-01-01"))):
        x = r[m]
        eq=(1+x).cumprod(); dd=(eq/eq.cummax()-1).min()
        yr = x.groupby(x.index.year).apply(lambda y:(1+y).prod()-1)
        o[tag]=dict(ann=round(x.mean()*252*100,1), sr=round(x.mean()/x.std()*np.sqrt(252),2),
                    mdd=round(dd*100,1), negy=int((yr<0).sum()), worst=round(yr.min()*100,1))
    return o

def row(name, r):
    s = isos(r)
    return (f"{name:28s} IS: ann {s['IS']['ann']:5.1f} sr {s['IS']['sr']:4.2f} dd {s['IS']['mdd']:5.1f} neg{s['IS']['negy']} wr{s['IS']['worst']:5.1f} | "
            f"OOS: ann {s['OOS']['ann']:5.1f} sr {s['OOS']['sr']:4.2f} dd {s['OOS']['mdd']:5.1f} neg{s['OOS']['negy']} wr{s['OOS']['worst']:5.1f}")

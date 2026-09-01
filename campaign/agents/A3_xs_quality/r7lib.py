"""r7 shared helpers: FRED/macro cross-asset engines (charter r7).
Conventions identical to r1-r6: signal at t uses data <= t; weights effective t+1;
costs 6bps x one-side turnover; trailing expanding vt10 (min 60d, cap 5x) AFTER trim.
Reuses r6lib.wback_rb (r6-verified: explicit Wt row at EVERY rebalance date) with
CUSTOM return panels; adds: generic circular-shift scramble (cost-inclusive),
sleeve-library corr scan, FRED loaders (local data_fred / data_fred_new / agent-fetched
r7_data). Scramble nulls are cost-inclusive per r2 lesson."""
import sys; sys.path.insert(0,"/Users/daxu/software/world-trader"); sys.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality")
import numpy as np, pandas as pd, glob
from r6lib import wback_rb, sret, gates6, xcorr, CH, OLD, IDX
FRED="/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred/"
FNEW="/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/"
R7D="/Users/daxu/software/world-trader/campaign/agents/A3_xs_quality/r7_data/"

def load(path):
    df=pd.read_csv(path); c0=df.columns[0]
    s=pd.Series(df.iloc[:,1].astype(float).values,index=pd.to_datetime(df[c0]))
    return s[~s.index.duplicated()].sort_index().dropna()

_LIB=None
def lib_series():
    global _LIB
    if _LIB is None:
        _LIB={p.split("/")[-1][:-4]:pd.read_csv(p,index_col=0,parse_dates=True).iloc[:,0]
              for p in glob.glob("/Users/daxu/software/world-trader/campaign/results/sleeve_library/*.csv")}
    return _LIB

def lib_corr(r):
    out={}
    for k,s in lib_series().items():
        j=pd.concat([r.rename("a"),s.rename("b")],axis=1).dropna()
        if len(j)>250: out[k]=round(j.a.corr(j.b),3)
    cs=pd.Series(out).dropna()
    return cs.reindex(cs.abs().sort_values(ascending=False).index)

def evaluate(name,r):
    g=gates6(r); g["corr_champ"]=xcorr(r,CH); g["corr_old"]=xcorr(r,OLD)
    lc=lib_corr(r); g["corr_lib_max"]=float(lc.abs().max()) if len(lc) else np.nan
    g["corr_lib_top"]=dict(lc.abs().sort_values(ascending=False).head(3)) if len(lc) else {}
    g["ok_r7"]=(g["SR"]>=0.6 and g["H1"]>=0.3 and g["H2"]>=0.3 and g["negYr"]<=2
                and g["worst"]>-5.0 and g["scramble_p"]<0.05
                and abs(g["corr_champ"])<0.25 and abs(g["corr_old"])<0.25)
    print(f"[{name}]",g,flush=True)
    return g

def circ_scramble(builder,sig,rets,start,target=0.10,nrep=200,seed=42,real_sr=None):
    """Circular time-shift of SIGNAL series/panel rows (preserves autocorr+xs structure,
    breaks signal/return alignment). Rebuild Wt via builder, reprice 6bps, same vt.
    Returns (p, null_srs): p = P(null SR >= real)."""
    vals=sig.values.copy(); T=len(sig.index)
    rng=np.random.default_rng(seed); srs=[]
    for _ in range(nrep):
        k=int(rng.integers(21,T))
        if sig.ndim==1: sp=pd.Series(np.roll(vals,k),index=sig.index)
        else: sp=pd.DataFrame(np.roll(vals,k,axis=0),index=sig.index,columns=sig.columns)
        Wt,rbd=builder(sp)
        net,_=wback_rb(Wt,rets,rbd)
        rr=sret(net,start,target)
        srs.append(rr.mean()/rr.std()*np.sqrt(252))
    srs=np.array(srs); return float((srs>=real_sr).mean()),srs

def wed_rbd(idx,start=None):
    return [d for d in idx if d.weekday()==2 and (start is None or d>=start)]
def month_rbd(idx,start=None):
    s=pd.Series(idx,index=idx)
    out=list(s.groupby(idx.to_period("M")).max().values)
    return [d for d in out if start is None or d>=start]

def synth_bond_ret(y, dur=8.5):
    """Daily total-return proxy of a constant-duration bond from its yield y (in pct pts):
    r_t = y_{t-1}/252/100 - dur*(y_t-y_{t-1})/100. PIT: uses only y_{t-1}, y_t."""
    return (y.shift(1)/252.0/100.0 - dur*(y-y.shift(1))/100.0)

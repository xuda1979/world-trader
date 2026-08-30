"""r6 lib: overnight/intraday split mechanics + gates. Decision-date convention:
signal/calendar known at close t; pnl booked at t = ret over t->t+1 (ON) or within t+1 (ID).
Costs: ON round trip = 1 one-side at close t + 1 one-side at open t+1 = turnover 2.0/day held.
ID round trip = buy open t+1, sell close t+1 = turnover 2.0/day held. 6bps per one-side."""
import os, sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
D=f"{ROOT}/campaign/agents/A2_fx_carry/data"
sys.path.insert(0,f"{ROOT}/campaign/harness")
import util

O=pd.read_pickle(D+"/O.pkl"); C=pd.read_pickle(D+"/C.pkl")
ON=O.shift(-1)/C-1.0            # night t -> open t+1
ID=C/O-1.0                      # intraday of day t (pairs with ON_{t-1})
on_ew=ON.mean(axis=1)           # EW across names with next open available
id_ew=ID.mean(axis=1)
id_fwd=id_ew.shift(-1)          # intraday of t+1, same booking date t
def days(): 
    return on_ew.dropna().index

COST_ON=2.0*6.0/1e4   # 12bp per held day
COST_ID=2.0*6.0/1e4

def net_series(gross, held_mask, cost_held):
    r=gross.copy()
    mask=held_mask.reindex(r.index).fillna(False).astype(bool)
    r=r[mask]
    r=r.dropna()-cost_held
    return r

def tdom_masks():
    idx=days()
    per=pd.PeriodIndex(idx,freq="M")
    s=pd.Series(np.arange(len(idx)),index=idx)
    g=s.groupby(per)
    tdom=g.cumcount()+1
    cnt=g.transform("count")
    tend=cnt-tdom+1
    return tdom,tend

def stats(r,label):
    r=r.dropna()
    ann=r.mean()*252; vol=r.std()*np.sqrt(252); sr=r.mean()/r.std()*np.sqrt(252)
    half=len(r)//2
    sr1=r.iloc[:half].mean()/r.iloc[:half].std()*np.sqrt(252)
    sr2=r.iloc[half:].mean()/r.iloc[half:].std()*np.sqrt(252)
    yr=(1+r).groupby(r.index.year).prod()-1
    neg=yr[yr<0]
    vt=util.vol_target(r,0.10)
    yrv=(1+vt).groupby(vt.index.year).prod()-1
    negv=yrv[yrv<0]
    dd=(vt.cumsum()-vt.cumsum().cummax()).min()
    # corr to champion
    try:
        ch=pd.read_csv(f"{ROOT}/campaign/results/CHAMPION_FINAL_daily.csv",index_col=0,parse_dates=True)["ret"]
        c=vt.to_frame("s").join(ch.rename("c"),how="inner").corr().iloc[0,1]
    except Exception as e: c=np.nan
    print(f"{label}: n={len(r)} ann={ann*100:.1f}% vol={vol*100:.1f}% SR={sr:.2f} H1={sr1:.2f} H2={sr2:.2f} "
          f"negYr={len(negv)} worstYr={yrv.min()*100:.1f}% vt_ann={(1+vt).prod()**(252/len(vt))-1 if len(vt) else 0:.2%} corrChamp={c:.2f} maxDDvt={dd*100:.1f}%")
    return dict(sr=sr,sr1=sr1,sr2=sr2,yrv=yrv,neg=len(negv),worst=yrv.min(),vt=vt,r=r)

def scramble(sig,r,n=200,seed=7):
    """pre-vt scramble (r2b lesson): circular-shift sig vs net pre-vt returns."""
    sig=sig.reindex(r.index).fillna(0.0); rr=r.reindex(sig.index)
    real=(sig*rr).mean()/(sig*rr).std()*np.sqrt(252)
    rng=np.random.default_rng(seed); null=[]
    v=sig.values
    for _ in range(n):
        k=rng.integers(1,len(v)); s=np.roll(v,k)
        ps=pd.Series(s,index=sig.index)*rr
        null.append(ps.mean()/ps.std()*np.sqrt(252))
    p=float((np.array(null)>=real).mean())
    print(f"  scramble pre-vt: real={real:.2f} p={p:.3f}")
    return real,p

"""D1_creditcurve shared lib: honest synth-TR engine + full campaign gates."""
import sys, numpy as np, pandas as pd
ROOT="/Users/daxu/software/world-trader"
FRED=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
FNEW=f"{ROOT}/tools/quant/hedge_fund_strats/data_fred_new"
CHAMP=f"{ROOT}/campaign/results/GOAL100_CHAMPION_BALANCED_daily.csv"
COORD=f"{ROOT}/campaign/results/COORD_FINAL_daily.csv"
A1CR=f"{ROOT}/campaign/agents/A1_trend_cta/sleeves/A1_credit_regime_mom.csv"
COST=6e-4
DUR={'DGS1MO':0.08,'DGS3MO':0.25,'DGS6MO':0.5,'DGS1':1.0,'DGS2':1.9,'DGS3':2.9,'DGS5':4.4,
     'DGS7':6.5,'DGS10':8.5,'DGS20':15.0,'DGS30':17.5}

def ser(path):
    df=pd.read_csv(path)
    v=pd.to_numeric(df.iloc[:,1],errors='coerce'); v.index=pd.to_datetime(df.iloc[:,0])
    v=v.replace([-99.99,-99.9],np.nan).dropna()
    return v[~v.index.duplicated(keep='last')].sort_index()

def yld(name, new=False):
    base=FNEW if new else FRED
    fn=f"{base}/{name}.csv"
    if not __import__('os').path.exists(fn): fn=f"{FRED}/{name}.csv"
    s=ser(fn)
    s=s.reindex(pd.bdate_range(s.index[0],pd.Timestamp("2026-08-28"))).ffill()/100.0
    return s

def rfn(y,d): return (-d*y.diff()+y/252.0)  # daily synth TR, PROPER decimal units

def rf_daily():
    t=yld('DTB3',new=True); return t/252.0

def vt(net,vt_ann=0.10,minp=60,clip=3.0):
    """Trailing-only expanding vol target (shift 1) applied to NET returns."""
    sc=(vt_ann/(net.expanding(minp).std()*np.sqrt(252))).clip(upper=clip).shift(1)
    return (net*sc).dropna()

def load(path):
    df=pd.read_csv(path,index_col=0,parse_dates=True); return df.iloc[:,0]

def stats(r):
    r=r.dropna(); mu,sd=r.mean(),r.std(); yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    eq=(1+r).cumprod()
    return dict(n=len(r),start=str(r.index[0].date()),end=str(r.index[-1].date()),
        ann=mu*252*100,sr=mu/sd*np.sqrt(252) if sd>0 else 0,
        mdd=(eq/eq.cummax()-1).min()*100,negy=int((yr<0).sum()),worst=yr.min()*100,
        yearly={int(k):round(v*100,1) for k,v in yr.items()})

def halves(r):
    mid=r.index[len(r)//2]
    h1,h2=r[r.index<=mid],r[r.index>mid]
    return (h1.mean()/h1.std()*np.sqrt(252) if len(h1)>1 else 0,
            h2.mean()/h2.std()*np.sqrt(252) if len(h2)>1 else 0)

def scramble_pctile(r,n=200,seed=0):
    rng=np.random.default_rng(seed); v=r.dropna().values
    real=v.mean()/v.std()*np.sqrt(252); cnt=0
    for _ in range(n):
        rc=rng.permutation(v)
        if rc.std()>0 and rc.mean()/rc.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, real

def rotation_scramble(net, sig, ex, rfc, n=200, seed=0):
    """Position-rotation null (A1-style): roll the signal through the IDENTICAL
    pipeline (excess returns, costs, rf accrual, VT machinery); real SR vs null."""
    rng=np.random.default_rng(seed)
    real=net.mean()/net.std()*np.sqrt(252); v=net.dropna().values; cnt=0
    nv=len(sig)
    for _ in range(n):
        k=int(rng.integers(1, nv))
        s2=pd.Series(np.roll(sig.values, k), index=sig.index)
        to2=s2.diff().abs().fillna(0)*1.0
        net2=vt(s2*ex-to2*COST+rfc*(1-s2))
        if len(net2)>60:
            vv=net2.values
            if vv.std()>0 and vv.mean()/vv.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, real

def corr_to(r,path):
    b=load(path); i=r.index.intersection(b.dropna().index)
    if len(i)<250: return np.nan
    return np.corrcoef(r[i],b[i])[0,1]

def gates(net,name="",plateau=None,plateau_idx=None):
    """plateau: list of SRs across param grid; plateau_idx: index of chosen param."""
    s=stats(net); h1,h2=halves(net); p,real=scramble_pctile(net)
    cb=corr_to(net,CHAMP); cc=corr_to(net,COORD); ca=corr_to(net,A1CR)
    pl=None
    if plateau is not None and plateau_idx is not None:
        peak=max(plateau); pl=dict(chosen=round(plateau[plateau_idx],2),
            peak=round(peak,2), neighbors_within_20pct=bool(plateau[plateau_idx]>=0.8*peak))
    g=dict(a_fullSR=s['sr']>=1.0, b_plateau=(pl['neighbors_within_20pct'] if pl else None),
        c_halves=(h1>=0.5 and h2>=0.5), d_yearly=(s['negy']<=2 and s['worst']>-5),
        e_scramble=(p<=0.05), f_corr15=(abs(cb)<0.15), g_window=s['n']>=60*4)
    return dict(name=name,stats={k:(round(v,2) if isinstance(v,float) else v) for k,v in s.items()},
        H1=round(h1,2),H2=round(h2,2),scramble_p=round(p,3),
        corr_champ=round(cb,3),corr_coord=round(cc,3),corr_A1credit=(None if np.isnan(ca) else round(ca,3)),
        plateau=pl,gates=g,ALL_PASS=all(v for v in g.values() if v is not None))

def turnover_per_day(pos):
    return pos.diff().abs().fillna(0)

"""HUNT_INDUSTRY48 lib: KF48 industry VW daily engines. Campaign-standard conventions:
- T+1: decision at t (data<=t) earns day t+1 return. Executed path W_t = sc_{t-1}*sig_{t-1}.
- COST 6.4bps/side charged on FINAL executed-weight turnover |dW|/2 (incl vol-rebalance).
- borrow 0.5%/yr on short notional. No RF credit on cash.
- vt: trailing expanding(min60) std of the strategy's own gross, cap 3, target 10% ann.
- poslag scramble: np.roll on DECISION series, costs recomputed, stored real scale applied.
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
KF=f'{ROOT}/tools/quant/data/kenfrench/48_Industry_Portfolios_Daily.csv'
COST=6.4/1e4
EACH_SIDE_PAYS=True  # cost = SUM|dW|*6.4bps (TRADE_RECORD_STANDARD: qty=|dW| per record, 6.4bps each)
BORROW=0.005/252

def load48(path=KF):
    lines=open(path).read().split('\n')
    hi=None
    for i,ln in enumerate(lines):
        if ln.startswith(',') and 'Agric' in ln: hi=i; break
    assert hi is not None, 'VW daily header not found'
    cols=[c.strip() for c in lines[hi].split(',')[1:49]]
    assert len(cols)==48, f'expected 48 industry names, got {len(cols)}'
    rows=[]
    for ln in lines[hi+1:]:
        p=ln.split(',')
        if len(p)>=49 and p[0].strip().isdigit() and len(p[0].strip())==8: rows.append(p[:49])
        elif rows and ('Equal Weighted' in ln or 'Average' in ln): break
    df=pd.DataFrame(rows,columns=['date']+cols).set_index('date')
    df.index=pd.to_datetime(df.index,format='%Y%m%d')
    df=df.apply(pd.to_numeric,errors='coerce')/100.0
    # KF missing codes are EXACTLY -99.99 and -999 in raw percent units -> -0.9999, -9.99 after /100.
    # Mask EXACT values only (verified by token scan: '-99.99' x56325 is the sole <=-0.99 code token;
    # legitimate crash returns like -53.62 must be preserved).
    df=df.mask(np.isclose(df,-0.9999) | np.isclose(df,-9.99) | np.isclose(df,-999.0))
    df=df.dropna(how='all')
    # drop leading rows until all 48 industries are live (post-missing-code era)
    live=df.notna().all(axis=1)
    first_live=int(np.argmax(live.values))
    df=df.iloc[first_live:]
    df.attrs['first_fully_live']=str(df.index[0].date())
    return df

def net_of_book48(sig, R, w_scale=None):
    """sig: DECISION weights DataFrame at t (info<=t), R: realized daily returns at t.
    Executed path: W_t = (w_scale or 1)_{t-1} * sig_{t-1}. Returns (net, W_exec).
    Costs charged on |dW|/2 *6.4bps; borrow 0.5%/yr on shorts."""
    if w_scale is None: w_scale=pd.Series(1.0,index=sig.index)
    W=(sig.mul(w_scale.shift(1),axis=0)).shift(1)
    gross=(W*R).sum(axis=1)
    turn=W.diff().abs().fillna(0.0).sum(axis=1)   # each side pays 6.4bps
    bor=BORROW*W.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor), W

def vt_scale(sig, R, vt=0.10, min_days=60, cap=3.0):
    """scale KNOWN at t: expanding std of strategy gross earned thru t (uses sig thru t-1)."""
    pre,_=net_of_book48(sig,R)   # no costs matter for vol est; use gross instead:
    gross=pd.Series((sig.shift(1)*R).sum(axis=1),index=sig.index)
    rv=gross.expanding(min_days).std()*np.sqrt(252)
    return (vt/rv).clip(upper=cap)

def poslag_scramble_p(sig, R, n=200, seed=0, min_lag=21, w_scale=None):
    """Charter gate: roll DECISION series by random lag in [21,T-21], recompute net incl
    costs (stored REAL w_scale applied), p=frac(permSR>=realSR). NOT return-roll."""
    if w_scale is None: w_scale=pd.Series(1.0,index=sig.index)
    def build(s):
        W=(s.mul(w_scale,axis=0)).shift(1)
        gross=(W*R).sum(axis=1)
        turn=W.diff().abs().fillna(0.0).sum(axis=1)
        bor=BORROW*W.clip(upper=0.0).abs().sum(axis=1)
        return (gross-turn*COST-bor).dropna()
    real_sr=float(build(sig).std())and float(build(sig).mean()/build(sig).std()*np.sqrt(252))
    T=len(sig); rng=np.random.default_rng(seed); cnt=0; meds=[]
    vals=sig.values
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        sp=pd.DataFrame(np.roll(vals,lag,axis=0),index=sig.index,columns=sig.columns)
        ns=build(sp); meds.append(float(ns.mean()/ns.std()*np.sqrt(252)))
        if meds[-1]>=real_sr: cnt+=1
    return cnt/n, float(np.median(meds)), real_sr

def full_stats(r):
    r=r.dropna()
    mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else np.nan
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r),ann_geo=eq.iloc[-1]**(252/len(r))-1,ann_arith=mu*252,sr=sr,mdd=dd,
                negy=int((yr<0).sum()),worst=float(yr.min()),years=len(yr),
                first=str(r.index[0].date()),last=str(r.index[-1].date()),
                yearly={int(k):round(v*100,2) for k,v in yr.items()})

def halves_sr(r):
    r=r.dropna(); mid=r.index[len(r)//2]
    return full_stats(r[r.index<=mid])['sr'], full_stats(r[r.index>mid])['sr']

def flatten_gates(r):
    r=r.dropna()
    return dict(ac1=float(r.autocorr(1)),uniqR=float(r.round(10).nunique()/len(r)))

def corr_to(r, other):
    j=pd.concat([r.rename('s'),other.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

def negyr_tol(r,max_neg=2,floor=-0.05):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg=yr[yr<0]; bad=neg[neg<=floor]
    return (len(neg)<=max_neg and len(bad)==0), {int(k):round(v,4) for k,v in neg.items()}

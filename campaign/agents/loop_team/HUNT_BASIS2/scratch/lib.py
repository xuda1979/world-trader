"""HUNT_BASIS2 shared lib: basis/spread mean-reversion sleeves + full gate evaluation.
Mechanics mirror the proven brwt recipe (campaign/scripts/backtest_brwt_spread_rev15.py):
z-score of log spread over trailing window, position only when |z|>gate, T+1 execution
(sp.diff().shift(-1)), 6bps/side on |pos| turnover /2 (half-spread per side), trailing
vol-target 0.08 (expanding window, min 60d, cap 3.0) — as in B2_highfreq/gates.py.
NO lookahead: signal at t uses info <= t; P&L from t->t+1. Real daily path (no flattening).
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
FRED=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
NEW=f'{ROOT}/tools/quant/data/newdata'

def fred(name, src=FRED):
    df=pd.read_csv(f'{src}/{name}.csv', index_col=0, parse_dates=True)
    s=df['value'] if 'value' in df.columns else df.iloc[:,0]
    return s[~s.index.duplicated(keep='last')].sort_index()

def zrev(spread, lookback=15, gate=1.5, min_start='2008-01-01', cost_bps=6.0):
    """z-rev on a price/log-spread series. Returns NET daily series (T+1, 6bps/side),
    gross (uncosted) for turnover reporting, and position series."""
    sp=spread.dropna(); sp=sp[sp.index>=min_start]
    m=sp.rolling(lookback,min_periods=lookback).mean()
    sd=sp.rolling(lookback,min_periods=lookback).std().replace(0,np.nan)
    z=(sp-m)/sd
    pos=pd.Series(0.0,index=sp.index)
    pos[z<-gate]=1.0; pos[z>gate]=-1.0
    ret=sp.diff().shift(-1)          # P&L t->t+1 (T+1 execution)
    gr=(pos*ret).dropna()
    tup=(pos.diff().abs()/2.0).reindex(gr.index).fillna(0.0)  # one-side turnover
    net=gr-tup*cost_bps/1e4
    return net, gr, pos.reindex(gr.index), tup

def vol_target(r, vt_ann=0.08, min_days=60, cap=3.0):
    rv=r.expanding(min_days).std()*np.sqrt(252)
    scale=(vt_ann/rv).clip(upper=cap)
    return (r*scale).dropna(), scale

def full_stats(r):
    r=r.dropna()
    mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else np.nan
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r), ann_geo=(eq.iloc[-1])**(252/len(r))-1, ann_arith=mu*252,
                sr=sr, mdd=dd, negy=int((yr<0).sum()), worst=yr.min() if len(yr) else 0,
                years=len(yr))

def halves_sr(r):
    r=r.dropna(); mid=r.index[len(r)//2]
    return full_stats(r[r.index<=mid])['sr'], full_stats(r[r.index>mid])['sr']

def negyr_tol(r, max_neg=2, floor=-0.05):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg=yr[yr<0]
    bad=neg[neg<=floor]
    return (len(neg)<=max_neg and len(bad)==0), {int(k):round(v,4) for k,v in neg.items()}

def scramble_p(r, n=200, seed=0, block=10):
    """200x 10-day block-scramble (moving-block bootstrap): p(SR_perm >= SR_real).
    This is the legitimate null for autocorrelated daily paths (VET_HONESTY fixed version)."""
    rng=np.random.default_rng(seed)
    r=np.asarray(r.dropna()); T=len(r); nb=T//block
    real=r.mean()/r.std()*np.sqrt(252); cnt=0
    for _ in range(n):
        st=rng.integers(0,T-block,size=nb)
        rc=np.concatenate([r[s:s+block] for s in st])[:T]
        if rc.std()>0 and rc.mean()/rc.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, real

def flatten_gates(r):
    r=r.dropna()
    ac1=r.autocorr(1); uniq=r.nunique()/len(r)
    # nonzero constant runs (exact-value runs, excluding 0.0 gate-off days which are by-design)
    v=r.values; runs=[]; cur=1
    for i in range(1,len(v)):
        if v[i]==v[i-1] and v[i]!=0.0: cur+=1
        else:
            if cur>1: runs.append(cur)
            cur=1
    if cur>1: runs.append(cur)
    return dict(ac1=float(ac1), uniqR=float(uniq), max_run_nz=int(max(runs) if runs else 0))

def corr_to_champion(r, champ):
    j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

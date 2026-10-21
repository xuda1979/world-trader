"""HUNT_CROSSASSET2 lib: cross-asset relative books + full campaign gate battery.
Conventions (campaign-standard, iter4/5-audited; cost = 6.4bps/side per THIS charter):
- T+1: pos decided at t (info<=t) earns ret t->t+1
- cost: 6.4bps * one-side turnover (|dpos|/2), charged once per day
- borrow: 0.5%/yr on short notional
- no RF credit on flat leg (conservative)
- vt: trailing expanding min 60d cap 3 (pool standard 0.08 where used)
- position-lag scramble: circular roll of POSITION by lag [21,T-21], 200x, p(SR_perm>=SR_real)
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
FRED=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
NEW=f'{ROOT}/tools/quant/data/newdata'
FXDIR=f'{ROOT}/tools/quant/data/fx'
COST=6.4/1e4
BORROW=0.005/252

def load_csv(path, valcol=None):
    df=pd.read_csv(path, index_col=0, parse_dates=True)
    if valcol and valcol in df.columns: s=df[valcol]
    else: s=df.iloc[:,0]
    s=pd.to_numeric(s,errors='coerce')
    s=s[~s.index.duplicated(keep='last')].sort_index()
    s=s[s.notna()]
    return s

def dex(name):  # FRED daily noon FX, local currency per USD
    return load_csv(f'{NEW}/{name}.csv')

def fred(name, src=FRED):
    return load_csv(f'{src}/{name}.csv')

def net_of(pos, r, cost=COST, borrow_short=True):
    """pos: position decided at t (info<=t); r: asset return at t. T+1 shift inside."""
    p=pos.shift(1).reindex(r.index)
    gross=(p*r)
    turn=(p.diff().abs()/2.0).fillna(0.0)
    net=gross-turn*cost
    if borrow_short:
        net=net-BORROW*p.clip(upper=0.0).abs()
    return net.dropna(), p.reindex(net.index).fillna(0.0)

def spread_net(pos, spread):
    """paper-spread convention (brwt champion): pos*spread.diff().shift(-1), T+1."""
    ret=spread.diff().shift(-1)
    return net_of(pos, ret)

def zrev_pos(spread, lookback=15, gate=1.5):
    sp=spread.dropna()
    m=sp.rolling(lookback,min_periods=lookback).mean()
    sd=sp.rolling(lookback,min_periods=lookback).std().replace(0,np.nan)
    z=(sp-m)/sd
    pos=pd.Series(0.0,index=sp.index)
    pos[z<-gate]=1.0; pos[z>gate]=-1.0
    return pos

def mom_pos(spread, lookback=126):
    sp=spread.dropna()
    sig=np.sign(sp-sp.shift(lookback))
    pos=sig.replace(0,0.0)
    return pos

def vol_target_scale(r, vt=0.08, min_days=60, cap=3.0, shift=1):
    rv=r.expanding(min_days).std()*np.sqrt(252)
    s=(vt/rv).clip(upper=cap)
    return s.shift(shift)

def full_stats(r):
    r=r.dropna()
    mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else np.nan
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r), ann_geo=(eq.iloc[-1])**(252/len(r))-1, ann_arith=mu*252,
                sr=sr, mdd=dd, negy=int((yr<0).sum()), worst=float(yr.min()) if len(yr) else 0.0,
                years=len(yr), first=str(r.index[0].date()), last=str(r.index[-1].date()))

def halves_sr(r):
    r=r.dropna(); mid=r.index[len(r)//2]
    return full_stats(r[r.index<=mid])['sr'], full_stats(r[r.index>mid])['sr']

def negyr_tol(r, max_neg=2, floor=-0.05):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg=yr[yr<0]; bad=neg[neg<=floor]
    return (len(neg)<=max_neg and len(bad)==0), {int(k):round(v,4) for k,v in neg.items()}

def position_lag_p(pos, r, n=200, seed=0, min_lag=21, cost=COST, borrow_short=True):
    p=pos.shift(1).reindex(r.index).fillna(0.0)
    r=r.reindex(p.index)
    turn=(p.diff().abs()/2.0).fillna(0.0)
    bor=BORROW*p.clip(upper=0.0).abs() if borrow_short else 0.0
    net=(p*r-turn*cost-bor).dropna()
    real=net.mean()/net.std()*np.sqrt(252)
    v=p.values.copy(); T=len(v); rng=np.random.default_rng(seed); cnt=0
    tv=turn.values; bv=np.asarray(bor); rv_=r.values
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        vs=np.roll(v,lag)
        ps=pd.Series(vs,index=p.index)
        nt=(ps.diff().abs()/2.0).fillna(0.0).values
        ns=pd.Series(vs*rv_-nt*cost-bv,index=p.index).dropna()
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, float(real)

def flatten_gates(r):
    r=r.dropna()
    ac1=float(r.autocorr(1)); uniq=float(r.round(10).nunique()/len(r))
    return dict(ac1=ac1, uniqR=uniq)

def corr_to(r, blend):
    j=pd.concat([r.rename('s'),blend.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

def load_blend():
    b=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True)
    return b.iloc[:,0]

def gate_battery(name, r, pos, blend, min_start='2008-01-01', min_sr=1.0, target_corr=0.15):
    r=r.dropna(); r=r[r.index>=pd.Timestamp(min_start)]
    pos=pos.reindex(r.index).fillna(0.0)
    st=full_stats(r); h1,h2=halves_sr(r); okn,negyrs=negyr_tol(r)
    pl_p, pl_real=position_lag_p(pos, r, n=200)
    fg=flatten_gates(r); corr,ncorr=corr_to(r,blend)
    g=dict(SR=st['sr'], gate_SR=(st['sr']>=min_sr), H1=h1, H2=h2, gate_halves=(h1>=0.3 and h2>=0.3),
           negy=st['negy'], worst=st['worst'], gate_negy=okn,
           scramble_p=pl_p, gate_scramble=(pl_p<0.05),
           ac1=fg['ac1'], gate_ac1=(fg['ac1']<0.5), uniqR=fg['uniqR'], gate_uniq=(fg['uniqR']>=0.08),
           corr=corr, gate_corr=(abs(corr)<target_corr), n_corr=ncorr)
    npass=sum([g['gate_SR'],g['gate_halves'],g['gate_negy'],g['gate_scramble'],g['gate_ac1'],g['gate_uniq'],g['gate_corr']])
    print(f"{name}: SR2008+ {st['sr']:.3f} | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']} worst {st['worst']*100:.1f}% | "
          f"poslag_p {pl_p:.3f} | ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={ncorr}) | "
          f"ann_geo {st['ann_geo']*100:.1f}% MDD {st['mdd']*100:.1f}% | GATES {npass}/7")
    return g, st

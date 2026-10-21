"""HUNT_FF2 lib: Fama-French DAILY factor data engines + full campaign gate battery.
Conventions (campaign-standard, iter4-audited):
- T+1: signal/position decided with info <= t earns return t->t+1 (pos.shift(1)*r alignment in build)
- costs 6bps/side on one-side turnover (|dpos|/2 per day, 6bps each side -> turn*COST with turn=|dpos|/2*2? 
  Convention from BASIS2/CFX4: net = gross - (|dpos|/2)*6bps  [half-turn per side = |dpos|/2, charged once]
- borrow 0.5%/yr charged on SHORT notional (max(-pos,0)) daily
- no RF/cash credit on flat leg (conservative, no Tbill-carry SR inflation)
- vol target: trailing EXPANDING window min 60d, cap (as BASIS2 vol_target), scale KNOWN at t
- position-lag scramble (charter iter5): circular shift (np.roll) of POSITION series by random
  lag in [21, T-21], 200x, recompute net incl costs, p = frac(SR_perm >= SR_real); gate p<0.05
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
FFDIR=f'{ROOT}/tools/quant/data/ff_factors'
KFDIR=f'{ROOT}/tools/quant/data/kenfrench'
COST=6.0/1e4
BORROW=0.005/252

def _parse_kf(path, colname):
    lines=open(path).read().split('\n')
    hi=None
    for i,ln in enumerate(lines):
        if ln.startswith(',') and colname in ln: hi=i; break
    assert hi is not None, f'header for {colname} not found in {path}'
    rows=[]
    for ln in lines[hi+1:]:
        p=ln.split(',')
        if len(p)>=2 and p[0].strip().isdigit() and len(p[0].strip())==8:
            rows.append(p)
    df=pd.DataFrame(rows)
    df[0]=pd.to_datetime(df[0],format='%Y%m%d')
    df=df.set_index(0)
    for c in df.columns:
        df[c]=pd.to_numeric(df[c],errors='coerce')
    df=df.dropna(how='all')
    return df

def load_ff3():
    df=_parse_kf(f'{FFDIR}/F-F_Research_Data_Factors_daily.csv','Mkt-RF')/100.0
    df.columns=['Mkt-RF','SMB','HML','RF']
    return df

def load_mom():
    df=_parse_kf(f'{FFDIR}/F-F_Momentum_Factor_daily.csv','Mom')/100.0
    df.columns=['MOM']
    return df

def load_vix():
    v=pd.read_csv(f'{ROOT}/alphaportfolio_replication/data/vix_daily.csv',index_col=0,parse_dates=True)
    return v['vix'][~v.index.duplicated(keep='last')].sort_index()

def load_champion():
    c=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv',index_col=0,parse_dates=True)
    return c.iloc[:,0]

def net_of(pos, r, borrow_short=True):
    """pos: position decided at t (info<=t); r: realized return at t. Shift inside."""
    p=pos.shift(1).reindex(r.index)
    gross=(p*r)
    turn=(p.diff().abs()/2.0).fillna(0.0)            # one-side turnover
    net=gross-turn*COST
    if borrow_short:
        net=net-BORROW*p.clip(upper=0.0).abs()
    return net.dropna(), p.reindex(net.index).fillna(0.0)

def vol_target_scale(r, vt=0.08, min_days=60, cap=3.0, trailing_shift=1):
    """scale known at t: expanding std of r up to t (min 60d), ann-vol target, capped."""
    rv=r.expanding(min_days).std()*np.sqrt(252)
    s=(vt/rv).clip(upper=cap)
    return s.shift(trailing_shift)  # known at t => apply to pos earning t+1 handled by net_of shift

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

def position_lag_p(pos, r, n=200, seed=0, min_lag=21, include_costs=True):
    """charter gate: circular-shift the POSITION series vs returns, 200x random lags in
    [21, T-21]; recompute net (incl costs+borrow); p = frac(SR_perm >= SR_real)."""
    p=pos.shift(1).reindex(r.index).fillna(0.0)
    r=r.reindex(p.index)
    turn=(p.diff().abs()/2.0).fillna(0.0)
    bor=BORROW*p.clip(upper=0.0).abs()
    net=(p*r-turn*COST-bor).dropna()
    real=net.mean()/net.std()*np.sqrt(252)
    v=p.values.copy(); T=len(v); rng=np.random.default_rng(seed); cnt=0
    tv=turn.values; bv=bor.values; rv_=r.values
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        vs=np.roll(v,lag)
        ps=pd.Series(vs,index=p.index)
        nt=(ps.diff().abs()/2.0).fillna(0.0).values
        ns=pd.Series(vs*rv_-nt*COST-bv,index=p.index).dropna()
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, float(real)

def flatten_gates(r):
    r=r.dropna()
    ac1=float(r.autocorr(1)); uniq=float(r.round(10).nunique()/len(r))
    return dict(ac1=ac1, uniqR=uniq)

def corr_to(r, champ):
    j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

def gate_battery(name, r, pos, champ, min_start='2008-01-01'):
    r=r.dropna(); r=r[r.index>=pd.Timestamp(min_start)]
    pos=pos.reindex(r.index).fillna(0.0)
    st=full_stats(r); h1,h2=halves_sr(r); okn,negyrs=negyr_tol(r)
    pl_p, pl_real=position_lag_p(pos, r, n=200)
    fg=flatten_gates(r); corr,ncorr=corr_to(r,champ)
    g=dict(SR=st['sr'], gate_SR=(st['sr']>=0.6), H1=h1, H2=h2, gate_halves=(h1>=0.3 and h2>=0.3),
           negy=st['negy'], worst=st['worst'], gate_negy=okn,
           scramble_p=pl_p, gate_scramble=(pl_p<0.05),
           ac1=fg['ac1'], gate_ac1=(fg['ac1']<0.5), uniqR=fg['uniqR'], gate_uniq=(fg['uniqR']>=0.08),
           corr=corr, gate_corr=(abs(corr)<0.15), n_corr=ncorr)
    npass=sum([g['gate_SR'],g['gate_halves'],g['gate_negy'],g['gate_scramble'],g['gate_ac1'],g['gate_uniq'],g['gate_corr']])
    print(f"{name}: SR2008+ {st['sr']:.3f} | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']} worst {st['worst']*100:.1f}% | "
          f"poslag_p {pl_p:.3f} | ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={ncorr}) | "
          f"ann {st['ann_geo']*100:.1f}% MDD {st['mdd']*100:.1f}% | GATES {npass}/7")
    return g, st

def net_of_book(pos, r):
    """pos: DataFrame of per-asset positions decided at t (rows=t). r: DataFrame aligned.
    Returns book net series (sum over columns), with per-asset turnover costs and borrow."""
    common=pos.index.intersection(r.index)
    p=pos.reindex(common).fillna(0.0); rr=r.reindex(common).fillna(0.0)
    ps=p.shift(1).fillna(0.0)
    gross=(ps*rr).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor).dropna()

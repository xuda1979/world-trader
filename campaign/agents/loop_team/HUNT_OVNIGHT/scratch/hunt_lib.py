"""HUNT_OVNIGHT lib: overnight/intraday panel engines on twelve_big (298 names, 2006-2026).
Conventions copied from campaign-standard (HUNT_FF2 lib.py, iter4-audited; B2 gates):
- net_of_book: pos decided at t (info<=t); net_t = pos_{t-1}*r_t - (|dpos_{t-1}|/2)*COST - BORROW*max(-pos_{t-1},0)
  COST=6.4bps/side (charter); BORROW=0.5%/252 per day on short notional
- xs_ls: cross-sectional long/short k-vs-k dollar-neutral weights (sum 0, sum|w|=k... top-k +1/k, bot-k -1/k)
- vt_scale: trailing expanding std (min 60d), target/cap, shift(1) -> known at t
- position_lag_p: circular np.roll of POSITION by random lag [21,T-21], 200x, recompute net incl costs
- full_stats/halves_sr/flatten_gates: identical formulas to campaign gates (B2_highfreq/gates.py)
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
COST=6.4/1e4          # 6.4 bps per side (charter)
BORROW=0.005/252      # 0.5%/yr daily on short notional

# ---------- panel loaders ----------
def load_panel():
    import os
    D=f'{ROOT}/tools/quant/data/twelve_big'
    o={}; c={}
    for f in sorted(os.listdir(D)):
        if not f.endswith('.csv'): continue
        df=pd.read_csv(f'{D}/{f}',parse_dates=['date'],index_col='date')
        s=f[:-4]; o[s]=df['open']; c[s]=df['close']
    O=pd.DataFrame(o).sort_index(); C=pd.DataFrame(c).sort_index()
    O=O[~O.index.duplicated(keep='last')]; C=C[~C.index.duplicated(keep='last')]
    return O,C

def onic(O=None,C=None):
    if O is None: O,C=load_panel()
    Cp=C.shift(1); valid=O.notna()&Cp.notna()
    on=O/Cp-1.0; ic=C/O-1.0
    on=on.where(valid); ic=ic.where(valid)
    return on,ic

# ---------- net / cost machinery ----------
def net_of_book(pos, r, borrow=True):
    """pos: DataFrame (t x name) position weights decided AT t (uses info<=t).
       r: DataFrame (t x name) same-day close-to-close returns.
       Returns (net Series, executed-position DataFrame p=pos.shift(1))."""
    common=pos.index.intersection(r.index)
    p=pos.reindex(common).fillna(0.0).shift(1).fillna(0.0)
    rr=r.reindex(common).fillna(0.0)
    gross=(p*rr).sum(axis=1)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)   # one-side turnover
    net=gross-turn*COST
    if borrow:
        net=net-BORROW*p.clip(upper=0.0).abs().sum(axis=1)
    return net, p

def xs_ls(sig, k=25):
    """sig: signal matrix (t x name), higher = long. +1/k on top-k, -1/k on bottom-k.
    NaN signal (invalid overnight) => weight 0. Returns position matrix decided at t."""
    R=sig.rank(axis=1,ascending=False)          # 1=best
    N=sig.notna().sum(axis=1)
    Ndf=pd.DataFrame(np.broadcast_to(N.values[:,None],sig.shape),index=sig.index,columns=sig.columns)
    valid=sig.notna()
    long_=(R<=k)&valid; short=(R>(Ndf-k))&valid
    w=pd.DataFrame(np.where(long_,1.0/k,np.where(short,-1.0/k,0.0)),index=sig.index,columns=sig.columns)
    return w.where(valid,0.0)

def vt_scale(r, tgt=0.10, min_days=60, cap=3.0):
    rv=r.expanding(min_days).std()*np.sqrt(252)
    return (tgt/rv).clip(upper=cap).shift(1).fillna(1.0)

# ---------- gates (identical formulas to campaign gates) ----------
def full_stats(r):
    r=r.dropna(); mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else np.nan
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r), ann_geo=float(eq.iloc[-1])**(252/len(r))-1, ann_arith=float(mu*252),
                sr=float(sr), mdd=float(dd), negy=int((yr<0).sum()),
                worst=float(yr.min()) if len(yr) else 0.0, years=len(yr),
                first=str(r.index[0].date()), last=str(r.index[-1].date()),
                yearly={int(a):round(float(b),4) for a,b in yr.items()})

def halves_sr(r):
    r=r.dropna(); mid=r.index[len(r)//2]
    return full_stats(r[r.index<=mid])['sr'], full_stats(r[r.index>mid])['sr']

def negyr_tol(r, max_neg=2, floor=-0.05):
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg=yr[yr<0]; bad=neg[neg<=floor]
    return (len(neg)<=max_neg and len(bad)==0), {int(a):round(float(b),4) for a,b in neg.items()}

def flatten_gates(r):
    r=r.dropna()
    return dict(ac1=float(r.autocorr(1)), uniqR=float(r.round(10).nunique()/len(r)))

def corr_to(r, champ):
    j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

def position_lag_p(pos, r, n=200, seed=0, min_lag=21, executed=None):
    """charter gate: circular-shift the EXECUTED position series by random lag in [21,T-21];
    recompute net incl costs+borrow on the SAME return matrix; p = frac(SR_perm>=SR_real).
    For book-level: pass executed-position matrix p (=pos.shift(1)) and per-name returns r.
    The blend is sum over names of p*r (net after costs recomputed per permutation)."""
    if executed is None:
        executed=pos.shift(1).reindex(r.index).fillna(0.0)
    p=executed.reindex(r.index).fillna(0.0)
    rr=r.reindex(p.index).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=BORROW*p.clip(upper=0.0).abs().sum(axis=1)
    net=(p*rr).sum(axis=1)-turn*COST-bor
    net=net.dropna()
    real=float(net.mean()/net.std()*np.sqrt(252))
    v=p.values; T=len(v); rng=np.random.default_rng(seed); cnt=0
    tv=rr.values
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        vs=np.roll(v,lag,axis=0)
        ps=pd.DataFrame(vs,index=p.index,columns=p.columns)
        nt=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
        ns=(ps*rr).sum(axis=1)-nt*COST-bor
        ns=ns.dropna()
        if len(ns)>1 and float(ns.std())>0 and float(ns.mean())/float(ns.std())*np.sqrt(252)>=real: cnt+=1
    return cnt/n, real

def gate_battery(name, r, posmat, rmat, champ, min_start='2008-01-01'):
    r=r.dropna(); r=r[r.index>=pd.Timestamp(min_start)]
    pm=posmat.reindex(r.index).fillna(0.0)
    ex=pm.shift(1).fillna(0.0)
    st=full_stats(r); h1,h2=halves_sr(r); okn,negyrs=negyr_tol(r)
    pl_p,pl_real=position_lag_p(pm,rmat,n=200,executed=ex.reindex(rmat.index).fillna(0.0))
    fg=flatten_gates(r); corr,ncorr=corr_to(r,champ)
    g=dict(SR=st['sr'],gate_SR=bool(st['sr']>=0.6),H1=h1,H2=h2,gate_halves=bool(h1>=0.3 and h2>=0.3),
           negy=st['negy'],worst=st['worst'],gate_negy=bool(okn),negyrs=negyrs,
           scramble_p=pl_p,gate_scramble=bool(pl_p<0.05),
           ac1=fg['ac1'],gate_ac1=bool(fg['ac1']<0.5),uniqR=fg['uniqR'],gate_uniq=bool(fg['uniqR']>=0.08),
           corr=corr,gate_corr=bool(abs(corr)<0.15),n_corr=ncorr)
    npass=sum([g['gate_SR'],g['gate_halves'],g['gate_negy'],g['gate_scramble'],g['gate_ac1'],g['gate_uniq'],g['gate_corr']])
    print(f"{name}: SR2008+ {st['sr']:.3f} | H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']}/{st['years']} worst {st['worst']*100:+.1f}% | poslag_p {pl_p:.3f} | ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f}(n={ncorr}) | ann_geo {st['ann_geo']*100:+.1f}% MDD {st['mdd']*100:.1f}% | GATES {npass}/7")
    return g, st

def load_champion():
    c=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',index_col=0,parse_dates=True)
    return c.iloc[:,0]


def position_lag_p2(pos, r_on, r_ic, n=200, seed=0, min_lag=21):
    """Two-stream book position-lag scramble (OVNCAP family): net = sum(pexec*(r_on - r_ic)) - costs.
    Circular np.roll of EXECUTED position matrix by random lag in [21,T-21]; recompute BOTH streams
    + costs; p = frac(SR_perm >= SR_real). This is the charter gate correctly specified for a book
    whose PnL is pos*on - pos*ic (a single-stream implementation mis-prices the IC leg)."""
    common=pos.index.intersection(r_on.index).intersection(r_ic.index)
    p=pos.shift(1).reindex(common).fillna(0.0)
    r1=r_on.reindex(common).fillna(0.0); r2=r_ic.reindex(common).fillna(0.0)
    turn=(p.diff().abs().sum(axis=1)/2.0).fillna(0.0)
    bor=p.clip(upper=0).abs().sum(axis=1)*BORROW
    net=(p.mul(r1).sum(axis=1)-p.mul(r2).sum(axis=1)-turn*COST-bor).dropna()
    real=float(net.mean()/net.std()*np.sqrt(252))
    pex=p.reindex(net.index).fillna(0.0)
    r1e=r1.reindex(net.index).fillna(0.0); r2e=r2.reindex(net.index).fillna(0.0)
    bve=bor.reindex(net.index).fillna(0.0).values
    v=pex.values; T=len(v); rng=np.random.default_rng(seed); cnt=0
    for _ in range(n):
        lag=int(rng.integers(min_lag,T-min_lag))
        vs=np.roll(v,lag,axis=0)
        ps=pd.DataFrame(vs,index=pex.index,columns=pex.columns)
        nt=(ps.diff().abs().sum(axis=1)/2.0).fillna(0.0).values
        ns=ps.mul(r1e).sum(axis=1)-ps.mul(r2e).sum(axis=1)-nt*COST-bve
        if float(ns.std())>0 and float(ns.mean())/float(ns.std())*np.sqrt(252)>=real: cnt+=1
    return cnt/n, real

"""HUNT_FXDEPO lib: DEX cross z-reversion engines, campaign gate battery.
Conventions (campaign-standard, FF2/CFX4-audited):
- T+1: position decided at t (info<=t) earns return t->t+1 (pos.shift(1) in net)
- costs 6bps/side on one-side turnover: net = gross - (|dpos|/2)*6e-4 per leg
- borrow 0.5%/yr on short notional
- gates per CHARTER: SR>=0.6 (2008+), H1/H2>=0.3, <=2 neg yrs each>-5%,
  200x 10d-BLOCK POSITION-LAG scramble p<0.05, |corr|<0.15 vs HONEST14V3_BALANCED,
  ac1<0.5, uniqR>=0.08.
"""
import numpy as np, pandas as pd
ROOT='/Users/daxu/software/world-trader'
ND=f'{ROOT}/tools/quant/data/newdata'
FR=f'{ROOT}/tools/quant/hedge_fund_strats/data_fred'
FXD=f'{ROOT}/tools/quant/data/fx'
COST=6.0/1e4
BORROW=0.005/252

def dex(name):
    df=pd.read_csv(f'{ND}/{name}.csv',index_col=0,parse_dates=True)
    v=pd.to_numeric(df.iloc[:,0],errors='coerce'); v=v[v>0]
    return v[~v.index.duplicated(keep='last')].sort_index()

def twelvedata(name):
    df=pd.read_csv(f'{FXD}/{name}.csv',index_col=0,parse_dates=True)
    return df['close'].sort_index()

def load_champion():
    c=pd.read_csv(f'{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv',
                  index_col=0,parse_dates=True)
    return c.iloc[:,0]

def book_ret(spread, pos, pxA, pxB):
    """spread book: pos decided at t on spread=ln(P_A/P_B); PnL=pos.shift(1)*(r_A-r_B).
    Costs per leg on |dpos|/2 one-side; borrow on shorts."""
    rA=pxA.pct_change(); rB=pxB.pct_change()
    idx=spread.index
    p=pos.reindex(idx).fillna(0.0)
    ps=p.shift(1).fillna(0.0)
    gross=(ps*rA.reindex(idx).fillna(0.0))-(ps*rB.reindex(idx).fillna(0.0))
    turn=(ps.diff().abs()/2.0).fillna(0.0)
    bor=BORROW*ps.clip(upper=0.0).abs()
    return (gross-turn*COST-bor)

def zpos(spread, lb, cap=2.0):
    """continuous -z position with cap: w=clip(-z,-cap,cap)/cap -> per-unit <=0.5 book each side."""
    m=spread.rolling(lb).mean(); s=spread.rolling(lb).std()
    z=(spread-m)/s
    return (-(z/cap)).clip(-0.5,0.5)

def net_of_book(pos, r):
    """pos: DataFrame per-asset positions decided at t; r: DataFrame returns aligned."""
    common=pos.index.intersection(r.index)
    p=pos.reindex(common).fillna(0.0); rr=r.reindex(common).fillna(0.0)
    ps=p.shift(1).fillna(0.0)
    gross=(ps*rr).sum(axis=1)
    turn=(ps.diff().abs()/2.0).fillna(0.0).sum(axis=1)
    bor=BORROW*ps.clip(upper=0.0).abs().sum(axis=1)
    return (gross-turn*COST-bor).dropna()

def position_lag_block_p(pos_book, rets, n=200, seed=0, block=10, min_lag=21):
    """CHARTER GATE: 10-day-block position-lag scramble.
    Permute the POSITION path in 10d blocks (same block order applied to all books)
    vs the SAME realized returns; recompute net incl costs+borrow; p=frac(SR_perm>=SR_real).
    pos_book: DataFrame (T x books) already shift(1)ed effective positions.
    rets: DataFrame (T x books) aligned returns."""
    P=pos_book.fillna(0.0).values
    R=rets.reindex(pos_book.index).fillna(0.0).reindex(columns=pos_book.columns).fillna(0.0).values[:len(P)]
    turn=np.abs(np.diff(P,axis=0,prepend=P[:1,:]))/2.0
    gross=(P*R).sum(axis=1); tc=(turn.sum(axis=1))*COST
    bor=(BORROW*np.clip(P,0,None).sum(axis=1))
    net=gross-tc-bor
    net=pd.Series(net,index=pos_book.index).dropna()
    real=net.mean()/net.std()*np.sqrt(252)
    T=len(P); rng=np.random.default_rng(seed); cnt=0
    nb=T//block
    Tuse=nb*block
    Rf=np.vstack([R, np.zeros((block,R.shape[1]))])  # pad so idx up to nb*block-1 valid
    for _ in range(n):
        perm=rng.permutation(nb)
        idx=np.concatenate([np.arange(b*block,(b+1)*block) for b in perm])
        idx=idx[:Tuse]
        Ps=P[idx]
        tn=np.abs(np.diff(Ps,axis=0,prepend=Ps[:1,:]))/2.0
        nr=(Ps*Rf[:Tuse]).sum(axis=1)-tn.sum(axis=1)*COST-BORROW*np.clip(Ps,0,None).sum(axis=1)
        ser=pd.Series(nr,index=pos_book.index[:Tuse])
        ns=ser.dropna()
        if ns.std()>0 and ns.mean()/ns.std()*np.sqrt(252)>=real: cnt+=1
    return cnt/n, float(real)

def full_stats(r):
    r=r.dropna()
    mu,sd=r.mean(),r.std()
    sr=mu/sd*np.sqrt(252) if sd>0 else np.nan
    eq=(1+r).cumprod(); dd=(eq/eq.cummax()-1).min()
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    return dict(n=len(r), ann_geo=(eq.iloc[-1])**(252/len(r))-1, ann_arith=mu*252,
                vol=sd*np.sqrt(252), sr=sr, mdd=dd, negy=int((yr<0).sum()),
                worst=float(yr.min()) if len(yr) else 0.0, years=len(yr),
                first=str(r.index[0].date()), last=str(r.index[-1].date()),
                yearly={int(k):round(v*100,2) for k,v in yr.items()})

def halves_sr(r):
    r=r.dropna(); mid=r.index[len(r)//2]
    return full_stats(r[r.index<=mid])['sr'], full_stats(r[r.index>mid])['sr']

def flatten_gates(r):
    r=r.dropna()
    return dict(ac1=float(r.autocorr(1)), uniqR=float(r.round(10).nunique()/len(r)))

def corr_to(r, champ):
    j=pd.concat([r.rename('s'),champ.rename('c')],axis=1,join='inner').dropna()
    return float(j['s'].corr(j['c'])), len(j)

def gate_battery(name, r, pos_book, rets, champ, min_start='2008-01-01', verbose=True):
    r=r.dropna(); r=r[r.index>=pd.Timestamp(min_start)]
    st=full_stats(r); h1,h2=halves_sr(r)
    posb=pos_book.reindex(r.index).fillna(0.0)
    pl_p, pl_real=position_lag_block_p(posb, rets)
    fg=flatten_gates(r); corr,ncorr=corr_to(r,champ)
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    bad=yr[(yr<=-0.05)]
    gates=dict(gate_SR=(st['sr']>=0.6), gate_halves=(h1>=0.3 and h2>=0.3),
               gate_negy=(st['negy']<=2 and len(bad)==0),
               gate_scramble=(pl_p<0.05), gate_ac1=(fg['ac1']<0.5),
               gate_uniq=(fg['uniqR']>=0.08), gate_corr=(abs(corr)<0.15))
    npass=sum(gates.values())
    line=(f"{name}: SR {st['sr']:.3f} | ann_g {st['ann_geo']*100:.1f}% vol {st['vol']*100:.1f}% MDD {st['mdd']*100:.1f}% | "
          f"H1 {h1:.2f} H2 {h2:.2f} | negy {st['negy']} worst {st['worst']*100:.1f}% | poslag_p {pl_p:.3f} | "
          f"ac1 {fg['ac1']:.3f} uniqR {fg['uniqR']:.3f} | corr {corr:+.3f} (n={ncorr}) | GATES {npass}/7")
    if verbose: print(line)
    return dict(name=name, stats=st, h1=h1, h2=h2, poslag_p=pl_p, poslag_real=pl_real,
                ac1=fg['ac1'], uniqR=fg['uniqR'], corr=corr, n_corr=ncorr,
                gates=gates, npass=npass, line=line)

"""SKILL_ALPHAAGM shared harness — mechanics mirror frozen brwt engine (T+1, 6bps/side, borrow 0.5%/yr)."""
import numpy as np, pandas as pd

BPS = 0.0006  # per side
BORROW = 0.005  # per year on short notional

def sr_d(r): 
    r = r.dropna()
    return r.mean()/r.std(ddof=1)*np.sqrt(252) if r.std(ddof=1) > 0 else np.nan

def stats(r, label=""):
    r = r.dropna()
    r = r[r.index >= '2008-01-01']
    eq = (1+r).cumprod()
    dd = (eq/eq.cummax()-1).min()
    ann = eq.iloc[-1]**(252/len(r))-1
    ann_a = r.mean()*252
    yrs = sorted(set(r.index.year))
    yv = pd.Series([ (1+r[r.index.year==y]).prod()-1 for y in yrs ], index=yrs)
    negy = yv[yv < 0]
    # H1/H2 per-year halves, pooled
    h1 = r[r.index.month <= 6]; h2 = r[r.index.month >= 7]
    h1s = sr_d(h1); h2s = sr_d(h2)
    # ac1, uniqR (flatten gate)
    ac1 = r.autocorr(1)
    uniqR = r.nunique()/len(r)
    mx = r.abs().max()
    return dict(label=label, n=len(r), SR_d=round(sr_d(r),4), ann_geo=round(ann,4),
        ann_arith=round(ann_a,4), vol=round(r.std(ddof=1)*np.sqrt(252),4), MDD=round(dd,4),
        negy=len(negy), worst_yr=round(yv.min(),4), best_yr=round(yv.max(),4),
        H1=round(h1s,4), H2=round(h2s,4), ac1=round(ac1,4), uniqR=round(uniqR,4),
        max_day=round(mx,4))

def position_lag_scramble(pos, ret, nperm=200, block=10, seeds=(7,11,23)):
    """Charter gate: circularly shift POSITION series by 10d-block offsets, recompute PnL vs REAL returns with costs. p = P(perm SR >= real SR)."""
    pos = pos.dropna(); ret = ret.reindex(pos.index)
    def pnl(p):
        turnover = p.diff().abs().fillna(0.0)
        gross = p*ret
        cost = turnover*BPS
        borrow = BORROW/252*np.abs(p).clip(upper=0)  # charge on short only
        return (gross - cost - borrow).sum(axis=1) if hasattr(gross,'ndim') and gross.ndim>1 else (gross-cost-borrow)
    real = pnl(pos)
    real_sr = sr_d(real)
    ge = 0; tot = 0
    rng = np.random.default_rng(seeds[0])
    idx = pos.index
    for seed in seeds:
        rng = np.random.default_rng(seed)
        for _ in range(nperm):
            sh = int(rng.integers(1, max(2,len(idx)//block)))*block
            p2 = pd.concat([pos.iloc[-sh:], pos.iloc[:-sh]]).reset_index(drop=True)
            p2.index = idx
            if hasattr(pos,'ndim') and getattr(pos,'ndim',1)>1:
                pass
            s = sr_d(pnl(p2))
            ge += (s >= real_sr); tot += 1
    return real_sr, ge/tot

def champion_corr(r, champ):
    df = pd.concat([r, champ], axis=1, join='inner').dropna()
    return round(df.corr().iloc[0,1], 4)

def load_champion(path="/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv"):
    c = pd.read_csv(path, parse_dates=['date'], index_col='date')['ret']
    return c[c.index >= '2008-01-01']

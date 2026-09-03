"""HUNT_VOLOVERLAY lib: champion loader, overlay application (T+1 + incremental costs), stats."""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader')
import numpy as np, pandas as pd
sys.path.insert(0, '/Users/daxu/software/world-trader/campaign/harness')
from data import fred, ff_factors, ff_mom, closes  # harness helpers

ROOT = "/Users/daxu/software/world-trader"
CHAMP = f"{ROOT}/campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv"
COST = 6.0/1e4

def champion():
    df = pd.read_csv(CHAMP, index_col=0, parse_dates=True)
    r = df.iloc[:,0].astype(float)
    r = r[~r.index.duplicated(keep='last')].sort_index()
    return r

def stats(r):
    r = r.dropna()
    mu, sd = r.mean(), r.std()
    sr = mu/sd*np.sqrt(252) if sd>0 else 0
    eq = (1+r).cumprod(); dd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12) if m.std()>0 else 0
    ann08 = None
    rr = r[r.index>='2008-01-01']
    if len(rr)>100:
        ann08 = ((1+rr).prod()**(252/len(rr))-1)*100
    return dict(n=len(r), ann_geo=((1+r).prod()**(252/len(r))-1)*100, sr=sr, srm=srm,
                mdd=dd*100, negy=int((yr<0).sum()), worst=yr.min()*100, years=yr.size,
                ann08=ann08, vol=sd*np.sqrt(252)*100)

def halves(r):
    r = r.dropna(); mid = r.index[len(r)//2]
    return stats(r[r.index<=mid])['sr'], stats(r[r.index>mid])['sr']

def apply_overlay(r_champ, m_signal, mcap=1.0, cost_bps=6.0):
    """ret'_t = ret_t * m_{t-1} (T+1: signal uses data <= t-1). Incremental turnover
    |m_t - m_{t-1}| charged at 6bps one-side on champion gross notional proxy 1.0.
    m_signal: daily series indexed like r (value known at close of that date).
    Returns net overlaid series and the executed weight series m_exec."""
    m = m_signal.clip(upper=mcap, lower=0.0)
    m_exec = m.shift(1).reindex(r_champ.index).fillna(1.0)   # T+1
    r_ov_gross = r_champ * m_exec
    turn = m_exec.diff().abs().fillna(0.0)
    r_ov = r_ov_gross - turn*cost_bps/1e4
    return r_ov, m_exec

def poslag_scramble(r_base, m_signal, n=200, seed=0, mcap=1.0, cost_bps=6.0):
    """Circular-shift the OVERLAY WEIGHT series (position lag scramble), recompute overlaid
    PnL vs the REAL champion returns; p = fraction of permuted SR >= real overlaid SR.
    A degenerate/no-op overlay gives p=1.0; an informative one p<0.05."""
    rng = np.random.default_rng(seed)
    m = m_signal.clip(upper=mcap, lower=0.0)
    m_exec = m.shift(1).reindex(r_base.index).fillna(1.0)
    r_ov, _ = apply_overlay(r_base, m_signal, mcap, cost_bps)
    real = stats(r_ov)['sr']
    vals = m_exec.values.copy(); cnt = 0
    for _ in range(n):
        perm = np.roll(vals, rng.integers(1, len(vals)))
        ms = pd.Series(perm, index=r_base.index)
        r_p = r_base*ms - ms.diff().abs().fillna(0)*cost_bps/1e4
        if stats(r_p)['sr'] >= real: cnt += 1
    return cnt/n, real

def zscore(s, win, minp=None):
    minp = minp or win
    ma = s.rolling(win, min_periods=minp).mean(); sd = s.rolling(win, min_periods=minp).std()
    return (s-ma)/sd

def exz(s, win=756, minp=252):
    """expanding z-score vs trailing expanding mean/std."""
    mu = s.expanding(min_periods=minp).mean(); sd = s.expanding(min_periods=minp).std()
    return (s-mu)/sd

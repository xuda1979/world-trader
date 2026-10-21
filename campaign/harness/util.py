"""Leak-proof standard mechanics for all campaign sleeves. Import, don't reinvent."""
import numpy as np
import pandas as pd

def t1(signal_pos: pd.DataFrame, fwd_ret: pd.DataFrame) -> pd.DataFrame:
    """Position from signal at t, return booked at t+1.
    signal_pos: weights (can be +/-), indexed by decision date t (uses info <= t)
    fwd_ret:    NEXT-day returns aligned: fwd_ret.loc[t] = return earned from t to t+1
    Returns per-day pnl series (gross, before costs).
    Standard usage:
      pos = build_signal(close)             # decided with data <= t
      fr  = close.pct_change().shift(-1)    # return t->t+1 KNOWN at t+1
      pnl = (pos * fr).sum(axis=1)          # booked at t (i.e., realized t+1) - date as decision date
    NOTE: dates in the output are DECISION dates; the return realized is t->t+1.
    This embeds T+1 execution with no lookahead.
    """
    return (signal_pos.shift(0) * fwd_ret).sum(axis=1, min_count=1)

def fwd_returns(close: pd.DataFrame) -> pd.DataFrame:
    return close.pct_change().shift(-1)

def cost(pnl: pd.Series, gross_turnover: pd.Series, cost_bps: float = 6.0) -> pd.Series:
    """pnl (gross) minus 6bps * one-side turnover per day. gross_turnover = sum |Δw| / nav at t."""
    return pnl - gross_turnover.fillna(0) * cost_bps / 1e4

def turnover_of(pos: pd.DataFrame) -> pd.Series:
    return pos.diff().abs().sum(axis=1)

def vol_target(ret_net: pd.Series, target: float = 0.10, min_win: int = 60,
               lag: int = 1) -> pd.Series:
    """Scale to target ann vol using ONLY trailing data (expanding, min_win, lagged 1d)."""
    vol = ret_net.expanding(min_periods=min_win).std().shift(lag) * np.sqrt(252)
    lev = (target / vol).clip(0, 3).fillna(0)
    return ret_net * lev

def scramble_test(sig: pd.Series, ret: pd.Series, n: int = 200, seed: int = 7):
    """Real SR vs SR of circular-shifted signals. Returns (real_sr, p_value)."""
    sig = sig.dropna(); ret = ret.reindex(sig.index).dropna()
    sig = sig.reindex(ret.index)
    real = (sig * ret).mean() / (sig * ret).std() * np.sqrt(252) if (sig*ret).std() > 0 else 0
    rng = np.random.default_rng(seed)
    null = []
    v = sig.values
    for _ in range(n):
        k = rng.integers(1, len(v))
        s = pd.Series(np.roll(v, k), index=sig.index)
        ps = (s * ret).dropna()
        null.append(ps.mean()/ps.std()*np.sqrt(252) if ps.std() > 0 else 0)
    p = float((np.array(null) >= real).mean())
    return real, p

def halves_ok(ret_net: pd.Series, floor: float = 0.3):
    r = ret_net.dropna()
    mid = r.index[len(r)//2]
    h1, h2 = r[r.index <= mid], r[r.index > mid]
    sr = lambda x: x.mean()/x.std()*np.sqrt(252) if x.std() > 0 else 0
    return sr(h1), sr(h2)

def yearly(ret_net: pd.Series) -> pd.Series:
    r = ret_net.dropna()
    return r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)

def gates(ret_net: pd.Series, min_full: float = 0.6, min_half: float = 0.3,
          max_neg_years: int = 2, worst_year: float = -0.05) -> dict:
    r = ret_net.dropna()
    if len(r) < 1500:
        return dict(pass_=False, why=f"too short: n={len(r)}")
    sr = r.mean()/r.std()*np.sqrt(252) if r.std() > 0 else 0
    if sr < min_full:
        return dict(pass_=False, why=f"full SR {sr:.2f} < {min_full}")
    h1, h2 = halves_ok(r)
    if h1 < min_half or h2 < min_half:
        return dict(pass_=False, why=f"halves H1={h1:.2f} H2={h2:.2f} < {min_half}", sr=sr)
    yr = yearly(r)
    neg = yr[yr < 0]
    if len(neg) > max_neg_years or (len(neg) and neg.min() < worst_year):
        return dict(pass_=False, why=f"neg years {len(neg)} worst {neg.min()*100:.1f}%", sr=sr)
    return dict(pass_=True, sr=sr, h1=h1, h2=h2, worst=neg.min() if len(neg) else 0,
                neg_years=len(neg))

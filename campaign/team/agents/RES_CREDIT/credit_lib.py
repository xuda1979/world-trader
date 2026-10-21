"""RES_CREDIT hunt library — credit-spread engines on FRED OAS + credit ETFs (no browser).

Conventions mirror RES_BASIS/hunt_r1.py and GATES_CONTRACT_V2 §0: T+1 via shift(1),
trailing-only stats (shift(1)), vt via bt.engine.vol_target_scale on the gross path,
6.4bps FULL |dW| (cost_turnover), 0.5%/yr borrow on shorts. Battery: gates.run with
r=PER-UNIT returns and sig=effective weight so sig*r == held gross book (pre-cost).
"""
import sys

sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT = "/Users/daxu/software/world-trader"
ETFS = f"{ROOT}/tools/quant/data/more_etf"
FRED = f"{ROOT}/tools/quant/hedge_fund_strats/data_fred"
MOREFRED = f"{ROOT}/tools/quant/data/more_fred"
VT_TARGET, VT_CAP = 0.08, 3.0


def load_series(path):
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    s = s[~s.index.duplicated(keep='last')].sort_index()
    return s.replace([np.inf, -np.inf], np.nan)


def ret_of(path):
    return load_series(path).pct_change()


def zscore_trailing(x, win, shift_stats=True):
    """z of level vs trailing mean/sd; stats lag 1 (no same-day leak)."""
    m = x.rolling(win, min_periods=win // 2).mean()
    s = x.rolling(win, min_periods=win // 2).std()
    if shift_stats:
        m, s = m.shift(1), s.shift(1)
    z = (x - m) / s.replace(0, np.nan)
    return z.where(s.notna())


def oas_book(oas, win=63, invert=True, vt=True, target=VT_TARGET):
    """Credit-quality book: short credit risk when OAS is stretched (z<-0, cheapening edge
    = spread contraction momentum). Position = sign of expected OAS move: OAS rising =>
    short HY (risk-off), falling => long HY. rpu = HY ETF daily return."""
    z = zscore_trailing(oas, win=win)
    sig = np.sign(z) if invert else np.sign(-z)   # invert: OAS z>0 (cheapening) -> short credit
    idx = z.dropna().index
    sig = (sig if invert else -sig).reindex(idx).fillna(0.0)
    r_hy = ret_of(f"{ETFS}/HYG.csv").reindex(idx)
    W = pd.DataFrame({'a': sig}, index=idx)
    return net_of(W, r_hy.to_frame('a'), vt=vt, target=target)


def net_of(W, R, vt=True, target=VT_TARGET):
    """T+1 effective weights, trailing vt on gross, 6.4bps full |dW| + 0.5%/yr borrow."""
    We = W.shift(1).fillna(0.0)
    gross = (We * R.fillna(0.0)).sum(axis=1)
    if vt:
        s = vol_target_scale(gross.to_frame('g'), target=target, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    port = (We * R.fillna(0.0)).sum(axis=1)
    cost = cost_turnover(We, cost_bps=6.4)
    borr = borrow_cost(We)
    return (port - cost - borr).rename('ret'), We, gross

"""RES_VOL R1 hunt library — volatility-surface engines on CBOE indices (no browser).

Untested corners only (prior work: HUNT_VOL2 R1/R2 risk-off gates+overlays DEAD; A5 contango
already in champion; E3 event-timing DEAD). Pre-registered lanes:
  L1 VRP:  VIX (implied, prior close) vs trailing realized vol -> VRP z state.
  L2 RVX:  Russell-2000 vol on IWM (the R1 'dropped' lane; IWM now on disk).
  L3 SLOPE: VIX9D-VIX3M short-end slope INVERSION -> SHORT the underlying (never tested as
            a short book; R2 only de-risked the champion long book).
Conventions = GATES_CONTRACT_V2 sec-0 (RES_BASIS pattern): T+1 via shift(1), trailing-only
stats shift(1), vt trailing on gross (bt.engine.vol_target_scale), 6.4bps FULL |dW| one-side
(bt.engine.cost_turnover), 0.5%/yr borrow on shorts, battery r=per-unit returns, sig=weight.
"""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader")
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign")

import numpy as np
import pandas as pd
from bt.engine import vol_target_scale, cost_turnover, borrow_cost

ROOT = "/Users/daxu/software/world-trader"
VOLDIR = f"{ROOT}/tools/quant/data/more_vol"
PXDIR = f"{ROOT}/tools/quant/data/twelvedata"
ETDDIR = f"{ROOT}/tools/quant/data/more_etf"
TRIM_VVIX = pd.Timestamp('2007-01-01')
VT_TARGET, VT_CAP = 0.10, 3.0
_PX = {'SPY': f"{PXDIR}/SPY.csv", 'IWM': f"{PXDIR}/IWM.csv",
       'USO': f"{ETDDIR}/USO.csv", 'GLD': f"{ETDDIR}/GLD.csv"}


def load_vol(sym):
    """CBOE index close; VVIX trimmed at 2007-01-01 (2006 pilot junk prints, HUNT_VOL2 R1)."""
    s = pd.read_csv(f"{VOLDIR}/{sym}.csv", parse_dates=['date'], index_col='date')['close']
    s = s.astype(float).sort_index()
    s = s[~s.index.duplicated(keep='last')]
    if sym == 'VVIX':
        s = s[s.index >= TRIM_VVIX]
    return s


def load_px(sym):
    p = pd.read_csv(_PX[sym], parse_dates=['date'], index_col='date')['close'].astype(float)
    return p.sort_index()[~p.index.duplicated(keep='last')]


def realized_vol(px, lb=21):
    """Trailing realized vol (annualized) of daily pct returns; stat at t uses r_t (close t).
    Used ONLY against PRIOR-close VIX for the NEXT-day position (no lookahead by construction
    of the caller's shift)."""
    return px.pct_change().rolling(lb).std() * np.sqrt(252)


def vrp_series(vix, rv):
    """VRP = implied(prior close) - realized(trailing incl today); caller shifts for T+1."""
    return vix.shift(1) - rv


def slope_series(short, long_):
    """Short-end term slope log ratio (short/long - 1); stats are LEVELS so no extra shift
    needed beyond the caller's T+1 position shift."""
    j = pd.concat({'s': short, 'l': long_}, axis=1).dropna()
    return (j['s'] / j['l'] - 1.0)


def long_book(signal, px, thr=0.0, hold=5, to_zero=True, vt=True, return_rpu=False):
    """Long book on signal: in (w=target) when state on, out when off; optional de-lever to
    zero. T+1 = shift(1). target = 1.6 (champion-identical gross) then trailing vt.
    rpu = px.pct_change() so sig*rpu == held gross book (V2 sec-0 fixture-tested)."""
    on = (signal > thr).astype(float)
    if hold > 1:
        on = on.replace(0.0, np.nan).ffill(limit=hold - 1).fillna(0.0)
    lvl = pd.DataFrame({'a': on * 1.6, 'b': 0.0}, index=signal.index)
    r = px.pct_change().reindex(signal.index)
    rpu = r.fillna(0.0).rename('rpu')
    We = lvl.shift(1).fillna(0.0)
    if vt:
        s = vol_target_scale(pd.DataFrame({'g': (We['a'] * rpu.abs())}), target=VT_TARGET, cap=VT_CAP)['g']
        We = We.mul(s, axis=0)
    port = (We['a'] * rpu)
    net = port - cost_turnover(We[['a']], 6.4) - borrow_cost(We[['a']])
    if return_rpu:
        return net.rename('ret'), We, rpu
    return net.rename('ret'), We


def slope_book(slope, px, enter=0.0, exit_=0.0, hold=5, side='short', return_rpu=False):
    """Slope-inversion book: short-end steep (slope>enter) => SHORT the underlying (fast vol
    spike = demand for 9d puts = pre-crisis), else long/flat. Hysteresis enter/exit levels."""
    st = pd.Series(0.0, index=slope.index)
    cur = 0.0
    for i, v in enumerate(slope.values):
        if np.isfinite(v):
            if cur == 0.0 and v > enter:
                cur = 1.0
            elif cur == 1.0 and v <= exit_:
                cur = 0.0
        st.iloc[i] = cur
    a = (-st if side == 'short' else st) * 1.6
    lvl = pd.DataFrame({'a': a, 'b': 0.0}, index=slope.index)
    r = px.pct_change().reindex(slope.index)
    rpu = r.fillna(0.0).rename('rpu')
    We = lvl.shift(1).fillna(0.0)
    s = vol_target_scale(pd.DataFrame({'g': (We['a'] * rpu.abs())}), target=VT_TARGET, cap=VT_CAP)['g']
    We = We.mul(s, axis=0)
    net = (We['a'] * rpu) - cost_turnover(We[['a']], 6.4) - borrow_cost(We[['a']])
    if return_rpu:
        return net.rename('ret'), We, rpu
    return net.rename('ret'), We

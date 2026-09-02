"""HUNT_TAIL — left-tail / risk-on-off overlay engine library.
T+1 (shift 1), 6bps/side on turnover, vt-style scaling trailing-only, NO flattening."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL")
import numpy as np, pandas as pd

def build_overlay(pos, R, tgt=0.10, cap=2.0, cost=6e-4, minlen=60):
    """pos: signal series (in [-1,1] units), R: base strategy daily returns.
    Execution: pos1 = pos.shift(1) (T+1), pnl = pos1*R, costs on |d pos1|,
    then TRAILING vol-target scale (expanding min 60d, shift(1), clip cap).
    Returns (net Series, final position Series)."""
    pos = pos.fillna(0.0).astype(float)
    R = R.reindex(pos.index)
    pos1 = pos.shift(1).fillna(0.0)
    to = pos1.diff().abs(); to.iloc[0] = abs(pos1.iloc[0])
    net0 = pos1 * R.fillna(0.0) - to * cost
    vol = net0.expanding(min_periods=minlen).std()
    sc = (tgt / np.sqrt(252) / vol).clip(0, cap).shift(1).fillna(0.0)
    posf = pos1 * sc
    to2 = posf.diff().abs(); to2.iloc[0] = abs(posf.iloc[0])
    net = (posf * R.fillna(0.0) - to2 * cost).dropna()
    return net, posf

def data_vix():
    p = "/Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred_new/VIXCLS.csv"
    df = pd.read_csv(p, index_col=0, parse_dates=True)
    s = pd.to_numeric(df.iloc[:, 0], errors="coerce")
    return s[~s.index.duplicated(keep="last")].sort_index()

def data_spx():
    """SPY close-to-close returns (SPY tracks the SPX that VIX is computed from;
    same-day close pairing, execution T+1). Twelve_big panel 2006-09..2026-08."""
    p = "/Users/daxu/software/world-trader/tools/quant/data/twelve_big/SPY.csv"
    df = pd.read_csv(p, index_col="date", parse_dates=["date"])
    c = df["close"].astype(float)
    return c.pct_change()

def hysteresis_pos(z, th, hyst):
    """state=1 when z<th (risk-on), 0 when z>th+hyst (risk-off)."""
    zv = z.values; out = np.zeros(len(zv)); st = 0.0
    for t in range(len(zv)):
        zz = zv[t]
        if not np.isnan(zz):
            if zz < th: st = 1.0
            elif zz > th + hyst: st = 0.0
        out[t] = st
    return pd.Series(out, index=z.index)

def maxdd_pct(r):
    eq = (1 + r.dropna()).cumprod()
    return float((eq/eq.cummax()-1).min()*100)

def dd_profile(r):
    """MaxDD and worst-3y-subwindow MaxDD (aligned-3y windows, step 21d)."""
    r = r.dropna(); eq = (1+r).cumprod(); dd = (eq/eq.cummax()-1)
    worst3 = dd.rolling(756).min().max()*100  # max over windows of min dd
    return dict(mdd=float(dd.min()*100), w3=float(worst3))

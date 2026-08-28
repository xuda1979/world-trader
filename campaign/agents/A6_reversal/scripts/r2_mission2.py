"""A6 r2 mission 2: LO reversal rescue — beta-conditioned losers, 130/30 small short, cadence 7-10.
Base (r1): k=10 reversal, long worst decile-20, ivol filter, cadence 5, vol-tgt 10 -> SR 0.63,
3 neg yrs {2008 -5.6, 2018 -1.3, 2022 -5.3}. Need negYr<=2 AND worst>-5%."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from lib6 import closes, stats, halves_sr, vol_target

px = closes()
rets = px.pct_change(fill_method=None).clip(-0.5, 0.5)
hist = px.notna().cumsum()
univ = px.notna() & (hist >= 120) & rets.notna()
mkt_ret = rets.where(univ).mean(axis=1)

# trailing 252d beta to EW mkt (min 126)
def beta_to(rets, x, win=252, mo=126):
    m_y = rets.rolling(win, min_periods=mo).mean()
    m_x = x.rolling(win, min_periods=mo).mean()
    m_yx = (rets.mul(x, axis=0)).rolling(win, min_periods=mo).mean()
    return (m_yx - m_y.mul(m_x, axis=0)).div(x.rolling(win, min_periods=mo).var() + 1e-12, axis=0)

beta = beta_to(rets, mkt_ret)
beta_med = beta.quantile(0.5, axis=1)          # cross-sectional median beta
lowb = beta.le(beta_med, axis=0)               # low-beta half
# 60d idio vol filter (10/90 trims) as in r1
def roll_idio_vol(rets, x, win=60, minobs=40):
    m_r = rets.rolling(win, min_periods=minobs).mean()
    m_x = x.rolling(win, min_periods=minobs).mean()
    m_rx = (rets.mul(x, axis=0)).rolling(win, min_periods=minobs).mean()
    beta_ = (m_rx - m_r.mul(m_x, axis=0)).div(x.rolling(win, min_periods=minobs).var(), axis=0)
    resid = rets.sub(beta_.mul(x, axis=0))
    return resid.rolling(win, min_periods=minobs).std()

ivol = roll_idio_vol(rets, mkt_ret)
iv_lo = ivol.quantile(0.10, axis=1); iv_hi = ivol.quantile(0.90, axis=1)
iv_ok = ivol.ge(iv_lo, axis=0) & ivol.le(iv_hi, axis=0)
vols = rets.rolling(20).std()

def weights(k=10, frac=0.2, cadence=5, ok=None, score=None, inv=None, short_frac=None):
    """Long worst `frac` by `score` (more negative = bigger loser) among ok; optional short best short_frac."""
    r = score.where(ok)
    q_lo = r.quantile(frac, axis=1)
    L = r.le(q_lo, axis=0) & ok
    lw = L.mul(inv.where(ok)).div(L.mul(inv.where(ok)).sum(axis=1).clip(lower=1e-9), axis=0)
    w = lw.copy()
    if short_frac:
        q_hi = r.quantile(1 - short_frac, axis=1)
        S = r.ge(q_hi, axis=0) & ok
        sw = S.mul(inv.where(ok)).div(S.mul(inv.where(ok)).sum(axis=1).clip(lower=1e-9), axis=0)
        w = w - short_frac * sw   # short small notional
    arr = w.values.copy(); cur = arr[0]
    for i in range(len(arr)):
        if i % cadence == 0: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def backtest(W, tag, vt=0.10, long_only_cash=True):
    if long_only_cash:  # long-only: weights sum to 1 (or 1-short when 130/30); remainder cash
        pass
    gross = (W.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = gross - turn * 6 / 1e4
    if vt: net, _ = vol_target(net, vt)
    net = net.dropna()
    s = stats(net); h = halves_sr(net)
    yr = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
    neg = {int(y): round(v*100,1) for y,v in yr.items() if v < 0}
    okg = s['sr']>=0.6 and h['H1']>=0.3 and h['H2']>=0.3 and s['neg_years']<=2 and s['worst_year']>-5
    print(f"{tag:52s} SR={s['sr']:.2f} H1={h['H1']:.2f} H2={h['H2']:.2f} negYr={s['neg_years']}{neg} {'<<== GATES' if okg else ''}")
    return net

print("=== base replication + beta-conditioning grid ===")
okb = univ & lowb
inv1 = pd.DataFrame(1.0, index=rets.index, columns=rets.columns)
for tag, ok in [("base(all-beta, ivol-filter)", univ & iv_ok), ("low-beta half (no ivol)", okb), ("low-beta AND ivol-filter", okb & iv_ok)]:
    for cad in [5, 7, 10]:
        backtest(weights(k=10, frac=0.2, cadence=cad, ok=ok, score=rets.rolling(10).sum(), inv=1/vols), f"{tag} cad{cad}")
print("=== 130/30: long worst 20% (low-beta) + short best 10/20/30% at low cadence ===")
for sf in [0.10, 0.20, 0.30]:
    for cad in [7, 10]:
        backtest(weights(k=10, frac=0.2, cadence=cad, ok=univ & iv_ok, score=rets.rolling(10).sum(), inv=1/vols, short_frac=sf), f"LO-beta + short{sf:.0%} cad{cad}", long_only_cash=False)

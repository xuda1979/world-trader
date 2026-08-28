"""A6 r3 idea 3: residual momentum PURE L/S (top/bottom tercile), MA150-gated, monthly cadence.
   idea 3b: gated resid-mom LONG book + trailing-beta market hedge (market-neutral form)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r3_lib import rets_px, gates, corr_to_champion, champion_mix, sr_monthly
from lib6 import stats, halves_sr, vol_target
from idea234_engine import resid_momentum, weights_long

rets, px = rets_px()
ok = rets.notna() & (px.notna().cumsum() >= 120)
mkt = px.mean(axis=1)
_, resid_mom, _ = resid_momentum()

def carry(w, cadence):
    arr = np.array(w.values); cur = arr[0]
    for i in range(len(arr)):
        if (np.arange(len(arr)) % cadence == 0)[i]: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def ls_weights(score, ok, frac=1/3, cadence=21):
    r = score.where(ok)
    q_lo = r.quantile(frac, axis=1); q_hi = r.quantile(1-frac, axis=1)
    L = r.ge(q_hi, axis=0) & ok; S = r.le(q_lo, axis=0) & ok
    lw = L.div(L.sum(axis=1).clip(lower=1), axis=0); sw = S.div(S.sum(axis=1).clip(lower=1), axis=0)
    return carry(0.5*lw - 0.5*sw, cadence)

def gate_dual(confirm=10, dd_entry=20, dd_thresh=-0.15, ma=150):
    ma_s = mkt.rolling(ma, min_periods=ma//2).mean()
    dd = (mkt / mkt.rolling(252, min_periods=126).max() - 1.0)
    above = (mkt > ma_s).values; below = (mkt < ma_s*0.98).values
    n = len(mkt); state = np.zeros(n); s = 0; cnt = 0
    for i in range(n):
        if np.isnan(ma_s.iloc[i]): continue
        need = dd_entry if (not np.isnan(dd.iloc[i]) and dd.iloc[i] < dd_thresh) else confirm
        if s == 1 and below[i]: s = 0; cnt = 0
        elif s == 0:
            cnt = cnt + 1 if above[i] else 0
            if cnt >= need: s = 1
        state[i] = s
    return pd.Series(state, index=mkt.index)

def book_ret(W, start="2007-01-01"):
    gross = (W.shift(1) * rets).sum(axis=1)[start:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
    return (gross - turn*6/1e4), turn

G = gate_dual()

print("=== IDEA 3: resid-mom PURE L/S tercile, monthly, gate variants ===")
Wls = ls_weights(resid_mom, ok, 1/3, 21)
for gname, g in [("ungated", pd.Series(1.0, index=mkt.index)), ("MA150c10dd20", G)]:
    net, turn = book_ret(Wls.mul(g, axis=0))
    r_vt, _ = vol_target(net.dropna(), 0.10)
    s = stats(r_vt); h = halves_sr(r_vt)
    print(f"  LS-tercile {gname:14s} SR={s['sr']:5.2f} H1={h['H1']:5.2f} H2={h['H2']:5.2f} negYr={s['neg_years']} worst={s['worst_year']:6.1f}%")
# leg attribution
for leg, Wl in [("LONG-top3", Wls.clip(lower=0)), ("SHORT-bot3", Wls.clip(upper=0))]:
    net, _ = book_ret(Wl)
    s = stats(net.dropna()); print(f"    {leg}: raw net SR={s['sr']:.2f}")

print("=== IDEA 3b: gated resid-mom LONG + trailing-beta market hedge ===")
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
net_long_raw, turn_long = book_ret(W.mul(G, axis=0))   # gate multiplies weights -> turnover of gated path
# hedge: trailing 252d beta of the long book vs equal-weight panel, hedge return overlay, 6bps on |dbeta| turnover
book = net_long_raw.dropna()
mr = mkt.pct_change(fill_method=None).clip(-0.5, 0.5)
b = book.rolling(252, min_periods=126).cov(mr) / mr.rolling(252, min_periods=126).var()
b = b.shift(1).clip(0, 2)  # trailing only, applied t+1
hedge_pnl = b * mr
hedge_cost = (b - b.shift(1)).abs() * 6 / 1e4
mn = (book - hedge_pnl - hedge_cost).dropna()
for tag, r in [("long gated (r2 leg1, control)", book), ("beta-hedged raw", mn)]:
    s = stats(r); h = halves_sr(r)
    yr = r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
    neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
    print(f"  {tag:30s} SR={s['sr']:5.2f} H1={h['H1']:5.2f} H2={h['H2']:5.2f} negYr={s['neg_years']}{neg} worst={s['worst_year']:6.1f}%")
mn_vt, _ = vol_target(mn, 0.10)
cm, _ = champion_mix()
print(f"  corr(hedged VT, champion) monthly = {corr_to_champion(mn_vt):.2f}")
okc, info = gates(mn_vt, "beta-hedged gated resid-mom VT10", W=W.mul(G, axis=0), rets=rets, scramble=False)

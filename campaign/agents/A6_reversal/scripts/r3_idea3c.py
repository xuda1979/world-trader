"""A6 r3 idea 3c: beta-hedged gated resid-mom with CONDITIONED hedge (trailing-data only).
   Hedge active only when: gate ON (we hold equity exposure) AND trailing mkt vol elevated.
   Grid: beta window x hedge frac x vol condition. All signals trailing; T+1."""
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

G = gate_dual()
W = weights_long(resid_mom, ok, frac=1/3, cadence=21)
Wg = W.mul(G, axis=0)
gross = (Wg.shift(1) * rets).sum(axis=1)["2007-01-01":]
turn = (Wg.shift(1) - Wg.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
book = (gross - turn*6/1e4).dropna()

mr = mkt.pct_change(fill_method=None).clip(-0.5, 0.5)

def beta_trail(win, mo):
    return (book.rolling(win, min_periods=mo).cov(mr) / mr.rolling(win, min_periods=mo).var()).shift(1).clip(0, 2)

# trailing vol conditions (ONLY trailing data)
v21 = mr.rolling(21).std()
v_exp_med = v21.expanding(min_periods=252).median().shift(1)   # expanding median of 21d vol
v252_q66 = v21.rolling(252, min_periods=126).quantile(0.66).shift(1)  # trailing 1y 66th pct
v504_q66 = v21.rolling(504, min_periods=252).quantile(0.66).shift(1)
conds = {"always": pd.Series(1.0, index=book.index),
         "gateON": G.reindex(book.index).fillna(0.0),
         "gateON&v21>expmed": (G.reindex(book.index).fillna(0.0) * (v21 > v_exp_med).astype(float).reindex(book.index).fillna(0.0)),
         "gateON&v21>1y66": (G.reindex(book.index).fillna(0.0) * (v21 > v252_q66).astype(float).reindex(book.index).fillna(0.0)),
         "gateON&v21>2y66": (G.reindex(book.index).fillna(0.0) * (v21 > v504_q66).astype(float).reindex(book.index).fillna(0.0))}

rows = []
for wname, win, mo in [("b126", 126, 63), ("b252", 252, 126)]:
    b = beta_trail(win, mo)
    for hfrac in [0.5, 0.75, 1.0]:
        for cname, cval in conds.items():
            hedge_pnl = (hfrac * b * cval) * mr
            hedge_cost = (hfrac * b * cval).diff().abs() * 6 / 1e4
            r = (book - hedge_pnl - hedge_cost).dropna()
            r_vt, _ = vol_target(r, 0.10)
            s = stats(r_vt); h = halves_sr(r_vt)
            yr = r_vt.groupby(r_vt.index.year).apply(lambda x:(1+x).prod()-1)
            neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
            corr = corr_to_champion(r_vt)
            passg = s["sr"]>=0.6 and h["H1"]>=0.3 and h["H2"]>=0.3 and s["neg_years"]<=2 and s["worst_year"]>-5.0 and corr<0.3
            rows.append((s["sr"], wname, hfrac, cname, h["H1"], h["H2"], s["neg_years"], s["worst_year"], corr, passg))
rows.sort(reverse=True)
for sr, wname, hfrac, cname, h1, h2, ny, wy, corr, passg in rows[:14]:
    print(f"  {wname} hf={hfrac:4.2f} {cname:20s} SR={sr:5.2f} H1={h1:5.2f} H2={h2:5.2f} negYr={ny} worst={wy:6.1f}% corr={corr:4.2f} {'<-- candidate' if passg else ''}")

"""A6 r3 idea 3e: HONEST hedged LO-reversal. FIX: hedge position known at t-1 earns day-t return.
   r(t) = book(t) - hh(t-1)*mr(t) - |hh(t-1)-hh(t-2)|*6bps. All conditions inside hh (trailing)."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r3_lib import rets_px, gates, corr_to_champion, champion_mix, sr_monthly, signal_scramble_p
from lib6 import stats, halves_sr, vol_target

rets, px = rets_px()
ok = rets.notna() & (px.notna().cumsum() >= 120)
iv = rets.rolling(63, min_periods=40).std()
mkt = px.mean(axis=1)
mr = mkt.pct_change(fill_method=None).clip(-0.5, 0.5)

def carry(w, cadence):
    arr = np.array(w.values); cur = arr[0]
    for i in range(len(arr)):
        if (np.arange(len(arr)) % cadence == 0)[i]: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def lo_weights(score, ok, frac, cadence, iv=None):
    r = score.where(ok)
    L = r.le(r.quantile(frac, axis=1), axis=0) & ok
    if iv is None:
        w = L.div(L.sum(axis=1).clip(lower=1), axis=0)
    else:
        inv = 1.0 / iv.where(ok)
        w = (L * inv).div((L * inv).sum(axis=1).clip(lower=1e-9), axis=0)
    return carry(w, cadence)

def book_of(W):
    gross = (W.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    return (gross - turn*6/1e4), turn

print("=== hedged grid, FIXED timing (hh shifted 1d; condition+beta both trailing) ===")
rows = []
for kn, k in [("k10", 10), ("k21", 21)]:
    score = px.pct_change(k, fill_method=None)
    for frac, fl in [(0.1, "d10")]:
        W = lo_weights(score, ok, frac, 21, iv=iv)
        book, _ = book_of(W)
        idx = book.index
        b126 = (book.rolling(126, min_periods=63).cov(mr) / mr.rolling(126, min_periods=63).var()).shift(1).clip(0, 2)
        b252 = (book.rolling(252, min_periods=126).cov(mr) / mr.rolling(252, min_periods=126).var()).shift(1).clip(0, 2)
        ma200 = mkt.rolling(200, min_periods=100).mean()
        below200 = (mkt < ma200).astype(float)          # condition at t
        ma150 = mkt.rolling(150, min_periods=75).mean()
        below150 = (mkt < ma150).astype(float)
        v21 = mr.rolling(21).std()
        vmed = v21.expanding(min_periods=252).median()
        hivol = (v21 > vmed).astype(float)
        conds = {"always": pd.Series(1.0, index=idx),
                 "below200": below200.reindex(idx).fillna(0.0),
                 "below150": below150.reindex(idx).fillna(0.0),
                 "below200|hl": (below200 * hivol).reindex(idx).fillna(0.0)}
        for bn, b in [("b126", b126), ("b252", b252)]:
            for hf in [0.5, 0.75, 1.0]:
                for cn, cv in conds.items():
                    hh = (hf * b * cv).reindex(idx).fillna(0.0)   # decided at t (uses data<=t)
                    r = (book - hh.shift(1) * mr.reindex(idx).fillna(0.0)
                         - hh.shift(1).diff().abs().fillna(0.0) * 6/1e4).dropna()
                    r_vt, _ = vol_target(r, 0.10)
                    s = stats(r_vt); h = halves_sr(r_vt)
                    yr = r_vt.groupby(r_vt.index.year).apply(lambda x:(1+x).prod()-1)
                    neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
                    corr = corr_to_champion(r_vt)
                    passg = (s["sr"]>=0.6 and h["H1"]>=0.3 and h["H2"]>=0.3 and s["neg_years"]<=2
                             and s["worst_year"]>-5.0 and corr<0.3)
                    rows.append((s["sr"], kn, bn, hf, cn, h["H1"], h["H2"], s["neg_years"], s["worst_year"], corr, passg))
rows.sort(reverse=True)
for sr, kn, bn, hf, cn, h1, h2, ny, wy, corr, passg in rows[:16]:
    print(f"  {kn} {bn} hf={hf:4.2f} {cn:12s} SR={sr:5.2f} H1={h1:5.2f} H2={h2:5.2f} negYr={ny} worst={wy:6.1f}% corr={corr:4.2f} {'<-- CANDIDATE' if passg else ''}")

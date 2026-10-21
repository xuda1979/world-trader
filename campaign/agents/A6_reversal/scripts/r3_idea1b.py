"""A6 r3 idea 1b/3d: LONG-side reversal monthly cadence (never tested; r1 weekly was SR 0.63),
   + market-hedged variants (hedge = short EW-panel via trailing beta), gates + corr to champion."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r3_lib import rets_px, gates, corr_to_champion, champion_mix, sr_monthly
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
    L = r.le(r.quantile(frac, axis=1), axis=0) & ok   # LOW past return = loser = buy
    if iv is None:
        w = L.div(L.sum(axis=1).clip(lower=1), axis=0)
    else:
        inv = 1.0 / iv.where(ok)
        w = (L * inv).div((L * inv).sum(axis=1).clip(lower=1e-9), axis=0)
    return carry(w, cadence)

def bt(W, tag, hedge=None, scramble=False):
    gross = (W.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = (gross - turn*6/1e4)
    if hedge is not None:
        net = net - hedge["pnl"] - hedge["cost"]
    net = net.dropna()
    r_vt, _ = vol_target(net, 0.10)
    corr = corr_to_champion(r_vt)
    oka, info = gates(r_vt, "", W=W, rets=rets, scramble=scramble, verbose=False)
    g = info["gates"]
    fails = [k for k, v in g.items() if not v]
    print(f"  {tag:44s} SR={info['sr']:5.2f} H1={info['halves']['H1']:5.2f} H2={info['halves']['H2']:5.2f} "
          f"negYr={len(info['neg'])}{info['neg']} worst={info['worst']:6.1f}% corr={corr:4.2f} "
          f"{'*** PASS ***' if oka else 'fail:'+str(fails)}")
    return r_vt, oka, info, corr

print("=== IDEA 1b: LONG-only reversal, monthly cadence 21 (and 10 for ref) ===")
best = None
for kn, k in [("k5", 5), ("k10", 10), ("k21", 21)]:
    score = px.pct_change(k, fill_method=None)
    for frac, fl in [(0.1, "d10"), (0.2, "q20")]:
        for cad in ([21] if k == 21 else [10, 21]):
            W = lo_weights(score, ok, frac, cad, iv=iv)
            r, oka, info, corr = bt(W, f"LO-rev {kn} {fl} cad{cad}")
            if oka and (best is None or info["sr"] > best[2]["sr"]):
                best = (W, f"LOrev_{kn}_{fl}_cad{cad}", info, corr, r)

print("=== IDEA 3d: best LO-rev + conditioned market hedge (trailing beta, gate/vol conditions) ===")
score = px.pct_change(10, fill_method=None)
W0 = lo_weights(score, ok, 0.1, 21, iv=iv)
gross = (W0.shift(1) * rets).sum(axis=1)["2007-01-01":]
turn = (W0.shift(1) - W0.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
book = (gross - turn*6/1e4).dropna()
b252 = (book.rolling(252, min_periods=126).cov(mr) / mr.rolling(252, min_periods=126).var()).shift(1).clip(0, 2)
b126 = (book.rolling(126, min_periods=63).cov(mr) / mr.rolling(126, min_periods=63).var()).shift(1).clip(0, 2)
v21 = mr.rolling(21).std()
vmed = v21.expanding(min_periods=252).median().shift(1)
# reversal book has no regime gate; hedge conditions: always / high-vol only / 200dma-regime
ma200 = mkt.rolling(200, min_periods=100).mean().reindex(book.index)
regime = (mkt.reindex(book.index) > ma200).astype(float)
conds = {"always": pd.Series(1.0, index=book.index),
         "v21>expmed": (v21 > vmed).astype(float).reindex(book.index).fillna(0.0),
         "mkt<ma200": 1.0 - regime}
for bn, b in [("b126", b126), ("b252", b252)]:
    for hf in [0.5, 1.0]:
        for cn, cv in conds.items():
            hh = (hf * b * cv)
            r = (book - hh * mr - hh.diff().abs() * 6/1e4).dropna()
            r_vt, _ = vol_target(r, 0.10)
            corr = corr_to_champion(r_vt)
            s = stats(r_vt); h = halves_sr(r_vt)
            yr = r_vt.groupby(r_vt.index.year).apply(lambda x:(1+x).prod()-1)
            neg = {int(y): round(v*100,1) for y,v in yr.items() if v<0}
            passg = s["sr"]>=0.6 and h["H1"]>=0.3 and h["H2"]>=0.3 and s["neg_years"]<=2 and s["worst_year"]>-5.0 and corr<0.3
            print(f"  hedge {bn} hf={hf:3.1f} {cn:12s} SR={s['sr']:5.2f} H1={h['H1']:5.2f} H2={h['H2']:5.2f} "
                  f"negYr={s['neg_years']}{neg} worst={s['worst_year']:6.1f}% corr={corr:4.2f} {'<-- candidate' if passg else ''}")

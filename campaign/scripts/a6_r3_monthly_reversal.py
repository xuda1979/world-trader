"""A6 r3 idea 1: MONTHLY xs reversal L/S (21d cadence, quintiles, inv-vol) — costs ~4x lower than r1 weekly.
   idea 2: residual reversal (5-21d reversal on FF4 residuals), monthly cadence."""
import sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
import numpy as np, pandas as pd
from r3_lib import rets_px, gates, signal_scramble_p, corr_to_champion, champion_mix, sr_monthly
from lib6 import stats, halves_sr, vol_target

rets, px = rets_px()
ok = rets.notna() & (px.notna().cumsum() >= 120)
iv = rets.rolling(63, min_periods=40).std()  # 63d idio-ish vol proxy for weights

def carry(w, cadence):
    arr = np.array(w.values); cur = arr[0]
    for i in range(len(arr)):
        if (np.arange(len(arr)) % cadence == 0)[i]: cur = arr[i]
        else: arr[i] = cur
    return pd.DataFrame(arr, index=w.index, columns=w.columns)

def ls_weights(score, ok, frac, cadence, iv=None):
    r = score.where(ok)
    q_lo = r.quantile(frac, axis=1); q_hi = r.quantile(1 - frac, axis=1)
    L = r.le(q_lo, axis=0) & ok; S = r.ge(q_hi, axis=0) & ok
    if iv is None:
        lw = L.div(L.sum(axis=1).clip(lower=1), axis=0); sw = S.div(S.sum(axis=1).clip(lower=1), axis=0)
    else:
        inv = 1.0 / iv.where(ok)
        lw = (L * inv).div((L * inv).sum(axis=1).clip(lower=1e-9), axis=0)
        sw = (S * inv).div((S * inv).sum(axis=1).clip(lower=1e-9), axis=0)
    return carry(0.5 * lw - 0.5 * sw, cadence)

def bt(W, tag, start="2007-01-01", scramble=False):
    gross = (W.shift(1) * rets).sum(axis=1)[start:]
    turn = (W.shift(1) - W.shift(2)).abs().sum(axis=1)[start:].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    r_vt, _ = vol_target(net, 0.10)
    s = stats(r_vt)
    print(f"  {tag:40s} SR={s['sr']:5.2f} turn/d={turn.mean()*1e4:5.1f}bps", end="")
    okall, info = gates(r_vt, "", W=W, rets=rets, scramble=scramble, verbose=False)
    print(f" -> gates {'PASS' if okall else 'fail'}", info["gates"] if not okall else "")
    return r_vt, net, okall, info

print("=== IDEA 1: monthly (cadence 21) xs reversal L/S, k-day past return, quintiles/deciles, inv-vol ===")
m12 = px.pct_change(21, fill_method=None)
m5 = px.pct_change(5, fill_method=None)
m10 = px.pct_change(10, fill_method=None)
results = {}
for kname, score in [("k21", m12), ("k10", m10), ("k5", m5)]:
    for frac, fl in [(0.2, "q20"), (0.1, "d10")]:
        for ivw, ivn in [(iv, "ivw"), (None, "ew")]:
            W = ls_weights(score, ok, frac, 21, iv=ivw)
            r_vt, net, okall, info = bt(W, f"rev {kname} {fl} {ivn} cad21")
            results[(kname, fl, ivn)] = (r_vt, W, info)

print("=== leg attribution on best config ===")
r_vt, W, _ = results[("k21", "q20", "ivw")]
L_only = W.clip(lower=0); S_only = W.clip(upper=0)
for leg, Wl in [("LONG(low-past-ret)", L_only), ("SHORT(high-past-ret)", S_only)]:
    gross = (Wl.shift(1) * rets).sum(axis=1)["2007-01-01":]
    turn = (Wl.shift(1) - Wl.shift(2)).abs().sum(axis=1)["2007-01-01":].fillna(0.0)
    net = (gross - turn * 6 / 1e4).dropna()
    s = stats(net); print(f"  {leg}: raw net SR={s['sr']:.2f}")

print("=== IDEA 2: residual reversal (FF4 residual 5/10/21d), monthly cadence ===")
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from idea234_engine import resid_momentum
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/A6_reversal/scripts")
from harness_shim import ff_factors, ff_mom
fac = ff_factors().join(ff_mom(), how="outer").sort_index()
fac.columns = [c.strip() for c in fac.columns]
fac = fac[["Mkt-RF", "SMB", "HML", "Mom"]].fillna(0.0)
rets2, px2 = rets, px
f = fac.reindex(px2.index).fillna(0.0)
def beta_of(y, x, win=252, mo=126):
    m_y = y.rolling(win, min_periods=mo).mean(); m_x = x.rolling(win, min_periods=mo).mean()
    m_yx = (y.mul(x, axis=0)).rolling(win, min_periods=mo).mean()
    return (m_yx - m_y.mul(m_x, axis=0)).div(x.rolling(win, min_periods=mo).var() + 1e-12, axis=0)
mkt_r = rets2.mean(axis=1)
b1 = beta_of(rets2, mkt_r); b2 = beta_of(rets2, f["SMB"]); b3 = beta_of(rets2, f["HML"]); b4 = beta_of(rets2, f["Mom"])
resid = rets2.sub(b1.mul(mkt_r, axis=0)).sub(b2.mul(f["SMB"], axis=0)).sub(b3.mul(f["HML"], axis=0)).sub(b4.mul(f["Mom"], axis=0))
for kk in [5, 10, 21]:
    score = resid.rolling(kk, min_periods=max(3, kk//2)).sum()
    for frac, fl in [(0.2, "q20"), (0.1, "d10")]:
        W = ls_weights(score, ok, frac, 21, iv=iv)
        r_vt, net, okall, info = bt(W, f"resid-rev k{kk} {fl} ivw cad21")

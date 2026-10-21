#!/usr/bin/env python3
"""G10: strict lev<=1.6 (HARD cap on the book multiplier too): per-sleeve cap K s.t.
lev mean ~1.26 (max 1.49 pre-boost), then boost capped at 1.6 hard:
scw = min(1 + w*stress, 1.6). Configs A/B and BAL. Reports + saves CSVs."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
from ht_lib import ROOT, POOL, EXEC, SHORTF, stats_r, corr_to
from champion_build import load, vt
from overlay_lib import data_vix, dd_profile
from pandas.tseries.holiday import USFederalHolidayCalendar

cal = USFederalHolidayCalendar(); hol = set(cal.holidays(start='2006-01-01', end='2026-12-31').date)
def sn(p):
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in hol) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

vix = data_vix()
v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std())

def build(K, TGT, THR, w, th, hardcap=1.6):
    S = {}
    for n, p in POOL.items():
        r = sn(p)
        vol = r.rolling(60).std().shift(1) * np.sqrt(252)
        s = (0.10 / vol).clip(upper=K); s[vol.isna()] = 0
        S[n] = s
    Sn = pd.DataFrame(S).dropna(how='all')
    capW = Sn / len(POOL)
    V = {}
    for n in POOL:
        r = sn(POOL[n])
        V[n] = r * Sn[n].fillna(0) - capW[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
    Vn = pd.DataFrame(V)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b = vt(blend, TGT)[0]
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    stress = (z > th).astype(float).reindex(b.index).fillna(0.0)
    scw = (1 + w*stress).shift(1).fillna(1.0).clip(upper=hardcap)
    r_out = r_out * scw - scw.diff().abs().fillna(0.0) * 6e-4
    htb = pd.Series(0.0, index=Sn.index)
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = Sn[n]/len(POOL) * sc * scw * sf
            htb = htb + gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)
    r = (r_out - htb/252).dropna()
    lev = (Sn.mul((sc*scw), axis=0).abs().mean(axis=1)).reindex(r.index)
    return r, lev

l16 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11L16_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
rA, levA = build(1.5, 0.07, 0.04, 0.25, 1.0)
rB, levB = build(1.5, 0.091, 0.03, 0.25, 1.0)
rBal = ((rA+rB)/2).dropna(); levBal = ((levA.reindex(rBal.index)+levB.reindex(rBal.index))/2)

def report(tag, r, lev, save=None):
    s = stats_r(r); dd = dd_profile(r)
    print(f"[{tag}] ann={s['ann_geo']:.2f}% SR_d={s['sr_d']:.3f} SR_m={s['sr_m']:.3f} MaxDD={s['mdd']:.2f}% "
          f"w3y={dd['w3']:.2f}% negyr={s['negyr']}/{s['nyr']} worst={s['worst']:.2f}% best={s['best']:.2f}% "
          f"OOS17+={s['oos17_ann']:.2f}% lev_mean={lev.mean():.4f} lev_max={lev.max():.4f}")
    if save:
        r.to_frame('ret').to_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_TAIL/sleeves/{save}")
    return s

report("HARD1.6 SAFE", rA, levA, "HT_TAIL_LEV16_SAFE_daily.csv")
report("HARD1.6 AGGR", rB, levB, "HT_TAIL_LEV16_AGGR_daily.csv")
s = report("HARD1.6 BAL", rBal, levBal, "HT_TAIL_LEV16_BAL_daily.csv")
c, n = corr_to(rBal, l16); print("corr BAL vs L16:", round(c,4))
print("BAL yearly:", s['yearly'])
print("BAL dd:", dd_profile(rBal))
eq=(1+rBal).cumprod(); ddser=(eq/eq.cummax()-1); tr=ddser.idxmin()
print("trough", tr.date(), "peak", eq.loc[:tr].idxmax().date())

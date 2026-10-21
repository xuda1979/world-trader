#!/usr/bin/env python3
"""G7: INTEGRATED builder — HONEST11 base engines at honest vol targets (no post-hoc scalar)
+ HT_TAILBOOST stress-boost overlay (sc = 1 + w*1{vix21_z252 > th}, shift(1) T+1, costs on
the boost turnover). All-in, with borrow charged on scaled short gn (honest11_build recipe).
Reports leverage (mean per-sleeve |scale|), full stats, worst-3y DD, all gate metrics,
corr to committed L16. Target: ann as high as possible s.t. mean lev <= 1.6, mdd <= 7,
negyrs 0, profit>=0 every year. boost helps return path in stress w/o leverage."""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd, itertools
from ht_lib import ROOT, POOL, EXEC, SHORTF, stats_r
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

Sn = pd.DataFrame({n: vt(sn(p), 0.10)[1] for n, p in POOL.items()}).dropna(how='all')
capW = Sn / len(POOL)
CACHE = {n: sn(POOL[n]) for n in POOL}
N = len(POOL)

vix = data_vix()
v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std())

def build(TGT, THR, w, th, lev_cap=None):
    V = {}
    for n in POOL:
        V[n] = vt(CACHE[n], 0.10)[0] - capW[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
    Vn = pd.DataFrame(V)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    if lev_cap is not None:
        gs = gs.clip(upper=lev_cap)
        b = blend * gs.fillna(0)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    # TAILBOOST overlay on the full book
    stress = (z > th).astype(float).reindex(b.index).fillna(0.0)
    scw = (1 + w*stress).shift(1).fillna(1.0)
    r_out = r_out * scw
    r_out = r_out - scw.diff().abs().fillna(0.0) * 6e-4
    # borrow on per-sleeve short gn (scaled by throttle * boost like book gross)
    htb = pd.Series(0.0, index=Sn.index)
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = Sn[n]/N * sc * scw * sf
            htb = htb + gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)
    r = (r_out - htb/252).dropna()
    lev = (Sn.mul((sc*scw), axis=0).abs().mean(axis=1)).reindex(r.index)
    return r, lev

rows = []
for TGT, THR in ((0.07,0.04),(0.091,0.03)):
    for w, th in ((0.0,1.0),(0.15,1.0),(0.25,1.0),(0.35,1.0),(0.5,1.0),(0.25,0.75),(0.5,0.75)):
        r, lev = build(TGT, THR, w, th)
        s = stats_r(r); dd = dd_profile(r)
        tag = f"A{round(TGT,3)}/thr{THR} w{w} th{th}"
        rows.append(dict(tag=tag, ann=s['ann_geo'], srd=s['sr_d'], srm=s['sr_m'], mdd=s['mdd'],
                         w3=dd['w3'], negyr=s['negyr'], worst=s['worst'], best=s['best'],
                         oos=s['oos17_ann'], lev_mean=lev.mean(), lev_max=lev.max()))
df = pd.DataFrame(rows)
df.to_csv(f"{ROOT}/campaign/agents/loop_team/HUNT_TAIL/logs/g7_integrated.csv", index=False)
pd.set_option('display.width', 250)
print(df.to_string())
print()
print("constraints: lev_mean<=1.6, mdd>=-7, negyr=0")
print(df[(df.lev_mean <= 1.6) & (df.mdd >= -7) & (df.negyr == 0)].sort_values('ann', ascending=False).to_string())

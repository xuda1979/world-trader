#!/usr/bin/env python3
"""G6: HONEST11-L16 BALANCED leverage audit + honest-scaling of the tail overlay idea.
Leverage published def: EW of per-sleeve |vt scale| (mean). Also global-vt x persleeve.
Then: honest constrained rebuild = HONEST11 base engines at vtA=0.07/vtB=0.091 (NO extra
scaling) + TAILBOOST overlay (sc=1+0.25*1{vix21_z252>1}) applied T+1 with costs — 
does it add ann / cut DD at mean persleeve scale <=1.6?"""
import sys; sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/HUNT_TAIL"); sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
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

def base(TGT, THR):
    V = {}
    for n in POOL:
        V[n] = vt(CACHE[n], 0.10)[0] - capW[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
    Vn = pd.DataFrame(V)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b = vt(blend, TGT)[0]
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    htb = pd.Series(0.0, index=Sn.index)
    for n in POOL:
        sf = SHORTF[n]
        if sf > 0:
            gn = Sn[n]/N * sc * sf
            htb = htb + gn*(0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2)
    return (r_out - htb/252).dropna(), b, sc

A, bA, scA = base(0.07, 0.04)
B, bB, scB = base(0.091, 0.03)
BAL = ((A+B)/2).dropna()
common = BAL.index
levA = Sn.reindex(common).abs().mean(axis=1)
print("L16 BAL rebuilt: mean per-sleeve scale = %.4f (max %.4f)  -> leverage<=1.6 mean: %s"
      % (levA.mean(), levA.max(), levA.mean() <= 1.6))
s = stats_r(BAL); print("stats:", {k: (round(v,3) if isinstance(v,float) else v) for k,v in s.items() if k not in ('yearly',)})

# tail boost overlay ON TOP of the L16-style champion: b_FINAL = b_champ * (1 + w*stress)
vix = data_vix()
v = vix.rolling(21).mean()
z = ((v - vix.rolling(252).mean())/vix.rolling(252).std())
stress = (z > 1.0).astype(float).reindex(common).fillna(0.0)
for w in (0.15, 0.25, 0.35, 0.5):
    scw = 1 + w*stress
    scw1 = scw.shift(1).fillna(1.0)          # T+1
    r_boost = (BAL * scw1)
    to = scw1.diff().abs().fillna(0.0) * 6e-4
    r_net = (r_boost - to).dropna()
    r_net = r_net[common.min():]
    s2 = stats_r(r_net); dd2 = dd_profile(r_net)
    # leverage: boost only raises gross in stress periods; mean multiple:
    mean_mult = scw1.mean()
    lev_adj = levA * scw1                    # per-sleeve scale approx scales by same factor
    print(f"TAILBOOST w={w}: ann={s2['ann_geo']:6.2f}% SR_d={s2['sr_d']:.3f} SR_m={s2['sr_m']:.3f} "
          f"MaxDD={s2['mdd']:6.2f}% w3y={dd2['w3']:6.2f}% negyr={s2['negyr']}/{s2['nyr']} worst={s2['worst']:6.2f}% "
          f"mean_sc={mean_mult:.4f} mean_levpersleeve={lev_adj.mean():.4f} max_levpersleeve={lev_adj.max():.4f}")

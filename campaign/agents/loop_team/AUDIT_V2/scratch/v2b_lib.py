#!/usr/bin/env python3
"""AUDIT_V2 rebuild lib v2 — calendar variants + slot-weight V2 recipe. Fresh code."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_allweeks(p):
    """keep ALL Mon-Fri raw rows (no federal keep-list)."""
    r = load(p).dropna()
    keep = np.array([d.dayofweek < 5 for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

def build(TGT, THR, PS=0.08, SLOT=0.10, REBAL='exact', CAL='allweeks'):
    sn = sn_allweeks
    SnP = pd.DataFrame({n: vt(sn(p), PS)[1] for n, p in POOL11.items()}).dropna(how='all')
    capWP = SnP / 11
    V = {}; S = {}
    for n in POOL11:
        r = sn(POOL11[n])
        v, s = vt(r, PS)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r11 = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL == 'formula':
        reb = Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)
        r11 = r11 - reb.reindex(r11.index).fillna(0)*6e-4
    elif REBAL == 'exact':
        pos = Sd.mul(gs, axis=0).mul(sc, axis=0)
        reb = pos.diff().abs().sum(axis=1)/11
        r11 = r11 - reb.reindex(r11.index).fillna(0)*6e-4
    # borrow: terms on SnP/11*sc — on allweeks calendar, federal rows now HAVE their raw print
    terms = []
    for n in POOL11:
        sf = SHORTF[n]
        if sf > 0:
            terms.append(SnP[n]/11 * sc * sf * (0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r11 = r11 - htb.reindex(r11.index).fillna(0)/252
    r11 = r11.dropna(how='all')
    return r11, dict(Sd=Sd, gs=gs, sc=sc, SnP=SnP, blend=blend, capWP=capWP)

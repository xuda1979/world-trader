#!/usr/bin/env python3
"""AUDIT_V2 rebuild lib v3: V2 hypothesis — 13 sleeves, rows-kept Mon-Fri calendar
(union of raw prints), no federal smearing. Fresh code."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_raw(p):
    """raw series, Mon-Fri rows kept as printed (no federal smearing)."""
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

def build13(TGT, THR, PS=0.08, SLOT=0.10, REBAL='formula', MEAN='skipna', CAL='union'):
    R11 = {n: sn_raw(p) for n, p in POOL11.items()}
    Rnew = {n: sn_raw(p) for n, p in NEW.items()}
    allR = pd.DataFrame({**R11, **Rnew})
    if CAL == 'union':
        idx = allR.dropna(how='all').index
    elif CAL == 'any11':
        idx = allR[R11.keys()].dropna(how='all').index
    allR = allR.reindex(idx)
    # scale books from vt on the raw (no-smear) series
    SnP = pd.DataFrame({n: vt(R11[n], PS)[1] for n in POOL11}).reindex(idx)
    capWP = SnP / 11
    V = {}
    for n in POOL11:
        v, s = vt(R11[n], PS)
        V[n] = v.reindex(idx) - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
    Vn = pd.DataFrame(V)
    Sd = pd.DataFrame({n: vt(R11[n], PS)[1] for n in POOL11}).reindex(idx)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    if MEAN == 'skipna':
        blend = Vn.mean(axis=1)          # pandas mean skips NaN by default
    else:
        blend = Vn.fillna(0).mean(axis=1)
    blend = blend[blend.index >= '2006-10-01']
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
    terms = []
    for n in POOL11:
        sf = SHORTF[n]
        if sf > 0:
            terms.append(SnP[n]/11 * sc * sf * (0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r11 = r11 - htb.reindex(r11.index).fillna(0)/252
    r11 = r11.dropna(how='all')
    return r11, dict(Sd=Sd, gs=gs, sc=sc, SnP=SnP, blend=blend, allR=allR)

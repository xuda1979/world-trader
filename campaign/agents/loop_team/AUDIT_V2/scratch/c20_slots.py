#!/usr/bin/env python3
"""Slot-weight construction: per-sleeve vt-0.08 pool of 13, slot weights {1.0 x11, 0.10 x2},
global vt + throttle + exact position-path reb + borrow. Multiple sub-variants."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt

def sn_raw(p):
    r = load(p).dropna()
    return r[r.index.dayofweek < 5]

ALL13 = dict(POOL11, **NEW)
SLOT = 0.10
WSLOT = {**{n: 1.0 for n in POOL11}, **{n: SLOT for n in NEW}}
NSUM = sum(WSLOT.values())  # 11.2

def build(TGT, THR, PS=0.08, smear=False, exact=True, newslots=True, capw_adj=True):
    def sm(p):
        return L_sn(p) if smear else sn_raw(p)
    def L_sn(p):
        from v2lib import HOL
        r = load(p).dropna()
        keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
        out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
        for i in range(len(r)):
            cu += v[i]
            if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
        return out.iloc[:ki]
    R13 = {n: sm(p) for n, p in ALL13.items()}
    union = pd.concat(R13.values(), axis=1).dropna(how='all').index
    SnP = pd.DataFrame({n: vt(R13[n], PS)[1] for n in ALL13}).reindex(union)
    capWP = SnP / len(POOL11)
    V = {}; S = {}
    for n in ALL13:
        v, s = vt(R13[n], PS)
        if capw_adj:
            v = v - capWP[n].diff().abs().fillna(0)*((EXEC.get(n, 6.0)-6.0)/1e4)
        V[n] = v.reindex(union); S[n] = s.reindex(union)
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = (SnP * pd.Series(WSLOT)).div(SnP.mul(pd.Series(WSLOT)).sum(axis=1), axis=0).fillna(0)
    if newslots:
        blend = (Vn * pd.Series(WSLOT)).sum(axis=1) / NSUM
    else:
        blend = Vn.mean(axis=1)
    blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    slotv = pd.Series(WSLOT)
    if exact:
        pos = Sd.mul(slotv, axis=1).mul(gs, axis=0).mul(sc, axis=0)
        reb = pos.diff().abs().sum(axis=1)/NSUM
    else:
        reb = Sd.mul(slotv, axis=1).diff().abs().sum(axis=1)/NSUM + gs.diff().abs().fillna(0)
    r_out = r_out - reb.reindex(r_out.index).fillna(0)*6e-4
    terms = []
    for n in POOL11:
        sf = SHORTF[n]
        if sf > 0:
            terms.append(SnP[n]*slotv[n]/NSUM * sc * sf * (0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
    return r_out.dropna(how='all'), dict(Sd=Sd, gs=gs, sc=sc, SnP=SnP, blend=blend, pos=pos if exact else None)

if __name__ == "__main__":
    ROOT = "/Users/daxu/software/world-trader"
    v2  = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    v2s = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_SAFE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    v2a = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_AGGRESSIVE_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
    for smear in [False, True]:
        for exact in [True, False]:
            A, _ = build(0.07, 0.04, smear=smear, exact=exact)
            Bp, _ = build(0.091, 0.03, smear=smear, exact=exact)
            BAL = ((A+Bp)/2).dropna()
            out = []
            for nm, old, cand in [("SAFE", v2s, A), ("BAL", v2, BAL), ("AGGR", v2a, Bp)]:
                j = pd.concat([old.rename('o'), cand.rename('n')], axis=1, join='inner').dropna()
                out.append(f"{nm}: n={len(j)} max|d|={float((j.o-j.n).abs().max()):.3e}")
            print(f"smear={smear} exact={exact} || " + " | ".join(out))

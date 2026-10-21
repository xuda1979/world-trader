#!/usr/bin/env python3
"""Cost-identity audit: r = b*t? - (tw + dsc + reb)*6e-4 - htb/252, term by term.
Reconstruct components from committed FIX BAL (pre-reb path) and compare V2 = f(FIX) row-wise.
KEY QUESTION: v2_hol == -(tw + dsc + reb)*6e-4 - htb/252 exactly? Which cost explains -5.8bp mean?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
from v2lib import POOL as POOL11, NEW, EXEC, SHORTF, load, vt, HOL

def sn(p):
    r = load(p).dropna()
    keep = np.array([(d.dayofweek < 5 and d.date() not in HOL) for d in r.index])
    out = pd.Series(0.0, index=r.index[keep]); cu = 0.0; ki = 0; v = r.values
    for i in range(len(r)):
        cu += v[i]
        if keep[i]: out.iloc[ki] = cu; cu = 0.0; ki += 1
    return out.iloc[:ki]

PS = 0.08
SnP = pd.DataFrame({n: vt(sn(POOL11[n]), PS)[1] for n in POOL11}).dropna(how='all')
capWP = SnP / 11
V = {}; S = {}
for n in POOL11:
    v, s = vt(sn(POOL11[n]), PS)
    V[n] = v - capWP[n].diff().abs().fillna(0)*((EXEC[n]-6.0)/1e4)
    S[n] = s
Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
b07, gs07 = vt(blend, 0.07)
b091, gs091 = vt(blend, 0.091)
def thr(b, THR):
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    return pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index)
scA = thr(b07, 0.04); scB = thr(b091, 0.03)
# committed FIX BAL is r(A); check identity to recover exact reb charge used
fix = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
dsc = scA.diff().abs()*0.5
base = b07*scA - (tw.reindex(b07.index).fillna(0) + dsc.fillna(0))*6e-4
terms = []
for n in POOL11:
    sf = SHORTF[n]
    if sf > 0:
        terms.append(SnP[n]/11*scA*sf*(0.005 + (0.03 if n=='dualmom' else 0.0)*0.2))
htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
# recover implied reb from FIX
imp = (base - htb/252 - fix).dropna()   # implied reb*6e-4
print(f"implied reb cost mean {imp.mean():.3e} -> reb mean {imp.mean()/6e-4:.4f}")
# formula reb
reb_formula = (Sd.diff().abs().sum(axis=1)/11 + gs07.diff().abs().fillna(0)).reindex(imp.index).fillna(0)
print(f"formula reb vs implied: max|d| {float((reb_formula - imp/6e-4).abs().max()):.6f}")
# exact pos-path reb
posA = Sd.mul(gs07, axis=0).mul(scA, axis=0)
reb_exact = posA.diff().abs().sum(axis=1)/11
print(f"exact reb vs implied: max|d| {float((reb_exact.reindex(imp.index).fillna(0) - imp/6e-4).abs().max()):.6f}")

# now federal rows: what are tw/dsc/htb there?
v2 = pd.read_csv("/Users/daxu/software/world-trader/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
fed = [d for d in v2.index if d.date() in HOL]
twf = tw.reindex(fed); dscf = dsc.reindex(fed); htbf = (htb/252).reindex(fed)
print("\nfed rows: tw mean %.6f | dsc mean %.6f | htb/252 mean %.6f" % (twf.mean(), dscf.mean(), htbf.mean()))
# candidate v2_hol = -(tw + dsc + reb)*6e-4 - htb/252 with reb=exact? formula?
for rname, reb in [("formula", (Sd.diff().abs().sum(axis=1)/11 + gs07.diff().abs().fillna(0))), ("exact", posA.diff().abs().sum(axis=1)/11)]:
    cand = -(tw.reindex(fed).fillna(0) + dsc.reindex(fed).fillna(0) + reb.reindex(fed).fillna(0))*6e-4 - htbf.fillna(0)
    print(f"{rname}: v2_hol - cand max|d| = {float((v2[fed] - cand).abs().max()):.3e} mean|d| {float((v2[fed] - cand).abs().mean()):.3e}")

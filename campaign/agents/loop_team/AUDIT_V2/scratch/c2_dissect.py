#!/usr/bin/env python3
"""AUDIT_V2 check 1b: dissect V2 vs FIX. Regenerate 11-pool FIX independently (fresh code),
then analyze V2-FIX difference + row-set differences to reverse-engineer the V2 recipe."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import v2lib as L
ROOT = "/Users/daxu/software/world-trader"

def build11(TGT, THR, PS=0.08, REBAL='formula'):
    """My independent FIX rebuild. REBAL: 'formula' (committed FIX) or 'exact' (position-path)."""
    SnP = pd.DataFrame({n: L.vt(L.sn(p), PS)[1] for n, p in L.POOL.items()}).dropna(how='all')
    capWP = SnP / 11
    V = {}; S = {}
    for n in L.POOL:
        r = L.sn(L.POOL[n])
        v, s = L.vt(r, PS)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((L.EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = L.vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc
    dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL == 'formula':
        reb = Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)
        r_out = r_out - reb.reindex(r_out.index).fillna(0)*6e-4
    elif REBAL == 'exact':
        # exact position path: pos_i = scale_i * global * throttle, one-side turnover
        pos = Sd.mul(gs, axis=0).mul(sc, axis=0)   # per-sleeve scaled position (pre capW)
        reb = pos.diff().abs().sum(axis=1)/11
        r_out = r_out - reb.reindex(r_out.index).fillna(0)*6e-4
    terms = []
    for n in L.POOL:
        sf = L.SHORTF[n]
        if sf > 0:
            terms.append(SnP[n]/11 * sc * sf * (0.005 + (0.03 if n == 'dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True)
    r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
    return r_out.dropna(how='all'), dict(Sd=Sd, gs=gs, sc=sc, SnP=SnP, blend=blend)

# verify my FIX rebuild vs committed FIX BAL
fixA, fxA = build11(0.07, 0.04)
fixB, fxB = build11(0.091, 0.03)
fixBAL = ((fixA+fixB)/2).dropna()
old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
j = pd.concat([old.rename('old'), fixBAL.rename('new')], axis=1, join='inner').dropna()
print(f"my FIX BAL rebuild vs committed: overlap {len(j)}  max|diff| = {float((j.old-j.new).abs().max()):.3e}")

v2 = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST13V2_BALANCED_daily.csv", index_col=0, parse_dates=True).iloc[:,0]
only_v2 = v2.index.difference(fixBAL.index)
only_fix = fixBAL.index.difference(v2.index)
print(f"\nV2 rows {len(v2)}, FIX rows {len(fixBAL)}; only-in-V2 {len(only_v2)}, only-in-FIX {len(only_fix)}")
dd = pd.Index(sorted(only_v2))
print("only-in-V2 sample:", [str(d.date()) for d in dd[:10]])
import collections
print("only-in-V2 by weekday:", collections.Counter(d.dayofweek for d in dd))
print("only-in-V2 by year:", collections.Counter(d.year for d in dd))

# V2 - FIX on common rows
jc = pd.concat([v2.rename('v2'), fixBAL.rename('fix')], axis=1, join='inner').dropna()
diff = jc.v2 - jc.fix
print(f"\ncommon rows {len(jc)}: V2-FIX diff mean {diff.mean():.3e} std {diff.std():.3e} max|.| {diff.abs().max():.3e}")

# regression of diff on the two new sleeve returns (per-unit)
dies = L.load(L.NEW['diescrack']); cfx = L.load(L.NEW['CFX4'])
X = pd.DataFrame({'dies': dies, 'cfx': cfx}).reindex(jc.index).fillna(0.0)
Amat = np.column_stack([X.dies, X.cfx, np.ones(len(X))])
coef, res, rank, sv = np.linalg.lstsq(Amat, diff.values, rcond=None)
resid = diff.values - Amat @ coef
print(f"diff ~ w_dies*dies + w_cfx*cfx + const: w_dies={coef[0]:.6f} w_cfx={coef[1]:.6f} const={coef[2]:.3e} resid_max={np.abs(resid).max():.3e}")

# also try vt-scaled (0.08) versions of new sleeves
def vt08(r):
    return L.vt(r, 0.08)[0]
dies08 = vt08(dies); cfx08 = vt08(cfx)
X2 = pd.DataFrame({'dies08': dies08, 'cfx08': cfx08}).reindex(jc.index).fillna(0.0)
A2 = np.column_stack([X2.dies08, X2.cfx08, np.ones(len(X2))])
coef2, _, _, _ = np.linalg.lstsq(A2, diff.values, rcond=None)
resid2 = diff.values - A2 @ coef2
print(f"vt-scaled: w_dies={coef2[0]:.6f} w_cfx={coef2[1]:.6f} const={coef2[2]:.3e} resid_max={np.abs(resid2).max():.3e}")
# raw unscaled with intercept
X3 = pd.DataFrame({'dies': dies, 'cfx': cfx}).reindex(jc.index).fillna(0.0)
for w in [0.0455, 0.04545, 1/22, 0.0417, 0.0082]:
    pred = w*(X.dies + X.cfx)
    print(f"w={w:.5f}: max|diff - w*(dies+cfx)| = {float((diff-pred).abs().max()):.3e}")

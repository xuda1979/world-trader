import sys, json
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/scripts")
import numpy as np, pandas as pd
import champion_build as cb

# 12-pool = 16-pool minus dropped
POOL12 = {k: v for k, v in cb.POOL.items() if k not in ("H21_f5", "H21_br", "A5r2", "A5r4")}
assert len(POOL12) == 12, len(POOL12)

def construct20(TGT, THR, FR=0.5, LB=126, START="2007-01-01"):
    V, S = {}, {}
    for n, p in POOL12.items():
        r = cb.load(p)
        v, s = cb.vt(r, 0.10)
        V[n] = v; S[n] = s
    Vn = pd.DataFrame(V); Sn = pd.DataFrame(S)
    W = Sn.div(Sn.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1)
    blend = blend[blend.index >= START]
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, _ = cb.vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod()
    rm = eq.rolling(LB).max().shift(1)
    tdd = eq.shift(1) / rm - 1
    sc = pd.Series(np.where(tdd < -THR, FR, 1.0), index=b.index)
    b = b * sc
    dsc = sc.diff().abs() * 0.5
    tot = tw.reindex(b.index).fillna(0) + dsc.fillna(0)
    return (b - tot * cb.COST).dropna()

A = construct20(0.065, 0.04)
B = construct20(0.08, 0.03)
BAL = ((A + B) / 2).dropna()

for name, r in [("SAFE", A), ("AGGRESSIVE", B), ("BALANCED", BAL)]:
    old = pd.read_csv(f"/Users/daxu/software/world-trader/campaign/results/GOAL100_CHAMPION20Y_{name}_daily.csv",
                      index_col=0, parse_dates=True).iloc[:, 0]
    j = pd.concat([old.rename("old"), r.rename("new")], axis=1, join="inner").dropna()
    md = float((j.old - j.new).abs().max())
    ident = md < 1e-12 and len(j) == len(old)
    print(f"{name}: n_rebuilt={len(r)} n_committed={len(old)} max|diff|={md:.3e} -> {'BYTE-MATCH' if ident else 'DEVIATION'}")
    print(f"   stats(rebuilt): {cb.stats(r)}")
    print(f"   span: {r.index.min().date()} .. {r.index.max().date()}  ({(r.index.max()-r.index.min()).days/365.25:.1f}y)")
json.dump({"byte_match_task1": "done"}, open("/Users/daxu/software/world-trader/campaign/agents/E5_champ20y/work/t1.json", "w"))

import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, ROOT

_, sa = build(0.07,0.04); _, sb = build(0.091,0.03)
def reb_of(s, TGT):
    Sd, gs = s['Sd'], s['gs']
    return (Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0))
rebA, rebG = reb_of(sa,0.07), reb_of(sb,0.091)
BAL = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))['BAL']
w = (rebA.index>='2008-01-01')
rebB = (rebA+rebG)/2
print(f"BAL reb turnover 2008+: mean {rebB[w].mean()*1e4:.2f} bp/d -> drag {rebB[w].mean()*6e-4*252*100:.3f}%/yr (p95 day {rebB[w].quantile(.95)*6e-4*1e4:.2f}bp)")

# exact-charge counterfactual on BAL: r_BAL_exact = BAL - (exactB - rebB)*6e-4
def exact_of(s):
    Sd, gs, sc = s['Sd'], s['gs'], s['sc']
    pos = Sd.mul(gs*sc, axis=0)
    return pos.diff().abs().sum(axis=1)/11
exB = (exact_of(sa)+exact_of(sb))/2
extra = (exB-rebB).reindex(BAL.index).fillna(0)*6e-4
r_ex = BAL - extra
eq=(1+r_ex).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
ann=(1+r_ex).prod()**(252/len(r_ex))-1; srd=r_ex.mean()/r_ex.std()*np.sqrt(252)
yr=r_ex.groupby(r_ex.index.year).apply(lambda x:(1+x).prod()-1); yr8=yr[yr.index>=2008]
print(f"BAL with EXACT pos-path reb charge: ann {ann*100:.2f}%  SR_d {srd:.3f}  MDD {mdd:.2f}%  neg08 {(yr8<0).sum()}/{yr8.size} worst {yr8.min()*100:.2f}%  (extra drag {extra[extra.index>='2008-01-01'].mean()*252*100:.3f}%/yr)")

# Aug-2026 tail impact
tail = BAL['2026-08-01':]
print(f"\nAug-2026 tail: n={len(tail)} sum {tail.sum()*100:.2f}%  daily mean {tail.mean()*1e4:.2f}bp; last 3 rows (a6r7-only): {[(str(d.date()), round(float(BAL[d])*1e4,1)) for d in tail.index[-3:]]}")
r_comp = BAL[(BAL.index>='2008-01-01')&(BAL.index<='2026-07-31')]
print(f"comparable-window ann(geo) {((1+r_comp).prod()**(252/len(r_comp))-1)*100:.2f}% vs full-span {(((1+BAL).prod())**(252/len(BAL))-1)*100:.2f}% -> tail+stub effect {(45.74-44.82):.2f}pp approx")

# worst 3y subwindow MDD (756 trading days), BAL comparable window
best = 0
for i in range(0, len(r_comp)-756, 21):
    x = r_comp.iloc[i:i+756]; eqx=(1+x).cumprod(); m=(eqx/eqx.cummax()-1).min()
    if m < best: best = m; bd = (x.index[0].date(), x.index[-1].date())
print(f"worst 756d-subwindow MDD: {best*100:.2f}% ({bd[0]}..{bd[1]})")

# partial-day weighting note: Good Friday 2024 — blend reweights to present sleeves
print(f"\nGF 2024-03-29 (1 sleeve): BAL {float(BAL[pd.Timestamp('2024-03-29')])*1e4:.1f}bp (blend mean of 1 sleeve = full weight to carryv2, not 1/11)")

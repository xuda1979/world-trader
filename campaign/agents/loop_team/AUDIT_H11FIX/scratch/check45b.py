import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, ROOT

# CHECK 4 BAL
_, sa = build(0.07,0.04); _, sb = build(0.091,0.03)
ga = sa['Sd'].abs().sum(axis=1)/N if False else sa['Sd'].abs().sum(axis=1)/11
ga = sa['Sd'].abs().sum(axis=1)/11 * sa['gs']; gb = sb['Sd'].abs().sum(axis=1)/11 * sb['gs']
g = ((ga+gb)/2).dropna(); g08 = g[g.index>='2008-01-01']
print(f"[BAL] 2008+: mean {g08.mean():.3f}x  median {g08.median():.3f}x  p95 {g08.quantile(.95):.3f}x  max {g08.max():.3f}x  days>1.6x: {(g08>1.6).mean()*100:.1f}%")
yrg = g08.groupby(g08.index.year).mean()
print("     yearly means: " + " ".join(f"{y}:{v:.2f}" for y,v in yrg.items()))

# CHECK 5 exact numbers table for all three variants (as committed span)
st = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
print("\n--- CHECK 5 goal battery (as committed span 2006-10-02..2026-08-27) ---")
for v in ['SAFE','BALANCED','AGGRESSIVE']:
    r = st[v]
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
    srd=r.mean()/r.std()*np.sqrt(252); m=(1+r).resample('ME').prod()-1; srm=m.mean()/m.std()*np.sqrt(12)
    ann=(1+r).prod()**(252/len(r))-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1); yr8=yr[yr.index>=2008]
    print(f"{v}: ann {ann*100:.2f}%  SR_d {srd:.3f}  SR_m {srm:.3f}  MDD {mdd:.2f}%  neg08 {(yr8<0).sum()}/{yr8.size}  negALL {(yr<0).sum()}/{yr.size} (worst yr {yr.min()*100:.2f}%)")

# worst single days + flatten gate on BAL
r = st['BAL']; sd = r.std()
imax, imin = r.idxmax(), r.idxmin()
print(f"\nBAL flatten: ac1 {r.autocorr(1):.4f}  uniqR {r.nunique()/len(r):.4f}  nzero {(r==0).sum()}")
print(f"BAL max day +{r[imax]*100:.2f}% ({imax.date()}, +{r[imax]/sd:.1f} sd)  min day {r[imin]*100:.2f}% ({imin.date()}, {r[imin]/sd:.1f} sd)")
print(f"BAL daily sd {sd*100:.3f}%  annualized vol {sd*np.sqrt(252)*100:.2f}%")

# exact-position-path reb cost decomposition on BAL legs
for tag, s in [('SAFE',sa),('AGGR',sb)]:
    Sd, gs, sc = s['Sd'], s['gs'], s['sc']
    pos = Sd.mul(gs*sc, axis=0)
    exact = pos.diff().abs().sum(axis=1)/11
    form  = Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)
    w = slice('2008-01-01', None)
    e = exact[(exact.index>='2008-01-01')]; f = form[(form.index>='2008-01-01')]
    print(f"[{tag}] exact pos-path turnover {e.mean()*1e4:.1f} bp/d -> {e.mean()*6e-4*252*100:.3f}%/yr vs builder formula {f.mean()*1e4:.1f} bp/d -> {f.mean()*6e-4*252*100:.3f}%/yr  (undercharge factor {e.mean()/f.mean():.2f}x)")
    # charged drag that WOULD result on ann if exact charge applied (approx: subtract extra)

import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, ROOT
st = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
print("--- CHECK 5 goal battery (as committed span 2006-10-02..2026-08-27) ---")
for v,k in [('SAFE','A'),('BALANCED','BAL'),('AGGRESSIVE','B')]:
    r = st[k]
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
    srd=r.mean()/r.std()*np.sqrt(252); m=(1+r).resample('ME').prod()-1; srm=m.mean()/m.std()*np.sqrt(12)
    ann=(1+r).prod()**(252/len(r))-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1); yr8=yr[yr.index>=2008]
    print(f"{v}: ann {ann*100:.2f}%  SR_d {srd:.3f}  SR_m {srm:.3f}  MDD {mdd:.2f}%  neg08 {(yr8<0).sum()}/{yr8.size}  negALL {(yr<0).sum()}/{yr.size} (worst yr {yr.min()*100:.2f}%)")
r = st['BAL']; sd = r.std()
imax, imin = r.idxmax(), r.idxmin()
print(f"\nBAL flatten: ac1 {r.autocorr(1):.4f}  uniqR {r.nunique()/len(r):.4f}  nzeros {(r==0).sum()}")
print(f"BAL max day +{r[imax]*100:.2f}% ({imax.date()}, +{r[imax]/sd:.1f} sd)  min day {r[imin]*100:.2f}% ({imin.date()}, {r[imin]/sd:.1f} sd)  sd {sd*100:.3f}%/d")
for tag,(TGT,THR) in [('SAFE',(0.07,0.04)),('AGGR',(0.091,0.03))]:
    _, s = build(TGT,THR)
    Sd, gs, sc = s['Sd'], s['gs'], s['sc']
    pos = Sd.mul(gs*sc, axis=0)
    exact = pos.diff().abs().sum(axis=1)/11
    form  = Sd.diff().abs().sum(axis=1)/11 + gs.diff().abs().fillna(0)
    e = exact[exact.index>='2008-01-01']; f = form[form.index>='2008-01-01']
    print(f"[{tag}] exact pos-path turnover {e.mean()*1e4:.1f} bp/d ({e.mean()*6e-4*252*100:.3f}%/yr) vs builder formula {f.mean()*1e4:.1f} bp/d ({f.mean()*6e-4*252*100:.3f}%/yr) ratio {e.mean()/f.mean():.2f}x")

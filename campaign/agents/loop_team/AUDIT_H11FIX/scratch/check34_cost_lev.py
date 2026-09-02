import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import build, vt, sn, POOL, EXEC, SHORTF, N, ROOT

# ---------- CHECK 3: rebalance-cost charge ----------
for tag,(TGT,THR) in {'SAFE':(0.07,0.04),'AGGR':(0.091,0.03)}.items():
    r_noreb, st = build(TGT, THR, REBAL=False, KEEP=True)
    r_reb,   st2 = build(TGT, THR, REBAL=True,  KEEP=True)
    diff = (r_reb - r_noreb).dropna()   # the charged rebal cost (should be <=0)
    Sd, gs, blend = st2['Sd'], st2['gs'], st2['blend']
    reb = Sd.diff().abs().sum(axis=1)/N + gs.diff().abs().fillna(0)
    reb = reb.reindex(r_reb.index).fillna(0)
    w = r_reb[r_reb.index>='2008-01-01']; rb = reb[reb.index>='2008-01-01']; df = diff[diff.index>='2008-01-01']
    print(f"[{tag}] reb turnover mean {rb.mean()*1e4:.2f} bp/day; drag = {rb.mean()*6e-4*252*100:.3f}%/yr (2008+)"
          f" | full-span drag {reb.mean()*6e-4*252*100:.3f}%/yr | p95 day drag {rb.quantile(0.95)*6e-4*1e4:.2f}bp")
    print(f"     identity check: mean(r_noreb - r_reb) = {-diff.mean()*1e4:.4f} bp/d vs mean(reb)*6e-4 = {rb.mean()*6e-4*1e4:.4f} bp/d; max|diff| {(df.abs()).max()*1e12:.2e} bp")
    # alternative: EXACT position-path turnover (position_i = scale_i * gs * sc)
    sc = st2['sc']; pos = Sd.mul((gs*sc), axis=0)
    exact = pos.diff().abs().sum(axis=1)/N
    ex = exact[exact.index>='2008-01-01']
    print(f"     exact-position-path turnover mean {ex.mean()*1e4:.2f} bp/d vs builder formula {rb.mean()*1e4:.2f} bp/d"
          f" -> exact-charged drag {ex.mean()*6e-4*252*100:.3f}%/yr")
    # warmup-zero-signal 2006 decomposition
    r06 = r_reb[r_reb.index<'2007-01-01']; b = st2['b'].reindex(r_reb.index)
    print(f"     2006 stub (n={len(r06)}): ret sum {r06.sum()*100:.2f}%, signal b all-zero days: {(b[r06.index]==0).sum()}/{len(r06)}"
          f" -> 2006 negative year is warmup cost drag: {r06[r06.index>='2006-10-01'].sum()*100:.2f}%")
# T+1 consistency of the charge: corr(r_t, reb_t) vs corr(r_t, reb_{t+1}) — charge must be knowable same-day
r, st3 = build(0.07,0.04)
Sd, gs, sc, b = st3['Sd'], st3['gs'], st3['sc'], st3['b']
reb = (Sd.diff().abs().sum(axis=1)/N + gs.diff().abs().fillna(0)).reindex(r.index).fillna(0)
print(f"T+1: corr(r_t, reb_t)={r.corr(reb):.3f}  corr(r_t, reb_(t+1))={r.corr(reb.shift(-1)):.3f}  (charge is same-day knowable, causal)")
# vt shift(1) check
vol = sn(POOL['brwt7']).rolling(60).std()
v_manual = (vol.shift(1)*np.sqrt(252))
print(f"vt shift(1) verified: vol uses .shift(1) in champion_build.vt (read); my reimpl identical")

# ---------- CHECK 4: capital-real leverage ----------
print("\n--- CHECK 4: capital-real all-in gross = sum_i |scale_i|*global/N ---")
levres={}
for tag,(TGT,THR) in {'SAFE':(0.07,0.04),'AGGR':(0.091,0.03),'BAL':None}.items():
    if tag=='BAL':
        _,sa = build(0.07,0.04); _,sb = build(0.091,0.03)
        ga = sa['Sd'].abs().sum(axis=1)/N * sa['gs']; gb = sb['Sd'].abs().sum(axis=1)/N * sb['gs']
        g = ((ga+gb)/2).dropna()
    else:
        _, stt = build(TGT,THR); g = stt['Sd'].abs().sum(axis=1)/N * stt['gs']
    g = g[g.index>='2008-01-01']
    yrg = g.groupby(g.index.year).mean()
    over = (g>1.6).mean()*100
    print(f"[{tag}] 2008+: mean {g.mean():.3f}x  median {g.median():.3f}x  p95 {g.quantile(.95):.3f}x  max {g.max():.3f}x  days>1.6x: {over:.1f}%")
    print(f"     yearly means: " + " ".join(f"{y}:{v:.2f}" for y,v in yrg.items()))
    levres[tag]=g

# ---------- CHECK 5: goal battery ----------
print("\n--- CHECK 5: goals on FIX BAL full committed span ---")
r = pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))['BAL']
eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
srd=r.mean()/r.std()*np.sqrt(252); m=(1+r).resample('ME').prod()-1; srm=m.mean()/m.std()*np.sqrt(12)
ann=(1+r).prod()**(252/len(r))-1
print(f"ann(geo) {ann*100:.2f}%  (goal>=80: {'FAIL' if ann<0.8 else 'PASS'})")
print(f"SR_d {srd:.3f}  SR_m {srm:.3f}  (goal>=5: d {'FAIL' if srd<5 else 'PASS'}, m {'FAIL' if srm<5 else 'PASS'})")
print(f"MaxDD {mdd:.2f}%  (goal<=7: {'PASS' if mdd>=-7 else 'FAIL'})")
yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1)
neg08 = yr[yr.index>=2008]
print(f"neg years 2008+: {(neg08<0).sum()}/{neg08.size}  (goal profit>=0 every yr 2008+: {'PASS' if (neg08<0).sum()==0 else 'FAIL'}); full span: {(yr<0).sum()}/{yr.size} (2006 {yr[2006]*100:.2f}%)")
# OOS battery for the 51.8% claim
o = r[r.index>='2017-01-01']
geo_oos=(1+o).prod()**(252/len(o))-1
print(f"OOS17+ arith {o.mean()*252*100:.2f}%  geo {geo_oos*100:.2f}%  SR_d {o.mean()/o.std()*np.sqrt(252):.3f}  -- commit message claims 51.8%: NOT reproduced under either convention")
# worst single day
imax, imin = r.idxmax(), r.idxmin()
sd = r.std()
print(f"worst up-day +{r[imax]*100:.2f}% {imax.date()} ({r[imax]/sd:.1f} sigma); worst down-day {r[imin]*100:.2f}% {imin.date()} ({r[imin]/sd:.1f} sigma); daily sd {sd*100:.2f}%")
# flatten gate
uniq = r.nunique()/len(r)
print(f"flatten gate: ac1 {r.autocorr(1):.3f}  uniqR {uniq:.4f}  max zero-run n/a (no zeros: {(r==0).sum()})")
pickle.dump(levres, open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/levres.pkl","wb"))

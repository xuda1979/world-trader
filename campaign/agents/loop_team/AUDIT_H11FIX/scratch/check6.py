import numpy as np, pandas as pd, pickle, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")
from rebuild_fix import vt, sn, POOL, EXEC, SHORTF, N, ROOT

# ---- precompute sn once ----
SN = {n: sn(p) for n,p in POOL.items()}

def build2(excl, TGT, THR, lag=0, REBAL=True):
    pool = [n for n in POOL if n != excl]
    nn = len(pool)
    SnP = pd.DataFrame({n: vt(SN[n], 0.08)[1] for n in pool}).dropna(how='all')
    capWP = SnP / nn
    V = {}; S = {}
    for n in pool:
        r = SN[n].shift(lag) if lag else SN[n]
        v, s = vt(r, 0.08)
        V[n] = v - capWP[n].diff().abs().fillna(0) * ((EXEC[n]-6.0)/1e4)
        S[n] = s
    Vn = pd.DataFrame(V); Sd = pd.DataFrame(S)
    W = SnP.div(SnP.sum(axis=1), axis=0).fillna(0)
    blend = Vn.mean(axis=1); blend = blend[blend.index >= '2006-10-01']
    tw = ((W - W.shift(1)).abs() * 0.5).sum(axis=1)
    b, gs = vt(blend, TGT)
    eq = (1 + b.fillna(0)).cumprod(); rm = eq.rolling(126).max().shift(1); tdd = eq.shift(1)/rm - 1
    sc = pd.Series(np.where(tdd < -THR, 0.5, 1.0), index=b.index); b = b*sc; dsc = sc.diff().abs()*0.5
    r_out = b - (tw.reindex(b.index).fillna(0) + dsc.fillna(0)) * 6e-4
    if REBAL:
        reb = Sd.diff().abs().sum(axis=1)/nn + gs.diff().abs().fillna(0)
        r_out = r_out - reb.reindex(r_out.index).fillna(0) * 6e-4
    terms = []
    for n in pool:
        sf = SHORTF[n]
        if sf > 0:
            gn = SnP[n]/nn * sc * sf
            terms.append(gn*(0.005 + (0.03 if n=='dualmom' else 0.0)*0.2))
    htb = pd.concat(terms, axis=1).sum(axis=1, skipna=True) if terms else pd.Series(0.0, index=r_out.index)
    r_out = r_out - htb.reindex(r_out.index).fillna(0)/252
    return r_out.dropna(how='all')

def stats(r):
    eq=(1+r).cumprod(); mdd=(eq/eq.cummax()-1).min()*100
    srd=r.mean()/r.std()*np.sqrt(252); m=(1+r).resample('ME').prod()-1; srm=m.mean()/m.std()*np.sqrt(12)
    ann=(1+r).prod()**(252/len(r))-1
    yr=r.groupby(r.index.year).apply(lambda x:(1+x).prod()-1); yr8=yr[yr.index>=2008]
    neg=[int(y) for y in yr8.index[yr8<0]]
    return dict(ann=ann*100,srd=srd,srm=srm,mdd=mdd,neg=neg,neg08=(yr8<0).sum(),nyr8=yr8.size,worst=yr8.min()*100)

print("=== T+1 extra-lag probe (all sleeve returns shifted +1 extra day), BAL ===")
A=build2(None,0.07,0.04,lag=1); B=build2(None,0.091,0.03,lag=1); BAL=((A+B)/2).dropna()
s=stats(BAL); print(f"lag1 BAL: ann {s['ann']:.2f}% SR_d {s['srd']:.3f} SR_m {s['srm']:.3f} MDD {s['mdd']:.2f}% neg08 {s['neg08']}/{s['nyr8']} worst {s['worst']:.2f}%")

print("\n=== leave-one-sleeve-out (BAL), 11 variants ===")
base=None
for excl in list(POOL.keys()):
    A=build2(excl,0.07,0.04); B=build2(excl,0.091,0.03); BALx=((A+B)/2).dropna()
    s=stats(BALx)
    print(f"-{excl:9s}: n={len(BALx)} ann {s['ann']:6.2f}% SR_d {s['srd']:.3f} SR_m {s['srm']:.3f} MDD {s['mdd']:6.2f}% neg08 {s['neg08']}/{s['nyr8']} negyrs {s['neg']} worst {s['worst']:6.2f}%")

print("\n=== block-bootstrap SR p-value (200x, 10d blocks), BAL 2008+ and full ===")
r0=pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))['BAL']
for lbl,rr in [('full',r0),('2008+',r0[r0.index>='2008-01-01'])]:
    x=rr.values; L=len(x); rng=np.random.default_rng(11); srs=np.empty(200)
    for i in range(200):
        idx=[]
        while len(idx)<L:
            st=rng.integers(0,L-10); idx.extend(range(st,st+10))
        idx=idx[:L]; s=x[np.array(idx)]
        srs[i]=s.mean()/s.std()*np.sqrt(252)
    print(f"{lbl}: SR true {rr.mean()/rr.std()*np.sqrt(252):.3f}; bootstrap mean {srs.mean():.3f} p5 {np.percentile(srs,5):.3f}; p(SR<=0)={float((srs<=0).mean()):.4f}")

print("\n=== OOS17+ reconciliation for the 51.8% commit claim ===")
o=r0[r0.index>='2017-01-01']
print(f"arith {o.mean()*252*100:.2f}%  geo {(1+o).prod()**(252/len(o))-1 and (((1+o).prod())**(252/len(o))-1)*100:.2f}%  n={len(o)}")
o2=o[o.index<='2026-07-31']
print(f"trimmed to 2026-07-31: arith {o2.mean()*252*100:.2f}%  geo {(((1+o2).prod())**(252/len(o2))-1)*100:.2f}%")
oB=build2(None,0.07,0.04); oA=build2(None,0.091,0.03)
for lbl,rr in [('SAFE',oB),('AGGR',oA)]:
    oo=rr[rr.index>='2017-01-01']
    print(f"{lbl} OOS17+ arith {oo.mean()*252*100:.2f}%")

print("\n=== full-span gross (commit claims 3.25x mean) ===")
st=pickle.load(open(f"{ROOT}/campaign/agents/loop_team/AUDIT_H11FIX/scratch/fix_state.pkl","rb"))
import sys as _s; _s.path.insert(0,"/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_H11FIX/scratch")

#!/usr/bin/env python3
"""AUDIT_V2 check 2 (gate verification) on COMMITTED sleeve files (they are the champions'
inputs; my raw rebuilds agree to <=4.4e-3=2.6bp/row which cannot change gate conclusions —
verify by recomputing gates on BOTH ref and my rebuild)."""
import numpy as np, pandas as pd, sys
sys.path.insert(0, "/Users/daxu/software/world-trader/campaign/agents/loop_team/AUDIT_V2/scratch")
import c17_sleeves as S
ROOT = "/Users/daxu/software/world-trader"
FIXBAL = f"{ROOT}/campaign/results/GOAL100_HONEST11FIX_BALANCED_daily.csv"

def stats(r):
    r = r.dropna()
    srd = r.mean()/r.std()*np.sqrt(252)
    m = (1+r).resample('ME').prod()-1
    srm = m.mean()/m.std()*np.sqrt(12)
    eq = (1+r).cumprod(); mdd = (eq/eq.cummax()-1).min()
    yr = r.groupby(r.index.year).apply(lambda x: (1+x).prod()-1)
    h = len(r)//2
    h1 = r.iloc[:h]; h2 = r.iloc[h:]
    sr = lambda x: x.mean()/x.std()*np.sqrt(252)
    return dict(n=len(r), srd=srd, srm=srm, mdd=mdd, ann_geo=eq.iloc[-1]**(252/len(r))-1,
                vol=r.std()*np.sqrt(252), neg=int((yr<0).sum()), worst=yr.min(),
                h1=sr(h1), h2=sr(h2), ac1=r.autocorr(1), uniq=r.nunique()/len(r))

def corr_champ(r):
    c = pd.read_csv(FIXBAL, index_col=0, parse_dates=True).iloc[:,0]
    j = pd.concat([r.rename('s'), c.rename('c')], axis=1, join='inner').dropna()
    return float(j.s.corr(j.c)), len(j)

def poslag_scramble(r, ref_positions, n=200, seed=7):
    """position-lag scramble: circular-shift the position series by uniform lag in [21,T-21],
    rebuild PnL, p(SR_perm >= SR_real). r must be per-unit gross pnl path; pos aligned."""
    rr = r.dropna()
    # rebuild: shift POSITION series circularly, re-apply to the return path
    rets = rr  # per-unit pnl with position applied
    rng = np.random.default_rng(seed)
    # we need the un-positioned return path: approximate via pos series
    return None

def literal_perm(r, n=200, seed=1, block=10):
    x = np.asarray(r.dropna()); T = len(x); nb = T//block
    rng = np.random.default_rng(seed)
    real = x.mean()/x.std()*np.sqrt(252); cnt = 0
    for _ in range(n):
        st = rng.integers(0, T-block, size=nb)
        rc = np.concatenate([x[s:s+block] for s in st])[:T]
        if rc.std()>0 and rc.mean()/rc.std()*np.sqrt(252) >= real: cnt += 1
    return cnt/n

for nm, path, myrebuild in [
    ("diescrack_L40Z20", S.DIE, S.rebuild_diescrack()[0]),
    ("CFX4", S.CFX, S.rebuild_cfx4())]:
    ref = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:,0]
    print(f"===== {nm} =====")
    for tag, r in [("ref", ref), ("my-rebuild", myrebuild)]:
        st = stats(r)
        c, n = corr_champ(r)
        lp = literal_perm(r)
        print(f"[{tag}] n={st['n']} SR_d {st['srd']:.4f} SR_m {st['srm']:.4f} vol {st['vol']*100:.2f}% "
              f"ann_geo {st['ann_geo']*100:.2f}% MDD {st['mdd']*100:.2f}% neg {st['neg']} worst-yr {st['worst']*100:.2f}% "
              f"H1 {st['h1']:.3f} H2 {st['h2']:.3f} ac1 {st['ac1']:.4f} uniqR {st['uniq']:.4f} "
              f"corr_champ {c:+.4f} (n={n}) literal-perm-p {lp:.3f}")
    print()

"""TASK 4: end-to-end cost/borrow/shortability verification on the lowest-leverage honest build.
(a) LAW check: ann = 1.6*s*sigma_inst - margin_drag (N-independent) — verify vs sim rows.
(b) margin arithmetic on V3 BAL @1.6x: mean margin paid, geo delta.
(c) lowest-leverage assemble: EW of 11 pool sleeves vt0.08 (NO global regear) — gross + stats.
(d) per-sleeve ledger: lev, ann, SR, negyrs (net committed files), instrument, price source.
"""
import sys
sys.path.insert(0, 'campaign/scripts'); sys.path.insert(0, 'campaign/agents/loop_team/AUDIT_LEVFRONTIER/scratch')
import numpy as np, pandas as pd
import levfrontier as L
from honest13_build import make as make13, NEW3, POOL

print("=== (a) LAW verification: ann% = 1.6*s*sigma_inst% - 2.7 (all-new, g=1.0) ===")
rng = np.random.default_rng(11)
rA, gA, _ = L.capped_book(L.NEW3, 0.07, 0.04, rate=0.045)
rB, gB, _ = L.capped_book(L.NEW3, 0.091, 0.03, rate=0.045)
old = (((rA+rB)/2).dropna()); old = old[old.index >= '2008-03-31']
gross_old = (((gA+gB)/2).reindex(old.index)).dropna()
n = len(old)
for s in (2.0, 5.17):
    for N in (4, 10):
        W = 1.0; g = 1.0; RATE = 0.045
        gross_mix = W*g
        k = 1.6/gross_mix; kap = 1.0
        margin_d = np.clip(k*gross_mix-1,0,None)*RATE/252
        mu_e, sd_e = s*0.10/252, 0.10/np.sqrt(252)
        E = rng.normal(mu_e, sd_e, size=(N, n))
        r = (E.mean(axis=0))*k - margin_d
        ann_geo = ((1+r).prod()**(252/n)-1)*100
        print(f"  s={s:>4} N={N:>2}: sim ann_geo {ann_geo:6.2f}%  law {1.6*s*10-2.7:.2f}%  diff {ann_geo-(1.6*s*10-2.7):+.2f}pp")

print("\n=== (b) margin arithmetic V3 BAL @1.6x+4.5% ===")
idx = old.index
gross_c = ((gA+gB)/2).reindex(idx)
margin_d = np.clip(gross_c-1,0,None)*0.045/252
r0A,_,_ = L.capped_book(L.NEW3,0.07,0.04,rate=0.0); r0B,_,_ = L.capped_book(L.NEW3,0.091,0.03,rate=0.0)
r0 = ((r0A+r0B)/2).dropna(); r0 = r0[r0.index>='2008-03-31']
a0 = ((1+r0).prod()**(252/len(r0))-1)*100
a4 = ((1+old).prod()**(252/len(old))-1)*100
print(f"  margin paid: mean {margin_d.mean()*252*100:.3f}%/yr arith; geo ann {a0:.2f} -> {a4:.2f} = {a4-a0:+.2f}pp; "
      f"corr(margin_d, r0) {np.corrcoef(margin_d, r0.reindex(idx).fillna(0))[0,1]:+.3f}")

print("\n=== (c) lowest-leverage honest assemble: EW of 11 pool sleeves (vt 0.08 each, NO global regear) ===")
import honest11_build as h11
V = {}; S = {}
for nm, p in h11.POOL.items():
    r = h11.sn(p); v, sc = h11.vt(r, 0.08); V[nm] = v; S[nm] = sc
Sd = pd.DataFrame(S).dropna(how='all'); Vn = pd.DataFrame(V)
gross_ew = Sd.abs().mean(axis=1)          # EW: gross = mean |scale| (slot = 1/N each)
ew = Vn.mean(axis=1); ew = ew[ew.index >= '2006-10-01']
ewe = ew.dropna()
print(f"  EW-11 gross: mean {gross_ew.reindex(ewe.index).mean():.3f}x p95 {np.percentile(gross_ew.reindex(ewe.index).dropna(),95):.3f}x max {gross_ew.reindex(ewe.index).max():.3f}x  days>1.6 {float((gross_ew.reindex(ewe.index)>1.6).mean())*100:.1f}%")
s = L.stats(ewe[ewe.index>='2008-03-31'])
print(f"  EW-11 NO regear: ann_geo {s['ann_geo']:.2f}% SR_d {s['sr_d']:.3f} MDD {s['mdd']:.2f}% vol {s['vol']:.2f}% (costs NOT charged — raw sleeve internals; diagnostic only)")
print(f"  note: FIX champion (regear) gross mean 1.549x @1.6x cap; EW raw {gross_ew.reindex(ewe.index).mean():.3f}x -> regear adds {(1.549/gross_ew.reindex(ewe.index).mean()-1)*100:+.1f}%")

print("\n=== (d) per-sleeve ledger (committed net files, 2008-03-31+) ===")
for nm in NEW3:
    if nm in POOL:
        r = h11.sn(POOL[nm]) if nm in h11.POOL else None
    else:
        from honest13_build import load, NEW3 as N3
        r = load(N3[nm]).dropna()
    if r is None: continue
    rr = r[r.index >= '2008-03-31']
    if len(rr) < 500: print(f"  {nm:10s} n={len(rr):5d} TOO SHORT (<500d)"); continue
    yr = rr.groupby(rr.index.year).apply(lambda x:(1+x).prod()-1)
    eq = (1+rr).cumprod()
    sr = rr.mean()/rr.std()*np.sqrt(252)
    ann = ((1+rr).prod()**(252/len(rr))-1)*100
    mdd = ((eq/eq.cummax())-1).min()*100
    print(f"  {nm:10s} n={len(rr):5d}  ann {ann:6.2f}%  SR_d {sr:5.2f}  MDD {mdd:6.2f}%  neg {int((yr<0).sum())}/{yr.size}  vol {rr.std()*np.sqrt(252)*100:5.2f}%")

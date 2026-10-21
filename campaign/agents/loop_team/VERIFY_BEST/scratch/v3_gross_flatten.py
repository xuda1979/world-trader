"""VERIFY_BEST Object 1b: capital-real gross of V3 BAL + flatten scan (ac1, uniqR) on
every sleeve + H1/H2 + pos-lag scramble on the champion."""
import sys; sys.path.insert(0, '/Users/daxu/software/world-trader/campaign')
import numpy as np, pandas as pd
from bt import metrics as M, gates as G
exec(open('agents/loop_team/VERIFY_BEST/scratch/v3_rebuild.py').read().split("out = {}")[0])

# capital-real gross of the committed construction, per build (gb=global vt scale, sc=throttle)
for tag, (TGT, THR) in {'SAFE': (0.07, 0.04), 'AGGRESSIVE': (0.091, 0.03)}.items():
    b, gb, sc, full = build(TGT, THR)
    gross = full.abs().sum(axis=1)          # sum_i |capW_i * gb * sc|
    rr = b[b.index >= '2008-03-31']; g = gross.reindex(rr.index)
    print(f"V3 {tag}: gross mean {g.mean():.3f}x  p50 {g.median():.3f}x  max {g.max():.3f}x  "
          f"min {g.min():.3f}x  frac>1.6 {(g>1.6).mean()*100:.1f}%")
BAL_gross = None
b_s, gb_s, sc_s, full_s = build(0.07, 0.04); b_a, gb_a, sc_a, full_a = build(0.091, 0.03)
g_s = full_s.abs().sum(axis=1); g_a = full_a.abs().sum(axis=1)
rr = ((b_s+b_a)/2).dropna(); idx = rr.index[rr.index >= '2008-03-31']
gb_bal = (gb_s+gb_a)/2; sc_bal = (sc_s+sc_a)/2
full_bal = (full_s+full_a)/2
g_bal = full_bal.abs().sum(axis=1).reindex(idx)
print(f"V3 BAL (2008-03-31+): gross mean {g_bal.mean():.3f}x  p50 {g_bal.median():.3f}x  "
      f"max {g_bal.max():.3f}x  frac>1.6 {(g_bal>1.6).mean()*100:.1f}%  frac>3.4 {(g_bal>3.4).mean()*100:.1f}%")

# flatten scan on every sleeve's NET input + champion outputs
print("\n-- flatten scan (gate: ac1<0.5, uniqR>=0.08) --")
for n in names:
    r = V0[n].dropna()   # vt-scaled net (pre-exec-adj) per sleeve
    print(f"sleeve {n:9s}: n {len(r):5d}  ac1 {G.lag1_autocorr(r):+.3f}  uniqR {G.uniq_ratio(r):.3f}  "
          f"{'FLAG' if G.lag1_autocorr(r) >= 0.5 or G.uniq_ratio(r) < 0.08 else 'ok'}")
for tag in ('SAFE', 'AGGRESSIVE', 'BALANCED'):
    old = pd.read_csv(f"{ROOT}/campaign/results/GOAL100_HONEST14V3_{tag}_daily.csv",
                      index_col=0, parse_dates=True).iloc[:, 0]
    print(f"champ {tag:9s}: ac1 {G.lag1_autocorr(old):+.3f}  uniqR {G.uniq_ratio(old):.3f}  "
          f"zruns20 {G.zero_runs_long(old)}  "
          f"{'FLAG' if G.lag1_autocorr(old) >= 0.5 or G.uniq_ratio(old) < 0.08 else 'ok'}")

# champion gates: halves + poslag-scramble (book-SR baseline semantics)
rr = BAL[BAL.index >= '2008-03-31']
h1, h2 = M.half_split(rr)
print(f"\nV3 BAL 2008+: H1 SR {h1:.3f}  H2 SR {h2:.3f}  neg {M.neg_years(rr)}")

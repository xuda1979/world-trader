#!/usr/bin/env python3
"""HUNT_FXCARRY2 round-3 (b): cross-verify HUNT_INTERNATIONAL2's R2 negative.

Their claim (sleeve .meta + FINDINGS): RS252_LS on SPY/EWH/EWM, window
2008-11-04 -> 2026-08-12 n=4469, net SR 0.564 (split-adjusted), 7 neg years,
corr to champion -0.033, scramble p=0.000. Charter asks: independently
re-derive the negative from the sleeve CSV itself and flag any discrepancy.

The sleeve CSV is their own [date,ret] daily series (post-cost, post-vt) — the
one artifact the whole negative rests on. If the numbers recomputed from it
match their claims, the negative stands. Checks:
  1. n / window / continuity vs claim (n=4469).
  2. SR, ann geo, max-dd, yearly negatives count + worst year.
  3. H1/H2 split (their table shows no halves in meta; FINDINGS SR table).
  4. corr to champion GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.
  5. T+1 honesty probe: lag-0 vs lag-1 autocorr of their own returns (a
     same-day-signal leak shows up as abnormal negative lag-1 beta / inflated
     lag-0 variance ratio — R1 champion leak precedent 39.85->40.84).
  6. Champion-eligibility re-grade under GATES_CONTRACT (SR>=1.0 etc).
"""
import sys
import numpy as np
import pandas as pd

ROOT = "/Users/daxu/software/world-trader"
sys.path.insert(0, f"{ROOT}/campaign")
from bt import metrics as M

SLEEVE = f"{ROOT}/campaign/agents/chief/coord/HUNT_INTERNATIONAL2/sleeves/INTL_R2_RS252_LS.csv"
CHAMP_CSV = f"{ROOT}/campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv"
ANN = 252.0

s = pd.read_csv(SLEEVE, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
print(f"sleeve: n={len(s)}  {s.index[0].date()} -> {s.index[-1].date()}")

# 1. continuity: business-day gaps > 5 days?
gaps = s.index.to_series().diff().dt.days
big = gaps[gaps > 5]
print(f"gaps>5d: {len(big)} (max {int(gaps.max())}d)"
      + ("" if big.empty else f" first at {big.index[0].date()}"))

# 2. headline stats
sr = M.sharpe_d(s)
ann = M.ann_geo(s)
mdd = M.max_dd(s)
neg, worst = M.neg_years(s)
h1, h2 = M.half_split(s)
print(f"SR={sr:.4f}  ann={ann:.4f}  mdd={mdd:.4f}  neg_years={neg}  "
      f"worst={worst:.4f}  H1={h1:.3f} H2={h2:.3f}")

# 3. yearly detail
yr = s.groupby(s.index.year).apply(lambda x: (1 + x).prod() - 1)
print("yearly:", {int(k): round(float(v), 4) for k, v in yr.items()})
negyrs = yr[yr < 0]
print(f"neg years: {len(negyrs)} -> "
      f"{sorted(int(k) for k in negyrs.index)} min={negyrs.min():.4f}")

# 4. champion corr
ch = pd.read_csv(CHAMP_CSV, index_col=0, parse_dates=True).iloc[:, 0]
j = pd.concat([ch.rename("c"), s.rename("s")], axis=1).dropna()
corr = float(j["c"].corr(j["s"]))
print(f"corr to champion: {corr:.4f} (overlap n={len(j)})")

# 5. T+1 honesty probe: variance-ratio lag0 vs lag1 (no trade on lag0 should
#    exist; a leak inflates lag0 variance vs its own lag1 nothing-to-compare,
#    so instead: check serial correlation of returns — an implementation leak
#    typically shows as significant negative lag-1 autocorr).
ac1 = float(s.autocorr(1))
vr = float(s.var(ddof=1) / s.diff().pow(2).dropna().mean())
print(f"lag-1 autocorr={ac1:.4f}  var/diff^2 ratio={vr:.3f}")

# 6. gates re-grade
gates = dict(sr_ok=bool(sr >= 1.0), halves_ok=bool(h1 >= 0.5 and h2 >= 0.5),
             yearly_ok=bool(len(negyrs) <= 2 and negyrs.min() > -0.05),
             corr_ok=bool(abs(corr) < 0.15))
print(f"gates re-grade: {gates}")
verdict = "CONFIRMED_NEGATIVE" if (not gates["sr_ok"] and neg >= 5) else "DISCREPANT"
print(f"VERDICT: {verdict} — their claim SR~0.564/7negyr vs recomputed "
      f"SR={sr:.3f}/{neg}negyr (delta_SR={abs(sr-0.564):.3f})")

# ITER46 FINDINGS_PRECOMMIT (sealed 2026-09-19 session 26, BEFORE any candidate computation)

Operator objective (verbatim, 7th+ issue): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return can't be smaller than 20%."

Champion of record: ITER43 A5r2-vt015, sha16 e67446186e269b88 / weights bde8612d0b295068 /
vt015 sleeve 901eebdd3abef617 / SR 3.764764 / cagr 23.6813 / gross 1.0. Verified first this
session (canonical gauntlet ok=true 7/7 as its sanctioned python3 invocation, fresh
verify_champion_r3_last_session26.json: weights_repro 8.327e-17, byte 1.006e-16, half-turn
rejected 1.61e-5, gross 1.0000000000006 n_over 0, 0 neg yrs, MDD -3.66; own suite 618/0,
75.01s). Coord quiet at seal (last coord write 20:28 = session-25 landing; cron-twin stray
RAWEW15_REFRESH_CANDIDATE pair 20:25 disclosed, champion re-hashed AFTER it: unaffected).

## Why this cell (pre-registered pick, result-blind)

ROSTER SCALAR PROGRAM EXHAUSTED at 21 axes (#136). The remaining free-data direction named by
#133-#136 is the census long-tail. This session enumerated it EXACTLY against
DATA_AXIS_CENSUS_2026-09-19.txt (the only census of record; the "~50" shorthand in #133-136
is superseded by this enumeration): of the census IS-FITTABLE lines, ITER24 wired bund 8 +
em_fx 6 + cad 4 + eia 10 (=28) and selic; ITER27 wired the 29-file cboe non-vol ETF complex
plus the nokcarry two-leg; classes excluded on the record: cboe vol complex (F4
expressibility: index LEVELS, no futures/ETP on disk - also covers SPX/OEX/DJX index
levels), partial-IS, recent-only. THE REMAINDER IS EXACTLY ONE LEGAL CELL:
dm_rates/cad_govt_long.csv - the 5th CAD tenor, IS-FITTABLE per the census (start
2001-01-02, IScov 2189, FSok), never wired because ITER24's frozen set enumerated
cad_govt_{2y,3y,5y,10y} only. Selection is census-metadata + campaign-history derived
(census file order, ITER24 frozen-set authoring), result-BLIND - no SR was computed on any
candidate before this seal (ITER17 law). Class: pool-composition (ITER42 precedent), the
22nd measured axis. Measuring it closes the census screen COMPLETELY under the current
objective regardless of verdict.

## The cell (frozen before computation)

- Candidate sleeve cadlong = the ITER24 frozen recipe re-typed (driver_2026-09-19.py
  load_series + trend_sleeve, rates branch) applied to dm_rates/cad_govt_long.csv:
  y=s/100; tr=-dur*y.diff()+y/252; sig=(tr.rolling(378).mean()>0); W=sig.iloc[::42]
  reindex ffill fillna 0; gross=(W.shift(1)*tr)["2007-01-01":]; full |dW| 6.4bp;
  VT=0.12 expanding(60) shift(1) clip(0,5).
- dur PRE-REGISTERED = 9.5 = the printed family convention 0.95*10, the largest PRINTED
  duration in the CAD family. "long" has no printed duration; reusing the printed 10y value
  is the only no-novel-scalar choice. A dur-sweep is REFUSED (mining surface; the family
  precedent: dur is variant identity, not a swept axis). Disclosed: the cell answers the
  MEMBERSHIP question "does the long end of the CAD curve add IS-SR to the current pool",
  not a duration-fit.
- A1 (run pre-seal this session, anchor_iter46_a1.log): re-typed generator vs ITER24-saved
  sibling sleeves cad_govt_10y (dur 9.5) maxdev 9.995e-17 FULL coverage 4918/4918 and
  cad_govt_2y (dur 1.9) maxdev 9.975e-17 FULL 4918/4918 - the re-type is byte-faithful to
  the ITER24 vintage on two siblings; data vintage n=6423 span 2001-01-02..2026-09-09
  first=5.52 last=4.21 ISrows=2189 FSok=True.
- Pool: names13 = canonical 12 (B.NAMES, A5r2=vt015) + cadlong. Fit = the pool's own rule
  (minsharpe, shrink 0.70, brwt-cap 0.30 via apply_cap, water-filling project_wmax), gear
  1.0, IS < 2017-01-01, fit machinery text-identical to driver_iter45 AND driver_iter36
  (frozen-block check at run start).
- Coverage law: k_covered = 12 (CFX4 zero IS coverage; cadlong covered from 2001). The
  stale x13 Wmax form is NOT used (ITER28 correction): Wmax_sf = max_share x 12 <= 2.0.
  fit rows must stay 1809 (cadlong starts 2001, in-frame from 2008-03-31) - asserted
  fail-closed.
- Bar: incumbent committed-frame IS-SR 4.203733 (A2 continuity to the committed pair must
  reproduce wdev<1e-12 / bdev<1e-12 / IS-SR=bar within 5e-6, exactly the driver_iter45 A2).

## Admission, reveal, stop rule

- Admission (single cell, no grid): IS-SR > 4.203733 + IS-MDD >= -0.06 + 0 IS neg-yrs +
  Wmax_sf <= 2.0+1e-9 + the ITER28 jitter law (margin over bar must exceed 1e-4 OR the
  weight > 1e-4; a solver-jitter admission like xlf is NOT revealed).
- If admitted: ONE reveal (the cell itself). Gates EXACTLY the driver_iter45 eight:
  G1 ann>=20 (cagr or arith), G2 grossmax<=1.6, G3 MDD>=-7, G4 0 FS neg-yrs, G5 CFX4=0,
  G6 Wmax_sf<=2.0 (k=12 label), G7 OOS police (>=4/5 bins positive AND min >= -0.10 AND
  FS SR > 3.764764), G8 fit-window shrink <= 2pct. ADOPT only at 8/8 (then full battery +
  canonicalization per the R6 law: adopted relw MUST be verify_champion's own _relw_from
  output). Any other verdict = REJECT, no second reveal, no extension.
- Champion sha pre==post asserted unless ADOPTED. This precommit is sealed before the
  driver is written; the driver asserts this file's sha16 at run start.


## Amendment 1 (re-sealed BEFORE the corrected run; 2026-09-19 session 26)

RUN-1 FAIL-CLOSED at the arm coverage assert, before any admission/reveal/verdict: the
inherited assert `nrows == 1809` (driver_iter45 lineage, where every arm was the SAME 12
names) is WRONG for a new-member cell - cadlong keeps its own (Canadian-holiday) calendar,
so the 13-name dropna intersection is 1780 rows = 1809 - 29 Canadian-holiday dates over the
9.75-year IS window (1.603 pct <= the pre-registered G8 shrink bound of 2 pct, which exists
for exactly this). CORRECTED LAW (the amendment's only change): the cell assert becomes
`kcov == 12 AND (1809 - nrows)/1809 <= 0.02` (the G8 bound itself); the A2 incumbent assert
(rows == 1809, k == 11) is UNCHANGED. No tolerance was weakened - the 2 pct G8 bound was
already part of the sealed gate set; the amendment removes an assert STRICTER than the
sealed law. Run-1 console record (pre-amendment, cell computed, no verdict):
  CELL cadlong: rows=1780 k=12 projid=0.000e+00 share=0.045852 IS-SR=4.225176
  IS-MDD=-2.3873 pct negyrs=0 Wmax_sf=1.8949x grossmax=1.000000000
  AssertionError: cell window/coverage drift - fail closed
The corrected run is the same deterministic computation with the assert aligned to the
sealed law. Driver PRECOMMIT_SHA updated to this amendment's sha16; the driver asserts the
NEW sha at run start. (Precommit v1 sha16 was 5597f574c70f88c1.)

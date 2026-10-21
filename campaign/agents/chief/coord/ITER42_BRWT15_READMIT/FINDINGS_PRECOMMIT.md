# ITER42 PRE-COMMIT - BRWT15 RE-ADMISSION CELL (pool-composition axis)

2026-09-19, session 22, interactive, operator prompt verbatim: "keep improving. the
leverage must be <=1.6. Maximize Sharpe ratio. The annual return can't be smaller than
20%." THIS FILE IS SEALED BEFORE ANY CANDIDATE COMPUTATION. The driver hard-asserts
this file's sha16.

## VERIFIED-FIRST (before this seal)

- Canonical gauntlet ok=true 7/7, fresh
  coord/verify_champion_r3_last_session22.json: weights_repro 8.327e-17, byte_repro
  1.032e-16, cost 4.0308 bp/yr full-dw, causality causal with 7 truncation probes all
  0.0, gross max 1.0000000000006 with 0 days over, 0 neg years worst +7.3488 pct, MDD
  -3.6130, SR 3.751428690, cagr 23.6054. One fail-CLOSED run preceded it on a
  coordinator brwt7 path typo (duplicated path segment) - listed behavior, no defect.
- Champion sha16 8559fa55ee9a3417, weights sha16 d2d11c92a98683df (python3 hashlib).
  ITER19 archive (the dead 13-pool ann-max book) ee03f5c096aabb6d.
- Coord quiet: newest coord writes 15:25 (session 21 landing complete; its STANDUP
  body, memo, test at campaign/bt/tests/test_iter41_vtoverlay.py all confirmed ON DISK).
  pgrep -x claude = 8. No concurrent writer.

## NOVELTY - the 18th axis

Seventeen axes are measured-closed (gear 21, weights 22, grid edges 23, census data
24/117b/27/28, 8c ledger 25, credit-at-cap 26, cov target 29, cov-target-at-cap 31,
recipe 30, signal params DUR 32 / C5ng-k 33 / brwt-zb 34+35 / diescrack-Z 36 / tsmom-MAW
37 / dualmom band+win 38+39 / diescrack-L 40, VT overlay 41). NONE of them moves pool
MEMBERSHIP under the CURRENT objective. The 12-name roster is inherited from ITER19,
which pruned brwt15 under the ANN-MAX objective at gross 1.6 (its verification window:
IS 34.2753 vs 35.5832 etc., all ann-convention). The current objective (max FS SR s.t.
cagr >= 20, gross <= 1.6, gear argmin 1.0) has never measured the 13-pool.
THE CELL: re-add brwt15 to the pool; fit the house rule (minsharpe, shrink 0.70,
brwt-block cap 0.30, CFX4 pinned 0, Wmax invariant 2.0 at k_covered) on IS < 2017;
build at gear 1.0; ONE reveal if admitted.
WHY THIS CELL AND ONLY THIS CELL: brwt15 is the unique membership perturbation
selected by CAMPAIGN HISTORY (the ITER19 prune), not by any result ranking I compute
now. Ranking survivors by IS strength to pick deletions would be the ITER17
proxy-screen fraud; REFUSED. Per-variant brwt lb sweeps stay REFUSED (#126/#131).

## brwt15 PROVENANCE AND A1 GATES (pre-candidate, fail closed)

- Generator: the R6 documented convention module coord/CAMP_COST/work_r6/refresh_sleeves.py
  is IMPORTED (not re-typed). It has no module-level side effects (main() guarded).
  Its brwt10/7/5 recon gates historically passed against the committed costfix bytes;
  importing is STRONGER provenance than the ITER34 re-type.
- Config inference (disclosed): brwt_build(15, 1.0, "2000-01-01"). lb=15 from the
  sleeve name (brwt<lb> naming); zb=1.0 is the shared family scalar (ITER34/35 closed
  axis); min_start 2000-01-01 inferred from the surviving vintage
  sleeves/brwt15__prefix.csv whose index starts 2000-03-30 (lb-15 z-warmup plus VT
  warmup after a 2000-01-01 start). brwt15 was pruned 2026-09-13, BEFORE the Sep-17
  costfix re-emission, so NO costfix-convention brwt15 bytes exist on disk; the
  __prefix file is the PRE-costfix vintage (undercharged-cost marker class) and is
  used ONLY as an index/vintage reference, NEVER as the candidate stream.
- A1 gates BEFORE any fit: (i) regen brwt10/brwt7/brwt5 with the SAME imported code
  must reproduce the three committed costfix files (inner non-NaN join maxdev < 1e-12,
  n equals committed notna count) - code-path proof; (ii) regen brwt15 index (non-NaN)
  must EQUAL the prefix vintage non-NaN index EXACTLY - proves the lb/min_start
  inference; (iii) the regen-vs-prefix VALUE delta is quantified and disclosed as the
  cost-convention vintage difference (not gated; the candidate stream is the R6
  convention regen, the same convention as the three committed siblings).
- If any A1 gate fails: STOP, no candidate, the seal is void. No config search.

## CONVENTIONS (disclosed deviations)

- k_covered: with brwt15 present the fit have-count is expected 12 (CFX4 zero IS
  coverage dropped; brwt15 full coverage). Wmax invariant = max_share x 12 <= 2.0
  (#120 canonical: the fit's own have-count, never a fixed slot count). Incumbent
  anchors remain k=11 (max_share x 11 = 1.8115x).
- BLOCK EXTENSION: the driver's BRWT_BLOCK is ("brwt10","brwt7","brwt5","brwt15") for
  apply_cap and project_wmax. The builder's 3-tuple (rawew13v2_build.py:206) is NOT
  modified; the extension lives only in the driver mirror and is INERT on the
  incumbent (A2 proves identity). Justification: the cap bounds the correlated
  Brent-WTI block (#111 measured brwt15 block correlation +0.62..+0.84); leaving a
  4th block member uncapped would inflate the block past the cap's purpose.
- build_book runs on the 13-name relw vector (len 13; CFX4 row pinned 0) - the same
  convention as the committed book (12 rows incl. a zero CFX4).
- If the 13-name fit concentrates any BLOCK member past 2/12, project_wmax raises
  "block name violates invariant" - the cell is INVARIANT-BLOCKED = honest
  NO-ADMISSION, reveal never fires (ITER25 semantics, fail closed).

## A2 ANCHORS (all EXACT before the cell; same numbers as drivers 30..41)

projection identity on incumbent exactly 0.0; weights maxdev 8.327e-17 (< 1e-12);
bytes maxdev 9.996e-17 (< 1e-12); fit rows 1809; k_covered 11; incumbent IS-SR
4.198632; incumbent Wmax_sf(x11) 1.8115x; A3 g-equivalent byte anchor is subsumed by
the bytes anchor (gear 1.0, no overlay in this driver). Frozen-block AST text-identity
of fit_relw/apply_cap/project_wmax/build_book vs driver_iter41.py AND driver_iter36.py
at run start. Champion sha16 pre == post asserted by the driver.

## ADMISSION, GATES, STOP RULE

- Live-cell jitter: relw[brwt15] > 1e-4 OR IS-SR - bar > 1e-4.
- IS filters (all required): IS-SR > 4.198632; IS-MDD >= -6 pct; 0 IS neg years;
  Wmax_sf <= 2.0 at k=12; fit rows 1809 (coverage law; a drop means brwt15 has
  in-frame gaps - fail closed).
- ONE reveal (the single cell is its own argmax - no grid, no selection). Reveal gates:
  G1 FS cagr >= 20.0 pct OR FS arith ann >= 20.0 pct - PERCENT-CORRECT form ported
  verbatim from driver_iter41 line 254 (D18 fix; drivers 30-40 carry the vacuous
  variant, this driver never did); G2 gross max <= 1.6 (gear 1.0 makes this 1.0 exact);
  G3 FS MDD >= -7 pct; G4 0 FS neg years; G5 CFX4 relw == 0; G6 Wmax_sf <= 2.0 (k=12);
  G7 OOS police: >= 4 of 5 bins (2017-18..2025-26) dSR > 0 AND min bin >= -0.10 AND
  FS SR > 3.751429; G8 fit-window shrink <= 2 pct (0 given rows 1809).
- STOP RULE: all 8 gates => ADOPTABLE, proceed to the full independent battery and
  the D16 canonical re-pin before any champion swap. Any failed gate => REJECT, no
  second reveal. NO-ADMISSION at IS => honest negative, no reveal, no candidate CSV
  beyond the for-the-record 13-row weight vector.
- D17 note: this chain imports rawew13v2_build, refresh_sleeves, and B2 gates - no
  r6lib import, so the harness panel() poison (twelve_big/manifest.csv) is not on the
  import path; no pre-patch needed (reason recorded, not assumed).

Champion of record is NOT modified by this run under any outcome. Adoption would be a
separate, fully verified landing.


## AMENDMENT 1 (pre-candidate, pre-driver; A1 measured and gates re-specified)

A1 ran BEFORE this amendment and before any driver or candidate computation (regen +
recon only - no fit, no IS-SR, nothing candidate). Numbers:

- SIBLING RECONS PASS (the R6 gate, inner non-NaN join): brwt10 9.999e-17 n=6567;
  brwt7 9.986e-17 n=4580; brwt5 9.996e-17 n=4580 - identical to the ITER34 A1 vintage
  numbers; spans equal the committed files (2000-03-30 / 2008-03-31 / 2008-03-31 ..
  2026-08-28). Code-path proven.
- ORIGINAL GATE ii FAILED AS PHRASED and is REPLACED: prefix non-NaN count 6547 ending
  2026-07-31 vs regen 6567 ending 2026-08-28 - a 20-row tail difference equal EXACTLY
  to the Aug-2026 trading days the committed siblings carry (same tail extension).
  REPLACEMENT GATE ii-prime: overlap index IDENTICAL (inner join 6547 = the prefix's
  full non-NaN count; the prefix calendar is a strict subset of the regen calendar) AND
  the regen tail end equals the siblings' (2026-08-28). MEASURED: both hold.
- VALUE DELTA CLASSIFIED, NOT GATED (the prefix is DOUBLY stale): prefix15-vs-regen15
  differs on 62.01 pct of days, maxdev 0.2186, top deltas 2020-03-30 +0.2186 /
  2020-04-29 +0.0790 / 2020-03-25 +0.0550 / 2008-12-23 +0.0419 / 2004-12-28 +0.0299 -
  a 2020-crisis-cluster plus a broad small-delta field. SIBLING CONTROL (decisive):
  prefix10-vs-regen10 - a config KNOWN RIGHT by the committed-bytes recon - differs on
  61.68 pct of days with maxdev 0.000296 = 3 bp, the undercharged-cost signature
  (pre-costfix half-turn-class vs 6.4 full-dW), NO crisis blowout. So the 62-pct broad
  field = the cost convention (both waves), and the crisis cluster = an OLDER
  generation wave in the 06:06 prefix vintage (brwt15/QAxasts/diescrack/dualmom were
  emitted 06:06; brwt10_2000/brwt5_2000 in the 10:51 wave carry current data). The
  prefix CANNOT discriminate brwt15 config on values - measured, disclosed.
- CONFIG TRIANGULATION (what the inference now rests on): lb=15 from the family naming
  (brwt<lb>: 10/7/5 all match their names); zb=1.0 the shared family scalar (ITER34/35
  closed); min_start 2000-01-01 from the emission-start signature - prefix15 starts
  2000-03-30, the SAME signature as the min_start-2000 sibling brwt10, while the
  min_start-2008 siblings start 2008-03-31. Overlap calendar identical (above).
  Residual config risk is DISCLOSED: if the acceptance-era brwt15 differed in any
  fourth aspect not represented in the R6 generator signature, this cell measures the
  R6-convention reconstruction, not the extinct vintage. That is the ONLY admissible
  stream regardless (the fit must not mix cost/data vintages across the brwt block -
  the three siblings enter as costfix bytes).
- log-of-nonpositive RuntimeWarnings from the 2020 WTI prints fire in the R6 generator
  itself; dropna() handles them inside brwt_load/spread construction (same as every
  R6-era run; benign, disclosed).
- Everything else in this precommit stands. The seal is re-newed: the driver asserts
  the sha16 of THIS FILE AS AMENDED.

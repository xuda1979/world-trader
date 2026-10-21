# ITER25 FINDINGS (2026-09-19, session #7) -- HONEST NEGATIVE at the IS concentration
# filter; the reveal never fired (stop rule). Champion UNCHANGED: ITER21 gear-1.0,
# sha16 8559fa55ee9a3417, weights d2d11c92a98683df (pre==post asserted by the driver).

## What was run (per FINDINGS_PRECOMMIT.md sealed 02:44 this session, sha16 d176f7cb8f2f11f5)
Re-adjudication of the standing 8c-only-rejected candidates under the CURRENT champion and
the operator's stated constraint set (max SR s.t. gross<=1.6, ann>=20%). Frozen candidate
set = {A5_r7_credit_composite} (full provenance .meta; standalone battery PASS SR 1.51 /
scramble p=0.000 / plateau / halves / corr-to-library 0.13). Excluded pre-reveal with
reasons: H21_fixed (no .meta), VOL2-R3+CRYPTO2 (standalone bar fails independent of 8c),
RB_hobr (already re-anchored #114, died OOS), CFX4 (dead vendor artifact).

## Anchors (all BEFORE the candidate, this run)
weights maxdev 8.327e-17 / bytes maxdev 9.996e-17 (n=4806) / grossmax 1.000000000 /
incumbent IS-SR 4.198632 (ITER22/23/24 exact continuity) / champ CAGR 23.6054% SR 3.751429
MDD -3.6130%. Champion + weights sha16 pre==post (bytes never written).

## Result: the fit WANTS the credit sleeve; the concentration invariant blocks it
13-pool = champion 12 + A5r7credit, relw = apply_brwt_cap(fit_relw(IS 2008-03-31..<2017-01-01,
shrink 0.70), cap 0.30), gear 1.0:
- relw[A5r7credit] = 19.034% -- the LARGEST single allocation any candidate has ever earned
  in this campaign (bund_02y earned 9.93% in ITER24). The unconstrained fit hits the
  credit sleeve's 2/13 bound and the brwt block's pro-rata redistribution (frozen house
  method, no post-cap clamp -- verified identical to rawew13v2_build.apply_brwt_cap) lifts
  it past the invariant edge.
- IS-SR 4.2575 > 4.198632 -- IS-SR bar PASSED (decisively; only the census bund family and
  cad have cleared it before).
- IS-MDD -2.52% (>= -6% PASS); 0 IS neg years (PASS); CFX4 = 0 exactly.
- **Wmax 2.4745x > 2.0x -- IS filter FAIL -> NO-ADMISSION. No reveal per the sealed stop
  rule. The FS gates (incl. the operator's ann>=20% floor and the 5-bin OOS police) were
  never reached, by design.**

## Reading
1. The gate-8c misalignment (the audit finding that motivated this iteration) is REAL as a
   documentation defect -- 8c's evidence cites superseded champions -- but it is MOOT for
   this candidate: the modern selector rejects credit BEFORE any return-dilution question.
   Two different methods, two different reasons, same verdict: the 2019-era overlay rungs
   rejected credit on 8c dAnn<0; the 2026 pool fit rejects it on the Wmax concentration
   invariant. The frontier statement survives its first adversarial re-audit.
2. This is the ITER23 wall hit from the candidate side, and the strongest evidence yet of
   WHERE the binding constraint bites: the fit's desire for credit (+0.059 IS-SR at 19%
   allocation) sits exactly at the concentration invariant the operator would have to
   relax. Per #109/#116 precedent the campaign does NOT self-relax; this is recorded as an
   OPERATOR-DECISION ITEM, not an iteration: "relax max-share <= 2x equal?" The cost of
   asking is one sentence; the campaign will not act without sanction.
3. Consistency: EM-FX/energy failed IS-SR AND Wmax (double rejection, dead at screen);
   bund/cad passed both and died at OOS honesty (ITER17 law); credit passes IS-SR and MDD
   but is blocked by the invariant. Every path into the book is now catalogued by its
   binding constraint.

## Deviations from the pre-commit: NONE.
(The driver ran the pre-declared amendment branch code path only if admission had
succeeded; it did not fire. The reveal block never executed.)

## Deliverables
- driver_2026-09-19.py + driver_2026-09-19.log (this dir; log = audit trail)
- candidate_A5r7credit_weights.csv + candidate_A5r7credit_daily.csv (emitted for the
  record; NOT a champion, NOT revealed as a book)
- campaign/bt/tests/test_iter25_credit_readj.py: reality-pins with recorded mutation check
- campaign/GOAL100_ITER25_CREDIT_READJ.md: operator-facing decision memo

## Mutation check (recorded, post-FINDINGS)
test_iter25_wmax_blocks_admission mutated (Wmax assertion inverted 2.4745 <= 2.0) -> RED;
restored byte-identical -> GREEN. Full suite after landing: see STANDUP_LOG entry.

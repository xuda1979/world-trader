# GOAL100 ITER27/ITER28 — CENSUS REMAINDER MEASURED-CLOSED (2026-09-19)

Iterations run by session #10 (04:18-04:35, coord/ITER27_CENSUS_REMAINDER +
coord/ITER28_CENSUSREMAINDER_FIX); landing completed and independently verified by
session #11 (memo/standup/memory here; pins and drivers are #10's own, found intact).

**Operator objective (unchanged, 6th verbatim issue):** keep improving; leverage <= 1.6;
maximize Sharpe; annual return >= 20%.

**Champion of record: UNCHANGED.**
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` — sha16
`8559fa55ee9a3417` / weights `d2d11c92a98683df` / CAGR 23.6054% / SR 3.751429 /
MDD −3.6130% / gross 1.0 exact (<= 1.6) / 0 neg yrs.

## What the pair measured

ITER27 sealed the last two census cells that ITER24 had closed WITHOUT measurement:
the 29 cboe non-vol capital-real ETFs (sector/country/bond/credit/metals equity
complex) and the nokcarry two-leg (NOK policy carry + USDNOK). As sealed: ADMITTED
0/30 => honest negative, no reveal, stop rule honored to the letter.

DEFECT DISCLOSED (caught by #10 before any reveal): the sealed Wmax filter coded the
invariant as max_share x 13 <= 2.0 (copied from ITER24_DA), but CFX4 has zero IS
coverage so the covered pool is 12 (fit rows use 11 names) — the recorded scale-free
invariant is max_share x k_covered <= 2.0. Proof of miscalibration: the INCUMBENT's
own committed fit (C5ng share 0.16468 -> 2.1409x in 13-slot units) violates the x13
form — a filter the live champion fails is definitionally wrong.

ITER28 = filter-repair reveal (new sealed pre-commit, driver byte-verbatim from
iter27's except OUT dir / filter normalization / k plumbing): corrected table admits
2/30 — xly_etf REAL (relw 2.806%, IS-SR 4.200683 > 4.198632, Wmax_sf 1.9321x) and
xlf_etf a relw-0.000000 solver-jitter admission (immaterial; lost argmax by 0.002).
Single reveal xly_etf: **FS SR 3.750133 < 3.751429 (−0.0013); OOS dSR bins
+0.0187/−0.0095/−0.0075/+0.0183/−0.0323 = 2/5 positive < 4 required => G7 FAIL =>
REJECT — ITER17 law kill #5** (bund #117, seliccary #117b, credit #119, xly #28).
All operator gates passed on the rejected candidate (ann 23.52% CAGR, gross 1.0,
MDD −3.57%, 0 neg yrs, CFX4 0) — rejection is purely OOS honesty.

## Convention corrections now on the record (landed by #10, pinned)

1. Any future Wmax filter MUST use max_share x k_covered (the fit's own have-count),
   never a fixed 13 — the 13-slot form overstates by 13/12 and the incumbent fails it.
   ITER24_DA's x13 filter was miscalibrated by the same authoring error; its VERDICTS
   are unaffected (every non-admitted row failed IS-SR as well — EM-FX/energy were
   double-dead; no weighted candidate ever exceeded credit's 19.03% largest-ever
   share, so x13 admitted a subset of the x12-admissible and the argmax/reveal
   (bund_02y) is unchanged).
2. Admission tests need a jitter tolerance (e.g. require |relw[S]| > 1e-4 OR
   IS-SR − bar > 1e-4) so zero-weight rows cannot slip in on solver noise (xlf).

## Strategic state after the pair

Every IS-FITTABLE line of DATA_AXIS_CENSUS_2026-09-19.txt now carries a recorded
verdict: bund 8 admitted-on-IS/OOS-rejected; em_rates 6 IS-dead; cad 4 superseded by
the argmax stop rule; eia energy 10 IS-dead; cboe vol complex excluded (not
capital-real, no VIX futures on disk); seliccary OOS-dead; ETF complex 29: 13 exact
duplicates (relw 0.000 — pure re-expression of existing pool exposure), 14 IS-SR-
lowering, slv optimizer-pathology (inadmissible both normalizations), xly IS-alive ->
OOS-dead; nokcarry double-dead (IS-SR + g8 2.21% shrink). **The free-data axis is
closed WITH MEASUREMENT over its whole screened universe.** Frontier: gear (ITER21),
weights (ITER22), grid edges (ITER23), census data (ITER24/#117b/27/28), 8c-era
ledger (ITER25), invariant-legal credit (ITER26) — all closed. Remaining levers:
purchased data (total-return ETF series, VIX futures, regional basis) or operator
rule change — both evidence-contradicted on their best axes.

## Session #11 independent verification (this landing)

- Canonical gauntlet re-run 7/7 (verify_champion_r3_iter29_start.json): weights_repro
  8.327e-17, byte_repro 1.032e-16, cost full_dw ratio 1.000000000, causality causal,
  gross 1.0000000 / n_over 0, 0 neg yrs.
- driver_iter28.py re-executed from a scratch copy (OUT redirected to /tmp):
  verdict block reproduced EXACTLY (argmax xly 4.200683, FS SR 3.750133, bins, G7
  FAIL, REJECT; champion sha pre==post).
- Suite: 515 passed / 0 failed on this session's run (509 baseline + #10's 6 pins +
  the round4b fix below).
- Defect found + fixed on landing: GOAL100_ITER26_CREDIT_CAPFIT.md (written 03:28 by
  session #9 MID-SUITE, after round4b's audit test had already executed) billed the
  champion by sha16 only — the round4b lint requires the champion FILENAME or the
  computed headline. Fixed with the lint's own prescription: ADDITIVE banner naming
  GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv; history untouched. RED (1 failed /
  514 passed) demonstrated before the fix on this session's first suite run.
  Lesson recorded: never land campaign docs while a suite run is in flight — the
  audit glob is evaluated at test-execution time.

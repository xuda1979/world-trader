# MANIFEST_R5 — bench pack for the V2 §8 blend battery (DATA_ETF_MORE round 5)

Charter corner (a): extend the ETF overlay bench (spy/ief/cta trio = minimum) with
1-2 DECORRELATED PASSIVE benches, keyless sources, PIT lint + byte-stable manifest.
No signal hunting: no sleeve, no gates.run candidate battery, no blend perf claim.

## Deliverable
`tools/quant/data/bench_r5/manifest.csv` — 10 rows, byte-stable across independent
process invocations (build1 == build2 == committed, sha256 326afe5a28db2809...).

- trio_pinned (3, PIN): the §7c trio, verified byte-identical to the R2 vintage,
  NOT re-fetched:
  - SPY  tools/quant/data/twelvedata/SPY.csv            sha16 d35d72808dcc9fc3
  - IEF  tools/quant/data/more_etf/IEF.csv              sha16 603cb2a56afd5616
  - CTA_15vol campaign/results/sleeve_library/CTA_15vol.csv sha16 d7f3b5cd4616f0f4
- decorrelated_passive (2, SELECTED) — the round's addition:
  - UUP (dollar index):  max|corr| vs trio 0.1833, corr_champ 0.0028, 2007-03-01,
    n=4911, PASS_WAIVER (span_class 2007plus disclosed)
  - GLD (gold):          max|corr| vs trio 0.2043, corr_champ 0.0119, 2004-11-18,
    n=5483, PASS (pre2007)
- eligible_not_selected (4): SLV 0.2294 / IAU 0.2056 / GSG 0.3705 / DBC 0.3789 —
  all pass the corr bar but the greedy cap is 2; IAU/SLV additionally
  near-duplicate GLD (gold complex, PAIR_CORR_MAX 0.7 rule).
- candidate_rejected (1): TIP — the pre-registered CONTROL, rejected for the
  expected reason: corr_ief 0.7635 > 0.5 (rates beta, not decorrelated).

## Pre-registered rule (encoded in work_r5/test_bench_r5.py BEFORE measurement)
Candidates a-priori: GLD SLV IAU DBC GSG UUP (+TIP control). Equity beta, rates/
credit, and stale-print commodity singles rejected a-priori on asset-class grounds
(no measurement, no fishing). Eligible iff: R3 lint PASS/PASS_WAIVER, span>=8y,
>=1008 common daily obs vs EVERY trio member, max|corr| vs trio <= 0.5. Rank by
max_corr_trio asc then span desc; take up to 2, skipping |corr|>0.7 vs an
already-taken bench. Correlations on COMMON dates only — no fill, no pad, no
synthetic alignment. Same-period daily pct-returns, price series pct_change'd,
ret curves pass-through (R3 beats_passive re-differencing bug class avoided).

## Lint discipline (PIT, unchanged from R3/R4)
Gates: n>=250, dups==0, maxgap<=10d, |ret|>50% on 1d == 0 rows, fresh end
(>2026-09-01 minus ~3.25y -> all candidates end 2026-09-02/04), span_class
{pre2007, 2007plus, inception_fail} on every row; inception_fail never written.
Fail-closed re-verified by test_failclosed_rejects_bad_bench (40-day-gap fabricated
frame -> FAIL, never selected).

## Reproduce
  python3 campaign/agents/chief/coord/DATA_ETF_MORE/work_r5/bench_r5.py
  python3 -m pytest campaign/agents/chief/coord/DATA_ETF_MORE/work_r5/test_bench_r5.py   # 8/8

## Consumption smoke (NOT a performance claim)
Through bt.beats_passive.evaluate on the champion span with production caller
convention (prices pct_change'd by caller, CTA curve pass-through; loader verified
by champion SR reproducing the charter pin 3.1810 exactly):
  spy_bh 0.5863 | sixty_forty 0.5916 | cta_trend -0.1097 (best = sixty_forty).
bt.blend.blend_nets accepts a selected bench on the common index mechanically and
raises on misalignment (asserted in T8). Champion of record untouched:
sha 4358dfab95679b97 (re-verified end-of-round).

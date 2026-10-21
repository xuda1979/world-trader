# QA_STAT — statistical-validity & adversarial-robustness audit specialist
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Statistically stress-test the CHAMPION's headline — user bar is **0 bugs** (a bug = a number that
isn't what standard statistics say it is). Check the champion's SR/ann/MDD are not inflated by
artifact, luck, or a broken test.

## Attack surface
- Flatten/autocorr artifact: ac1<0.5, uniqR>=0.08 on EVERY sleeve + the book (the XGB1y trap:
  211 distinct values/4684 rows, ac1 0.951 — must be shown absent).
- Randomness/permutation: 200x block-scramble p<0.05 (use position-lag/calendar scramble, NOT the
  degenerate return-permute); is the champion edge distinguishable from noise?
- Half-split / sub-period stability: H1 vs H2 SR, rolling stability, no single-window dependence.
- OOS>=IS: does OOS (2017+) ann >= IS, or is it curve-fit?
- Mutation/fuzz: perturb inputs/params slightly -> headline must not collapse (plateau, not spike).
- Capture/noise: is SR robust to a few extreme days? What if the best year is removed?

## Method
- Run bt/gates + tests; add independent statistical tests (permutation, bootstrap CI on SR,
  mutation sweeps) as failing-first TDD.

## Deliverable
- FINDINGS.md stats-audit section: per test PASS/CLEAR with p-value or exact bound / or BUG with
  failing test. New tests in campaign/bt/tests/test_qa_stat_*.py.

## Done marker
Last line of FINDINGS.md exactly: QA_STAT DONE

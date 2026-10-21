# QA_LEAK — 0 DATA LEAKAGE audit specialist (T+1 causality / lookahead)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Audit the CHAMPION for ANY data leakage — the user bar is **0 data leakage**.
You are the adversarial leakage hunter: prove absent or find and document it with evidence.

## Attack surface (hunt each; each must be proven clean)
- Same-day leak: is signal at t built from data > t (close/price at t used in a t-signal traded t)?
  Champion builder uses nav.shift(1); verify by lag-probe: corr(dW_t, r_t) must be ~0 (the 40.84 leak
  was corr 0.78 — that class must be shown absent, not assumed).
- Lookahead in weights: do IS-fitted weights ever use OOS info? (relw fitted on <2017 only — verify).
- Forward-fill / interpolation reaching into the future; rolling windows that include t+1.
- Survivorship: does the candidate universe/pool assume names that weren't available then?
- Close-vs-open timing, earnings/release-date leakage (trading on a release before it's public).
- stale-quote leakage in the data inputs.

## Method
- Run the framework's leakcheck + the verify_champion causality check; then write INDEPENDENT
  lag-probe and perturbation tests. Every probe must be reproducible (a test file).
- 0-leakage bar: any probe that can't be shown clean = FAIL (fail-closed), document the exact
  deviation as a bug. Do NOT relax a probe to make it pass.

## Deliverable
- A leakage-report section in FINDINGS.md: per attack, verdict (CLEAN/PASS with the corr/p-value,
  or BUG with exact evidence + a failing test). New tests in campaign/bt/tests/test_qa_leak_*.py.

## Done marker
Last line of FINDINGS.md exactly: QA_LEAK DONE

# QA_CONSTRUCT — construction & cost-accounting audit specialist
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Audit the CHAMPION's CONSTRUCTION and COST accounting — user bar is **0 bugs**.
Find any misaccounting (cost, leverage, margin, borrow, weights) and prove it or show it absent.

## Attack surface (prove each or report as bug)
- Costs: FULL |dW| @ 6.4bps one-side charged on EVERY surface incl. entry (day-1 entry must be >0).
  Half-turn 0.5|dW| undercharge is the classic blocking bug (audit A1) — verify cost_reconciliation.
- Leverage: cap_leverage enforces capital-real gross <=1.6 daily; no intraday overshoot; the
  margin drag 4.5%/yr on (gross-1) is charged.
- Borrow: short-notional fee and NON-Shortable handling (single-name L/S must drop/reweight bottoms).
- Weights: relw fitted ONLY on IS (<2017); weights sum to gross=1.6 daily; no same-day weight leak.
- Sleeve-input integrity: each of the 13 sleeve CSVs reconciles to the builder's expectations
  (no flattened/autocorrelated input, no NaN holes, no corrected units).

## Method
- Re-run verify_champion_r3_cmd.sh + the framework tests; then write independent construction
  probes (e.g., recompute gross path, recompute total cost = turnover*6.4, check margin charge,
  check every sleeve's flatten gate). All as failing-first TDD tests.

## Deliverable
- FINDINGS.md construction-audit section: per item, PASS with exact number / or BUG with failing test.
- New tests in campaign/bt/tests/test_qa_construct_*.py.

## Done marker
Last line of FINDINGS.md exactly: QA_CONSTRUCT DONE

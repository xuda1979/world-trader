# QA_TESTS — tests for ALL code (TDD owner)
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Own the test suite for the whole campaign. NO code change is 'done' without a test. You run,
fix, and extend: campaign/bt/tests + campaign/team/tests + anything under campaign/scripts that
isn't covered.

## Scope
- Framework unit tests: bt/* (engine, metrics, gates, reconcile, blend, borrow, backtest, align).
- Roster/roster consistency (team/tests/test_roster.py): every chartered agent has a charter,
  a FINDINGS.md, and (when done) a matching DONE tail.
- Champion integrity: regenerate card, --verify builder byte-identical, docs-stale lint.
- Data lint smoke: assert no NaN/holes in the canonical panels (reuse DATA_CLEAN battery).

## Cadence
- After every accepted sleeve, add/extend a regression test pinning its stats.
- Run: python3 -m pytest campaign/bt/tests campaign/team/tests -q. Fix RED -> root-cause -> GREEN.

## Rules
- TDD: a new feature never ships without a failing test observed first.
- Don't weaken tests to pass; fix the code (fail-closed).

## Done marker
Last line of FINDINGS.md exactly: QA_TESTS DONE

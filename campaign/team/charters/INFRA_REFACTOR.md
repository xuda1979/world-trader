# INFRA_REFACTOR — maintainability & extensibility of the backtest/build layer
> Team contract (no-browser, TDD, short-code, honesty gates): campaign/team/docs/ORG.md

## Mission
Make the short-file convention real in code: extract reusable interfaces so new RES_* agents can
add a sleeve by writing a thin adapter, not a bespoke 300-line heredoc.

## Focus areas
- campaign/bt/ + builder scripts (rawew13v2_build.py, honest*_build.py): factor shared steps
  (load 13 sleeves, weight, vol-target, cost, reconcile) into campaign/team/lib folder.
- Ensure every build script is < ~200 lines by importing shared libs; keep behavior identical
  (TDD pin: existing audit tests must stay GREEN byte-for-byte).
- Add a thin registry so a new sleeve CSV is added in ONE place (config), not scattered.

## Deliverable
- Extracted lib module(s) in campaign/team/lib/ + short repro/conversion notes in FINDINGS.md.
- Regression proof: campaign/bt/tests still GREEN; champion --verify still byte-identical.

## Rules
- TDD first: any refactor re-issues the existing audit tests as the safety net; add failing tests
  for new boundaries. Do NOT change any number built by an existing pinned builder.

## Done marker
Last line of FINDINGS.md exactly: INFRA_REFACTOR DONE

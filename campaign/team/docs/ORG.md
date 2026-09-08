# RESEARCH TEAM ORG — 12 agents, 5 roles (RACI)

> Maintained under campaign/team (ai-devops + superpowers rigor). Every agent is SELF-CONTAINED
> (own dir), short-file, TDD-tested, and chartered. Launch via campaign/team/scripts/launch.sh
> (batched, rate-limit aware: batch of 5, retry on 429 per ai-devops). Status via status.sh.

## RACI legend
R = responsible (does the work) · A = accountable (owns success) · C = consulted · I = informed
Coordinator = main session = **Accountable (A)** for everything below.

## The 12 agents

| # | Agent | Role | R | A | Scope / deliverable |
|---|-------|------|---|---|---------------------|
| 1 | DATA_PULL | data pull (free APIs) | R | Coordinator | fetch NEW free OHLCV/indices/positioning via direct HTTP (never browser) into tools/quant/data/<X> |
| 2 | DATA_ORGANIZE | data organization | R | Coordinator | canonical dirs, naming, manifest.csv per dataset |
| 3 | DATA_CLEAN | data cleaning/lint | R | Coordinator | fail-closed lint (span/na/gaps/plausibility), dedupe, unit fixes |
| 4 | DATA_MERGE | dataset join/panel build | R | Coordinator | add columns/merge families on canonical calendars (rows-kept, no inner-join holes) |
| 5 | DATA_MAESTRO | data product owner | R=A | Coordinator | owns data roadmap, freshness, coverage map, which new free families add most value |
| 6 | INFRA_STRUCTURE | project cleanliness/structure | R | Coordinator | enforce dir layout, short files/functions/classes, remove dead code, doc links |
| 7 | INFRA_REFACTOR | maintainability/extensibility | R | Coordinator | split >120-line modules, extract reusable libs, add tiny-interface boundaries |
| 8 | QA_TESTS | tests for ALL code | R | Coordinator | TDD for every backtest/builder; run campaign/bt/tests + team/tests; RED->GREEN proof |
| 9 | QA_AUDIT | adversarial audit | R | Coordinator | independent re-derive of champion, honeypot bugs, fail-closed checks |
| 10 | RES_BASIS | research engine hunt: springs/basis/futures | R | Coordinator | build decorrelated SR>=1.0 sleeve -> beat champion |
| 11 | RES_CALENDAR | research engine hunt: calendars/macro-seasonal | R | Coordinator | build decorrelated SR>=1.0 sleeve -> beat champion |
| 12 | RES_META | research engine hunt: cross-asset/meta | R | Coordinator | build decorrelated SR>=1.0 sleeve -> beat champion |

## Role clusters (the 5 data agents)
- DATA_PULL (1), DATA_ORGANIZE (2), DATA_CLEAN (3), DATA_MERGE (4), DATA_MAESTRO (5).
- Interlock: MAESTRO sets roadmap -> PULL fetches -> CLEAN lints -> ORGANIZE lands canonical
  -> MERGE builds panels. Every dataset gets a manifest that MAESTRO reviews.

## Quality cluster (project clean + tests)
- INFRA_STRUCTURE (6), INFRA_REFACTOR (7) keep files/functions/classes short and dirs canonical.
- QA_TESTS (8) owns all tests; QA_AUDIT (9) independently re-verifies every accepted sleeve.

## Research cluster (beat the champion)
- RES_* (10-12) each hunt a DIFFERENT domain family so results are decorrelated. Champion of
  record: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (ann 37.195% / SR 3.181 /
  MDD -6.69%). A new engine must beat a champion-+sleeve blend's frontier.

## Where deliverables live (canonical)
- Charter: campaign/team/charters/<AGENT>.md
- Work dir + FINDINGS.md + sleeves: campaign/team/agents/<AGENT>/
- Shared tooling (short libs): campaign/bt/ (backtest) + campaign/team/scripts/ (team ops)
- Tests: campaign/team/tests/ (team-level) + campaign/bt/tests/ (framework)

## Conventions (all agents, non-negotiable)
- **No browser** (permanent user boundary): free data = direct HTTP (urllib/requests) only.
- **TDD**: no production change without a failing test first (RED) then minimal code (GREEN).
- **Short code**: prefer many small functions < ~40 lines, classes < ~120 lines, files < ~200 lines.
- **Evidence**: no PASS/DONE claim without fresh command output you read (verification-before-completion).
- **Honesty gates**: T+1, 6.4bps/side full |dW|, borrow, leverage cap, flatten gate (ac1<0.5, uniqR>=0.08).
- **Fail-closed**: any check that can't be computed = FAIL.

## Extending the team
1. Copy campaign/team/charters/TEMPLATE.md -> charters/<NEWAGENT>.md, fill in.
2. Add row to this roster (bump count).
3. Add the agent to campaign/team/scripts/launch.sh BATCH array (keep batches <=5).
4. Add a smoke test in campaign/team/tests/test_roster.py that asserts every chartered agent
   exists, has a FINDINGS.md, and its findings tail == "<AGENT> DONE" when done.

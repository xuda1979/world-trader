# RESEARCH TEAM ORG — 27 agents (10 data, 2 infra, 5 audit/QA, 10 research)

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
| 21 | DATA_EDGAR | new free data: SEC EDGAR fundamentals | R | Coordinator | US financial statements (rev/income/assets) via EDGAR XBRL, no key, direct HTTP |
| 22 | DATA_AKSHARE | new free data: AKShare broad market | R | Coordinator | A-share/HK/global commodity/rates/currency breadth via AKShare (no key) |
| 23 | DATA_YFIN | new free data: yfinance global | R | Coordinator | extend equity/ETF/FX universe via yfinance (no key), long daily OHLCV |
| 24 | DATA_FXHIST | new free data: 160-currency FX history | R | Coordinator | broad cross-rate matrix (1999+) via ECB/reference APIs, long span |
| 25 | DATA_ALTLIB | new free data: no-key alt libraries | R | Coordinator | CoinPaprika/CoinGecko/efinance/ml4t breadth & alt regime series (no key) |
| 6 | INFRA_STRUCTURE | project cleanliness/structure | R | Coordinator | enforce dir layout, short files/functions/classes, remove dead code, doc links |
| 7 | INFRA_REFACTOR | maintainability/extensibility | R | Coordinator | split >120-line modules, extract reusable libs, add tiny-interface boundaries |
| 8 | QA_TESTS | tests for ALL code | R | Coordinator | TDD for every backtest/builder; run campaign/bt/tests + team/tests; RED->GREEN proof |
| 9 | QA_AUDIT | adversarial audit | R | Coordinator | independent re-derive of champion, honeypot bugs, fail-closed checks |
| 18 | QA_LEAK | 0-DATA-LEAKAGE audit | R | Coordinator | T+1 causality / lookahead / same-day-leak / survivorship — prove clean or find bug |
| 19 | QA_CONSTRUCT | construction & cost audit | R | Coordinator | costs FULL-|dW|@6.4, leverage cap, margin, borrow, weights-IS, sleeve integrity — 0 bugs |
| 20 | QA_STAT | statistical-validity audit | R | Coordinator | flatten/ac1/uniq, 200x scramble, halves, OOS>=IS, mutation/fuzz robustness — 0 bugs |
| 10 | RES_BASIS | research engine hunt: basis/futures | R | Coordinator | decorrelated SR>=1.0 sleeve -> beat champion |
| 11 | RES_CALENDAR | research engine hunt: calendars/macro-seasonal | R | Coordinator | decorrelated SR>=1.0 sleeve -> beat champion |
| 12 | RES_META | research engine hunt: cross-asset/meta | R | Coordinator | decorrelated SR>=1.0 sleeve -> beat champion |
| 13 | RES_VOL | research: volatility/options-implied | R | Coordinator | VIX 9d/3m/6m term-slope + vol-of-vol engines (new CBOE data) |
| 14 | RES_CREDIT | research: credit spreads/surveys | R | Coordinator | HY/LQD OAS + credit-regime engines (decorrelated to equity mom) |
| 15 | RES_CARRY | research: FX/commodity carry | R | Coordinator | multi-pair FX carry/deep carry (beyond CFX4) |
| 16 | RES_REVERSAL | research: short-horizon cross-sectional reversal | R | Coordinator | reversal on wide equity panels (champion is momentum-heavy) |
| 17 | RES_STATARB | research: relative-value/stat-arb | R | Coordinator | pairs/sector-relative mean-reversion on big panels |
| 26 | RES_FXSTYLE | research: cross-sectional FX factors | R | Coordinator | FX carry/momentum on NEW 508-pair fx_hist (1999+), decorrelated to equity |
| 27 | RES_ALTDATA | research: alt/regime engine | R | Coordinator | alt-regime / DeFi-TVL / fear-greed signal from NEW altlib data (fail-closed short spans) |

## Role clusters (the 10 data agents)
- Pipeline (1-5): DATA_PULL, DATA_ORGANIZE, DATA_CLEAN, DATA_MERGE, DATA_MAESTRO.
- New-source agents (21-25): DATA_EDGAR (SEC XBRL fundamentals), DATA_AKSHARE (broad market),
  DATA_YFIN (yfinance global extension), DATA_FXHIST (160-currency FX), DATA_ALTLIB (no-key alt).
- Interlock: MAESTRO sets roadmap -> PULL/source agents fetch -> CLEAN lints -> ORGANIZE lands
  canonical -> MERGE builds panels. Every dataset gets a manifest that MAESTRO reviews.

## Audit/test cluster (5 agents — the 0-bugs / 0-data-leakage gate)
- QA_TESTS (8): owns ALL tests; runs campaign/bt/tests + team/tests; TDD regression pins.
- QA_AUDIT (9): independent byte-repro re-derivation of the champion; honeypot/fail-closed audit.
- QA_LEAK (18): **0 data leakage** — T+1 causality, same-day leak, lookahead, survivorship (corr(dW_t,r_t)~0).
- QA_CONSTRUCT (19): **0 bugs** in construction/cost — FULL-|dW|@6.4bps, leverage cap, margin, borrow, IS-weights, sleeve integrity.
- QA_STAT (20): **0 bugs** in statistics — flatten/ac1/uniq, 200x scramble, halves, OOS>=IS, mutation/fuzz.
- Together = the user's "0 bugs, 0 data leakage is acceptable" gate on any champion before it's quoted.

## Research cluster (beat the champion)
- RES_* (13-17, 26-27) each hunt a DIFFERENT domain family so results are decorrelated. Champion of
  record: campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (ann 37.195% / SR 3.181 /
  MDD -6.69%). A new engine must beat a champion-+sleeve blend's frontier.
- FIRST STEP is ALWAYS the decorrelation-first filter (lib/corr_gate.py, |corr|<0.15 to champion)
  before any backtest (item 2). 10 research agents = 10 orthogonal families (incl. RES_FXSTYLE on
  the NEW 508-pair FX history and RES_ALTDATA on alt data) = best shot at the >=2 more SR>=1.5,
  corr<0.1 engines the honest frontier needs (docs/TARGET_DECISION.md).

## Extending the team (bump count here and in README + test_roster + launch.sh batch)

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

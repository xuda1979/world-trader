# campaign/bt — REUSABLE + TESTABLE backtest framework (GOAL100)

Short, honest, dependency-light core for ALL backtests in the campaign. Every module is small and
has tests in `campaign/bt/tests/` (TDD). **All new hunts SHOULD build on this, not on new heredocs.**

## Modules (each < ~100 lines, one responsibility)
| module | purpose |
|---|---|
| `bt/engine.py` | T+1 `lag_signal`, trailing no-lookahead `vol_target_scale`, `capital_gross`, `cap_leverage`, `cost_turnover`, `borrow_cost`, `margin_cost` (IBKR call rate) |
| `bt/metrics.py` | `ann_geo/arith`, `sharpe_d/m`, `max_dd`, `neg_years`, `half_split`, `report` |
| `bt/gates.py` | acceptance battery: `run()` (SR/H1H2/negyr/ac1/uniq/corr), `uniq_ratio`, `zero_runs_long`, `position_lag_scramble`, opt-in `beats_passive=True` mandatory beats-passive gate (default OFF) |
| `bt/beats_passive.py` | MANDATORY beats-passive gate (INTL2 R3): matched-span net benchmarks — SPY B&H (1× 6.4bps entry, T+1), 60/40 SPY-IEF monthly-rebalanced (full \|dW\| costs), CTA_15vol 10% VT proxy — candidate net SR must STRICTLY beat the best (ties fail, fail-closed on missing/unmeasurable benchmarks) |
| `bt/reconcile.py` | `max_abs_diff`, `repro_ok`, `ledgers_reproduce` (ledger PnL == champion), `turnover_reconciles` (TRADE_RECORD_STANDARD) |
| `bt/backtest.py` | high-level `sleeve()` and `book()` runners tying the above together |
| `bt/borrow.py` | `margin_daily/ann`, `gross_exact` (fail-closed 1e-9), `borrow_tier_uplift`, `rate_path`/`spike_window` (fail-closed on pre-index/after-end windows), `margin_daily_path`, `scenario_net`, `path_metrics` |
| `bt/blend.py` | constant-mix champion+sleeve blends; margin charged ONCE on blended gross−1 (sign-fixture-pinned) |
| `bt/financing_stress.py` | CAMP_BORROW R4 tool: given a net series + gross path, emit the call-rate rung ladder (per-rung ann/SR/MDD deltas, arithmetic slope exactly −(gross−1)pp/+1pp), named rate-path scenarios, borrow-tier block — one JSON-able `stress_table()`; fail-closed on missing/misaligned/non-finite inputs; `gate_moves` = neg_years>0 or MDD≤−7% |

## Run tests
```
python3 -m pytest campaign/bt/tests/ -q
```

## Honesty contracts (enforced + tested)
- **T+1 / no lookahead**: `lag_signal` shifts by 1; `vol_target_scale` scale at row t uses returns
  r[0..t-1] only (verified by perturbation test). 
- **Leverage**: `cap_leverage` enforces max capital-real gross per day; `margin_cost` charges only
  on (gross−1)⁺ at an IBKR-style annual rate (default 4.5%).
- **Costs**: `cost_turnover` = 0.5·Σ|dw|·bps; `borrow_cost` on short notional (default 0.5%/yr).
- **Flattening gate**: `uniq_ratio`<0.08 or ac1>0.5 flags a flattened/autocorrelated fake-daily sleeve
  (the XGB1y trap).

## Conventions
- Annualization 252 (daily), geometric ann in `report`.
- `cap_leverage` is a DAY-LEVEL cap (not per-instrument cap); the committed builders cap the
  vol-targeted weight path identically.

## Ownership
Coordinator: daxu (main session). If you find a bug, add a failing test first (TDD), fix, verify RED
→GREEN, and record in your FINDINGS.md + this file.

## AUDIT_FRAMEWORK verdict (2026-09-03, iter7 adversarial audit — READ-ONLY audit, 10 bugs found)
Adversarial audit of engine/metrics/gates/reconcile/backtest: 10 confirmed bugs (regression tests in
`campaign/agents/loop_team/AUDIT_FRAMEWORK/tests_audit_bt.py`, class TestAuditRED — all 10 RED vs
current code, 9 GREEN behavior locks pass). HEADLINES:
1. **COST MISMATCH (blocking)**: `cost_turnover` charges `0.5*|dw|*6.4bps` = 3.2bps per unit |dw|;
   committed champion reb stream charges `|dw|*6.0bps` and TRADE_RECORD_STANDARD min is `|dw|*6.4bps`
   one-side. Framework undercharges 1.875x vs champion reb stream -> PnL from bt cannot reconcile.
2. **Entry trade never charged** in `backtest.sleeve()` AND `backtest.book()`: weights row0 is NaN
   (from shift), `diff()` -> NaN -> entry (0->w) costs 0. Verified: book() first net 0.0 vs -2.56e-4.
3. `vol_target_scale`: row0 all-NaN (docstring claims NaN-free); `window` param is DEAD (verified
   max|s(window=10)-s(window=200)|=0.0 on non-NaN rows).
4. `metrics.ann_geo`: ruin day r<-1 can return FALSE POSITIVE ann (+432% on [1%, -200%, 1%]).
5. `reconcile` fails OPEN: `turnover_reconciles` passes when pos_path turnover is 0 but ledger qty>0
   (rel NaN -> filled 0); `ledgers_reproduce` passes with partial date coverage (join='inner' drops
   missing champion days); `repro_ok` ignores mismatches hidden in NaN rows.
6. `cap_leverage` strict bound violated by 2.2204e-16 on a deterministic input (float overshoot);
   `margin_cost(max_lev=...)` param is dead; `borrow_cost` docstring says 0.5x but code charges 1.0x
   short notional (code matches champion; docstring wrong).
7. `gates.zero_runs_long` miscounts leading/trailing runs by 1 (drops first/last row: 25-run -> 24).
`backtest.py` appeared mid-audit (uncommitted at session start). Fixes belong to a bt-owner wave;
do NOT trust bt cost/borrow defaults until #1/#2 are fixed and re-reconciled to the champion.

# campaign/bt — REUSABLE + TESTABLE backtest framework (GOAL100)

Short, honest, dependency-light core for ALL backtests in the campaign. Every module is small and
has tests in `campaign/bt/tests/` (TDD). **All new hunts SHOULD build on this, not on new heredocs.**

## Modules (each < ~100 lines, one responsibility)
| module | purpose |
|---|---|
| `bt/engine.py` | T+1 `lag_signal`, trailing no-lookahead `vol_target_scale`, `capital_gross`, `cap_leverage`, `cost_turnover`, `borrow_cost`, `margin_cost` (IBKR call rate) |
| `bt/metrics.py` | `ann_geo/arith`, `sharpe_d/m`, `max_dd`, `neg_years`, `half_split`, `report` |
| `bt/gates.py` | acceptance battery: `run()` (SR/H1H2/negyr/ac1/uniq/corr), `uniq_ratio`, `zero_runs_long`, `position_lag_scramble` |
| `bt/reconcile.py` | `max_abs_diff`, `repro_ok`, `ledgers_reproduce` (ledger PnL == champion), `turnover_reconciles` (TRADE_RECORD_STANDARD) |
| `bt/backtest.py` | high-level `sleeve()` and `book()` runners tying the above together |

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

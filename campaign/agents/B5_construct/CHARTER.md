# B5_construct — MISSION: Portfolio construction to maximize return per unit MaxDD

## OVERRIDING GOAL
20y, SR>=2, ann>=50%, MaxDD<=8%, 6bps/side, free data, no leverage, OOS. You are the
PORTFOLIO / CONSTRUCTION agent. Others generate sleeves; you figure out how to combine
them (plus the existing 55-sleeve library + champion + h21 XGB books) to hit the target.
The binding constraint: current vol-targeted EW blend gives ann 50% at 22% vol but MaxDD -18%.
You need to squeeze the MAXIMUM ann per unit MaxDD.

## What exists (all on disk)
- Champion: campaign/results/WORLDTRADER8_daily.csv (8-sleeve, ann 20%, MaxDD -12%).
- Sleeve library: campaign/results/sleeve_library (42+ sleeves) + agents A1-A6/B1-B4 sleeves.
- h21 XGB books: tools/quant/reports/xgb_horizons/{h21_book_daily_f5,h21_breadth_gate_daily}.csv
- Harness: campaign/harness/{blend4.py, eval.py, data.py}. Read blend4.py for the canonical method.
- A key finding: vol-targeted EW of 15 sleeves -> ann 50%@22%vol, MaxDD-18%; ann25%@8%vol, DD-7.9%.

## Ideas (construction / capital allocation / risk engineering)
1. **Max-Sharpe / risk-parity with a DRAWDOWN objective**: solve weights that maximize
   ann/annum-MaxDD (Calmar) instead of Sharpe. Use only forward/expanding covariance
   (trailing, shift-1) — no lookahead in weights. Report IS vs OOS (weights frozen post-fitting).
2. **Tail-aware weight reduction**: dynamically cut weights of sleeves that currently hold
   regime losses (rolling 63d return), shift-1, with hysteresis to avoid whipsaw.
3. **Hard vol cap + drawdown throttle**: vol-target but add a TRAILING drawdown governor
   (reduce gross when trailing DD>threshold). This is conventional risk management, honest
   if trailing-only. Test DD/ann ratio across thottle params.
4. **Correlation-sparsified selection**: pick the subset of sleeves that maximizes
   diversification (min mean |corr| AND max SR) — a smarter pool than the 15 I tested.
5. **Regime-based sleeve emphasis**: shift allocation toward decorrelated sleeves in stress
   (trailing VIX/credit regime), shift-1. Report whether this beats static.
6. **All of the above combined** — build the best (ann% | MaxDD<=8%) portfolio you can.

## CRITICAL HONESTY
- WEIGHTS/MANAGEMENT must be TRAILING-ONLY (shift-1). Fitting weights on full-sample then
  reporting full-sample MaxDD is LOOKAHEAD. Every construction must be evaluated with
  expanding-window / walk-forward discipline: fit weights on train, freeze on test.
- Report BOTH IS (2008-2016) and OOS (2017-2026) for your final construction, and the
  per-decade yearly P&L.
- Costs: 6bps one-side on rebalancing turnover of the Sleeve blend itself.
- No leverage (weights sum to 1, no borrowing). Vol-targeting is gross intensity, allowed.

## DELIVERABLE
campaign/results/B5_CONSTRUCT_*.csv (daily + monthly) with full stats + IS/OOS split,
the weight scheme, and an honest FRONTIER table: across construction params, what is the
max ann% achievable subject to MaxDD<=8%? State clearly the wall and what more is needed.
Save repro script campaign/scripts/b5_construct.py. Last line: ROUND 1 DONE

# Campaign brief for every research agent

## MISSION
Campaign goal: a 20-year (2006/2008-2026) backtest, **annualized Sharpe >= 2.0**,
net of 6 bps one-side costs, free data only. Route to SR 2: MANY low-correlation
sleeves, blended. Your job: contribute validated sleeves (SR >= 0.6 FULL window,
robust across halves, low corr to the library).

## HONESTY CONTRACT (violations = sleeve rejected)
1. No lookahead: signal at t uses data <= t; trade at t+1 (T+1 execution).
2. Costs: subtract 6 bps x one-side turnover from gross returns (apply_cost in harness/data.py).
3. Gates (ALL required, else do NOT save the sleeve — report in FINDINGS.md):
   a) FULL-window SR >= 0.6 after costs
   b) param-plateau: chosen params sit on a plateau (neighbors within 20% of peak SR; no isolated spike)
   c) halves: H1 (first half) SR >= 0.3 AND H2 (second half) SR >= 0.3
   d) yearly: <= 2 negative years, each > -5%
   e) signal-scramble: shuffle signal vs returns 200x — real SR > 95th pctile of scrambled
   f) economic rationale (2-3 sentences) in .meta
   g) vol-target ~10% ann using ONLY trailing data (expanding window, min 60d)
4. Save per contract: `campaign/scripts/{name}.py` (reproducible), sleeve CSV at
   `campaign/agents/<agent>/sleeves/{name}.csv` [date, ret] + `{name}.csv.meta`
   (rationale, params, validation results incl. scramble p-value).
5. Do not modify other agents' dirs or the shared library.
6. Be honest: failed gates -> FINDINGS.md entry, next idea. Iterate quickly.

## DATA (all free, on disk; canonical paths)
- Panel: /Users/daxu/software/world-trader/tools/quant/data/twelve_big (298 names, OHLCV 2006-09..2026-08)
- Extended panel: /Users/daxu/software/world-trader/tools/quant/data/twelve_extend (440 names)
- Shared loaders: /Users/daxu/software/world-trader/campaign/harness/data.py
  (closes(), volumes(), ff_factors(), ff_mom(), fred(name), fx)
- FF factors+momentum: /Users/daxu/software/world-trader/tools/quant/data/ff_factors (daily, 1926+)
- Macro: /Users/daxu/software/world-trader/tools/quant/hedge_fund_strats/data_fred
  (vix, dxy, us10y, us2y, t10y2y, hy_oas, xau, wti, brent, spx, tbill3m, aaa, baa, copper_monthly, natgas, slv, dow)
- FX: /Users/daxu/software/world-trader/tools/quant/data/fx (8 pairs, 2007+)
- Fundamentals annual: /Users/daxu/software/world-trader/alphaportfolio_replication/data/fundamentals_annual.parquet
  (7451 rows: equity, total_assets, net_income, revenue, cogs, cash, debt, shares, ...)
- Prior validated sleeves: /Users/daxu/software/world-trader/campaign/results/sleeve_library (40; best SR 0.87)
- Eval: python3 /Users/daxu/software/world-trader/campaign/harness/eval.py <csv>

## COORDINATOR
Periodically blends best-of-library + new sleeves into campaign/results/blend_report.md.
Target: >= 8 sleeves, mean pairwise |corr| < 0.15, all SR >= 0.6, both halves positive.
Report ideas in campaign/ideas.md; log every run in campaign/agents/<agent>/LOG.md.

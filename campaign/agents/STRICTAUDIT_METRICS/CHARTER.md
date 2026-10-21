# STRICTAUDIT_METRICS — adversarial recomputation of EVERY headline number (read-only)

TARGET: campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv  [date,ret], n=4522, 2008-03-31..2026-07-31.

CLAIMED HEADLINE (verify each independently, do NOT trust — recompute from the CSV):
  ann 49.4% | SR 5.24 (daily) / 3.46 (monthly, bootstrap CI [3.02, 4.01]) | MaxDD -6.1%
  0/19 negative years (lowest year 2026-partial +20.7%, best 151.1% 2023) | OOS 2017+ 55.9% @ -6.1%
  span 17.9y | "every 3y and calendar-year window DD <= -6.1%"

YOUR JOBS (exact numbers, no hand-waving):
1. RECOMPUTE all headline stats from the CSV alone using YOUR OWN code (do not use
   harness/eval.py only — write independent pandas/numpy): ann return, ann vol, daily SR,
   monthly SR, MaxDD (full series), per-calendar-year returns, OOS 2017+ stats, full-row count,
   actual first/last date and span in years. Compare to every claimed value; report diffs.
2. BOOTSTRAP on MONTHLY returns: resample months (block or iid, report which) 5,000x, build the
   95% CI on the monthly Sharpe. Does [3.02, 4.01] reproduce? Also compute the daily-SR CI.
3. WINDOW-DD CLAIM: verify "every 3-year subwindow DD and every calendar-year DD <= -6.1%".
   Slide a 3y (756-trading-day) window across the whole series; compute each window's max
   drawdown; list ANY window with DD worse than -6.1%. Then compute every calendar-year DD.
4. INTERNAL CONSISTENCY of the CSV: dates strictly increasing & weekdays only (NYSE calendar —
   list any weekend or NYSE-holiday date with nonzero return); no NaN/inf; no duplicate dates;
   max single-day |return| (flag >15%); count exact-zero interior runs (a run of zeros
   may indicate phantom flat days — list any run >= 5 days with dates). Is the series a clean
   daily-return stream or are there artifacts?
5. DAILY-SR vs MONTHLY-SR sanity: a huge gap between daily and monthly SR (5.24 vs 3.46) implies
   negative lag-1 autocorrelation / mean-reversion. Compute lag-1 autocurr and explain the gap.
   Report whether daily SR 5.24 is materially overstated relative to a monthly investor.

Write campaign/agents/STRICTAUDIT_METRICS/FINDINGS.md with a verdict table:
CLAIM | claimed | recomputed | MATCH/DIFF. Be adversarial — hunt for an inflated number.
Last line exactly: STRICTAUDIT_METRICS DONE

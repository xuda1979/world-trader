# HUNT_ALT_METALS — Copper ("Dr. Copper") alternative-data honest gate

Date: 2026-09-22. Data fetched the same day via AlphaVantage COPPER (free tier, working key
in .env.local); persisted at data/copper_alpha.csv (monthly, 1992-01 -> 2026-07, 415 rows).

## Why this matters (the "if you can get" answer = YES, we got it)
The V7 frontier was declared closed over the on-disk inventory; the 2026-09-14 log explicitly
noted METALS were NOT on disk ("no GC/SI" for gold/silver/soybean crush). Copper was the one
reachable, working, decorrelated metals surface: AlphaVantage's GOLD/SILVER functions no
longer exist (Error Message: function does not exist), but COPPER returns full history.
Nasdaq Data Link / Quandl (data.nasdaq.com) is 403-blocked without an API key, so that
larger alt-data surface (Baltic Dry, WGC gold, LME bags) is NOT currently fetchable.

## Honest gate results (same monthly convention as V7, >=2009, IS<2017 / OOS>=2017)
| signal            | IS monthly SR | OOS SR | corr to champion |
|-------------------|--------------|--------|------------------|
| copper raw long   | 0.48         | 0.67   | +0.023           |
| copper tsmom-12   | 0.24         | 0.42   | +0.088           |
| copper mom-12     | -0.18        | 0.31   | +0.027           |
| banded_z12/z1     | -0.31        | 0.34   | -0.034           |
| banded_z6/0.5     | -0.09        | 0.38   | +0.096           |
| trend-24          | -0.16        | 0.27   | +0.067           |
| champ gated on copper12mo>0 (regime filter) | IS 1.99 / OOS 2.78 (corr 0.31) |

## VERDICT: REJECTED for V7 adoption — honest reproducible negative
- The GOOD: copper is GENUINELY DECORRELATED (corr 0.02-0.10 vs the energy-dominated book)
  and the OOS SR (> IS on most signals) shows NO overfit — this is a real, if weak, signal.
- The BAD: every copper construction has IS monthly SR <= 0.48, far under V7's >~1.0
  adoption floor and the 6.5 shrunk-Sharpe optimizer constraint. A copper sleeve cannot
  survive a capital-real re-fit (optimizer assigns ~0 weight). The copper REGIME-FILTER on
  the champion (OOS SR 2.78) is WORSE than the bare champion (3.63) — copper does not
  improve timing either.
- Consistent with the campaign's repeated finding: a low-corr but low-per-gross sleeve
  cannot clear the bar set by the energy book's high per-gross return. This is a
  concentration-refractive result, NOT a data dead-end.

## What would reopen it (for a future agent/operator)
- A daily-frequency metals source (LME/LBMA or a metals futures chain) — monthly copper is
  too slow for a daily-return V7 sleeve; a daily copper trend could clear the SR bar where
  the monthly one cannot.
- Copper relative-value vs. the energy book (copper/energy ratio) as a macro-cycle trade,
  rather than absolute copper trend.

Artifacts: data/copper_alpha.csv (new alt-data), honest_gate_copper.py (reproducible),
tests: campaign/bt/tests/test_alt_metals_copper.py (3 pins). V7 champion UNCHANGED.

# ML Long/Short Strategy Stack — Master Summary

**Date:** 2026-08-20 · **Status:** research complete, live-positive, monitoring mode
**Full details:** `GKX_1M_FINAL_REPORT.md` (1m arc) · `XGB_1Y_FINAL_VERDICT.md` (1y arc)

## The stack (all net of costs, full ~900-name union universe, OOS 2009-2026)

| # | Book | Rebalance | SR | ann | dd | Capacity | Worst yr |
|---|---|---|---|---|---|---|---|
| 0 | **Ridge-1m + 1y-deploy 50/50** | monthly+quarterly | **1.32** | +15.8% | **-19%** | both legs' capacity | — |
| 1 | **Ridge, 1m** | monthly | **0.93** | +14.1% | -29% | **0.79 @ $20M ADV, ~$1.6B/leg** | **-17%** |
| 2 | **XGB d3, 1y target** | annual 12m-hold | **1.03-1.10** | +21-25% | -15% | ~$144-288M/leg | -13% |
| 3 | Ridge+XGB ensemble (w=.6), 1m | monthly | 1.05 | +21.1% | -52% | 0.58 @ $20M ADV | -35% |
| 4 | XGB d3, 1y, staggered deploy | quarterly, 12m | 1.06 | +16.4% | -23% | beta -0.06 | -13% |
| 5 | XGB d3, 1y, 24m-hold | biennial | 0.96 | +14.5% | -8.9% | — | -7.8% |

Portfolio combination (2026-08-20): the two primary books' monthly P&L
correlates only 0.15 — 50/50 capital split gives SR 1.32 (ann +15.8%,
dd -18.9%), the best risk-adjusted book of the program. Prediction-level
blends were dilutive; portfolio-level diversification is NOT.

Ranking note: Ridge-1m is #1 on time-robustness (best pre-2018 regime,
1.13 post-2018 hold-out), capacity, and live record. The ensemble's
full-period edge over Ridge is concentrated post-2018 (split-half check)
— discretionary full-breadth enhancement, not the primary book.

## Cross-validation (independent 285-name large-cap daily panel)

| Signal | Result | Reading |
|---|---|---|
| 1y-target (252d) monthly rebalance | SR 0.68, ann +19.9% | survives in large caps |
| 1m-target (21d) decile | SR 1.17 overall | **edge faded 2013-2023** (2008-12 dominance) |

## Structural facts (the "why")

- **Size**: the 1m edge is small-names ONLY (LARGE 0.04 / MID -0.08 / SMALL
  0.61 SR). The 1y edge survives large caps (0.68) — horizon-matched
  deployment: **large caps → 1y book; full breadth → 1m books.**
- **Horizon**: 1m XGB decays by 6m; Ridge-1m persists (0.65 @12m); the 1y
  model is the dedicated long-hold book. Same-horizon model diversity
  (Ridge+XGB) is additive; cross-horizon blending is dilutive.
- **Signal**: momentum/vol/macro-conditioned; NOT the 12m-momentum factor
  (survived the 2009 momentum crash where that factor lost -105%).

## Data integrity (fixed 2026-08-20 — all numbers above are post-fix)

1. Scrambled `ret_next` (row-positional shift mixed returns across tickers)
2. 292-name label joins on a 913-name panel (quarter-universe backtests)
3. Horizon-mismatch booking (12m return booked monthly → +297% ann artifacts)

## Live record (post-backtest)

- 1y cohorts (Nov-25/Feb-26/May-26): **+42.3% / +16.1% / +2.4%** cum net
- Ridge 1m: 10/14 months positive, **+137%** compounded (14 mo)
- XGB 1m: 11/14 positive, +74% · Ensemble (w=.6): 10/14, +77%

## Operational

- Monitor: `python3 tools/quant/bigmove/live_monitor.py`
- Next formation 2026-08-31; next refit 2027-01-31; price data through 2026-08-18
- Key risks: execution/turnover (68%/yr 1y book, 100%/mo 1m book),
  small-name capacity protection, data-refresh cadence
- Repo note: all research artifacts are uncommitted as of this writing

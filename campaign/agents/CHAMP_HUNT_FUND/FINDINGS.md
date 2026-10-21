# CHAMP_HUNT_FUND — ROUND 1 (2026-09-14)

Mission: build the BEST HONEST cross-sectional equity quality/profitability long-short
sleeve from on-disk data and test whether it clears the champion's dAnn>0 adoption gate.
(Agent hit a 429 API rate limit mid-run with live data loaded — closes.pkl/vols.pkl/
liquid_names.pkl; the analysis was completed via the shared harness below.)

## CONSTRUCTION (honest, T+1, no same-month lookahead)
- Source: alphaportfolio_replication/data/model_panel_full.csv (503 US stocks, 2016-08..2026-08).
- Signal at month M: cross-sectional quality = mean(ROE rank, ROOA rank) within M.
- Return earned: the TOP-minus-BOTTOM quintile spread of the CROSS-SECTIONAL RANK of next
  month's return (next_ret1 = r_ret1 shifted forward one month per symbol). CRITICAL: the
  panel's r_ret1 for month M is the SAME-month return; we shift by 1 so the signal known at M
  earns only the M+1 return — no same-month leak. Costs approximated (one-side, modest).

## RESULTS (measured on the champion's 2016-2026 overlap)
| metric | value |
|---|---|
| ann (gross, monthly-cadence) | 27.95% |
| monthly SR | 0.92 |
| halves: H1 / H2 | 29.7% / 26.2% (stable, no overfit collapse) |
| corr to champion (daily book) | 0.020 (essentially decorrelated) |
| champion-overlap ann (geometric, monthly) | 44.95% |
| quality sleeve ann (same overlap) | 26.17% |

## THE ADOPTION GATE (dAnn>0 HARD, at fixed gross scale)
Blending the sleeve into the champion at constant weights (5/10/15%) — the honest way to test
whether it RAISES champion ann:
| blend weight | champion+qual ann | dAnn (pp) |
|---|---|---|
| 0% (champion) | 44.95% | — |
| 5% | 44.34% | -0.61 |
| 10% | 43.69% | -1.26 |
| 15% | 43.00% | -1.95 |

## VERDICT: REJECT (does NOT clear dAnn>0)
Despite being genuinely decorrelated (corr 0.02) with positive ann (28%), the equity-quality
sleeve DILUTES the champion's ann at every weight (dAnn = -0.6 to -2.0pp). Reason (matches
the documented frontier): its per-gross IR ~0.92 << the champion's energy-core ~2.1-2.8, so at
fixed gross it earns less return-per-gross than the incumbents it displaces. This independently
re-confirms the honest frontier: the ONE untested family (PIT/quality equity fundamentals) does
not raise the champion.

No sleeve CSV saved (rejected). No live network used (proxy-flaky per charter).
Last line: CHAMP_HUNT_FUND DONE

## ADDENDUM — PIT-CLEAN test (the honest lever-#1 test, 2026-09-14)
After the 429-rate-limit abort, I completed the lever-#1 test the goal ACTUALLY asked for: a
**PIT-clean** (filed-date as-of, no restatement lookahead) cross-sectional equity sleeve built
from the 503-stock SEC EDGAR XBRL cache (257,803 facts, 2009-2026, all with `filed` timestamps).
This is the same family A5 tested with the RESTATED 2016+ model panel (which showed a spurious
SR~0.92). The PIT-clean version (490 stocks, 2010-2026, T+1) gives:
| signal | direction | ann | SR(m) |
|---|---|---|---|
| ROE (sqrt quality) | high-long | -2.45% | -0.30 |
| ROE | high-short (value) | +2.45% | +0.30 |
| Net-margin | high-long | -6.19% | -0.66 |
| Net-margin | high-short (value) | +6.19% | +0.66 |
VERDICT: with PIT-clean fundamentals the equity quality/profitability premium is NEGATIVE or, at
best, SR 0.66 (value direction) — far below the adoption bar. The restated-panel "quality" profit
was a LOOKAHEAD artifact (using future-restated fundamentals). This closes the ONE untested-family
hypothesis: PIT-clean equity quality does NOT clear the champion's dAnn>0 gate. No sleeve saved.
Last line: CHAMP_HUNT_FUND DONE

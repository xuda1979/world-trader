# Session Summary — AlphaPortfolio & strategies improvement loop
(2026-08-12..13, /loop campaign, 50+ fires)

## Final validated portfolio (all numbers DAILY-frequency audited)

| book | SR | ret | MaxDD | key validation |
|------|-----|-----|-------|----------------|
| Polygon LS champion @3x | 2.23 (active) | 26% (active) | -6.3% | scramble PASS (p=0.000), costs scale, factor-decay monitored |
| AP gold composite | 0.94 | 13.2% | -17.5% | split-half, daily audit |
| **Blend 40/60** | **1.73 full / 2.26 active** | **13.8% / 22.7%** | **-5.7%** | meets BOTH user targets at daily frequency; corr -0.15 |
| DRL ensemble | 1.66 raw | 0.9% | — | optional sleeve; vol-target claims RETRACTED (not implementable) |

Artifacts: `DEPLOYMENT.md` (spec), `run_blend_champions.py` (daily), champion
configs `champion_n10_r14[_lev3]`, daily stream `wf_champion_gold_opt_daily.csv`,
health monitor `check_champion_health_polygon.py`.

## What was tested and failed (closed threads)
- **twelvedata LS path**: dead on the current panel - every window (20y/10y/8y),
  every config (h21, tw320d4, VIX gate), even with the original 3-factor set
  restored. Root cause isolated by cross-data test: the edge is PRICE-SOURCE-
  SPECIFIC (same config: polygon SR 1.42 vs twelvedata SR -0.83). The live
  config on the extended panel produces a broken model (SR -0.19).
- **AP composite DD levers** (all exhausted): VIX gates/percentile/term, crash
  filters, SPY-short hedge, rebalance cadence (weekly/biweekly), DD-reducer
  resolution, watermark release, defensive momentum tilt. -16% DD was
  structural; GOLD SLEEVE (0.2) was the first lever to improve the champion
  (SR 0.93 -> 1.09) - split-half robust.
- **DRL vol-targeting**: arithmetic scaling (SR 1.66 at any vt) is not
  implementable - honest trailing vol-target collapses SR to 0.43.
- **Suspect CSVs flagged**: wf_longonly_mom_*_g* (impossible 2022 returns,
  no producing script) - leak/oracle artifacts, do not cite.

## Honesty corrections made this session
1. Monthly-sampled MaxDD understates intra-month drawdowns -> all claims
   re-audited at daily frequency (blend DD -2.7% -> -5.7%, AP DD -14.2% -> -17.5%).
2. Cross-suite AP correlation was monthly sampling luck (0.03 monthly vs
   0.56 daily); the LS champion (corr -0.003 daily) is the genuine diversifier.
3. Overnight hedge-fund metric fix (cost-exclusive Sharpe) audited: ls/blend
   paths unaffected (cost-inclusive verified).
4. Factor-decay characterization: the champion's edge is real but FRAGILE
   (all 4 measurable factors decayed in half 2), carried by the 20-day
   adaptive refit. Monitoring rule operationalized.

## Cross-suite improvements (logged in hedge_fund_strats/RESEARCH_REPORT.md)
- hedge EW + AP gold (monthly 18y): SR +0.45 (daily: +0.18)
- hedge EW + LS champion (daily 26mo): SR +0.72, MaxDD halved (corr -0.003)
- 6-stream (h+AP+LS, daily): SR 1.47, ret 10.5%, DD -5.2%

## Open items (user decisions)
1. **Live migration**: switch run_live_signal.py to the polygon champion
   (candidate run_live_signal_polygon.py verified; old config broken).
2. **Milestone commit**: large body of validated work since 1583d56.
3. **Loop steering**: stop (CronDelete 66111700) or new research direction.

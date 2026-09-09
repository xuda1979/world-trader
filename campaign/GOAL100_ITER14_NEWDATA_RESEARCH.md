# GOAL100 ITER14 — NEW-DATA RESEARCH + DATA-FRESHNESS (2026-09-09)
> /loop: "add more data, then research to improve the champion using 5+ agents leveraging new data."

## Bottom line
- **Champion of record unchanged: RAW-EW13v2 weighted @1.6x, ann 37.20%, SR 3.181, MDD -6.69%, 0/19 neg yrs.**
- **6 new-data research agents executed (all honest REJECT with numbers).** None of the NEW datasets
  (fx_hist 554-pair, altlib DeFi/fear-greed, long BAA-AAA credit) yields a decorrelated SR>=1.5
  champion-eligible sleeve in the costed/causal harness.
- **One concrete champion improvement IS available and validated: RAWEW15 data-refresh adoption**
  — a pure freshness win lifting the champion to ann 37.49% / SR 3.195 by extending the costfix
  sleeve tails (brwt10/7/5, diescrack) to 2026-08-28 (was truncated 2026-08-10).

## Research executed (6 agents) — ALL REJECT, numbers in each agent FINDINGS
| Agent | New data / lane | Best result | Verdict |
|-------|-----------------|-------------|---------|
| RES_FXSTYLE | fx_hist cross-sectional FX mom (28 majors) | SR 0.42, dd -25..-64% | REJECT |
| RES_ALTDATA | altlib DeFi TVL/fear-greed | starts 2014-2018, no 2008+ | REJECT (fail-closed span) |
| RES_VOL | CBOE VIX term-slope / VRP (20 books) | SR 0.70 | REJECT |
| RES_CREDIT | BAA-AAA spread + t10y2y slope | 2s10s slope SR 1.062 (all gates pass but <1.5) | REJECT |
| RES_REVERSAL | xs reversal (prior A6 + C1) | daily cost-negative, best 0.7 fails gate | REJECT |
| RES_CARRY | FX/commodity carry | oracle-ceiling 0.18-0.52 | REJECT |

## NEW DATA findings (correct DATA_COVERAGE)
1. **FRED BAML OAS is NOT 1996+**: current vintage (api + fredgraph endpoints, checked 2026-09-09)
   serves only 793 obs 2023-09-11..2026-09-07. Long-history credit level data = Moody's
   BAA/AAA/BAA10Y (1983-1986+), used in the credit test. DATA_COVERAGE's "~7400 rows" is stale.
2. **fx_hist = 554 pairs** (1999+, daily close) — landed by DATA_FXHIST, broad matrix intact.
3. **altlib = DeFi TVL / activity / fear-greed** (2014-2018+) — real but too short for 2008+
   champion eligibility.

## Champion refresh (validated, recommended adoption)
RAWEW15_REFRESH_CANDIDATE (CAMP_COST R7): the committed 13-sleeve book with the 4 refreshed sleeves
(brwt10/7/5 -> 2026-08-28, diescrack -> 2026-08-24) re-solved. Verified:
- rows <= 2026-08-10 byte-identical to champion (no history relabel); weights identical (post-IS tails).
- FULL |dW|@6.4bps + margin, gross exactly 1.6x, 0 overshoot; causality nav.shift(1); 8/8 TDD green;
  verify_champion exit 0 (all ok): **ann 37.49% | SR 3.195 | MDD -6.69% | 0 neg yrs**.
- Only 2026 differs (+0.054pp) — pure freshness, no strategy change. Recommend adopting RAWEW15 as
  the refreshed champion of record (or keeping the committed champion and refreshing sleeves in-place).

## Honest framing
The GOAL100 100%-ann target remains unmet. The champion sits at the honest frontier (37.2%); the
repeated finding across ~103 DEAD_IDEAS and this 6-agent wave is that on-disk data (even the NEW
fx_hist / altlib / credit) does not contain enough additional decorrelated SR>=1.5 engines to close
the ~1.8-2.5x gap. The refresh keeps data current; the research keeps the "no free lunch" record current.

## Coordinator next-step suggestion
- ADOPT RAWEW15 as refreshed champion (freshness) with the R7 charter + full verify log.
- Keep fx_hist in the data roadmap (it is a real long-history matrix worth future FX-regime work,
  even though standalone FX momentum fails the standalone-SR bar here).

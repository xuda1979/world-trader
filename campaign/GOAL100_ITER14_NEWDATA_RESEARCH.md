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

---

## SUPPLEMENT: CAN WE RAISE THE CHAMPION'S SHARPE BY ADDING SLEEVES? (direct answer)
Short answer: **YES for one specific sleeve — CFX4 — and NO for the 6 new-data engines.** The
blocker is a DATA-COVERAGE artifact, not alpha.

### Why new-data engines do NOT raise Sharpe
The champion (SR 3.18) is a NAV-drift, IS-SR^0.55-weighted book dominated by the 5 mutually-
correlated brwt trend sleeves (SR 2.3-3.0, corr 0.85-0.91). For a NEW sleeve to lift the blend
SR under this weighting it needs **IS-window SR comparable to the book AND low correlation** — an
extremely high bar. Verified with real numbers:
  - credit 2s10s sleeve (corr -0.02 to champion, full SR 0.92, IS SR 0.56): blend 3.181->3.178 (dilutes).
  - FX xsmom (IS SR ~0.25): dilutes.
  - vol (SR 0.70), alt (no 2008+ span), reversal/carry (dead): all far below.
The credit case is the decisive one: even a genuinely decorrelated (corr -0.02) sleeve with
positive SR leaves the blend flat, because its IS SR is too low to earn weight against the
brwt-dominated book.

### CFX4 IS the Sharpe lever (currently zero-weighted by accident)
CFX4 (FX 4-book cross z-reversion) has full-window SR 1.91, corr just 0.05 to the champion, and
is NET of 6.4bps+borrow. BUT the champion builder weights sleeves by IS-window (<2017) SR; CFX4's
history starts 2019-09-10, so is_sr=0 -> relw=0.00. It sits in the pool unused despite being the
single best diversifier.
Champion+CFX4 constant-mix on the 2019+ overlap (margin repriced once):
  w=1.00 champion:  SR 2.53  ann 35.8%  gross 1.6
  w=0.70:           SR 2.89  ann 29.4%  gross 1.42
  w=0.50:           SR 3.08  ann 25.2%  gross 1.30
=> Sharpe RISES ~2.5 -> ~3.1 as CFX4 is blended in; ann FALLS (de-lever/return dilution).
This is the risk-adjusted-return vs raw-return tradeoff: CFX4 materially improves Sharpe (your
metric) but is lower-return than the brwt core.

### Actionable proposals to raise champion Sharpe
1. **Extend CFX4's history pre-2017** (needs pre-2019 FX closes for the same 4-book z-rev; the new
   fx_hist data goes back to 1999 and could reconstruct it) -> then the IS solver gives CFX4 real
   weight and the champion Sharpe rises in-sample AND out.
2. **Explicit CFX4 upweight / constant-mix overlay** at ~20-40% on the 2019+OS deployment to capture
   the Sharpe gain now (accepting lower ann).
Both are honest, numbers-backed and actionable next steps.

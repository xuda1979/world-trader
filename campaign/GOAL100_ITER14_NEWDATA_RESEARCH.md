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

---

## SUPPLEMENT 2 — RESOLVED: WHY ON-DISK SLEEVES CANNOT LEGITIMATELY RAISE SHARPE
Following up the CFX4 finding with a full scan of every genuine net-return sleeve on disk
(excluding positions/weights/signal ladders), the "add a sleeve to raise Sharpe" question is
now CONCLUSIVELY answered. All apparent wins are either cost-inflated or below the hurdle.

### 1. The BIG apparent win (HT_TAIL SR 4.72) is INVALID — cost-undercharged ancestor
Scanning all net sleeves, the highest-SR candidate is HUNT_TAIL (SR 4.72, ann 45%, 2008+).
Adding it to the champion's 13-sleeve pool lifts the blend to SR 3.985 / ann 48.5% (IS 3.81,
OOS 4.16 — no overfit). BUT this is an ARTIFACT:
- HT_TAIL is the tail-boosted **HONEST11** portfolio — the same lineage the RAWEW champion
  SUPERSEDED specifically for construction defects.
- Its cost line (g9_final.py): `tw = (|dW|*0.5).sum(); r_out -= (tw+dsc)*6e-4` = **HALF-turn × 6.0bps**
  **undercharge**. The honest convention is **full |dW| × 6.4bps** (audit A1: the half-turn×6.0
  was a BLOCKING defect undercharging 41.7% of the honest cost rate; RAWEW fixed it).
- HT_TAIL undercharges ~2.13x on a high-turnover levered book -> its SR 4.72 is NOT comparable
  to the champion's honest 3.18. This is why the project's RAWEW champion (37.2%) and the
  HONEST11 family (45-60%) differ — the gap IS the defect, not a real Sharpe edge.
=> Do NOT adopt HT_TAIL. Any "Sharpe boost" from it is cost-dishonest.

### 2. Genuinely honest decorrelated sleeves (FF2_DUALGATE SR1.03 corr0.02; HF_mom_cheap SR0.92
corr-0.04; both 2008+ long span) give only TINY lifts: blend SR 3.181->3.191 (+0.01). Reason:
the champion's IS-SR hurdle (~2+) is so high that a decorrelated sleeve at IS SR~1.0 earns only
a small weight and adds almost nothing. More decorrelation alone is NOT enough — the sleeve must
also clear the book's alpha hurdle, and none on disk does (other than cost-inflated HT_TAIL).

### 3. CFX4 (SR 1.91, corr 0.05) — the only genuine stand-alone l ever, but limited & cannot extend
- Blend lifts SR 2.53->3.08 on the 2019+ overlap, but lowers ann (de-lever), and it's 2019+ only.
- **Cannot be extended pre-2017 via fx_hist**: price-source mismatch confirmed — my faithful
  rebuild reproduces committed CFX4 EXACTLY on `tools/quant/data/fx/` (SR 1.911, corr 1.0000,
  maxdiff 9.97e-17) but is SR -0.84 on `fx_hist` (daily-return corr between sources only 0.53).
  The z-reversion edge is PRICE-SOURCE-SPECIFIC (fx_hist is a different vendor); consistent with
  the project's twelvedata-vs-polygon price-source finding.

### Verdict
The champion's full-window Sharpe CANNOT be legitimately raised by adding any on-disk sleeve.
Every apparent improvement is either (a) a cost-undercharged ancestor (HT_TAIL/HONEST11 family,
invalid), or (b) below the IS-SR hurdle (FF2/HF/credit/FX, SR<2, tiny/dilutive), or (c) a genuine
edge (CFX4) that is 2019+ only and unextendable. Raising Sharpe requires NEW genuinely-decorrelated
SR>2 honest sleeves — which no dataset on disk provides. This RESOLVES the question with evidence.

---

## SUPPLEMENT 3 — "ALL KINDS OF METHODS" scan (2026-09-09, continued)
Expanding beyond "add sleeves" to every other honest improvement method. Results:

### Method A — Walk-forward refit cadence (walkforward_champ.py, honest T+1 trailing refits)
| cadence  | ann    | SR   | MaxDD |
|----------|--------|------|-------|
| frozen   | 37.22% | 3.18 | -6.69% |
| yearly   | 37.97% | 3.19 | -6.72% |
| quarterly| 37.67% | 3.18 | -6.74% |
| monthly  | 38.09% | 3.18 | -6.89% |
OOS(2017+) similar: frozen 40.67% vs monthly 40.78%. => Walk-forward REFIT raises ANN ~+0.8pp
(year-to-year / monthly) but leaves SR FLAT (3.18-3.19). Not a Sharpe lever; a modest return lever.
Monthly has slightly worse MaxDD (-6.89%). Honest, no leakage; a defensible ann improvement but NOT
Sharpe.

### Method B — Cost/turnover optimization (consolidate the 5 brwt sleeves @ corr 0.85-0.91)
Measured champion turnover: TOTAL one-side |dW| over 18y = 16 (=0.8/yr, =5.26bp/yr actual cost).
The book is ALREADY extremely cost-efficient (0.8 turns/yr). The 4 brwt trend sleeves together
account for 50% of that tiny turnover. Consolidating them into one composite sleeve would save at
most ~2.6bp/yr — NEGLIGIBLE. => Cost optimization is not a lever; the champion is already
turnover-minimal (frozen weights + NAV-drift).

### Method C — RAWEW15 data-refresh adoption (the finished, verified improvement)
The single cleanest honest improvement now adoptable: RAWEW15 (fresh sleeve tails) = ann 37.49% /
SR 3.195 / MDD -6.69% / 0 neg yrs, verify_champion exit 0 (all ok), 8/8 R7 TDD green, byte-identical
prefix <=2026-08-10, weights identical. It only ADDS recent return; a strict, honest freshness win.
RECOMMENDED for adoption as the refreshed champion of record (or in-place sleeve refresh).

### Synthesis
The champion sits at the honest frontier: SR 3.18 / ann 37.2%. Every legitimate improvement method
is small or non-Sharpe:
- new decorrelated sleeves -> negligible (IS-SR hurdle too high)
- HT_TAIL/HONEST11 -> cost-inflated (invalid)
- walk-forward refit -> +0.8pp ann, SR flat
- turnover/cost optimization -> already minimal
- RAWEW15 refresh -> +0.3pp ann (the concrete adoptable win)
Raising SR meaningfully still needs a genuinely decorrelated SR>2 honest sleeve (not on disk).

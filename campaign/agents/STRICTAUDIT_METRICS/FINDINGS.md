# STRICTAUDIT_METRICS — FINDINGS (adversarial recomputation of every headline number)

Agent: STRICTAUDIT_METRICS | Date: 2026-09-02 | Read-only. Scratch: `scratch/m1..m13*.py` (my own pandas/numpy; no harness/eval.py reuse).
TARGET: `campaign/results/GOAL100_STRICTTRADE_BALANCED_daily.csv` (committed in 28c892b, unmodified since — git-verified).

## 0. VERDICT TABLE

| # | CLAIM | claimed | recomputed (my code) | VERDICT |
|---|---|---|---|---|
| 1 | ann return | 49.4% | **49.36%** (arith mean×252) | MATCH |
| 2 | CAGR (not claimed; adversarial cross-check) | — | **63.03%** (n/252), 61.35% calendar-day | headline is the CONSERVATIVE arithmetic convention |
| 3 | ann vol | (9.4% implied) | **9.42%** | consistent |
| 4 | daily SR | 5.24 | **5.241** (ddof=1 and ddof=0 both) | MATCH |
| 5 | monthly SR | 3.46 | **3.461** (221 months, compounded) | MATCH |
| 6 | monthly-SR bootstrap CI | [3.02, 4.01] | iid monthly 5000x: **[3.025, 3.978]**; 6-month block: **[2.958, 4.030]** | APPROX-MATCH (point exact; their hi 4.01 sits between my iid and block CIs — seed/bootstrap convention not committed, cannot reproduce byte-exactly) |
| 7 | daily-SR bootstrap CI (charter add-on) | — | iid daily: **[4.624, 5.866]**; 21d-block: [4.570, 5.971]; analytic [4.765, 5.716] | daily SR floor ≈ 4.6 even adversarially |
| 8 | MaxDD full | -6.1% | **-6.051%** (trough 2022-05-27) | MATCH (claim quotes it 5bp worse → conservative rounding) |
| 9 | negative years | 0/19 | **0/19**; min year **+20.72% (2026, partial n=142)**; max **+151.12% (2023)** | MATCH exactly (memo numbers 20.7/151.1 reproduce) |
| 10 | OOS 2017+ | 55.9% @ -6.1% | **55.85% @ -6.05%** (SR 5.54, n=2343) | MATCH (same conservative rounding) |
| 11 | span | 17.9y, n=4522 | n=**4522** (exact); 2008-03-31..2026-07-31 = **17.944y by n/252**, 18.333y calendar | MATCH (n/252 convention; calendar span is longer → conservative) |
| 12 | "every 3y window DD <= -6.1%" | no 3y window worse | **3767/3767** rolling 756-row windows pass; worst **-6.051%** (start 2021-09-20); median -4.61% | MATCH |
| 13 | "every calendar-year DD <= -6.1%" | no year worse | worst year-DD **-5.25% (2014)**; 19/19 pass. Also verified 1y and 2y rolling windows: 0 violations | MATCH |
| 14 | "12 sleeves" pool | 12 | GOAL100_STRICTTRADE.json lists exactly 12; my from-raw 12-sleeve rebuild correlates **0.9830** with the CSV | MATCH as listed — but see #21 (breadth) |

**Every claimed headline number reproduces from the CSV alone within rounding (claimants consistently rounded in the CONSERVATIVE direction). I could not find an inflated number in the file-vs-claim comparison. The problems are elsewhere (grid holes, provenance, breadth — below).**

## 1. Internal consistency (charter job 4) — the file itself is clean
- 4522 rows, strictly increasing, **0 duplicate dates, 0 NaN, 0 inf, 0 exact-zero rows** (min |ret| = 8e-8 bp-equivalent; zero-run analysis: no run ≥ 2 days — the "phantom flat day" defect of earlier champions is GONE).
- **0 weekend dates, 0 NYSE-closed dates** (my from-scratch NYSE calendar: fed-holiday rules + Good Friday + Sandy 2012 + Irene 2011 + mourning days 2018-12-05/2025-01-09). The "phantom calendar days" audit fix (TRUTH-MEMO item 7) is genuinely FIXED in this file.
- Max single-day |ret| **+14.721% (2020-09-01)** — under the 15% flag threshold but it is **24.8σ** vs full-sample daily σ and 20.3σ vs prior-126d σ. Skew +4.46, excess kurtosis **89.4**. This is a legal part of the strategy (see §5) but the daily SR is tail-event-driven: 2020-09-01 alone = 1.7% of 18.3y total PnL; top-5 days = 4.1%, top-20 = 9.4%. Without 2020-09-01: ann 48.5% (from 49.4%). Distribution is NOT Gaussian-nice; t-stat of mean = 22.2, so the edge is real in-sample, but SR 5.24 leans on a handful of Brent–WTI dislocation days (2020-03-19, 2020-09-01, 2021-03-31 all = brwt-family).

## 2. THE REAL DEFECT FOUND: 89 NYSE-open days are MISSING (2.0% of grid) and their PnL is DISCARDED
- Reconstructed NYSE calendar 2008-03-31..2026-07-31: **4611 open days; CSV has 4522 → 89 open days absent** (cross-checked vs SPY/twelvedata which has 4614 rows; 92 SPY-days absent; CSV has 0 days SPY lacks).
- The holes are NOT random: they are pre/post-holiday sessions (Columbus/Thanksgiving-adjacent Fridays, Dec 24/26/31, Easter-Monday-adjacent days, Veterans Day, Juneteenth-eve…) where **some sleeve files have no row**. The champion grid ≈ union of sleeve dates minus days the generator apparently treated as illiquid (on 43 of the 89 holes only 8/12 sleeves have data; on 2017-11-10 and 2021-06-18 **all 12 sleeves have data and the day is still excluded**).
- **The dropped days' PnL is NOT folded into the next row.** Regression of champion next-row returns vs sibling file (GOAL100_FINAL_TRUTH_BALANCED) over the 75 holes where a sibling row exists: not-folded hypothesis corr **0.9863** / mean|diff| 19.2bp vs folded hypothesis corr 0.8981 / 52.9bp. Folding is rejected.
- Materiality: those 75 holes carried +10.40pp of sibling PnL (43 win/32 loss, mean +0.139%/day). Restoring them at 12/14 scale lowers ann **49.36% → 49.05%**; zero-filling them on the full NYSE grid gives ann **48.41%, SR 5.184**, MaxDD -6.05%, still 0/19 neg years. So the blemish is worth ~+0.3–1.0pp ann / +0.06 SR to the headline — an adverse-direction artifact, but NO conclusion flips: even adversarially repaired, the system is ~48–49% ann, SR ≈ 5.2, DD ≈ -6%.
- UNVERIFIED: why the generator dropped 89 open days (no committed code — §4); whether the drop was deliberate liquidity hygiene or a join bug.

## 3. Bootstrap / SR-horizon sanity (charter jobs 2 & 5)
- Monthly iid bootstrap (5000x, seed 20260902): SR_m point 3.461, 95% CI **[3.025, 3.978]**. 6-month block: [2.958, 4.030]. The claimed [3.02, 4.01] is consistent in center and width; exact reproduction requires the uncommitted bootstrap code → APPROX, not byte-verified.
- Daily-vs-monthly gap (5.241 vs 3.461 = 1.51x): the charter's hypothesized mechanism (negative lag-1 / mean-reversion) is **empirically WRONG for this series**: daily lag-1 autocorr = **-0.0127** (≈0), monthly lag-1 = **+0.217**. The true driver is POSITIVE multi-week autocorrelation: variance ratios VR(5d)=1.14, **VR(21d)=2.07**, VR(63d)=3.74. Horizon SRs: 5d 4.92, 21d **3.73**, 63d **2.93**.
- Adversarial answer: daily SR 5.24 IS materially overstated for a monthly-or-slower investor (they experience 3.46 monthly / ~2.9 quarterly). But even the slowest-investor number stays ≈ 2.9, i.e. >2. The gap is a momentum/convexity property, not a data artifact.

## 4. PROVENANCE GAP (the same defect class that killed MHX/H21, applied to the champion itself)
- `GOAL100_STRICTTRADE_BALANCED_daily.csv` was committed (28c892b) with a JSON manifest (pool list + claimed stats) but **NO committed script generates it**. I searched all campaign/scripts/*.py (champion_build.py = 16-sleeve pre-audit pool; coord_goal100_v2.py = old pool; champion20y_build.py = 20y file), tools/, all agent scratch, and git history for "STRICTTRADE": nothing. The IBKR_STRICT and FINAL_TRUTH sibling files are likewise script-less.
- My independent 12-sleeve rebuild from raw sleeve CSVs (per-sleeve vt10 cap 8, EW, global vt cap 8, 126d throttle ×0.5 @ -5%, no costs): corr **0.9830** with committed, my SR **5.22** vs committed 5.24 — construction is approximately as claimed — but my ann is **60.9%** vs committed 49.4% (the committed file embeds ~-11pp of instrument-specific costs/borrow fees that are nowhere scripted), and max daily diff **3.44pp**, concentrated 2020-09-01: EW of raw sleeves that day = +1.12%, my capped rebuild ≈ +9%, committed **+14.72%** → the actual generator's implied scale that day (≥13x EW) **exceeds the 8x cap documented in champion_build.py**. UNVERIFIED: the exact generator, its cost schedule, and its cap structure. By the campaign's own H21 standard ("generator state not in git → removed"), the champion FILE is not frozen — the 12 input sleeves are (AUDIT2 verified byte-exact), but the assembly + cost layer is not.

## 5. Breadth/concentration adversarial check
- The 4 "brwt" slots are the same Brent–WTI spread-reversion strategy at 4 vt levels: internal vt-normalized corr **0.774** (family max 0.86). Effective independent engines N* = n/(1+(n-1)ρ̄): **6.2 of the 12 advertised** (9-family version: ρ̄=+0.021, N*=7.7). Six commodity-family slots (4 brwt + 2 natgas, C5ng/C5ngsum corr 0.453) hold **31.1% of mean gross**. "12 sleeves" is nominally true and disclosed as a list, but "12 engines" overstates breadth by ~2x. The memo's "ann>=100% needs 2x more engines" is directionally honest here (real N ≈ 6–8).
- Big single days are one-family events: 2020-09-01 (+14.72%), 2021-03-31 (+7.28%), 2017-02-28 (+4.41%) are brwt-quartet days; 2020-03-19 (+3.80%) includes brwt15 sleeve +15.82%.

## 6. UNVERIFIED (explicit)
1. Exact generator script/state of the STRICTTRADE CSV (cost layer, caps, hole-day rule, bootstrap seed) — no committed code reproduces it; my rebuild is corr 0.983 / SR 5.22 vs 5.24.
2. Whether 2020-09-01's implied ≥13x-EW scaling violates the disclosed gross/leverage envelope (max 4.44x gross claimed in memo §15.2 — vt scale ≠ gross, but the two disclosures have not been reconciled on that day).
3. The bootstrap convention that produced [3.02, 4.01] (my iid and 6-mo-block CIs bracket it).
4. Why 89 NYSE-open days (incl. 2 days where ALL 12 sleeves have data) are absent from the grid.
5. The 4 remaining grid holes with sibling files present in neither IBKR nor FINAL_TRUTH (e.g. 2008-10-13, SPY +14.52% that day) — sleeve-level PnL that day could not be proxied.

## 7. BOTTOM LINE (adversarial, independent)
The claimed metrics are honestly computed FROM THE FILE: every headline (49.4% ann, SR 5.24/3.46, -6.05% DD, 0/19 neg years, OOS 55.9%, all 3y/calendar DD windows) reproduces exactly or with conservative rounding, and the file itself is a clean NYSE-calendar daily stream (no weekends, no holidays, no zero-runs, no dupes). I found NO inflation in the claimed numbers themselves. The four genuine defects: (a) **89 dropped open trading days whose PnL is discarded, worth ~+0.3–1.0pp ann to the headline**; (b) **the champion file has no committed generator** — under the campaign's own provenance standard this is a FATAL-class defect for the FILE (not the sleeves); (c) **true engine breadth ≈ 6–8, not 12**; (d) the daily SR 5.24 overstates what a monthly investor gets (3.46; quarterly ~2.9) via positive multi-week autocorrelation — the charter's mean-reversion explanation is backwards. Adversarially repaired (zero-filled grid): **ann ≈ 48.4%, SR ≈ 5.18, MaxDD -6.05%, 0/19 neg years** — the bettable-number CLAIM survives my audit materially intact; its REPRODUCIBILITY does not (fix: commit the generator script + hole-day policy).

STRICTAUDIT_METRICS DONE

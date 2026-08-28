# A2_fx_carry FINDINGS (round r1)

## Round r1 (2026-08-28) — A2_fx_carry

**Data reality check (drove everything):** twelvedata FX panel (data/fx) only starts 2019-04 (~7.2y, 8 pairs).
Free long history = FRED daily spots EUR/GBP/JPY/CAD (2000+, 20y, 4 pairs) + AUD/NZD/CHF twelvedata 2019+.
Foreign 10y yields (data_fred): monthly only, 2018+. So: carry book = 7 pairs from 2018-07; momentum book = 4 pairs 2000+.
All backtests: harness t1 (T+1), 6bps/side, 10% vol-target on trailing data, monthly or daily rebalance.

### Ideas tried (all gates applied; NONE passed)

| # | idea | window | FULL SR | H1/H2 | neg yrs | verdict |
|---|------|--------|---------|-------|---------|---------|
| 1 | carry top2/bot2 by 10y diff, monthly | 7p 2018+ / 4p 2006+ | −0.06 / 0.11 | 0.07/−0.23, 0.00/0.16 | 5 / 4 | FAIL (spot-only carry ≈ 0 net) |
| 2 | carry + 50d trend gate | both | −0.54 / −0.60 | neg/neg | 8 / 5 | FAIL (trend gate destroys carry) |
| 3 | tsmom 63d & 126d, vol-wt, day+mon | 4p 2000+ | −0.09..0.04 | mixed | 14-18 | FAIL |
| 4a | vol-scaled carry (inv 21d vol) | 7p / 4p | −0.43 / −0.01 | neg/0 | 8 / 4 | FAIL |
| 4b | tsmom 21d / 252d eqw (sweep) | 4p 2000+ | −0.25 / 0.24 | −0.12/−0.43, 0.34/0.11 | 20 / 13 | FAIL (252d best but <0.6) |
| 5 | rate-diff momentum 3m/6m (monthly agg) | 7p 2018+ | −0.12 / 0.27 | −0.44/0.24, 0.26/0.29 | 5 / 4 | FAIL (6m consistent but weak) |
| 6 | DXY 126/252d trend → fade 4 pairs | 2006+ | −0.10 / −0.11 | mixed | 12-14 | FAIL |
| 7 | VIX>80pct gate → long JPY(,CHF) | 2006+ | 0.24 / 0.00 | 0.48/−0.21 | 9 / 7 | FAIL (H2 breaks) |
| 8 | long-horizon reversal 756/1260d | 4p 2006+ | −0.03 / −0.41 | neg | 8 / 13 | FAIL |
| 9 | single-pair JPY/CHF trend 63/126/252d | 2006+ | −0.60..0.15 | mixed | 4-12 | FAIL (JPY63 best 0.15) |
| 10 | carry + accrual (ydiff/100/252 daily) | 7p 2018+ | **0.30** | 0.28/0.33 | 3 (worst −2.0%) | FAIL (best true-carry result; <0.6) |
| 11 | blend carry+accrual + tsmom252 + ratemom6m | 2018+ padded | **0.38** | 0.48/0.32 | 8 (worst −10.5%) | FAIL full+yearly; scramble p=0.000 PASS; pairwise corr ≈ 0.03 |

### Honest conclusions
1. **No FX sleeve passed ALL gates in r1.** Best honest result: 3-signal blend SR 0.38, halves 0.48/0.32,
   statistically real (scramble p<0.001) but below the 0.6 bar and too many soft negative years.
2. Interest **accrual is what carry actually is** — spot-only carry (idea 1) measures ~nothing. With accrual,
   carry is weakly positive on the short 2018+ window but the window contains no 2008/2014-style carry crash test.
3. The "accrual-only" book (SR 27, vol 0.1%) was **rejected as a data artifact**, not saved: it's a deterministic
   yield spread with no price risk, not a tradable strategy at 6bps.
4. Bugs caught & fixed along the way (worth remembering): (a) `df / series` misalignment → use `.div(s, axis=0)`;
   (b) `diff()` on sparse monthly-in-daily frames kills the signal → resample("MS") first; (c) FRED yields in
   percent → accrual must divide by 100.
5. **Recommendation to coordinator:** FX (free data) cannot carry a sleeve at SR≥0.6 alone. The idea-11 blend
   (corr≈0.03 to everything, H2-robust) is a candidate *diversifier* only if the bar is relaxed to ~0.4, or if
   someone supplies policy-rate / CPI data for a proper carry. Do not blend it as-is.

Scripts kept: scripts/fx_lib.py, idea1_carry.py, idea2_carry_trend.py, idea3_tsmom.py,
idea4_volscaled_carry.py, idea5_7_variants.py, idea5b_more.py, idea10_carry_accrual.py, idea11_blend.py.
No sleeves saved (no candidate cleared all gates).
ROUND r1 DONE

# Round r2 (2026-08-28) — A2_fx_carry

**Setup:** built PIT-correct COT loader (`campaign/scripts/a2_lib.py`): TFF report Tue → release +4 trading days
→ weekly W-FRI signal → trade next week (double lag). Mapped TFF markets → tradable proxies: SPY/QQQ (panel 2006+),
UST2/10/30 (synth TR from FRED yields, carry+dur), EUR/JPY/GBP/CAD (FRED 2000+). Legacy COT (1986–2016) →
XAU/SLV/COPX/WTI/NATGAS via FRED. All sleeves: T+1, 6bps one-side on BOTH spread legs where applicable, vt10 trailing.

## Ideas tried (all gates applied; NONE passed — nothing saved)

| # | idea | best FULL SR | H1/H2 | failing gate | verdict |
|---|------|-------------|-------|--------------|---------|
| 12 | charter 1a: lev-fund z-fade, 10 TFF mkts, lb 26/52/78/104/156 × thr 1.0-2.0 | 0.44 (lb104 thr1.5/2.0) | 0.24/0.75 | full SR; plateau FAIL (lb78≈0, lb156<0) | FAIL |
| 13 | charter 1b: AM net 6m-change follow, lb 13/26/52 | 0.41 (lb52) | 0.19/0.75 | full SR < 0.6 | FAIL |
| 14 | refinement sweeps incl. longer lbs | 0.44 | — | same | FAIL (non-plateau) |
| 15 | per-asset breakdown of best z-fade | QQQ solo 0.54; equity sub-book 0.45 | — | full SR; nothing > 0.6 | FAIL |
| 16 | charter 2: TSMOM breadth ALL FRED assets, w 63-504 | 0.25 (2007+ no-fx) / full-len 0.13 | ~0.3/0.2 | full SR | FAIL (2y trend SR .60 solo but book diluted) |
| 17 | multi-horizon TSMOM 63/126/252 | 0.36 | 0.64/0.10 | full SR, H2 decay (2007-09 SR 2.2 → 2020s ~0.2) | FAIL |
| 18 | charter 1c: COT-extreme conflict/fade veto on TSMOM | 0.33 | 0.52/0.14 | full SR | FAIL (vetoes don't help) |
| 19 | charter 3: gold/silver ratio MR + gold trend | MR −0.24..0.04; gold trend 0.54 (w126) | 0.48/0.60 | MR dead; trend w126 is ISOLATED SPIKE (w105 0.22, w147 0.13) → plateau fail; combo 0.40 | FAIL |
| 20 | charter 4a: WTI−Brent spread MR z-band | 0.63 (z63/z126 thr1.0), plateau 0.45-0.63, 2 neg yr | 2.25/0.45 | **scramble p=0.35-0.45** (need <0.05) | FAIL — timing adds nothing on stationary spread; return = episode-invariant level premium (2000-14), 2015+ SR 0.5 |
| 20b | charter 4b: copper/gold ratio trend | −0.23..0.06 | — | full SR | FAIL |
| 21 | legacy COT spec z-follow lb156 (1986-2016 data) | 0.83 "pass" 2016+ | 0.78/0.87 | **artifact**: live-signal era 2000-2017 SR 0.14, H2 0.05; 2016+ window is 90% frozen stale signal (static tilt, not strategy) | REJECTED as data artifact |
| 22 | 2s10s curve: always-on flattener SR 1.06, curve trend | 1.06 | 1.11/1.01 | yearly 7 neg yrs worst −12%; always-on secular term-premium position, no signal | FAIL |
| 23 | rates trend L/S: UST2 378d SR 1.25 | 1.25 | 1.44/1.05 | yearly 6 neg yrs | FAIL |
| 23b | rates momentum LONG/FLAT UST2 378d | **1.45** | 1.50/1.45 | yearly 5 neg yrs (worst −2.1%, all soft); scr_p 0.07 | FAIL — best single sleeve of r2 |
| 24 | BLEND4 (ratesLF + tsmom-exb + gold + AMmom, corr ≤0.10) | **0.83** | 0.58/1.05 | yearly 4 neg yrs (−0.3/−2.6/−0.4/−2.0, ALL SOFT), n=3573 2012+ | FAIL narrowly — best blend of r2 |
| 25 | credit spread (Baa−Aaa) MR | 0.07 | −0.18/0.34 | full SR; synth spread TR ≈ noise | FAIL |

## Honest conclusions (r2)
1. **Still nothing saved.** r2's charter families all fail honestly on free data. Closest: idea 23b (SR 1.45,
   halves 1.50/1.45, kills only on negative-year count 5 vs 2) and idea 24 BLEND4 (SR 0.83, halves 0.58/1.05,
   kills only on 4 soft negative years, all |y|<2.6%).
2. **COT positioning (both TFF and legacy) has no tradable edge at weekly frequency on these proxies.** The one
   "passing" config (idea 21) was a stale-signal artifact — COT data ends 2017 and the ffill'd tilt did all the work.
   Lesson: always re-evaluate with a hard cutoff at signal-data end when a source goes stale.
3. **WTI−Brent MR passed 4/5 gates** (SR 0.63, plateau, halves, yearly) but failed scramble: the profitable part is
   the 2000-2014 episode (spread rarely negative before shale); post-2011 the spread is a different regime and timing
   signals add ~nothing (sharper-timing variants: SR ≈ 0). Scramble gate caught a regime bet, not a repeatable signal.
4. **Yearly-gate calibration note (feedback to coordinator):** ≤2 neg years in 15-27y at vt10 implies P(neg year) ≤ 7-13%,
   i.e. needs SR ≳ 1.1-1.3 absent skew. Gates a-c are internally consistent with SR≥0.6 but gate (d) dominates and
   effectively requires SR ~1.2+ for symmetric-return books. Either (i) accept it and expect few sleeves ever pass
   (r2: SR 1.45 sleeve still failed), or (ii) acknowledge skew/variance-drain sleeves are the intended passers.
5. Scramble-methodology note: scramble_test on POST-vt returns inflates the null (slow leverage persistence raises
   scrambled SRs). Use pre-vt net returns for the test. p-values here are pre-vt.
6. Not-overlapping recommendation: BLEND4's components are pairwise-corr ≤0.10 and its worst year is −2.6% — if the
   coordinator ever relaxes gate (d) to ≤4 soft neg years, re-run `idea24_blend4.py` first.

Scripts kept: campaign/scripts/a2_lib.py (PIT COT loader + mapping + mechanics), and
campaign/agents/A2_fx_carry/scripts/idea12..25 (all sweeps reproducible). Sleeves dir empty (nothing passed).
ROUND r2 DONE

## Round r2b (2026-08-28) — COT positioning + macro-CTA + spread MR (r2 charter, executed)

Prior r2 session crashed before running anything (scripts idea12–20 existed, logs empty; sleeves dir empty).
r2b executed every charter idea with the PIT-correct lib (a2_lib.py: Tue report → +4 trading days release lag).

| # | idea (charter item) | best FULL SR | H1/H2 | verdict |
|---|---------------------|--------------|-------|---------|
| 12 | (1a) lev-funds net-z CONTRARIAN fade, TFF 2010+, lb∈{26,52,104,156}, thr∈{1.0..2.0}, 9 assets | 0.44 (lb104/thr1.5) | 0.24/0.75 | FAIL full+halves; lb=78 (−0.0) & lb=156 (−0.34) collapse → isolated spike, no plateau |
| 13 | (1b) asset-mgr 6m-change MOMENTUM follow, lb∈{13,26,52,78,104} | 0.41 (lb52) | 0.19/0.75 | FAIL; short lookbacks negative (−0.29..−0.33); LF-change variant worse (−0.14) |
| 14 | refine z-fade/AM-mom (longer lb, zcap sweep) | 0.44 | 0.24/0.75 | FAIL — confirms #12 is the family peak and it's sub-bar |
| 15 | per-asset attribution of #12 lb104/thr1.5 | 0.54 (QQQ) | 0.55/0.53 | FAIL; no asset passes; bonds sub-book SR 0.13; driver was QQQ momentum-in-disguise |
| 16 | (2) TSMOM-sign breadth book, 18 FRED-mapped assets, w∈{63..504} | −0.00 | −0.35/0.12 | FAIL badly (21/44 neg yrs) |
| 17 | multi-horizon TSMOM [63,126],[126,252],[63,126,252],[21,63,126,252] | 0.33 | 0.64/0.05 | FAIL (H1 0.64 but H2 ≈ 0) |
| 18 | (1c) COT-extreme veto on 63/126 TSMOM (conflict/fade modes) | 0.33 | 0.52/0.14 | FAIL; veto never helps |
| 19 | (3) gold/silver ratio MR (state-machine bands) + gold trend + combo | 0.54 (gold trend 126d) | 0.48/0.60 | FAIL; ratio MR is a coin (0.00–0.04); combo 0.40 |
| 20 | (4) WTI-Brent spread MR + copper/gold ratio trend | 0.63 spread / 0.06 cu-au | 1.9/0.4 | cu-au FAIL; spread MR → promoted to deep dive (#21) |
| 21 | **(5 deep dive) WTI-Brent spread z-fade honesty audit** | 1.97 zero-lag → **0.41 lagged** | 2.23/1.69 → 0.41/0.41 | **REJECTED: publication-lag lookahead** (details below) |

### Idea 21 — the one that got away, and why it HAD to be rejected
Zero-lag daily build (z126, thr 1.0, exit 0.75, 2×6bps, 10% vt): SR 1.97, ann 20.9%, H1 2.23/H2 1.69,
1 neg yr (−2.2%), maxDD −12.2%, plateau 1.47–2.31 across all 18 neighbors, scramble p=0.000 (correct
pos-vs-fwd pairing), max corr 0.08 to the 40-sleeve library, SR ex-2020 2.06, ex-2008 1.98, ex-best-day 2.00,
stable by decade (1.81/1.89/1.73). It passes every written gate.
**Why it's still rejected:** the signal uses EIA *daily spot* prints that are published the NEXT morning.
Booking P&L on the decision-day convention with zero lag harvests the t→t+1 move that is unknown at
decision time. With the honest 1-day publication lag: SR 0.41 (H1 0.40/H2 0.41); lag 2: 0.25; weekly
decision with 2-day staleness: 0.41–0.49, scramble p=0.77. The edge lives entirely in the first
post-print move = lookahead. Also neutralized: Apr-2020 −$36.98 WTI spot print treated as unpriceable
(it adds a phantom +147% day and 17% of cumulative P&L in the naive build).
Repro: scripts/idea20b_wtibrent_honest.py. **No sleeves saved this round — nothing cleared all gates.**

### Lessons for r3+
1. Gate (e) scramble is necessary but NOT sufficient — a signal can be statistically real and still
   lookahead (idea 21 passes scramble at 1.97 only because the lookahead is consistent). Publication
   calendars must be audited for EVERY data source: EIA spots +1d, FRED monthlies +1mo, CFTC +4d (lib ok).
2. The harness's decision-date convention (pnl booked at t, realized t→t+1) silently assumes data at t
   is public at t. Any daily macro print violates this by 1 day — worth a shared `publag()` helper.
3. COT positioning on these 9 liquid assets adds nothing net of costs at weekly freq (two independent
   families, both <0.45 with no plateau) — I would stop allocating to COT-on-FRED-mapped-assets.
4. Gold 126d trend (0.54) and equity-index COT-fade (0.54) are near-miss diversifiers if the bar ever
   relaxes; not saved per contract.
ROUND r2b DONE

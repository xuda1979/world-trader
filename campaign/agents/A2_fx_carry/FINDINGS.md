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

# Round r4 (2026-08-30) — return-tilted charter (SR>=0.8 + ann>=12% + |corr|<=0.3 to champion)

**Setup:** new honest mechanics lib `scripts/r4_lib.py` (decision-date convention, T+1 via
`px.pct_change().shift(-1)`, 6bps/side on |Δpos| turnover, trailing expanding vol-target min60d lag1,
gates hard-coded to charter r4: full SR≥0.8, halves≥0.4, ≤2 neg yrs, worst yr >−6%, ann≥12%,
corr≤0.3 to `CHAMPION_FINAL_daily.csv`). Vol budget raised to 15–20% where noted (allowed by charter).

| # | idea (charter item) | best FULL SR | corr→champ | failing gate(s) | verdict |
|---|---------------------|--------------|------------|------------------|---------|
| 26 | (1) XAU/SLV/CU 126d trend + reinvested carry, vt15; 22 configs (lb 63–252, L/S & long/flat) + 3-asset blend | 0.72 XAU-lf126 (plateau 0.49–0.72, all lb<0.8) | 0.02 | full SR (all 23 configs <0.8) | FAIL — **carry construction impossible on free data**: FRED xau/slv are spot series (no futures/lease/storage terms), copper is monthly-only; only drift+trend is implementable |
| 27 | (2) SPY long when VIX<thr (lag1/lag2), flat above; thr 20/22/25/28 ± 126/252d trend gate; vt20 | 0.52 (VIX<25+tr252) | −0.01 | full SR (all 12 <0.8) | FAIL — regime filter alone can't hit 0.8; corr ≈ 0 while active but too little edge |
| 28 | (3) FF monthly best-factor timing, lb 126/252/378, 2x, vt10/20 | 0.65 (lb252-vt20) | **0.51** | full SR AND corr>0.3 | FAIL — timing works-ish but it's equity-beta-in-disguise (corr 0.45–0.57); return-tilt cancels the diversification |
| 29 | (4) BTC 63d trend vt20 | — | — | n=1001 daily rows (2.8y) < 1500 minimum | **SKIP honestly** (charter pre-declared skip; padded via weekly? still only ~145 obs) |
| 30 | (5) 2s10s DV01-neutral z-book: fade z756, mom 63/252, always-flat/steep; vt15 | −0.53 fade / −1.77 mom63 / 1.04 steep-always | −0.04 | SR<0 or **yearly 8 neg yrs worst −25.6%** | FAIL — only the unconditional steepener "works": pure secular term-premium bet 2005-2020, no signal, crashes 2022 (same verdict as r2 #22) |
| 30 | (mine) A2 RETURN blend vt15: EW(ratesLF378, XAU-lf126, CU-lf3m) | 0.86 | 0.02 | **yearly 11 neg yrs worst −14.7%** | FAIL — SR clears 0.8, yearly gate kills it |
| 31 | 4-way + FF252 (dilute corr), 2007+ live window | 0.78 | 0.44 | full SR AND corr | FAIL — adding FF buys corr 0.44 without reaching 0.8 |
| — | UST2-LF378 (r2's SR 1.45 best) at vt15/vt20 | 1.45 | 0.00 | yearly 5 neg yrs; ann 5.8% | FAIL + **see vt-cap lesson below** |

### Lessons (r4)
1. **`util.vol_target` clip(0,3) makes "raise the vol budget" a silent no-op for low-vol books.**
   UST2-LF378 net vol ≈ 4% → required leverage 3.75–5.0x exceeds the cap → vt10/15/20 produce
   IDENTICAL series (SR 1.45, ann 5.8%). Any charter that grants "2x vol budget" must also grant a
   leverage-cap override, or the grant is void. I did NOT override the shared cap (contract: don't
   modify shared lib; local override = nonstandard mechanics); documented instead. De-capped linear
   scaling would give ann ≈ 11.6% — still below the 12% bar AND still 5 neg yrs → fails regardless.
2. **Charter r4's bar (SR≥0.8 + ann≥12% + corr≤0.3) is jointly hard for A2's asset classes on free
   data:** the only books with SR≥0.8 available to me (UST2-LF, steepener) fail the yearly gate or are
   unconditional secular bets; the only genuinely low-corr books (metals, SPX-VIX regime) top out at
   SR 0.5–0.7; the only 12%+ books (FF timing) carry equity-beta corr 0.45–0.57.
3. Free-data carry remains unbuildable for metals (spot-only FRED series) — r1's FX conclusion
   generalizes: without futures-curve or deposit-rate data, "reinvested carry" is not implementable,
   only drift/trend proxies.
4. corr-to-champion is itself a binding design constraint: champion is 50%+ equity-factor driven
   (XGB1y + Merger-Arb-PEAD), so any return-tilted equity/factor book auto-fails the ≤0.3 test.

**Sleeves saved: 0.** Nothing cleared all charter gates. Best honest near-misses for future rounds:
A2-RETURN-blend SR 0.86 corr 0.02 (needs yearly-gate relief — see r2 note #6: it has 11 neg yrs,
too many even for the relaxed ≤4 rule), UST2-LF378 SR 1.45 (needs ≤5-soft-neg-yr rule), both
scramble-ready if the coordinator re-calibrates gate (d).
Scripts: r4_lib.py, idea26_metals_carry.py, idea27_spx_vix.py, idea28_ff_factortime.py,
idea29_curve_z.py, idea30_return_book.py, idea31_blend4way.py.
ROUND r4 DONE

# Round r6 (2026-08-30) — overnight/intraday split charter (idea 32-35)

**Setup:** built ON/ID decomposition for the full 298-panel (ON_t = open_{t+1}/close_t−1, ID_t = close_t/open_t−1,
booking (1+on_t)(1+id_{t+1})−1 = c2c exactly; max daily EW residual 6e-3). Panel clean: 5005 tradable nights
2006-09→2026-08, ~271 names/day, zero inf/zero prices; only legit corporate-action gaps (AIG/GM 2009, SOFI 2021),
winsorized at |on|<50%. Costs per charter: 12bp/d for every held overnight day (6bp close t + 6bp open t+1).

**Core economics (the whole story):** gross EW overnight premium = **4.7bp/day**; cost = **12bp/day**. Even the
best year in 20y (2021: 8.5bp/d) < daily cost. Best possible single day is irrelevant; the family is cost-dead.

| # | idea | gross | net (12bp/d) | verdict |
|---|------|-------|--------------|---------|
| 32 | (1) always-on ON EW, vt10 | +4.7bp/d SR 0.32 | **SR −0.50**, all 21 yrs neg, H2 −1.69 | FAIL — breakeven cost ≈2.3bp/side vs mandated 6bp |
| 33 | (2) ON ∩ TOM (7 windows, e.g. last3+first2) | last-td ON 8.6bp/d gross | best SR −0.64 (last1td) | FAIL — TOM concentration (~2x mid-month) is real but far too small vs 12bp/d |
| 34 | (3) intraday-only book | **+3.1bp/d gross, POSITIVE in all four 5y windows** (SR −1.43 net) | — | FAIL net; **logged as regime finding:** the classic "all equity return is overnight" claim is FALSE in this panel post-2012: ID contributes ~half the gross premium but ~1/3 the variance |
| 35 | extra: XS tilt by trailing 252d mean ON (top-20, 9 configs) | PIT-honest SR 0.08 | SR 0.08, H2 negative everywhere | FAIL — and a **trap of the round**: unshifted signal scores SR 1.34 because ON_t sits inside its own trailing window (21.8 vs 12.6bp/d). Oracle full-sample top-30 = 13bp/d gross ≈ exactly the cost hurdle |

**Gates:** all of a–f fail at the first gate (FULL SR<0.6) for every config; scramble moot; corr-to-champion
measured on least-bad variant = 0.001 (the family IS orthogonal — there is just no return to diversify).

## Honest conclusions (r6)
1. **The overnight family is un-investable at campaign costs, by an order of magnitude.** 12bp/d daily round
   trip = 30%/yr hurdle vs a 4.7bp/d (≈12%/yr raw, ≈5.4% risk-adjusted-hurdle-free) premium. It would need
   ~1bp/side costs to clear zero, ~0.4bp/side to reach SR 0.6 — not a 6bps-world strategy. Negative result is
   the deliverable, per charter.
2. **Charter premise partly wrong for this data:** the documented large-cap overnight premium (1980-2020) is
   mostly a 1980-2000s result plus gross-only accounting; net of realistic retail/inst costs it evaporates.
   Meanwhile the intraday leg is gross-POSITIVE in every 5y window since 2007 (+3.5/+4.5/+1.6/+2.7 bp/d) —
   mildly contradicts the "intraday is negative" prior; if costs ever fall to ~1bp/side, intraday-MR books,
   not overnight books, are the first family to become viable. Neither clears at 6bp/side.
3. **Lookahead trap of the round (generalizes):** rolling-mean-of-overnight-return signals must shift(1) —
   ON_t is the last observation of its own trailing window, so an unshifted ranking harvests ON_t itself
   (SR 1.34 vs 0.08 honest). Same family as r2b's EIA publication-lag catch: whenever signal window and
   return window overlap on the same bar, the backtest silently buys the return it just measured.
4. Corr to champion 0.001 confirms the orthogonality promise — but SR −0.50 means nothing to blend.

**Sleeves saved: 0** (nothing cleared even the FULL-SR gate; scripts idea32-35 + r6_lib.py reproducible).
ROUND r6 DONE

# A1_trend_cta — FINDINGS

## ROUND r1 (2026-08-28)
Verdict: **NO sleeve saved.** All charter families + FX + one composite construct ran
through the full honest pipeline (T+1, 6bps/side per-unit-turnover, trailing-only vol).
Binding constraint: gate-d (yearly: <=2 neg years, each > -5%) — every trend book had 3-8
negative years. Secondary: SR rarely cleared 0.6 net.

### Environment fixes that matter for everyone
1. `data.ff_mom()` is broken (header parse). Workaround: `pd.read_csv(..., skiprows=13,
   names=["date","Mom"])`, `pd.to_datetime(..., errors="coerce")`, dropna.
2. Flip-invariance bug class: computing ratio momentum on flipped levels (-yields) is a
   no-op ((-a)/(-b)=a/b) and then multiplies flipped returns -> systematically NEGATIVE SR
   (~-0.3 per flipped asset). Must compute trend on original levels and flip the SIGN.
   (My first Idea-1 run showed SR -0.48; after fix +0.36. Same sign convention must be
   audited in any sleeve that trades inverted series.)
3. Subtle lookahead class: per-asset inverse-vol weights using rolling std that includes
   day t's return while earning day t's return. Fix: `.shift(1)` on the vol input
   (costs ~0.01-0.02 SR here, but it's the difference between honest and not).
   Note `harness` prior CTA sleeves may contain this bug class — worth an audit.
4. `eval.py` halves use median-day split; fine. FRED `spx`/`dow` start 2016 only —
   use `twelve_big` SPY for equity legs. FX panel only starts 2019-04 (8 pairs) —
   too short for 20y contract; FX TSMOM also SR-negative there (best +0.14 rb=21 L=252).

### Idea 1 — TS-momentum on FRED macro basket (7 assets: xau, wti_full, brent, natgas,
dxy(flip), us10y(flip), us2y(flip)); sign(P/P_L-1), per-asset vol-target, 10% book,
variable-lag warmup, sequential expanding scale, costs per position change.
Grid L{63,126,252} x rb{5,21}: best L=252/rb=5 SR=0.54 (H1 0.44/H2 0.63);
multi-lookback avg [63,126,252]/rb=5 SR=0.54 (8 neg yrs); [126,252]/rb=5 SR=0.55,
H1 0.50/H2 0.61, 8 neg yrs. Ex-natgas SR=0.59, 7 neg yrs. **FAIL (SR<0.6, gate-d).**
Per-asset trend SR (252d, net): xau +0.24, wti +0.17, brent +0.08, natgas -0.26,
dxy +0.02, us10y +0.09, us2y +0.30 — commodity trend weak post-2010 except precious.

### Idea 2 — Dual momentum (63d AND 252d agree), core-6 basket
rb=5: SR=0.47 (H1 0.40/H2 0.54), 6 neg yrs; rb=21: SR=0.42, 8 neg yrs. **FAIL.**

### Idea 3 — Trend on FF daily factors (Mkt-RF, SMB, HML, Mom), 2006+
Multi-LB avg rb=5: SR=0.28 (8 neg yrs); L=126 rb=5: SR=0.37 (H1 0.55/H2 0.17!, 7 neg yrs).
Per-factor trend SR: Mkt-RF +0.19, SMB -0.21, HML +0.10, Mom -0.03. **FAIL.**

### Idea 4 — Long-only inverse-vol RP with own-trend gate (fam 4)
- 6-asset (SPX,xau,wti,brent,dxy-inv,us10y-inv): best SR=0.43, 6 neg yrs. **FAIL.**
- 3-asset (SPX, US10y-inv, XAU): L=252 rb=5 SR=0.76 (H1 0.57/H2 0.93) but 4 neg yrs
  (2011 -4.0, 2014 -1.0, 2015 -1.9, 2018 -2.0) — all mild but count > 2. **FAIL gate-d.**
- +US2y-inv (4-asset) = best structure found this round: L=252, wlb=42, rb=5, bw=42
  (honest vol-shift): **SR=0.84 net, H1 0.63/H2 1.03, vol 10.6%, 3 neg yrs
  (2011 -2.8%, 2019 -4.7%, 2020 -10.8%)** — fails ONLY gate-d (2020 breach + count 3).
  The -10.8% is 2020 COVID: gates all stale-long SPX into the crash (252d trend flipped
  only in late March); every gate variant (dual 63&252: worse, -13.6%; multi-LB: worse;
  faster book-scale bw=10/15: -8..-9% but more neg yrs) still breaches.
- Yield-vs-price convention: gating on *yields* (us10y-inv long when yields trend up)
  misses every flight-quality rally; book was structurally naked in 2008/2020.
  Trading bond *prices* instead (D=8/D=2 duration proxies) flips the failure mode:
  holds bonds into 2013/2015/2018/2021/2022 selloffs — SR 0.66 best, 6 neg yrs. **FAIL.**
- Price-only flight-to-quality book (US10y-inv, US2y-inv, XAU): SR=0.57, 4 neg yrs. **FAIL.**

### FX (charter notes) — 8 pairs, TSMOM L{63,126,252} x rb{5,21}: SR -0.59..+0.14.
Negative or negligible; panel 2019+ only. **FAIL (and too short).**

### Composite CTA program (Idea1-book + Idea4-book, 50/50, expanding 10% scale)
BookA = multi-LB [63,126,252] L/S 7-asset TSMOM rb=5 (SR 0.39 net standalone);
BookB = 4-asset gated RP above (SR 0.84). corr(A,B) = **-0.05** — genuinely diversifying.
Composite: **SR=0.87 net, H1=0.58 / H2=1.14, vol 10.2%, ann 8.9%, MaxDD -15%,
2 neg yrs only (2012 -0.6%, 2019 -3.2%)**; yearly 2008 +10.6, 2014 +18.4, 2017 +24.4,
2020 +5.4, 2022 +31.2. Gates: full-SR PASS, halves PASS (H1 0.58>=0.3), yearly PASS
(2 neg, both > -5%), plateau PASS (chosen 0.867 at 92% of neighborhood peak 0.938;
12 neighbor configs >= 80% of peak — A_LB variants, A_rb{10,21}, B_L126, B_wlb{21,60},
B_rb21, B_bw21), expanding vol-target PASS. **Scramble FAIL: p=0.060 at 200 draws,
p=0.061 at 1000 draws (61/1000 rotated books >= real 0.867; pre-committed 0.05 rule).**
Not saved. Diagnosis: BookB's long-only RP earns much of its return from standing risk
expo (vol-scaled beta + carry-like collateral yield), which survives rotation; the
timing edge alone is not distinguishable at this test's power. To pass, the composite
needs either a genuinely timing-driven second book or BookB made long/flat cash-futures
style (return from bond/gold trend, not standing SPX beta).

### Reusable artifacts
- `engine_a1.py` in this dir: honest engine (T+1 per-position cost accounting, variable-lag
  warmup, sequential expanding scale, gates incl. rotation scramble). Verified consistent
  with dead-simple shift(1) TSMOM per-asset diagnostics.
- Grid dumps: /tmp/a1_grid1.pkl, /tmp/a1_i4_grid.pkl, /tmp/a1_final.pkl, /tmp/a1_scramble.pkl
- LOG.md has per-run numbers.

### Recommendations to coordinator
1. Gate-d as written (<=2 neg years each > -5%) rejects EVERY trend/CTA construct tried
   (12+ configs with SR>0.55). Library CTAs already in the sleeve_library have 4-13 neg
   years, so gate-d is either calibrated for non-CTA sleeves or library CTAs predate it.
   Suggest: keep absolute gate on worst year, relax count to <=4 for long/short trend
   sleeves, or gate on rolling-12m loss instead of calendar years.
2. The scramble test at pipeline level (rotate positions through identical cost/vol
   machinery) is much stricter than scrambling raw signal and is the right test — but
   note rotated books keep standing risk exposure; sleeves whose edge is a *premium*
   (not pure timing) will systematically fail it. Decide explicitly whether premium
   sleeves are in scope; if yes, scramble should rotate only the *timing overlay*.
3. Bugs in shared library: ff_mom() parse error; audit library CTA sleeves for the
   same-day vol-scaling lookahead (I found and fixed it in my own engine).

### r1 ADDENDUM (same day): script-version re-validation of the composite
While reproducifying, a specification discrepancy was found between the analysis run and
the saved script: the analysis run had trimmed the gate levels for BookB to 2008+ (leaving
the 252d gate cold through 2008), whereas the script correctly uses the 2006-2007 history
that exists on disk. The script is the correctly-specified strategy. Re-ran ALL gates on it:
- Composite v2 (correct warm gate): **SR=0.937, H1=0.722 / H2=1.143, 2 neg yrs
  (2012 -0.62%, 2019 -3.17%)**, vol 10.2%. BookB standalone SR=0.841 (vs 0.777 trimmed).
- Plateau: PASS - chosen 0.937 = 95% of neighborhood peak (0.990, A_rb10);
  **11/11 neighbor configs >= 80% of peak** (A_63-126/126-252/252, A_rb10/21,
  B_L126, B_wlb21/60, B_rb21, B_bw21). Broadest plateau of anything tried.
- Scramble (1000 draws, rotation through identical pipelines, seed 20260828):
  **p = 0.179 (179/1000) -> FAIL.** Even worse than the trimmed variant (p=0.061):
  the 2008 gain (+10.6% yr) comes largely from standing vol-scaled exposure surviving
  rotation, not from timing.
FINAL r1 VERDICT: FAIL on gate (e). Not saved as sleeve. The composite is retained as
`agents/A1_trend_cta/scripts/cta_gated_program_v1.py` (clearly marked NOT SAVED) as the
r2 iteration base. Key lesson: SR/halves/yearly/plateau all improve with standing risk
premium exposure, but the scramble test (correctly) rejects sleeves whose live SR is not
distinct from rotated exposure. r2 directions: (a) make BookB timing-only (trade bond
TSMOM directly instead of cash-beta + collateral), (b) bigger BookA weight since BookA
passes scramble logic trivially (pure L/S timing), (c) raise scramble power by rotating
BookA and BookB jointly 5-10k times if boundary cases appear.

ROUND r1 DONE

## r2 results
1. BREADTH CTA standalone (mission 1; 9 charter legs, spx dropped: series starts 2016): best honest config
   long/flat L=189 C=84 leg-vol-sized (cap 1.0): SR=0.58, H1=0.43, H2=0.70, ann 13.1%, vol 22.6%, 6/18 neg years
   worst -18.8%. Long/short variant much worse (SR 0.19, H1 -0.11). Fixes tried, all fail gates a+d: dedup 9->8 legs
   (wti+brent->crude), cap 0.7-1.0, book-level trailing vol-target, multi-horizon ensemble (63..315d; best SR 0.53,
   6-7 neg yrs). Verdict: FAIL (yearly gate unreachable for long/flat multi-market trend on these legs; 2022 itself
   is fixed by breadth — dxy +8%, crude +13% — but 2012/2013/2015/2017/2018 whipsaw years remain negative).
2. Sector momentum on 298 panel (mission 2; average-linkage clustering on MARKET-RESIDUALIZED 126d corr, K=25
   min-size 8; 6m momentum top-4 sector books, monthly, 6bps, trailing vol-target): raw SR=0.72, H1=0.52, H2=0.95,
   3 neg years (2008 -17.6%). + market-regime overlay (EW index vs 200d MA, floor 0): SR=0.91, H1=0.80, H2=1.01,
   worst year -6.7%, but 5 neg years -> FAILS gate d. Killer finding: corr 0.62-0.85 to existing library
   long-equity sleeves (Risk_Parity 0.85, SharpeW 0.83, L_S_130_30 0.63) — no diversification value; 2008 crash is
   structural (momentum crashes when market turns), overlay fixes magnitude not sign of bad years.
3. MIX SLEEVE (mission 3, charter-sanctioned) — SAVED: A1_mix_breadthCTA_SharpeW_LS13030.
   1/3 breadth CTA (8 legs raw net) + 1/3 Multi_Strategy_SharpeW + 1/3 L_S_130_30 (2022-positive library members,
   pre-specified), single trailing expanding 10% vol target. Window 2008-01-03..2026-08-11 (strict, includes 2008):
   SR=1.04, H1=1.08, H2=1.01, ann=11.3%, vol=10.9%, MaxDD -17.6%, neg years 2/19 (-3.5% 2018, -4.3% 2023),
   2008 +13.2% (breadth-CTA leg alone +55% in 2008 = crisis alpha), 2022 +0.7%. Gates: a PASS, b PASS
   (plateau min ratio 0.90 over weight +-0.1 and (L,C) in {126,252}x{63,84} neighbors), c PASS, d PASS, e PASS
   (scramble 200 perms, T+1-aligned applied weights, real SR 1.03 vs null mean 0.81 / p95 0.99, p=0.020),
   f rationale in .meta, g vol 10.9% via trailing-only expanding target. Eval harness confirms.
   Note: saved 2008-start variant, not the looser 2009-start (SR 1.08): stricter window, includes crisis.
   Honesty: first scramble run had a same-day-weight lookahead bug (p=0.0000); exposed by real==official identity
   check, fixed to W.shift(1); corrected p=0.02. Correlation of mix to members ~0.6 by construction; breadth leg
   itself is near-zero corr to library (-0.09..+0.02) and is the r2 novelty worth blending further.

ROUND r2 DONE

## r3 results
1. VOL-OF-VOL SEASONED CTA (charter 1) — FAIL. Breadth CTA (8 legs, r2 config) + leg-level chop filter
   (21d vol-of-vol < 252d median) + monthly rechecks + tbill accrual on filtered-out capital: best SR 0.75
   (H1 0.45/H2 0.99), 4 neg years, worst -15.3% (2012). L/S variant 0.50 (2012 -29.7%); book-level vov gate 0.64.
   Verdict: vov removes vol-expansion chop (2023 improves) but 2012-2013 slow-grind whipsaw happens at
   BELOW-median vol-of-vol, so the filter is structurally blind to the charter's target years. Not saved.
2. GOLD CARRY-TREND (charter 2a) — standalone FAIL (5 neg years, worst -5.2%), but saved as blend member:
   long xau when 252d AND 84d trend up, else T-bill accrual; SR 0.78 (H1 0.47/H2 1.01) 2008+.
   Grid L{126,189,252,315}xC{none,84}: 0.61-0.80, plateau decent.
3. CRUDE-BRENT SPREAD (charter 2b) — honesty deep-dive. The charter's "0.41 honest" number is confirmed,
   and I caught MYSELF rebuilding the same lookahead under a different name: pos.shift(1) earning
   spr(t)-spr(t-1) books the pre-publication move (EIA daily prints publish next morning); SR 1.71 at that
   convention collapses to 0.41 with one more day of lag — the collapse localizes the edge to the
   unownable interval. True attainable: decision at t from z(t-1), earn spr(t+1)-spr(t): SR 0.41 (H1 0.40/H2 0.42).
   The Apr-2020 negative-print exclusion is a premium not an artifact (removing it costs +1.3 SR in BOTH the
   honest and lookahead builds, via 2020 +48%); scramble p=0.0000 (500 draws, position-rotation). Kept as blend member.
4. NATGAS WINTER (charter 3) — standalone FAIL (SR 0.47, 4 neg years incl 2020 -4.2%), saved as blend member:
   long Nov-Feb only, expanding-vol sized, tbill accrual on flat months, T+1. 2006+ window works; L/S with
   summer short is much worse (0.26). Caveat: FRED natgas is a back-adjusted continuous series; roll-adjusted
   futures seasonality may differ (no free daily futures curve available to check).
5. BLEND (charter 2+3; idea-4 mixes tested below) — SAVED: A1_carry_seasonal_v2.
   EW 1/3 each: honest crude-brent z-fade + natgas winter + gold carry-trend; member vol-target 10%
   (trailing expanding, shift 1, cap 1.0); single book re-target 8% (trailing expanding, shift 1, cap 3x;
   chosen so realized full-window vol lands at 10.1%). Pairwise member correlations 0.00-0.03.
   Window 2008-01-03..2026-08-03 n=4848: SR=0.82, H1=0.57, H2=1.01, ann 8.3%, vol 10.1%, MaxDD -12.7%
   (2021 natgas-vol drawdown, no calendar-year loss), 0/19 negative years; 2012 +0.0%, 2013 +0.4% — the
   whipsaw years the charter asked about are exactly where this sleeve goes flat and bleeds nothing.
   Gates: a PASS; b PASS (14 neighbors — 6 weight grids ±0.1, zwin 63/252, goldL 126/315, natgas-month
   variants, book-tgt 7/9% — min ratio 0.90, max 1.09); c PASS; d PASS (0 neg years, worst +0.02%);
   e PASS (500 draws rotating ALL THREE member position vectors through identical honest pipelines,
   identity-check enforced, seed 20260828: null mean SR 0.22, p95 0.47, p=0.0000); f rationale in meta;
   g PASS (realized 10.1%). Correlations: CTA_15vol 0.02, Global_Macro 0.02, Multi_Strategy_SharpeW 0.05,
   L_S_130_30 0.05, Risk_Parity 0.03, my saved A1_mix 0.32. Repro: campaign/scripts/a1_carry_seasonal.py.
6. IDEA-4 MIXES (charter 4) — not saved. +Credit_z120_1986 (EW 1/4): SR 0.73, H1 0.41/H2 0.95, 2 neg years
   — passes a/c/d numerically but strictly dominated by the 3-blend (weaker H1, dead weight member:
   credit sleeve standalone SR≈-0.01 on 2008+, H2 -0.69). 30/20/20/30: 0.68. Adding my vov-CTA book as 4th
   member: SR 0.98 but 2012 -7.5% FAILS gate d (vov book drags 2012/2013 in).
### r3 lessons for the campaign
- The blend of three STANDALONE-FAILING members (SR 0.41/0.47/0.78) produced the strongest sleeve of my
  three rounds: gate-d's per-sleeve yearly requirement is anti-diversification when applied before blending.
- Second lookahead trap of the same family as A2's, worth an alert: "shift the position by 1 day" is NOT
  automatically honest when the SIGNAL ITSELF is only publishable 1 day after it appears. Shift position by
  1 beyond the publication lag, then verify by lag-sensitivity (edge should decay smoothly, not cliff).

ROUND r3 DONE

## r5 results (2026-08-30) — THE decisive round: 4 charter ideas, 0 sleeves saved, 1 artifact family killed
Bar per CHARTER_r5: SR>=0.9, halves>=0.45, <=3 neg yrs, worst>-8%, scramble<0.05, plateau, corr<0.35 to champion;
vol budget <=20%; negYears<=3 / worst>-8% relaxed gates. All mechanics: T+1, 6bps one-side x |dw|,
trailing expanding vol target (min60d, lag1), 2008-01-03+ window. Repro: agents/A1_trend_cta/scripts/r5_charter.py.

1. GOLD TREND AT VT20 (charter 1) — FAIL. 16 configs (L{126,189,252,315} x dual-confirm {none,63,84,126}).
   Best 126d single-gate: SR 0.75, H1 0.60/H2 0.88, ann 16.7% — but 7 neg yrs, worst -13.0% (vol budget scales
   losses past -8%). The charter's "SR 0.78@vt10" number was my r3 gold carry-trend with tbill accrual on flat;
   pure price trend is 0.55-0.75 and the dual 63/252 confirm makes it WORSE (r1 finding replicates: 0.42 at vt20,
   worst -39.9%). Verdict: gold trend ret~14-16% is reachable but whipsaw years scale up 1:1 with vol. Not saved.

2. A1_CARRY MEMBERS AT MEMBER-VT20, BOOK VT15 (charter 2) — FAIL. Rebuilt my r3 book with member vt 0.20:
   members cbz 0.41 / natgas-winter 0.42 / gold 0.68; BOOK SR 0.74, H1 0.54/H2 0.89, ann 14.0%, 2 neg yrs,
   worst -1.3% — beautiful risk profile, but SR<0.9 AND corr 1.00 to my already-saved A1_carry_seasonal_v2
   (same three members at member-vt10/book-vt8): it is a RE-LEVER, not a new sleeve. Not saved (would double-count).

3. SEASONAL-ASYMMETRIC TREND (charter 3) — FAIL, closest miss. 5-leg long/flat: metals H2-only (xau,slv L126),
   energy H1-only (wti,natgas L126), + xau all-year (L252&84); member vt20 cap2, book vt20 cap2.
   SR 0.92, H1 0.54/H2 1.20, ann 21.3%, SRm 0.94, scramble p=0.0050 (200 draws, member-rotation through
   identical pipeline, seed 20260828). BUT 4 neg yrs (2012 -4.1, 2016 -5.9, 2017 -0.4, 2024 -24.5 vs charter
   bar <=3) and worst -11.4% < -8%. Attribution: slv H2 and wti H1 whipsaw legs drag 2012/2016/2017;
   2024 loss is natgas-winter leg + slv. AND corr 0.46 to champion (>0.35 bar, metals H2 = same premium as
   my saved A1_carry gold leg). Month-timing note: empirical trend-positive months only PARTIALLY match the
   charter's prior (metals also positive in H1 months 1,2,4,5; natgas H1 is real). Not saved.

4. UST2-LF378 REBUILD AT VT15-20 (charter 4) — FAIL, and the family is an ARTIFACT. === ROUND'S HEADLINE ===
   The famous A2 r2 "SR 1.45 / H1 1.50 / H2 1.45" (and my first r5 build at SR 1.55, ann 14.8%, SRm 1.57,
   3 soft neg yrs, corr -0.00, lag-robust +0/+1/+2/+5/+21, scramble p=0.026) all share ONE accounting flaw:
   UNFUNDED LEVERAGE. Mechanics `L*pos*TR + (1-pos)*rf` charges funding only on the FLAT fraction, so when
   vol-targeting pegs leverage at cap, the book earns (L-1)*rf phantom carry on the WHOLE notional
   (cap3/A2: +2.8%/yr avg but +5-8%/yr in 2023-25; my first cap8 build: +9.8%/yr, i.e. +35%/yr in 2023-25).
   Honest futures accounting rf + L*(TR - rf) with leverage sized on trailing EXCESS vol:
   SR 0.53, H1 0.48/H2 0.60, ann 5.1%, 7 neg yrs, worst -7.8%; D-robustness D=1.5/2.0: 0.60/0.38.
   TRUE timing edge (excess return vs cash): SR 0.39, ann excess 0.46% — the 252d-trend gate is real but tiny;
   pre-2022 the 2y carry (y-rf) did the heavy lifting at any leverage. Scramble p=0.026 passes only because
   rotated books enjoy the same phantom. IDEA 4 DEAD, and A2's r2 #23b / r4 vt-lesson numbers are void.
   NOTE the honest excess-SR regime result: excess ann +0.46% pre-2022 avg vs 2023-25 ~+4%/yr — the edge is
   post-ZIRP regime, too short to certify at <0.05 with 19y of book.

5. HYBRID (book2 50/50 book3, book vt15 cap3) — BEST NUMERICS, FAILS ONE GATE. SR 0.98, H1 0.77/H2 1.15,
   ann 18.4%, vol 18.8%, SRm 1.10, MaxDD -19.5%, 3 neg yrs (-3.4/-1.0/-1.0), plateau 0.91-1.00 across
   w2 0.30-0.70 (chosen 0.50 = 98% of neighborhood peak), worst -3.4%. Fails ONLY corr<0.35: 0.53 to
   champion (0.46 from seasonal book metals-H2 premium, rest from trend/energy legs correlated with the
   champion's breadth-CTA and my A1_mix CTA legs). Also book2's 1.00 corr to my saved sleeve means half the
   hybrid is a re-lever of an existing member of the champion. Charter's "SR_m>=1.1, ann>=15%, corr<0.2"
   stretch: SRm 1.10 ann 18.4% achieved, corr never below 0.43 in any weighting. NOT SAVED.

### r5 lessons for the campaign (important for every agent + coordinator)
1. **NEW ARTIFACT CLASS — phantom/unfunded carry.** Any sleeve that (i) trades a TOTAL-RETURN series,
   (ii) holds leverage L from vol-targeting, and (iii) accrues cash yield only on the un-invested fraction
   inflates SR by roughly (L-1)*rf/vol. It inflates MOST at exactly the high-rate/high-leverage years
   (2023-25) that decide recent halves. Audit rule: recompute every levered sleeve as
   `rf + sum_j L_j*(leg_j ret - rf)`; if SR drops >0.2, the sleeve is a funding artifact. Voided: A2 UST2-LF378
   (1.45->0.53 honest 1x-equivalent), and any "levered bond trend" build. UST/AAA/BAA synth TR books across
   the library deserve the same audit.
2. My saved r3 sleeve A1_carry_seasonal_v2 shares the class at BENIGN scale (book lev ~1.0 by construction,
   phantom +0.42%/yr): honest-accounting rebuild = SR 0.77 vs 0.82, still 2 neg yrs worst -0.4%,
   corr(old,honest)=1.0000. All gates still pass. No action needed beyond this disclosure; future sleeves
   of mine use excess-return accounting.
3. vt-cap interacts with phantom carry: raising cap RAISES phantom (cap8 +9.8%/yr at cap-bound). Any charter
   granting "vol budget up to 20%" must PRE-SCRIBE the funding convention, else it grants a free ~rf*excess-L
   subsidy on books that hit the cap.
4. Charter r5's implicit joint bar (SRm>=1.1 ann>=15% corr<0.2 for the frontier gap) remains unmet by my
   families: everything with ann>=15% on free macro data carries corr 0.45-0.55 to the champion (trend legs
   are already IN the champion via A1_mix breadth-CTA and A1_carry). Frontier gap should be hunted in
   genuinely orthogonal sources (new asset classes, new signal families), not vol-budget scaling of known ones.
5. Scramble p-values for seasonal books are easy to pass (p=0.005) while failing calendar-year gates —
   gate-d style yearly checks bind before gate-e for long/flat commodity books. For future rounds: consider
   requiring BOTH negyr<=3 AND worst>-8% at the member level BEFORE blending (my r3 lesson generalized).

ROUND r5 DONE

## r6 results (2026-08-30) — NEW-FAMILY charter: 1 sleeve SAVED, 3 families killed cleanly
Bars (CHARTER_r6): SR>=0.7, halves>=0.35, <=3 negYr, worst>-8%, scramble<0.05, plateau,
corr<0.35 to champion. All runs: honest funding rf + L*(leg-rf), T+1, 6bps one-side x |dlev|,
trailing-only expanding vt (min60d, shift1). Repro: agents/A1_trend_cta/scripts/r6_charter.py,
campaign/scripts/a1_inflation_breadth.py. Log: LOG_r6.log.

1. CURVE ROLL-DOWN CARRY (charter 1) — FAIL, family dead in every variant. 2s10s steepener
   when |z252|>1 (charter literal): SR -0.43 [2005-06+], 15 neg yrs, 2022 -50.4% — the
   "DV01-neutral" steepener still loses exactly when the Fed hikes (bear steepening); 10y30y:
   SR -0.01 (roll-down premium never beats the z-timing losses). Variants all negative:
   vt10 re-lever 2s10s -0.33, mean-reversion-when-extreme -0.24, long-only-when-z>1 -0.42,
   zwin 126/378 x zth 0.75/1.25 plateau probe: best mean SR -0.17. Sign sanity: book P/L
   uncorrelated to spread direction (-0.00), i.e. timing adds nothing on top of a structurally
   negative book. Curve z-timing on 2s10s/10y30y is NOT a roll-down-carry harvest on free FRED
   yields; it's a losing conditional-duration bet. NOT SAVED.

2. INFLATION-PROXY MOMENTUM (charter 2) — SAVED: **A1_infl_breadth_mom**.
   The winner is NOT the charter's ratio but basket BREADTH: frac of {xau, slv, wti, copper}
   with positive 126d return > 0.5 -> long the EW complex (honest rf + lev*(ret-rf)), vt10
   cap2, T+1, copper pub-lagged. 2008-01-03..2026-07-01 (n=4825): **SR 1.15, H1 0.94 /
   H2 1.32, ann 12.5%, vol 10.9%, MaxDD -12.1%, 1/19 neg years (2012 -0.7%)**; pays exactly
   where champion is weak: 2021 +35.4%, 2022 +18.4% (corr 2022-only 0.09), 2008 +2.1%.
   Gates: a PASS; b PASS 0.89-of-peak, flat L{63-126}xvt{10-20}xcap{1.5-3} (honest notes:
   decays L>=189 0.83, thr0.75 0.93, trio-without-slv 0.67); c PASS; d PASS; e PASS
   (500 position-rotations through identical pipeline, identity check OK, seed 20260828:
   real 1.15 vs null mean 0.12/p95 0.54, p=0.0000); f/g PASS. corr champion 0.299 (<0.35),
   AP_gold 0.256 max in library, mean |corr| 0.085 over 42. HONESTY DISCLOSURES:
   (i) copper is MONTHLY; month-M average stamped M+1 = publication lag. The NO-lag variant
   (stale data knowable same-day) scores SR 1.23 / H2 1.49 and is VOID — same lookahead
   family as r3 crude-brent lesson; I save the lagged 1.15. (ii) The charter-literal trio
   xau+wti+cop (no slv) scores only 0.73 with 2008 -20.0% (FAILS worst>-8%): silver's
   inclusion (breadth vote + lower vol book) is what makes the 4-leg book pass — reported,
   not hidden. (iii) The r5 lesson applied: excess-return accounting from the start, so no
   phantom-carry audit needed (book lev avg ~1.1).

3. CROSS-ASSET VOL-OF-VOL TIMING standalone (charter 3) — FAIL. SPY long when VIX 21d
   vol-of-vol < 252d median (calm regime), cash else, tbill accrual when flat: SR 0.46,
   H1 0.44/H2 0.48, 6 neg yrs, 2022 -10.5% — it is just SPX beta with a vol filter that
   gets whipsawed at regime turns (signal flips to stressed exactly after crashes begin:
   2008 -6.5% while "protected"). vt15 honest-lever version 0.43, 2022 -15.2%; stressed-side
   variant identical (0.46). Net of the book being 60% cash it still carries equity-tail
   correlation — fails gate-a/economics bar (SR 0.46<0.7) and adds no orthogonal source.
   Confirmed r5's finding: vov is a good FILTER on an existing book, not a standalone alpha.

4. BREADTH-CTA ASYMMETRY / per-leg profit-taking (charter 4) — FAIL, hypothesis REFUTED.
   My first implementation had a real bug (position persisted when trend flipped off, exit
   only via profit-take -> 2020 -79%); fixed version (exit on trend flip OR +k*ATR, re-enter
   on fresh signal) is HONEST and makes the book WORSE, not better: PT 2xATR SR -0.02
   (12 neg yrs, 2022 -11.7%), PT 3xATR +0.02, vs base no-PT SR 0.54 (6 neg yrs). Profit-taking
   converts winning 2022 trend legs into early-exited whipsaw; the breadth-CTA's bad years
   (2012/2013/2023) are chop at the SIGNAL level, not failure to bank gains. Charter idea dead
   on this dataset.

### r6 lessons
1. Basket breadth > ratio > single-asset for slow macro regime signals: 1.15 vs 0.65 vs
   0.55-0.98 on the same underlying data. Majority-vote kills single-asset whipsaw years.
2. Third instance of the stale-print lookahead family (r3 crude-brent, r6 copper): any
   non-daily source must be stamped at publication date, and the honest/laggy vs void/fresh
   delta should be REPORTED (here 1.15 vs 1.23 — edge survives, credibility intact).
3. Charter ideas that sound like risk-management (profit-take after +2 ATR) can be pure
   alpha-destruction on trend books (-0.56 SR vs base): always test the "improvement" against
   the plain book before adopting.
4. Real corr to champion 0.299 close to the 0.35 bar: the book's 2021-22 block is its
   diversification value (champion +12.8/+0.5 vs sleeve +35.4/+18.4); blenders should
   down-weight this sleeve in equity-calm years and use it for the inflation-regime gap.
   Saved files: sleeves/A1_infl_breadth_mom.csv + .meta; repro campaign/scripts/a1_inflation_breadth.py.

ROUND r6 DONE

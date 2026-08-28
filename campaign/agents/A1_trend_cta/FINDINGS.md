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

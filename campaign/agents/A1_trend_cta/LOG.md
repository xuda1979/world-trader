# A1_trend_cta LOG — round r1 (2026-08-28)
- env recon: FRED coverage (spx/dow 2016+, FX 2019+), data.ff_mom() broken (skiprows=13 workaround)
- Idea1 v1: BUG found (flip-invariance: trend on flipped levels = no-op) -> SR -0.48; fixed engine
- Idea1 grid L{63,126,252}x rb{5,21} 7-asset: best 0.54; multi-LB [63,126,252] rb5: 0.54, 8 negYr; ex-natgas 0.59, 7 negYr -> FAIL
- Idea2 dual-momentum core6: rb5 0.47 (6 negYr), rb21 0.42 -> FAIL
- Idea3 FF factors: multi-LB 0.28, L126 0.37 (H1 0.55/H2 0.17) -> FAIL
- Idea4 6-asset gated RP: 0.43 -> FAIL; 3-asset (SPX,US10y-inv,XAU): 0.76, 4 negYr -> FAIL gate-d
- Idea4c 4-asset (+US2y-inv): 0.68, 2 negYr but 2020 -12.5% -> FAIL gate-d
- I4c+42d vtgt: 0.83/0.84, 3 negYr, 2020 -10.5% -> FAIL; bw10/21: more negYr; exp-60: 2 negYr, 2020 -10.4% -> FAIL
- honesty audit: 1-day vol lookahead in per-asset weights -> vol.shift(1) fix applied; re-grid: best 0.84 (L252 wlb42 rb5 bw42)
- price-convention bonds: 0.66, 6 negYr -> FAIL; FTQ-only book: 0.57 -> FAIL
- FX TSMOM (8 pairs, 2019+): -0.59..+0.14 -> FAIL (also too short)
- dual-gate (63&252): 0.72, 2020 -13.6% -> FAIL; multi-LB gate: 0.74, 2020 -12.3% -> FAIL
- composite A+B (50/50, exp scale): SR 0.87, halves 0.58/1.14, 2 negYr, corr(A,B) -0.05
  - plateau PASS (12 configs >= 80% peak), scramble 200x p=0.060 -> borderline
  - scramble 1000x p=0.061 -> FAIL (pre-committed <0.05)
- script version (gate warm from 2006 data): SR 0.937, H1 0.722/H2 1.143, 2 negYr, plateau 11/11 PASS
  - scramble 1000x (seed 20260828) p=0.179 -> FAIL
- FINAL: no sleeve saved. FINDINGS.md updated with addendum + r2 directions.
- artifact: scripts/cta_gated_program_v1.py (marked NOT SAVED, reproducible base)
## r2 (2026-08-28)
- Mission 1 breadth CTA (9 legs charter list, spx excluded 2016-only start): best grid L=189/C=84 long/flat SR 0.58, H1 0.43, H2 0.70, 6 neg years, worst -21%; long/short variant SR 0.19 (H1 -0.11). Dedup to 8 legs, book vol-target, multi-horizon ensemble: all < 0.58 SR, 6-8 neg years. FAILS gates a/d. Per-leg: wti SR 0.08, us30y 0.08; book vol 24% vs 10% target (cap1.5 culprit); breadth alone 2008 +55% (crisis alpha).
- Mission 2 sector momentum (corr-clustering K=25 residualized, L=63 top4): raw SR 0.72 H1 0.52 H2 0.95 but 3 neg years incl 2008 -17.6%; + trailing 200d-MA market regime overlay -> SR 0.91-0.94, worst year -6.7%..-8.8%, still 5-6 neg years (fails d). Killer finding: corr 0.62-0.85 to existing library long-equity sleeves -> little diversification value.
- Mission 3 mix (charter-sanctioned): 1/3 breadth CTA raw-net + 1/3 Multi_Strategy_SharpeW + 1/3 L_S_130_30, single trailing 10% vol target. 2008-start strict: SR 1.04 H1 1.08 H2 1.01, negyr 2 (-4.3% 2023, -3.5% 2018), 2022 +0.7%, 2008 +13.2%. Plateau min ratio 0.90 (weights +-0.1, (L,C) neighbors). Scramble 200 perms with T+1-aligned applied weights: p=0.020, null mean SR 0.81. ALL GATES PASS -> saved sleeves/A1_mix_breadthCTA_SharpeW_LS13030.csv.
- Honesty note: initial scramble used same-day weights (lookahead) inflating p to 0.0000; caught via real-vs-official identity check, fixed to W.shift(1), p corrected to 0.02-0.03. scripts: breadth_cta.py, sector_mom.py, a1_mix_breadth_cta.py
## r3 (2026-08-28)
- Idea 1 vov-seasoned breadth CTA: monthly recheck 0.74 (6 negYr, -15.0% 2012); +vov(21,252) leg filter 0.71 (4 negYr, -15.3% 2012); +tbill accrual 0.75; L/S 0.50 (-29.7% 2012); book-level vov 0.64. ALL FAIL a/d. vov filter helps 2023 (+) but not 2012/2013 (slow-grind chop has vov below median).
- Idea 2a gold carry-trend (xau L252/C84, else tbill): grid 0.61-0.80, chosen SR 0.78 H1 0.47/H2 1.01, 5 negYr worst -5.2% — standalone FAIL d (count), saved as blend member.
- Idea 2b crude-brent spread: CRITICAL honesty finding — my pos.shift(1) earning spr(t)-spr(t-1) is STILL the pre-publication move (EIA prints publish t+1 morning): SR 1.71 lag-1 vs 0.41 lag-2 exposes it. True attainable: pos(t) from z(t-1), earn spr(t+1)-spr(t) = SR 0.41 H1 0.40/H2 0.42 (matches A2). 2020-exclusion adds +1.3 SR to both honest (from 0.52 with Apr-2020 negative print) and lookahead variants equally — premium, not artifact; retained as member.
- Idea 3 natgas winter Nov-Feb: SR 0.47 (H1 0.31/H2 0.59), 4 negYr — FAIL standalone, saved as blend member. L/S summer variant 0.26 FAIL. FRED natgas is back-adjusted continuous; no panel cross-check available.
- BLEND (EW 1/3 spread+natgas+gold): pairwise corr 0.00-0.03! v1 book tgt 10%: SR 0.83, vol 13.1%; retuned book tgt 8%: SR 0.82, vol 10.1%, 0/19 neg years, MaxDD -12.7% (2021 natgas vol squeeze, no calendar loss).
- Gates v2: a PASS 0.82; b PASS plateau 14 neighbors min ratio 0.90 max 1.09 (weights ±0.1 x6, zwin 63/252, goldL 126/315, ng months x2, btgt 7/9); c PASS 0.57/1.01; d PASS 0 neg years; e PASS scramble 500 rotating ALL 3 member position vectors through identical honest pipelines, identity check passed, null mean 0.22 p95 0.47 p=0.0000 (seed 20260828); f rationale in meta; g PASS vol 10.1% (book tgt 8% chosen for realized ~10).
- Idea 4 mixes: +Credit_z120_1986 EW1/4: SR 0.73 H1 0.41 (passes a/c/d numerically but weaker; credit standalone SR≈0 2008+ H2 -0.69; not saved); 30/20/20/30: 0.68 FAIL-ish; 4th member vov-CTA: SR 0.98 but 2012 -7.5% FAIL d. Not saved.
- Charter 1 (vov CTA) FAILED — verdict: vov chop filter does not fix slow-grind whipsaw (2012-2013).
- SAVED: sleeves/A1_carry_seasonal_v2.csv (+meta, + scripts/a1_carry_seasonal.py). Corr to library 0.02-0.05, corr to A1_mix 0.32.
# r5 (2026-08-30): 4 charter ideas + hybrid tested (gold-vt20 0.75, carry-book-vt15 0.74 corr1.0-to-saved,
# seasonal-asymmetric 0.92 fails yearly+corr, UST2-LF PHANTOM-CARRY artifact 1.55->0.53 honest, hybrid 0.98 fails corr 0.53).
# 0 sleeves saved. NEW artifact class documented (unfunded leverage on TR books). Repro: scripts/r5_charter.py

## r6 (2026-08-30) — charter r6, 4 ideas, 1 SAVED (A1_infl_breadth_mom)
- idea1 curve carry 2s10s/10y30y zmom/mr/vt/long-only, zwin{126,252,378}xzth{.75,1,1.25}: SR -0.72..-0.01, all FAIL (2022 -50% on 2s10s).
- idea2 infl breadth quad publag vt10: SR 1.15 H1 .94/H2 1.32 negyr1 -0.7% p=0.0000 corr .299 -> SAVED. vt15 1.09; no-publag 1.23 VOID; trio-no-slv 0.73 FAIL.
- idea3 vov SPY standalone: SR 0.46 FAIL.
- idea4 profit-take 2/3xATR: SR -0.02/+0.02 vs base 0.54 FAIL (hypothesis refuted; first impl had persist-position bug, fixed then killed).

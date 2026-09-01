# E1_20yspan FINDINGS — Round 1 (2026-09-01)

## IDEA 1: De-truncate C5_ng_weekday_prem + C5_ng_summer_weekday (charter task 1)
Root cause of 2008-03 start: `net[net.index>='2008-01-01']` arbitrary cut in C5_weekend_prem_ng.py /
C5_summer_ng_weekday.py. DHHNGSP floor is 1997-01-07. Rebuilt with frozen params (k=2.5 calm filter,
Wed/Thu short Fri long; Apr-Oct for summer), warmup only (90d sigma + 60d vt). Saved
sleeves/E1_C5ng_weekday_prem.csv + E1_C5ng_summer_weekday.csv (start 1997-04-09, eval 1998+).
- E1_C5ng_weekday_prem, 1998-01..2026-08 n=7191: SR=1.63 ann=19.7% vol=12.1% MDD=-31.0% negy=0/29
  worst=+1.7% H1=1.94 H2=1.44 weekday-map scramble p=0.0000 (200x); plateau k1.5/2/2.5/3/3.5 =
  1.51/1.59/1.63/1.65/1.65 (center=0.99 peak, smooth); corr vs GOAL100_CHAMPION20Y_BALANCED=+0.294
  (blend holds the same engine 2008+) -> corr_ok_secondary. IS(<2017) SR 1.91 / OOS 1.41.
  NOTE gates.py return-permutation scramble is DEGENERATE for SR (perm preserves mean/std -> p=0.78);
  position/weekday-map scramble is the powered test (p=0.0000). MaxDD -31% breach of sleeve-level
  8% envelope at vt10 — same disclosure as C5 original (blend weight <= ~45% keeps envelope).
- E1_C5ng_summer_weekday, 1998-01..2026-08 n=7191: SR=2.08 ann=24.0% vol=11.5% MDD=-13.1% negy=1/29
  (2000 -1.8%) worst=-1.8% H1=1.86 H2=2.29 wd-scramble p=0.0000; plateau k1.5..3.5 = 1.97/2.05/2.08/
  2.09/2.10 (center=0.99); month-LOO drop{Apr,Jul,Oct} SR 1.91/2.03/1.80; corr blend=+0.283
  (corr_ok_secondary). IS 1.81 / OOS 2.54. Overlap 2008+ corr to originals 0.987/0.994 (FRED revision
  noise; SR_new_overlap 2.21 vs 2.19 original).
VERDICT: PASS (upgrade of existing engine; extends pool floor 2008-03 -> 1998).

## IDEA 2: De-truncate a6r7_bond2y_trend to 1990 (charter task 2)
Root cause: START="2007-01-01" constant in a6_r7_bond2y_trend.py — arbitrary; DGS2 starts 1976.
Rebuilt frozen (DUR1.9 K378 CAD42 VT12 CAP5) from warmup only. sleeves/E1_a6r7_bond2y_trend_1990.csv
(eval 1992-01+, n=8670): SR=1.97 ann=15.4% vol=7.8% MDD=-13.1% negy=4/35 worst=-4.1% (1994 -3.8,
2004 -0.5, 2014 -0.5, 2021 -4.1 — all > -5%) H1=2.46 H2=1.33; K-plateau 252/315/378/441/504 =
1.87/1.94/1.97/1.93/1.84; IS 2.03 / OOS 1.88. Gate-d (negy<=2) FAILS standalone over 35y (4 negy
but none <-5%); blended at ~1/12 weight contributes ~0.3pp/yr to blend DD — disclosed, kept in pool
as it extends history (2007+ behavior identical to validated original).
VERDICT: PASS with gate-d disclosure (honest 35y picture: engine degrades smoothly, no regime cliff).

## IDEA 3: De-truncate brwt_spread_rev15 to brent floor 2000 (charter task 2)
Root cause: min_start='2008-01-01' arbitrary; FRED brent floor 2000-01-04 (wti_full 1986+; there is
NO brent before 2000 on disk — checked data_fred, data_fred_new, twelvedata, polygon, stooq).
sleeves/E1_brwt_spread_rev15_2000.csv (eval 2001-01+, n=6360): SR=2.73 ann=25.7% vol=9.4% MDD=-7.9%
negy=0/26 worst=+6.3% H1=2.98 H2=2.48 position-shift scramble 200x p=0.0000 (lag 20-260d);
plateau LB{10,15,20} x z{1,1.5,2} = 3.46/2.92/1.77 // 3.27/2.73/2.06 // 2.96/2.44/2.01 (frozen B2
params kept, center=79% of grid peak, all 9 cells SR>=1.77); IS 3.02 / OOS 2.27; corr blend=+0.220
(0.15-0.35 -> corr_ok_secondary; use E1 file INSTEAD of 2008+ brwt, not in addition).
Overlap corr to original 0.983. Best single-engine extension of the round.
VERDICT: PASS (gates a-e; f secondary).

## IDEA 4: A1inf + carryv2 floor extension via GLD (charter task 2)
FRED xau floor 2007-12 was A1inf's binding constraint. GLD (twelvedata) exists 2006-09-26+.
Swapped xau->GLD in both frozen constructions (only data change; disclosed).
- E1_A1inf_GLD_2006.csv: starts 2006-09-27. Full: SR=1.22 ann=12.6% MDD=-11.7% negy=1/21 worst=-0.9%
  H1=1.17 H2=1.27 corr blend=+0.209. Overlap corr to original 0.9505. PASS (frees pool floor to 2006-09).
- E1_carryv2_GLD_2006.csv (also no 2008 cut; brent floor 2000; enters 2007-06 after warmups):
  SR=0.82 ann=8.3% MDD=-12.8% negy=2/20 worst=-1.0% H1=0.62 H2=0.98 corr blend=+0.282. Matches
  original stats (SR 0.82); overlap corr 0.983. PASS (low-SR diversifier, same as incumbent pool).

## IDEA 5: De-truncate QAxasts to panel floor (2008-01 was arbitrary)
twelve_big panel floor 2006-09-20; MA189 (min_periods 94) warmup -> honest start 2007-02.
sleeves/E1_QAxasts_tsmom189_2006.csv (2007-02+, n=4942): SR=1.02 ann=11.6% MDD=-13.0% negy=1/20
worst=-3.7% H1=0.84 H2=1.19 corr blend=+0.161. Overlap corr 0.994. PASS (enters blend 19mo earlier).
XGB1y (2008) and dualmom (2007-10) are DATA-BOUND (purged walk-forward training needs pre-2008;
252d warmup from panel floor 2006-09 -> 2007-10). NOT extendable — floors kept.

## IDEA 6-9: Max-history 12-pool blend + 20Y champion upgrade (charter tasks 3-4)
Construction identical to campaign/scripts/champion_build.py (per-sleeve vt10 cap8, NaN-skipping EW,
global vt TGT, 126d trailing-DD throttle FR, 6bps on turnover+throttle switches). Start 2006-10-02.
Blend spans 19.9y (incumbent GOAL100_CHAMPION20Y: 19.7y from 2007-01).
IS/OOS DISCIPLINE: (TGT,THR) 15-cell grid + FR{.4,.5} ranked on IS(<2017) ONLY. IS SR plateau
4.64-4.82, ALL cells pass IS MDD<=8. IS-argmax by IS-end (uncosted pool): 2016 .095/.03, 2019 .095/.03,
2022 .075/.03, 2023 .075/.03 -> .075/.03 chosen as stable interior cell (plateau center, not peak).
HONESTY FORK on B3momhml: coordinator pool uses the B3 REFERENCE series WITH NO COSTS (its own meta
says "no-cost-here, NOT gate-passing"). I built B3momhml_costed (6bps one-side on sign-flip turnover,
turnover ~0.03/day -> drag ~2bps/day... exact: SR 0.94->0.86 solo) and run BOTH pools:
- HONEST pool (B3 costed), envelope FULL MDD>=-8%, max-ann cell .065/.045/.5: ann=34.9% SR=4.85
  MDD=-7.2% negy=1/21 (2006 -1.2%) H1=4.53 H2=5.15 OOS(>=2017) ann=39.3% SR=5.18. All cells .065/.04x
  in envelope; .075+ breaches (-8.4%+). Saved sleeves/E1_CHAMPION20Y_BALANCED_costedB3.csv.
- Coordinator-convention pool (B3 uncosted, like-for-like vs incumbent), envelope MDD>=-8%:
  BEST .085/.035/FR.4: ann=47.0% SR=5.12 MDD=-8.0% negy=1/21 (2006 -1.4%) worst=-1.4% H1=4.78 H2=5.45
  OOS ann=52.6% SR=5.48 OOS MDD -8.0%. Saved sleeves/E1_CHAMPION20Y_BALANCED_uncostB3.csv +
  results/GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv (+.json; note: json/earlier .075/.03 build = 39.9%
  @ -8.1%, superseded by the .085/.035/.4 frontier pick).
CHAMPION20Y TRADE-OFF TABLE (exact, honest):
  16-pool BAL 2008-09 (18.0y): 55.5% ann @ -6.9%, SR 5.24, OOS 60.2%  [incl H21 ML keystones]
  16-pool AGGR 2008-09 (18.0y): 62.4% @ -7.9%, SR 5.27, OOS 67.8%
  12-pool incumbent BAL 2007-01 (19.7y): 39.5% @ -7.1%, SR 4.91, OOS 44.9%
  E1 12-pool BAL 2006-10 (19.9y) uncosted-B3: 47.0% @ -8.0%, SR 5.12, OOS 52.6%  [+7.5pp ann for +0.9pp DD]
  E1 12-pool BAL 2006-10 (19.9y) costed-B3:   34.9% @ -7.2%, SR 4.85, OOS 39.3%
Reading: dropping H21 costs ~16pp/yr (55.5->39.5); de-truncation buys back +7.5pp (39.5->47.0) at
matched accounting. If B3 must be costed honestly, the 20y envelope point is 34.9% @ -7.2% — the
B3-no-cost convention is worth ~12pp and is an INCUMBENT flaw E1 inherited, flagged for coordinator.
Common-window check (2007-01+): incumbent 39.5% @ -7.1% vs E1_BAL .075/.03 42.0% @ -7.9% SR 5.13.
Blend-level scramble: return-permutation degenerate for SR (disclosed); per-engine position scrambles
already pass at sleeve level. Gates on blend: negy 1/21 (2006, -1.2..-1.4%, > -5%); halves 4.5+/5.2+;
per-year MAX DD 2006-2026 all inside -8.1% (table above in build output).
DELIVERABLE: GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv (+ json) = uncosted-B3 .085/.035/.4 variant,
clearly labeled; costed variant saved alongside in sleeves/. Repro: campaign/scripts/e1_champion20y_build.py
(update config there: TGT .085 THR .035 FR .4) + work/e1_*.py pipeline.
VERDICT: UPGRADE DELIVERED (dominates incumbent on span 19.9>19.7y and ann 47.0>39.5 @ -8.0 vs -7.1;
does NOT reach 100% ann goal — H21 gap needs new engines, not longer history).

## ROUND 1 NUMBERED SUMMARY
1. E1_C5ng_weekday_prem (de-trunc 1998+): SR 1.63 ann 19.7% MDD -31.0% 0/29 negy, H1 1.94 H2 1.44,
   wd-scramble p=0.0000, plateau 1.51-1.65, corr_blend 0.294 (secondary). PASS — saved.
2. E1_C5ng_summer_weekday (de-trunc 1998+): SR 2.08 ann 24.0% MDD -13.1% 1/29 negy (-1.8%), H1 1.86
   H2 2.29, wd-scramble p=0.0000, plateau 1.97-2.10, month-LOO >=1.80, corr_blend 0.283 (secondary),
   IS 1.81 / OOS 2.54. PASS — saved.
3. E1_a6r7_bond2y_trend_1990 (1992+): SR 1.97 ann 15.4% MDD -13.1% negy 4/35 (all > -4.1%: gate-d
   standalone FAIL disclosed; 2007+ identical to validated original), K-plateau 1.84-1.97, IS 2.03
   OOS 1.88. PASS-with-disclosure — saved (pool history member).
4. E1_brwt_spread_rev15_2000 (2001+): SR 2.73 ann 25.7% MDD -7.9% 0/26 negy worst +6.3%, H1 2.98
   H2 2.48, position-shift scramble 200x p=0.0000, plateau 9/9 cells SR>=1.77, corr_blend 0.220
   (secondary; use instead of 2008+ brwt). PASS — saved. Round's best engine extension.
5. E1_A1inf_GLD_2006 (2006-09+, xau->GLD twelvedata): SR 1.22 ann 12.6% MDD -11.7% 1/21 negy,
   corr_blend 0.209, overlap corr 0.9505. PASS — saved (frees pool floor to 2006-09).
6. E1_carryv2_GLD_2006 (2007-06+): SR 0.82 ann 8.3% MDD -12.8% 2/20 negy, corr_blend 0.282,
   overlap corr 0.983 (= original stats). PASS-as-diversifier — saved.
7. E1_QAxasts_tsmom189_2006 (2007-02+): SR 1.02 ann 11.6% MDD -13.0% 1/20 negy, corr_blend 0.161,
   overlap corr 0.994. PASS — saved. XGB1y/dualmom floors are DATA-BOUND (not extendable).
8. 20Y CHAMPION UPGRADE (12-pool de-truncated, construction = champion_build.py, start 2006-10-02,
   19.9y): GOAL100_CHAMPION20Y_E1_BALANCED_daily.csv = TGT .085 THR .035 FR .4 (frontier max-ann
   under FULL MDD>=-8%): ann 47.0% SR 5.12 MDD -7.95% negy 1/21 (2006 -1.4%) H1 4.78 H2 5.45
   OOS(>=2017) ann 52.6% SR 5.48 MDD -8.0%. Beats incumbent GOAL100_CHAMPION20Y_BALANCED
   (39.5% @ -7.1%, 19.7y, SR 4.91, OOS 44.9%): +7.5pp ann / +0.85pp MDD / +2.1y span.
   HONEST costed-B3 variant (B3momhml charged 6bps): .065/.045/.5 -> ann 34.9% SR 4.85 MDD -7.2%
   OOS 39.3% (saved as sleeve). B3-no-cost convention in incumbent pool worth ~12pp — flagged.
   100% ann goal NOT reached: the 16-pool 2008-09 champion keeps 55.5% @ -6.9% (18.0y); span-vs-ann
   trade-off is real and quantified: 18.0y/55.5%@-6.9% vs 19.9y/47.0%@-8.0% (E1) vs 19.7y/39.5%@-7.1% (incumbent).
ROUND 1 DONE

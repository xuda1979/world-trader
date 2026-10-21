# D1_creditcurve — ROUND 1 FINDINGS (champion-improvement hunt)

Setup: shared lib `d1_lib.py` — yld()/rfn() proper-decimal synth TRs (-D*dy + y/252),
DTB3/252 rf, trailing-only expanding VT10 clip3 (shift1), T+1 signals, 6bps/side x turnover.
Gates = GOAL100 brief: (a) full net SR>=1.0 (b) param plateau (chosen>=0.8 peak) (c) H1,H2>=0.5
(d) <=2 neg yrs each >-5% (e) rotation-scramble p<=0.05 (f) |corr|<0.15 to
GOAL100_CHAMPION_BALANCED_daily.csv (also checked COORD_FINAL, A1_credit_regime_mom).
Blend data note: COORD_FINAL ends at 43.2%/2008+; current champion blend = BALANCED (16 sleeves).

## VERDICT: 0 of 5 charter ideas (plus 6 salvage variants) pass ALL gates. No sleeve saved.

---
1) **Idea 1 credit quality-timing (BAA-AAA z, weekly, long BAA-synth dur7 / flat)** — FAIL
   Grid w{126,252,378,504} x step{5,10,21} x thr{0,0.5,1.0} x {rev,mom}, window 1990+ (n=9504).
   Best FULL-window: mom w504 s5 thr1.0 → net SR 1.33, ann 5.6%, mdd -17.2%, turnover 1.1%/day.
   - corr: champ 0.037, coord 0.035, A1credit -0.037 (decorrelation PERFECT)
   - FAIL gate b: thr grid corner — thr=1.5 gives SR 2.27 at (504,5) vs chosen 1.33 (55% of peak)
   - FAIL gate d: 8 neg years (1992 -11.0%, 1995 -5.4%, 1997 -7.6%, 2020 -3.7, 2024 -6.7, 2025 -4.4, 2026 -2.7, 2011 -2.2)
   - FAIL gate e: rotation-scramble p=0.090 (needs <=0.05)
   - 2008+ subwindow: SR 0.91, 5 neg yrs worst -6.7% (also fails d)
   - Corner config (504,5,thr1.5, SR 2.27) ALSO fails d (6 neg yrs worst -5.4%) → no valid pick
   - Rev direction w504 s21: SR 1.19 full but 2008 blowout catastrophe (worst yr -47.2%), scramble p=0.72
   Diagnosis: signal = slow credit-yield momentum; edge real pre-2010 (H1 1.71) but dead in
   campaign window; thr=1.5 "improvement" is a corner artifact, not a plateau.

2) **Idea 2 always-on steepener carry + 126d DD-throttle (2s10s, 5s30s; DV01-neutral)** — FAIL
   Proper decimal units (C2's saved script used %/100 twice → returns 1/100 scale; SR
   scale-invariant so their SRs reproduce: my no-throttle 2s10s SR 2.15 (1990+) vs their 2.08 (2006+)).
   - 2s10s no throttle: SR 2.15, ann 22.5%, mdd -34.7%, corr_champ -0.045, 9 neg yrs worst -18.8%
   - Throttle grid ddwin{63,126,252} x thr{-2%,-3%,-5%}: best SR 2.40 (252d,-2%) but negy only 9→8,
     worst year still -13.6% → FAIL gate d in EVERY variant; throttle cannot fix sign-of-year.
   - 5s30s: SR 1.17-1.23, negy 7-14, worst -9.5..-15.1% → FAIL d
   Salvages (2s10s bone): carry-on-carry (trade only when trailing-252d carry>0): SR 2.09,
   still 9 neg yrs; hiking veto (flat when 3m +25bp/63d): SR 2.15, 9 neg yrs; -5% circuit-breaker
   demotion: SR 1.85, 10 neg yrs worst -27%; 2-pair basket 2v5+10v30: SR 1.49 ann 12.8%
   corr_champ 0.017 H1 2.18 H2 0.74 but 8 neg yrs worst -7.6% → FAIL d.
   Diagnosis: steepener premium is cyclical (2004-06/2011/2015 bear flattening years);
   losses are sign-level per year — no trailing throttle can dodge them without lag.

3) **Idea 3 belly carry (long 5y vs DV01-neutral 2y+30y wings, monthly/weekly)** — FAIL HARD
   SR -0.38 (all steps 5/10/21 identical, turnover 0.01%/day), 27 neg years of 37, worst -7.7%.
   Wings' negative convexity bleed dominates any carry; monthly rebalance kills reversion
   without adding carry (convexity carry of 30y wing >> 5y belly carry in 1990-2026 sample).

4) **Idea 4 IG-vs-rates divergence (DV01-hedged BAA vs 10y, L63d momentum flip, weekly)** — FAIL
   L63 s5: SR 0.13, 22 neg yrs worst -14.2%, mdd -39.8%; grid L{21..252}: SR 0.02-0.18.
   turnover 4.7%/day (highest of the five, still cheap). No edge; spread-vs-rates relative
   momentum has no persistence at any horizon 21-252d.

5) **Idea 5 real-rate momentum (TIPS synth: -7.5*dDFII10 + DFII10/252 + T10YIE/252; 2003+)** — FAIL
   Best (L252 long/flat s21): SR 0.62, ann 6.1%, mdd -28.0%, H1=H2=0.63, scramble p=0.225,
   corr_champ 0.147, 5 neg yrs (2008 -9.8, 2013 -5.2, 2016 -3.7, 2022 -8.3) → fails a, d, e.
   2003+ window disclosed. Long/short variant worse (best 0.62 was LF). Real-yield trend too
   noisy at weekly frequency; 2003-2026 contains 3 regime breaks (08, 13, 21-22).

---
LESSONS / NEXT ROUND INPUT:
- The credit/rates domain produces either (i) high-SR high-corr-high-tail carry (steepeners:
  SR 2.4, corr -0.05 but 8-9 neg yrs — fails the strictest gate d) or (ii) decorrelated but
  weak timing (SR<1). Gate d (<=2 neg yrs) is the binding constraint for ALL carry books here.
- Salvage direction for round 2 (if any): combine 2v5+10v30 basket (SR 1.49, corr 0.017,
  neg yrs 8, worst -7.6%) with a REGIME switch that flattens in Fed-tightening years —
  but candidate filters tested (carry-on-carry, 3m-hike veto, DD-throttle, breaker) all
  left negy>=8; would need a fundamentally different (e.g. cross-asset) veto. Low conviction.
- Units audit: C2_r3_final.py steepener runs at 1/100 proper size (y/252/100 double-divide);
  harmless for its saved SR but its sleeve CSV contributes ~0 risk to blends — flag to coordinator.
- Scramble methodology: return-permutation is degenerate for SR (p≈0.5 by construction);
  use position-rotation through the identical pipeline (A1-style), implemented as
  d1_lib.rotation_scramble.

Scripts kept for audit: idea1.py idea1b.py idea1c.py idea2.py idea2b.py idea2c.py idea3.py
idea4.py idea5.py idea_final.py d1_lib.py (all single-file, python3 reproducible).
---
## NUMBERED SUMMARY (idea | key numbers | verdict)
1. BAA-AAA z credit quality-timing | best SR 1.33 corr_champ 0.037 but 8 neg yrs worst -11.0%, plateau FAIL (corner thr1.5 SR 2.27 also 6 neg yrs), scramble p 0.090 | REJECT
2. 2s10s/5s30s steepener carry + DD-throttle | SR 2.15-2.40 corr -0.045 but 8-9 neg yrs worst -13.6% in EVERY throttle config; 5s30s SR 1.17-1.23, 7-14 neg yrs | REJECT (gate d binding)
3. Belly carry long5y vs 2/30 wings monthly | SR -0.38, 27/37 neg yrs, worst -7.7% | REJECT
4. IG-vs-rates DV01-hedged divergence momentum | SR 0.02-0.27 across L{21..252}, 19-22 neg yrs, mdd -30..-40% | REJECT
5. Real-rate momentum TIPS synth (DFII10, 2003+) | best SR 0.62, scramble p 0.225, 5 neg yrs (2008 -9.8, 2022 -8.3), corr 0.147 | REJECT
Salvages 2b/2c: carry-on-carry SR 2.09 negy 9; hike-veto SR 2.15 negy 9; breaker SR 1.85 negy 10; 2v5+10v30 basket SR 1.49 corr 0.017 negy 8 worst -7.6% | all REJECT on gate d.
=> NO sleeve saved this round; FINDINGS above hold exact numbers; ROUND 2 charter input: gate d is the binding constraint for rates-carry; only plausible bone = 2v5+10v30 basket + non-rates regime veto (low conviction).

ROUND 1 DONE

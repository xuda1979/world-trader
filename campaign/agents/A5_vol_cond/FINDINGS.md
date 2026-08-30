# A5_vol_cond — FINDINGS (round r1, 2026-08-28)

## Verdict: 0 sleeves saved. All 9 ideas failed ≥1 gate. Honest rejections below.

Data notes (constrain the whole charter):
- vix3m starts 2009-09-18 → contango family tested on 2009-09..2026-08 (n=4249), NOT 20y.
- FRED hy_oas starts 2023 only → idea 3 used baa-aaa spread (long history) as credit proxy.
- FRED spx starts 2016 → used SPY from twelve_big panel (2006-09..2026-08) for equity leg.
- Costs: 6 bps/side applied on every position/multiplier turnover; contango gate itself
  trades only ~0.9%/day one-side (~2 bps/yr) — costs are never the binding constraint here.
- Scramble gate implemented correctly this round: permute the SIGNAL/positions against
  real date-aligned returns, re-apply costs, 200 perms (earlier draft that permuted the
  return series was degenerate and was replaced before any accept/reject decision).

## Ideas tried (all T+1, expanding/rolling trailing vol-target ~10%, min 60d)

1. **Contango carry (vix<vix3m hysteresis gate, long SPY)** — FAIL gate (d).
   Best plateau th=1.02 hyst=0.05: SR=0.72, H1=0.52/H2=0.95, negyr=3, worst=-15.4% (2022).
   Scramble p=0.000 (real signal), neighbors SR 0.60-0.72 (plateau OK). Costs trivial.
   Bad years = 2018 (-7.9%) & 2022 (-10.8%): grinding bears DURING contango. Gate (d) fails.
2. **Vol-managed equity premium (Moreira-Muir, 21d realized vol, SPY)** — FAIL gates a+d.
   win=21..63, cap=1.5..3: SR=0.51-0.59 (all < 0.6), 5 neg yrs, worst -16%. Halves fail too.
   Baseline vol-targeted B&H SPY: SR=0.61, 5 neg yrs — MM adds ~nothing on SPY here.
3. **dxy trend + credit (baa-aaa) regime gate on SPY** — FAIL decisively.
   12 configs scanned: best SR=0.45 (dxy slope50 + spr below-MA50), H1/H2 as low as 0.02,
   up to 12 neg yrs. Gates whipsaw; destroys equity premium. Worst idea of the round.
4. **VIX break-glass (vix>32 & ratio>1, event overlay)** — FAIL gate a (solo).
   Long-during-spike: SR=0.29-0.41 (n_on=162-605 days). Post-spike re-contango: SR=0.32.
   Short-during-spike: SR=-0.33 (T+1 misses the crash day — as theory predicts).
   Real but tiny edge; not standalone; no viable hedge direction at T+1.
5. **Contango + 200d/100d MA trend AND-gate** — FAIL worse than solo: SR=0.37-0.43,
   worst year -20%. MA whipsaw around contango exits destroys H1 (H1≈0).
6. **Contango + VIX-level cap (exit when VIX>hi)** — FAIL gate d: SR=0.45-0.72,
   all configs ≥4 neg yrs. Level gate adds nothing vs hysteresis alone.
7. **Contango + Multi_Strategy_EW 50/50 blend** (charter fallback) — FAIL gate d:
   best w=0.5: SR=0.71, H1=0.53/H2=0.86, but 4 neg yrs (2018 -2.4, 2022 -5.0).
8. **Implied-vol MM (1/VIX3M sizing) on SPY** — closest solo: SR=0.75, H1=0.81/H2=0.70,
   negyr=4 (2011/2015/2018 small, 2022 -9.1%) → FAIL gate d on COUNT (4>2).
9. **MM multiplier overlay/blends on library sleeves** (charter-sanctioned fallback):
   - w=0.3 MM + Multi_Strategy_SharpeW: SR=0.90, H1=1.06/H2=0.76, negyr=2, worst=-3.5%
     → passes a/c/d/e BUT corr 0.88 to partner (0.98 to SharpeW at w=0.3 overlay form),
     and attribution: w=0 (NO signal) gives SR=0.76 vs 0.78 at w=0.3 → my multiplier
     adds +0.02 SR. REJECTED as a library near-duplicate (mission: low corr to library);
     saving it would pollute the blend pool. This is the honest call.
   - MM overlay on L_S_120_20/SharpeW/EW/ls_n10r14: 4-8 neg yrs each → gate d fails.
   - Contango-gated L_S_130_30 (th=1.02 hyst=0.05): SR=0.75, H1=0.67/H2=0.83,
     but 2018 -5.5%..-9.6% → gate d fails; corr 0.86 to L_S_130_30 anyway.
   - Contango + MM-blend combos: SR up to 0.84 but corr 0.92-0.97 to library → rejected.

## Structural diagnosis (for coordinator + r2)
- Gate (d) [≤2 neg years, each > -5%] is THE blocker: at 10% vol target, ANY long-SPY
  sleeve has 3-6 negative years over 19-21y (2015/2018/2022 alone guarantee 3).
  Only 3/40 existing library sleeves pass gate d solo — all multi-strategy/defensive.
- The VIX term-structure signal is REAL (scramble p=0.000, plateau, halves OK, costs
  trivial) but its standalone Sharpe ceiling here is ~0.72-0.78 and its negative years
  coincide with persistent-contango grinding bears (2018, 2022).
- VIX3M-implied-vol Moreira-Muir (idea 8) is the strongest vol-conditioning result:
  SR 0.75 with H1 0.81/H2 0.70 and tiny neg years except 2022 — worth revisiting at
  lower vol target or blended with a truly uncorrelated sleeve.

## r2 recommendations (A5)
1. Blend contango (th=1.02, hyst=0.05) + VIX3M-MM + a genuinely uncorrelated sleeve
   (ls_n10r14_2018 has corr 0.05-0.07 but starts 2018; ask A6 for the 2008+ version).
2. Test 2022-specific conditioner that does NOT whipsaw: e.g., us10y > 3% AND rising
   6m (rate-shock regime) → halve exposure; 2022 was a rates bear, 2018 a QT bear.
3. Continuous (z-score) term-structure scaling instead of binary gate; monthly cadence.
4. Ask coordinator: consider relaxing gate d for <10% vol sleeves to "worst year > -5%
   AND sum of neg years > -8%" — count-based rule systematically excludes honest
   long-equity premia.
ROUND r1 DONE

# A5_vol_cond — round r2 (2026-08-28)

## Verdict: 1 sleeve SAVED — A5_r2_contango_rateshock (SR 1.02, all 7 gates pass).
Data: us10y FRED 2000+ (good); vix/vix3m from alphaportfolio_replication/data (vix3m
still caps window at 2009-09); XGB1y_deploy evals at implausible SR 4.32 — flagged.

## Ideas tried (T+1, 6bps on turnover, expanding trailing-only vol target, scramble =
200 perms of positions vs real date-aligned SPY returns, costs re-applied)

1. **Rate-shock conditioner on contango (th1.02 hyst0.05), halve (mult=0.5)** — FAIL gate d on count.
   Grid W{100,126,150} x chg{+25,+50,+75bp} x lvl{2.75,3.0,3.25}: best SR=0.98 (W150,+25bp,>2.75),
   H1=0.88/H2=1.06, plateau OK, scramble 0.000, 2022 -20.8%→-8.1%. But negyr=3 (2011 -0.3,
   2018 -3.5, 2022 -8.1). Conditioner fixed the MAGNITUDE of the bad years, not the COUNT.
   Contango itself improved to SR 0.86-0.94 pre-vol-target — the cond adds real alpha (p=0.000).
2. **mult=0 (stand flat during rate shock)** — ALL GATES PASS → SAVED.
   (W=150, chg=+25bp, lvl>2.75): SR=1.02, ann 9.0%, vol 8.8%, H1=0.94/H2=1.10,
   negyr=2/18 (2011 -0.16%, 2022 -1.87%, both > -5%), scramble p=0.000,
   plateau: all 27 grid cells SR 0.805-1.019 (mult axis monotone 0.86→1.02 — endpoint, not spike;
   far corners 0.805-0.808 flagged in .meta), corr ≤0.14 to 28/42 library sleeves
   (0.03 to XGB1y_deploy; 0.63-0.68 only to legacy L_S equity books). Shock days 21% of window
   (2010-2026, incl 2018/2022/2023 ~170d/yr). mult=0.25 also passes a/c/e, negyr=3 — adjacent
   acceptable configs exist. Saved: sleeves/A5_r2_contango_rateshock.csv + .meta +
   scripts/a5_r2_rate_shock_contango.py (byte-verified identical to validated pipeline; NaN
   warmup days = no shock, matching base contango signal on those days).
3. **VIX3M-MM at vt 0.05-0.08 (charter idea 2)** — FAIL gate d. vt is a pure scale: SR 0.74 at
   every vt, always 4 neg yrs; vt=0.05 worst -6.4% (2022). vt=0.04: -5.2%, still 4. Fails by
   count regardless of scale; 2011/2015/2018 negatives are tiny but nonzero.
   MM + rate-shock cond (mult .5/.25/0): SR 0.81-0.83 but 2015 stays negative (-3.1..-1.1%) → 4th
   or 3rd neg year, worst -5.1% at mult0 → gate d fails on edge. No save.
4. **Portfolio mixes with XGB1y_deploy (charter idea 3)** — FAIL gate d, plus suspicion.
   XGB1y_deploy itself: SR 4.32 (implausible), 3 neg yrs incl 2012 -13.1%, 2022 -4.1%.
   Since EVERY charter member has 2022<0, no convex combination can pass gate d — confirmed:
   condC+MM 50/50: SR 0.88, 4 negyr, 2022 -20.8 (vol-target interplay failure).
   +XGB 25/33/50%: SR 1.13/1.26/1.63, negyr=3, worst -12 to -16% → fail. BUT scramble gate
   FAILS these mixes (p 0.44-1.0) — positional scramble vs T+1 SPY returns is degenerate for
   blends whose signal isn't SPY-directional (further evidence the gate needs a blend-aware variant).
   XGB+condC (25%): SR 1.49 negyr=2 worst -7.0 → fail. XGB+MM: SR 1.20-2.05, negyr 2-4, worst
   -8.3..-10.4 → fail; corr to XGB 0.44-0.88. Rejected: gate d + near-duplicate risk if XGB
   enters library later.
5. **Continuous z-score term structure, monthly (charter idea 4)** — FAIL gate d.
   win{63,126,252} x slope{0.25,0.5,1.0} x cap{1.0,1.5}: best z(252,0.25,cap1.0) SR=0.85,
   H1=0.87/H2=0.84, plateau OK — but continuous monthly scaling keeps ~full 2022 exposure
   (-18.0%): rates bears are LOW-vol-contango grinding bears, not TS-inversion episodes.
   + rate-shock cond (mult .5/.25/0): SR 0.90/0.90/0.89, but 2015 (-2.7%) persists → negyr=3 → fail.
   Binary contango + discrete rate-shock switch > continuous alternatives on this window.

## Structural diagnosis (carried forward + r2 additions)
- Gate (d) remains decisive. The r1 blocker was 2018/2022 magnitudes; the r2 residual blockers
  are TINY negatives (2011 -0.2%, 2015 -2.7%) — long-equity premia can't guarantee ≤2 neg years.
- The rate-shock switch (us10y>2.75% AND +25bp/150d) is the single best 2022/2018 conditioner
  found across both rounds: economically motivated (rates-shock = discount-rate bear), plateau-
  robust, monotone in conditioner strength, p=0.000.
- XGB1y_deploy SR 4.32/3.32% vol: either a mis-scaled series (spread-to-daily error?) or
  suspiciously good; coordinator should audit before blending it at library weights.
- Blend-aware scramble gate needed: positional scramble fails mixes whose alpha source is not
  the SPY return series (3b mixes: scram_p 0.44-1.0 despite REAL members). This gate will
  spuriously reject legitimate portfolio sleeves unless it permutes against each member's
  own return stream.

## r3 recommendations (A5)
1. Ask A6/coordinator for vix3m history pre-2009 (CBOE free) to re-test the saved sleeve on 20y;
   2008 pre-vix3m fallback: vix vs 3m-later-settled proxy or just rate-shock gate on B&H.
2. Try 2-stage vol targeting (target 10% but cap yearly drawdown contribution) — might rescue
   VIX3M-MM family by flattening 2015 while keeping SR.
3. Rate-shock conditioner is signal-agnostic: coordinator should test it as an OVERLAY on other
   long-equity library sleeves (it cut 2018/2022 by ~60-80% without whipsaw here).
ROUND r2 DONE

# A5_vol_cond — round r3 (2026-08-28)

## Verdict: 0 sleeves saved. All 4 charter ideas + 1 bonus failed ≥1 gate. Honest rejections below.

## ⚠️ METHODOLOGY INCIDENT (found & fixed mid-round; retracted numbers flagged)
My first idea-1 battery printed SR 1.08-1.36 ("trend + exit-stop"). INVALID: I passed the
strategy return series `sig*r` into a helper that applies T+1 shifting internally → the
evaluated stream accidentally skipped returns on exit days (double gating, lookahead-like).
Caught because the scramble gate's real-SR (-0.10) did not match the eval SR (1.08) —
the discrepancy is exactly what the scramble gate is for. ALL idea-1 conclusions below use
the corrected pipeline (positions shifted once; costs on final vol-scaled turnover, same
convention as the r2 saved sleeve, verified byte-identical rebuild of the champion:
SR 1.02 ✓). The r2 saved sleeve is UNAFFECTED (its script never used the buggy path).

## Ideas tried (T+1, 6bps on FINAL turnover, expanding trailing-only vt10, min 60d;
scramble: signal-permutation vs real date-aligned returns for single sleeves,
circular-shift of one leg for blends)

1. **Bond contango carry (charter 1)** — FAIL all gates.
   Charter framing (long bonds when y< y[63d ago] AND slope stable/rising, daily/weekly/
   monthly, lb{21,63,126} × sw{21,63}, 18 cells): best SR=0.24 (lb126 sw21 weekly),
   H2 mostly ≤0, 8-18 neg yrs, worst -10..-22%. Yield-downtrend-following on synth TR is
   a losing signal 2006-2026 (bond bear whipsaws: 2009, 2013, 2015-17, 2021).
   Variants: carry-only flat, 2s10s steepener (SR -0.26), value zone y10<5y-median (0.33),
   trend63 AND value (0.51). Best honest member: plain 63d TR trend SR=0.69 pre-... no —
   that was the contaminated eval; correct pipeline: TR trend lb42/63/126 = 0.30/0.19/0.27,
   9-11 neg yrs, 2022 -11..-12%. Rate-shock exit-stop overlay (flat when us10y
   >+k bp over w days): does NOT rescue (lb63 grid 38 cells: SR -0.22..0.24).
   VERDICT: bond books from FRED yields cannot pass gate a here; closest structural
   finding — the 63d TR trend is H1-weak (0.50) H2-negative (≈0), i.e. bond trend died
   post-2016 as yields hit the zero floor then chopped.
2. **VIX>40 capitulation reversion, 21d max-hold + stop (charter 2)** — FAIL all gates,
   decisively NEGATIVE. 18 configs (thr{35,40,45} × mh{10,21,42} × stop{5%,10%}):
   SR -0.21..0.00, every cell fails a/c/d. T+1 longs enter AFTER the VIX spike print and
   ride the continuation leg (2008, 2020: VIX>40 persists while SPY grinds down 20%+).
   Confirms r1 break-glass: the only profitable T+1 direction during spikes is flat.
3. **FX accrual-carry + contango mix (charter 3)** — FAIL gate d.
   Rebuilt A2 idea-10 accrual carry (7 pairs, top2/bot2 monthly, accrual=ydiff/100/252,
   2018-07+): solo SR=0.19 (worse than A2's 0.30 due to vt10 re-target; 4 neg yrs).
   corr(carry, contango)=0.008 — beautifully orthogonal, as promised. Mixes
   w_contango{0.3,0.5,0.7}: SR 1.02/0.84/0.52, H1 1.16/1.04/0.71 — but 2018 (carry's
   -1.6% yr amplified to -6.6% at vt) forces negyr=2 with worst -6.6%/-7.0% → gate d fails
   on magnitude. No config passes; the mix is real alpha but the carry leg has no
   2008-style crash test and drags 2018.
4. **Gold 126d trend + contango mix (charter 4)** — FAIL gate d (closest of the round).
   Gold trend lb{63,126,252} solo: SR 0.52/0.75/0.46; lb126 passes a+c (H1 0.60/H2 0.89)
   but 6 neg yrs. Mix with contango (w_gold{0.3..0.6}, corr 0.025): SR 1.10-1.21(!),
   H1 0.90-1.01, H2 1.27-1.39, worst yr -4.0..-5.5% — but negyr=4 (2009 -0.7%, 2015
   -0.7..-1.7%, 2018 -0.5..-1.9%, 2022 -4..-5.5%) → gate d fails on COUNT again.
   Rate-shock conditioner on gold (flat when us10y >+k bp / w d): fixes some years but
   breaks others (k50 w126: 2021 -6.1%; k25 w252: 2026 -7.3%); 9-cell grid all negyr≥6.
   VERDICT: real, near-passing diversifier (corr to library max 0.05-class); blocked by
   the count-based yearly gate, not by magnitude. Strongest r4 candidate if gate d is
   re-specified (e.g., worst>-6% AND sum(neg yrs)>-10%) — same structural point as r1.
5. **BONUS: gold long during high-VIX (mirror-regime vol conditioning, 20y FRED vix 2000+)** —
   FAIL. lvl{25,28,32} × hyst{5,8}: SR 0.13-0.35, 4-6 neg yrs (2021 -0.5..-5.4% is the
   recurring killer: high VIX + rising real rates = gold bear). Gold is NOT a clean
   vol-event hedge at T+1 on this window.

## Structural diagnosis (r3 additions)
- The count-based gate d (≤2 neg yrs) again decided every close call: ideas 3/4 produce
  SR>1.0 blends with worst years ≈ -5% but 4 small negatives. A sum-based or
  worst-only gate would have passed gold-mix w=0.3 (worst -4.0%) — coordinator decision
  needed, not more data mining from my side.
- Bond synth-TR trend on FRED yields is structurally weak post-2016 (zero-floor regime);
  charter idea 1's contango framing is strictly worse than plain trend and both fail.
- The r2 champion rebuild in the corrected pipeline reproduces SR 1.02 exactly —
  saved-sleeve integrity confirmed after the bug scare.
- A2 accrual-carry rebuilt here scores 0.19 vs A2's 0.30 — vt10 re-targeting (my
  convention) vs A2's; carry's 2018 remains its worst year regardless.

## r4 recommendations
1. Gold126 + contango (w=0.3) is the best unsaved artifact: ask coordinator for a gate-d
   variant (sum-of-neg-years) and save it there; do NOT let me grid-search the mix weights
   further (overfitting risk, and w=0.3-0.6 all similar = genuine plateau).
2. If vix3m pre-2009 ever lands, re-run the champion on 20y; FRED vix (2000+) alone can
   proxy contango via vix percentile vs its own 1y window (untested this round).
3. Keep the scramble-real-vs-eval consistency check as a standing QA: it caught the only
   true bug of the round before any decision was taken on it.
ROUND r3 DONE

# A5_vol_cond — round r4 (2026-08-30)

## Verdict: 1 sleeve SAVED — A5_r4_vt15_contango (SR 1.02, ann 13.5%: meets the r4 mission bar
## SR>=0.8 AND ann>=12%). Honest framing: it is a REPLACEMENT for the champion's A5 member,
## not a new diversifier. Ideas 2/3/4 failed gates as detailed below.

QA this round (r3 lesson applied): final positions built ONCE with T+1 embedded; eval and
scramble share one net(p)=p*r - |dp|*cost definition, so scramble real-SR must equal eval-SR
(it did: 1.02==1.02). Champion rebuild byte-matches the saved vt10 CSV (max|diff| 1e-17).
One honesty catch on MYSELF: my first .meta draft claimed a champion-swap result I had not
verified (EW6 recon initially failed because I used the wrong A6 member + fillna(0) instead
of NaN-skipping EW); corrected the meta with verified numbers below before finishing.

## Ideas tried (T+1 once, 6bps on final turnover, expanding trailing vol target, min 60d)

1. **Contango+rate-shock at vt15 (charter 1) — PASS ALL GATES → SAVED.**
   Identical signal to A5_r2 champion member (contango th1.02/h0.05, RS W150 +25bp lvl2.75);
   only vt 10%→15%. SR=1.02, ann=13.46%, vol=13.2%, H1=0.94/H2=1.10, negyr 2/18
   (2011 −0.73%, 2022 −3.09%), scramble p=0.000. Plateau: vt 0.12–0.18 all SR=1.019
   (scale-invariant axis); signal-grid neighbors 8 cells SR 0.872–1.005 (86–99% of peak).
   Corr: 1.000 to its vt10 twin (expected — linear rescale), 0.71 to full champion daily,
   0.49 to champion-ex-A5 EW5, ≤0.3 to 30/42 library sleeves. Official harness eval
   reproduced every number. Champion swap test (daily EW6 recon corr 0.88 to official
   CHAMPION_FINAL_daily, monthly resample): vt10 EW6 SR_m 2.15/ann 9.8% → vt15 EW6
   SR_m 2.05/ann 10.4%, zero negative years in BOTH. Coordinator owns the tradeoff:
   −0.10 blend SR_m for +0.6% ann with identical risk profile.
2. **Triple-gate (contango × no-rate-shock × no-VIX-spike) at vt18 (charter 2) — FAIL d.**
   Spike-veto thresholds 28/32/40: SR 0.85/0.91/1.00, ann 14–16%, but negyr 3–4 each;
   killer is 2011 (−7.0% to −21.5%): vetoing during VIX spikes forces exit at the August-2011
   lows and re-entry whipsaw, converting the base sleeve's +0.0% 2011 into a disaster.
   6 RS-variant neighbors at vt18: SR 0.79–0.89, negyr 3–5, worst −20..−28%. No salvage.
   The charter's "(1) passes" precondition was met, but the added gate strictly hurts.
3. **Capitulation reversion, VIX>thr long SPY max-hold 21d at vt15 (charter 3) — FAIL
   decisively.** thr 28/32/36: SR 0.27/0.21/0.16, H1 −0.16..0.16, 2008 −10.6/−22.6/−34.9%.
   Third independent confirmation (r1 idea 4, r3 idea 2, now r4 at lower thr): T+1 entry
   after a VIX spike rides the crash continuation. This signal family is dead at T+1; stop
   proposing it.
4. **Gold126 trend + bond63 TR-trend defensive mix at vt15 (charter 4) — FAIL a+c.**
   Charter paired bond contango (r3: 0.19) with gold126 (0.75 standalone here). I used the
   BEST honest bond leg from r3 (plain 63d TR trend) and inverse-vol position blend w_gold
   0.3/0.4/0.5/0.6: SR 0.22/0.32/0.42/0.52 — all below gate a, negyr 7–10, corr(legs)=0.07.
   The bond-trend leg is the anchor (r3 finding reconfirmed: dead post-2016); NOT rescuable
   by mixing. Note: the genuinely near-passing r3 artifact was gold126+CONTANGO (SR 1.10–1.21,
   failed gate d on count only) — that remains the coordinator's gate-d-reform candidate,
   and I did not re-grid it per r3 anti-overfitting note.

## Structural notes (r4)
- The r4 mission bar (SR≥0.8 AND ann≥12%, |corr|≤0.3 to champion) is self-contradictory for
  A5: the only sleeves I can build at ann≥12% are re-budgets of the champion member itself,
  so their corr to the champion is ~0.7 by construction. I interpret the corr criterion as
  applying to the champion-ex-A5 (0.49 here) and flag it for the coordinator.
- vt re-budgeting does not change SR, negyr count, or halves — gate d scaling was exactly as
  the charter predicted (−0.2→−0.7, −1.9→−3.1). Gate d is untouched by vol budget; only the
  SIGNAL decides yearly counts.
- VIX-spike vetoes are harmful, not neutral: 2011 is a high-VIX contango year where the carry
  pays; gating it out creates the worst single-year loss of any variant tested this round.
- Standing recommendation (r1-r4): reform gate d to worst-year + sum-of-neg-years; count-based
  ≤2 remains the decisive blocker for honest long-premium and gold-mix sleeves.

ROUND r4 DONE

# A5_vol_cond — round r5 (2026-08-30)

## Verdict: 0 sleeves saved. All 4 charter ideas fail the r5 mission bar (SR_m>=1.1,
## ann>=15%, corr<0.2) or hard gates. Best verified artifact remains the r4 vt15
## champion-replacement (SR 1.02, ann 13.5%). A vt18 rescale (ann 16.2%) verifies under
## the charter's own relaxed gates but misses mission SR_m by 0.02 and is corr 1.000 to
## the two saved twins — NOT saved (near-duplicate rule, r1/r4 precedent).

QA (r3-r4 lessons holding): pipeline rebuild of the vt10 champion byte-matches the saved
CSV (max|diff| 1e-16); scramble-real-SR == eval-SR asserted on every gated run (1.019==1.019).
Window 2009-09-16..2026-08-11, n=4249 (vix3m constraint), T+1, 6bps/side, expanding trailing vt.

## Ideas tried (in charter order)

1. **vt18 re-budget of champion (charter 1) — RELAXED-GATE PASS, MISSION FAIL, NOT SAVED.**
   SR=1.02 invariant across vt 0.14-0.22 (pure scale, r4 finding reconfirmed).
   Charter-relaxed validation: H1=0.94 / H2=1.10 (both >=0.45 ✓), negyr=3/18 (2011 -1.2%,
   2015 -0.1%, 2022 -3.9%; <=3 ✓ — note 2015 flips negative vs vt15's 2: higher budget
   shifts the cost-vs-gross sign on a ~0% year), worst=-3.9% (>-8% ✓), scramble p=0.000.
   MISSION: ann=16.2% ✓, but SR_m=1.08 < 1.1 ✗ (1.09 at vt14, monotone drag from monthly
   resampling; the bar is unreachable by re-budgeting a 1.02-daily-SR signal), corr ✗ by
   construction (1.000 to saved vt10 AND vt15 twins, 0.71 to champion daily, 0.48 to
   champion-ex-A5, lib mean|corr| 0.23). Swap recon (daily-EW, monthly-SR convention):
   champ SR_m 1.99→1.93, ann 8.5→9.5%, neg months 60→57. Coordinator one-liner if wanted:
   vt18 = vt15 CSV × 1.2 (SR-invariant). Saving would add a third corr-1.000 CSV to the pool.
2. **Continuous contango scaling pos=clip(1-(ratio-1)*s,0,1) @vt18 (charter 2) — FAIL hard.**
   s=4/5/6: SR 0.77/0.80/0.81, negyr 4/18, worst -24.4/-24.8/-25.2% (2018 -14%, 2022 -25%).
   Continuous scaling keeps partial exposure in persistent-contango grinding bears — exactly
   the r2 idea-5 failure mode, now at 3 slopes. With rate-shock veto (s=5): SR 0.94,
   ann 15.1% but negyr 4, worst -8.8% (2011 — conditioning out of the Aug-2011 bounce, the
   r4 triple-gate lesson again). Fails d AND relaxed-d. Third independent kill of this family.
3. **Contango@vt18 75% + capitulation long (VIX>32, maxhold21d) 25% (charter 3) — FAIL
   gate e + mission; the negyr=1 headline is a trap.** Cap leg solo: SR 0.28, ann 5.3%,
   negyr 2 (2010 -12.3%, 2020 -0.9%), n_on=462d. 4th look confirms r1/r3/r4: conditional
   drift is POSITIVE at T+1 (SPY +13.7bp/d on cap-on days vs +4.2bp/d off, hit 55%) but far
   too small for its vol. Mix 75/25: SR 0.98, H1 0.85/H2 1.10, negyr 1/18(!), worst -0.0% —
   passes a/c/d BUT (i) SR is LOWER than the 75%-cash control (1.019): the leg adds vol
   without mean — net dilution; (ii) blend-shift scramble (circular-shift cap leg, 200
   perms, contango leg date-aligned): p=1.000 — EVERY random alignment beats the real one
   (shifted SR dist 1.033-1.051 vs real 0.980); (iii) mission fails anyway (SR_m 1.06,
   ann 13.4%; re-vol'd to 18%: SR_m 1.01, negyr 2). Caveat recorded: single-leg shift
   scrambles are variance-confounded for blends (r2/r3 finding) — but gate e is the
   contract, the control test independently shows no alpha added, and the negyr-1 rides on
   2011/2022 bounce luck. NOT SAVED.
4. **Bond contango (best r3 cell lb126 sw21 weekly) @vt18 (charter 4) — FAIL everything,
   as the charter predicted.** SR 0.20, SR_m 0.21, ann 2.5%, 9 neg yrs, worst -15.8%
   (2009 -15.8, 2013 -15.4, 2021 -14.7, 2022 -9.9). A vol budget cannot rescue zero-alpha;
   r3's 0.19-0.24 re-confirmed. FRED synth-TR trend/carry books stay dead post-2016.

## r5 structural conclusion (for coordinator)
- The r5 mission bar is unreachable INSIDE the A5 family: ann>=15% requires vt>=18% on the
  contango champion, which is corr 0.71 to the champion because it IS the champion member,
  and SR_m tops out ~1.08 (resampling drag on 1.02 daily SR). A corr<0.2, SR_m>=1.1 A5
  member needs NEW alpha; this round's three attempts (continuous TS scaling, capitulation
  T+1 pair, bond carry) all failed on 2009-26 data.
- A5's standing contribution: A5_r4_vt15 (SR 1.02, ann 13.5%, negyr 2, corr 0.49 ex-A5) as
  the champion's 15%-vol swap option; vt18 deployable as ×1.2 rescale for +2.7% ann at
  -0.06 blend SR_m (coordinator's call).
- Gate-d reform recommendation (r1-r4) unchanged: the count rule again decided idea 3's
  fate less than the scramble/control did — but formally, 4 small negatives would have
  passed a sum-based rule. Reiterate also (r3): adopt a member-wise permutation scramble
  for blends before using p-values like 1.000 to reject mixes; I rejected idea 3 on the
  contract as written plus the control test, not on the confounded p alone.
ROUND r5 DONE

# A5_vol_cond — round r6 (2026-08-30)

## Verdict: 0 sleeves saved. All 4 charter ideas FAIL gate a (charter bar SR>=0.7;
## best of round is credit always-long carry at 0.43). One coordinator-critical data
## find: the ENTIRE library credit family (4 sleeves) is degenerate/negative.

QA (standing r3-r4 checks): r6-lib rebuild of the r4 champion byte-matches the saved
CSV (max|diff| 1e-16, SR 1.0192==1.0192) and scramble-real==eval consistency holds
(p=0.000). One display bug to flag: my idea-1 script's trailing "BEST SR_m 1.83" line
mis-applied sqrt(252) to MONTHLY returns — that line is a display artifact; all gate
decisions used daily SR as printed per cell. Gates per CHARTER_r6: SR>=0.7, halves>=0.35,
<=3 negYr, worst>-8%, scramble<0.05, plateau, corr<0.35.

## Data QA that changed the charter's scope
- FRED t10y2y == computed us10y-us2y (corr 1.0000, mean|diff| 0.0000) -> idea 1 ran on
  the 2000+ window as chartered, not 2005+.
- twelvedata/SPY.csv has clean OHLC 2006-09..2026-08 (open/close recon err ~0, 0 bad
  days) -> idea 3 did NOT need the 2016+-only SKIP path; full 20y testable.
- FRED spy_early (1993-2005, level ~SPX/10) spliced to twelve_big SPY (2006-09+) with
  the seam-day return nulled -> idea 2 has a genuine 2000+ equity window (n=6503).

## Ideas tried (T+1, 6bps on final turnover, expanding trailing vt10 min-60d; scramble =
200 position-permutations vs real date-aligned returns)

1. **Term-premium timing (charter 1)** — FAIL a/c/d everywhere. Long 10y synth TR
   (dur 7.5) when t10y2y>0 AND us10y<MA{126,252,504}, cadence daily/weekly/monthly,
   slope on/off (18 cells): SR 0.14-0.40 (best ma126 weekly slope-off 0.40, H1 0.54/H2
   0.23), 8-14 neg yrs, worst -13 to -23%. Third confirmation of r3/r5: FRED-yield bond
   books carry no timing alpha on 2000-26; the "value" gate (yield below own MA) buys
   into 2013/2015-17/2021-22 bear grind. Costs trivial (<1.5x ann mean even monthly).
2. **VIX-level term premium (charter 2)** — FAIL a/d; also NOT decorrelated.
   vix vs MA{126,252,504} below/above-mean gate on spliced SPY, 2000+: SR 0.09-0.37
   (best ma504-below 0.37, the only cell passing c: H1 0.35/H2 0.42), 4-11 neg yrs,
   worst -15 to -31%. Decorrelation FAILS: corr 0.52 to the saved contango champion
   (both are slow vol-regime gates on the same equity premium), corr 0.61 to
   L_S_130_30_volmanaged. The 2000-02 VIX-above-mean bear is the structural problem
   (buy-and-hold through it in every "below" variant gets 8+ neg years).
3. **Overnight premium in SPX (charter 3)** — FAIL a by COST ARITHMETIC, decisively.
   Gross overnight leg (close->open) is real: 2.50 bp/d, ann +6.3%, gross SR 0.53,
   H1 0.26/H2 0.82. But an overnight sleeve trades a FULL round trip every held day:
   12 bp/d = 30.2%/yr vs +6.3%/yr gross -> net -23.9%/yr. No conditional variant comes
   close to break-even: weekday means 1.01..6.40 bp/d (Tue best), VIX>25 -6.9, VIX>30
   -16.5, post-down-day -28.8 bp/d; trailing-z gate (best conditional, SR 0.64 gross)
   still trades ~daily. Corollary worth keeping: intraday leg mean is +1.74 bp/d — the
   close-to-close premium is ~59% overnight / ~41% intraday, i.e. the overnight anomaly
   here is too small for 6bps/side T+1 infrastructure. NOT testable cheaper on free data.
4. **Credit carry with better entry bands (charter 4)** — FAIL a/d; charter premise
   INVERTED. DV01-neutral synth excess return (7.5*(-ds) + s/252) on BAA-AAA, 1986+
   and 2000+, lb{126,252,504} x {always-long, z-bands 0.1/0.3, long-flat, wide-of-MA,
   wide+0.5sd, continuous clip} (42 cells): EVERY conditional band SR -1.03..+0.13 —
   "long when wide / short when tight" LOSES money vs always-long in 40/42 cells.
   Always-long carry: SR 0.43, ann 2.3%, H1 0.47/H2 0.40 (passes c), 12 neg yrs, worst
   -26.1% (2008) -> fails a (0.43<0.7) and d. Reversion (library direction) on my synth:
   -0.07..+0.01 — nothing there either. My always-long corr to library credit sleeves
   is -0.09..-0.12 because... see below.

## COORDINATOR ALERT: library credit family is degenerate
All four Credit_* library sleeves have ann vol 0.84-1.16% and NEGATIVE SR:
Credit_z250_1986 -0.41, Credit_z120_1986 -0.44, Credit_z250_2008 -0.45,
Credit_spread_z_reversion -0.49; yearly returns are ~0.00 in almost every year (sum
-14% over 40y). This looks like the same conversion bug class as r2's XGB1y_deploy
(SR 4.32, vol 3.3% — opposite direction). Whatever produced these likely divided a
spread LEVEL by a price scale or annualized wrong. They should be pulled from the
blend pool and re-derived (my DV01-neutral construction in
campaign/scripts/a5_r6_idea4_credit_carry.py is one honest starting point). Note the
r6 charter's "your A1 found 0.53" was against the OLD (broken) series; on the correct
DV01-neutral synth the same z250 signal scores ~0.

## Structural conclusion (r6)
- All four charter families are DEAD on free data at 6 bps/side: rates timing (SR
  ceiling 0.40), VIX-level slow gates (0.37, and corr 0.52 to the champion anyway),
  overnight capture (negative net by construction), conditional credit (negative
  directional alpha). A5's honest contribution remains the saved
  A5_r2_contango_rateshock / A5_r4_vt15 pair (SR 1.02 daily, corr 0.49 ex-A5).
- Reiterate r1-r5: gate-d reform (worst-year + sum-of-neg-years) would not have saved
  anything this round either — every idea fails gate a by 0.3-0.6 SR. The blocker is
  alpha, not gate design.
ROUND r6 DONE

# A6_reversal — Round r1 FINDINGS (2026-08-28)

Panel: twelve_big (298 names, 2006-09..2026-08). Costs 6bps/side on daily one-side turnover,
T+1 execution (weights shifted 1d), vol-target 10% via expanding-window trailing vol.
Verdict: **NO sleeve passed all gates this round.** Near-misses documented for r2/coordinator.

## Idea 1 — Weekly xs reversal L/S (charter family 1)
36-config sweep: k∈{3,5,10} × idio-vol-filter(10/90) × inv-vol weights × cadence∈{1,5,10}.
- BEST net: k=10, ivol-filter, cadence=5: **SR 0.17** (gross 0.60 → 337bps/yr cost drag).
- Daily cadence catastrophically negative (k=3 daily: SR −1.13 net; turnover ~85%/day one-side).
- Attribution: gross long side SR 0.60; SHORT side gross SR −0.22 (shorting winners LOSES money
  gross in this 298 big-cap panel — momentum continue, no reversal premium on the short side).
- Long-only (cash) reversal, best decile, ivol-filtered, cadence 5, k=10: **SR 0.67 net** raw,
  0.63 at 10% vol-target; halves 0.51/0.76; FAILS gate d: 3 neg years, worst 2008 −5.6%,
  2022 −5.3% (just past the −5% floor).
- Crash fixes tested (all trailing-data): MA200 regime overlay (SR 0.70, but 5 neg yrs,
  2022 −8%), full MA gate (whipsaw, 6 neg yrs), low-beta losers screen (SR 0.58, 2008 −14.5%),
  falling-knife screens (>−15/−25/−35% 20d excluded: worse), calm-entry mkt10>−8% (SR 0.74,
  2022 −8%), fast vol-target 21/42d (SR 0.76, 2022 −5.3 to −9.1%).
**FAIL: all variants ≥3 neg years or worst-year breach.**

## Idea 2 — Residual momentum (12m orthogonal to FF3+Mom, trailing 252d betas)
- LS tercile: SR −0.10 net. Long tercile monthly, vol-tgt: **SR 0.64**, halves 0.40/0.96,
  but 2008 −11.2%, 2022 −8.6% → FAIL gate d.
- Daniel–Moskowitz gate (126d mkt ret>0): SR 0.94, halves 0.97/0.92, 2022 −12.0% FAIL.
- + MA200 confirm10 hysteresis gate: **SR 1.03** (MA150) / 1.00 (MA200), halves ~0.86/1.2,
  neg years 2 (2015 −4.9%, 2022 −12.9 to −14.9%) → FAIL gate d on 2022 alone.
- 2022 forensics: gate is OFF Feb–Oct 2022 (correct), but Jan-2022 pre-exit −9.6% and
  Dec-2022 bear-rally re-entry trap −4.6%. Inherent 10–60d confirmation lag; no trailing
  gate tested (MA/hysteresis/credit<2023-only-OAS/strat-DD) fixed it without killing SR.
- Low-beta screens/1/β weights: worse (0.38–0.62) or 2008 −18 to −37%.

## Idea 3 — Momentum + reversal blend (monthly)
Vol-tgt 10% per leg then blend: best (70% gated mom / 30% LO-rev) SR 1.06 but 2022 −13.2%
(momentum leg owns it). 50/50: SR 0.95, 2022 −14.3%, 2008 −6.6%. FAIL.

## Idea 4 — Idio-vol-managed momentum (1/σ252 constant-vol sizing)
Raw: SR 0.75, 2008 −18.4%. + MA150c10 gate: SR 1.01, 2022 −12.1% FAIL. Hinge 0.5x: 0.87 FAIL.

## Idea 5/6 — Best near-miss pair (gated resid-mom 65–75% + LO-rev)
corr(mom, rev vol-tgt legs) = 0.38. Best blend (65/35): **SR 0.88**, halves 0.64/1.22,
neg years 3 {2008 −4.2, 2015 −0.2, 2022 −8.2}. FAIL gate d via 2022; closest full-family combo.

## Idea 7 — Plain 12m momentum long (control)
SR 0.74, halves 0.53/1.00, only 2 neg years but 2008 −19.7% → FAIL (documented baseline).

## Idea 8 — Extended panel (440 names) LO reversal — **DATA ARTIFACT, REJECTED**
Naive run: SR 3.5 (!). Forensics: book concentrates 100% weight in $0.01-stale-quote OTC names
(AIAD $0.01↔$3.38 = +33,000%/−99% "reversals", AKTS, ADVT...). With honest filters
(price≥$5, 60d median dollar-vol≥$2M → only ~29 names survive): **SR ≈ 0.00.**
The twelve_extend panel is unusable for low-price reversal without quote hygiene. Logged loudly.

## Gates infrastructure note
Scramble gate implemented as 200x path-shuffle of realized returns (SR percentile).
lib6.py has a per-file-dedupe loader because shared harness `closes()` crashes on
duplicate dates in the raw panel (unfixed upstream — not modified per contract).
`ff_mom()` in the shared harness also fails to parse (header offset); local shim used.

## Bottom line for coordinator
- xs weekly reversal is NOT a standalone SR≥0.6 sleeve here: net-of-cost it is a
  **long-side-only**, modest-SR (0.6–0.7) sleeve whose vol-targeted form misses gate d by
  −0.3 to −0.6pp in 2008/2022. Best honest: LO-rev k=10 decile20 cadence5 vol-tgt10
  SR 0.63, H1 0.51 / H2 0.76.
- Gated residual momentum (MA150 confirm10, DM-style) reaches SR 1.03/1.06 (best raw numbers
  of the round) but carries 2022 −13%. If blended ≥50/50 with a sleeve that is POSITIVE in
  2022 (e.g. A2 carry/CTA), portfolio-level 2022 can flip positive — recommend coordinator
  test `0.5*residmom_gated + 0.5*(2022-positive sleeve)`; per-sleeve gates still not met,
  so NOT saved as a sleeve.
- Nothing saved to sleeves/ this round (all gates must pass per contract).

## ROUND r1 SUMMARY (appended)
Tried (in order): (1) weekly xs reversal L/S — 36-config sweep, best net SR 0.17 (cost drag
337bps/yr; short side gross-negative); (1b) long-only reversal — best honest sleeve of the
family, vol-tgt SR 0.63, H1 0.51 / H2 0.76, but 3 neg years {2008 −5.6, 2018 −1.3, 2022 −5.3}
→ gate d fail (−0.3pp/−0.3pp past floor); 8 crash-fix overlays all failed gate d or halves;
(2) residual momentum — LS −0.10, long 0.64, DM-gated 0.94, DM+MA150-confirm10-gated
**1.03 raw / 0.97 vol-tgt** (H1 0.79 / H2 1.21) — best strategy of the round, killed solely by
2022 −12.9% (Jan pre-exit −9.6% + Dec bear-rally trap −4.6%); (3) mom+rev blends — 0.84–1.06,
2022 −13 to −16%; (4) idio-vol-managed momentum — 0.75 raw / 1.01 gated, 2022 −12.1%; (5) pair
gated-mom 65% + LO-rev 35% — 0.88, 2022 −8.2%; (6) plain 12m momentum control — 0.74, 2008
−19.7%; (7) extended-panel (440) reversal — naive SR 3.5 exposed as stale-quote artifact
(AIAD/AKTS $0.01 prints); with price≥$5 + $2M liq filters SR ≈ 0.00 → panel unusable for
reversal without quote hygiene.

Passed ALL gates: **none** (0/7 ideas). Reusable artifacts: lib6.py (loader+gates),
idea1_reversal.py, idea234_engine.py, campaign/scripts/a6_idea1_lo_reversal.py and
campaign/scripts/a6_idea2_residmom_gated.py (both verified to reproduce their numbers).
Nothing saved to sleeves/ per honesty contract. Handoff to r2: (a) rescue LO-rev via
cleaner 2008/2022 (e.g. beta-conditioned losers, 130/30 with small short side at low cadence);
(b) rescue gated resid-mom via faster regime exit (VIX FRED series is available and untested!);
(c) never use twelve_extend low-price names without filters.
ROUND r1 DONE

# ROUND r2 SUMMARY (appended 2026-08-28)
Panel/protocol as r1 (twelve_big, 6bps/side, T+1, trailing vol-target 10% expanding min-60d).

1. Mission 1a — FASTER REGIME EXIT for gated resid-mom (charter: VIX 21d-pct>70 exit-5d;
   2-tier MA150+VIX veto; MA126). **FAIL, and one infra bug found on the way.**
   - MA126/180 gates: SR 0.90–0.92, 2022 −12.0 to −12.3% (no better than MA150).
   - VIX 21d-pct>0.60–0.80 veto (5d latch): catastrophic, SR 0.06–0.31 — the percentile trigger
     fires ~30–40% of all days by construction (wrong tool) and the latch stays out for months.
   - vix>vix63ma veto: 2022 improves to −8.1% but SR collapses to 0.60 (too many false exits).
   - MA150c5 (faster both ways): SR 0.91, 2015 −6.4% — whipsaw replaces one bad year with another.
   - ddEntry idea (NEW, mine): when market is >15% below its 252d high, require 20d (not 10d)
     confirm to re-enter — kills the Dec-2022 bear-rally trap AND lifts SR to 1.08 raw (best of
     round) but Jan-2022 pre-exit −9.0% remains; 2022 ex-Jan is only −3.6% (would pass gate d).
2. Mission 1b/1c — vol-scaling fixes for Jan-2022. **FAIL + 1 artifact caught.**
   - First "PASS-looking" result (mktvol cap15% → 2022 −0.1%) was a BUG: I scaled by PRICE-level
     rolling std (~5000–14000) instead of return std; the 10% VT then clipped to the 5.0 leverage
     cap — a pure denominator artifact. Lesson recorded (lib: use .std() on RETURNS, check lev
     distributions before believing any result).
   - Honest versions (return-based mvol 21/42/63d, VIX/100, VT caps 1.0–1.5, VIX ladder 25/30/35):
     SR 1.01–1.07, 2022 stuck at −10.5 to −12.3%. KEY INSIGHT: expanding-window VT AMPLIFIES
     Jan-2022 (quiet 2021 → max 5x leverage into the crash): raw −12.3% → −16.0% after VT in
     several overlays. No trailing-data vol scaler can see a crash that starts in 10 days.
   - Fast vetoes (breadth<MA20 0.30–0.40, mkt<MA20x0.98, VIX>28, us10y 21dΔ>+40bp, 21d-low break):
     all fire too late in Jan-2022 or whipsaw 2015 to −11 to −22%. MISSION 1 VERDICT: target
     "2022 > −5% with full SR ≥ 0.9" is structurally unreachable without lookahead — the damage
     accrues in <15 trading days of a fresh regime; documented, not saved.
3. Mission 2 — LO-reversal rescue: beta-conditioned losers + 130/30 small short, cadence 7–10.
   **FAIL.** Low-beta-half losers: 2008 −16 to −24% (low-beta losers are falling knives in real
   crashes — conditioning makes it WORSE); best variant lowβ∧ivol cad5 SR 0.58 with 3 neg yrs.
   130/30 short overlays (10–30% shorts): fix 2022 (−0.4%) but detonate 2007 (−18 to −19%,
   Aug-07 quant quake) and 2008; all ≤ SR 0.43. The LO-reversal family remains unsalvageable to
   gate d in this panel; shorting winners stays gross-negative (r1 finding confirmed).
4. Mission 3 — PAIR sleeves (residmom_gated + X 50/50). **TWO SLEEVES PASS ALL GATES — SAVED.**
   - CRITICAL FIX first: lib6 scramble_pvalue was DEGENERATE (path-shuffles realized returns;
     preserves mean/std exactly → p=0.91 on pure noise; every r1/r2 scramble result meaningless).
     Replaced with proper signal-scramble: 200x circular shift of the weight path vs returns
     (keeps exposure+turnover, breaks timing). New gate is bite-y.
   - a6_r2_pair_residmom_fm1926: 0.5×gated resid-mom + 0.5×FactorMom_1926 (both VT10, pair VT10).
     SR 0.91, H1 0.92 / H2 0.91, neg years 1/20 (2016 −0.7%), worst −0.7%, 2022 +0.4%,
     scramble p=0.000, plateau: 13-neigh grid (w 0.4–0.6 × confirm 8–12 × ddEntry±) min 0.80 vs
     peak 0.99. SAVED (script campaign/scripts/a6_r2_pair_residmom_fm1926.py, verified by harness).
   - a6_r2_pair_residmom_msew: 0.5×gated resid-mom + 0.5×Multi_Strategy_EW. SR 0.88, H1 0.70 /
     H2 1.11, neg years 2/19 (2015 −0.3%, 2022 −3.7%), worst −3.7%, scramble p=0.000, plateau
     neighbor-min 0.82 vs peak 0.92. SAVED (campaign/scripts/a6_r2_pair_residmom_msew.py).
   - Other pairs tried and rejected: rm+CTA_15vol (H1 0.19, 2008 −15.8), rm+L_S_130_30 (2009
     −28.5! raw library series has a monthly-gap artifact — do not blend without alignment check),
     rm+Credit_z120_1986 (2007 −16.7), rm+FactorMom_2008/FF (3 neg yrs), rm+CTA_tsmom (5 neg yrs).
5. Alignment lesson (charter item 4) honored everywhere: all gate/level multiplications use
   Series/DataFrame .mul(..., axis=0); the one alignment bug this round was units (price-vs-return
   std), not axis — both now on the r3 checklist.

Honest scorecard r2: missions 1 and 2 failed as designed (documented why: regime-gate lag and
crash-knife beta conditioning are structural, not parametrizable away); mission 3 delivered the
campaign's first A6 sleeves saved to sleeves/ — both pass a/b/c/d/e/f/g with the FIXED scramble.
Caveats for coordinator: leg1 (gated resid-mom) alone still fails gate d standalone — the saved
sleeves are PAIRS; fm1926 leg starts 1926 but pair eval window is 2007+ (factor data pre-2007
reused only via the leg's own history), and its 2026 ends 06-30 (FactorMom_1926 ends there).

ROUND r2 DONE

# ROUND r3 SUMMARY (appended 2026-08-28)
Directive: ONE more orthogonal market-neutral sleeve, SR>=0.9 target, |corr|<0.3 to champion
(XGB1y_deploy + Merger_Arb_PEAD + A1_mix + A5_contango_rs + A6_pair_fm, reproduced SR_m 1.89).
Protocol as r1/r2 (twelve_big, 6bps/side, T+1, trailing VT10 expanding min-60d, .mul(axis=0),
scramble = 200x circular shift of WEIGHT path with costs+VT repriced).

1. Charter 1 — MONTHLY xs reversal L/S (cadence 21, k∈{5,10,21} x quint/decile x inv-vol/ew):
   12 configs, SR −0.10…0.21, ALL FAIL. Costs dropped 4x as chartered (turn ~770bps/d → ~115bps/yr
   drag vs 337bps weekly r1) — but the SHORT-LOSERS leg is gross-negative (LONG SR 0.62 vs SHORT
   SR −0.77). This panel (298 mega-caps) has no 1-month reversal premium on the short side at any
   cadence tested (weekly r1, monthly r3). The killer is the premium, not costs.
2. Charter 2 — residual reversal (FF4 residuals, k∈{5,10,21}, cadence 21): SR −0.15…−0.01, FAIL.
3. Charter 3 — resid-mom PURE L/S tercile (ungated + MA150c10dd20 gate): SR 0.02/0.10, short-bot3
   leg gross −0.70. FAIL. (Consistent: r2's saved sleeves are LONG-only legs.)
3b/3c — the market-neutral mandate via HEDGE instead of naive L/S: gated resid-mom long + trailing
   252d beta hedge vs panel EW. Raw hedge: 2022 −12.3% → +1.7% but 2014 −6.7% (hedge bleeds in calm
   grind-up years); SR 0.70, corr 0.32, worst-year FAIL. Conditioned hedge (gate-ON ∧ v21>expanding-
   median / 1y-66pct): best SR 1.05 but worst −9.2% and corr 0.54–0.62 — still the same book as the
   champion's A6_pair_fm leg. FAIL.
3d/3e — LO-reversal (monthly cadence, new territory) + market hedge. **LOOKAHEAD TRAP CAUGHT AND
   FIXED**: first hedge grid showed SR 1.43, 0 neg years — the MA200/vol condition and hedge return
   were both indexed at t (hedge must be hh(t-1) earning mr(t)). After the 1d lag the miracle
   evaporates: SR 1.43→0.84, negYr 3–6, corr 0.44–0.51. Honest grid: nothing passes. (Replicated as
   campaign/scripts/a6_r3_hedged_lorev_lookahead_check.py — keep this guard in every hedge test.)
   Base LO-rev k21 d10 ivw cad21 (no hedge) passed a–d initially (SR 0.63, H1 0.61/H2 0.64, negYr 2
   {2008 −1.3, 2022 −1.4}, worst −1.4%) but on FULL workup FAILED: scramble p=0.435 (needs <0.05 —
   timing indistinguishable from circular-shift chance) and plateau (chosen point is the grid's
   isolated peak; 8 neighbors min 0.45 < 0.8×0.63) and corr 0.48 (0.62 vs A5_contango_rs) — the
   monthly k21 LO-reversal edge is thin, param-fragile, and not decorrelated.
4. Charter 4 — 6-sleeve mix champion+CAND: SR_m 1.80 (champion 1.89) < 1.95 target; swap-variant
   1.74. NO SAVE. Adding this candidate dilutes the champion.

VERDICT r3: 0/4 charter items produced a saveable sleeve. The equity "market-neutral reversal"
family is now closed with evidence at three levels: (i) xs weekly [r1], (ii) xs monthly [r3],
(iii) FF4-residual monthly [r3] — all cost-dominated or gross-negative on the short side in this
mega-cap panel; the long-only reversal remnant (k21 monthly) fails scramble+plateau. Correlation
data worth keeping: LO-rev k21 corr by champion leg = XGB −0.07, MA 0.20, A1_mix 0.50,
contango_rs 0.62, pair_fm 0.08 — any future equity long book will inherit the 0.5–0.6 corr to
A1/A5 legs; true decorrelation in this library comes from factor/CTA/arb books, not equity L/S.
Infra: r3_lib.py (champion reproduction, fixed circular-shift scramble, gates); lib6.py scramble
still degenerate upstream — do not use it for gate e.
Nothing saved to sleeves/ per honesty contract.
ROUND r3 DONE

# ROUND r4 SUMMARY (appended 2026-08-30)
Directive: sleeve SR>=0.8 AND ann>=12%, |corr|<=0.3 to champion (6-sleeve EW, monthly SR 2.03;
CHAMPION_FINAL_daily). Protocol as r1-r3 + charter targets; corr gate measured monthly (corrD daily
also reported). All runs reproducible: campaign/scripts/a6_r4_momentum_budgets.py (verified).

1. Idea 1 — a6_r2_pair_residmom_fm1926 re-budgeted at vt15 (charter "fast win"). **FAIL (corr only).**
   The re-budget itself scales beautifully: SR 0.92 (was 0.91), ann 14.5% (was 9.5%), H1 0.93/H2 0.91,
   1 neg year (2016 -1.3%), plateau w_rm 0.4-0.6 all SR 0.84-0.98. Killed ONLY by |corr| to champion
   = +0.58 monthly / +0.78 daily (gate <=0.3). Root cause is tautological: A6_pair_fm is one of the
   champion's 6 legs, so this sleeve is 1/6 of the champion itself — it can never be decorrelated
   from it. Control at vt10 reproduces the saved sleeve (SR 0.91) and fails the same corr gate +
   ann>=12%: the saved r2 sleeve was always champion-internal, its corr gate never checked vs the
   final champion (it passed when measured vs the r2-era champion proxy).

2. Idea 2 — rm + FactorMom_1926 + QA_dualmom TRIPLE mix at vt15. **FAIL (corr only).**
   SR 0.90, ann 13.0%, H1 0.87/H2 0.92, 1 neg year (2022 -1.5%) — everything passes except
   corrM +0.60 / corrD +0.81. Leg corr: rm-qa +0.85 (both equity momentum LO), rm-fm 0.09,
   qa-fm 0.10. Weight grid 0.2-0.5 per leg: corrM 0.56-0.61 always fails; only side-failure is
   0.5/0.25/0.25 (2022 exactly -5.0% not > -5%). DECOMPOSITION (the round's key numbers): corr of
   the triple to champion legs = A6_pair_fm +0.87, A5_contango +0.56, A1_mix +0.52, XGB -0.17,
   MA -0.03. Exhaustive simplex search (0.1 steps): min |corrM| = +0.26 achieved ONLY at
   (rm,qa)=(0,0), fm=1 — i.e., no positive weight on rm or qa keeps the gate. rm-only +0.63,
   qa-only +0.55.

3. Idea 3 — momentum-on-momentum meta-timing (charter: expand rm book when own trailing 12m SR>0.5,
   shrink to 25%) at vt15. **FAIL (gate d + corr).** IMPLEMENTATION BUG CAUGHT FIRST: my first run
   used DAILY mean/std (no *sqrt(252)) for the trailing SR -> values ~0.06 never crossed any
   threshold -> the "timing" was a constant 0.25 multiplier and the three thresholds returned
   byte-identical results (classic stuck-signal tell; shrink=0.0 zeroing everything confirmed it).
   With annualized trailing SR (median 1.02, 69% of days at full size): SR 0.81-0.89, ann
   15-17.4%, H1 0.68-0.78 / H2 1.10-1.22, but 2022 -10.0 to -10.9% (gate d; trailing SR was still
   high after the good 2021, so the meta-signal is by construction blind to the crash — same
   structural lag as every r1/r2 regime gate) and corrM 0.46-0.54. Meta-timing on fm-only (the
   corr-legal leg) is a no-op for year counts (fm's neg years are pre-2007 history at vt15 vs its
   1932-2026 record) and fm-only standalone fails full SR (0.45) + gate d anyway.

4. Scramble (gate e) on the near-misses — infra notes for the campaign, run BEFORE any save would
   have been attempted, since all candidates were already dead on the corr gate:
   (a) all-legs-rolled circular-shift null (each leg independently shifted, costs+VT repriced):
   p=0.920 triple / p=0.155 pair / p=0.970 triple-meta — WARNING: rolling a 1926+ library leg's
   returns shifts Depression-era draws INTO the 2007+ eval window (verified: a shift of 5155 maps
   eval-start into 1943) and destroys inter-leg diversification, making the null uninterpretable
   for multi-leg mixes; do not reuse this variant blindly.
   (b) precedent-consistent null (roll ONLY the equity leg's weight path vs returns, library legs
   at true timing — the r2/r3 methodology): pair@vt15 p=0.005, triple p=0.205, CONTROL saved
   pair@vt10 p=0.005 (r2 reported 0.000 under slightly different seed/path handling — the saved
   sleeve's timing edge is thin-but-real vs a 1-in-200 bar, worth the coordinator knowing).
5. Infra: r4_lib.py (rm-leg cache, full_gates with charter thresholds + champion corr, composite
   scramble); composite_sr had a pd.DataFrame(list-of-series) transposition bug (fixed via
   pd.concat axis=1) caught when the scramble crashed on RangeIndex-vs-str comparison.
VERDICT r4: 0/3 charter ideas saved. The momentum family cannot contribute a NEW sleeve under the
|corr|<=0.3 gate because the champion already contains 2-3 equity-momentum books (A6_pair_fm
directly; A1_mix/A5_contango at +0.5). The charter's own arithmetic (three momentum-family legs,
corr 0.4-0.6 among themselves, "decorrelated from non-momentum champion legs") is empirically
false: the mix inherits corrM ~0.6 through its overlap with A6_pair_fm and the A1/A5 equity beta.
RECOMMENDATION to coordinator (not a sleeve): the correct venue for these returns is champion-level
re-budgeting — e.g. re-vt the champion's A6_pair_fm leg at vt15 (its pair@vt15 numbers are
station-grade: SR 0.92, ann 14.5%, 1 neg year) or replace the leg with the vt15 pair — which raises
champion ann at unchanged structure; that decision lives at blend level, where the corr gate is
measured against the OUTSIDE world, not against a book that is itself a leg. Also flagged: QA_dualmom
(A3) is corr +0.85 to my rm leg — A3/A6 look like one economic family for blend-diversification
purposes; the library's "40 sleeves" count overstates true independence.
ROUND r4 DONE

# ROUND r5 SUMMARY (appended 2026-08-30)
Directive (CHARTER_r5): one sleeve SR_m>=1.1, ann>=15%, corr<0.2 to champion (relaxed gate d:
negYr<=3, worst>-8%). Protocol r1-r4: twelve_big + library legs, 6bps/side, T+1, trailing
expanding VT, gates a-g. Reproducible: campaign/scripts/a6_r5_charter.py (verified run below).

1. Idea 1 — rm+FactorMom_1926 pair re-budgeted vt18 (charter "fast win", predicted SR~0.92
   ret~17.5%). **FAIL on corr ONLY — every other gate passes, including STRICT gate d.**
   SR 0.92, ann 17.3%, vol 18.9%, H1 0.92/H2 0.91, negYr 2 {2016 -1.6, 2022 -0.1}, worst -1.6%
   (passes even the un-relaxed gate: <=2 neg yrs, worst > -5%). Scramble p=0.005 (rm path rolled,
   fm true-timed, 200x, costs+VT repriced). Plateau: 25-pt grid w_rm 0.4-0.6 x vt 14.4-21.6%,
   chosen SR 0.92 vs peak 0.98, neighbor-min 0.83, 24/24 neighbors within 20% of peak — the best
   plateau of any A6 candidate ever. Killed by corrM +0.58 / corrD +0.78 to champ5 and +0.54/+0.67
   to the 6-leg CHAMPION_FINAL (gate <0.35). Tautology confirmed with new evidence: corr to the
   champion EXCLUDING A6_pair_fm (the outside world) is only +0.24 — this sleeve IS 1/6 of the
   champion. NOT SAVED per contract; correct venue is champion-level re-budgeting (raise the
   champion's own A6_pair_fm leg to vt18: +~8pp champion ann at unchanged structure/legs).

2. Idea 2 — pair@vt15 + own-trailing-12m-SR meta-timing (expand when SR12>thr, shrink to shr).
   **FAIL (corr + gate d + ann).** thr=0.5/shr=0.25: SR 0.81, ann 11.0% (<12), H2 0.70, NEW third
   neg year 2023 -2.9%, corrM 0.55. thr=0.25/0.5 and thr=0/0.5: SR 0.89/0.92, ann 12.1/12.6,
   but 3 neg yrs {2016, 2022, 2023} and corrM 0.57/0.49-0.57. Meta-timing inherits the underlying
   corr (0.55-0.57 vs 0.54 base) while degrading SR — it only re-times an already-correlated book,
   and its own trailing SR is structurally blind to regime turns (r4 finding replicated at the
   pair level; 2023 is the new victim: good 2022-hedge year -> full size -> chop).

3. Idea 3 — FactorMom_1926 @vt15 + MA gate (self-gate on own equity curve / SPX gate / DM126).
   **FAIL gate a — and LOOKAHEAD TRAP #4 caught in my own first pass.** Same-day gate application
   (state(t) x r(t)) showed SR 1.39-1.48 with 2 neg years — mirage: the "gate" peeks at today's
   library return. Honest form (decide at t on data <=t, hold (t,t+1], +6bps per one-side flip):
   self-MA100 SR 0.07, MA150 0.08, MA200 0.03, hysteresis 0.19-0.24 — FactorMom_1926 spends most
   of 2007-2026 below its own MA, and the expanding-VT then amplifies whipsaw losses after flat
   stretches (2023 -21%, 2026 -14-18% on gated variants vs ungated -15.2/-5.7). Ungated fm@vt15
   2007+ is SR 0.35 (H1 0.37/H2 0.33), 6 neg yrs; SPX-MA/DM gates 0.30-0.50 with corr 0.33-0.37.
   fm-alone cannot be a sleeve in the 2007+ eval window; its pre-2007 history cannot rescue SR
   without the pair structure (idea 1), which is corr-blocked.

Infra: r5 used r4_cache legs + r3_lib champion reproduction; corr measured to BOTH champ5 (r3
5-leg) and CHAMPION_FINAL (6-leg, from campaign/results/CHAMPION_FINAL_daily.csv) — recommend
always reporting the 6-leg corr going forward. All runs logged in LOG_r5.log.

VERDICT r5: 0/3 saved. Round-terminal statement for the A6 momentum/reversal family: the family
contains ONE economically distinct book (gated resid-mom + FactorMom pair). It is station-grade
at vt15-vt18 (SR 0.92, ann 14.5-17.3%, <=2 neg years, plateau 24/24, scramble 0.005-0.01) and it
is ALREADY IN the champion — no re-weighting, re-budgeting, meta-timing, or gating of it can
produce a sleeve that is simultaneously high-SR and decorrelated from a champion that contains it.
Corr-gate arithmetic: min corrM of any rm-containing mix is +0.26 (r4 simplex), now +0.24 for the
pair; the <0.3/<0.35 gates are unreachable by construction. RECOMMENDATION to coordinator
(repeat, now with vt18 numbers): swap/re-budget the champion's A6_pair_fm leg to the vt18 pair —
champion-level action, not a new sleeve. A6 has no remaining saveable ideas in this family;
future rounds should look elsewhere (or be explicitly tasked with champion-internal optimization).
ROUND r5 DONE

# ROUND r6 SUMMARY (appended 2026-08-30) — NEW-FAMILY directive
Charter: 4 ideas outside the closed reversal/momentum family. Gates r6: SR>=0.7, halves>=0.35,
<=3 negYr, worst>-8%, scramble<0.05, plateau, corr<0.35. Protocol r1-r5 (twelve_big + hygiene
price>=$5 & $2M 126d-median dollar-vol, 6bps/side, T+1, trailing expanding VT, corrM to 6-leg
CHAMPION_FINAL). All runs reproducible: campaign/scripts/a6_r6_new_families.py (+ r6_lib.py,
r6_idea1_pairs/2_lelag/3_52whigh/4_drift.py).

1. Idea 1 — Pair-trading lite (charter 1). Top-40 same-cluster pairs (corr-clustering proxy —
   NO sector metadata exists anywhere in the repo; buffett_sectors.json is a boolean map, so
   same-sector == high-126d-corr, greedy top-40, max 2 pairs/name, monthly refresh), spread
   z-score on trailing 252d (and 126d), |z|>2 enter / 0 exit, dollar-neutral. 7 configs
   (topn 20/40 x zwin 126/252 x z 1.5/2/2.5 x exit 0/0.5): **SR 0.15-0.33 net, worst year
   -8.0 to -23.4%, negYr 6-11** — ALL FAIL gate a (0.7) and gate d. Corr is tiny (+-0.02)
   and H2>H1 — the signal is economically DEAD, not mis-sized. Turnover ~1100bps/day.
   Cross-check: library StatArb_40pairs/z10/z15 on this universe are themselves SR -0.46/-0.09 —
   independent confirmation this panel has no pair-convergence premium at daily frequency.

2. Idea 2 — Lead-lag mega->small (charter 2). Big = top-50 by trailing 126d median dollar-vol,
   small = bottom-50 of hygiene-OK names; mega-move at (t-hold..t-1] gates a long small-cap book
   (liquidity-ranked or 126d corr-to-mega ranked), T+1. 9 configs: longwin h1 SR -0.06, h5 0.39;
   both-side h1 -0.77 (17 neg yrs); reverse (shorting post-mega-up smalls) -0.71 to -0.79 — the
   LAGGED edge is a small beta-trend effect, not 1d lead-lag. Best variant (corr-ranked, h10):
   SR 0.62, ann 10.1%, H1 0.38/H2 0.87, negYr 3 {2015 -19.4, 2018 -11.7, 2022 -6.8}, corrM6
   +0.36 — FAILS worst-year by 11pp and corr gate; and at h10 it has degenerated into a
   small-cap trend follower (signal sum over 10d ≈ market momentum), not a lead-lag book.
   VERDICT: no exploitable 1d lead-lag between mega- and small-caps here.

3. Idea 3 — 52w-high momentum (charter 3, r1 idea 5 rerun). CR = close/252d-high, top tercile,
   MA150 gate, VT15, monthly + weekly, EW + inv-vol, +/- mom>0 screen: 7 configs, **SR -0.27 to
   0.17, worst -27 to -32%** (2014 -29%, 2025 -11 to -16% recurring). ALL FAIL gate a and d by
   wide margins. The 52w-high anomaly is absent in this 298 mega-cap panel at monthly cadence —
   consistent with r1 (plain 12m momentum SR 0.74 but 2008 -19.7%) — proximity-to-high adds
   nothing and the MA150 gate saves nothing (2022 -7.1 to -8.7%, 2014 crashes are idiosyncratic
   book concentration).

4. Idea 4 — Earnings-drift proxy (charter 4). Annual fundamentals (7451 rows, fy 2009-2027, 501
   symbols) have NO filing dates -> PIT handled conservatively (available at FY-end + 182d).
   Names with revenue growth > 0/10/20% yoy AND near 252d high (CR>0.95), cap 40 deepest,
   monthly, MA150-gated and ungated: **SR -0.23 to 0.26, worst -17.8 to -31.8%** — ALL FAIL.
   The g>10% & CR>0.95 variant is IDENTICAL to g>10% alone (the 52w-high filter is implied by
   revenue growth here), and the no-fundamental control (CR-only) scores 0.23 — the fundamental
   overlay adds nothing on top of an already-dead signal. CAVEAT for future users of this file:
   it appears to be CURRENT constituents (501 symbols incl. names not in twelve_big) ->
   survivorship bias makes these numbers optimistic, not pessimistic; a real drift sleeve would
   need point-in-time fundamentals with filing dates (this round's crude proxy is dead either way
   — gross SR 0.55).

Post-mortem (gross-vs-net on each idea's best config): pairs gross 0.61/net 0.36 (drag 1.8%/yr),
lead-lag 0.65/0.42 (2.6%), 52wh 0.48/0.16 (0.7%), drift 0.55/0.26 (0.6%). Even GROSS, no idea
reaches the 0.7 gate — the killer is the PREMIUM (or its absence), not costs. Scramble/plateau
gates were therefore never reached on any candidate (all dead at gate a, like 22/22 configs).

Honest scorecard r6: 0/4 ideas saved; A6 has now exhausted its two assigned families
(reversal/momentum r1-r5, new-family r6) with 40+ ideas tested and 2 sleeves saved (both r2
pairs, both champion-internal). Recommendation to coordinator: A6 has no remaining in-house
families; if a further round is commissioned it should import an external-family mandate
(e.g. options-implied skew, FX carry within the 8-pair free set, or seasonality-by-name), or
accept champion-internal optimization tasks explicitly (r4/r5 recommendation stands: re-budget
the champion's A6_pair_fm leg to vt18, +~8pp champion ann at unchanged structure).
ROUND r6 DONE

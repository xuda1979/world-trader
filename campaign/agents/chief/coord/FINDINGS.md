# FINDINGS.md — chief/coord round-1 (2026-09-06)
Agent roles: HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2
CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON
All engine hunts: honest T+1, 6.4bps one-side FULL |dW| + 0.5%/yr borrow + 4.5%/yr margin on
(gross-1), vt10% trailing clip 3.0. Gates per GATES_CONTRACT (SR>=1, halves>=0.5, <=2 neg yrs
>-5%, scramble p<0.05, |corr|<0.15 vs champion).

## 1. DATA_FREDMORE — 13 PASS / 5 FAIL (fail-closed)
PASS written to tools/quant/data/more_fred/: VIXCLS(2004+,5737), T10Y2Y(1976+,12563),
T5YIFR(2003+,5924), DGS2/DGS10/DGS30, AWHAETP, CSUSHPISA, TOTALSL, IPMAN, DGORDER, USREC, HSN1F.
FAIL (not written): NROU (gaps=702 — forecast rows to 2036), LNS11300060/IRLTLT01NZM156N/
CPILFESL (1 gap each). VIXCLS pre-2004 has genuine CBOE publish holes (lint caught, refetched
from 2004-01-02). Fetcher: work_r1/fetch_fredmore.py (reuses fred_dl.fetch/lint/write_csv).
Manifest: DATA_FREDMORE/MANIFEST_R1.md.

## 2. DATA_ETF_MORE — 10 PASS / 10 FAIL (fail-closed)
PASS written to tools/quant/data/more_etf/: XLE,XLF,XLI,XLB (11-SPDR set now complete for
XLRE/XLC-era), LQD, TLT, IEF, EWH, EWM, GLD — all 2006-10-19..2026-09-04, n=5000, maxgap 5d.
FAIL (start >2007-01-01 lint bound): HYG(2007-04, 3mo past bound), EWC, EIS, TUR, DBE, EPHE,
USCI, COPX, DBP, ENOR. Manifest: DATA_ETF_MORE/MANIFEST_R1.md. Fetcher: work_r1/fetch_etf_more.py
(TwelveData free tier, 8 req/min).

## 3. HUNT_CRYPTO2 — HONEST NEGATIVE (all four families)
(a) Vol-scaled weekly crossover 12 coins, best-per-coin configs (10/30..50/150): per-coin SR(vt)
0.19-0.61; EW basket (20/60, weekly, vt): SR=0.164 ann=1.19% mdd=-30.6% 5 neg yrs (2017 -14.8%,
2019 -5.4%, 2023 -3.9%, 2026 -4.7%) → FAILS SR/halves/yearly. Scramble p=0.000 on singles is
meaningless at this SR.
(b) Daily short-term reversal (BTC/ETH/LTC, win 1-5d): best LTC_rev5 SR=0.548 (negyr=1 but
ann=1.9%, corr=-0.02); BTC_rev1 0.27, ETH_rev1 0.23. All << 1.0 → FAIL.
(c) BTC/ETH spread z-rev (20/60/120d): SR -1.05/-0.68/-0.35 → DEAD (crypto RV = momentum regime).
(d) VIX gate on BTC 30/90 crossover: SR -0.05/+0.17/+0.15 (thr 20/25/30), negyr 4-6, corr~0.00
→ FAIL (and gate kills the only decent years).
Verdict: no crypto candidate near SR>=1.0. Dead.

## 4. HUNT_CMDT2 — HONEST NEGATIVE
Universe USO,DBC,DBA,GSG,CANE,CORN,SOYB,WEAT,MOO,UNG,SLV,GLD,GDX (13 ETFs, 2006+).
(b) xs mom rank12m-hold3m top3/bot3: SR 0.212 (mom252/63), mdd -30.1%, 9 neg yrs; all 5 configs
0.03-0.21. Long-only top3: SR 0.355 (mom126/63), 9 neg yrs. FAIL.
(c) ENERGY/PRECIOUS/AGRI 6m-mom monthly rotation: SR 0.399, ann 3.77%, mdd -39.1%, 9 neg yrs → FAIL.
(d) CPI-yoy-accel gate on DBC: SR -0.188, 16 neg yrs → DEAD.
Verdict: dead. (Commodity ETF momentum post-costs is SR<0.5 at 10% vol — consistent with prior hunts.)

## 5. HUNT_MACRO2 — HONEST NEGATIVE (all four composites)
(a) Credit-cycle (BAA-AAA & HY OAS 126d trends, 21d release lag): longQQQ SR -0.06/-0.48/-0.30;
HY/IG switch on HYOAS SR -0.840 → DEAD.
(b) Activity nowcast (INDPRO+CFNAIMA3+RRSFS+PAYEMS z-avg, 42d lag): longQQQ SR -0.447 (12 neg yrs),
longDBC SR -0.062 → DEAD.
(c) Real-rate duration (DFII10 126d trend → TLT/IEF L/S): SR -0.39/-0.66 (14 neg yrs); breakeven
63d → TIP: SR -0.187 → DEAD.
(d) Liquidity (WALCL-RRP 52w z): longQQQ SR -0.328, longDBC SR -0.259 → DEAD.
Verdict: macro composites dead, consistent with prior macro hunts. (New DFII10 fetched for this.)

## 6. HUNT_FXCARRY2 — HONEST NEGATIVE (data-limited: FX spans only 2019-06..2026-08)
Carry proxy = IRLTLT01 long-rate differential (US,AU,CA,CH,GB,JP,DE; NZ unavailable — lint gap).
(a) Carry+momentum combo (5 tradable pairs): per-pair SR -0.22..+0.39 (only USD_JPY positive);
EW book SR=-0.342, 7 neg years (every year except 2022 negative) → FAIL.
(b) Real carry (CPI-deflated): EW SR=0.016 → FAIL.
(d) Vol-scaled 63d momentum, 8 pairs: EW SR=-1.000 (7 neg yrs) → DEAD.
Verdict: dead (and 6y span can't clear halves + 20y champion gates anyway).

## 7. HUNT_SECTOR2 — HONEST NEGATIVE
9 SPDR sectors (XLK..XLU, 2006+; XLRE/XLC too short).
(a) 12-1 xs momentum top3/bot3 monthly: SR -0.20/-0.06/-0.16 (13/11/13 neg yrs) → L/S DEAD
(same verdict as prior HUNT_SECTOR_FULL; costs not the issue — even gross barely >0).
(a2) Long-only top3: SR 0.295/0.362 (4/2 neg yrs) → FAIL SR gate.
(c) QQQ-200d trend gated long-only: SR 0.395, 7 neg yrs → FAIL.
Verdict: dead.

## 8. HUNT_CREDIT2 — HONEST NEGATIVE (all four)
(a) HY/IG carry sized by BAA-AAA change63 (thr 0/0.1/0.25): SR -1.30/-1.09/-0.76 → DEAD.
(b) 2s10s curve steepener/flattener via SHY/TLT (21d/63d): SR -1.12/-0.83 (19/16 neg yrs) → DEAD.
(c) Breakeven trend TIP/SHY: SR -4.25 (TIP vs SHY spread is dominated by duration noise) → DEAD.
(d) Credit-impulse (HY OAS 1y change) gated HY/IG: SR -0.327 → DEAD.
Verdict: dead. Rates/credit ETF spread engines remain negative post-cost.

## 9. CAMP_SHORT — model + TDD + impact
Research: IBKR ~0.5% GC / 2% MEDIUM / 8%+ HARD borrow tiers; bottom-decile micro-caps mostly HTB
with an un-shortable slice. Implemented campaign/bt/shortability.py: shortability_gate() drops
NONE-tier short legs (fail-closed) + tiered borrow on survivors; mcap_tier() rank mapping.
TDD: campaign/bt/tests/test_shortability.py — 5 tests (leg-drop, tier-fee math, same-day borrow
accrual, longs untouched, unknown-tier raises) ALL GREEN.
Impact: committed champion has NO single-name equity L/S slot (dualmom is long-only + index
gate) → shortability does not correct the champion. MHX (non-champion, 20-name mega-cap L/S,
ann 93.9% SR 5.20): EASY→MEDIUM tier uplift on short half ≈ 75bps/yr on sleeve — material for
any future integration re-audit; documented, committed files untouched.

## 10. CAMP_BORROW — margin/borrow audit + stress
Champion margin verified: 4.5%/yr charged on exactly (1.6-1)=0.6 gross → 2.70%/yr drag
(4.5%/252*0.6/day = 0.00010714/day). IBKR-reasonableness: fed funds + spread — 4.5% fair;
stress table (recomputed from builder internals):
  4.5%: ann 40.84% SR 3.339 MDD -6.80%
  5.5%: ann 40.00% SR 3.281 MDD -6.81%
  6.5%: ann 39.16% SR 3.224 MDD -6.82%
→ each +1pp call rate ≈ -0.84pp ann; goal-irrelevant but noted.
Borrow: 0.5%/yr charged inside pool sleeve files per standard; only dualmom has an equity-type
short exposure (index-gated). HTB tier 5% on its short frac ≈ 10.6bps/yr champion-level — immaterial.

## 11. CAMP_COST — full-|dW| audit of every builder
1. rawew13v2_build.py (LIVE): charges FULL |dW| * 6.4bps — verified by re-run (--verify IDENTICAL,
   max|new-old| 9.996e-17; charged-turnover==full-|dW| test green) + sha256 champion
   0516e543615c0fc6, weights 8107aab3bb33fd6f.
2. Half-turn offenders found (grep '0.5*'):
   - campaign/scripts/QA_dualmom_band121.py:63 `0.5*(neww-prev).abs().sum()` — dualmom IS a
     committed champion slot (relw 0.994, share 6.38%). Sleeve-level undercharge est. ~24bps/yr
     on that sleeve book → ~0.1bps/yr champion-level (slot-scaled) — immaterial but a real
     convention violation, flagged for the re-emit wave.
   - campaign/scripts/champion_build.py + e1_champion20y_build.py: 0.5*sum|dW| + 0.5*|dsc| —
     SUPERSEDED builders (not on the committed chain); flagged archived.
   - loop_team/HUNT_BASIS2/scratch/lib.py: `pos.diff().abs()/2.0` half-turn — diescrack is a
     committed slot (share 9.5%); est. undercharge ~22bps/yr sleeve-level → ~2.2bps/yr
     champion-level. Flagged for re-emit.
3. Vol-target/throttle: champion has NO separate vt/throttle streams — all rebalancing flows
   through Wg (NAV-drift), charged by the same full-|dW| term. No free rebalances.
4. TDD: test_camp_cost_full_dw.py extended (no-live-builder-half-turn + offender-set pin).
   Suite: 51 passed, 1 xfailed.

## 12. AUDIT_FWBUGS — 2 real bugs found + fixed (TDD RED→GREEN)
BUG-1 reconcile.turnover_reconciles: compared ledger qty vs pos.diff() — dropped day-1 entry
notional while engine.cost_turnover (R1 fix) CHARGES it → compliant ledger falsely failed.
Fix: seed prev row with zeros (matches engine semantics). RED: test failed → GREEN.
BUG-2 metrics.neg_years: pandas (1+x).prod() skips NaN → all-NaN year returned 0.0% and did NOT
count negative (fail-open). Fix: prod(min_count=1) + non-finite year counts as -1 (fail-closed).
RED: neg=1 on NaN-year fixture → GREEN: neg=2.
Post-fix suite: 51 passed, 1 xfailed (was 43 baseline → +8 tests).
Also probed: cap_leverage NaN/under-levered rows (no inflation bug — verified numerically),
vol_target_scale NaN propagation (clean), scramble length-mismatch raises (fail-closed OK).

## 13. AUDIT_RECON — integrity report
(a) Byte-repro: rawew13v2_build.py --verify IDENTICAL (max dev 9.996e-17 net, 2.22e-16 weights;
    n=4805 both; sha256 champion 0516e543615c0fc6 / weights 8107aab3bb33fd6f).
(b) Costs: turnover charged == FULL |dW| (day-1 seeded): max diff 0.000e+00; window turnover
    0.018 bps/day; margin 0.00010714/day; gross 1.600000 (max dev 1.11e-15, 0 days >1.6).
(c) **FINDING (overstatement, immaterial to gates): same-day NAV-drift weights.** Wg_t is built
    from nav_t=cumprod(1+r)_t which contains r_t, then earns Wg_t*r_t → the weight path partially
    uses the same day's returns (deviation per slot up to 0.0263). Fully-causal recomputation
    (weights = Wg.shift(1); verified max|Wg_lag − Wg.shift(1)| = 0.0):
    ann 40.84% → 39.85% (−0.99pp), SR 3.339 → 3.296, MaxDD −6.80% → −6.84%, 0/19 neg years BOTH,
    worst year +8.89% → +8.61%. Every constraint gate still passes; goals unaffected (still far
    from ann80/SR5). Documented as xfail test test_champion_portfolio_return_uses_lagged_weights_
    auditrecon; committed champion CSV NOT modified (per instructions — coordinator decision on
    re-emit wave).
(d) 60-day window reconstruction: portfolio − turnover*6.4bps − margin == committed net with
    max diff 1.084e-19 (algebra reconciles exactly).
(e) Shortability: no single-name L/S slot in champion (see CAMP_SHORT) → no overstatement of
    that class; MHX-type books carry a flagged 75bps/yr borrow-tier risk if ever integrated.

## ROUND-1 VERDICT
- 6/6 engine hunts: HONEST NEGATIVE — no candidate cleared SR>=1.0 (best single-config: crypto
  LTC_rev5 SR 0.55, cmdt sector-rot SR 0.40; all fail halves/yearly/scramble or span).
- Data: +13 FRED, +10 ETF series linted PASS (manifests saved).
- Framework: +2 bugs found & fixed RED→GREEN; +1 champion finding (same-day NAV-drift weights,
  -0.99pp ann when made fully causal; documented xfail, champion untouched); +2 slot-level
  half-turn cost conventions flagged (dualmom ~0.1bps/yr, diescrack ~2.2bps/yr champion-level).
- New reusable asset: campaign/bt/shortability.py + 5 TDD tests (borrow tiers, fail-closed).
- bt suite: 51 passed, 1 xfailed (baseline 43).
ROUND 1 DONE

====================================================================
HUNT_CREDIT2 ROUND 2 (2026-09-07) — all four charter engines DEAD
====================================================================
Repro: campaign/scripts/HUNT_CREDIT2_round2.py + _gate.py + _gate2.py; TDD 4/4 green
(work_r2/test_credit2_r2.py); bt suite 148 passed. Sleeve CSVs + .meta in
HUNT_CREDIT2/sleeves/ (3 files, fail-closed diagnostics inside). DEAD_IDEAS.csv rows appended (80->84).
Charter pre-authorized substitution for (d): FRED BAMLH0A0HYM2 serves 2023-09-05+ only (787 rows,
verified with observation_start=1996-12-31; aliases BAMLH0A0HYM2EY/BAMLHE00EHYIOAS/BAMLH0A1HYBB
all 2023+), champion window is 2008-03-31+ -> used BAA10Y (1986+, same credit-stress spread
minus the AAA leg's rate content). True HY OAS gives 15/4805 gated days on the overlap = unjudgeable.

(a) LQD-TLT credit-spread momentum k=126 (a-priori), +1/-1 dollar, VT10%, 6.4bps+borrow:
    SR=-0.31 (gross +0.01 — signal has NO alpha before costs), ann=-4.2%, H1=-0.24 H2=-0.44,
    13 negyr worst=-32.7%, scram_p=0.000 (kills it from the other side), corrChamp=0.142 (the
    ONLY gate it passes), SR_08+=-0.17. k-scan 63/-0.24 126/-0.31 252/-0.17 -> plateau FAIL
    (nonpositive_peak). Post-hoc sign-flip (banned for adoption, run to kill the idea both
    ways): SR=-0.33. DEAD.
(b) T10YIE 63d breakeven trend, TLT/TIP monthly tilt, extra publish-lag day:
    SR=-0.80 (gross -0.40), ann=-9.7%, H1=-1.10 H2=-0.45, 21 negyr worst=-35.3%, scram_p=0.000,
    corrChamp=-0.050. k-scan 21/-1.21 63/-0.80 126/-0.44 252/-0.25 all negative. Flipped +0.09
    still fails SR>=1.0. DEAD.
(c) 2s10s (T10Y2Y) steepener, IEF/TLT 0.5/0.5 barbell, k=21 (a-priori):
    SR=-0.54 (gross +0.07), ann=-5.1%, H1=-0.59 H2=-0.50, 21 negyr worst=-17.9%, scram_p=0.000,
    corrChamp=-0.128. k-scan 5/-1.38 10/-0.93 21/-0.54 42/-0.45 63/-0.38 all negative. Flipped
    -0.64. DEAD.
(d) HY-stress gate overlay (0.7x champion when BAA10Y 252d trailing z>2) — LOOKED live:
    champion SR 3.296 -> 3.494, delta=+0.198, 323/4805 days gated. Killed by adversarial controls
    (scripts/HUNT_CREDIT2_round2_gate2.py) — the delta is CONTENT-FREE, not credit:
      * N x z_thr plateau (delta objective): +0.198..+0.254 everywhere = parameter-insensitive,
        i.e. generic de-levering, not a stress threshold. Lag T+1..T+10 stable (+0.19..+0.22).
      * Era split: 2008-12 +0.046 / 2013-19 -0.064 / 2020-26 +0.295 -> COVID-concentrated.
      * Gated days carry champion ann returns +66.1% (08-12), +59.5% (13-19), +201.8% (20-26);
        59% of gated days are champion POSITIVE days, mean +39bp/d. A real stress gate should
        fire on losses. Net cumulative return contribution of the gate = -0.38 (it GIVES UP
        3.8pp of return); the SR gain is purely variance-outlier suppression.
      * Concentration: 85% of gated-day variance sits in 22 positive-outlier days; top-6 |contrib|
        days are all Mar-Apr 2020 champion WINS (+18.31% z=7.0, +14.42% z=7.0, +5.91%...).
      * GENERIC CONTROL (kills it): champion's own trailing 252d realized-vol z>2 -> 0.7x (same
        machinery, ZERO credit content) gives delta +0.224 > credit gate's +0.198. Vol-matched
        CONSTANT 0.93x scale gives delta 0.000 (SR is scale-invariant) -> the entire +0.198 is
        non-uniform de-levering of the biggest WIN days. Credit information adds NOTHING
        (credit delta < content-free control). Other credit indicators same machinery:
        DAAA +0.157, DBAA +0.168, BAA10Y +0.198 — spread across the rate complex, again
        consistent with a generic vol effect, not HY-specific stress.
      * ANTI-gate (z<-2 -> 0.7x on the calmest days) delta -0.006: firing on calm days does
        nothing; the effect is entirely WHERE the outlier days sit, not what credit is doing.
      * Scramble 200x (gate values permuted, count preserved): p=0.000 — note this PASSES
        because permuting a 0.7x/1.0 mask across 4805 days still de-levers whatever big days it
        lands on (delta_real +0.198 vs scrambled mean ~+0.18, CI [+0.02,+0.31], P(delta<=0)=1.7%
        by day-iid bootstrap). Statistical nonzero-ness is NOT economic content: the control in
        the previous bullet is the decisive one.
      * Costs: 105 on<->off transitions * 0.3*1.6 gross * 6.4bps = 17.5bps/yr — small; the gate
        is not a cost artifact, it is a vol artifact.
      * Verdict: applying ANY 0.7x/1.0 state mask to a book whose SR comes from compounding a
        few huge up-days mechanically raises SR by trimming the variance of the wins. This is
        the same champion-whitening illusion documented in round 1 (VXV/VIX term overlay,
        max dSR -0.29 dead ledger). NOT adoptable; champion untouched.

Round-2 conclusion: credit & rates-spread domain is now exhausted on available instruments —
ETF spread momentum (a), breakeven trend (b), curve barbells (c) all have gross SR ~ 0
(+0.01/-0.40/+0.07), i.e. no alpha exists pre-cost to even pay for itself, and the one
apparent win (d) decomposes to a content-free vol artifact. Champion
GOAL100_RAWEW13v2_WEIGHTED_GEAR16 (ann 39.85%, SR 3.296, maxDD 6.8%) untouched.
No round-2 sleeve passed any gate combination. Honest negative.
ROUND 2 DONE

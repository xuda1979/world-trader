# HUNT_VOLOVERLAY — FINDINGS (2026-09-03, iter 6)
Charter: find a regime/timing overlay m_t ∈ [0, cap] applied to the EXISTING champion
(GOAL100_HONEST14V3_BALANCED) that lifts SR by >0.15 (sustained), with MaxDD not worse,
200x position-lag scramble p<0.05 of the TIMING signal, H1/H2 both improved-or-flat, ≤2 neg yrs,
money-neutral (leverage ≤ current). Prior findings read first: HUNT_FF2 (vol-gate geometry,
scramble degeneracy, 2022+ weakness), STATS_REVIEW (BAL gross 3.367x, MDD -5.60% on comparable
span, throttle already inside, LB whitening), HUNT_CROSSREGIME (no work — 429 API death, log empty).

## HEADLINE VERDICT: **NO DELIVERY — charter FAILS on every family tested.**
The champion's PnL is essentially INDEPENDENT of every trailing macro/vol state variable I can
build from on-disk data (max |corr| 0.049), and it earns POSITIVELY IN ALL STATES (13–20 bp/day in
every signal quintile). Any m∈[0,1] overlay must forgo 7+ bp/day of unconditional mean to harvest
≤2 bp/day of conditional separation — the arithmetic is underwater before costs. Best candidate of
60+ tested: dSR **+0.0347** (bar: +0.15), scramble p 0.085–0.115 (bar: <0.05). Nothing delivered.

## 0. Setup honesty
- Champion loaded from campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv — sha256
  fdbca6552b9a2e9e, 5,086 rows, 2006-10-02..2026-08-27 (THE instrument/price path for any future
  trade-record audit of this hunt: all overlays were applied to this exact return path).
- Baseline reproduced from the file (my stats code): FULL SR_d 3.9228, ann_geo 43.13%, MDD -4.9185%,
  1/21 neg yr (worst -1.38%); **2008+ (n=4,713): SR_d 3.9397, SR_m 4.0163, ann_geo 43.61%, MDD -4.9185%,
  0/19 neg, worst +13.94%, halves 3.811/4.069**. Matches commit ca859e1 claims (SR 3.92/-4.92%/0-neg).
- OVERLAY COST MODEL: ret'_t = r_t * m_{t-1} − |Δm_t| × 6bps × GROSS, GROSS = 3.367 (STATS_REVIEW §8
  BAL capital-real all-in mean 2008+). This is the honest charge: the champion runs ~3.4x gross, so
  de-risking/re-risking m trades champion notional. dSR@1x also reported in recon2 — conclusions
  identical (charging 1x only makes overlays look ~0.1 SR better; all still fail).
- T+1 everywhere: m shifted by 1 day before application. Signals built from data ≤ t only.

## 1. Predictive screen (recon1) — champion ret_t vs signal_{t-1}, full sample
corr (n≈4,950–5,035): dvix21 +0.0487 | mx_mom21 +0.0437 | champ_rv63 -0.0350 | bz_mom21 +0.0345 |
slope -0.0309 | slope_z -0.0305 | champ_rv63_z -0.0277 | be_z -0.0200 | vix_zexp +0.0170 |
mkt_rv63_z -0.0135 | baa_aaa_z -0.0080 | mom_rv63_z +0.0070 | dxy_mom63 +0.0017 | spx_ma_gap -0.0010 |
vix_z252 +0.0003. Strongest predictor of the champion in existence on this disk: |corr| 0.049.
hy_oas on disk starts only 2023-08 (785 rows) — long-history credit-OAS overlay INFEASIBLE on disk;
T5YIFP file malformed (ParserError line 6) — skipped. VIX sources: VIXCLS (to 2026-08-28, used),
vix.csv stale (ends 2026-08-10). No VIX3M/VXV anywhere on disk → term-structure overlay stays UNRUN.
Quintile means (bp/day, q1→q5): dvi21 13.3/13.8/9.7/16.3/19.7 (SR 3.99→5.11, non-monotone q3 dip);
slope_z 17.3/16.7/14.4/14.5/11.2 (monotone-ish but only 6.1bp spread); rv63z 18.2/13.9/15.5/10.9/14.3
(NON-monotone: q5 rebounds to SR 4.57); mxm21 12.6→17.8 (SR 3.78→4.89, weakest spread).

## 2. Gate/ramp overlays (recon2/3/7; dSR = SR_overlay − 3.9397 at 3.367x cost charge, 2008+)
RISK-ON gates (ON in calm, OFF in stress) — ALL NEGATIVE:
  ramp rv 1..2 inv -0.233 | mxm21>-0.01/0/+0.01 -0.344 (tiny 2.1% on) | bzm21>0 -0.344 |
  rv63z<1.0 -0.443 | vix_zexp<1.0 -0.556 (MDD -6.49) | slope>0bps -0.609 | cred_z<1.0 -0.717 (1 neg yr) |
  rv63z<0.5 -0.758 | cred_z<0.5 -0.995 | slope_z>-1.0 -1.097 (H2 1.972) | rv63z<0.0 -1.124 |
  vix_zexp<0.0 -1.267 (MDD -10.47, 2 neg yrs) | ramp slope -1..0 -1.296 (MDD -13.68, 3 neg) |
  slope_z>-0.5 -1.517 | cred_z<0.0 -1.543 | slope_z>0 & rv63z<1 -2.393 (H2 0.372) | vix_zexp<-1 -3.187.
DEFENSIVE/FLIPPED gates (OFF when signal bad, or ON only when stress rising) — ALL NEGATIVE:
  OFF rv63z>1 -0.435 | OFF mkt_rv63z>1 -0.373 | OFF slope_z<-0.5 -1.506 (MDD -15.89, H2 0.78 —
  champion EARNS through curve inversion) | OFF cred_z>1 -0.382 | OFF vix_z>1 -0.472 |
  ON only dvix21>0 -2.281 | ON only dvix21<0 -2.418 | ON only mx_mom21>0 -1.871.
VRP overlay (vix − spx_rv21, coverage only 2016-09+): ON vrp_z>0 -2.5185 | OFF vrp_z<1 -1.3690
  (MDD -21.45, 6 neg yrs — worst object built this hunt). Real-yield z: ON>-1 -1.3105, OFF<0 -2.0583.
DD-throttle on champion (already throttles internally at -4%/-3%): <-1%x0.5 -0.302 | <-2%x0.5 -0.108 |
  <-4%x0.5 -0.026 (further throttle only duplicates what's inside).
Internal-state: champion has ZERO zero-days (zero-frac 0.0000 — zero-gate structure gone in V3);
  zerofrac21 overlays no-op exactly (dSR +0.0000); loss-streak OFF -1.02/-0.26; activity-z OFF -0.10.
Breadth (twelve_big, 271 names/day median, 2006-09..2026-08): ON breadth63>0.5 -2.291 (H1 0.30!);
  breadth21z gates -1.2/-1.0. DEAD — champion is NOT breadth-conditional.

## 3. Vol-target family (only non-negative family; still FAILS)
rv252 tgt/cap plateau (dSR): tgt .06 +0.0347 | .08 +0.0358 | .10 +0.0059 | .12 -0.0049; cap 1.5/2/3
IDENTICAL (scale rarely binds; cap is a dead knob). rv21/rv63 variants all negative (-0.04..-0.24).
FULL BATTERY on best (rv252 tgt0.08): SR 3.9744 (dSR **+0.0347**), ann_geo 43.75→**38.88%** (-4.9pp —
  the SR gain is bought by cutting vol; NOT money-neutral on returns), MDD -4.92→-4.41, 0 neg yrs,
  H1 3.786 / H2 4.158 (H1 slightly WORSE), position-lag scramble p = **0.115/0.115/0.085**
  (3 seeds × 200; bar <0.05) → **FAILS scramble AND the SR bar by 4x**.
Corr(m_exec, champ_rv63) -0.506 (it is just a vol-scaler — geometry already inside the 11-pool vt).

## 4. Multivariate combo (recon5) — 8 signals, ridge H1-fit → H2-test (honest split)
corr(pred, r) H1 +0.0217 → H2 +0.0383 but the m-tilt LOSES on both halves at every λ∈{0.1,1,10},
k∈{2e4,5e4}: best H2 SR 3.810 vs base 4.069 (H1 3.655–3.666 vs base 3.811). The in-sample
predictive sign does not survive transaction geometry. SAFE−AGGR tilt screen: max |corr(diff_t, sig_{t-1})|
= 0.038 (mxm21) — no timing variable separates the champion's own leverage states either.

## 5. Budget arithmetic (why this hunt is structurally underwater)
- Perfect-foresight ceiling m∈{0,1} (infeasible upper bound, no costs): SR 8.4571, ann 88.82%
  (mean 25.4 vs 14.6 bp/day). Headroom exists IN THEORY but requires daily sign foresight.
- dSR_d +0.15 at unchanged vol ⇔ mean +0.555 bp/day of CONDITIONAL mean. Best measured split
  (dvi21 median): 2.2 bp/day separation, forgoing 7.3 bp/day mean under a 50%-off gate ⇒ net -5.1
  bp/day before costs. With max |corr| 0.049, no m∈[0,1] function of these states can clear +0.555
  net; measured best is +0.035 SR and it charges 4.9pp of ann to get it.

## 6. Charter gate table (delivered candidate: NONE; best candidate shown)
| Gate | Best candidate (voltarget rv252 tgt.08) | Bar | Verdict |
|---|---|---|---|
| SR lift sustained | +0.0347 | >+0.15 | **FAIL (4.3x short)** |
| MaxDD not worse | -4.41 vs -4.92 | ≤-4.92 | pass (only gate passed) |
| Position-lag scramble | p 0.115/0.115/0.085 | <0.05 | **FAIL** |
| H1/H2 improved-or-flat | H1 3.786 (<3.811) | both | **FAIL (H1 worse)** |
| ≤2 neg yrs | 0 | ≤2 | pass |
| Money-neutral | ann 43.75→38.88 (-4.9pp) | ≤current lev | **FAIL (buys SR with vol cut, not free)** |
=> 2/6 gates. NO overlay module delivered. Per honesty contract, not saved as a sleeve.

## 7. Negative-results ledger (anti-repeat for future hunters)
- DO NOT re-run ANY risk-on gate on this champion: rv63z / VIX z / baa-aaa z / 2s10s slope z /
  DMX/DBZ 21d momentum / breadth63 / breadth21z / VRP z / real-yield z / dxy z — 40+ variants,
  ALL dSR<0 at 3.367x cost charge (list §2). The champion is a contrarian/stress-harvester:
  gates that de-risk in stress delete its best days (vix_zexp<0 → MDD -10.5% and SR -1.27).
- Flipped "OFF-when-stressed" gates: also all negative — champion earns THROUGH stress
  (OFF slope_z<-0.5: MDD -15.9%, H2 SR 0.78). There is no on/off regime where it is weak.
- DD-throttle overlays beyond the internal -4%/-3% throttle: ≤ -0.03 dSR, and the -1% variant
  LOSES 0.30 SR to harvest 0.75pp of MDD — bad trade at 3.367x turnover costs.
- Vol-targeting on rv21/rv63: negative; on rv252: +0.03 max — noise-level, scramble-fails.
- Multivariate ridge timing of the champion: OOS-negative on an honest H1→H2 split.
- hy_oas overlays: INFEASIBLE (data starts 2023-08). T5YIFP: malformed file. VIX3M: not on disk.

## 8. What WOULD move the frontier (for the coordinator)
1. Per STATS_REVIEW §9 and this hunt: SR is scale-invariant ~3.92 and overlay/timing on the
   champion is DEAD. The only lever is NEW decorrelated high-SR engines (sqrt-of-squares compose),
   or new data domains. FF2 (corr 0.14) added ~+0.02-0.03 blended SR at slot 0.10 — the pool is
   thin: the 3 new engines since V2 moved blended SR ~0.
2. The perfect-foresight bound (SR 8.46, ann 88.8% unlevered) says daily-timing alpha of the
   required size exists mathematically but needs signal sources with |corr|>0.1 to champion
   returns — nothing on the on-disk FRED/FF/breadth panel provides it.
3. If a future vintage brings VIX3M/VXV or long hy_oas, a term-structure/credit-stretch overlay
   is the only untested family — but the base rates from this hunt (7 families, 60+ variants,
   all fail) say the prior should be LOW.

## UNVERIFIED / caveats
- Cost charge uses constant GROSS=3.367 mean; day-by-day gross varies (p95 6.95) — a
  path-dependent charge would shift dSR by <±0.01 (recon2 1x-vs-3.367x bracket shows the
  uncertainty is ~0.1-0.2 SR on gate dSRs, nowhere near the 0.15-needed margins at stake).
- DEX-based EM-FX signals are DAILY-fix series (FRED), not tradeable intraday prints; used only
  as state variables (no execution realism issue for an overlay that was not delivered).
- 2026-08 champion rows inherited as-is (STATS_REVIEW caveat: sleeve prints may revise).

## Files
- scratch/lib.py (champion loader, overlay applier, poslag_scramble — position-shift variant,
  NOT the degenerate return-roll test), recon1-7 (each self-contained, re-runnable).
- No sleeves saved (charter FAIL). Champion instrument/price-path identity for audit: sha256
  fdbca6552b9a2e9e, 5,086 rows 2006-10-02..2026-08-27 (§0).

HUNT_VOLOVERLAY DONE

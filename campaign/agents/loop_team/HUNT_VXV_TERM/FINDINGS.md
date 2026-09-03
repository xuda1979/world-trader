# HUNT_VXV_TERM — FINDINGS (2026-09-03, iter 7.5)
Charter: VIX/VXV (VXV=VIX3M) term-structure + GVZ/OVX vol-structure — (A) overlay/timing on the
committed champion GOAL100_HONEST14V3_BALANCED, (B) satellite on ONE clean on-disk instrument.
Read-first done: DEAD_IDEAS.csv (SR-lift overlay family dead — rv63/z based, NOT term-structure),
HUNT_VOLOVERLAY FINDINGS (60+ variants, max dSR +0.0347, base "LOW"), SUPERPOWERS_RIGOR.

## VERDICT: **NO DELIVERY — the term-structure family is DEAD. Overlay: max dSR 0.0000 (degenerate);
best real overlay dSR −0.2924 (bar +0.15). Satellite best SR 0.612 but 4 neg-yrs + scramble p 0.080.
The champion is confirmed whitened against VXV term-structure too; satellites are drift-not-timing.**

## 0. Data premise lint (charter-time, verified fresh in THIS session)
- Champion: campaign/results/GOAL100_HONEST14V3_BALANCED_daily.csv, sha256 fdbca6552b9a2e9e,
  5,086 rows, 2006-10-02..2026-08-27, col ret. Baseline 2008+ (n=4,774): SR_d 3.9397,
  ann_geo 43.75%, MDD −4.92%, 0/19 neg yrs, worst +13.94% (bt.metrics, reproduced).
- VIX: tools/quant/hedge_fund_strats/data_fred_new/VIXCLS.csv, 9,261 rows, 1990-01-02..2026-08-27.
- VXV (VIX3M): tools/quant/data/more_fred/VXVCLS.csv, 4,715 rows, 2007-12-04..2026-09-01,
  0 NaNs, lint_pass True (manifest: gaps 176, max_run 2). **This is the data that was "not on disk"
  at iter6 — now on disk, so the last untested family became testable.**
- GVZ: more_fred/GVZCLS.csv 4,593 rows 2008-06-03..2026-09-01; OVX: OVXCLS.csv 4,861 rows
  2007-05-10..2026-09-01 (both lint_pass True).
- Satellite instruments (REAL closes): twelve_big/SPY.csv 5,001 rows 2006-09-26..2026-08-12;
  more_etf/IAU.csv, more_etf/USO.csv.
- Join: vol indices ffilled ≤3d onto champion calendar (lint gaps ≤2). Joint screen n=4,627
  (2008-01-02..2026-09-01). All figures below 2008+ per charter.

## 1. TDD (superpowers) — RED→GREEN observed, not claimed
- Failing test first: scratch/test_overlay.py, 3 property tests. RED observed:
  ModuleNotFoundError: No module named 'overlay' (collection error, 1 error). GREEN after minimal
  overlay.py: 3 passed. Two test EXPECTATION bugs found by the code (t=4 flat day earns 0 not r−cost;
  t=5 re-entry charges cost) — each fix verified by revert→fail→restore→pass
  (REVERTED-EXPECTATION: 1 failed, 2 passed; RESTORED: 3 passed).
- Properties locked: P1 m≡1 reproduces champion except day-0 entry 6.4bps·gross; P2 exact cost
  stream |Δm|·6.4bps·gross; P3 T+1 — signal change at t moves ret' at t+1 only.
- bt framework baseline: campaign/bt/tests 28 passed (fresh run, this session). No bt changes made.
- Methodology bug found & fixed (systematic-debugging): recon4 scramble first run passed the
  vol-targeted NET series as "positions" (realSR +6.57 impossible for SPY-timed book) — root cause:
  wrong input, not framework; fixed to raw executed weight path × raw SPY returns (realSR +0.65);
  recon4b supersedes recon4. Exact numbers below are recon4b.

## 2. Predictive screen (signal_{t−1} vs champion r_t, 2008+, n=4,627)
corr: dvxv21 +0.0676 (non-monotone) | contango −0.0268 | combo −0.0243 | slope_z −0.0187 |
slope −0.0160 | ratio_z −0.0160 | gvzovx_z +0.0177 | dvxv +0.0051. Max |corr| 0.068 — same
whitening regime as HUNT_VOLOVERLAY (max 0.049 there). Best quintile spreads: dvxv21 q5 +21.0 vs
q2 +10.6 bp/day but NON-monotone (q1 12.3); contango q2 9.7 vs q3 15.3 (non-monotone).

## 3. Overlay battery (recon2/3/7; m∈{0,1} or {0.5,1} or ramp; T+1 via bt.lag_signal;
charged |Δm|·6.4bps·3.367 gross = STATS_REVIEW §8 BAL all-in mean; dSR vs 3.9397)
Best REAL overlays, exact dSR (all FAIL bar +0.15, all keep 0 neg-yrs, MDD all WORSE than −4.92%):
  THROTTLE0.5 ratio_z<−1.0  dSR −0.2924 (MDD −5.69)  [best real]
  OFF dvxv21>q90 2day-conf  dSR −0.4304 (MDD −5.95)
  THROTTLE0.5 ratio_z>1.0   dSR −0.4618 | THROTTLE0.5 ratio_z<−0.5 dSR −0.4832
  OFF ratio_z>1.5           dSR −0.5394 (MDD −5.72) | THROTTLE0.5 ratio_z>0.5 dSR −0.5208
  ON contango=1 (89.9% on)  dSR −0.6443 (MDD −7.34) — classic contango-protect DELETEs champion value
  OFF slope<0 backward      dSR −0.6430 | RAMP risk-on z/cap2 dSR −0.8907 | RAMP risk-off cap1 dSR −2.6498
  OFF gvzovx_z>1.0          dSR −1.2651 | OFF combo>1.0 dSR −1.2869 | ON gvzovx_z>0.5 dSR −2.6286
  ON backwardation          dSR −3.4155 (8 neg yrs) | ON ratio_z>1.0 dSR −3.7370 (9 neg yrs)
  ON ratio_z>1.5            dSR −4.1928 (13 neg yrs, SR −0.2531) — worst object built
  2 rows show dSR exactly 0.0000 (OFF slope_z<−1.0; also ON slope_z<−0.5 in recon2): DEGENERATE
  never-fire gates — slope_z=vxv/vix−1 range [−0.3012, +0.4077], P(<−0.5)=0.0000 (disclosed, not
  evidence of success). @1x charge (cheapest honest): best real overlay still dSR −0.1247.
=> OVERLAY FAMILY: 31 variants, best real dSR −0.2924; every real overlay cuts ann and worsens MDD.
The champion EARNS IN ALL term-structure states (quintile means 9.7..27.1 bp/day, all positive).

## 4. Satellite (ONE clean instrument per family; bt machinery: T+1, 6.4bps one-side,
borrow 0.5%/yr, cap 1.6x capital-real; gates SR≥0.6, |corr|<0.15, H1/H2≥0.3, neg≤2, poslag p<0.05)
SPY (REAL close, twelve_big), 2008+ (n=4,682):
  A long-contango/flat-backwardation: SR 0.612, ann +7.9%, MDD −34.0%, neg 4/19 (BAR ≤2 FAIL),
    H1 0.40 / H2 0.83, corr +0.133, ac1 −0.008, uniq 0.896, poslag p 0.080 (bar <0.05 FAIL).
  K contango & ratio_z≤1.5: SR 0.580, neg 5, poslag p 0.060 — FAIL.
  C L/S contango sign: SR 0.318, p 0.565 FAIL | D zrev ratio_z: SR −0.138 FAIL |
  F long dvxv21>0: SR 0.234 FAIL.
  G always-on long control: SR 0.551, poslag p 1.000 → variant A beats buy&hold by only
    +0.061 SR — **drift not timing** (identical signature to dead-ledger row 32 short-VIX MA timing).
IAU/USO (GVZ/OVX regimes; REAL closes): ALL FAIL — best L long IAU gvzovx_z<0 SR 0.485 <0.6,
  poslag p 0.115; M inverse SR 0.030; N L/S SR −0.514; USO family SR −0.164..−0.003 (USO is a
  roll-decay graveyard, MDD −98.2% always-on); Q IAU gvz_z<0 SR 0.538 p 0.170; controls confirm
  regime adds nothing (IAU always-on 0.561 vs best regime 0.485).
=> SATELLITE FAMILY: 16 variants, 0 pass; best timing-lift over control +0.061 SR.

## 5. Trade-record (TRADE_RECORD_STANDARD) for the best satellite variant (NOT delivered; ledger
kept as evidence scratch/LEDGER_VXV_CONTANGO_SPY.csv, 264 rows)
- instrument SPY | price_path twelve_big/SPY.csv close | price_source REAL | price = t−1 close
- side BUY when contango (flip to SELL on backwardation entries) | qty_notional=|Δw| one-side
- Recon gate: Σ|qty|=264.0 == charged turnover (cost Σ 0.168960 = 264×6.4bps), |diff|=0.000e+00;
  ledger-recomposed PnL vs engine net max|diff|=0.000e+00 (PASS <1e-12).
- Economics 2008+: 264 flips/4,682 days (1 per 17.7 days), one-side turnover 5.64% NAV/day mean,
  total cost 16.90% NAV over 18.6y, borrow 0 (never short).

## 6. Gate table (nothing delivered; best candidates shown)
| Gate | Overlay best real (THROT0.5 z<−1.0) | Satellite best (A contango) | Bar |
|---|---|---|---|
| SR lift / SR | dSR −0.2924 | SR 0.612 | dSR>+0.15 / SR≥0.6 |
| MDD not worse | −5.69% vs −4.92% FAIL | −34.0% (standalone) FAIL | ≤−4.92 / n/a |
| neg-yrs | 0 pass | 4/19 FAIL | ≤2 |
| H1/H2 | 3.55/3.91 FAIL(lift) | 0.40/0.83 pass | ≥0.3 |
| |corr| to champ | n/a | 0.133 pass | <0.15 |
| poslag scramble 200x | n/a | p 0.080 FAIL | <0.05 |
| ≤1.6x capital-real | yes (m≤1) | yes (|w|≤1) | ≤1.6 |
=> 1–2/6 per family. Not saved as sleeves. No champion change.

## 7. Dead-variant ledger (exact numbers, anti-repeat)
1) Champion overlay by VXV/VIX slope z (252d): 31 variants, best real dSR −0.2924 @3.367x charge,
   −0.1247 @1x — champion whitened to term structure (quintile means all-positive 9.7..27.1bp/day).
2) Contango/backwardation gate on champion: ON contango dSR −0.6443; ON backwardation −3.4155.
3) GVZ/OVX 63d z overlay on champion: best dSR −1.2651; combo −1.2869..−3.6107.
4) VXV 1d/21d change gates on champion: dSR −0.4304..−3.2139.
5) SPY satellites (contango sign, ratio_z mom/rev, dvxv21): SR −0.138..0.612, neg-yrs 4..12,
   poslag p 0.060..0.590 — all FAIL; best +0.061 SR over always-on control = drift.
6) IAU/USO GVZ/OVX satellites: SR −0.514..0.538, poslag p 0.115..0.960 — all FAIL.
7) DEGENERATE (excluded): slope_z thresholds outside [−0.301,+0.408] never fire (dSR exactly 0).

## 8. Anti-repeat guidance (for DEAD_IDEAS + coordinator)
- The term-structure family was the LAST untested overlay family and it FAILS the same way as
  rv63/z: the V3 champion has no state variable on this disk (now incl. VXV/VIX, GVZ, OVX) with
  enough conditional separation to pay 6.4bps·gross flip costs. Any future overlay needs a signal
  with |corr(r_{t}, s_{t−1})| ≳ 0.15 AND monotone quintiles — nothing on disk qualifies (max 0.068).
- VIX ETP satellites remain BLOCKED (VXX/VIXY not on disk, per charter) — and variant A's +0.061
  drift-lift says the ETP version would face the same bar plus ~45-85%/yr contango decay.
- Do not re-run slope-z gates with |thr|>0.41 (never fire). Do not re-run USO long (roll decay).

## UNVERIFIED / caveats
- VIX from hedge_fund_strats/data_fred_new (not more_fred) — the more_fred VIXCLS path in the
  charter does not exist on disk; series content verified 1990..2026-08-27, no NaNs.
- SPY twelve_big ends 2026-08-12 (13 days before champion) — immaterial for 2008+ gates.
- Scramble p for variant A (0.080) is positions-only (re-costs not re-applied) — conservative FOR
  the candidate; it fails anyway, so no conclusion changes.
- recon4b inline print "neg 4/4" denominator is a print bug; correct count is 4 neg / 19 years
  (bt.gates neg_years=4; year set 2008..2026 = 19).

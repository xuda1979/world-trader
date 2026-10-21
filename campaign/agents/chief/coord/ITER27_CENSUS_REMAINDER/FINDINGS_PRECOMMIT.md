# ITER27 PRE-COMMIT - CENSUS REMAINDER CLOSURE (2026-09-19, session #10, 04:1x CST)

Sealed BEFORE any candidate sleeve return was computed. Reuse pattern: ITER24_DA
(driver_2026-09-19.py) verbatim with the two disclosed changes below.

## Provenance and motivation
- Operator objective (4th verbatim resend): keep improving; leverage <= 1.6; maximize
  Sharpe; annual return >= 20%. No rule change granted; no purchased data available.
- Live champion entering (byte-verified this session pre-seal):
  campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv sha16 8559fa55ee9a3417,
  weights RAWEW13v2_IS_SR_weights.csv (d2d11c92 family), SR 3.751429 / ann 23.6054% /
  MDD -3.6130% / gross 1.0. Data-feed staleness: find tools/quant/data -newer
  DATA_AXIS_CENSUS_2026-09-19.txt returned ZERO files => the axis is byte-identical to
  the screened census.
- Frontier entering: gear/weights/grid-edges/census-charted-families/8c-ledger/
  invariant-credit ALL closed (#114-#119). This iteration measures the two cells the
  2026-09-19 census closed WITHOUT a measurement:
  (a) cboe_hist NON-VOL capital-real ETF family. ITER24's recorded exclusion covers the
      vol complex only (index levels, no VIX futures on disk). The ~30 equity / bond /
      credit / commodity-ETF census lines flagged IS-FITTABLE were never built, fitted,
      or excluded on the record. Silence is not a verdict; this closes them.
  (b) nokcarry two-leg. nok_policy_rate.csv was skipped as a non-USD-real single-leg
      (recorded); the USD-real two-leg construction (#117b seliccary analogue) was never
      built. Ingredients verified on disk pre-seal: dm_rates/nok_policy_rate.csv
      (1991-01-01..2026-09-09, values 8.5 -> 4.25 = ANNUAL percent, opposite of selic's
      daily-percent quirk) + fx_hist/USD_NOK.csv (1999-01-04..2026-09-07, close).

## Frozen candidate set (30) - no additions, no substitutions
- F1 (29, kind "px"): DIA EEM EFA EMB EWT FXI GLD HYG IEF IWM JNK LQD QQQ SHY SLV SMH
  SPY TLT TSM VNQ XLB XLE XLF XLI XLK XLP XLU XLV XLY - exactly the census cboe_hist
  lines flagged IS-FITTABLE that are capital-real ETFs.
- F2 (1, kind "ret"): nokcarry = trend_sleeve over
  tr = nok_policy_rate/100/252 - d(USD_NOK)/USD_NOK (inner join, dropna), the #117b
  seliccary formula with the NOK unit correction (annual percent -> daily decimal /100/252).
- Recorded exclusions (same census, no discretion): VIX/VIX6M/VVIX vol index levels, not
  capital-real, no VIX futures on disk (ITER24 recorded; GVZ/OVX/VIX3M partial-IS anyway);
  SPX/DJX/OEX index levels with tradable proxies already in-set (SPY/DIA/QQQ);
  RUT/VIX1D/ulsd_la recent-only; KWEB partial-IS (2013 start); dm_rates aud_* post-2008
  starts; brazil_ipca / wb_commodity / wb_cmo / gas_storage low-freq or partial-IS per
  screen; brazil_selic/brazil_usdbrl single-leg non-USD-real already superseded by
  seliccary (#117b, OOS-dead).

## Method - ITER24_DA driver VERBATIM except the two disclosed changes
- Sleeve builder (house recipe): 378-trend / 42-cadence / T+1 / FULL |dWsig| 6.4bp /
  VT12 cap5, SSTART 2007-01-01. Sleeves are LONG-FLAT (signal in {0,1}) - never short,
  so single-name non-shortability cannot bind (covers TSM).
- 13-pool fit: fit_relw mirror (shrink 0.70 diag, two-stage Wmax cap 2/k, 3 SLSQP
  starts) + apply_brwt_cap mirror (0.30 brwt-block share cap, pro-rata redistribution,
  CFX4 pinned 0) - mirrors anchored byte-exact before any candidate.
- Per-candidate filters: Wmax(raw x13) <= 2.0+1e-9; IS-MDD >= -6%; 0 IS-neg years;
  [change 2 - #117b landed hygiene, adopted to protect IS-bar comparability] fit-row
  shrink = (incumbent IS fit rows - candidate 13-pool IS fit rows)/incumbent must be
  < 2% (seliccary precedent: 2.54% shrink flagged G8-FAIL).
- Admission: filters AND IS-SR > 4.198632 (incumbent continuity value).
- ONE global IS-argmax over admitted -> SINGLE reveal at gear 1.0 with gates:
  G1 FS ann >= 20% (CAGR or arithmetic); G2 gross <= 1.6; G3 FS MDD >= -7%;
  G4 0 FS neg years; G5 CFX4 = 0; G6 Wmax <= 2.0x; G7 OOS police (>= 4/5 positive
  2-yr bin dSR vs the committed champion AND min bin >= -0.10 AND FS SR > 3.751429).
- STOP RULE (frozen): 0 admitted => honest negative, no reveal. The admitted argmax
  failing ANY gate => REJECT, NO SECOND REVEAL, no re-fit, no substitution, no repair.
- Disclosed change 1: F2 built via kind "ret" (pre-computed return stream) + in-driver
  FAIL-CLOSED unit gate BEFORE any fit: (1 + tail60mean/100/252)^252 - 1 in [2%, 8%]
  and (1 + head60mean/100/252)^252 - 1 in [3%, 15%]; violation => SystemExit before
  candidates run. (Selic analogue #117b used /100 because selic is DAILY percent.)

## Anchors required BEFORE the reveal (all must pass or STOP, fail-closed)
1. Independent gauntlet: python3 campaign/bt/verify_champion.py with the
   verify_champion_r3_cmd.sh args (shrink 0.70, brwt-cap 0.30, gear 1.0, 12-sleeve map)
   => ok=true 7/7, byte_repro ~1e-16 class, gross 1.0000000, n_over 0.
2. Driver anchors: weights maxdev < 1e-12 vs committed weights file; bytes maxdev
   < 1e-12 vs champion CSV (n=4806); grossmax <= 1.0+1e-9; incumbent IS-SR prints
   4.198632 (ITER22/23/24/25/26 continuity).
3. Champion sha16 pre-run == post-run (the champion is never written by this iteration).

## Caveats disclosed pre-reveal
- cboe_hist ETF series are PRICE series (no dividend/coupon carry). Verdicts bind to the
  on-disk price series. A total-return upgrade is a data lever, recorded as such if the
  family dies IS (missing carry ~2-3%/yr on equity ETFs biases trend levels, noted).
- Costs: flat 6.4bp FULL |dW| one-side (ITER24 pre-committed convention), no
  per-instrument repricing.
- dAnn at fit recorded informationally only (#118: the operator constraint is a FLOOR,
  not zero-dilution; 8c is not an admission filter here).
- Multiplicity: FIRST reveal for every candidate in this set; none was inside any prior
  sealed candidate set (ITER24 28-row table, ITER25 credit, ITER26 credit-capfit).
  Prior stop rules are untouched; this is a new sealed cell, not a second reveal.

## Output contract
Driver log + 30 sleeve CSVs + (if a reveal fires) candidate book/weights CSV under
coord/ITER27_CENSUS_REMAINDER/. Pins: campaign/bt/tests/test_iter27_census_remainder.py
(mutation-checked RED -> restore -> GREEN). Full suite green from repo root.
STANDUP_LOG append + memory topic-file sub-entry (#120) AFTER the verdict, topic file
re-read at write time (concurrent-writer rule).

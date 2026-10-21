# ITER57 PRE-COMMIT - sealed BEFORE any candidate adjudication (2026-09-20, session #37)

Operator objective (5th verbatim re-issue): "keep improving. the leverage must be <=1.6.
Maximize Sharpe ratio. The annual return can't be smaller than 20%."

Champion of record at seal time: ITER49 tsm-vt015 book, sha16 cfa9ec4d38158691 / weights
a384d6b92e258fd5, SR 3.8203573 / CAGR 23.9215% / MDD -3.7339% / 0 neg yrs / gross 1.0
(<= 1.6 operator cap). Fresh canonical gauntlet THIS session BEFORE sealing: ok=true 7/7
(weights_repro 7.633e-17, byte_repro 1.041e-16, cost full_dw implied ratio 1.0000000000053,
causality causal + 7 truncation probes 0.0, gross max 1.0000000000006 n_over 0, 0 neg yrs,
MDD -3.7339%). JSON: coord/verify_champion_r3_last_session37.json. Baseline suite 682/0
(65.65s) incl. the 4 frontier-closure manifest pins.

## 1. The axis under test (why this iteration exists)

#146/#147 declared the frontier closed over the CURRENT 12-sleeve input map and named the
operator levers as purchased data / rule change. This session ran a DATA-INVENTORY audit
(all 81 tools/quant/data dirs x 3,786 repo files): every dir is name-referenced, but the
census screen (ITER23 criterion: >500 IS-window rows, start <= 2008-03-31, last >= 2024)
plus prior verdicts leave EXACTLY ONE fittable never-measured recipe x universe cell:

  fx_hist G10-USD spot TREND (tsmom-189 transplant), vt015 canonical construction.

Prior art that closes the SIBLING cells (recorded, not re-run):
  - FX CARRY on fx_hist: HUNT_CN_FUTURES FINDINGS #5 - SR 0.03, 11 neg yrs, scramble 0.86 - REJECT.
  - FX cross-z REVERSION (CFX4 recipe) extension to fx_hist: ITER25 pre-commit - "dead
    (vendor artifact; fx_hist extension rendered unreproducible)" - CLOSED.
  - cboe_flow put/call: vol-expression pre-excluded (not capital-real, no VIX-futures cost
    model - ITER24 correction), equity-expression = ITER27 dead-duplicate class.
  - boe_curve gilt real: kin of the G1-rejected bund/cad foreign-curve family.
  - remaining census-screen failures: em_macro/noaa/shiller monthly (106 IS rows), BTC
    on-chain 2010+, eastmoney 2010+, naver 2014+, nyfed 2016+, nikkei/wiki_pv/farside/cnn_fg
    recent-only, fred_tga/fiscal_tga/rba_bond/sffed_sentiment/zillow/altme/coingecko/cpc_dd/
    dbnomics/stooq_c5 EMPTY on disk (manifest-only).
Measuring this cell completes the data inventory: after it, every fittable landed dataset
carries a measured verdict or a census-class exclusion.

## 2. Frozen candidate (ONE construction; NO parameter sweep - the ITER24 family-level
no-edge law forbids recipe-tuning follow-ups)

Name FXH9. Universe: EUR, GBP, AUD, NZD, CAD, CHF, JPY, SEK, NOK vs USD (fx_hist daily
closes 1999-01-04..2026-09-07, n=7087 each, identical calendars). Quote convention: *_USD
as-is, USD_* inverted to USD-per-foreign; foreign-TR = pct_change of the inverted level
(geometric; the SNB day 2015-01-15 = +16.16% vs the arithmetic +13.91% - disclosed 2nd-order
identity r_inv = -r/(1+r)). Signal: sign(px - MA189, min_periods 94) per pair, weight 1/9
per leg (gross 1.0 pre-VT; disclosed leg-count adaptation of QA's 0.2 x 5). Execution:
wback_rb (Wed rebalance via wed_rbd, T+1, FULL |dW| 6.4 bps one-side), then vol_target
(expanding-60 trailing, vt_ann=0.15, clip 3.0) - the EXACT canonical vt015 vintage of the
pool's adopted tsmom family (ITER49). Spot-only (no interest differential), consistent with
the pool FX leg (-dxy spot index). Spot FX = fungible-short (ops constraint satisfied).

Stream artifact: sleeves derived in probe_iter57_a1.py (GREEN: A1a canonical-recipe fidelity
maxdev 9.996e-17 inner 4947; hygiene gates all 9 pairs no-NaN/maxgap<=5/stale<=1/|r|<20%;
direction gates corr(longEUR,longCHF)=+0.787>+0.30, SNB +0.1616>+0.10). sleeve_FXH9_stream.csv
sha16 9f61a03317a535ef (n=7028, 1999-03-26..2026-09-07; fit-row shrink on the 1809-row
12-pool IS frame = 0.6633% <= 2%). The driver must re-derive the stream byte-equal to this
sha and fail closed otherwise. The probe computed NO pool-fit/admission numbers.

## 3. Method (driver_iter49 machinery verbatim; single candidate instead of arms)

Frozen-block check: fit_relw/apply_cap/project_wmax/build_book text-identical to
driver_iter41.py AND driver_iter36.py AND driver_iter49.py (3-way). D17 dual-identity panel
patch BEFORE the r6lib-resolving import (Amendment 1). A2 continuity vs the LIVE pair
(additive candidate, not a replacement stream): weights maxdev < 1e-12, bytes maxdev < 1e-12,
n=4806, IS fit rows 1809, IS-SR continuity |sr - 4.218504| < 5e-6. A1a re-run in-driver.
Candidate fit: 13-name frame (12 + FXH9 reindexed to the champion frame), fit_relw on
2008-03-31..<2017-01-01 (have excludes IS-dead CFX4 -> kcov=12), apply_cap, project_wmax(k).
IS admission (ALL required): IS-SR > BAR + 1e-4 (BAR = 4.218504), IS-MDD >= -6%,
0 IS neg years, Wmax_sf = max(relw)*kcov <= 2.0 + 1e-9, g8 fit-window shrink <= 2%.

## 4. Reveal gates (G1-G8, ITER49 verbatim, FS_BAR = 3.8203573)

G1 FS ann >= 20% (CAGR or arith); G2 grossmax <= 1.6; G3 FS MDD >= -7%; G4 0 FS neg years;
G5 CFX4 relw = 0 exactly; G6 Wmax_sf <= 2.0x (have-set k=12); G7 OOS police (dSR vs
incumbent positive in >= 4/5 bins {2017-18,2019-20,2021-22,2023-24,2025-26}, min bin dSR
>= -0.10, FS SR > FS_BAR); G8 fit-window shrink <= 2%.

## 5. Stop rule + legality

ANY IS-admission failure => iteration CLOSED honest-negative, NO reveal, no parameter
retries, no second candidate. If admitted and revealed: any gate fail => same closure.
On 7/7+G8 PASS: full battery (placebo, halves, independent re-verification, mutation-checked
pins) BEFORE any champion swap; champion bytes never written by the driver (sha16 pre==post
asserted). Era-pin duty (Amendments 3+4): an adoption must update
test_frontier_closure_manifest.py + this ledger in the SAME landing.

## 6. Honest priors (disclosed, pre-reveal)

ITER24's pool-geometry lesson: transplants with standalone IS-SR far below the incumbents'
(IS ~4.2) dilute under the frozen max-Sharpe fit and die G1 (all five rate transplants
0.83-1.26 died). A 9-leg FX trend composite plausibly lands in that band. The cell is
measured to COMPLETE the data-inventory closure, not to force an adoption; both verdicts
are acceptable outcomes under the operator's stated gates.

## 7. Deviations ledger (disclosed pre-reveal)

1. Per-leg weight 1/9 vs QA's 0.2 (leg-count adaptation of the frozen recipe).
2. Geometric foreign-TR from inverted USD_* levels (SNB-day +16.16% vs +13.91% arithmetic).
3. Spot-only FX (no carry adjustment), consistent with the pool's -dxy FX leg.
4. A2 anchors to the LIVE champion pair (additive slot), not to a prior_champion_backup
   pair - no pool member is replaced, so no era-pair A2 is required.

Seal: this file written before the driver is invoked; the driver asserts its sha16.

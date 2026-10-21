# CHARTER: HUNT_WX_DEMAND — weather-demand (HDD/CDD) natgas-complex signals

Pre-registered BEFORE any result computation. Date: 2026-10-08.
Gates: coord/GATES_CONTRACT.md verbatim (SR >= 1.0 full-window net after costs,
plateau, halves >= 0.5, <=2 neg years > -5%, scramble 200x p<0.05, corr vs
champion, vt 10% trailing clip 3.0, economic rationale).

## Why this hunt (beat-path (b): new data acquisition)

The eia_weekly seam is fully closed (L48 row 57 + PADD row 66 + regional row
72). Beat-the-champion frontier requires new data; the 87th axis
(tools/quant/data/noaa_hddcdd/, acquired today, commit 8d72dd62) is US
population-weighted monthly HDD/CDD (base 65F), national + 9 climate regions,
1895-01..2026-08, from NCEI Climate at a Glance. Weather demand is the
dominant fundamental driver of natgas prices (heating ~ 50% of US gas demand,
EIA); NO prior axis or DEAD_IDEAS row covers degree-days. This charter
pre-registers the full config space BEFORE measuring.

## Data (frozen disk vintages, sha16-pinned)

- HDD monthly: tools/quant/data/noaa_hddcdd/hdd_monthly.csv sha16 0be7aa2620a76e52
  (date,US,NE,UP,OH,SE,NO,SO,SW,NW,WE; 1895-01..2026-08, 1580 rows, 0 gaps)
- CDD monthly: tools/quant/data/noaa_hddcdd/cdd_monthly.csv sha16 f658bcdcdda3dcaa
- Henry Hub spot: tools/quant/data/newdata/DHHNGSP.csv sha16 b9329a850156bc79
  (1997-01-07..2026-09-22 daily)

## Publication lag (T+1 / no-lookahead convention — CRITICAL)

NCEI posts month-M HDD/CDD mid-month M+1 (2nd Thursday-ish). A month-M signal
is knowable no earlier than the 12th of M+1 (conservative: before the typical
posting window opens). Convention: signal_date(M) = 12th of M+1; the monthly
signal is joined as-of to the DHHNGSP daily calendar from that date; trade
t+1. This is fail-closed: if NCEI ever posted earlier than the 12th we would
still be safe (we never trade before the conservative posting date).

## Instrument (expressibility)

Henry Hub spot DHHNGSP daily returns (pct_change, sanity clip ±25%), long/short
tilt ±1 gross, vol-target ~10% ann trailing (gate g). HDD/CDD signals tilt the
natgas complex (DHHNGSP) directly; regional cross-sections (9 climate regions)
are used ONLY to condition/weight the national tilt (regional degree-days are
not separately tradable). Borrow 0.5%/yr on short notional; costs 6.4bps on
FULL |dW|.

## Families (pre-registered; total 16 configs)

W1 HDD-deviation tilt (6 configs): national HDD deviation from trailing
seasonal normal, z-scored (10y trailing window, min 5y), winsorized |z|<=4.
Sign variants: long-when-cold (z>thr -> long HH), fade (z>thr -> short).
Thresholds: 1.0 / 1.5 / 2.0.
   Rationale (W1): cold winter -> heating demand surprise -> gas drawdown
   bullish; OR weather surprise already priced -> fade. Both directions
   pre-registered; the market prices forecasts, not realizations, so fade has
   comparable prior.
W2 Cumulative HDD surplus/deficit (4 configs): season-to-date (Jul-Jun gas
year) cumulative HDD minus trailing-10y same-season-to-date normal, as % of
normal, winsorized. Sign variants x thresholds: |surp%| > 2% / 5%.
   Rationale: cumulative deficit compounds storage draws across a season;
   the level effect (not just the monthly surprise) pressures prices.
W3 CDD summer variant (4 configs): same as W1/W2 but CDD, cooling season
(May-Sep), thresholds 1.0/1.5 (z) and 2%/5% (cum surplus).
   Rationale: summer cooling demand sets gas-for-power draws; hot summer ->
   storage enters winter tight.
W4 Regional composition tilt (2 configs): national tilt SCALED by heating-
region (NE+UP+OH) share of national HDD deviation vs their trailing share —
i.e., dispersion-weighted W1; sign follow only, thresholds 1.5.
   Rationale: demand concentrated in pipe-constrained heating regions is
   more price-elastic than national-average mildness suggests.

## Predictions (pre-registered)

P1 Most likely outcome: honest negative. Spot HH monthly-weather tilt after
   6.4bps FULL|dW| costs and the conservative 12th-of-M+1 lag: weather is
   the most-watched fundamental in the gas market; realized-print tilts are
   likely priced. Expected best |SR| 0.2-0.5.
P2 If any family passes 1.0 net: expect it to be W2 cumulative (seasonal
   compounding is slower to price than monthly prints); corr vs champion
   likely ~0 (champion is diversified daily) — corr-primary candidate.
P3 W4 regional composition: expected |SR| < 0.3 (second-order effect on a
   single-instrument tilt).
P4 The 1895-2026 span is a gift for halves/plateau robustness but the
   DHHNGSP instrument only starts 1997-01; effective test span 1997-2026
   (~29y, ~350 monthly signals). No span extension claims beyond instrument.

## Caps

- No champion/weights/manifest/suite file touched.
- Sleeve CSV only if a family clears ALL gates; else honest negative +
  DEAD_IDEAS row (coordinator adds it).
- All numbers from the frozen disk vintages above (no re-download).
- Champion trio STAGED-UNCHANGED; explicit-pathspec commits only.

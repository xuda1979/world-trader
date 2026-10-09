# CHARTER: HUNT_ENSO_AG — ENSO/NAO climate-index tilts on the ag-ETF complex

Pre-registered BEFORE any result computation. Date: 2026-10-08.
Gates: coord/GATES_CONTRACT.md verbatim (SR >= 1.0 full-window net after costs,
plateau, halves >= 0.5, <=2 neg years > -5%, scramble 200x p<0.05, corr vs
champion, vt 10% trail clip 3.0, economic rationale). Fail-closed; honest
negative expected scale ~0.2-0.4 SR (frontier prior from WX_DEMAND + EIA rows).

## Hypothesis (economic, falsifiable)

ENSO state (El Nino / La Nina) and the North Atlantic Oscillation shift global
crop-growing conditions (precipitation/temperature over major breadbaskets,
US + southern-hemisphere harvests) with multi-month persistence. Agricultural
commodity prices should drift while ENSO extremes persist and around
southern-hemisphere (SH) harvest windows (Nov-Mar), when realized supply
shocks from ENSO-affected growing seasons settle into prices. NAO shifts US
east-coast winter weather (export/shipping corridors) — a second, weaker
candidate channel. If these effects are not already arbitraged away in liquid
ag futures/ETF prices, conditioning long/short ag exposure on public,
free, monthly climate indices should produce positive net SR at the gates.

## Why now (untried seam)

- DEAD_IDEAS has NO row touching ENSO/ONI/MEI/NAO/climate-indices (verified
  2026-10-08, rows 57/66/72/73 are natgas-weather, different seam).
- Axes on disk, manifest-pinned, zero-gap, never used as signals:
  ONI 1950-2026.07, MEI.v2 1979-2026.07, NAO 1950-2026.07 (noaa_climate);
  DBA/CORN/WEAT/SOYB ETFs 2007/2010/2011-2026.09 (more_etf).
- Same beat-path as DATA_NOAA_HDDCDD round: axes already acquired and pinned;
  this hunt consumes them as SIGNALS (first time).

## Frozen inputs (sha16-pinned, RAW_DATA_MANIFEST-verified; no re-download)

- tools/quant/data/noaa_climate/oni.csv   a458c1cc929c36ab (919 rows, 1950-01..2026-07)
- tools/quant/data/noaa_climate/meiv2.csv ce8c21bf3c4dc2ee (571 rows, 1979-01..2026-07)
- tools/quant/data/noaa_climate/nao.csv   3e723c3c42ac609f (919 rows, 1950-01..2026-07)
- tools/quant/data/more_etf/DBA.csv       7a12c1e0d6f11f65 (4948 rows, 2007-01..2026-09)
- tools/quant/data/more_etf/CORN.csv      a579ceacc2dc1d21 (4086 rows, 2010-06..2026-09)
- tools/quant/data/more_etf/WEAT.csv      33c6813fc1c5db93 (3763 rows, 2011-09..2026-09)
- tools/quant/data/more_etf/SOYB.csv      b53ab1388a569b6b (3763 rows, 2011-09..2026-09)
Harness asserts sha16 of every input at run time; vintage drift = abort.

## Index label semantics + publication convention (fail-closed, verified live)

- ONI: 3-month centered mean; row label = CENTER month (NDJ 2015 = 2.59
  verified vs live psl.noaa.gov). CPC posts ONI ~around the 10th of the month
  following the final month of the window; we use a conservative signal date:
  label month M's value (window M-1..M+1 finalized) knowable at 12th of M+2.
- MEI.v2: 2-month sliding seasons labeled by SECOND month (JJ 1997 = 2.27,
  ND 2020 = -1.14 verified vs live PSL). PSL updates ~within first week after
  season close; conservative: label month M's season (M-1,M) knowable at
  12th of M+1.
- NAO: calendar-month station-based index (Azores-Iceland SLP), posted within
  days of month end; conservative: month M's value knowable at 12th of M+1.
- Any index's latest months beyond its conservative posting horizon are NEVER
  used early. As-of join onto ETF daily calendars; trade t+1. If real-world
  posting is earlier than the 12th, we are still safe (fail-closed).

## Pre-registered configs (16 total, 4 families; NO post-hoc additions)

Signal construction (monthly, from frozen vintages):
  z vs trailing 10y same-month history (min 5y, only data >= 1y old),
  clip [-4, 4]; state = z >= +thr (El Nino / high NAO), z <= -thr
  (La Nina / low NAO), else neutral; position applied while state persists.

E1 "enso_state" — ONI state tilt on DBA (the ag-complex broad instrument):
  thr 0.5 / 1.0 / 1.5 x {long-when-Nino, long-when-Nina} = 6 configs.
  (Nino years: S Hemisphere drought-supply story -> long ag; alternates
  tested, pre-registered both directions.)
E2 "enso_sh" — same ONI states but restricted to SH harvest window
  (position only during Nov..Mar; flat outside): thr 1.0 x 2 directions = 2.
E3 "nao_state" — NAO state tilt on DBA: thr 1.0 / 1.5 x 2 directions = 4.
E4 "enso_ag_ls" — ONI state (thr 1.0) long-when-Nino applied long the
  weakest / short the strongest of {CORN, WEAT, SOYB} trailing 60d return
  when state active (cross-sectional rank, pre-registered rule) = 2 configs
  (Nino-long-weakest; Nina-long-strongest). If state inactive: flat.
  (E4 is the only cross-sectional family; entry/exit at monthly signal dates.)

Total 16 configs. Any config that clears ALL gates goes to sleeves/ with
.meta; the family count is final before any result is computed.

## Costs + mechanics (TRADE_RECORD_STANDARD, mirrors HUNT_WX_DEMAND harness)

- T+1: weight at t applies to t+1 close-to-close returns (pct_change,
  sanity clip ±25% as in prior hunts on these ETFs).
- 6.4bps one-side on FULL |dW| traded notional; borrow 0.5%/yr on short
  notional (ETF shorts borrow as cash-proxy per CAMP_BORROW r3 standard).
- Vol-target ~10% ann trailing-only, scale clip <= 3.0 (gate g).
- Scramble 200x, seed 17, p = wins/200 (gate e).
- E4 cross-sectional legs each costed separately; combined sleeve = mean of
  leg net returns (equal-weight pre-registered).

## Prediction (pre-registered, honest)

Expected outcome: NEGATIVE at the 0.2-0.4 SR scale. Priors: (i) crop-ETF
tracks futures, and ENSO state is among the most-watched public signals in
ag markets (professional weather desks), so the monthly public-information
edge is likely priced; (ii) instrument friction: ETF basis noise vs futures
dilutes signal; (iii) WX_DEMAND + EIA rows show realized public weather
prints are priced at publication. A pass would require an unpriced
persistent tilt channel, most plausible in E2 (SH-harvest timing) if any.

## Cap constraints

- No champion/weights/manifest/suite file touched.
- Sleeve CSV only if a family clears ALL gates; else honest negative +
  DEAD_IDEAS row (coordinator adds it).
- All numbers from the frozen disk vintages above (no re-download).
- Champion trio STAGED-UNCHANGED; explicit-pathspec commits only.
- E4 restrictions: rank uses ONLY trailing 60d returns of the 3 ETFs (no
  fundamentals), and only rebalances at monthly signal dates (no daily
  churn).

## Robustness diagnostics (reported regardless of pass/fail)

- Per-config: full-window net SR, H1/H2 SR, negY count + worst year,
  scramble p, |corr| vs champion trio (GOAL100_RAWEW13v2_WEIGHTED_GEAR16).
- Plateau report for any config family with a >= 0.7 SR member.
- Span honesty: effective test span is ETF-limited (DBA 2007+, cross-sec
  2011+); no claims beyond instrument span; pre-2007 climate history is
  context only (never backtested on synthetic instruments).

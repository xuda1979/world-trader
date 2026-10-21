# MANIFEST_R4 — CFTC trader-count breadth panel (charter R4b deliverable)

**File:** `trader_count_panel.csv` — 29,017 rows x 51 cols, 35 families, weekly.
**Built by:** `build_trader_count_panel.py` (run from this dir; ~40s). Tests: `pytest test_trader_count_panel.py` -> 22/22.
**Source:** in-repo `tools/quant/data/more_cot/_raw/fut_disagg_txt_20{10..26}.zip` +
`fut_fin_txt_20{10..26}.zip` (34 zips). NO network. Same audited `cot_matcher` as R1-R3.

## What this is

The HUNT_COT2 R3 closure memo named trader-count breadth (`Traders_Tot_All` etc., 191 cols in
the raw zips) the cheapest untested COT corner. This panel materializes the COUNT columns
(not positions) as PIT z-scores so hunt agents can test breadth without touching the raw zips.

Columns:
- `family` — R1 universe slug (35; matches universe_manifest.csv families incl. canola/sofr_3m)
- `report_date` — CFTC report Tuesday (or holiday Monday)
- `release_date` — next Friday STRICTLY after report (Tue->+3d, Mon->+4d). Lags present in
  data: {3, 4} days ONLY (measured, 0 same-day, 0 other). Signals must trade on/after this.
- `format` — `disagg` (prod/swap/MM/other categories) | `fin` (dealer/assetmgr/levmoney/other)
- `open_interest` — Open_Interest_All, as published that week
- `cnt_Traders_*` — raw trader COUNTS (23 cols = union of both formats; the other format's
  columns are structurally blank for a family — NOT missing data). CFTC `.` suppression
  sentinel -> blank cell, never 0, never imputed.
- `z_Traders_*` — PIT expanding z of the matching cnt col: rows <= t only, `min_periods=26`
  (first valid z at the 26th observation), `ddof=0`, blank count -> blank z, measured-constant
  window -> 0.0 (never inf).

## Core columns (both formats)

`Traders_Tot_All`, `Traders_Tot_Rept_Long_All`, `Traders_Tot_Rept_Short_All`.

Category cols: disagg adds Prod_Merc L/S, Swap L/S/Spread, M_Money L/S/Spread,
Other_Rept L/S/Spread; fin adds Dealer L/S/Spread, Asset_Mgr L/S/Spread,
Lev_Money L/S/Spread, Other_Rept L/S/Spread.

## Lint (fail-closed; `build_trader_count_panel.py` exits 1 on any FAIL)

33/35 families PASS, 2 PASS_WITH_EXN (measured universe breaks — see below), 0 hard FAIL.
Hard gates enforced at parse time (raise, never warn):
- negative count -> refuse; per-category count > its side total > grand total -> refuse
  (spread counts are cross-side entities: excluded from the side-nesting identity)
- unparseable OR calendar-impossible report date -> refuse
- duplicate (family, report_date): same-name re-report -> newer `as_of` wins (CFTC revision);
  different-name collision (rename seam) -> matcher priority wins, collision recorded
  (193 collisions resolved: lumber CME->RANDOM LENGTH LUMBER 2023, nat_gas HENRY HUB->
  NATURAL GAS 2018-07, wheat CBOT->KCBT 2013 class; full list prints)
- cadence gate per family: max gap <= 21d. Measured: max gap 8d everywhere except sofr_3m
  14d (2018 launch year) — matches the R1 span-gate story.
- BREAK gate (added this session after real-data catch): a source-name transition whose
  first row moves Traders_Tot_All or OI by >=30% is a universe BREAK, not a rename ->
  PASS_WITH_EXN with measured magnitudes. Two families flagged:
  * nat_gas_nymex: break at 2022-02-08, NATURAL GAS - NYMEX -> HENRY HUB - NYMEX,
    Tot_All 281 -> 40 (-86%), OI 1,162,813 -> 590,294 (-49%). CFTC split the report;
    the stitched z hit **-10.74** on 2022-02-08 — pure level artifact. Engines must NOT
    read z across 2022-02-08 for nat_gas (or must re-run z within the post-break segment).
  * lumber: break at 2023-04-25, RANDOM LENGTH LUMBER -> LUMBER - CME, Tot_All 21 -> 43
    (+105%) — same class, smaller magnitude (post-rename re-consolidation of reporting).

Per-family spans are identical to R1 universe_manifest (disagg 2010-01-05..2026-08-25 n=869;
fin 2010-07-20..2026-08-25 n=841; eurodollar_3m ends 2023-06-13; canola 2018-08-07+;
sofr_3m 2018-07-24+). Core columns (Tot_All / side totals): ZERO suppressed cells in all
35 families (`core_miss=0`) — the headline breadth count is always present.

Suppression (blanks) measured over each family's OWN format columns only (the earlier
44-51% numbers wrongly counted the other format's structural blanks; corrected):
median 2.6%, worst lumber 19.8% (spread cols), then rough_rice 17.7%, dow_emini 17.3%,
wheat_hrspring 17.0%, jpy 14.5%; vix 1.2%.

## Honest limits

- z-scores are LEVEL-breadth (number of distinct traders), NOT positioning direction. A
  market can have few traders and net-long positioning; the two families of signal are
  different corners. HUNT agents must NOT treat z_Traders_Tot_All as a positioning signal.
- The two PASS_WITH_EXN families (nat_gas_nymex 2022-02-08, lumber 2023-04-25) carry
  structural level breaks INSIDE the stitched series. Any z read across the break date is
  an artifact (nat_gas printed -10.74 on it). Segment-local z is the honest usage.
- Earlier draft of this manifest said the z tail was "2020-03 COVID OI collapse" — WRONG,
  the min is nat_gas 2022-02-08 at the CFTC reporting split. Corrected above; kept here so
  the correction is visible (same class as the R2 "CIT identical to disagg" retraction).
- Counts restate at CFTC's discretion (re-reports resolved newer-as_of-wins); the panel is
  as-of final-published, z at t uses only rows <= t, but a LATER revision can change a past
  cnt value. PIT discipline holds at the release-date level, not the revision level.
- Structural blanks: the 12 other-format columns are NaN for every family — filter to your
  format's columns before any cross-family use.
- MIN_OBS=26 warmup: first ~half-year of each family has NaN z. By design.
- Release lag is CALENDAR (next Friday), matching CFTC's actual Friday 15:30 ET release;
  align_daily.release_shift uses the same +3d convention, so this panel composes with the
  R2 alignment machinery unchanged.

## Cross-checks done (not prose — run commands)

1. Raw-vs-panel field identity, corn 2024-01-09 (independent read, no builder code):
   Tot_All 719=719, side totals 522/550=522/550, MM 61/91=61/91, OI 1,410,115=1,410,115.
2. `release lags in data = {3,4}d only`; 0 duplicate (family, report_date); 0 negative counts.
3. Full suite 24/24 (`python3 -m pytest test_trader_count_panel.py -q`), incl. RED->GREEN
   tests for: fixture-calendar validity, source-name break flagging (nat_gas-class seam
   flagged, lumber-class continuous rename stays PASS), warmup NaN (first z at obs 26).
4. `z_Traders_Tot_All` measured range [-10.74, 4.10]; the min IS the nat_gas 2022-02-08
   break (excluded as artifact; next-most-extreme legit values ~-2.5).

NO signal/overlay backtest was run on this panel (charter cap: data deliverable only;
hunting is HUNT_* territory).

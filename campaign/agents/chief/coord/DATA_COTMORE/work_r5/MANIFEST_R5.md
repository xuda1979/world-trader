# MANIFEST_R5.md — DATA_COTMORE round 5 (2026-09-08)

## Deliverable: trader_count_panel.csv (refreshed)

- **Rows 29,051 × 51 cols × 35 families** (R4: 29,017 — +34 rows = one report week,
  2026-09-01, on 34 families; eurodollar_3m correctly static, contract sunset 2023-06).
- Span 2010-01-05 .. **2026-09-01** (R4 ended 2026-08-25). Weekly, Tue report →
  release_date = next Friday strictly after (new week all 2026-09-04).
- sha256(panel)16 = `9e2c82303acf4c24` (R4 vintage: `02aa8f0028144d9d` — superseded).
- Builder + tests byte-identical to R4 (sha 7ee710b9… / 9a6f99cb…): **no code changed**;
  the only delta is the data vintage.

## Vintage pins (V2 §10b)

| file | sha256-16 | bytes | note |
|---|---|---|---|
| _raw/fut_disagg_txt_2026.zip | 70e18ad5a7e61745 | 1,685,920 | fetched 2026-09-08 07:45 |
| _raw/fut_fin_txt_2026.zip | 7b744b8c6b241008 | 488,449 | fetched 2026-09-08 07:45 |
| _raw/fut_disagg_txt_2026.zip.sep3.bak | 3e816c649e39c016 | 1,637,614 | Sep-3 vintage backup |
| _raw/fut_fin_txt_2026.zip.sep3.bak | 0d3a015f09b47a05 | 474,205 | Sep-3 vintage backup |
| _raw/fut_disagg_txt_2010..2025.zip | unchanged | — | mtimes 2026-09-03, untouched |

New 2026 vintage covers report dates .. 2026-09-01 (disagg 9,502 rows, fin 3,050 rows;
Sep-3 vintage: 9,217 / 2,959 ending 2026-08-25).

## BREAK gate re-run — charter pass criterion: 2 known EXN rows stable ✅

- 35 families: **33 PASS, 2 PASS_WITH_EXN, 0 FAIL.**
- nat_gas_nymex: break at 2022-02-08 NATURAL GAS→HENRY HUB: Traders_Tot_All 281→40 (−86%)
  — IDENTICAL to R4.
- lumber: break at 2023-04-25 RANDOM LENGTH LUMBER→LUMBER: Traders_Tot_All 21→43 (+105%)
  — IDENTICAL to R4.
- No new break candidate fired anywhere (including the new 09-01 week: max name-transition
  move < 30% gate).

## Overlap integrity (R4 vintage vs R5 vintage, all 29,017 shared rows)

- Changed cnt_ cells across 23 cnt columns × 29,017 rows: **0** — no CFTC revisions
  between the Sep-3 and Sep-8 vintages. The +34 rows are pure append.

## Lint (unchanged gates, MAX_GAP 21d; z warmup MIN_OBS 26)

Suppression% by family ranges 0.0% (coffee/gold/silver/soybeans) .. 19.8% (lumber);
core columns (Tot_All + side totals) 0 suppressed cells in all 35 families. Full table
printed by build_trader_count_panel.py; statuses identical to R4 except the +1 week.

## (a) Family-extension check on the fresh fetch — NONE eligible

Genuinely-first-in-2026 unmatched CFTC names (32, verified against full 2010-2026 name
history across all 32 zips): Coinbase crypto perps (n≤35 wks, e.g. AAVE PERP STYLE
first 2026-08-11), ICE carbon/REC/basis contracts, Nodal PJM/ISO nodal contracts, FMX
SOFR-3M (first 2026-08-25, 2 wks), CBOT Bloomberg HY/IG credit futures (first 2026-03-31
/ 2026-05-05, n=22/18 < 26-obs z warmup). All are either sub-warmup, non-liquid, or
outside the R1 liquid-majors matcher scope → **0 new families added; panel stays 35.**
Oats re-checked in the fresh data: still dead (new gaps 2026-02-03→05-19 105d and
2026-06-02→09-01 91d, on top of the 294d 2024-11→2025-09 suspension; OI 3,132 at end).

## (b) CBOE PCR refresh past 2019-10-04 — FROZEN, honest STOP (charter b)

probe_pcr_refresh_r5.py (this dir), run 2026-09-08 ~07:5x CST:

1. control VIX_History.csv → **200 text/csv** (network path open; probe not void).
2. 6 API variants under cdn.cboe.com/api/global/delayed_quotes/{put_call_ratios/
   _all.json, put_call_ratios/history.json, put_call_ratios/SPX.json, pc_ratio/_all.json,
   market_stats/put_call_ratio.json, us_options/put_call_ratios/_all.json} → **ALL HTTP
   403** `application/xml` `<Error><Code>AccessDenied</Code>` (RequestIds logged in the
   probe output, e.g. 7PXRTJSWYYP24PHJ).
3. historical_data page → 200 HTML, publishes **exactly the same 10 archive CSVs** as R3.
4. byte-compare totalpc.csv / equitypc.csv / spxpc.csv vs on-disk _raw → **200, sha256
   identical 3/3** (remote_rows 3,256 / 3,256 / 2,332 = local).
→ The archive remains live but FROZEN at 2019-10-04 upstream. No scraping workarounds,
no synthetic substitutes; the R3 manifest (stale=True) and HUNT_VOL2-R5's dead-row
warning stand unchanged. Evidence file: probe_pcr_refresh_r5.py (rerunnable, exit 0).

## Suite status (this round, from repo root)

- work_r5/test_trader_count_panel.py: **24/24 pass** (15.6s).
- more_cot/test_lint_cot_universe.py: **14/14 pass** (raw-zip refresh regression).
- cboe_pcr/test_pcr_lint.py: **21/21 pass** (PCR untouched; archive unchanged).

## Honest limits (carried from R4 + R5 deltas)

- z columns are LEVEL-breadth (participant counts), not positioning direction.
- nat_gas/lumber z's are segment-local only across their EXN break dates.
- Counts can be REVISED by CFTC re-reports; this vintage shows 0 revisions vs Sep-3, but
  PIT discipline stays: align on release_date, never on report_date.
- PCR covariates remain frozen 2019-10-04 (re-verified this round); overlay work stays
  2006-2019 only.
- eurodollar_3m panel rows end 2023-06-13 (contract sunset); SOFR bridge is a separate
  R1-mapped series — engines must not treat the fin panel as continuous for it.

## R7 provenance clarification (2026-09-08 23:0x, DATA_COTMORE R7)

The vintage-pin table above says `_raw/...` — that is shorthand for the builder's RAW
constant (build_trader_count_panel.py line 34): tools/quant/data/more_cot/_raw
(34 zips + 2 sep3 baks). work_r5/_raw_live/ holds the 2-zip 2026 fetch copies,
byte-identical to canonical (sha16 70e18ad5a7e61745 / 7b744b8c6b241008). All 4 pins
re-hashed MATCH at the canonical path during R7 (DATA_COTMORE/FINDINGS.md round 7);
a bare `work_r5/_raw/` does not exist.

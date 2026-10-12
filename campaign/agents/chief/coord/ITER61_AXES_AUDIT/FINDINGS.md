# FINDINGS: ITER61_AXES_AUDIT — 87-axis manifest vs hunted-set cross-reference

## Scope-registered question
Enumerate all 87 axes in the raw-data manifest and cross-reference against the
hunted/measured set (74-row DEAD_IDEAS ledger, 38 distinct hunt sources, sleeve
library, DATA_COVERAGE map, STRATEGY doc). Goal: verify or refute the "hunts
stay closed" claim — an acquired-but-unmeasured axis would be an autonomous
beat-path-1 hunt (new data, already certified).

## Method
- Axis enumeration: `find tools/quant/data -mindepth 1 -maxdepth 1 -type d`
  => exactly 87 axes (matches the `test_raw_data_manifest.py` pin at line 122).
- Name-match pass: each axis name searched (lowercase) in DEAD_IDEAS.csv
  (idea+evidence+source concatenated), DATA_COVERAGE.md, STRATEGY.md.
- The 5 name-unmatched axes were resolved manually by opening charters,
  findings, and the files themselves.

## Result: ZERO unmeasured axes. "Hunts stay closed" is CONFIRMED.

82/87 axes name-match directly to ledger/coverage/strategy text. The 5
name-unmatched axes resolve as follows (per-axis detail in
`audit_87_axes.csv`, same dir):

| axis | resolution | evidence |
|---|---|---|
| binance_bookdepth | MEASURED | HUNT_BINANCE_AXES — DEAD_IDEAS row 70 (24 configs, best BTC imb5 net SR 0.811, short-span 2.7y) |
| binance_metrics | MEASURED | HUNT_BINANCE_AXES — DEAD_IDEAS row 69 (70 configs incl. cross-sectional RV) |
| binance_dl_common | NOT-A-DATA-AXIS | shared downloader lib (`binance_dl.py` + tests) used by the bookdepth/metrics builders; appears as an axis only because the manifest splits on directory |
| fred_full | MEASURED-BUT-TRUNCATED | 4 BAML OAS files, 781 rows, 2023-09-22..2026-09-01 — same series as `more_fred` BAML (DEAD_IDEAS row 41: blocked, data starts 2023-09; rows 40/31: credit dead via HUNT_CROSSASSET2/SKILL_ALPHAAGB_B); DATA_COVERAGE item 1 documents the truncation repair path |
| noaa_hddcdd | MEASURED | HUNT_WX_DEMAND — DEAD_IDEAS row 73; charter pins hdd_monthly sha16 0be7aa2620a76e52 / cdd_monthly f658bcdcdda3dcaa |

## Caveats (honest)
- Name-matching is a floor, not a ceiling: an axis could be "mentioned" yet
  have sub-files never opened by any hunt. This audit verifies axis-level
  coverage only (one or more pre-registered measurement passes per axis),
  not file-level coverage. File-level residuals already have their own
  tracking (DATA_COVERAGE "Notes" + manifest lint columns).
- `binance_dl_common` is a bookkeeping artifact of the directory-level axis
  split, not a data acquisition. If the manifest is ever regenerated with a
  smarter axis definition, it would drop out (86 axes) — the
  `test_raw_data_manifest.py` pin would need a matching update. Not worth
  doing on its own.
- `fred_full` is the only axis where the measurement is arguably stale:
  its content (BAML OAS) was hunted as *blocked/truncated* in
  HUNT_CROSSASSET2 (row 41) because the on-disk series starts 2023-09
  while FRED serves 1996-12+. The DATA_COVERAGE item-1 repair (full
  re-pull via fredgraph.csv) would convert this into a genuinely new
  measurement opportunity (credit-spread signals on 1996+ history).
  That repair is ALREADY a standing documented item — this audit adds
  no new obligation, but notes it is the single most concrete
  data-side residual in the entire 87-axis map.

## Verdict
No autonomous beat-path-1 hunt is available from the current manifest.
Every acquired axis has at least one pre-registered measurement pass in the
ledger or a documented blocker. The hunt-closure claim stands. Data-side
residuals remain exactly: (a) fred_full/more_fred BAML full-history repair
(standing item), (b) Binance CBOE H1/options axes pending live accumulation,
(c) Binance short-span trigger re-measure (fires 2027-09).

# MANIFEST_R4 — DATA_ETF_MORE round 4 (2026-09-08)

Charter round 4: clear the 10 lint-bound FAILs from R1 or prove them unobtainable.
R3 had already cleared 5 of the 10 under the coordinator 2007-waiver
(HYG EWC DBE DBP USCI -> on disk, PASS_WAIVER, manifest-verified).
Round 4 rotated the remaining 5 (EIS TUR EPHE COPX ENOR) across the keyless
source roster. **Result: 5/5 PASS_WAIVER, written fail-closed, manifest rebuilt**
-> all 10 charter names now resolved; 0 remaining FAILs from the R1 list.

## Charter-10 final state (manifest.csv, 82 series, all disk-matched)

| symbol | status | span_class | start | end | rows | maxgap | jumps | dups |
|--------|--------|-----------|-------|-----|------|--------|-------|------|
| HYG | PASS_WAIVER | 2007plus | 2007-04-11 | 2026-09-04 | 4883 | 5 | 0 | 0 |
| EWC | PASS_WAIVER | 2007plus | 2008-01-02 | 2026-09-04 | 4699 | 5 | 0 | 0 |
| DBE | PASS_WAIVER | 2007plus | 2007-01-05 | 2026-09-04 | 4948 | 5 | 0 | 0 |
| DBP | PASS_WAIVER | 2007plus | 2008-01-02 | 2026-09-04 | 4699 | 5 | 0 | 0 |
| USCI | PASS_WAIVER | 2007plus | 2010-08-10 | 2026-09-04 | 4043 | 5 | 0 | 0 |
| EIS | PASS_WAIVER | 2007plus | 2008-03-28 | 2026-09-04 | 4640 | 5 | 0 | 0 |
| TUR | PASS_WAIVER | 2007plus | 2008-03-28 | 2026-09-04 | 4641 | 5 | 0 | 0 |
| EPHE | PASS_WAIVER | 2007plus | 2010-09-29 | 2026-09-04 | 4008 | 5 | 0 | 0 |
| COPX | PASS_WAIVER | 2007plus | 2010-04-20 | 2026-09-04 | 4121 | 5 | 0 | 0 |
| ENOR | PASS_WAIVER | 2007plus | 2012-01-24 | 2026-09-04 | 3676 | 5 | 0 | 0 |

## Round-4 rotation results (results_r4.json, reproducible via r4_fetch.py)

Sources per symbol, in order: (1) TwelveData time_series full-history
(8 req/min respected), (2) Nasdaq historical keyless (browser UA).
TwelveData won on depth every time (vendor-bounded Nasdaq depth is 10y,
~2016-09 onward); no stitch was needed or applied.

| symbol | winner | rc | span | n | nasdaq cross-check | written |
|--------|--------|----|------|---|--------------------|---------|
| EIS | twelvedata | 200 | 2008-03-28..2026-09-04 | 4640 | rc=200 n=2514 (10y) | yes (4640 rows) |
| TUR | twelvedata | 200 | 2008-03-28..2026-09-04 | 4641 | rc=200 n=2514 (10y) | yes (4641 rows) |
| EPHE | twelvedata | 200 | 2010-09-29..2026-09-04 | 4008 | rc=200 n=2514 (10y) | yes (4008 rows) |
| COPX | twelvedata | 200 | 2010-04-20..2026-09-04 | 4121 | rc=200 n=2514 (10y) | yes (4121 rows) |
| ENOR | twelvedata | 200 | 2012-01-24..2026-09-04 | 3676 | rc=200 n=2514 (10y) | yes (3676 rows) |

## Failing probes

None. Every probe returned rc=200 with data; no FAIL row was produced this
round, so there are no failing-probe URLs to disclose. The only remaining
FAILs in the directory are the two genuine post-2013 inceptions (XLC 2018-06-19,
XLRE 2015-10-08) — unchanged since R3, loud in manifest.csv, unobtainable by
any source (a vendor inception is not a fetch problem).

## Verification

- test_r4.py 8/8 (after fixture-gate-order fixes; production code unchanged)
- test_manifest_r4.py 3/3: manifest rows == disk for the 5 new; independent
  re-lint (fresh logic, NOT r4_fetch.lint_series) confirms gap<=10, dups=0,
  jumps=0, ascending, positive, end 2026-09-04 on all 5.
- test_r4_t7_done.py 2/2: charter-10 partition exact; all 10 PASS_WAIVER +
  disk-matched. Total 13/13 green.
- Zero-run disclosure (not a gate, loud): see manifest zero_ret_rows column.

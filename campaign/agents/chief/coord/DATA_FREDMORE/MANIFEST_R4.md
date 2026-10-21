# MANIFEST_R4 — DATA_FREDMORE / DATA_CBOEHIST (2026-09-07)

Charter: materialize the MAX free CBOE options-chain history (per-symbol put/call volume,
pc_ratio, atm_iv if present), keyless CDN only, fail-closed span lint like R1, write to
`tools/quant/data/cboe_opts/` + this manifest. If keyless history is NOT feasible, prove
with exact probe evidence.

**Headline: per-symbol put/call volume + pc_ratio HISTORY is NOT keyless-feasible — proven
with exact probes, not assumed. What IS feasible and now on disk: the CBOE per-symbol
implied-vol index family (VX{SYM}, the historical-ATM-IV class) and the options-strategy
index family (BXM/BXY/BXMD/PPUT/PUTR/WPUT/CLL/LOVOL, 1986+). 22 linted CSVs + honest
manifest.**

## 1. Feasibility verdict (exact probe evidence, reproducible)

`work_r4/probe_history_endpoints.py` (saved output: `probe_history_endpoints_out.json`):

| route | HTTP | verdict |
|---|---|---|
| `us_indices/daily_prices/VIX_History.csv` (control) | 200, 472,309B | network path alive |
| `delayed_quotes/put_call_ratios/_all.json` | **403** S3 `AccessDenied` | aggregate P/C blocked (matches DEAD_IDEAS row 108) |
| `delayed_quotes/put_call_ratios/SPY.json` | **403** | per-symbol P/C blocked — charter's pc_ratio ask NOT servable |
| `delayed_quotes/charts/historical/volumes/SPY.json` | **403** | per-symbol options-volume history blocked |
| `delayed_quotes/charts/historical/_all.json` | **403** | aggregate chart list blocked |
| `delayed_quotes/charts/historical/SPY.json` | 200 | 5,707 rows 2004-01-02..2026-09-03 — but keys are ONLY `date,open,high,low,close,volume` of the UNDERLYING. No put/call/IV fields. Charter's put/call ask NOT servable here either. |
| `delayed_quotes/options/SPY.json` | 200 | 12,086 contracts, `timestamp` 2026-09-07 15:35:36 → SNAPSHOT-ONLY (refetch overwrites; already exploited by `cboe_options/` since R-earlier) |
| `resources/options/volume_and_call_put_ratios/totalpc.csv` | 200 | official aggregate archive, FROZEN at 2019-10-04 (DEAD_IDEAS row 109, DATA_COTMORE's deliverable) |

Roster enumeration: `work_r4/probe_roster.py` + tail re-probe (69 candidate symbols across
the single-stock VX*, ETP/commodity VX*, strategy-index families; control-first, 0.15s
sleep). 403s are endpoint-level (S3 AccessDenied with RequestId), NOT WAF-scraping
territory — no workarounds attempted (AAII/FINRA precedent).

## 2. Deliverables on disk (`tools/quant/data/cboe_opts/*.csv`, date,close)

**Class 1 — per-symbol implied-vol indexes (VX{SYM}), role=per_symbol_atm_iv** — this is
the historical ATM-IV class the charter asked for (CBOE computes VX{SYM} from the symbol's
options surface; near-30d implied vol).

| series | n | span | max_gap | note |
|---|---|---|---|---|
| VXAPL | 3934 | 2011-01-07..2026-09-04 | 5d | PASS |
| VXGS | 3934 | 2011-01-07..2026-09-04 | 5d | PASS |
| VXIBM | 3934 | 2011-01-07..2026-09-04 | 5d | PASS |
| VXEEM | 3888 | 2011-03-16..2026-09-04 | 5d | PASS |
| VXPFE | 490 | 2020-11-27..2022-11-07 | 4d | PASS but DISCONTINUED upstream (ends 2022-11-07) |
| VXWMT | 490 | 2020-11-27..2022-11-07 | 4d | PASS but DISCONTINUED upstream |
| VXVXX | 490 | 2020-11-27..2022-11-07 | 4d | PASS but DISCONTINUED upstream |
| VXGDX_era1/era2 | 2744+245 | 2011..2022-02-11 / 2025-09-16..now | 5d/4d | parent FAIL: 1313d upstream hole; eras delivered separately, hole NOT spliced |
| VXSLV_era1/era2 | 2744+329 | 2011..2022-02-11 / 2025-05-15..now | 5d/4d | parent FAIL: 1189d upstream hole |
| VXFXI_era1/era2 | 2744+245 | 2011..2022-02-11 / 2025-09-16..now | 5d/4d | parent FAIL: 1313d upstream hole |

**Class 2 — options-strategy indexes, role=options_strategy_index** — synthetic options
books (covered-call / put-write / protective-put), tradeable proxies:

| series | n | span | max_gap | note |
|---|---|---|---|---|
| BXMD | 10125 | 1986-06-20..2026-09-04 | 7d | PASS — longest options-strategy history available keyless |
| PPUT | 10119 | 1986-06-30..2026-09-04 | 7d | PASS |
| BXY | 9633 | 1988-06-01..2026-09-04 | 7d | PASS |
| BXM | 6151 | 2002-03-22..2026-09-04 | 5d | PASS |
| PUTR | 6434 | 2001-01-31..2026-09-04 | 7d | PASS |
| WPUT | 5179 | 2006-01-31..2026-09-04 | 5d | PASS |
| LOVOL | 5145 | 2006-03-21..2026-09-04 | 5d | PASS |
| CLL_era2/era3 | 1134+3299 | 2008-12-01..2013-06-21 / 2013-07-02..2026-09-04 | 5d | parent FAIL: two 11d holes (2008-11-20→12-01, 2013-06-21→07-02); CLL_era1 n=61 (< 100) correctly NOT written |
| PUT | (dedup) | 1991-03-04..now | — | already in `tools/quant/data/cboe_flow/` — NOT re-fetched, manifest row marked dedup |

**Totals: 22 linted CSVs on disk (14 unique series + 8 era files), 28 manifest rows = 22
PASS + 6 FAIL (3 split parents VXGDX/VXSLV/VXFXI + CLL + CLL_era1 n=61 + PUT dedup row).**
All files `date,close` only — no forecast rows, no splices; era splits are a
disclosure device (hole bounds in manifest `reason`), never a joined span. Every attempt
(live or 403) is a manifest row; lint is law.

## 3. Charter span preference (start <= 2010)

`start_pref2010=True` (8 PASS rows): BXMD 1986, PPUT 1986, BXY 1988, PUTR 2001,
CLL_era2 2008, LOVOL 2006, WPUT 2006, BXM 2002.
`start_pref2010=False` (documented actual): all VX{SYM} (earliest 2011-01-07 — upstream
birth), VXPFE/WMT/VXX (2020-11), era2 files.

## 4. Reproduce

    python3 tools/quant/data/cboe_opts/cboe_opts_dl.py     # fetch+lint+write (fail-closed)
    python3 -m pytest campaign/.../work_r4/test_cboe_opts_dl.py   # 21/21
    python3 campaign/.../work_r4/verify_round4.py          # 69 PASS / 0 FAIL, exit 0

Fetcher/lint: `tools/quant/data/cboe_opts/cboe_opts_dl.py`; tests: `work_r4/test_cboe_opts_dl.py`
(TDD red→green, 21 tests); verifier: `work_r4/verify_round4.py` (69 checks, independent
re-lint of all 22 files + era arithmetic + probe-evidence checks).

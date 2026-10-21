# DATA_FREDMORE ROUND-2 MANIFEST (2026-09-07)
Fetcher: work_r2/fetch_round2.py (fred_dl.fetch + fail-closed lint, same semantics as R1).
Tests: work_r2/test_fred_round2.py — 11/11 green (TDD: red first, then fetcher run).
Framework regression: more_fred/test_fred_dl.py 19/19 green.

Charter note: a prior R2 attempt (crashed) had already written DEXUSEU, RSAFS,
IRLTLT01NZM156N, and a 3y BAMLH0A0HYM2; this session completed the remaining
fetches, verified every structural claim against raw FRED payloads, and reconciled
the manifest against disk reality (26 verdict corrections).

## NEW PASS this round (written to tools/quant/data/more_fred/{id}.csv)
| series | freq | role | start | end | n | note |
|---|---|---|---|---|---|---|
| DEXJPUS | daily | USD/JPY (HUNT_FXCARRY2) | 1971-08-31 | 2026-08-28 | 13795 | head-trim @11bd hole 1971-08-16 (post-Nixon-shock FX closure); R1 VIXCLS precedent |
| DEXUSUK | daily | USD/GBP (HUNT_FXCARRY2) | 1971-08-23 | 2026-08-28 | 13801 | head-trim @5bd hole 1971-08-16 (same closure) |
| DTWEXBGS | daily | broad dollar idx (trimmed) | 2016-01-27 | 2026-08-28 | 2645 | mid-series Fed Board blizzard closures 4bd@2010-02-08 + 3bd@2016-01-22 are NOT head-trimmable; only clean trim is 2016-01-27 |
| TWEXBMTH | monthly | broad dollar idx (full span) | 1973-01-01 | 2019-12-01 | 564 | discontinued monthly native, ZERO holes — long-span replacement for DTWEXBGS daily |

## VERIFIED / CARRIED (already on disk, re-linted PASS)
| series | freq | start | end | n | note |
|---|---|---|---|---|---|
| BAMLH0A0HYM2 | daily | 2023-09-05 | 2026-09-03 | 787 | 3y ICE BofA licensing window = FRED policy (Apr-2026, family-wide: BAMLC0A0CM, BAMLHE00EHYIOAS same notes; ALFRED has no older vintages — realtime_start=1997 probe returns realtime_start>=2023-09-05 only). Pre-2023 HY OAS requires paid ICE source → permanent fail for full history |
| DEXUSEU | daily | 1999-01-04 | 2026-08-28 | 6936 | EUR born 1999, no holes |
| DEXCAUS | daily | 1971-01-04 | 2026-08-28 | 13963 | zero contiguous holes ≥3bd |
| RSAFS | monthly | 1992-01-01 | 2026-07-01 | 415 | retail sales |
| IRLTLT01NZM156N | monthly | 1979-10-01 | 2026-06-01 | 561 | R1 single-hole fail fixed by 1979-10-01 head-trim (legit: 1979-09 publish hole) |
| UMCSENT | monthly | 1978-01-01 | 2026-07-01 | 583 | monthly era (pre-1978 quarterly survey) |
| HOUST / PERMIT | monthly | 1959/1960 | 2026-07 | 811/799 | verify PASS |
| T10YIE | daily | 2003-01-02 | 2026-09-02 | 5922 | verify PASS |
| USREC | monthly | 1854-12-01 | 2026-08-01 | 2061 | verify PASS; binary {0,1}, 2008-06 & 2020-04 flagged 1 (depth test) |

## PERMANENT FAILS (documented, fail-closed, no splices — lint is law)
| series | verdict | evidence |
|---|---|---|
| BAMLH0A0HYM2 full history | impossible via FRED | FRED series notes: "Starting in April 2026, this series will only include 3 years of observations"; obs_start=2023-09-05 family-wide; ALFRED vintage probe empty pre-2023-09 |
| DTWEXBGS full span daily | structural mid-series holes | 4bd@2010-02-08 + 3bd@2016-01-22 Fed Board closures; discontinued DTWEXB has identical holes → not a vintage issue |
| NROU | unusable as history | quarterly + forecast rows to 2036 (R1 gaps=702 vs monthly grid) |
| CPIAUCSL / UNRATE / UNRATENSA / RRSFS / CPILFESL / LNS11300060 | 1-month upstream hole @2025-10-01 | BLS published no Oct-2025 CPI (government shutdown); verified `.` in raw FRED payloads 2026-09-07; monthly zero-tolerance |

## MANIFEST CORRECTIONS (honesty pass — lint re-run against every on-disk file)
26 verdict corrections, most importantly:
- CPIAUCSL, UNRATE, UNRATENSA, RRSFS: claimed lint_pass=True (stale) → **False** (files carry the 2025-10-01 hole)
- TEDRATE: True → **False** (contiguous-hole=3 @1986-01-20)
- MORTGAGE30US: True → **False** (gaps=1194 on weekly grid — structural publication irregularities)
- GFDEGDQ188S: True → **False** (gaps=480, irregular quarterly→monthly transitions)
- R1 files (VIXCLS, T10Y2Y, T5YIFR, DGS*, AWHAETP, CSUSHPISA, TOTALSL, IPMAN, DGORDER, USREC, HSN1F): backfilled manifest rows, all lint PASS
Manifest final: 141 rows = 125 PASS / 16 FAIL. PASS↔file consistency: every PASS row has its file on disk; FAIL rows marked `file=""`. 7 pre-existing on-disk files that fail lint were NOT deleted (not mine to delete; they predate R1) — consumers must filter on `manifest.lint_pass`.

## Span/coverage notes for the hunt teams
- FX carry (HUNT_FXCARRY2) now has EUR/JPY/CAD/GBP legs + two dollar indices; longest spans: DEXCAUS 1971, DEXJPUS 1971-08, DEXUSUK 1971-08; DTWEXBGS usable only 2016+, use TWEXBMTH for long-span dollar work.
- HY OAS (HUNT_CREDIT2): only a 3-year window exists on FRED — any credit-signal backtest relying on BAMLH0A0HYM2 is capped at 2023-09+; BAA10Y (1986+) on disk remains the long-span credit spread.
- Any monthly macro panel must handle the 2025-10-01 BLS shutdown hole: CPIAUCSL/UNRATE/UNRATENSA/RRSFS/CPILFESL/LNS11300060 all miss exactly that month, upstream, unbackfilled as of 2026-09-07.

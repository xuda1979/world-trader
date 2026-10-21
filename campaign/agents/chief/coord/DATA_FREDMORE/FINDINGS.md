# FINDINGS — DATA_FREDMORE

## ROUND 2 (2026-09-07)

Charter: (a) must-fetch list, (b) legit retry of R1 5 fails, (c) all through fred_dl lint,
fail-closed, manifest with freq/gaps. Context: a prior R2 attempt had crashed mid-run
(BAMLH backup made, file left truncated; DEXJPUS/DEXUSUK/DTWEXBGS not written; manifest
stale). This session verified all prior state against raw FRED payloads, TDD'd the
remaining work (red first), completed the fetches, and reconciled the manifest.

### (a) Must-fetch — results (all through fred_dl.fetch + fail-closed lint)
| series | verdict | exact numbers | evidence from command output |
|---|---|---|---|
| BAMLH0A0HYM2 (HY OAS) | STRUCTURAL: full history impossible via FRED | on-disk 3y window n=787, 2023-09-05..2026-09-03, lint PASS; full-span permanent FAIL | direct curl probe: no-start AND observation_start=1996 both return n=795 first=2023-09-05; series notes: "Starting in April 2026, this series will only include 3 years of observations"; family-wide (BAMLC0A0CM, BAMLHE00EHYIOAS identical obs_start + notes); ALFRED realtime_start=1997 probe returns only realtime_start>=2023-09-05 rows. Not a fetch bug — the pre-2023 data is gone from FRED |
| T10YIE | PASS (verified) | n=5922, 2003-01-02..2026-09-02, gaps=0 | lint re-run on disk file |
| DEXUSEU | PASS | n=6936, 1999-01-04..2026-08-28 | EUR birth 1999, no holes |
| DEXJPUS | PASS after head-trim | n=13795, 1971-08-31..2026-08-28, gaps=554 maxrun=2 (holidays only) | raw span 1971-01-04..: one contiguous 11-bday hole @1971-08-16 (post-Nixon-shock FX closure). Head-trim to 1971-08-31 (first data after hole) — same precedent as R1 VIXCLS. No splice |
| DEXCAUS | PASS (already written by crashed run, verified) | n=13963, 1971-01-04..2026-08-28, no contiguous runs ≥3 | hole-mapper output: runs>=3: [] |
| DEXUSUK | PASS after head-trim | n=13801, 1971-08-23..2026-08-28, gaps=554 maxrun=2 | one contiguous 5-bday hole @1971-08-16 (same closure); trim to 1971-08-23 |
| DTWEXBGS | PARTIAL: trimmed PASS + full-span permanent FAIL | trimmed n=2645, 2016-01-27..2026-08-28, gaps=118 maxrun=2, lint PASS | raw span 2006-01-02..: mid-series holes 4bd@2010-02-08 AND 3bd@2016-01-22 (Fed Board blizzard closures) — NOT head-trimmable without discarding 2010-2015. Discontinued DTWEXB (1995-2019) has the IDENTICAL two holes → not a vintage problem, structural. Documented permanent fail for full span |
| UMCSENT | PASS (verified) | n=583, 1978-01-01..2026-07-01 | monthly era; pre-1978 quarterly survey trimmed (crashed-run decision, verified sound) |
| RSAFS | PASS | n=415, 1992-01-01..2026-07-01 | written by crashed run, re-linted |
| HOUST | PASS (verified) | n=811, 1959-01-01..2026-07-01 | |
| PERMIT | PASS (verified) | n=799, 1960-01-01..2026-07-01 | |
| USREC (depth) | PASS (verified) | n=2061, 1854-12-01..2026-08-01; values ⊆ {0,1}; 2008-06-01=1, 2020-04-01=1 | depth test green |
| CPIAUCSL | PERMANENT FAIL (upstream) | n=954, 1947-01-01..2026-07-01, gaps=1 @2025-10-01 | raw payload check: `2025-10-01 .` (BLS published no Oct-2025 CPI — govt shutdown; unbackfilled as of 2026-09-07). Same hole verified in UNRATE, UNRATENSA, RRSFS, CPILFESL, LNS11300060 |
| NEW: TWEXBMTH | PASS (found as DTWEXBGS long-span substitute) | n=564, 1973-01-01..2019-12-01, monthly native, ZERO holes | discontinued monthly broad dollar index — long-span dollar work should use this instead of 2016+ DTWEXBGS |

### (b) R1 5 fails — legitimate retries
| R1 fail | retry attempted | verdict |
|---|---|---|
| IRLTLT01NZM156N (gaps=1) | head-trim to 1979-10-01 (1979-09 publish hole) | **PASS** n=561, 1979-10-01..2026-06-01, gaps=0 |
| NROU (gaps=702) | none possible | permanent fail: quarterly + forecast rows to 2036 → unusable as history. Documented in manifest |
| LNS11300060 (gaps=1) | alternate vintage probe | permanent fail: hole @2025-10-01 is upstream (BLS shutdown), unbackfilled — verified `.` in raw payload |
| CPILFESL (gaps=1) | same | permanent fail, same upstream hole |
| VIXCLS pre-2004 | n/a (R1 fixed via 2004 trim, PASS) | carried |

### (c) Lint/manifest discipline — honesty reconciliation (26 verdict corrections)
Re-linted EVERY on-disk CSV against detected native freq and rewrote stale manifest rows:
- CPIAUCSL, UNRATE, UNRATENSA, RRSFS: claimed lint_pass=True (stale from earlier round) → **False** (files carry 2025-10-01 hole). Reason annotated REAL-UPSTREAM-HOLE
- TEDRATE: True → **False** (contiguous-hole=3 @1986-01-20)
- MORTGAGE30US: True → **False** (gaps=1194 on weekly grid, structural)
- GFDEGDQ188S: True → **False** (gaps=480, irregular quarterly)
- 14 R1 files had NO manifest row at all (AWHAETP, CSUSHPISA, DFII10, DGORDER, DGS2/10/30, HSN1F, IPMAN, T10Y2Y, T5YIFR, TOTALSL, USREC, VIXCLS): backfilled, all lint PASS
- 5 explicit structural-fail rows added (NROU, LNS11300060, CPILFESL, BAMLH0A0HYM2-FULL-HISTORY, DTWEXBGS-FULL) with evidence in `reason`
- 7 pre-R1 on-disk files that fail lint (CPIAUCSL, UNRATE, UNRATENSA, RRSFS, TEDRATE, MORTGAGE30US, GFDEGDQ188S) were NOT deleted (not mine; they predate this sleeve) — consumers MUST filter on `manifest.csv:lint_pass==True`

Manifest final: **141 rows = 125 PASS / 16 FAIL**, PASS↔file consistency verified (every PASS row's file exists on disk; FAIL rows have `file=""`).

### TDD
- work_r2/test_fred_round2.py: red first (4 failed: FX files missing, TWEXBMTH absent, stale manifest claims, NROU unrecorded) → after fetcher run **11/11 passed**
- Framework regression: tools/quant/data/more_fred/test_fred_dl.py **19/19 passed**
- New tests encode structural reality: BAMLH 3y-licensing-window, FX trim start floors (prevents hole re-introduction), shutdown-hole manifest honesty, NROU never-written invariant

### Deliverables
- tools/quant/data/more_fred/: DEXJPUS, DEXUSUK, DTWEXBGS, TWEXBMTH (new) + BAMLH0A0HYM2 (3y, max available) + manifest.csv reconciled
- MANIFEST_R2.md (full tables + evidence), this FINDINGS.md
- Fetcher/tests: work_r2/fetch_round2.py, work_r2/test_fred_round2.py

### Hunt-team guidance (span/coverage notes)
- HUNT_FXCARRY2: EUR/JPY/CAD/GBP daily legs ready; JPY/GBP start 1971-08 (not 1971-01); use TWEXBMTH for long-span dollar, DTWEXBGS only for 2016+
- HUNT_CREDIT2: BAMLH0A0HYM2 capped at 2023-09+ on FRED (licensing) — long-span credit spread remains BAA10Y (1986+)
- All monthly macro panels: exactly one upstream hole @2025-10-01 across CPIAUCSL/UNRATE/UNRATENSA/RRSFS/CPILFESL/LNS11300060 (BLS shutdown, unbackfilled)

## ROUND 3 (2026-09-07, verification + completion session)

Charter: read GATES_CONTRACT.md + DEAD_IDEAS.csv (107 rows) FIRST — done; this is a
data-acquisition round (no signal tested), so no dead family re-tested and no dead
signal re-tuned. (a) ALFRED first-release vintages, (b) reconcile the 7 pre-R1 lint-FAIL
files, (c) TDD. A prior R3 session today (15:20-16:33 CST) had left: alfred_dl.py, 6
vintage files, fetch_round3.py, a 28-test suite, and a BROKEN truncated stub
coord/test_fred_round3.py. This session independently re-verified every claim from disk +
live FRED (nothing trusted from the prior session's cache), fixed 2 defects under TDD
(red test first), and saved a standalone verifier so every claim reproduces.

### (a) ALFRED first-release vintages -> tools/quant/data/alfred/<sid>/vintage.csv
ot4 semantics verified live: realtime_start of the value-in-effect block = first-release
date (exactly one block per observation_date; PAYEMS pre-1955-05 has none — ALFRED birth,
documented truncation, not a bug).
| series | n | obs span | release span | lag min/max | missing '.' dropped |
|---|---|---|---|---|---|
| PAYEMS | 856 | 1955-05-01..2026-08-01 | 1955-06-07..2026-09-04 | 28/80 | 0 |
| UNRATE | 797 | 1960-03-01..2026-08-01 | 1960-04-12..2026-09-04 | 28/80 | 1 (2025-10) |
| CPIAUCSL | 648 | 1972-07-01..2026-07-01 | 1972-08-22..2026-08-12 | 37/62 | 1 (2025-10) |
| ICSA | 901 | 2009-05-30..2026-08-29 | 2009-06-04..2026-09-03 | 4/54 | 0 |
| RSXFS | 302 | 2001-06-01..2026-07-01 | 2001-07-13..2026-08-14 | 38/85 | 0 |
| IPMAN | 224 | 2007-12-01..2026-07-01 | 2008-01-16..2026-08-18 | 42/93 | 0 |
Independent checks (my script, not the fetcher's): one row per obs (0 dup obs, 0 dup
(rel,obs) pairs); lag_min per row >= charter lag floor (PAYEMS/UNRATE 27, CPI 35, ICSA 4,
RSXFS 37, IPMAN 41); sorted by (release,obs). Live ot4 equality re-pull: PAYEMS 0/856
mismatch, ICSA 0/901, UNRATE 0 release-date + 0 numeric mismatches (85 strings like "5"
vs "5.0" = formatting only). PIT sanity vs release history: PAYEMS 2020-03 -> 151786
@2020-04-03, UNRATE 2020-04 -> 14.7 @2020-05-08, ICSA wk2020-03-21 -> 3283000 @2020-03-26.
2025-10-01 absent from UNRATE/CPIAUCSL vintages (BLS shutdown month, never published).
Loud drop: SP500 has NO ALFRED metadata (vintagedates HTTP 400 "does not exist in
ALFRED") -> FAIL row, no file written. Correction of an earlier draft's false claim:
VIXCLS (n=3927), DGS10 (n=5103), DEXJPUS (n=651) DO have vintages — recorded as
has-vintages info rows (lint_pass blank, no file => R2 PASS-row=>file invariant intact).
Manifest extended: vintage=True + lag_days on all 6 ALFRED:* rows.

### (b) Reconcile the 7 pre-R1 lint-FAIL files (no deletion, no splices)
| file | verdict | evidence (re-derived this session) |
|---|---|---|
| CPIAUCSL | stays FAIL | 2025-10 hole is upstream BLS shutdown, unbackfilled; vintage fetched separately |
| UNRATE | stays FAIL | same hole; ALFRED vintage has it too (never published) |
| UNRATENSA | stays FAIL | same hole; no NSA vintage exists to substitute |
| RRSFS | stays FAIL, backfill=impossible | nominal RSAFS HAS 2025-10 (731051, grep-verified) but real = nominal/CPI and CPI has no 2025-10; CPALTT01USM657N absent 2025-09..11. No splice |
| TEDRATE | stays FAIL | 5 missing-bday runs of len 3 = Christmas closure clusters 1993/1999/2004/2010/2021 (NYSE closed Fri+Mon); 486 isolated 1d gaps OK |
| MORTGAGE30US | reclassified PASS | linter artifact: holiday-shifted weekly publication, max spacing 9d (<=9d proves no absent week); holiday_tol_days=3 lint added under TDD, data untouched |
| GFDEGDQ188S | reclassified PASS | linter artifact: 241/241 quarterly slots present (0 off-grid), was mis-linted as monthly; quarterly freq support added under TDD, data untouched |
Honesty defect found + fixed this session: the fetcher's TEDRATE reason claimed
"1986-01-20 has data" — grep proves 1986-01-20 is ABSENT (MLK Day, first federal
observance; isolated 1-bday gap, lint-OK). The R2 max-run LOCATION @1986-01-20 and this
"has data" sub-claim were both wrong; both corrected in fetch_round3.py under TDD.

### (c) TDD (failing test first, exact numbers)
- New red: test_tedrate_reason_no_false_has_data_claim + test_tedrate_1986mlk... ->
  **2 failed, 28 passed**. After fixing fetch_round3.py reason + re-running the saved
  fetcher: **31/31 passed**. (First red run also caught MY OWN test bug: I counted run
  length in calendar days — 1993-12-24..28 is 5 calendar days but 3 missing bdays;
  fixed my test to count missing bdays, matching the linter, which is correct.)
- Broken stub coord/test_fred_round3.py (10 lines, undefined _manifest_raw_rows/os/ROOT,
  would NameError if collected) replaced with a pointer docstring; its one good idea
  (PASS-row=>file invariant) carried into the canonical suite as a real test.
- Final: R3 suite **31/31**; R2+fred_dl regression **30/30**; combined **61 passed**.

### Independent verifier (every claim reproduces from a saved script)
work_r3/verify_round3.py -> verify_round3_output.txt: **84 PASS / 0 FAIL, exit 0**.
Checks: vintage structure/PIT/lag-floor/live-equality (18), 2020 PIT sanity (3), 2025-10
hole in vintages (2), FAIL7 data facts incl. 241/241 quarterly slots + max-spacing 9d +
bday-run accounting (17), manifest honesty incl. no dup rows, header-covers-keys,
reconciled_r3=True x7, stays-FAIL x5, reclassified-PASS x2, SP500 loud drop,
no-false-no-vintages x3, PASS-row=>file sweep (136 bare-name + 6 repo-relative paths,
all resolve) (44+). Two verifier iterations were my own check bugs (expected
backfill=impossible for TEDRATE, whose closures are STRUCTURAL — nothing to backfill;
and a pipe-masked exit code), both fixed before final green.

### Manifest final state
160 rows. FAIL7: 5 FAIL / 2 reclassified PASS. ALFRED rows: 6 vintage PASS (lag_days
recorded) + SP500 loud-drop FAIL + 3 has-vintages info. 2025-10 BLS hole remains the
single upstream gap across monthly macro; consumers must filter manifest lint_pass==True.

### Hunt-team guidance for HUNT_MACRO2
- Use ALFRED vintage files (release_date, observation_date, value) for PIT macro-surprise
  construction; lag floors enforced: PAYEMS/UNRATE 27d, CPI 35d, ICSA 4d, RSXFS 37d,
  IPMAN 41d. ICSA weekly vintages start 2009-05 (ALFRED birth).
- Known truncation: first obs per series = first obs AFTER ALFRED birth (e.g. PAYEMS
  1955-05), so early-span surprise windows are shorter than the FRED full-history span.
- SP500 has no vintages (not in ALFRED) — any PIT equity-vintage need needs a different
  source. VIXCLS/DGS10/DEXJPUS vintages EXIST on ALFRED if the hunt needs them.
- 2025-10 CPI/unemployment: never published (shutdown) — no vintage will ever carry it.

ROUND 3 DONE


## ROUND 4 (2026-09-07 ~23:0x CST, DATA_CBOEHIST)

Charter: read GATES_CONTRACT.md + DEAD_IDEAS.csv (118 rows on disk) FIRST — done.
Dead-family check: rows 108/109 already own the AGGREGATE CBOE put/call story
(108 = current-day API/CSV routes BLOCKED, 403, DATA_COTMORE-R3; 109 = the 10 official
archive CSVs 1995-2019, acquired + frozen at 2019-10-04). Rows 23/44/45/58/67/72 kill
vol-TIMING overlays (VIX/VXV/GVZ/OVX term-structure, vol-gates) — none cover per-symbol
options data acquisition. My round is data-acquisition only (no signal tested), so no dead
family was re-tested and no dead signal re-tuned. Pre-registered new corner: PER-SYMBOL
options history (the aggregate-vs-per-symbol distinction is the new corner vs rows 108/109).

### Verdict on the charter's headline ask
Per-symbol put/call VOLUME history + per-symbol pc_ratio history are **NOT keyless-feasible
— proven with exact probe evidence, not assumed**. CBOE options chains are SNAPSHOT-ONLY.
What IS feasible, and is now on disk: the per-symbol implied-vol index family (VX{SYM} =
the historical ATM-IV class the charter asked for as "atm_iv if present") and the options-
STRATEGY index family (BXM/BXY/BXMD/PPUT/PUTR/WPUT/CLL/LOVOL, back to 1986).

### (a) Feasibility probe (work_r4/probe_history_endpoints.py; saved output
probe_history_endpoints_out.json; control-first, exact HTTP status + first bytes logged)
- control us_indices/daily_prices/VIX_History.csv -> HTTP 200, 472,309B (network path alive)
- delayed_quotes/put_call_ratios/_all.json -> HTTP 403 S3 AccessDenied (RequestId-logged;
  matches DEAD_IDEAS row 108 exactly, re-probed live this session)
- delayed_quotes/put_call_ratios/SPY.json -> HTTP 403 -> per-symbol pc_ratio NOT feasible
- delayed_quotes/charts/historical/volumes/SPY.json -> HTTP 403 -> per-symbol options-volume
  history NOT feasible
- delayed_quotes/charts/historical/_all.json -> HTTP 403
- delayed_quotes/charts/historical/SPY.json -> HTTP 200, 5,707 rows 2004-01-02..2026-09-03,
  but data_keys_union = EXACTLY [close,date,high,low,open,volume] of the UNDERLYING
  (stock OHLCV; volume = share volume, not put/call volume). No put/call/IV fields anywhere.
- delayed_quotes/options/SPY.json -> HTTP 200, 12,086 contracts, payload timestamp
  "2026-09-07 15:35:36" -> snapshot semantics (refetch overwrites; this is what
  tools/quant/data/cboe_options/ already exploits for current-day chains).
- resources/options/volume_and_call_put_ratios/totalpc.csv -> 200 but FROZEN at 2019-10-04
  (DEAD_IDEAS row 109). The official historical_data page publishes ONLY the same 10
  aggregate CSVs (link dump from the live page, 11 hrefs, all row-109 files).
- No auth tricks, no scraping workarounds (AAII/FINRA precedent).

Roster enumeration (work_r4/probe_roster.py + tail, 69 candidates, 0.15s sleep, VIX
control-first): 13 HTTP 200 on first pass + LOVOL/BXY/PPUT/BXMD/CLL/VXIBM/VXPFE/VXWMT/
VXVXX on full run. 30+ siblings 403 (VXAMZN/VXMSFT/VXNFLX/VXTSLA/VXGLD/VXGOOG/TDOL/XMPT...).
403s are endpoint-level S3 AccessDenied, not symbol typos: same path shape returns 200 for
the delivered set.

### (b) Deliverables: tools/quant/data/cboe_opts/ — 22 linted CSVs (date,close), 28 manifest rows
Class 1 per_symbol_atm_iv (VX{SYM}): VXAPL/VXGS/VXIBM n=3934 2011-01-07..2026-09-04
maxgap 5d; VXEEM n=3888 2011-03-16.. maxgap 5d; VXPFE/VXWMT/VXVXX n=490 2020-11-27..
**2022-11-07 (PASS lint but DISCONTINUED upstream — honest end, not hidden)**; VXGDX/
VXSLV/VXFXI parent FAIL (single upstream hole: 2022-02-11 -> 2025-05/09, 1189-1313d,
values differ across it = real hole, not frozen copy) -> era-split disclosure:
era1 n=2744 2011..2022-02-11 + era2 n=245-329 2025-05/09..now, hole NEVER spliced.
Class 2 options_strategy_index: BXMD n=10125 1986-06-20.., PPUT n=10119 1986-06-30..,
BXY n=9633 1988-06-01.., PUTR n=6434 2001-01-31.., BXM n=6151 2002-03-22.., WPUT n=5179
2006-01-31.., LOVOL n=5145 2006-03-21.., CLL parent FAIL (two 11d holes 2008-11-20->12-01,
2013-06-21->07-02) -> CLL_era2 n=1134 + CLL_era3 n=3299 delivered, **CLL_era1 n=61
fail-closed at MIN_N=100 and correctly NOT written**. PUT dedup: already in
tools/quant/data/cboe_flow (1991-03-04..) -> manifest row marked dedup, NOT re-fetched.
Values sanity: BXM 584.30 (2002) -> 2541.16 (now); VXAPL range 12.52-101.69 — plausible.
Charter span preference: start<=2010 = start_pref2010 True on exactly 8 PASS rows (BXMD
1986, PPUT 1986, BXY 1988, PUTR 2001, CLL_era2 2008, LOVOL 2006, WPUT 2006, BXM 2002);
all VX{SYM} documented False (upstream birth 2011-01-07 — earliest per-symbol IV history
CBOE publishes). Totals: 22 files = 14 unique + 8 era files; 28 rows = 22 PASS + 6 FAIL
(3 split parents + CLL + CLL_era1 + PUT dedup). PASS-row=>file invariant holds (verifier).

### (c) TDD (red first, exact numbers)
- RED: work_r4/test_cboe_opts_dl.py written first -> ModuleNotFoundError (no
  cboe_opts_dl). Green: tools/quant/data/cboe_opts/cboe_opts_dl.py (parse both CBOE
  formats, fail-closed lint: order/dupe/NaN/plausibility-by-class/gap-census-9d/MIN_N=100,
  actual-start recorded as start_pref2010, era split as disclosure).
- Second red round: 4 era-split tests -> AttributeError (no split_eras); 2 iterations of
  MY OWN test bugs fixed (wrong expected dates: 41d hole from dropping rows 60-99 of a
  day-stepped frame, not 40d from 2011-03-11; eras too short for MIN_N -> moved hole to
  rows 200-239; labeled/manifest tests needed the hole too, contiguous returns []).
- Final: **21/21 pytest + 21/21 plain runner.** Manifest-row contract: 403 symbol never
  enters ROSTER (VXAMZN/VXMSFT/VXNFLX/VXTSLA/VXGLD/TDOL/XMPT asserted absent); failed row
  never produces a file; every row carries role/start/end/max_gap/split_of/reason.

### Independent verifier (every claim reproduces from a saved script)
work_r4/verify_round4.py -> verify_round4_output.txt: **69 PASS / 0 FAIL, exit 0**
(exit code captured un-piped this time — R3 lesson applied). Checks: manifest honesty
(no dup ids, PASS=>file, no file=>failed row), independent re-lint of ALL 22 files from
disk (structure + class plausibility + gap census, not trusting the fetcher), era
arithmetic no-fabrication (parent n == sum of era n incl. undelivered CLL_era1 61:
2989=2744+245, 3073=2744+329, 2989=2744+245, 4494=1134+3299+61), era order/no-overlap,
documented facts (VXPFE frozen 2022-11-07, BXY 1988, BXMD 1986, PPUT 1986, CLL_era1
fail-closed), probe-evidence file (4 blocked routes all 403, OHLCV keys exactly the
6 underlying fields, snapshot timestamp, control 200), PUT dedup. Two verifier iterations
were my own check bugs, both fixed before final green: parent CSVs don't exist on disk
(only eras are written — switched to manifest-arithmetic check), CLL has 3 eras not 2
(61 undelivered), and an un-piped exit-code capture.

### Honest negatives / limits
- Charter's per-symbol put/call volume + pc_ratio: **infeasible keyless** (403s above).
  If the fleet needs per-symbol P/C, it needs a paid source — say so plainly rather than
  proxying with stock OHLCV volume.
- VX{SYM} per-symbol IV starts 2011 (upstream birth), so any HUNT using it gets max ~15y.
- VXPFE/VXWMT/VXVXX dead 2022-11-07; VXGDX/VXSLV/VXFXI have 3.3-3.6y upstream holes
  (2022-02..2025-05/09) — era files only, never spliced.
- CLL crisis-era stub (61 rows, Aug-Nov 2008) too short to deliver.
- No signal tested this round (data acquisition only, per charter) — no GATES claims made.

### Hunt-team guidance
- Longest options-strategy histories: BXMD 1986-06, PPUT 1986-06, BXY 1988-06 give ~40y
  for regime/covariate work. Index COMPOSITIONS not verified this round (BXM/BXY/PPUT/PUTR
  are buy-write/put-write/protective-put families per CBOE naming; exact underlying + rules
  -> CBOE prospectus pages) — check before tradeability claims; as DATA they are linted.
- Per-symbol IV (VXAPL/VXGS/VXIBM/VXEEM, 2011+): single-name implied-vol level for
  cross-sectional vol work; pairs with existing more_vol aggregates (which are index-level
  only) — NOT a duplicate of any existing directory (cboe_flow=PUT index, cboe_pcr=
  aggregate P/C frozen 2019, cboe_options=snapshot chains, more_vol=aggregate VIX family).
- Era files are PIT-safe as-is; if a consumer joins eras it is THEIR lookahead/splice
  decision — manifest split_of column marks every parent.

ROUND 4 DONE
## ROUND 5 (2026-09-08 ~08:3x CST) — charter (a): materialize + PIT-lint NEW FRED series for the R5 corners

READ FIRST done: coord/GATES_CONTRACT_V2.md (RATIFIED 2026-09-08) + DEAD_IDEAS.csv
recounted myself at round start: **130 rows** (charter said 120 at R4-end — dynamic,
recount discipline applied). Dead-family check: the HUNT_CREDIT2-R5 row killed
mortgage-spread RV / NFCI regime / CP-OIS stress (spread/STANDARDS classes); the
HUNT_CMDT2-R5 rows killed propane SPOT seasonality + trend + UNG-spread. My pre-registered
corner (from the prior session's saved probe, probe_r5_finalists_out.json, live
re-verified this session before any write): bank DELINQUENCY-RATE cycle (credit-QUALITY
class — a new signal class, not a spread family) for HUNT_CREDIT2, and the PPI propane
commodity INDEX (monthly, 1977+, a different object from the dead daily-spot series) for
HUNT_CMDT2. No signal hunted; no dead family re-tested; no dead signal re-tuned.

### (a) Deliverables: 3 NEW linted series = 3 level CSVs + 3 PIT vintage CSVs, 3/3 PASS
Fetch path: existing fred_dl.fetch/lint/write_csv + alfred_dl.fetch_first_release/
lint_vintage (charter-mandated reuse), orchestrated by work_r5/fetch_round5.py.
| series | role | delivered span | n | gap lint | PIT vintage | lag (measured, floor) | BREAK gate |
|---|---|---|---|---|---|---|---|
| DRALACBS (Delinquency Rate, All Loans, All Commercial Banks, quarterly, %) | credit-delinq-q (HUNT_CREDIT2 corner) | 1985-01-01..2026-04-01 | 166 | PASS, gaps=0 | n=61 first-release blocks (ALFRED birth 2011-05-24) | 136..166d, floor 130 | 0 structure events, 0 coincident breaks, refuse=False |
| DRCLACBS (Delinquency Rate, Consumer Loans, same panel) | credit-delinq-q | 1987-01-01..2026-04-01 | 158 | PASS, gaps=0 | n=61 (birth 2011-05-24) | 136..166d, floor 130 | clean, refuse=False |
| WPU05320104 (PPI by Commodity: Fuels: Propane, monthly, Index 1982=100) | energy-ppi-m (HUNT_CMDT2 corner) | 1984-01-01..2026-07-01 | 511 | PASS, gaps=0 | n=136 (birth 2015-03-13) | 37..105d, floor 35 | refuse=False; 9 >=30% market swings DISCLOSED, 0 coincide with structure events |

Files: tools/quant/data/more_fred/{DRALACBS,DRCLACBS,WPU05320104}.csv +
tools/quant/data/alfred/{sid}/vintage.csv (release_date, observation_date, value).
Manifest: +6 rows (level + ALFRED: vintage rows per the ICSA/PAYEMS convention,
lag_days=floor recorded) -> **166 rows**; PASS-row=>file invariant holds (verifier
whole-file sweep). DEAD_IDEAS: +2 status=data-acquired rows (source DATA_FREDMORE-R5)
-> **132 rows**.

### Fetcher run output (actual command output, python3 work_r5/fetch_round5.py)
DRALACBS: delivered n=166 1985-01-01..2026-04-01 gaps=0 | vintage n=61 lag 136..166d |
breaks(full)=0 refuse=False | PASS
DRCLACBS: delivered n=158 1987-01-01..2026-04-01 gaps=0 | vintage n=61 lag 136..166d |
breaks(full)=0 refuse=False | PASS
WPU05320104: delivered n=511 1984-01-01..2026-07-01 gaps=0 | vintage n=136 lag 37..105d |
breaks(full)=9 refuse=False | PASS
ALL-PASS (exit 0)

### Lint = 3 gates (charter spec)
1. GAP STRUCTURE: fred_dl.lint on native freq (quarterly/quarterly/monthly). Zero
   tolerance, all 3 PASS with gaps=0. Quarterly slot census: DRALACBS 166/166 slots,
   DRCLACBS 158/158 (no absent quarters).
2. PIT LAG: alfred first-release vintages; release_date >= observation_date + floor,
   floors derived from measured lags (DR 130d — Fed charge-off release lands ~4.5
   months after the quarter-start stamp; WPU 35d — BLS PPI ~41-44d). Fail-closed via
   lint_vintage. Consumers must lag by >= floor; 4.5mo PIT lag on the DR pair is LONG
   and is documented as the admission price of this data.
3. SOURCE-TRANSITION BREAK (DATA_COTMORE R4 pattern, generalized under TDD): a >=30%
   level step is a break ONLY if it coincides with a publication-structure event
   (suppressed '.' obs or absent grid slot); otherwise it is a market move, disclosed.
   WPU full history (587 obs): structure events = exactly the 3 dots 1983-04/08/12
   (a quarterly-publication interlude — 70/70 monthly slots present 1977-06..1983-03,
   dots every 3rd month 1983-04..12, monthly again 1984+); values are continuous across
   the interlude within 30% so the gate does NOT refuse; the broken head is TRIMMED to
   1984-01-01 (R2 DEXJPUS precedent, no splice) rather than delivered with holes.
   The 9 disclosed market steps: 1990-01 +95.8 (Dec-1989 record cold snap propane
   spike — no structure event anywhere near), 1990-03 -39.5, 1990-08 +30.2,
   1990-10 +36.7, 2000-03 +33.3, 2008-10 -33.3, 2014-12 -32.5, 2020-05 +33.4,
   2021-01 +44.3. DR pair: zero events, zero steps>=30%.

### Real catch of the round (PIT honesty): WPU 2015-10-01 suppressed at first release
Live ot4 probe: obs 2015-10-01 carries a DOT block realtime_start=2015-12-11 ->
realtime_end=2016-03-14 (value '.'), while today's level series has 92.2 there — the
value was backfilled later and the backfill block is ABSENT from ALFRED (the same FRED
omission class documented in R3). Consequence: the vintage stream has n=136 (not 137)
and exactly ONE post-birth coverage hole, 2015-10-01. Pinned by a dedicated test
(test_wpu_vintage_only_coverage_hole_is_documented_suppressed_obs) and the verifier —
any consumer backtesting must not treat vintage-2015-10 as publishable at release time.

### TDD (red first, exact numbers)
- RED: work_r5/test_fred_round5.py written first -> **12 failed** (no fetch_round5
  module, no files, no manifest rows, no DEAD_IDEAS rows).
- My own bugs caught en route (fixed before green): `dict(pass=...)` SyntaxError
  (pass is a keyword); wrong unpack of alfred_dl.fetch_first_release — it returns
  ((rows, n_missing), err), my caller took it as (rows, err) and crashed
  lint_vintage (TypeError int not subscriptable); a duplicated/dead code block in
  break_census; and a test asserting the census SUPPRESS non-coincident steps when
  the honest design DISCLOSES them (coincides=False) — test corrected to pin
  disclosure, not suppression.
- GREEN after fetcher run: **13/13 passed** (12 original, +1 for the 2015-10 vintage
  coverage pin added when the verifier surfaced it).
- Regression: tools/quant/data/more_fred/test_fred_dl.py **19/19 passed**;
  work_r4/test_cboe_opts_dl.py plain runner **ALL PASS** (21 checks).

### Independent verifier (every claim reproduces from a saved script)
work_r5/verify_round5.py -> verify_round5_output.txt: **64 PASS / 0 FAIL, exit 0**
(exit captured un-piped, R3/R4 lesson). Checks: independent re-lint of all 3 level
files from disk (n/start/end/gaps/order/no-NaN), PIT lag floors re-measured from the
vintage CSVs (>=130d DR, >=35d WPU), coverage-hole == documented set
({2015-10-01} for WPU, {} for DR pair), break census re-derived from the saved
wpu_full_history.json artifact (587 obs, 3 events, 9 disclosed swings, 95.8 first,
refuse=False), manifest honesty (6 new ids exactly-once, lint_pass=True =>
file on disk, lag_days floors recorded, whole-file PASS=>file sweep, 166 rows),
DEAD_IDEAS (2 DATA_FREDMORE-R5 rows both data-acquired, 132 total), LIVE equality
re-pull from api.stlouisfed.org (all 3 delivered files byte-value-equal to FRED,
delivered end == live max obs: 2026-04-01 / 2026-04-01 / 2026-07-01), corner
discipline (fetcher PLAN == exactly the 3 charter series; dead-family staging files
NFCICREDIT/NFCIRISK/RIFSPPFAAD01NB pre-date this round — mtime Sep 4 — and were not
written or re-tested by me). Verifier iterations were my own check bugs, fixed before
final green: read_rows() on a vintage CSV (header is release_date,..) and a 502
transient (retry added); one check asserted no dead-family file EXISTS when the real
claim is none was WRITTEN THIS ROUND — corrected to pin the PLAN + manifest writes.

### Honest limits / consumer guidance
- DR pair PIT lag is 136-166d (quarter-start obs stamp + Fed charge-off release) —
  the longest lag of anything in more_fred; a HUNT using it gets very stale signals.
  Vintage files start 2011-05-24 (ALFRED birth), so PIT backtests on the DR pair are
  2011+ only (level files reach 1985/1987 for non-PIT covariate work).
- WPU05320104 monthly PPI index is a PRICE LEVEL, not a total-return series; NSA;
  1983 quarterly interlude removed by head-trim (1984+ only); one obs (2015-10)
  unpublishable at first release (see catch above).
- DPROPANEMBTX (daily spot, 1992+) remains the only propane series with daily
  resolution; the two series are complementary (index vs spot), relationship NOT
  tested here (no signal hunting this round).
- Candidates probed and rejected en route: DPBUTANEBTX and WPU17511301 -> HTTP 400
  (invalid FRED ids), consistent with the DEAD_IDEAS propane row's note on invalid
  sibling ids. DRDLACBS/DRCCLACBS-style siblings were in the prior probe roster;
  the two delivered here were selected because titles/units verified clean.

ROUND 5 DONE


## ROUND 6 (2026-09-08 ~15:5x CST) — charter (a) fraud-catch cross-verification + (b) FRED health census

READ FIRST done: coord/GATES_CONTRACT_V2.md (in force; my round makes ZERO gates.run
calls — data-only verification, so no sig=/leak_check battery is owed under the V2 §0
two-track rule) + DEAD_IDEAS.csv recounted MYSELF: **145 data rows (146 lines incl
header)** at 15:49, mtime 14:55 today (row 145 = HUNT_SECTOR2-R6 "sector-rotation
covariates...", appended 14:55). Charter's "137 at R5-end" -> dynamic +8. My
dead_ideas_count.txt "146" records total LINES incl header — convention noted. No
dead family re-tested; no signal hunted; bt/ untouched; champion untouched (re-hashed
in-check: 4358dfab95679b97); no other agent's file written — my writes confined to
work_r6/.

Session provenance: a prior DATA_FREDMORE session today (15:19-15:39) left work_r6/
with the verifier + evidence but NO FINDINGS entry. I audited verify_round6.py
line-by-line (found one check-semantics caveat, C4, below), then re-executed
everything fresh this session and added one NEW discriminator test the prior session
did not run live.

### (a) FRAUD-CATCH: DATA_ETF_MORE R5 (bench pack) — verdict GENUINE, one clobber flagged

- §7c trio pins re-hashed byte-identical: twelvedata/SPY.csv d35d72808dcc9fc3,
  more_etf/IEF.csv 603cb2a56afd5616, sleeve_library/CTA_15vol.csv d7f3b5cd4616f0f4.
- All 7 candidates independently re-measured from raw CSVs (my own loader, NO import
  of their modules): UUP max|corr|trio 0.1833 (spy -0.1833/ief -0.1480/cta -0.0156/
  champ 0.0028, n=4911), GLD 0.2043 (0.0628/0.2043/0.0553/0.0119, n=5483), SLV
  0.2294, IAU 0.2056, GSG 0.3705, DBC 0.3789, TIP control corr_ief 0.7635 > 0.5 ->
  rejected as pre-registered. Every number matches their manifest to 4dp.
- Selection rule reproduced: rank asc = UUP 0.1833 < GLD 0.2043 < IAU 0.2056 < SLV
  0.2294 < GSG 0.3705 < DBC 0.3789; pair corrs SLV|IAU 0.7974, GLD|IAU 0.9969,
  GLD|SLV 0.7973 (all > 0.7 -> gold-complex dup skips) and UUP|GLD -0.4077 (<= 0.7)
  -> greedy pick UUP+GLD is FORCED. span_class pins match (UUP 2007plus PASS_WAIVER;
  GLD/TIP/SLV/IAU pre2007; DBC/GSG 2007plus).
- Consumption smoke via bt.beats_passive on champion span: spy_bh 0.5863 /
  sixty_forty 0.5916 / cta_trend -0.1097, best=sixty_forty — exact.
- **THE CATCH: tools/quant/data/bench_r5/manifest.csv was CLOBBERED today 14:10-14:40**
  (10 rich rows -> 47-byte stub header `family,file,date_col,kind,rows,cols,exception`)
  by the DATA_ORGANIZE canonicalization sweep (README restamped "Generated:
  2026-09-08" + canonical-layout line — charter-legitimate scope for that agent).
  **Discriminator test (NEW this session): I re-ran THEIR committed build() with
  out_path redirected to my evidence dir (zero shared-tree writes) — my fresh rebuild
  hashes sha16 326afe5a28db2809 == their claimed sha == the prior session's saved
  rebuild == BYTE-IDENTICAL, 10 rows.** So their R5 manifest is fully deterministic
  from their committed script: the R5 claim is GENUINE; the on-disk loss is a layout
  sweep, not data fraud. Evidence: work_r6/evidence/{etfmore_rebuild_manifest_RERUN_1600.csv
  (mine), etfmore_rebuild_manifest.csv (prior), bench_r5_manifest_asfound_153813.csv
  (as-found stub)}. FLAG FOR COORDINATOR: decide stub-vs-restore; restore is cheap
  and safe because byte-reproducible. I did NOT restore it (not my file).

### (a) FRAUD-CATCH: DATA_COTMORE R5 (trader_count_panel) — verdict GENUINE, reproduced

- Vintage pins re-hashed: work_r5/trader_count_panel.csv 9e2c82303acf4c24 (R4 panel
  02aa8f0028144d9d); 2026 zips fut_disagg 70e18ad5a7e61745 / fut_fin 7b744b8c6b241008;
  .sep3.bak pair 3e816c649e39c016 / 0d3a015f09b47a05 — all match their MANIFEST_R5.
- My own csv reader (their modules not imported): **29,051 rows x 51 cols x 35
  families, span 2010-01-05..2026-09-01**; new week 2026-09-01 = exactly 34 families,
  release_date all 2026-09-04 (next-Friday rule holds for all 34).
- Delta vs R4: 0 dropped pairs, added = exactly 34 rows, **0 changed cnt_ cells
  across 29,017 shared rows** — pure append, zero CFTC revisions Sep-3->Sep-8 vintage.
- BREAK anchors byte-stable at exact date+magnitude: nat_gas_nymex 2022-02-08
  281.0->40.0 (-86%), lumber 2023-04-25 21.0->43.0 (+105%).
- MY OWN live spot-fetch: CFTC fut_disagg_txt_2026.zip pulled fresh from
  www.cftc.gov n=1,685,920 bytes sha16 70e18ad5a7e61745 == pin (vintage integrity
  live-confirmed today, not just trusted from disk).

### (a) CBOE PCR freeze — independently re-verified today

put_call_ratios/_all.json still HTTP 403; all 3 archive CSVs re-fetched live from
cdn.cboe.com are BYTE-IDENTICAL to on-disk (totalpc 139,830 B sha 0c49f75637aa8315;
equitypc 135,696 B 2e73b05586b558d6; spxpc 98,266 B 68e1ae6d3b202cf1), frozen at
2019-10-04 (3,253/3,253/2,330 data rows + their newline-count convention
3,256/3,256/2,332). Their R5 FROZEN verdict stands.

### (b) FRED endpoint health census (CAMP_COST sleeve-refresh lane) — NOT BLOCKED

- Charter-pinned R5 artifacts on disk confirmed: CAMP_BORROW/work_r5/fred_dff.csv
  n=26,363 last 2026-09-03; fred_sofr.csv n=2,198 last 2026-09-03 (both fresh at R5
  as the charter states).
- LIVE re-fetch from api.stlouisfed.org now: **DFF latest obs 2026-09-03 = 3.63;
  SOFR 2026-09-03 = 3.66** — both at 09-03, endpoint healthy, NO series blocking a
  refresh from the FRED side.
- Wider lane (CAMP_COST/CAMP_SHORT charters): DJFUELUSGULF live 2026-09-01 = 4.19
  (weekly, normal T+2 lag); WTISPLC live 2026-08-01 = 83.9 (monthly, as designed).
- Refresh blockers listed: NONE upstream. On-disk more_fred copies ARE stale —
  more_fred/DFF.csv n=26,361 end 2026-09-01 (mtime 09-03 15:11); more_fred/SOFR.csv
  n=2,103 end 2026-09-02 (mtime 09-03 22:18). Quiet-data-tree round: documented, NOT
  refreshed by me. The refresh lane is clear for whoever holds that charter.
- HONEST CAVEAT (my verifier's weakest check): C4 "no revision at the boundary"
  compares on-disk last row (DFF 09-01 / SOFR 09-02) against live LATEST (09-03) —
  cross-date, not same-date. DFF 3.63==3.63; SOFR 3.65 vs 3.66 is adjacent-day drift,
  not a revision. Harmless (C3 already documents the staleness) but the check NAME
  overstates what it proves.

### Independent verifier — fresh re-run this session

work_r6/verify_round6.py re-executed end-to-end (live FRED + CFTC + CBOE fetches):
**99 PASS / 0 FAIL, exit 0** (captured un-piped, exit code checked; output at
work_r6/verify_round6_output.txt). Verifier design: NO imports of either sibling's
modules — every claimed number re-derived from raw artifacts + live endpoints.

### Round verdict

Both sibling R5 verdicts REPRODUCED and CONFIRMED GENUINE (0 fraud found in claims;
1 file clobber found, cause identified as DATA_ORGANIZE's sweep, content proven
byte-reproducible, evidence preserved, coordinator flag raised). FRED lane healthy;
zero refresh blockers; DFF/SOFR on-disk staleness documented. Champion of record
untouched: 4358dfab95679b97. Honest frontier UNCHANGED. DEAD_IDEAS: no rows appended
by me (data-verification round, precedent: my R4/R5 data-deliverable disposition).

ROUND 6 DONE

## ROUND 7 (2026-09-09 00:2x CST) - PIT vintage restoration (a) + refresh lane (b)

Session provenance: two prior instances died mid-round on API 429s (one left
restore_pit_manifest.py + test_r7_restore.py + a regenerated manifest + verifier edits,
no FINDINGS entry; one was killed right after reading the charter). This session
audited everything they left on disk BEFORE trusting it, then re-executed all
verification live. No code from the dead sessions is trusted unverified.

### (a) CENTERPIECE - PIT manifest restoration: DONE and verified

State found on disk (crash artifacts of the DATA_ORGANIZE 14:40 sweep):
 - tools/quant/data/alfred/manifest.csv: header-only after the sweep; restored by the
   dead session at 23:32 as a purpose-built 21-col PIT manifest (3 data rows:
   DRALACBS / DRCLACBS / WPU05320104), registered in DATA_ORGANIZE's
   rich_manifest_registry.json ("alfred" pin, two-way fail-closed: regen guard refuses
   flatten; a rich manifest losing a required col OR regaining canonical fails the test).
 - The two defects I (.remember 23:26) had flagged in the dead session's manifest were
   ALREADY FIXED on disk before this session: (1) literal `obs+%dd` placeholder -> now
   formatted per-row (`obs+130d` / `obs+130d` / `obs+35d`); (2) the WPU-only 2015-10-01
   coverage-hole note was attached to ALL rows -> now WPU-only (T7 asserts both, and
   asserts the note against the disk fact: WPU obs SKIP 2015-10-01, both DR series HAVE
   2015-10-01 - so the cross-series claim would have been false).

Verification executed live THIS session (exact numbers):
 - work_r7/test_r7_restore.py: 8 passed / 0 failed in 7.65s (T1 PIT facts re-derived
   from disk incl. lag 136..166d vs floor 130d for the DR pair and 37..105d vs floor
   35d for WPU; T1b non-canonical header; T2 registry pin; T3 organize_lib regen guard
   raises ManifestRegenerationRefused on write_manifest("alfred"); T4 more_fred canonical
   144 rows + file<->row bijection intact; T5 verify_round5 subprocess -> 64/0;
   T6 C4 same-date source assertions; T7 per-series notes).
 - verify_round5.py re-run directly: exit 0, "VERIFY ROUND 5: 64 PASS / 0 FAIL"
   (dead_ideas recount line: total rows 152, R5 pin 132 superseded, R7-start count
   re-derived live).
 - verify_round6.py re-run directly: exit 0, 99 PASS / 0 FAIL (99 `ok` lines counted).
   C4 is now honestly labeled "same-date revision check": DFF disk 3.63 ==
   live-at-2026-09-01 3.63; SOFR disk 3.65 == live-at-2026-09-02 3.65. The R6 FINDINGS
   caveat is resolved: the 3.65-vs-3.66 "drift" was pure cross-date comparison, ZERO
   actual revision at either boundary.
 - crosscheck_alfred_live.py: exit 0, all 3 series value-equal to a FRESH live ot4 pull
   from api.stlouisfed.org: DRALACBS live n=61 disk n=61 mism=0; DRCLACBS 61/61 mism=0;
   WPU05320104 136/136 mism=0 (lags 136..166d / 136..166d / 37..105d; vintagedates
   endpoint returns 62/62/140 - current-cycle/suppressed vintages carry no ot4 rows,
   value-equality vs ot4 is the gate and it is EXACT).
 - Provenance byte-compare: restored vintage.csv shas 5553a1cfc43bb8d9 / 6eb4ee6726fe3b89
   / f21ed8a48ffd54d8 are BYTE-IDENTICAL to CAMP_BORROW/work_r6/vintage_rebuilt/
   (the charter-named source) - sha256_16 manifest cells re-derived from disk match.
 - Atomicity + idempotency: restore_pit_manifest.py re-run this session -> exit 0,
   manifest sha 53f43abe4f629df3 BEFORE == AFTER (temp + os.replace, no
   truncate-then-crash window; identical bytes on rerun).
 - Verifier staleness pins updated per charter arithmetic ("update YOUR pin, not the
   manifest"): verify_round5.py now asserts the canonical more_fred manifest at 144 data
   rows + the alfred PIT manifest exists as a registered rich manifest (not canonical-
   flat); the 166-vs-145 stale-pin diff is gone - verifier at 64/0.

### (b) Refresh lane: CONDITION NOT TRIGGERED - documented, no refresh performed

 - CAMP_COST R7 is COMPLETE (their FINDINGS ends ROUND 7 DONE; 50/50 suite; bt 444/0;
   RAWEW15_REFRESH_CANDIDATE_daily.csv sha 8d7e711e6d05a2b1 + weights 8c19ef227cf9b7b0
   staged for coordinator adoption). Their (a) centerpiece consumed their OWN staged
   work_r6/refresh/ sleeves (brwt10/7/5 -> 08-28, diescrack -> 08-24) - grep of their
   work_r7 scripts references NEITHER more_fred/DFF.csv NOR SOFR.csv.
 - Therefore the charter's conditional ("DFF/SOFR on-disk staleness may be refreshed if
   CAMP_COST's (a) needs it") does NOT fire. On-disk staleness stands, documented:
   more_fred/DFF.csv end 2026-09-01 (mtime 09-03 15:11), more_fred/SOFR.csv end
   2026-09-02 (mtime 09-03 22:18); CAMP_BORROW's fresh work_r5 copies end 09-03.
   Upstream endpoint health re-verified in R6 and again today by verify_round6 C1-C3
   (live DFF/SOFR fetched same-session, 99/0).
 - C4 renamed rather than deleted: same-date semantics, honest label, zero revisions
   found at either boundary.

### Pins re-verified fresh this session (independent, my own loader)

 - Champion of record campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv:
   sha256_16 4358dfab95679b97 BYTE-MATCH; independent recompute from the CSV
   (my own loader, no bt import): n=4805, 2008-03-31..2026-08-27, SR 3.1810 EXACT,
   MDD -6.6922 EXACT, 0 negative years (nav convention: geometric ann 37.19 pct ==
   charter pin; arithmetic 32.14 pct is the same data, different annualization).
   Coordinator's 18:3x standup pin verify_champion_standup_1830.json read: ok=true,
   weights_repro max_dev 2.22e-16, byte_repro 1.11e-16, cost 5.2622307199 bp/yr
   full_dw, causal mechanism nav.shift(1).
 - DEAD_IDEAS.csv recount: 152 rows (charter said 145-146 at R6-end, dynamic by
   design; CAMP_COST counted 151 at their R7 start). No dead-family re-test; my
   round is the charter pre-registered PIT-restoration corner. No rows appended by me.
 - Data-tree byte-stability: 3 vintage CSVs + 3 more_fred level CSVs at their 14:56
   restore bytes; the ONLY file my round changed under tools/quant/data/ is
   alfred/manifest.csv (sha 53f43abe4f629df3, idempotent). bt/ untouched. No other
   agent's file written.

### Round verdict

Charter (a) COMPLETE: PIT vintages restored, live-verified, manifest regenerated
atomically + idempotently, registry-pinned fail-closed, verifier back to 64/0, and the
R6 C4 honesty caveat fixed to same-date semantics (99/0). Charter (b) resolved as
NOT-TRIGGERED with evidence (the conditional consumer never needed the stale files;
staleness documented; endpoint health clean). Champion of record untouched and
independently re-verified. Honest frontier UNCHANGED (37.2 vs 80 goal).

ROUND 7 DONE
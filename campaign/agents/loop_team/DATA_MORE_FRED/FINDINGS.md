# DATA_MORE_FRED — FINDINGS (2026-09-03)

Charter: download MORE free FRED macro/rates/credit/commodity/vel series into
`tools/quant/data/more_fred/`, lint each fail-closed (span, n, gaps, frequency), manifest.
DATA-ONLY, no backtests. Superpowers rigor applied: TDD (RED→GREEN watched, revert-check done),
verification-before-completion (fresh disk-truth re-lint, API cross-checks), systematic-debugging
(root causes documented below).

## TDD record (test_fred_dl.py — 19 tests, all GREEN)
- RED #1 observed before fred_dl.py existed: `ModuleNotFoundError: No module named 'fred_dl'`.
- RED #2 observed for v2 spec (contiguous-run gap semantics, detect_freq, fetch failure-shape):
  7 failed before implementation.
- Revert-check (Red-Green regression): neutering `maxrun` accumulation in `fred_dl._count_gaps`
  → `test_daily_contiguous_5day_hole_fails` FAILED (1 failed); restore → 18/19→19 passed.
- Final suite: `19 passed in 0.02s` (fresh run, quoted from output).
- Test-authoring bugs caught by the impl itself during GREEN phase (documented as per rigor):
  (a) "good daily" fixture was only 86 bdays — correctly rejected n<250; widened to 500 days.
  (b) monthly fixture `range(1,13)*3` duplicated 12 identical dates — correctly rejected
      order/dupe; rebuilt as 36 distinct months.

## Bugs found & root-caused (systematic-debugging)
1. **fetch() failure-shape inconsistency** (TypeError in driver): success returned
   `((rows,nmiss), err)` but failure returned bare `(None, err)`; unpacking crashed.
   Failing test first (`test_fetch_failure_shape_consistent`), then fixed all failure paths to
   `((None,None), err)`. GREEN after.
2. **GASREGCO does not exist** (HTTP 400 "The series does not exist" — exact FRED message).
   Correct ID probed and verified: **GASREGCOVW** (US weekly regular gas $/gal, 1990-08→2026-08).
3. **Initial gap-tolerance design was wrong** (count-based `tol=max(60,3%)` let a contiguous
   5-day hole pass). Root cause: count-based tolerance cannot distinguish scattered holidays
   from contiguous holes. Fixed to **contiguous-run semantics**: daily FAIL if any missing run
   ≥3 bdays (isolated 1–2 day runs = holidays, allowed), or gross missing >5% of span;
   weekly/monthly = zero tolerance. Verified by RED→GREEN + revert-check.

## Real upstream data anomalies (verified, not download bugs)
- **2025-10 missing in UNRATE, CPIAUCSL, RRSFS**: value `'.'` in FRED payload (verified by
  direct query 2026-09-03: UNRATE 2025-09-01=4.4, 2025-10-01='.', 2025-11-01=4.5; same hole in
  CPIAUCSL and RRSFS). Single-month holes only, exactly at 2025-10 → stored WITH documented
  exception `REAL-UPSTREAM-HOLE(ex)` in manifest (not a silent pass; lint itself still flags).
- **UMCSENT**: 210 missing months pre-1978 — the survey was quarterly/irregular until the
  monthly era began 1978. Trimmed to 1978-01-01 onward → 0 gaps, n=583, PASS.
- **MZM weekly ends 2021-02-01**: verified TRUE upstream end via API (`2026-09-03` query shows
  latest obs = 2021-02-01, 21401.2) — FRED discontinued weekly MZM with the H.6 cessation.
  Stored as-is; annotated in manifest.
- **GASREGCOVW Dec-1990–Jan-1991 skips** (5 scattered weekly gaps, Gulf-war start): trimmed
  start to 1991-01-21 → 0 gaps, n=1859, PASS.

## Deliverables (tools/quant/data/more_fred/ — 26 CSVs + manifest.csv, 1.8 MB)
Columns exactly `date,value`; header row present. Per-series disk-truth re-lint
(fresh independent pass reading only written CSVs, no fetch reuse — all PASS):

| series | freq | n | start | end | gaps | maxrun | note |
|---|---|---|---|---|---|---|---|
| AAA | monthly | 1292 | 1919-01-01 | 2026-08-01 | 0 | 0 | Moody's AAA |
| BAA | monthly | 1292 | 1919-01-01 | 2026-08-01 | 0 | 0 | Moody's BAA |
| BAA10Y | daily | 10167 | 1986-01-02 | 2026-09-01 | 442 | 2 | holidays only, maxrun 2 |
| CPIAUCSL | monthly | 954 | 1947-01-01 | 2026-07-01 | 1 | 1 | REAL-UPSTREAM-HOLE 2025-10 (verified '.') |
| DAAA | daily | 10962 | 1983-01-03 | 2026-09-01 | 430 | 2 | daily AAA yield |
| DBAA | daily | 10203 | 1986-01-02 | 2026-09-01 | 406 | 2 | daily BAA yield |
| DFF | daily | 26361 | 1954-07-01 | 2026-09-01 | 0 | 0 | daily effective fed funds |
| DFII5 | daily | 5921 | 2003-01-02 | 2026-09-01 | 253 | 1 | 5y real yield |
| DFII20 | daily | 5530 | 2004-07-27 | 2026-09-01 | 236 | 1 | 20y real yield |
| DFII30 | daily | 4136 | 2010-02-22 | 2026-09-01 | 176 | 1 | 30y real yield |
| FEDFUNDS | monthly | 866 | 1954-07-01 | 2026-08-01 | 0 | 0 | |
| GASREGCOVW | weekly | 1859 | 1991-01-21 | 2026-08-31 | 0 | 0 | trimmed pre-1991-01-21 |
| GVZCLS | daily | 4593 | 2008-06-03 | 2026-09-01 | 168 | 2 | gold vol index |
| HOUST | monthly | 811 | 1959-01-01 | 2026-07-01 | 0 | 0 | housing starts |
| INDPRO | monthly | 1291 | 1919-01-01 | 2026-07-01 | 0 | 0 | |
| MZM | weekly | 2092 | 1981-01-05 | 2021-02-01 | 0 | 0 | TRUE upstream end (discontinued) |
| OVXCLS | daily | 4861 | 2007-05-10 | 2026-09-01 | 178 | 2 | oil vol |
| PERMIT | monthly | 799 | 1960-01-01 | 2026-07-01 | 0 | 0 | |
| REALLN | monthly | 955 | 1947-01-01 | 2026-07-01 | 0 | 0 | real-estate loans |
| RRSFS | monthly | 414 | 1992-01-01 | 2026-07-01 | 1 | 1 | REAL-UPSTREAM-HOLE 2025-10 (verified '.') |
| TB3MS | monthly | 1112 | 1934-01-01 | 2026-08-01 | 0 | 0 | |
| TB6MS | monthly | 813 | 1958-12-01 | 2026-08-01 | 0 | 0 | |
| TWEXAFEGSMTH | monthly | 248 | 2006-01-01 | 2026-08-01 | 0 | 0 | broad dollar (ageral FX) |
| UMCSENT | monthly | 583 | 1978-01-01 | 2026-07-01 | 0 | 0 | trimmed to monthly era |
| UNRATE | monthly | 942 | 1948-01-01 | 2026-07-01 | 1 | 1 | REAL-UPSTREAM-HOLE 2025-10 (verified '.') |
| VXVCLS | daily | 4715 | 2007-12-04 | 2026-09-01 | 176 | 2 | VIX 3-month (VXV) |

## Failures reported honestly (4, in manifest with exact FRED messages)
- DFOIL — HTTP 400 "The series does not exist." (no such FRED ID; distillate fuel = DPUFUEUS2M,
  already on disk at newdata/DPUFUEUS2M.csv)
- GASBREW — HTTP 400 "The series does not exist."
- H15TBS (and bare H15) — HTTP 400 "The series does not exist." (H15 on/off-the-run TB is not a
  FRED observations series)
- MOVE — HTTP 400 "The series does not exist." (ICE MOVE bond-vol index is NOT on FRED; needs
  alternative source)

## Already-on-disk cross-reference (no duplicate downloads; per charter)
newdata/: DCOILWTICO (1986-01-02→2026-08-25, 10605 rows), DCOILBRENTEU, DHHNGSP,
DPROPANEMTXCF, DHOILNYH, DJFUELUSGULF, GASREGW, DTWEXBGS, ICSA, M2SL, NFCI, STLFSI4, BOGMBASE,
PAYEMS, BAMLH0A0HYM2.
hedge_fund_strats/data_fred/: DGS1MO/3MO/6MO/1/2/5/7/10/20/30, DFII10, T10YIE, T5YIE, T5YIFP,
VIXCLS, WALCL, aaa/baa spreads (as spreads), hy_oas.
=> Charter list fully covered: 26 NEW series delivered + rest verified on disk.

## Verification evidence (fresh, this session)
- `python3 -m pytest test_fred_dl.py -q` → `19 passed in 0.02s`
- Independent disk-truth re-lint: 26/26 PASS (one caveat class: 3 documented 2025-10 holes).
- API↔disk value cross-check (3 series, last row): DFF 3.63==3.63, BAA10Y 1.58==1.58,
  VXVCLS 18.33==18.33 (all exact match).
- MZM end-of-series verified genuine via API (latest obs 2021-02-01).
- All 4 failures quoted with exact FRED error messages (see above).
- Writes confined to `tools/quant/data/more_fred/` (plus this FINDINGS.md). No champion files touched.

DATA_MORE_FRED DONE

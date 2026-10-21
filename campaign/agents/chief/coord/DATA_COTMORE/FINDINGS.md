# DATA_COTMORE — ROUND 1 (2026-09-06)

Charter: verify the more_cot COT positioning universe (lint gates), map every market to a
LIQUID price proxy, deliver a CLEANED universe manifest for engine-hunt agents. Download
only what's missing.

## What was there (verified, no download needed)

tools/quant/data/more_cot/ held 106 positioning CSVs across 3 families of builders:
- 35 legacy disagg markets `<fam>_cot.csv` (net_noncomm, col `net_noncomm_pct_oi`, weekly Tue)
- 52 TFF category series `tff_<fam>_<cat>.csv` (13 fin families x 4 categories, col `pct_of_oi`)
- 14 CIT series `cit_<fam>.csv` (col `cit_pct_oi`), + 3 manifests (manifest.csv / _tff / _cit)
All 3 existing manifests already report lint=PASS on all rows (CFTC rename-audited matcher,
collision-by-priority, jump/gap gates). My throwaway scan of all 106 files: 0 parse failures,
0 duplicate dates, 0 NaN — the prior sessions' data is clean. Task = gates + proxy mapping,
not re-fetching.

## TDD: lint_cot_universe.py (11 tests, RED->GREEN)

New: `more_cot/lint_cot_universe.py` + `more_cot/test_lint_cot_universe.py`.
RED first (ModuleNotFoundError), then 11 tests covering: parse (bad pct rejected),
span>=522w (10y), gap>9d fails, gap=9d exactly passes, duplicate dates fail,
pct outside [-1,1] fails, proxy overlap/tradeable_from arithmetic, proxy-after-COT-end
=> overlap 0, real-tree integration (all families mapped + gated), manifest written.
Final: 11/11 GREEN; full more_cot suite 41/41 GREEN (no regressions to prior sessions' tests).

Gate semantics decision (test-locked): soft-gate violations (span, gap) keep MEASURED stats
in the manifest with usable=false + FAIL reason — engine agents see why a market is excluded
and how much data exists; hard violations (parse, |net|>OI, pct range, duplicates) produce no
stats at all. Fail-closed, never silently dropped.

## Deliverable: more_cot/universe_manifest.csv — 35 families, 33 PASS / 2 FAIL (honest)

33 PASS markets (family | COT span | price proxy | proxy span | tradeable_from):

| market | COT span | proxy | proxy span | tradeable-from |
|---|---|---|---|---|
| cocoa | 2010-01..2026-08 16.6y | FRED PCOCOUSDM (spot, monthly) | 1992-01..2026-07 | 2010-01-05 |
| coffee_c | 2010-01..2026-08 16.6y | FRED PCOFFOTMUSDM (spot, monthly) | 1992-01..2026-07 | 2010-01-05 |
| copper | 2010-01..2026-08 16.6y | more_etf/CPER (USCP ETF, daily) | 2011-11..2026-09 | 2011-11-15 |
| corn | 2010-01..2026-08 16.6y | more_etf/CORN (daily) | 2010-06..2026-09 | 2010-06-09 |
| cotton_no2 | 2010-01..2026-08 16.6y | FRED PCOTTINDUSDM (spot, monthly) | 1992-01..2026-07 | 2010-01-05 |
| crude_wti_nymex | 2010-01..2026-08 16.6y | more_etf/USO (daily) | 2006-10..2026-09 | 2010-01-05 |
| dow_emini | 2010-07..2026-08 16.1y | twelvedata/DIA (daily) | 2006-09..2026-08 | 2010-07-20 |
| eur | 2010-07..2026-08 16.1y | ecb_fx/USD (ECB ref, daily) | 1999-01..2026-09 | 2010-07-20 |
| eurodollar_3m | 2010-07..2023-06 12.9y | FRED SOFR (daily) [ED sunset] | 2018-04..2026-09 | 2018-04-03 |
| feeder_cattle | 2010-01..2026-08 16.6y | more_etf/DBA (ags basket, daily) | 2007-01..2026-09 | 2010-01-05 |
| gbp | 2010-07..2026-08 16.1y | ecb_fx/GBP (ECB ref, daily) | 1999-01..2026-09 | 2010-07-20 |
| gold | 2010-01..2026-08 16.6y | more_etf/GLD (daily) | 2006-10..2026-09 | 2010-01-05 |
| jpy | 2010-07..2026-08 16.1y | ecb_fx/JPY (ECB ref, daily) | 1999-01..2026-09 | 2010-07-20 |
| lean_hogs | 2010-01..2026-08 16.6y | more_etf/DBA (ags basket, daily) | 2007-01..2026-09 | 2010-01-05 |
| live_cattle | 2010-01..2026-08 16.6y | more_etf/DBA (ags basket, daily) | 2007-01..2026-09 | 2010-01-05 |
| lumber | 2010-01..2026-08 16.6y | more_etf/ITB (builders, daily) | 2006-10..2026-09 | 2010-01-05 |
| nasdaq_emini | 2010-07..2026-08 16.1y | twelvedata/QQQ (daily) | 2006-09..2026-08 | 2010-07-20 |
| nat_gas_nymex | 2010-01..2026-08 16.6y | more_etf/UNG (daily) | 2007-04..2026-09 | 2010-01-05 |
| rough_rice | 2010-01..2026-08 16.6y | more_etf/DBA (ags basket, daily) | 2007-01..2026-09 | 2010-01-05 |
| silver | 2010-01..2026-08 16.6y | more_etf/SLV (daily) | 2006-10..2026-09 | 2010-01-05 |
| soybean_meal | 2010-01..2026-08 16.6y | more_etf/SOYB (daily) | 2011-09..2026-09 | 2011-09-19 |
| soybean_oil | 2010-01..2026-08 16.6y | more_etf/SOYB (daily) | 2011-09..2026-09 | 2011-09-19 |
| soybeans | 2010-01..2026-08 16.6y | more_etf/SOYB (daily) | 2011-09..2026-09 | 2011-09-19 |
| sp500_emini | 2010-07..2026-08 16.1y | twelvedata/SPY (daily) | 2006-09..2026-08 | 2010-07-20 |
| sugar_no11 | 2010-01..2026-08 16.6y | more_etf/CANE (Teucrium SUGAR, daily) | 2011-09..2026-09 | 2011-09-19 |
| us_10y_note | 2010-07..2026-08 16.1y | more_etf/IEF (daily) | 2006-10..2026-09 | 2010-07-20 |
| us_2y_note | 2010-07..2026-08 16.1y | more_etf/SHY (daily) | 2006-10..2026-09 | 2010-07-20 |
| us_5y_note | 2010-07..2026-08 16.1y | more_etf/IEF (7-10y; no 5y ETF on disk) | 2006-10..2026-09 | 2010-07-20 |
| us_tbond | 2010-07..2026-08 16.1y | more_etf/TLT (daily) | 2006-10..2026-09 | 2010-07-20 |
| vix | 2010-07..2026-08 16.1y | more_vol/VIX (index, daily) | 1990-01..2026-09 | 2010-07-20 |
| wheat_hrspring | 2014-03..2026-08 12.4y | more_etf/WEAT (SRW fund; sector proxy) | 2011-09..2026-09 | 2014-03-25 |
| wheat_hrw | 2013-12..2026-08 12.7y | more_etf/WEAT (SRW fund; sector proxy) | 2011-09..2026-09 | 2013-12-17 |
| wheat_srw | 2010-01..2026-08 16.6y | more_etf/WEAT (daily) | 2011-09..2026-09 | 2011-09-19 |

2 FAIL (kept in manifest with measured stats + reason, fail-closed):
- canola: span 421w < 522w (8.0y). ICE canola CFTC reporting only began 2018-08-07. Proxy
  mapped (DBA) but the positioning history itself is <10y. Not fixable by download.
- sofr_3m: span 422w < 522w (8.1y) + single 14d gap 2018-09-18->2018-10-02 (contract's
  2018-07 launch year). Same story: SOFR futures only exist since 2018.
- oats: EXCLUDED from manifest entirely (matcher already refuses it; 294d CFTC reporting
  suspension 2024-11..2025-09 = dead contract, OI 4.4-4.7k at end).

TFF (52) and CIT (14) series: same families as the disagg universe, category breakdowns.
Their own manifests already lint PASS (841w weekly, gaps<=8, jump<0.6). Not re-linted by
the new script; engine agents should treat tff_*/cit_* per-family availability as identical
to the disagg family list above.

## Proxy-mapping catches (things that would have bitten an engine agent)

1. CANE is Teucrium SUGAR, not canola. Any "canola=CANE" mapping would have paired canola
   positioning with sugar prices. Canola has NO US-listed ETF (iPath CAN delisted) — mapped
   to DBA basket, flagged, and then excluded anyway on the span gate.
2. Copper upgraded monthly->daily: round started with FRED PCOPPUSDM (monthly, freq=31d —
   unusable for a weekly-signal engine). Fetched more_etf/CPER.csv via twelvedata
   (charter-sanctioned: missing liquid proxy): 2011-11-15..2026-09-04, n=3722, max_gap=5d,
   zero_ret_rows=374. Copper now tradeable-from 2011-11-15 on a daily proxy.
3. Sugar upgraded monthly->daily the same way (CANE on disk, daily since 2011-09-19,
   n=3762): tradeable-from 2011-09-19. Probe confirmed NIB/JO/SGG/BAL all HTTP 404 (iPath
   softs ETNs delisted 2023), so cocoa/coffee/cotton stay on monthly FRED spot — the only
   honest option; flagged proxy_kind=spot_m + freq=31d in the manifest so engines can
   downsample or exclude deliberately.
4. eurodollar_3m is a SPLIT universe: positioning 2010-07..2023-06 (ED futures stopped
   reporting after June 2023), proxy SOFR only from 2018-04. Overlap window 2018-04..2023-06
   (272w). Do not treat as a 16y continuous series.
5. us_5y_note has no 5y ETF on disk; mapped to IEF (7-10y duration bucket) — same duration
   direction, coarser. Flagged in manifest comment.
6. Livestock/rice/canola have no liquid single-commodity ETF on disk (COW delisted 2023,
   iPath ags gone). DBA basket is the honest sector-level proxy, flagged proxy_kind=etf
   with note; engines wanting pure contract economics should use these families only for
   positioning-vs-sector studies.
7. Proxy column conventions differ by dir: more_etf/twelvedata use `date,close`;
   more_fred/newdata use `date,value` or `observation_date,<SERIES_ID>`; ecb_fx uses
   `date,value`. The manifest records each file's date col + value col + median frequency
   (proxy_freq_days) — engines should read through the manifest, not hand-roll loaders.

## Where the manifest lives

- more_cot/universe_manifest.csv (35 rows, columns: family, lint, cot_file, start, end,
  n_weeks, span_years, max_gap_days, proxy, proxy_kind, proxy_start, proxy_end,
  proxy_span_weeks, proxy_overlap_weeks, proxy_freq_days, proxy_note, tradeable_from, fails)
- Rebuild: `python3 lint_cot_universe.py` (exit 1 if any FAIL — the 2 known FAILs mean
  round-1 exit is 1 by design; engines should read the CSV, not trust exit code)
- Tests: `python3 -m pytest more_cot/ -q` -> 41 passed (11 new + 30 prior)

## Downloads this round (only what was missing, per charter)

- 1 new file: more_etf/CPER.csv (USCP copper ETF, daily closes via twelvedata, 3722 rows).
  Nothing else was missing — every listed charter market either had a proxy on disk or is
  documented above as excluded/flagged.

ROUND 1 DONE


---

# DATA_COTMORE — ROUND 2 (2026-09-07)

Charter: (a) extend CIT coverage via cit_* infra; (b) document eurodollar_3m split universe
in the manifest; (c) shared daily price-alignment helper + tests; (d) re-run lint; engines
read the CSV manifest, not exit codes.

## State on arrival

A prior session (Sep 7 03:2x) had already landed part of r2(b): lint_cot_universe.py carried
SPLIT_CUTOFF_DATE logic, PASS_WITH_EXN flags, and 3 tests (suite 48/48 green). This round
audited that work, kept it, and closed the remaining gaps.

## (a) CIT coverage: ALREADY COMPLETE — corrected a false R1 claim with measured numbers

Exhaustive audit of _raw_cit/dea_cit_txt_2010..2026.zip (17 zips, 11,128 data rows,
0 unparseable): exactly 15 distinct CFTC market names -> 13 matched families -> 13 built
cit_<fam>.csv. Zero unmatched names (the CFTC CIT supplemental report covers only these 12
contracts — no metals, energy, or financials by design; wheat accounts for 2 of the 13
families via the 2013 KCBT->CBOT rename). Row-count identity check: 10x869 + 700 +
206+206+663+663 = 11,128 = raw total, so the builder dropped nothing. soybean_meal's
2013-04-02 start is CFTC-side (verified 0 rows in the 2010/2011/2012 zips; 40 rows in 2013
starting 2013-04-02) — not an acquisition gap. Disagg-side audit too: fut_disagg_txt zips
contain 22 matched families, all built (the 14 financial families come from fut_fin_txt
zips), nothing unbuilt.

CORRECTION to R1 FINDINGS: R1 said "engine agents should treat tff_*/cit_* per-family
availability as identical to the disagg family list." That is FALSE — CIT covers only 13 of
the 35 disagg families (no cit_ for financials, metals, energy, wheat_hrspring, rough_rice,
canola, oats, lumber, or vix). Fix: universe_manifest.csv now carries measured per-family
CIT columns (cit_file, cit_start, cit_end, cit_rows) joined from manifest_cit.csv,
test-locked (test_cit_matches_manifest_cit_manifest). Engines read real CIT availability
per family instead of inheriting the R1 error.

## (b) eurodollar_3m split universe: locked at the DISK level

The prior session's in-memory build_universe flag was test-locked; this round added
disk-artifact tests (test_round2_manifest.py): the CSV row must read
lint=PASS_WITH_EXN(split universe: positioning ends 2023-06-13 (ED sunset), SOFR proxy
bridge from 2018-04-03; usable window [2018-04-03, 2023-06-13]), tradeable_from=2018-04-03,
joint_end=2023-06-13; and eurodollar_3m must be the ONLY family with joint_end < 2026.
Engine contract verified on disk: lint=='PASS' filters to exactly 32 continuous markets;
PASS_WITH_EXN is deliberate opt-in; canola/sofr_3m stay FAIL with reasons.
35 rows = 32 PASS + 1 EXN + 2 FAIL.

## (c) align_daily.py — the shared PIT-audited join helper (TDD, RED->GREEN, 16 tests)

New: more_cot/align_daily.py + test_align_daily.py. RED first (ModuleNotFoundError). API:
- load_proxy(path): one loader for all 3 header conventions on disk (date,close |
  date,value | observation_date,<SERIES_ID>); sorted/dedup/NaN-free; raises on
  missing/broken/nonpositive (fail-closed).
- asof_prices(px, dates): last session AT-OR-BEFORE each query (no lookahead); before
  proxy start -> NaN (never fabricated); monthly FRED proxies snap to prior month-end.
- release_shift(dates): report Tue -> release Fri (+3d), mirroring lib_hunt.
- signal_to_daily(sig, prices, release_lag): first session STRICTLY after release when
  lag=1 (c3 headline), at-or-after when lag=0; later release wins a collision; ffill;
  zero (not NaN) before first release; accepts a Series or a bare DatetimeIndex calendar.
- cot_to_daily_positions(cot, px, release_lag=1, joint_end=None, stale_after_days=7,
  signal_col=...): full pipeline; signal_col selects net_noncomm_pct_oi | cit_pct_oi |
  pct_of_oi so CIT/TFF positioning aligns under the SAME conventions.
- alignment_report(...): measured diagnostics (proxy freq/staleness, release->session
  snapping, releases-beyond-proxy-end, release-to-entry lag distribution, days-in-market).

EQUIVALENCE PROOF (what makes it trustable): on the real us_10y_note + IEF pair,
cot_to_daily_positions(..., stale_after_days=None) is BIT-FOR-BIT IDENTICAL to
HUNT_COT2/lib_hunt.signal_to_daily over all 6,065 sessions
(pd.testing.assert_series_equal passed; ref rows 6065 == ours rows 6065, identical: True).
Hunt agents can switch to the shared helper without changing any published backtest.

stale_after_days=7 (NEW, default-on): positions older than one release cycle past the LAST
report are dropped. Found while testing ED: plain ffill carries 2023-06 ED positioning out
to the 2026 SOFR proxy end (2,103 daily rows of phantom positions) — the exact "split
universe masquerading as continuous" hazard charter 2(b) targets. With the default, ED
positions end 2023-06-23 (last report Tue 2023-06-13 -> release Fri 2023-06-16 -> live one
release cycle); joint_end clips to 2023-06-13 on request. Pass stale_after_days=None for
exact legacy HUNT_COT2 semantics on continuous universes.

Real-tree validation (alignment_report over all 33 linted families):
- 27 daily-proxy markets: freq=1d, median release->entry 3.0d, max 5d — healthy.
- 3 monthly-FRED markets (cocoa, coffee_c, cotton_no2): freq=31d, stale_proxy=True,
  median release->entry 16.0d, MAX 31d, 9 releases beyond proxy end. Engines on these
  markets trade up to a month-stale price — now MEASURED and flagged instead of unknown.
- ETF-proxied markets whose COT starts before the ETF listing (corn COT 2010-01 vs CORN
  ETF 2010-06; soy complex/sugar/wheat vs 2011-09 listings; copper vs CPER 2011-11):
  max release->entry 152-676d, all collapsing onto the ETF's first session. This is the
  proxy-start gap the manifest's tradeable_from already encodes — now per-family measurable.
- eurodollar_3m: median 455.5d, max 2811d — the split universe quantified (pre-2018
  releases collapse onto SOFR's first session 2018-04-03).

## (d) Lint re-run + suite

- python3 lint_cot_universe.py: 35 families -> universe_manifest.csv; PASS/PASS_WITH_EXN 33,
  FAIL 2 (canola span 421w < 522w; sofr_3m span 422w + gap 14d — unchanged, honest); exit
  code 1 BY DESIGN. Engine contract re-verified: filtering lint=='PASS' from the DISK CSV
  yields exactly the 32 continuous markets — the R1 note stands (read the CSV, not the exit).
- pytest more_cot/: 71 passed (48 prior + 16 align_daily + 7 round-2 manifest), 0 failures.
- universe_manifest.csv now 23 columns (was 19): + cit_file, cit_start, cit_end, cit_rows.

## Downloads this round

NONE. CIT coverage was already complete in the raw archive; every proxy was on disk.
(Charter sanctioned downloads only for missing listed markets; there were none.)

## Honest limits

- asof/staleness gates are ADVISORY: the helper measures and flags, but nothing forces an
  engine to gate on stale_proxy; a hunt agent can still ignore alignment_report output.
- TFF (52 series) and CIT (13) are linted only by their builder manifests (gap<=21d,
  jump<0.5), not by the 10y-span universe gate. The universe manifest's new cit_* columns
  cover CIT; TFF category availability is still read from manifest_tff.csv.
- The 9 releases beyond proxy end on monthly-FRED markets: those weeks' signals never get
  a price (proxy ends 2026-07-01); alignment_report counts them instead of hiding them.

ROUND 2 DONE

---

# DATA_COTMORE — ROUND 3 (2026-09-07)

Charter: (a) attempt free CBOE daily put/call ratio, STOP on block with logged HTTP;
(b) if fetched: lint/manifest/alignment vs COT price proxies, champion-OVERLAY covariates
ONLY (no signal hunting); (c) curate R2 rows in DEAD_IDEAS. Gates contract + DEAD_IDEAS
(now 106 rows at round start, charter said 90) read FIRST — no listed-dead family re-tested.
The COT fade/cross-section/crowding-overlay rows (HUNT_COT_ITER11, HUNT_COT2, HUNT_COT2-R2)
were treated as closed: this round adds a NEW data family (options PCR), not a COT re-tune.

## (a) Acquisition: current-day PCR = BLOCKED (charter STOP honored); archive = LIVE but FROZEN

A prior session of this agent had already fetched 10 CBOE archive CSVs (08:50) and left
build_pcr.py + test_pcr_lint.py at 15 pass / 3 FAIL; probes existed in more_vol/. This
round verified everything live instead of trusting prose, and CORRECTED the prior claim:

- Modern put/call API routes BLOCKED, exact responses (probe_pcr_live.py, reproducible):
  cdn.cboe.com/api/global/delayed_quotes/put_call_ratios/_all.json -> HTTP 403
  `<?xml ...><Code>AccessDenied</Code><Message>Access Denied</Message><RequestId>...`
  .../delayed_quotes/scratch/pcr.json -> HTTP 403 AccessDenied.
  Control on the same CDN: .../us_indices/daily_prices/VIX_History.csv -> HTTP 200 CSV
  (network path open; block is endpoint-level, matching the earlier probe JSON that also
  logged 403 for PCR_DAILY_History/PCR_History/PCRC_History/PCRE_History and 404-HTML for
  www.cboe.com/us/options/market_statistics/daily/csv/daily_market_statistics.csv).
- KEY CORRECTION to the prior session's conclusion ("CBOE retired these archive CSVs"):
  the historical_data page (HTTP 200, 626,776B) links 10 archive CSVs at
  cdn.cboe.com/resources/options/volume_and_call_put_ratios/*.csv. All 10 re-probed live
  this session: HTTP 200 and sha256-BYTE-IDENTICAL to the on-disk _raw/ copies (10/10,
  probe_pcr_live.py step 6 asserts this). They are LIVE but FROZEN upstream at 2019-10-04
  (CBOE stopped updating them; the 2020+ record lives only in the 403'd API).
- Verdict: charter (a) STOP holds for current-day data (no scraping, no synthetic
  substitutes). The frozen official archive is charter-(b)-eligible as a stale covariate
  family and is delivered as such.

## (b) Deliverables: pcr_manifest.csv + PIT covariates + alignment report (no signal hunt)

Three format epochs stitched, newer epoch wins, agreement MEASURED per boundary:
  A 1995-09-27..2003-12-31 pcratioarchive.csv (ratio-only) | B 2003-10-17.. *pcarchive.csv
  (padded volumes) | C 2006-11-01..2019-10-04 *pc.csv (unpadded volumes).
Printed 'P/C Ratio' columns are 2dp-rounded, so wherever volumes exist the ratio is
RECOMPUTED as put/call (identity verified: real spxpc 7/6/2010 printed 1.91 vs
446308/233843 = 1.9086; med |printed-recomputed| ~2.6e-3 on totalpc).

Six series (pcr_manifest.csv; lint gates: gap>9d FAIL, range [0.1,6.0] drop+count,
dupes raise):
  pcr_total  PASS          6044d 1995-09-27..2019-10-04 max_gap 7d, A->B n=51 med|d|=0.0025,
                           B->C n=1410 med|d|=0.007 max 0.2103 (prelim-vs-cleared volume)
  pcr_index  PASS_WITH_EXN 4019d, B->C med|d|=0.1666 max 1.3678 = METHODOLOGY BREAK
                           (manifest note names the break; do not use across it)
  pcr_equity PASS          4018d, B->C med|d|=0.0064
  pcr_spx    PASS          2330d 2010-07-06..2019-10-04 (single epoch)
  pcr_etp    PASS          3253d 2006-11-01..2019-10-04
  pcr_vix    PASS          3337d, 90 junk rows (0.0 / 21.04) DROPPED AND COUNTED
All stale=True with the corrected stale_reason.

TDD this round (RED -> GREEN, suite 15p/3F -> 21/21; combined more_cot+cboe_pcr 92/92):
1. test_parse_spx_epoch_ratio_first: the FIXTURE was self-inconsistent (put=100 call=110
   but printed 1.10; recompute correctly gives 0.909). Fixed the fixture, kept the code.
2. test_covariates_pit_strictly_prior_session (RED, cov NaN on Mondays, coverage 34.4%):
   real bug — side='right' asof + strict-filter NaNs every same-day session. Fixed
   structurally: searchsorted(side='left')-1 IS the strictly-prior lookup.
3. test_alignment_table (ValueError: DataFrame truthiness in `REAL.get(name) or ...`).
   Also the test's own invariant was backwards: strictly-prior coverage >= same-day, not <=.
4. test_real_stitch_boundary_labels_are_epoch_adjacent (RED): stitch labeled boundary 2
   'A->C' (impossible — A ends 2003-12, C starts 2006-11); now A->B then B->C, test-locked.
5. test_covariates_nan_after_series_freeze_no_phantom_ffill (RED, THE BIG ONE): my first
   fix ffilled the last 2019-10-04 value (1.05274) across 1,720 sessions to 2026-08-12 —
   exactly the R2 ED phantom-position hazard. Mask now: obs must fall at-or-after the
   PREVIOUS proxy session (max ONE session stale carry: Fri obs -> Mon session). After the
   fix: coverage on the SPY calendar 65.6% (was the fake 100.0%), last live covariate
   session 2019-10-07, 2019-10-08..2026-08-12 all NaN. test_covariates_no_same_day_leak_
   structural verifies strictly-prior over ALL >2000 valued sessions.
6. test_covariates_pit_strictly_prior_session still passes: Mon 2019-09-09 carries Fri
   2019-09-06 exactly.

Files (engine agents read these, not this prose):
  cboe_pcr/pcr_manifest.csv (6 rows, lint + stitch evidence + stale_reason)
  cboe_pcr/pcr_covariates_SPY_daily.csv (5000x6, PIT, NaN outside [2006-09-27, 2019-10-07])
  cboe_pcr/pcr_alignment_report.csv (6 series x SPY/QQQ/DIA/GLD: spans, overlap_days,
    cov_lag0 vs cov_lag1 — identical 65.6% because CBOE publishes daily on sessions)
  cboe_pcr/probe_pcr_live.py (charter-(a) evidence, exit-clean, asserts 10/10 sha256)
Charter (b) cap honored: covariates only, zero signal/overlay backtests run on PCR.

## (c) DEAD_IDEAS curation

- Verified all 9 COT-family repro paths named by the R3 correction rows exist on disk:
  loop_team/HUNT_TFF/{run_tff,tff_eng}.py + screen_tff.csv; loop_team/HUNT_CIT_AG/
  {cit_ag,run_hunt}.py + screen_results.csv; scripts/{cot_positioning_hunt,
  cot_delta_momentum,cot_delta_weekly}.py — 9/9 OK, evidence complete, no edits needed.
- Appended 2 rows (now 108): PCR current-day acquisition = blocked (exact 403/404
  evidence + probe path, so no future agent re-attempts); PCR archive family =
  data-acquired (frozen-2019 covariate deliverable + lint summary + the charter-(b)
  covariate-only cap).

## Honest limits

- The PCR archive ends 2019-10-04: any champion-OVERLAY covariate work is confined to
  2006-2019 and CANNOT be validated out-of-sample on 2020+. The alignment report's
  stale=True column says this at the data layer.
- pcr_index must not be used across 2006-11 (methodology break, med |dPCR| 0.167) —
  PASS_WITH_EXN, not PASS.
- VIX PCR had 90 junk rows (0.0 / 21.04) — dropped and counted in the manifest, not
  silently kept.
- The one-session-carry cap is a DESIGN DECISION (daily publisher): a Monday holiday
  weekend is fine (Fri obs -> Tue session fails the mask -> NaN). Engines needing longer
  staleness tolerance must opt in explicitly, not inherit it.
- Coverage 65.6% (not 100%): epochs B starts 2003-10 and SPY proxy starts 2006-09, but
  pcr_spx only 2010-07 (46.6%) and the pre-series head is NaN by design (no backfill
  into the void).

ROUND 3 DONE

---

# DATA_COTMORE — ROUND 4 (2026-09-08)

Charter: (a) CBOE TOTAL + equity-only PCR daily, fail-closed lint, cboe_pcr/ + manifest;
(b) materialize the trader-count breadth panel to work_r4/trader_count_panel.csv +
MANIFEST_R4.md, correct release lag, "lint or it did not happen". GATES_CONTRACT +
DEAD_IDEAS read FIRST: 119 idea rows (csv-parsed; 120 lines incl. header — the charter's
"108" was pre-R4 sessions), zero COT/TFF/CIT/PCR families re-tested, no dead family
touched. No engines run (charter cap); no signal/overlay backtest anywhere in this round.

## (b) trader_count_panel.csv — MATERIALIZED (was missing at round start)

State on arrival: a 01:54 session left build_trader_count_panel.py + tests, but NO panel
file and the suite at 14/22 (8 failed). Root causes, all fixed this session:
1. TEST fixture generated 3-digit-day dates ('2010-01-208') — the prior session's own
   fail-closed _parse_date (correctly) refused them. Replaced with a real weekly calendar
   (week_dates()) + a fixture-guard test that every date round-trips.
2. TEST fixtures violated the builder's CORRECT nesting identity (cat <= side total <=
   grand total) by overriding tt without scaling side totals/categories. Fixture now
   scales the whole nested structure with any tt override.
3. TEST called B.lint_all() — never existed (lint_panel). Fixed call.
4. REAL BUILDER BUG (test-caught, RED->GREEN): z.where(sd > 0, 0.0) zeroed the MIN_OBS=26
   warmup rows because NaN > 0 is False — phantom z=0 signal during warmup. Now
   z.mask(sd == 0, 0.0): warmup stays NaN, measured-constant windows get 0.0.
5. Test off-by-one: expanding().mean(min_periods=26) yields the first z at the 26th
   observation (index 25), not 27th; test slice corrected to the documented contract.
6. REAL LINT BUG: missing_pct counted NaN over the CSV's 23-column UNION, inflating
   suppression with the other format's structural blanks (44.7% canola). Now scoped to
   the family's own format columns: median 2.6%, worst lumber 19.8% (spread cols),
   rough_rice 17.7%, dow_emini 17.3%, vix 1.2%.

7. REAL-DATA CATCH (the important one): nat_gas_nymex z_Traders_Tot_All printed -10.74 on
   2022-02-08. NOT a market event — CFTC SPLIT THE REPORT: 'NATURAL GAS - NYMEX'
   (Tot_All 281, OI 1,162,813) ends 2022-02-01; 'HENRY HUB - NYMEX' (Tot_All 40, OI
   590,294) continues 2022-02-08+. The rename-stitch produced a -86% level step and the
   z spike is pure artifact. Added a BREAK gate (TDD, RED->GREEN): source-name transition
   moving Tot_All or OI by >=30% -> PASS_WITH_EXN with measured magnitudes (a measured
   break flags; a hard violation refuses). Real-tree result: nat_gas_nymex EXN (break at
   2022-02-08, 281->40, -86%) and lumber EXN (break at 2023-04-25, RANDOM LENGTH LUMBER
   ->LUMBER, 21->43, +105%; the 2023 rename is NOT value-continuous as R1 assumed).
   33/35 PASS, 2 PASS_WITH_EXN, 0 FAIL. Engines must not read z across those dates.

Deliverable (all in DATA_COTMORE/work_r4/):
- trader_count_panel.csv: 29,017 rows x 51 cols, 35 families, weekly
  (family, report_date, release_date, format, open_interest, 23 cnt_Traders_*,
  23 z_Traders_*).
- MANIFEST_R4.md: columns, gates, the 2 breaks, honest limits, cross-checks.
- build_trader_count_panel.py + test_trader_count_panel.py: 24/24 green.

Release lag: report -> release_date = next Friday STRICTLY after the report Tuesday
(mon-holiday reports +4d). Measured lags in the data: {3,4} calendar days, 0 same-day.
Charter's 'T+1 business day' is the release->trade leg: engines apply align_daily's
release_lag=1 (first session strictly after release) — panel release_date composes with
the R2 machinery unchanged. 193 rename-seam collisions resolved by matcher priority
(recorded, printed); 180,190 unmatched-market rows skipped and counted; '.' suppression
sentinel -> blank (core columns Tot_All/side totals: 0 suppressed cells in all 35
families). Independent raw-vs-panel field check (corn 2024-01-09, no builder code):
Tot_All 719=719, sides 522/550, MM 61/91, OI 1,410,115 — exact.

CORRECTION during the round (logged so it stays visible): my first MANIFEST_R4 draft
attributed the z tail to '2020-03 COVID OI collapse' — WRONG (min is the nat_gas
2022-02-08 break); and quoted median suppression ~10% — WRONG (2.6%). Manifest corrected
before handoff; next-most-extreme legit |z| ~2.5.

## (a) CBOE PCR — re-VERIFIED LIVE, not trusted from R3 prose

- probe_pcr_live.py re-run today (2026-09-08): modern endpoints still 403
  (delayed_quotes/put_call_ratios/_all.json AccessDenied); the 10 archive CSVs still
  HTTP 200 and sha256-BYTE-IDENTICAL to disk (10/10) — charter STOP holds for current-day;
  archive FROZEN at 2019-10-04 upstream.
- pcr_manifest.csv re-checked: pcr_total PASS n=6044 1995-09-27..2019-10-04 max_gap=7d
  range_dropped=0; pcr_equity PASS n=4018 2003-10-17..2019-10-04 max_gap=5d drops=0.
- INDEPENDENT recompute from _raw CSVs (my own parser + stitch, R3 gates): pcr_total
  n=6044 1995-09-27..2019-10-04 max_gap=7d out_of_range=0; pcr_equity n=4018 max_gap=5d
  out_of_range=0 — manifest confirmed. My B->C med|d| 0.0100 vs manifest 0.0070 is the
  known 2dp-rounded-printed vs volume-recomputed difference, already documented in R3.
- Suites: test_pcr_lint.py 21/21; combined more_cot+cboe_pcr 92/92 (no regressions).

## DEAD_IDEAS

No rows appended: R4 produced two LIVE data deliverables, no dead family, no failed
signal. Charter R4 sanctions reading the ledger (done: 119 rows), not curating it;
honest-negative row logging stays with engine hunts via the coordinator.

## Honest limits

- trader-count panel z is LEVEL-breadth (participant counts), NOT positioning direction.
- nat_gas/lumber z's are segment-local only across their EXN break dates.
- Counts can be REVISED by CFTC re-reports (newer-as_of-wins): PIT at the release-date
  level, not the revision level.
- PCR covariates remain frozen 2019-10-04 (65.6% SPY-calendar coverage; any overlay work
  is 2006-2019 only and cannot be validated 2020+).
- 35th family count: panel carries canola/sofr_3m (span-gated in R1 universe) — data
  present, z warmup 26 obs; engines filtering to the 32-33 continuous set should keep
  that filter when joining.

ROUND 4 DONE

## ROUND 5 (2026-09-08, coordinator standup 04:0x CST) — data refresh, no signal hunting

READ FIRST done: coord/GATES_CONTRACT_V2.md (RATIFIED 09-08 03:1x; v1 gates 1-5 unchanged;
my round carries NO submission, so no gates.run battery owed - data deliverables only) +
DEAD_IDEAS.csv RECOUNTED MYSELF: **130 data rows** (charter's "120 at R4-end" is already
stale; includes new HUNT_VOL2-R5 rows). My R3 PCR rows re-read: current-day acquisition
row stays 'blocked' (403), archive row stays 'data-acquired' - and HUNT_VOL2-R5 has now
consumed the archive as a covariate family and logged it DEAD as an overlay (0/148
dAnn>0). No dead-family re-test performed; my corner is pre-registered in the charter
(panel refresh + PCR freeze re-check), both data-only.

Champion of record untouched: GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv (I made no
changes in bt/, campaign/*.md, or any other agent's dir; my writes: DATA_COTMORE/work_r5/
only, plus the 2 fetched CFTC zips in tools/quant/data/more_cot/_raw/ with .sep3.bak
backups of the Sep-3 vintage preserved next to them).

### Inherited state (found on round start, verified not trusted)

A prior interrupted session this morning (07:42-07:49) had already fetched fresh 2026 CFTC
zips and rebuilt work_r5/trader_count_panel.csv, leaving NO manifest/tests/notes. I
verified: builder+tests in work_r5 are byte-identical to R4 (sha256 7ee710b90d21befa /
9a6f99cba4647c66 - zero code drift); fetched zips extend report dates 2026-08-25 ->
2026-09-01 (disagg 9,217 -> 9,502 rows; fin 2,959 -> 3,050); backups kept. Everything
below re-ran under my session.

### (a) trader_count_panel refresh - PASS

- Rebuilt from 32 _raw zips (2 refreshed): **29,051 rows x 51 cols x 35 families**,
  span 2010-01-05..2026-09-01 (R4: 29,017 rows ..2026-08-25).
- Delta decomposition: +34 rows = exactly one report week (2026-09-01) on 34 families;
  eurodollar_3m +0 (contract sunset 2023-06, correct). Overlap check on all 29,017 shared
  (family, report_date) rows across all 23 cnt_ columns: **0 changed cells** = no CFTC
  revisions between Sep-3 and Sep-8 vintages; pure append. 0 dropped pairs.
- Tests: work_r5 test_trader_count_panel.py **24/24 pass** (15.56s).
- BREAK gate re-run: 35 families -> **33 PASS / 2 PASS_WITH_EXN / 0 FAIL**; both EXN rows
  BYTE-STABLE at the charter-named anchors: nat_gas 2022-02-08 281->40 (-86%), lumber
  2023-04-25 21->43 (+105%). No new >=30% name-transition break anywhere (incl. new week).
- Release-lag spot check: new week report 2026-09-01 (Tue) -> release_date 2026-09-04
  (Fri) for all 34 families; corn z trail 1.119 -> 1.652 -> 1.868 continuous.
- Lint: max_gap <= 8d everywhere except sofr_3m 14d (known 2018 launch-year gap) - same
  as R4; core-column suppression 0 cells in all 35 families; family-level suppression
  0.0%..19.8% (lumber worst, unchanged).
- Family-extension sweep on the fresh fetch: 32 genuinely-first-in-2026 unmatched CFTC
  names, ALL ineligible (Coinbase crypto perps n<=35w; ICE carbon/REC/basis; Nodal
  ISO/PJM; FMX SOFR-3M n=2; CBOT Bloomberg HY/IG credit n=22/18 < 26-obs z warmup).
  **0 new families; panel stays 35.** Oats re-checked in fresh data: still dead (new
  105d + 91d reporting gaps in 2026 atop the 294d suspension; OI 3,132).
- Deliverables: work_r5/trader_count_panel.csv (sha256-16 9e2c82303acf4c24),
  MANIFEST_R5.md (vintage pins per V2 SS10b: new zips 70e18ad5a7e61745 / 7b744b8c6b241008,
  .sep3.bak 3e816c649e39c016 / 0d3a015f09b47a05).

### (b) CBOE PCR refresh attempt past 2019-10-04 - FROZEN, honest STOP per charter

New probe work_r5/probe_pcr_refresh_r5.py (rerunnable, exit 0), run 2026-09-08 ~07:5x:
- control cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv -> **200
  text/csv** (network path open; probe not void).
- 6 NEW API variants (put_call_ratios/_all.json, put_call_ratios/history.json,
  put_call_ratios/SPX.json, pc_ratio/_all.json, market_stats/put_call_ratio.json,
  us_options/put_call_ratios/_all.json) -> **6/6 HTTP 403 application/xml
  <Error><Code>AccessDenied</Code>** (S3 RequestIds logged, e.g. 7PXRTJSWYYP24PHJ).
- www.cboe.com/us/options/market_statistics/historical_data/ -> 200 HTML still publishing
  EXACTLY the same 10 archive CSVs; byte-compare totalpc/equitypc/spxpc vs on-disk _raw ->
  200 + sha256 identical 3/3 (3,256/3,256/2,332 rows). Still FROZEN at 2019-10-04.
- STOP: no scraping workarounds, no synthetic substitutes (AAII/FINRA precedent). No
  manifest change needed - pcr_manifest.csv stale=True rows stand as-is; regression suite
  cboe_pcr/test_pcr_lint.py **21/21 pass**, more_cot lint suite **14/14 pass** post-refresh.

### Verdict

Both charter items PASS as data deliverables: panel refreshed +34 rows with gates stable
and zero revisions; PCR freeze re-confirmed with exact HTTP evidence (6 new 403s + 3/3
byte-identical). ZERO adoptable-alpha claims made (none sought); honest frontier
UNCHANGED (champion ann 37.1954 pct). DEAD_IDEAS: no rows appended by me - both my R5
deliverables are LIVE data artifacts (precedent: my R4, where the coordinator confirmed
data deliverables do not self-log as dead ideas), and the one related family (PCR
overlay) is already honestly logged dead by HUNT_VOL2-R5 with my archive as its evidence
base.

Honest limits: trader-count z = breadth not direction; nat_gas/lumber segment-local
across EXN dates; align on release_date (PIT), never report_date; PCR overlay work
remains 2006-2019-only (frozen, re-verified); eurodollar_3m rows end 2023-06-13.

ROUND 5 DONE

## ROUND 6 (2026-09-08 15:0x CST) - verification + curation round, charter-locked narrow

Charter R6: (a) re-verify the trader_count_panel BREAK gate still fires fail-closed on BOTH
known breaks (nat_gas_nymex 2022-02-08 CFTC split; lumber 2023-04-25 rename). (b) Curation;
no new panel columns without a pre-registered consumer. READ-FIRST done: GATES_CONTRACT_V2.md
(in force; my round makes no gates.run calls - data-only verification, so no sig=/leak_check
battery owed) + DEAD_IDEAS.csv recounted myself (below). No dead-family re-test; no signal
hunting; bt/ untouched.

### (a) BREAK gate re-verification - PASS on all four axes

Environment found on round start: _raw/ has 34 zips = 32 untouched (2010-2025 x disagg/fin,
mtime Sep-3) + the 2 R5-refreshed 2026 zips with .sep3.bak backups; panel CSV on disk sha16
9e2c82303acf4c24 == MANIFEST_R5 pin (no drift since R5). All 4 vintage pins re-hashed this
session and MATCH: fut_disagg_txt_2026.zip 70e18ad5a7e61745, fut_fin_txt_2026.zip
7b744b8c6b241008, .sep3.bak pair 3e816c649e39c016 / 0d3a015f09b47a05.

1. Unit suite: work_r5/test_trader_count_panel.py **24/24 pass** (18.85s), including both
   break-gate fixture tests (test_source_name_break_flagged_not_stitched_silently,
   test_pure_rename_with_continuous_values_stays_pass) and the 3 fail-closed integrity raises.
2. Real-tree lint (35 families from all 34 zips): **33 PASS / 2 PASS_WITH_EXN / 0 FAIL.**
   Both charter anchors fire at EXACT date + magnitude:
   - nat_gas_nymex: break at 2022-02-08 NATURAL GAS - NYMEX -> HENRY HUB - NYMEX,
     Traders_Tot_All 281->40 (-86%).
   - lumber: break at 2023-04-25 RANDOM LENGTH LUMBER - CME -> LUMBER - CME,
     Traders_Tot_All 21->43 (+105%).
   Both asserts (date-in-status, magnitude-in-status) hold programmatically, not by eye.
3. Byte-stability: fresh in-memory rebuild of the full panel is **byte-identical** to the
   committed trader_count_panel.csv (29,051 rows x 51 cols x 35 families,
   2010-01-05..2026-09-01, sha16 9e2c82303acf4c24). Gate output is deterministic.
4. Not-vacuous (fail-closed proof): (i) full-coverage scan - the boundary detector walks
   **18 real source-name transitions** across 35 families (53 distinct CFTC source names);
   exactly **2** cross the |30%| gate - the two known EXNs; nearest miss dow_emini
   2022-02-08 (DJIA rename, -8.8%), then wheat_hrspring 2024-11-26 (-5.8%): quiet renames
   correctly stay PASS. (ii) mutation test on REAL panel data - injected a synthetic
   corn rename at 2026-09-01 with Traders_Tot_All 883->12 (-99%): gate FIRED
   (PASS_WITH_EXN, 'break at 2026-09-01 ... -99%'), EXN count 2->3 with the 2 known rows
   unchanged. The gate detects breaks it has never seen; its silence on the other
   33 families is measured, not vacuous.

### (b) Curation - ledger verified, panel schema frozen, nothing mined

- DEAD_IDEAS.csv recounted with proper csv.DictReader (multi-line quoted fields):
  **145 data rows** at my read (charter's '137 at R5-end' already stale - concurrent R6
  appends landed mid-round per design, e.g. HUNT_CREDIT2-R6, CAMP_SHORT-R6, HUNT_SECTOR2-R6,
  HUNT_COT2-R6 rows 135-137). Integrity at my read: **0 malformed rows, 0 byte-dup
  (idea,source) pairs**, ledger sha16 at read 97bd6b603a1aa09c.
- My rows verified intact and accurate, no edits needed: row 107 [blocked] CBOE PCR
  current-day acquisition (403 evidence stands), row 108 [data-acquired] CBOE PCR archive
  1995-2019 (consumed by HUNT_VOL2-R5, logged dead as overlay - correctly not re-touched).
- HUNT_COT2-R6 curation rows 135-137 verified present and scoped to CMDT2/CREDIT2/positioning
  rows - not mine, not modified. No panel consumer added a column; no new column added
  (no pre-registered consumer exists for one); panel stays 51 cols / 35 families.
- No signal hunting; the panel is not mined (HUNT_COT2 R5 9/9-FAIL stands).

### Verdict

Both charter items PASS. ZERO adoptable-alpha claims (none sought); honest frontier
UNCHANGED (champion ann 37.1954 pct / SR 3.1810 / sha 4358dfab95679b97 - untouched, I
wrote only inside DATA_COTMORE/ this round). No DEAD_IDEAS rows appended by me: both my
deliverables (panel, PCR archive) are LIVE data artifacts per the R4/R5 coordinator
precedent, and this round changed no data state to log.

Honest limits (unchanged from R5): trader-count z = breadth not direction; nat_gas/lumber
counts are segment-local across their EXN dates (use z within-segment only, or exclude
the seam week); align on release_date (PIT), never report_date; eurodollar_3m rows end
2023-06-13; PCR overlay evidence remains 2006-2019-only (frozen, re-verified R5 with
exact HTTP 403 evidence).

ROUND 6 DONE

## ROUND 7 (2026-09-08 23:1x CST) - panel + ledger integrity after the heavy concurrent-append week; curation only

Charter R7: (a) recount rows/cols (expect 51 cols / 35 families; data rows dynamic ~145-146),
0 malformed, 0 byte-dup (idea,source) pairs, EXN break gates fail-closed on both dates,
eurodollar_3m end 2023-06-13 unchanged. (b) curation only - no panel mining, no new columns.
READ-FIRST done: GATES_CONTRACT_V2.md (Step-2 leak flip already executed per its insert-only
banner; my round makes ZERO gates.run calls - data-only verification, no sig=/leak_check battery
owed) + DEAD_IDEAS.csv recounted myself (152 data rows at my read, below). No dead-family
re-test; no signal hunting; bt/ untouched; wrote only inside DATA_COTMORE/ this round.

### Environment note at round start (cost one detour, resolved)

work_r5/trader_count_panel.csv had mtime 22:48 today (6 min before this session, 22:54).
Content check: sha16 9e2c82303acf4c24 == MANIFEST_R5 pin -> NOT modified; mtime-only touch.
Separately, work_r5/_raw/ does NOT exist - MANIFEST_R5's vintage-pin table uses `_raw/` as
shorthand for the builder RAW constant (build_trader_count_panel.py:34 =
tools/quant/data/more_cot/_raw); work_r5/_raw_live/ holds the 2 fetched 2026 zips,
byte-identical to canonical. Clarification note appended to MANIFEST_R5.md (my file).

### (a) Panel integrity - ALL PASS

- Recount: **29,051 data rows x 51 cols x 35 families** (expect 51/35: EXACT); span
  2010-01-05..2026-09-01; 0 malformed-width rows; 0 dup (family,report_date) keys;
  trailing newline intact. sha16 9e2c82303acf4c24 (unchanged since R5/R6).
- Determinism: fresh in-memory rebuild from the 34 canonical raw zips is **BYTE-IDENTICAL**
  to the committed CSV (both sha16 9e2c82303acf4c24; run via builder copy in /tmp so the
  committed artifact was not rewritten).
- Vintage pins re-hashed at the canonical path, 4/4 MATCH: fut_disagg_txt_2026.zip
  70e18ad5a7e61745, fut_fin_txt_2026.zip 7b744b8c6b241008, sep3.bak pair 3e816c649e39c016 /
  0d3a015f09b47a05. Canonical _raw = 34 zips + 2 baks, matching the R6 record.
- EXN break gates **fail-closed on BOTH dates, asserted programmatically** (not by eye):
  lint 35 families = 33 PASS / 2 PASS_WITH_EXN / 0 FAIL; nat_gas_nymex status contains
  2022-02-08 AND -86% (HENRY HUB rename, Traders_Tot_All 281->40); lumber contains
  2023-04-25 AND +105% (LUMBER rename, 21->43). Assert set(exn)=={nat_gas_nymex,lumber} held.
- eurodollar_3m: last report_date **2023-06-13** unchanged (n=674, release 2023-06-16).
- Unit suites: work_r5/test_trader_count_panel.py **24/24 pass** (18.6s);
  more_cot/test_lint_cot_universe.py **14/14 pass** (2.1s); cboe_pcr/test_pcr_lint.py
  **21/21 pass** (1.4s). 59/59 green, no regressions in any of my three deliverables.

### (b) Ledger curation + charter conditional - PASS

- DEAD_IDEAS.csv recounted with csv.DictReader (multi-line quoted fields):
  **152 data rows** (R6-end count 145; delta +7 = 6 R7-tagged rows [HUNT_CRYPTO2-R7 blocked,
  HUNT_FXCARRY2-R7 dead, HUNT_SECTOR2-R7 dead, HUNT_TREASFUT-R7 dead, CAMP_SHORT-R7 verified,
  CAMP_BORROW-R7 verified] + 1 concurrent non-R7 append). Ledger sha16 at read
  d6873418ffa0da5e; trailing newline intact after the last concurrent row (xxd-verified).
- Integrity at my read: **0 malformed rows, 0 byte-dup (idea,source) pairs** (exact-match
  Counter over both fields). One idea text appears twice (sector-rotation covariates,
  csv rows 120/146) but with DIFFERENT sources (HUNT_SECTOR2-R5 vs -R6; R6 is the bugfix
  re-run superseding R5) -> not a dup pair; logged for the record, no action.
- My rows verified intact: 108 [blocked] CBOE PCR current-day acquisition, 109
  [data-acquired] CBOE PCR archive 1995-2019 (consumed by HUNT_VOL2-R5 row 119, dead) -
  no edits needed. Status census at read: 128 dead / 7 blocked / 4 data-acquired /
  3 R2 dead / 2 R3 dead / 1 dead/NOT-ADOPTED / 1 dead (adoption REJECTED on 8c) / 6 verified.
- Charter conditional: HUNT_SECTOR2's FINRA corner is row 150 status=dead (0/6 keyless
  routes, WAF 307 evidence) - NO data landed, so **no [data-acquired] row owed**; none written.
- No panel mining (HUNT_COT2 R5 9/9-FAIL stands); no new panel column (no pre-registered
  consumer); panel schema frozen at 51 cols / 35 families. No DEAD_IDEAS rows appended by me
  (R4/R5 coordinator precedent: live data artifacts do not self-log; this round changed no
  data state to log).

### Verdict

Both charter items PASS. ZERO adoptable-alpha claims (none sought); honest frontier UNCHANGED
(champion ann 37.1954 pct / SR 3.1810 / MDD -6.6922 / sha 4358dfab95679b97 - untouched, not
re-verified by me this round, coordinator-pinned 18:3x). Honest limits carried unchanged:
trader-count z = breadth not direction; nat_gas/lumber z's segment-local across EXN dates
(use within-segment or drop the seam week); align on release_date (PIT), never report_date;
PCR evidence frozen 2019-10-04 (re-verified R5, exact 403s); eurodollar_3m rows end 2023-06-13.

ROUND 7 DONE

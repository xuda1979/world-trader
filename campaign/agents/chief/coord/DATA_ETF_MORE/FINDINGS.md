

# ROUND 2 (2026-09-07, session closed 2026-09-07 04:30)

Universe: tools/quant/data/more_etf/ — 70 series on disk, manifest.csv rebuilt and
cross-checked by an independent re-lint this session. **50 PASS / 20 FAIL** (gates:
start<=2007-01-01, n>=250, maxgap<=10d, |ret|>50% on <=3d, dups==0, end>=2026-06).
Round-2 delta is DEPTH, not count: R1's 5000-row outputsize cap truncated every
PASS series at ~2006-10; 49 series now extend to true inceptions 1996-2006
(+31,001 rows total), all fail-closed re-linted.

## (a) Must-fetch — ALL RESOLVED
- EWJ EWG EWU EWQ EWL EWS EWI EWP EWH EWM: on disk, extended to 1996-03-18
  (7665-7668 rows each, maxgap 7d, 0 jumps, 0 dups). EWM/EWW also extended dir-wide.
- IYR 2000-06-19 (6593), VNQ 2004-09-29 (5517), SHY 2002-07-30 (6063),
  TIP 2003-12-05 (5721), AGG 2003-09-29 (5771).
- UUP: FAIL(start=2007-03-01) — 56 days past bound, vendor inception. Not written.
- BND: FAIL(start=2007-04-10) — vendor inception; AGG (2003) covers the same beta.
- HYG: FAIL(start=2007-04-11), documented honestly per charter; 2007-04 start is
  3.5 months past bound. JNK same story (2007-12-04). Not written.

## (b) R1 start-bound fails — 10/10 remain FAIL, honestly
Two-window stitch (1995-01-01..2012-12-31 + 2013-01-01..now, freshness gate
end>=2026-06) re-probed EWC EIS TUR DBP USCI COPX ENOR EPHE + BND/HYG/DBE.
Vendor genuinely has no pre-2008 depth: EWC 2008-01-02, DBP 2008-01-02,
EIS/TUR 2008-03-28, USCI 2010-08-10, COPX 2010-04-20, ENOR 2012-01-24,
EPHE 2010-09-29, DBE 2007-01-05 (4 days late). 0 of 12 flipped to PASS.
Failure mode caught and documented: start_date=1995+outputsize=5000 alone returns
the EARLIEST 5000 rows and silently truncates the series END (~2015) -> would pass
start-lint while writing a dead series. Freshness gate added fail-closed.

## EWF: not a TwelveData symbol (404 is correct)
symbol_search?symbol=EWF returns 0 exact matches; name search "iShares MSCI France"
returns **EWQ/NYSE**. The R2-first-attempt 404 was not transient and the ARCX
fallback in retry_r2.py was dead code (HTTPError raised before the fallback branch).
France coverage already on disk: EWQ 1996-03-18, 7667 rows, PASS.

## Dir-wide depth recovery (b-spirit, EWT precedent): 70 considered, 32 EXTENDED
Extended head window 1995..2012-12-31 stitched prepend-only (head wins at seam),
re-linted + seam-noise gate (NO_WRITE if head/tail disagree >0.5% of price level;
all seams measured seam_rel=0.00000). Highlights: QQQ->1999-03-10 (+1915),
DIA->1998-01-20 (+2201), XLB/XLE/XLF/XLI->1998-12-22 (+1968 ea),
XLK/XLP/XLU/XLV/XLY->1998-12-22 (+1966 ea), SMH->2000-06-05 (+1601),
EWW->1996-03-18 (+2665), EWM->1996-03-18 (+2667), LQD/TLT/IEF/SHY->2002-07-30,
EFA->2001-08-27 (+1291), IGV->2001-07-17 (+1322), EWY->2000-05-12 (+1616),
EWZ->2000-07-14 (+1573), VWO->2005-03-10, GLD->2004-11-18.
3 NO_GAIN (already at vendor inception: DIA/EFA/EWT on recheck), 15 SKIP (done
earlier this round), 2 FETCH_FAIL XLC/XLRE (HTTP 400; both post-2007 inceptions,
would fail start-lint regardless — left as FAIL rows, not silent).

## Verification (independent of the scripts that wrote the data)
- Prepend-only check vs backup_pre_extend/ (70 files): 49 EXTENDED series verified —
  every backup row preserved bit-identical at overlap (atol 1e-4), added rows
  strictly earlier, 0 dup dates, all ascending, max seam calendar gap 1 day. BAD: NONE.
- TDD seam-noise test (work_r2/test_seam_noise.py): PASS (0.1000 exact).
- Spot-check: EWJ 2006-10-18 close 55.2 unchanged after stitching. PASS.
- manifest_r2.py rebuilt manifest.csv over all 70: 50 OK, 20 FAIL, charter-(c)
  n/maxgap/zero_ret columns populated (asserted non-empty). Matches independent lint.

## Coverage table (PASS universe, by role)
- SPDR sectors (9): XLB XLE XLF XLI XLK XLP XLU XLV XLY — all 1998-12-22, ~6966 rows
  (XLC 2018 / XLRE 2015 remain fail-closed: inception-limited)
- Intl single-country (17): 10x EW* at 1996-03-18 + EWT 2000 + EWY 2000 + EWZ 2000 +
  EWM + EWW + EWP/EWL/EWS/EWK/EWQ/EWG/EWU/EWI/EWH — all PASS
- Broad intl: EFA 2001-08-27; EEM stays FAIL (2008 vendor inception)
- Real estate: IYR 2000-06-19, VNQ 2004-09-29
- Rates/credit: TLT/IEF/LQD/SHY 2002-07-30, AGG 2003-09-29, TIP 2003-12-05
  (HYG/JNK/EMB/BND fail-closed on inception)
- Commodity: GLD 2004-11-18, SLV 2006-04-28, USO 2006-04-10 (DBC/GSG/DBA/UNG/
  CANE/CORN/SOYB/WEAT/CPER all inception-limited FAILs)
- Equity broad/other: QQQ 1999-03-10, DIA 1998-01-20, SMH 2000-06-05, IGV 2001-07-17,
  GDX 2006-05-22, GDXJ FAIL 2009, XHB/XME/XOP/KBE/KRE/ITB/FXI/VWO mid-2000s PASS

## Bottom line for dependents (HUNT_INTERNATIONAL2 etc.)
Usable now: 70-series dir, 50 lint-PASS with 1996-2006 depth on 49 of them; the
20 FAILs are vendor-inception facts, not fetch bugs — retrying is dead weight
unless the coordinator waives the 2007-01 bound (would add HYG/JNK/UNG/UUP ~2007
+ EWC/DBC/GSG/EEM 2008 as 2007+ hunts). Directory is honest: every FAIL row is
loud in manifest.csv, nothing fail-closed was written.

ROUND 2 DONE
# ROUND 3 (2026-09-07, session closed 09:5x CST)

Charter 3(a): re-test the 20 known start-bound FAILs under the coordinator
WAIVER (2007-01 bound lifted for inception-limited series; span_class =
pre2007 | 2007plus | inception_fail, disclosed per-file, hunts filter on it).
Read GATES_CONTRACT.md + DEAD_IDEAS.csv (95 rows incl. header) first: this
round is data-lint only — no signal family touched, nothing in DEAD_IDEAS
re-tested, no dead signal re-tuned.

## (a) Waiver re-test: 19/20 PASS_WAIVER, 1 recovered after clean re-stitch
results_retest_r3.json (saved, reproducible via retest_r3.py; 8req/min
throttle respected, TDD tests written FIRST in test_span_class.py — 7 green):
all 20 rows re-fetched fresh full-history. 19 PASS_WAIVER (2007plus), written,
re-linted: n=3722..4948, maxgap<=5d, jumps=0, dups=0, end=2026-09-04.
  HYG 2007-04-11 n=4883 | JNK 2007-12-04 n=4718 | EMB 2007-12-19 n=4707 |
  BND 2007-04-10 n=4884 | UUP 2007-03-01 n=4911 | EWC 2008-01-02 n=4699 |
  DBC 2008-01-02 n=4701 | GSG 2008-01-02 n=4699 | DBA 2007-01-05 n=4948 |
  UNG 2007-04-18 n=4878 | CANE 2011-09-19 n=3763 | CORN 2010-06-09 n=4086 |
  SOYB 2011-09-19 n=3763 | WEAT 2011-09-19 n=3763 | CPER 2011-11-15 n=3722 |
  DBP 2008-01-02 n=4699 | DBE 2007-01-05 n=4948 | BNO 2010-06-02 n=4091 |
  USCI 2010-08-10 n=4043.
0 pre2007 upgrades (waiver cannot create pre-2007 depth — a vendor inception
is a vendor inception). Charter's expected unlocks confirmed: HYG/JNK/EMB
~2007, DBC/GSG/EWC ~2008-01.
- EEM: first fetch FAIL(dup) — dup-polluted vendor frame (5000 raw rows over
  2012-10-12..2026-09-04, 1507 dup dates; 3493 unique), on-disk file left
  intact, flagged loud (KEPT-FAIL-ROW). Recovered by eem_refetch.py: R2
  two-window stitch (2007..2016 + 2017..now, head wins at seam) ->
  PASS_WAIVER 2008-01-02, n=4699, dups=0, gap=5d, jumps=0. Verified the
  keep-first dedup was safe: raw dup-close spread max 0.072% (same bar
  double-reported by vendor, not conflicting data); seam 2016-12-30 ->
  2017-01-03 is a clean 1-calendar-day handoff, density 4699/18.7y = 251/yr.

## Integrity defects found by independent re-lint (this session), TDD-fixed
An independent re-lint of all 20 files with freshly written logic (not
retest_r3.lint_series) confirmed every metric, then a dir-wide sweep found
two defects the round's scripts did not cause but the manifest disclosed
wrongly. Failing tests written first (test_r3_integrity.py), then fixed:
1. EWA silent truncation (pre-existing): on-disk file started 2012-10-12 with
   3493 rows (mtime Sep 4 — not written this round) — the exact R2-documented
   dup/truncation signature — while R2 had MEASURED attainable depth
   2008-01-02 (+1206 rows, seam_rel=0.00000, results_extend_all.json) and
   could not apply it under the then-unwaived start gate. Manifest row said
   PASS_WAIVER 2007plus starting 2012-10-12: span misdisclosed to hunts.
   Fixed via fix_r3_integrity.py (R2 stitch method + dup-spread gate:
   NO_WRITE if any dup date's close spread >0.5%; measured max 0.0537%):
   now 4700 rows 2008-01-02..2026-09-04, dups=0, gap=5d, jumps=0,
   PASS_WAIVER. First attempt NO_WRITEd itself loudly — my first seam gate
   was wrong (measured 2-week drift inside window 0, not a seam; the windows
   do not overlap) and the fail-closed gate refused the write until the gate
   was corrected. That is the discipline working.
2. Charter write-spec violation (pre-existing): BIL EWT GDXJ INDA XLC XLRE
   were 6-column OHLCV, charter spec is [date,close]. Normalized in place,
   row counts unchanged (4847/6587/4228/3666/2063/2741), close values
   asserted bit-identical post-write.

## Manifest (b): rebuilt, 77 series, span_class on every row, fail-closed
PASS (pre2007) 50 | PASS_WAIVER (2007plus) 25 | FAIL(inception) 2 — XLC
2018-06-19, XLRE 2015-10-08 stay loud FAILs (genuine post-2013 inceptions;
T3 verified a post-2013 start can never be written as huntable).
PASS_WAIVER = the 20 charter rows + 5 reclassified by the same rule from
on-disk first dates: BIL 2007-05-30, MOO 2007-09-05, GDXJ 2009-11-10,
INDA 2012-02-03 (all genuine vendor inceptions), EWA (defect #1, fixed).
Independent final check (own logic, not manifest_r3.build): all 77 manifest
rows match disk exactly — start, rows, span_class, dups=0, ascending,
positive, jumps=0, maxgap<=10. 0 problems.
Zero-run disclosure (not a gate change, loud): CPER max 8 consecutive
flat closes, CANE 6, BNO 5 (ETN stale prints; tracked in manifest
zero_ret_rows col; R1/R2 gates never failed a series on zero runs, so no
retro-invented gate and no silent pass — hunts can filter on it).

## Gates/tests (TDD)
- test_span_class.py 7/7 green: classify boundaries (2007-01-01 is pre2007,
  2013-01-02 inception_fail), waiver lifts ONLY start (gap/jump/short/stale/
  dup all still fail), inception_fail never written, writes ascending+unique,
  manifest span_class column non-empty AND matching disk for all 77.
- test_r3_integrity.py 3/3 green after fixes (red first: 3 fail on EWA +
  OHLCV files; I3 initially over-broad — flagged genuine 2000-cohort
  inceptions EWT/EWY/EWZ — corrected to per-fund R2-measured attainable
  starts, encoding EWT 2000-06-23 / EWY 2000-05-12 / EWZ 2000-07-14 as
  truths, EWA 2008-01-02 as the attainable fix point).
- 9/9 green total. Results reproducible: work_r3/{retest_r3.py,
  eem_refetch.py, fix_r3_integrity.py, manifest_r3.py} + saved JSON/logs.

## Bottom line for dependents (CREDIT2, CMDT2, FX/Intl hunts)
Usable now: 77-series dir, 75 lint-PASS (50 pre2007 + 25 2007plus with
span_class for depth filtering), 2 loud inception FAILs. New depth: credit
(HYG 2007-04, JNK 2007-12, EMB 2007-12, BND 2007-04), dollar (UUP 2007-03),
commodity (DBC/GSG/DBP/DBE 2007-08, grains CANE/CORN/SOYB/WEAT 2010-12,
CPER 2011, BNO 2010, USCI 2010), Australia (EWA 2008-01, truncation fixed).
Every PASS_WAIVER row discloses its true first date — hunts filter on span
per the waiver; nothing fail-closed was written; every FAIL is loud.

ROUND 3 DONE


# ROUND 4 (2026-09-08, session closed 00:3x CST)

Charter round 4: clear the 10 R1 lint-bound FAILs (HYG EWC EIS TUR DBE EPHE USCI
COPX DBP ENOR) or prove them unobtainable. Read GATES_CONTRACT.md +
DEAD_IDEAS.csv (119 data rows) first: data-lint round, zero signal families
touched, nothing in DEAD_IDEAS re-tested, champion untouched.

## Partition: 5 already cleared in R3, 5 genuinely unfetched
Verified from manifest.csv + disk before any fetch (test_r4.T7 guarded this):
HYG EWC DBE DBP USCI were already PASS_WAIVER on disk from R3. The round's
work was the remaining 5: EIS TUR EPHE COPX ENOR.

## Rotation: 5/5 PASS_WAIVER (results_r4.json, reproducible via r4_fetch.py)
Two keyless sources per symbol, in order: (1) TwelveData time_series full
history (8req/min throttle respected), (2) Nasdaq historical keyless
(browser UA, wt.sources.nasdaq_history endpoint family). TwelveData won on
depth every time; Nasdaq serves only ~10y (n=2514, 2016-09-06..2026-09-04,
rc=200 every time) so it served as a live cross-check, not the winner. No
stitching needed or applied. All written fail-closed ([date,close], 2-col):
  EIS   2008-03-28 n=4640  | TUR   2008-03-28 n=4641
  EPHE  2010-09-29 n=4008  | COPX  2010-04-20 n=4121
  ENOR  2012-01-24 n=3676
All end 2026-09-04, maxgap<=5, jumps=0, dups=0, span_class=2007plus
(genuine vendor inceptions, disclosed per-file per the waiver; not pre2007).

## Failing probes: none
Every probe (10/10: 5 TwelveData + 5 Nasdaq) returned rc=200 with a parseable
frame; there are no FAIL rows from this round and hence no failing-probe URLs
to disclose. Remaining directory FAILs are unchanged and unobtainable: XLC
(2018-06-19) and XLRE (2015-10-08) — genuine post-2013 vendor inceptions,
loud in manifest.csv since R3. The R1 charter-10 list is now fully resolved:
10/10 on disk as PASS/PASS_WAIVER, 0 silent drops.

## Manifest (charter: record every write)
r4_fetch.py wrote CSVs but did NOT update manifest.csv (78 lines = 77 rows) —
caught by TDD before any downstream consumer saw a stale manifest
(test_manifest_r4.py written RED first: m1 files-vs-rows, m2 rows-match-disk,
m3 independent re-lint; m1+m2 red, then manifest_r4.py rebuilt via the R3
builder+gates unchanged -> 82 rows, 2 loud FAILs, m1+m3 green; m2 green).
Independent disk-vs-manifest-vs-MANIFEST_R4.md cross-check of all 10 charter
rows: row counts identical in all three (e.g. HYG 4883, ENOR 3676).

## TDD discipline (13/13 green at close)
test_r4.py 8/8. The prior session left 3 RED (T1/T4/T7) — all three were
TEST defects, not production defects: T1 compared Timestamps to strings
(production returns Timestamps because lint needs a datetime index — string
dates would FAIL(read) everything); T4 fixtures tripped the wrong gates
(stale/short/dup preempting: fixtures ended >3y before ref_end, had <250
rows, or OVERLAPPED windows producing dups instead of the intended gap);
T7 asserted list==set (unsatisfiable in Python). Fixed by correcting fixture
gating and assertion forms — NO gate was weakened; the inception fixture was
strengthened (3000 rows ending 2026-07) so FAIL(inception) fires for the
documented reason, not stale-preempted. Also added: test_r4_t7_done.py 2/2
(completion invariant: all 10 charter names PASS_WAIVER + disk-matched;
the original T7 pre-round premise is retired in place with a comment).
Gate-order note now encoded in test comments: short -> dup -> gap -> jumps
-> stale -> inception.

## Bottom line for dependents
Usable now: 82-series dir, 80 lint-PASS (50 pre2007 + 30 2007plus), 2 loud
inception FAILs. New this round: Israel (EIS 2008-03), Turkey (TUR 2008-03),
Philippines (EPHE 2010-09), copper miners (COPX 2010-04), Nordic (ENOR
2012-01). Every write discloses its true first date via span_class; hunts
filter on span per the coordinator waiver. Nothing fail-closed was written;
every FAIL is loud; no synthetic fills anywhere.

ROUND 4 DONE


# ROUND 5 (2026-09-08, session closed ~06:3x CST)

Charter round 5 corner (a): extend the ETF overlay bench for the V2 section-8
blend battery - the pinned spy/ief/cta trio is the minimum; add 1-2 DECORRELATED
PASSIVE benches; PIT lint + byte-stable manifest; NO signal hunting. READ FIRST
done: GATES_CONTRACT_V2.md (RATIFIED 03:1x) full-read; DEAD_IDEAS.csv recounted
MYSELF = 130 data rows (charter's "120 at R4-end" -> dynamic per V2 preamble,
HUNT_VOL2-R5/SECTOR2-R5/CREDIT2-R5/FXCARRY2-R5/TREASFUT-R5 appended since). No
dead family re-tested (bench acquisition is data-lint work, R2-R4 class); no
signal hunted; bt/ untouched (quiet-tree rule respected); champion untouched.

## Trio pins verified byte-identical (V2 section-7c: NOT re-fetched)
SPY twelvedata/SPY.csv sha16 d35d72808dcc9fc3 | IEF more_etf/IEF.csv 603cb2a56afd5616
| CTA_15vol sleeve_library d7f3b5cd4616f0f4 - all three match the pre-round
measurement exactly (T1 canary, green at close; a re-fetch would force re-running
every open submission per 7c and none happened). Champion of record re-verified
end-of-round: sha 4358dfab95679b97 (charter pin), untouched.

## Deliverable: tools/quant/data/bench_r5/manifest.csv - 10 rows, byte-stable
Two independent process invocations produce byte-identical builds (build1 ==
build2 == committed, sha256 326afe5a28db2809...; T4 asserts committed == fresh
build). Rows: 3 trio_pinned (PIN), 2 decorrelated_passive (SELECTED), 4
eligible_not_selected, 1 candidate_rejected (loud reason per row).
- SELECTED (the round's addition, 2 benches):
  UUP  max|corr| vs trio 0.1833 (spy -0.1833/ief -0.1480/cta -0.0156),
       corr_to_champion 0.0028, 2007-03-01 n=4911 PASS_WAIVER span 19.5y
  GLD  max|corr| vs trio 0.2043 (spy 0.0628/ief 0.2043/cta 0.0553),
       corr_to_champion 0.0119, 2004-11-18 n=5483 PASS pre2007 span 21.8y
- eligible_not_selected (cap=2): SLV 0.2294, IAU 0.2056, GSG 0.3705, DBC 0.3789
  (IAU/SLV also gold-complex near-duplicates of GLD; PAIR_CORR_MAX 0.7 rule)
- candidate_rejected CONTROL (pre-registered, expected rejection): TIP
  corr_ief 0.7635 > 0.5 - rates beta, correctly NOT decorrelated. The control
  firing as predicted is evidence the gate has real content, not that data is bad.

## Pre-registered selection rule (encoded in tests BEFORE any measurement)
Candidates a-priori GLD SLV IAU DBC GSG UUP (+TIP control); equity beta, rates/
credit, stale-print commodity singles excluded on asset-class grounds a-priori
(no fishing). Eligible iff: R3 lint PASS/PASS_WAIVER + span>=8y (R4 TimesFM
span-gate generalization) + >=1008 common daily obs vs EVERY trio member +
max|corr| vs trio <= 0.5. Rank max_corr_trio asc / span desc; greedy take <=2,
skip |corr|>0.7 vs already-taken. Correlations on COMMON dates only - no fill,
no pad, no synthetic alignment. Every candidate row carries its measured numbers
even when rejected - nothing silently dropped.

## TDD (8/8 green at close; test_bench_r5.py)
RED first (ModuleNotFoundError), then two RED-first defect catches during build:
1. corr_common pct_change'd BOTH inputs - CTA is a [date,ret] curve; pct_change
   of a 0.0 return is NaN (0/0) -> 'corr unmeasurable on every trio member',
   zero benches selectable. This is the R3 beats_passive re-differencing bug
   class (SPY-returns-named-close, SR 0.000) reproduced in my own first draft.
   Fix: px_convention travels WITH the series (to_daily_ret(mode)); T5-style
   test asserts the trio's disclosed jump_days/zero_ret_rows/maxgap match the
   convention (RED 1161-vs-0 on IEF before fix).
2. My own consumption test passed vacuously first (price LEVELS into
   beats_passive -> the >1e3 curve heuristic scored level-SRs, finite garbage).
   Corrected to the production caller contract (HUNT_INTL2_round5.py:219-222:
   caller pct_changes prices, CTA passes through). After correction the loader
   reproduces the champion SR pin 3.1810 EXACTLY and the trio on the champion
   span reads spy_bh 0.5863 / sixty_forty 0.5916 / cta_trend -0.1097.

## Fail-closed discipline + consumption smoke (not a performance claim)
test_failclosed_rejects_bad_bench: fabricated 40-day-gap frame -> FAIL(short/gap
path), never selected, role=loud. T8 smoke: all 10 manifest inputs load clean
through one loader (ascending, unique, positive/finite); trio evaluates through
bt.beats_passive (complete trio, finite per-benchmark SRs); bt.blend.blend_nets
accepts a selected bench on the common index AND raises on misalignment
(asserted). NO gates.run candidate battery, NO blend dAnn/dMDD numbers, NO
sleeves produced - the blend battery itself is the consumers' job; this round
only widens what they can be judged against.

## Bottom line for dependents (overlay/blend submitters, V2 section-8)
Consume tools/quant/data/bench_r5/manifest.csv: the pinned trio (do NOT re-fetch;
T1 canary will fire) + UUP and GLD as decorrelated passive benches with measured
corr vs trio/champion printed per row and vintage sha256_16 pinned per row
(V2 9d/10b discipline). UUP is span_class 2007plus - filter on span per the R3
waiver exactly as with hunt data. Reproduce: python3
campaign/agents/chief/coord/DATA_ETF_MORE/work_r5/bench_r5.py (writes manifest,
byte-stable) + pytest work_r5/test_bench_r5.py (8/8). Full details:
MANIFEST_R5.md (same dir).

ROUND 5 DONE


# ROUND 6 (2026-09-08, session closed ~16:0x CST)

Consolidation round. READ FIRST done: GATES_CONTRACT_V2.md (in force; leak_step-2
banner noted - flip already executed, pass sig= and leak_check=True explicitly)
+ DEAD_IDEAS.csv recounted MYSELF = 145 data rows (charter said 137 at R5-end;
dynamic per V2 preamble - new rows landed mid-round incl. a row citing this
agent's R5 fetcher defect as fixed by SECTOR2-R6). No dead family re-tested; no
signal hunted; champion untouched (sha 4358dfab95679b97 re-verified end-of-round);
CAMP_COST's charter-named bt/ work (test_camp_cost_r6_hobr.py, mtime 15:28) left
alone - disjoint surface, verified zero beats_passive references in their file.

## (a) TDD BUGFIX: 0.0-return -> degenerate-benchmark edge (bt/beats_passive.py)

THE BUG (named file: campaign/bt/beats_passive.py, function best_passive_sr):
a benchmark book that NEVER VARIES on the span (identically-0.0 returns) has
zero variance; bt.metrics.sharpe_d() floors zero std to a FINITE SR 0.0, so the
measurability test (len>=MIN_OBS and coverage>=0.5) accepted a benchmark that
never traded as "measurable SR 0.0" - and on any span where SPY/60-40 are
negative (2008 crash), the flat line WINS best_passive_sr and an honest
candidate is rejected with reason='candidate_sr_le_passive' against a fiction.
This is the exact edge class the charter names (R5: pct_change of a 0.0 return
is NaN -> corr unmeasurable), one layer deeper: the same 0.0-return data also
manufactures a measurable-looking benchmark through the SR floor.
REAL DATA TRIGGER: library CTA_15vol (pinned sha d7f3b5cd4616f0f4) rows 0..200
are placeholder 0.0 (2008-01-03..2008-10-17). Measured on the pinned bytes,
production convention (caller pct_changes prices, CTA pass-through):
  2008-01-03..2008-06-30 n=124: HEAD scored cta_trend SR 0.000 'measurable' ->
    best=cta_trend 0.0 vs spy_bh -1.1460 / sixty_forty -1.3807 -> any candidate
    that beat both tradable benchmarks was rejected against the never-traded line.
  2008-01-03..2008-10-17 n=201: same failure (cta_trend 0.000 vs spy_bh -1.4784).
This blocks honest beats-passive verdicts on short-span candidates exactly as
the charter says.

TDD EVIDENCE (RED first, then smallest fix, then GREEN):
- RED: 4 new tests appended to campaign/bt/tests/test_beats_passive.py; 3 RED
  at HEAD failing on the documented reason (info dict printed
  {'sr': 0.0, 'n': 124} for the flat cta_trend). 4th test
  (test_zero_return_input_to_best_passive_fails_closed) is a GREEN boundary
  pin at HEAD (degenerate CANDIDATE already fails closed via SR 0.0 losing to
  spy_bh) - disclosed as such, NOT claimed as a RED-first catch.
- FIX (7 lines incl. comment, in best_passive_sr only): a benchmark book with
  s.std(ddof=1) < 1e-12 is UNMEASURABLE - info[name] = sr=NaN + note=
  'unmeasurable(zero-variance book: benchmark never traded on span)' - same
  fail-closed rule as <MIN_OBS. No threshold, fixture, or caller contract
  touched; evaluate()/gate() semantics flow from the same info dict unchanged.
- GREEN: test_beats_passive.py 46/46 (42 pre-existing + 4 new).
- FULL bt SUITE: baseline BEFORE any edit 422 passed / 0 failed (coordinator's
  11:4x 410/0 + CAMP_COST's r6_hobr tests landed 15:28); AFTER the fix 426
  passed / 0 failed. No pre-existing test weakened (incl. the R4
  test_degenerate_benchmark_never_masks_no_data fail-closed family and
  test_cta_proxy_uses_library_series_when_given, whose fixture has variance).
- VERDICT NEUTRALITY on real data, verified on the pinned bytes:
  1. Crash spans inside the flat window: cta_trend now reports
     sr=nan + unmeasurable(zero-variance book) and best falls to a TRADABLE
     benchmark (spy_bh -1.1460); the fiction comparison is gone.
  2. Post-window span 2008-10-20..2009-04-20 n=125: cta_trend MEASURES
     NORMALLY (SR 0.1033) - no over-rejection: real variation is still a
     valid benchmark.
  3. Champion-span regression pin UNCHANGED (R5 MANIFEST numbers reproduce
     exactly): spy_bh 0.5863 / sixty_forty 0.5916 / cta_trend -0.1097 /
     champion SR 3.1810. The fix cannot touch champion-track verdicts:
     verify_champion.py/reconcile.py/metrics.py/engine.py import nothing from
     beats_passive (grepped, zero hits).
- Blast radius: production callers all read best_passive_sr/best_passive_name
  from the info dict (HUNT_TIMESFM eval_r5.py:99, HUNT_INTL2 round5/round6,
  HUNT_CRYPTO2 carry_engine*, RES_BASIS emit_sleeve.py). All published
  TIMESFM R5 bp_best pins (0.2801/0.5336/0.5643/0.5839) are positive numbers
  from full spans (2007+/2013+ starts), none inside the CTA flat window ->
  no published verdict changes. HUNT_INTERNATIONAL2's R4
  pristine-snapshot copy intentionally NOT touched (it pins their R4
  provenance bytes).

## (b) Trio span refresh + disclosure (pins intact, NOT re-fetched)

V2 section-7c discipline: the trio was verified byte-identical, never
re-fetched (a re-fetch would force re-running every open submission).
  SPY       tools/quant/data/twelvedata/SPY.csv            sha16 d35d72808dcc9fc3
  IEF       tools/quant/data/more_etf/IEF.csv              sha16 603cb2a56afd5616
  CTA_15vol campaign/results/sleeve_library/CTA_15vol.csv   sha16 d7f3b5cd4616f0f4
Row-count disclosure, BOTH conventions stated (this was the confusion source):
  SPY:  5000 price rows 2006-09-26..2026-08-12 -> ret n 4999 (charter's R5 n)
  IEF:  6065 price rows 2002-07-30..2026-09-04 -> ret n 6064 (charter's R5 n)
  CTA:  4683 ret rows  2008-01-03..2026-08-12 -> ret n 4683 (pass-through)
Charter's R5 numbers are RETURN-series counts (the blend/bp consumption n);
the +1 on SPY/IEF is the pct_change head row, not new data. Zero byte drift:
fresh sha16s equal the R5 pins exactly. Also disclosed per-file in
bench_r5/manifest.csv trio rows (start/end/rows/sha256_16, restored - below).

## DATA_ORGANIZE sweep clobber + restore (both deliverables byte-exact)

The DATA_ORGANIZE canonicalization session (13:44 today; cron attribution in
job_af5fd127caab log line 1708) rewrote 71 manifest.csv files at ~14:40 to the
foreign 1-row schema family,file,date_col,kind,rows,cols,exception. Two of MY
directory's deliverables were flattened (both untracked, .gitignore line 5 -
not git-recoverable):
  1. tools/quant/data/bench_r5/manifest.csv: 10 rows sha 326afe5a28db2809...
     -> 47-byte 1-row header (sha16 13a9c9cfd9952995). RESTORED by re-running
     my own deterministic builder (work_r5/bench_r5.py build()) - fresh build
     sha256 326afe5a28db280917ef2751d303e3c6659c4408a2284145c0ab1a707db038f4,
     byte-identical to the R5-committed pin BEFORE any write; restored on disk,
     work_r5/test_bench_r5.py back to 8/8 GREEN (was 6/8 RED on the clobber).
  2. tools/quant/data/more_etf/manifest.csv: 82 rows x 10 cols with span_class
     -> foreign-schema 82x7, span_class column GONE (hunts filter on it per
     the R3 waiver). RESTORED via the R3 builder (work_r3/manifest_r3.py
     build() - re-lints every CSV fail-closed from disk, zero fabrication):
     82 rows, 10 cols, 2 loud FAILs back (XLC 2018-06-19, XLRE 2015-10-08),
     R4 spot-facts verified row-exact (HYG 4883 / ENOR 3676 / EIS 4640 /
     TUR 4641 / EPHE 4008 / COPX 4121, all PASS_WAIVER).
     NOTE: restored sha16 9b04a324ebb4db04; the pre-clobber bytes were not
     sha-pinned anywhere I can find, so byte-identity is claimed via the
     deterministic builder + row-exact spot-facts, not by hash. tools/quant/
     data/twelvedata/manifest.csv remains in the foreign schema (not my
     deliverable; flagged for DATA_ORGANIZE's post-mortem).
DATA_FREDMORE's verify_round6.py independently documented the same clobber
(their section A4) and CAMP_BORROW-R6 restored FRED's PIT vintages - cross-
agent corroboration on file. Escalation carried in their logs: DATA_ORGANIZE
needs an atomic-write + do-not-touch-pinned-artifacts fix before the next
sweep; my bench_r5/manifest.csv IS a pinned artifact (T4/T5 assert its bytes).

## Round-6 test totals (all green at close)

bt/test_beats_passive.py 46/46 (4 new, 3 RED-first verified) | full bt suite
426/426 (baseline 422/422 pre-edit) | work_r5 8/8 | R3+R4 data suites 22/22
(span_class 7, r3_integrity 2, r4 8, r4_t7_done 2, manifest_r4 3) |
work_r2/test_seam_noise.py script-run PASS exit 0 (never pytest-collected;
unchanged since R2). Champion of record untouched: sha 4358dfab95679b97
re-verified. Reproduce: python3 -m pytest campaign/bt/tests/test_beats_passive.py;
python3 -m pytest campaign/agents/chief/coord/DATA_ETF_MORE/ (76 passed incl. bt bp file).

ROUND 6 DONE


# ROUND 7 (2026-09-08, session closed ~22:5x CST)

Consolidation/repair round. READ FIRST done: GATES_CONTRACT_V2.md full-read (in
force; VOL2's V3 per-class placebo noted as PROPOSAL - not depended on either
way; nothing this round touches acceptance verdicts). DEAD_IDEAS.csv recounted
MYSELF = 151 data rows (charter said 145-146 at R6-end; dynamic per V2 preamble
- R7 rows landed mid-round incl. FXCARRY2-R7, ECB SDMX, FINRA CSI, AUDIT-R7
borrow refresh). No dead family re-tested; no signal hunted; no sleeves
produced. Champion of record untouched: sha 4358dfab95679b97 re-verified
end-of-round. bt/ untouched (quiet-tree rule; the 14 uncommitted bt/ files in
the working tree are concurrent agents' live work, zero bytes mine).

## (a) CENTERPIECE - DATA_ORGANIZE post-mortem fixes, TDD RED-first

Post-mortem source identified: coord/CAMP_BORROW/FINDINGS.md "LIVE INCIDENT"
(lines 304-309, 2026-09-08 14:1x) - it documents the DATA_ORGANIZE session that
(1) truncated alfred/manifest.csv to 0 bytes mid-crash, (2) destroyed more_fred's
6 ALFRED vintage rows + lag_days fields by regenerating into the flat schema,
(3) left alfred/<SID>/vintage.csv dirs illegal-by-construction under the layout
test. Its escalation items #1-3 are exactly charter (a)(i)/(ii)/(iii). Damage
state verified on disk this round BEFORE any edit: alfred/manifest.csv was
header-only (1 line); vintage CSVs had been restored 14:56 by someone
(62/62/137 lines, byte-equal to CAMP_BORROW's work_r6/vintage_rebuilt/ source);
my more_etf + bench_r5 manifests were back at their R6-restored bytes.

TDD EVIDENCE (RED first, then smallest fix, then GREEN):
- RED: work_r7/test_organize_postmortem.py written first: 9 tests, ran RED at
  HEAD with exactly 5 failing (T2 crash-midwrite-truncates, T4 rich-schema
  regen unguarded, T5 lag-floor regen unguarded, T6 subdir-artifact-ref regen
  unguarded, T8 real more_etf/bench_r5 unguarded - AttributeError: no
  _regen_refusals). T1 (crash-before-open) already passed at HEAD because
  manifest_rows() runs before open(); disclosed as not-RED. T3/T7 are contract
  pins, T9 is the (b) decision pin (green by design).
- FIX 1 of 2 (campaign/team/agents/DATA_ORGANIZE/organize_lib.py, +64 lines):
  (i) _atomic_write_manifest(): csv serialization into <path>.tmp then
  os.replace (atomic same-fs); BaseException path unlinks the tmp. The 14:10
  open-then-crash truncation class is now structurally impossible.
  (ii) _regen_refusals() + ManifestRegenerationRefused: write_manifest refuses
  (loud RuntimeError, no write) when the CURRENT manifest is unreadable,
  non-canonical schema (rich columns like span_class/lag_days the flat write
  would destroy), or references subdir artifacts (PIT vintage rows). Absent and
  0-byte manifests (the incident damage state, nothing left to destroy) and
  canonical ones regenerate freely - legitimate sweeps are not wedged.
- FIX 2 of 2 (campaign/team/tests/test_data_layout.py): (iii) _pit_dirs()
  content-class + reservation wired into _in_reserved_raw() and
  test_raw_subdirs_use_reserved_names; two new two-way tests. The class is
  granted BY CONTENT - a dir qualifies iff it holds EXACTLY vintage.csv in
  release-event schema (hdr release_date,observation_date) - so it cannot be
  squatted (stray dir stays rogue) and never goes stale (losing vintage.csv
  de-classifies -> re-flagged). Two-way fail-closed survives by construction.
  alfred/DRALACBS-style series-ID dirs stay legal WITHOUT renaming (renaming
  would break CAMP_BORROW/FREDMORE path pins); the literal '_pit' name is also
  reserved in raw_subdir_convention.json for future PIT drops.
- GREEN: 9/9 in work_r7. One mid-fix iteration: T7 failed against production
  behavior - my fixture wrote a headerless file (genuinely non-canonical, guard
  correctly refused it); fixed the FIXTURE, not the guard.
- Deadlock resolved (the fix behind the fix): the layout test's canonical-schema
  check DEMANDED flattening exactly what the new guard REFUSES to flatten - that
  contradiction was the pressure that produced the 14:40 clobber. Added
  campaign/team/agents/DATA_ORGANIZE/rich_manifest_registry.json pinning the
  two legitimately-rich manifests (more_etf 10-col span_class, bench_r5 27-col
  corr/sha pins) with required_cols; the layout test now grants them an
  exemption two-way (lose a required column -> fail; regain canonical schema ->
  'RICH_PIN_FLATTENED(registry entry stale)' fail). Unpinned rich schemas still
  fail loud (no license to flatten by hand either).
- REAL-TREE VERIFICATION (no fabrication, all commands run live):
  * Guard: _regen_refusals on the live tree -> more_etf RICH_SCHEMA(10-col),
    bench_r5 RICH_SCHEMA(27-col) = protected; more_fred/alfred/twelvedata = []
    (regenerable; the destroyed rich rows are unrecoverable from current files,
    recovery is FREDMORE/CAMP_BORROW's documented lane, disclosed in
    MANIFEST_R7.md).
  * Atomic path: write_manifest('twelvedata') re-run live -> rows=104, sha256
    e251e647af9761c5 before == after (byte-identical regeneration), no .tmp
    litter.
- SUITE DELTAS (exact, all re-run this session):
  * campaign/team/tests/test_data_layout.py: baseline 1 passed / 9 failed ->
    now 5 passed / 7 failed. Cleared: test_csvs_uniform_date_column_with_
    pinned_exceptions (vintage.csv exemption), test_no_empty_family_dirs
    (transient, passed in final runs), test_manifests_canonical_schema_
    and_complete w.r.t. more_etf/bench_r5 (registry exemption; altlib STALE +
    fx_hist BAD_SCHEMA still fail = other families' debt, loud).
    New tests all green: test_pit_class_is_content_classified_two_way,
    test_pit_vintage_files_exempt_from_date_column_rule.
  * Remaining 7 layout failures are PRE-EXISTING debt, none mine, all loud:
    altlib (6 unpinned .py, 3 raw subdirs, STALE manifest disk=0/rows=12),
    fx_hist (5-col schema), akshare (no README/manifest), yfin (no
    README/manifest - DATA_YFIN agent live mid-round at 22:1x), 12
    __pycache__/.pytest_cache items, 2 altlib .pyc. NOT cleared by design:
    not charter-named for me and other agents own those families.
  * work_r5 bench suite 8/8 (deliverable byte-pin T4 green: fresh sha
    326afe5a28db2809... == R5-committed pin); full DATA_ETF_MORE dir 39/39;
    R3+R4 data suites 22/22.
  * campaign/team/tests overall: 70 passed / 13 failed where 5 are
    test_merge.py failures PRE-EXISTING at HEAD (their loader call
    load_series('twelvedata','SPY') omits '.csv' ->
    FileNotFoundError, file mtime 13:49 = the DATA_ORGANIZE session's own
    test, not my surface) and 7 are the layout debt above.

## (b) twelvedata/manifest.csv - DOCUMENTED (stays canonical), test-pinned

Charter said "restore ... from the foreign 82x7 schema to the 10-col span_class
schema via the R3 builder ... or document precisely why it must stay foreign."
Verdict: the premise conflated two files; full evidence chain in MANIFEST_R7.md
(new, same dir). The "82x7 foreign" was CLOBBERED more_etf (restored in R6,
sha16 9b04a324ebb4db04 re-verified unchanged this round); twelvedata/manifest.csv
was BORN canonical (DATA_ORGANIZE organize_lib's own 7-col output), the 14:40
sweep regenerated it in place with no schema change, proven by byte-comparing
the 09-08 cron-transcript's pre-clobber bytes (twelvedata,AAPL.csv,date,
timeseries,5000,6, / ABBV 3423) against the current file: same schema, order,
values. Zero DATA_ETF_MORE builder ever wrote it (R1-R4 scripts all target
more_etf/); zero consumers need span_class for it (SPY is consumed via
twelvedata/SPY.csv directly by path, sha16 d35d72808dcc9fc3 = the V2 section-7c
trio pin exactly, re-verified). Converting it would violate the canonical
layout contract AND, post-(a), be locked forever by the guard. It must stay
canonical + disk-accurate: pinned by test_t9 (file set == disk, schema ==
canonical, SPY/AAPL/AGG row+col counts == disk).

## Round-7 test totals (all re-run green at close)

work_r7 9/9 (5 RED-first verified at HEAD) | layout 5 passed/7 failed (baseline
1/9; my corner green; 7 loud foreign-family debts) | work_r5 8/8 | DATA_ETF_MORE
full dir 39/39 | R3+R4 suites 22/22. Champion sha 4358dfab95679b97 untouched.
Reproduce: python3 -m pytest campaign/agents/chief/coord/DATA_ETF_MORE/
python3 -m pytest campaign/team/tests/test_data_layout.py -k "pit or manifests"

ROUND 7 DONE

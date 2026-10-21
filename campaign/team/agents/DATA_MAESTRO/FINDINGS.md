# DATA_MAESTRO FINDINGS — Round R1, 2026-09-08 (started 13:44, executed ~14:30–15:05 CST)

## Context observed at execution time
- A fleet-wide reorganizer pass mutated the ENTIRE data estate WHILE I worked: all 71
  manifest.csv mtimes = 14:40:11–14:40:13 (I first saw transient self-referential rows,
  then header-only 47-byte stubs); bench_r5/cboe_options/cboe_flow CSVs emptied ~14:10–14:17
  (cboe_options CSVs moved to latest/); alfred/DRALACBS landed 14:56:20 (DATA_PULL alive).
- Consequence: figures below are fresh-read; the tree may drift again after this timestamp.

## Charter deliverable 1 — coverage map REGENERATED (build_coverage.py, TDD)
- TDD RED->GREEN: added 4 new tests to campaign/team/tests/test_data_maestro.py; final
  suite: **11 passed in 12.52s** (fresh, post-fix; earlier full-team run: 11/11 twice).
- Bug 1 (count inflation): cb_rates claimed 6 series; disk truth = 5 data CSVs — generator
  counted the manifest_lint.csv byproduct row. RED: "generator counted 6, disk truth 5";
  GREEN: byproduct rows excluded. Only offender estate-wide (audited all 71 manifests).
- Bug 2 (stale fail labels): doc claimed "UNPARSABLE manifest: EmptyDataError" for 20
  families whose manifests are now parseable header-only (47 B). Now "EMPTY manifest".
- Bug 3 (hidden data): cboe_options manifest EMPTY while latest/ held 9 CSVs → map hid
  data. RED: "cboe_options: empty manifest + 81 on-disk CSVs must be flagged" (81 = live
  restore in progress); GREEN: recursive count + "NEEDS ORGANIZE (9 CSVs on disk...)".
  First GREEN attempt exposed a real race (file deleted between os.walk and open,
  cboe_pcr/equitypc.csv FileNotFoundError) → fail-closed tolerance added.
- Bug 4 (span poverty): 14:40 manifest standard dropped start/end AND lint columns →
  52/71 families showed span "?" and lint n/a. Added CSV-probe span derivation
  (first-data-row + last-data-row of each CSV; BOTH ends checked). Caught 2 of my own
  probe bugs pre-commit: (a) header row treated as data → bis_eer 2026-07-01..2026-09-01
  (wrong; fixed → 1994-01-01..2026-09-01); (b) break-after-first-match → same defect.
  Post-fix spot checks vs direct head/tail reads: bis_eer 1994-01-01..2026-09-01 ✓,
  mof_jgb 1974-09-24..2026-08-31 ✓, more_fred 1854-12-01..2026-09-08 ✓, noaa_climate
  1950-01-01..2026-07-01 ✓, cb_rates 2001-01-02..2026-09-04 (5 series) ✓.
- Determinism: 2 consecutive regens → identical md5 958e64f1a8e28db264593ec91b2bbea8.
- Files: build_coverage.py 176 lines (<200 cap), test_data_maestro.py 143 lines.

## Estate census (fresh reads, exact numbers)
- 71 family dirs, all manifest-bearing; 52 with data, 19 EMPTY manifests; 0 true stub dirs.
- Largest families: polygon_v2 351→(reorg; regen shows) more_fred 144, eia_weekly 215→215,
  more_cot 105 (was 35 pre-reorg, +70 COT contracts incl. 1971-01-04 era), twelve_extend 440.
- Long-span anchors intact: more_fred 1854-12-01+, bis_eer 1994+, boe_curve 1979-01-02+,
  mof_jgb JGB curve 16 tenors 13,290 rows 1974+, noaa_climate nao 919 rows 1950+, wb_cmo
  1960+, cboe_opts 1986-06-20+ (22 series).

## Charter deliverable 2 — ranked gap list (all four items cite disk probes; in doc)
1. BAML credit OAS TRUNCATED: BAMLH0A0HYM2 = 787 rows starting 2023-09-05 (FRED serves
   1996-12+, ~7,400 rows) → RES_CREDIT decade+ gate FAILS by ~13y. Repair = top priority.
2. German daily Bund curve ABSENT (JP + GB sovereign dailies exist; DE missing).
3. Daily NAO/AO absent (monthly 1950+ complete: nao 919 rows/0 nulls, meiv2 571).
4. VIX1D absent estate-wide (2023+ only → decade+ gate fail; bonus only).
Prior-round gaps RESOLVED and retired from list: FRED monthly base-metals/grains landed
(PALUMUSDM/PCOPPUSDM/PCOTTINDUSDM/PWHEAMTUSDM/PSOYBUSDM/PSUGAUSAUSDM/PCOFFOTMUSDM, 415
rows each, 1992-01-01..2026-07-01); more_cot expanded 35→105; mof_jgb full curve was
already present (old "1 file" note was wrong in spirit — it IS the full curve).

## Charter deliverable 3 — assignments issued (post-reorg repair round R1; in doc)
- DATA_PULL: full BAML OAS history re-pull (+VIX1D bonus). Acceptance: BAMLH0A0HYM2
  >= 7,000 rows from 1996-12.
- DATA_CLEAN: restore lint columns fleet-wide (52/71 families lint n/a after reorg).
- DATA_ORGANIZE: reconcile 19 empty manifests vs on-disk CSVs; cb_rates byproduct row;
  stub cleanup. Acceptance: manifest count == disk count for ALL 71.
- DATA_MERGE: panel_vixterm via campaign/team/lib/merge.py (absent on disk).

## Escalations (not my remit, evidence attached)
1. DATA_MERGE regression: merge.load_series("twelvedata", "SPY") raises FileNotFoundError —
   loader requires "SPY.csv" (merge.py:144 maps spy→"twelvedata/SPY.csv"; disk has SPY.csv).
   test_merge.py 4 FAIL (load_series/union/fill/panel smoke). merge.py mtime 14:35 = mid-edit.
   NOTE: test calls load_series("twelvedata","SPY") but loader signature is
   load_series(family, fname) — the third positional arg col="close" lands on sub →
   path twelvedata/SPY/close → FileNotFoundError. Root cause = arg-order mismatch,
   either fix owner: DATA_MERGE.
2. Fleet reorg integrity: 19 empty manifests, lint columns dropped estate-wide, bench_r5
   50 series wiped (files gone, gitignored → unrecoverable), cboe_flow/_raw/SPX_History.csv
   survives. Coordinator should confirm the 14:40 pass was intentional and gate future
   passes on test_data_layout.py + test_data_maestro.py.
3. Live-tree junk regenerated DURING session: 4 new __pycache__ dirs (alfred, cboe_opts,
   more_cot, more_fred) ~10 min after I cleaned them (test_data_layout 10/10 at 14:52 →
   4 FAIL at 15:04, e.g. alfred/__pycache__/alfred_dl.cpython-314.pyc + new unpinned
   alfred/DRALACBS vintages). Fix at source: dl scripts must set sys.dont_write_bytecode
   or write pycache outside the data tree; layout test must run AFTER pull passes settle.

## Verification log (commands → exact results)
- python -m pytest campaign/team/tests/test_data_maestro.py → 7 passed (pre-change baseline)
- RED proofs: 6≠5 count; UNPARSABLE stale; NEEDS ORGANIZE missing; span "?" rows — each
  observed failing for the exact intended reason before the minimal fix.
- python -m pytest campaign/team/tests/test_data_maestro.py → 11 passed in 12.52s (final)
- md5 2x regen: 958e64f1a8e28db264593ec91b2bbea8 (identical)
- direct probes: head/tail of BAMLH0A0HYM2.csv (2023-09-05 first data row, 2026-09-03 last,
  788 lines), PALUMUSDM row in more_fred/manifest.csv (415, 1992-01-01, 2026-07-01, 0, 414),
  noaa_climate/manifest.csv (nao 919/1950-01-01, meiv2 571/1979-01-01, 0 nulls each),
  mof_jgb/jgb_curve.csv header (16 tenors) + first row 1974-09-24, cb_rates manifest
  (5 data rows after byproduct exclusion), stooq blocked note (796B HTML JS-gate 3/3).
- Boundary honored: zero browser use; all data ops direct-HTTP lineage; no champion
  artifacts touched.

DATA_MAESTRO DONE
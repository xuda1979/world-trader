# MANIFEST_R7 — twelvedata/manifest.csv: DOCUMENTED, NOT RESTORED (2026-09-08)

Charter R7(b) asked: restore `tools/quant/data/twelvedata/manifest.csv` "from the
foreign 82x7 schema to the 10-col span_class schema via the R3 builder (your flagged
R6 leftover), or document precisely why it must stay foreign."

**Verdict: neither foreign nor ever span_class — it STAYS in the canonical DATA_ORGANIZE
7-col schema, and that is now TEST-PINNED (test_t9).** The charter premise was a
conflation of two files with the same clobber timestamp:

1. `more_etf/manifest.csv` — MINE, was 82 rows x 10 cols with span_class, WAS
   clobbered to the foreign 82x7 schema at 14:40 (this is the "82x7" the R6
   FINDINGS line referred to), and was ALREADY RESTORED via the R3 builder in R6
   (sha16 9b04a324ebb4db04, verified unchanged again this round: 82 rows, 3
   span_class values, 2 loud FAILs). Nothing left to do there.
2. `twelvedata/manifest.csv` — NOT MINE and never was: it was born canonical in
   DATA_ORGANIZE's own layout (their `organize_lib.write_manifest` writes exactly
   this 7-col schema), and the 14:40 sweep REGENERATED it in place with no schema
   change. Evidence:
   - The 09-08 cron-session transcript pinned its pre-clobber bytes
     (`twelvedata,AAPL.csv,date,timeseries,5000,6,` / `ABBV...3423,6,` CRLF) —
     byte-compared this round against the current file: same schema, same row
     order, same values. The "82x7 foreign" description never applied to it.
   - No DATA_ETF_MORE builder ever wrote it: my manifests (R1-R4) were all
     more_etf-family only (work_r1/work_r2/work_r3/work_r4 scripts all target
     `more_etf/`); zero span_class-era writes to twelvedata anywhere in my
     FINDINGS/MANIFEST_R*.md or the DATA_ORGANIZE LOG.log.
   - Zero consumers tree-wide need span_class for it: SPY (the only twelvedata
     series in the pinned trio) is consumed via `twelvedata/SPY.csv` DIRECTLY by
     path (bt.beats_passive pins, V2 section-7c), not via any manifest row. SPY.csv
     sha16 re-verified this round: d35d72808dcc9fc3 = the V2 7c pin exactly.
   - Converting it to my 10-col ETF schema would (a) violate the canonical layout
     contract for a family whose CSVs are OHLCV 6-col equity/FX rows, not the
     [date,close] ETF lint my schema's columns describe, and (b) since R7(a) it
     would be LOCKED by the regeneration guard (a rich manifest refuses flat
     regeneration), permanently freezing an artifact that is legitimately and
     byte-stably regenerable: `write_manifest('twelvedata')` re-run this round
     reproduced it byte-identically (sha256 e251e647af9761c5... before == after).

## What R7(a) added that makes this state safe

- `organize_lib._regen_refusals()` + `ManifestRegenerationRefused` in
  `campaign/team/agents/DATA_ORGANIZE/organize_lib.py`: any future organize sweep
  now FAILS CLOSED rather than re-flattening rich manifests (more_etf, bench_r5 —
  refusal verified live this round) or truncating-on-crash (atomic tmp+os.replace).
- `rich_manifest_registry.json` (same dir): pins the two legitimately-rich
  manifests with required_cols, two-way (a pinned manifest that loses a column OR
  regains the canonical schema fails the layout test).
- `test_t9` in `DATA_ETF_MORE/work_r7/test_organize_postmortem.py`: twelvedata
  manifest must STAY canonical 7-col + disk-accurate (file set + row/col counts
  spot-checked against the actual CSVs). If a future sweep makes it stale, this
  fires.

## Related damage NOT fixed here (owner lanes, disclosed)

- `alfred/manifest.csv` is header-only (the 14:10 truncation damage; its 6 rich
  ALFRED vintage rows + lag-floor fields are unrecoverable from the current file).
  CAMP_BORROW delivered the rebuilt vintage CSVs (work_r6/vintage_rebuilt/, now
  restored on disk at alfred/<SID>/vintage.csv, 62/62/137 lines) and DATA_FREDMORE
  pins the manifest row count (166 vs current 145) in their verifier — restoring
  those rows is FREDMORE/CAMP_BORROW's manifest schema, not my 10-col ETF builder's.
- Pre-existing layout-test failures in OTHER families (altlib unpinned .py +
  raw subdirs + STALE manifest, fx_hist 5-col schema, akshare missing
  README/manifest, yfin mid-round churn) were RED before this round and are not
  charter-named for me. Layout suite moved 9 failed/1 passed -> 7 failed/5 passed
  with my corner green (12 more_efm/work_r7 tests).

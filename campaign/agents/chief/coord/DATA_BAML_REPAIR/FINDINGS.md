# DATA_BAML_REPAIR — FINDINGS (2026-10-12)

**Verdict: PHANTOM CONFIRMED — DATA_COVERAGE item-1's "~7,400 rows" claim is falsified on
every FRED route. No repair is possible; the item is closed as source-truncation. One new
hazard discovered and fenced: the truncation window ROLLS, so a blind re-pull is now
data-DESTRUCTION, not repair.**

## The contradiction under test
- DATA_COVERAGE item-1 (regenerated 2026-09-17): "more_fred BAML OAS files are TRUNCATED on
  disk (BAMLH0A0HYM2 = 787 rows, 2023-09-05..2026-09-03; FRED serves 1996-12+ ~7,400 rows).
  Re-pull FULL history ... Unblocks RES_CREDIT (decade+ span gate currently FAILED by ~13
  years)."
- HUNT_CREDIT2 R2 (2026-09-2x) verified the OPPOSITE on every route it tried: API with
  observation_start=1996-12-31, fredgraph.csv, aliases — all returned 2023-09+ only.
- ITER61_AXES_AUDIT (2026-10-12, earlier this session) named this contradiction the single
  most concrete data-side residual in the 87-axis map: "the DATA_COVERAGE item-1 repair
  (full re-pull via fredgraph.csv) would convert this into a genuinely new measurement
  opportunity (credit-spread signals on 1996+ history)."

## Probe (pre-registered 3 routes + 2 follow-ups, all live 2026-10-12)
Script: work/probe_baml_routes.py (fail-closed, read-only, writes nothing to data dirs).
FRED key from .env.local.

| route | rows | first | last | verdict |
|---|---|---|---|---|
| (a) API, NO observation_start (repair-script premise) | 786 | 2023-10-10 | 2026-10-08 | TRUNCATED |
| (b) fredgraph.csv, no key | 794 | 2023-10-10 | 2026-10-08 | TRUNCATED |
| (c) API, explicit observation_start=1996-12-31 | 794 | 2023-10-10 | 2026-10-08 | TRUNCATED |
| (d) alfredgraph.csv (ALFRED archival CSV) | 794 | 2023-10-10 | 2026-10-08 | TRUNCATED |
| (e) ALFRED vintage API (realtime 1996-12-31..2026-10-12) | — | — | — | HTTP 400: "The series does not exist in ALFRED but may exist in FRED." |

## Root cause (from FRED's own series metadata, fetched live)
- `observation_start: 2023-10-10`, `observation_end: 2026-10-08` — the series span ITSELF
  is 3 years, as served.
- Note, verbatim: **"Starting in April 2026, this series will only include 3 years of
  observations. For more data, go to the source."** This is an ICE licensing cap —
  STANDUP_LOG 2026-09-11 already recorded this mechanism ("the ICE BofA BAML* truncation
  is an ICE LICENSING CAP at FRED"), but DATA_COVERAGE.md item-1 (regenerated 2026-09-17,
  AFTER that standup) still carried the phantom "~7,400 rows" claim and the "re-pull FULL
  history" instruction. The regeneration propagated a stale premise into the map that
  drives MAESTRO assignments; the audit caught it; this round kills it at both sites
  (doc + generator, build_coverage.py) so no future regeneration resurrects it.

## The rolling-window hazard (NEW — worse than either R1 or R2 recorded)
- On-disk files (pulled ~2026-09-03): BAMLH0A0HYM2 787 rows **2023-09-05**..2026-09-03;
  BAMLC0A0CM 786; BAMLEMHBHYCRPIOAS 793 (newdata manifest) / 787 (more_fred);
  fred_full/BAMLH0A0HYM2.csv 780 rows 2023-09-22..2026-09-01.
- FRED today serves from **2023-10-10**. The window has rolled ~5 weeks past the on-disk
  front month. Therefore the on-disk files are the ONLY surviving copy of
  2023-09-05..2023-10-09 anywhere in the estate (ALFRED has no vintage either).
- Consequence: executing item-1 as written ("re-pull FULL history"; acceptance
  "BAMLH0A0HYM2 >= 7000 rows") or running repair_baml_oas.py would fetch 786-794 rows
  starting 2023-10-10 and overwrite the on-disk CSVs — silently destroying a month of
  data while failing its own acceptance gate. The instruction was not merely wrong; it
  had become destructive.

## Actions taken (phantom-documentation path, pre-registered)
1. tools/quant/data/more_fred/repair_baml_oas.py: docstring rewritten (DEAD banner,
   falsified-premise record, preserved original text); HARD RUNTIME GUARD added at
   main() — raises SystemExit before any fetch. Verified: running it exits 1 with the
   guard message. The script can no longer destroy the front month even if run in error.
2. campaign/team/docs/DATA_COVERAGE.md item-1: replaced with the CLOSED/phantom record
   (root cause, rolling-window destruction warning, dead-script marker, beat-path-1
   pointer for licensed long-history credit spreads).
3. campaign/team/docs/DATA_COVERAGE.md DATA_PULL assignment row: VOIDED with strikethrough
   (premise + acceptance); VIX1D bonus acceptance unchanged.
4. campaign/team/agents/DATA_MAESTRO/build_coverage.py: SAME two edits applied to the
   generator (item-1 text + DATA_PULL row), so the next regeneration emits the closed
   record, not the phantom. This was the resurrection vector — fixed at the source.
   VERIFIED: generator re-run regenerates DATA_COVERAGE.md emitting the closed text
   (n=2 stubs — honest disk re-scan adds binance_dl_common, matching the audit's
   bookkeeping-artifact note; no other content drift).
5. ITER61_AXES_AUDIT/FINDINGS.md: dated addendum — residual (a) CLOSED, residuals now
   (b)/(c) only. Point-in-time documents get corrections, not rewrites.
6. No data files touched: no re-pull, no lint re-run needed (data unchanged). The
   raw-data manifest DID move — repair_baml_oas.py itself lives inside the pinned
   gitignored tree — so the manifest protocol ran: re-emit, re-pin, ledger note
   (see verification record below).

## Standing consequences for the estate
- RES_CREDIT (HUNT_CROSSASSET2 row 41, blocked/truncated) is PERMANENTLY blocked on the
  decade+ span gate via FRED — not "pending repair". Long-history credit spreads need a
  new axis (licensed ICE direct, or a proxy axis e.g. TED/FRA-OIS spreads or HYG-LQD
  decomposition) — that is beat-path-1 (new data-axis acquisition) and requires an
  OPERATOR charter per goal.md; it is NOT auto-scoped by this round.
- The on-disk more_fred + fred_full BAML files are now load-bearing archival artifacts.
  Do not overwrite, re-pull, or "refresh" them. A future DATA_MAESTRO regeneration should
  keep their manifest rows as-is (span 2023-09 is the frozen window, not a lint error).
- ITER61_AXES_AUDIT's residual list narrows to: (b) Binance CBOE H1/options axes pending
  live accumulation; (c) Binance short-span trigger re-measure (fires 2027-09). The
  "fred_full BAML full-history repair" residual is CLOSED by this round.

## Checklist (pre-registered in goal.md round entry)
probe ✓ (5 routes) → decide ✓ (phantom, no repair) → repair-or-document ✓ (document;
hard guard) → lint/manifest/suite verify ✓ (see below) → DATA_COVERAGE ✓ + standup ✓ +
goal round entry ✓ → explicit-pathspec commit ✓.

## Manifest + suite verification record (final gate)
- RAW-DATA MANIFEST: this round edits repair_baml_oas.py, which lives INSIDE the
  gitignored tools/quant/data/ tree (single-copy, manifest-pinned). First verify after
  the edit was RED exactly as designed: "EXTRA more_fred/repair_baml_oas.py (5151 B,
  sha16 90e2dd099ef5fe77) / MISSING (3321 B, 1ce4082a7743f1cf)" — the pin caught the
  byte change fail-closed. Per the test's own protocol (re-emit, re-pin, ledger note):
  --emit re-run (11780 files, tree sha16 1cfad63f89775723 -> 662cc9db40d2d355, file
  count unchanged), --verify GREEN, test_raw_data_manifest.py re-pinned (history
  docstring: "DATA_BAML_REPAIR: repair_baml_oas.py fenced DEAD ... 3321->5151 bytes"),
  6/6 GREEN. NOTE: `python3 test_raw_data_manifest.py --verify` exits 0 SILENTLY (test
  module has no CLI handler); the real entry point is campaign/scripts/raw_data_manifest.py.
- FULL SUITE (campaign/bt, first full run since the 10-09 32/720 baseline): 57 failed /
  695 passed. CAUSAL DECOMPOSITION (method: exclusion run): suite minus this round's
  test file = 57 failed / 689 passed — IDENTICAL failure set; test file alone = 6/6
  GREEN. All 41 failing test files contain ZERO references to any file this round
  touched (DATA_COVERAGE.md, build_coverage.py, repair_baml_oas.py,
  RAW_DATA_MANIFEST.csv, test_raw_data_manifest.py). CONTEXT CORRECTION (23:5x, traced
  via the prior-session transcript 27433085): the working tree carries an IN-FLIGHT
  ITER61 ADOPTION — the operator approved at 21:02 CST ("go ahead"); the pre-compaction
  session archived the old trio (SUPERSEDED_by_ITER61_DDCON, 21:24), staged the A_cap28
  champion (21:25:03, NG block exactly 0.28 verified in staged weights; verifier 9/9
  GREEN at 22:37), and was cut off mid-suite-decomposition at 22:53 — its own final
  suite measurement was ALSO 57/695 (transcript line 3339), identical to this round's.
  So the 57 decompose as: adoption-state champion pins (staged A_cap28 vs HEAD
  vintage) + the Oct-10 09:39 append-only sleeve-vintage wave (diescrack 08-10 -> 08-24,
  brwt5 08-10 -> 08-28, append-only verified) + the 32 documented pre-existing classes.
  The adoption commit belongs to the adoption session's operator, not this round; the
  57-set is the adoption-state baseline it was about to adjudicate when cut off.
- LINT: N/A by design (no data CSV touched; the more_fred/fred_full BAML CSVs are
  unchanged and remain correct-for-their-window).

## Repro
- work/probe_baml_routes.py (exit 0 = full history obtainable, 1 = all truncated,
  2 = inconclusive). Today: exit 1.
- FRED metadata: api.stlouisfed.org/fred/series?series_id=BAMLH0A0HYM2 (notes field).
- ALFRED 400: api.stlouisfed.org/fred/series/observations?series_id=BAMLH0A0HYM2
  &realtime_start=2000-01-01&realtime_end=2010-01-01.

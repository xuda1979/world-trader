# CHAMPION COMMIT DECISION MEMO — the "09-28 rewrite" is actually the un-committed ITER49 champion of record

> **STATUS: OPERATOR DECISION PENDING.** Written 2026-10-01 by the main session.
> This memo CORRECTS the premise of the 2026-09-30 19:0x census entry
> ("operator-pending champion re-emission decision on the 09-28 champion rewrite")
> with new forensic evidence. Read §1 before deciding.

## 1. THE CORRECTED FORENSIC (what the 09-30 entry got wrong)

The 09-30 census attributed the MACRO2 r2/r4 REDs to
`campaign/results/GOAL100_RAWEW13v2_WEIGHTED_GEAR16_daily.csv` being "REWRITTEN
2026-09-28 17:02, all 4,807 rows differ vs HEAD." New evidence:

1. **The on-disk CSV (sha16 `cfa9ec4d38158691`) is NOT a 09-28 rewrite. It IS the
   documented champion of record — the ITER49 tsmom vt=0.15 adoption of
   2026-09-19** (STANDUP_LOG session 29: "Champion MOVED: 3c456aa53193eb89 ->
   cfa9ec4d38158691"; headline SR 3.820357 / ann 23.9215% / gross 1.0 /
   MaxDD -3.73% / 0 neg yrs — re-measured this session, exact match).
2. **14 COMMITTED test files at HEAD pin `cfa9ec4d38158691`** (incl.
   test_frontier_closure_manifest.py CHAMPION_PAIR,
   test_iter21_srmax_gear_champion.py, test_audit_champ2_round2.py). The
   champion-of-record hash is already the system of record in git — only the CSV
   blob itself lags.
3. **The CSV was last committed 2026-09-13 (ITER16, `46c5ba59`, sha16
   `ee03f5c096aabb6d`, the gear-1.6 ITER15 vintage, ann 38.11%).** Every champion
   move since (ITER17..ITER49, 09-13 → 09-19: gear 1.6→1.0, A5r2 vt024, QAxasts
   vt015 adoptions) happened on disk but the file was never re-committed. HEAD's
   copy is 6 champion-generations stale, superseded history.
4. **The 17:02:32 09-28 mtime is a bulk-touch signature, not a content rewrite.**
   85+ unrelated files share the exact mtime `Sep 28 17:02:32` (fleet_keeper.py,
   E1 detrunc script, GOAL100_ITER*.md docs, 14 bt test files, the builder). The
   on-disk content equals what ITER49 recorded on 09-19.
5. **Byte-exact reproduction PROVEN this session**: with the two
   frontier-manifest-pinned sleeve vintages (brwt7 `8e76dd581ec6e50d` last
   2026-08-28, C5ng_summer `ccfe3a4bc8706161` last 2026-08-24), the current
   builder reproduces the on-disk champion sha16 EXACTLY (`cfa9ec4d38158691`,
   n=4806, maxdev 9.99e-17). The champion is the sealed frontier book, not a
   rogue emission.

The CHAMPION_CARD.md on disk (uncommitted `M`) also already documents
`cfa9ec4d38158691` / 23.92% — it was regenerated when the card-lint test demands.

## 2. WHY THE 29 REDs EXIST (the actual split)

HEAD is internally contradictory: committed tests pin the ITER49 champion; the
committed CSV is ITER16. The 29-RED documented baseline decomposes as:

- **Committed-CSV-lag class (majority)**: tests that read the committed CSV and
  compare against the champion of record (hash/bytes/stats). GREEN the moment
  the on-disk CSV+weights are committed — zero re-pinning needed, because the
  pins ALREADY expect `cfa9ec4d`/`a384d6b9`.
- **Rebuild-extends class (~4-6 tests)**: `test_rawew13v2::test_reproducible_from_builder`,
  `test_verify_r3_cmd_canonical_pin` ("champion n=4806 rebuild n=4821"), the
  iter19/20/21/23 "reproduces_champion_bytes" family. These fail because two
  sleeves were DELIBERATELY extended AFTER the champion was sealed
  (C5ng_summer DHHNGSP +19 rows through 2026-09-21, 09-28 12:0x session,
  documented in V7_SESSION_2026-09-28.md; brwt7 through 2026-09-14, committed
  3c9caf6c 09-25) so a fresh build now spans 4,821 rows vs the sealed 4,806.
  These REDs are the frontier-seal-vs-later-refresh tension, NOT corruption.
- **iter60 import-seam class (1)**: `test_iter60_charter_caps_held` imports
  `test_frontier_closure_manifest` unqualified — RED from repo root, GREEN from
  the tests dir (the suite's own run convention). Pre-existing, orthogonal.

## 3. OPTIONS (quantified this session)

### Option A — COMMIT the on-disk champion + weights as-is (RECOMMENDED)
- `git add` the CSV (`cfa9ec4d`), weights (`a384d6b9`), CHAMPION_CARD.md
  (already regenerated to match), plus the ITER17-49-era uncommitted docs that
  reference the current champion state.
- Effect: HEAD becomes self-consistent with its own 14 test pins; the
  committed-CSV-lag REDs go GREEN with zero re-pinning; the
  rebuild-extends class stays RED (documented, governed) until a separate
  champion-extension decision.
- Risk: none identified — the content being committed is the documented,
  test-pinned, byte-reproducible champion of record. NOT committing it is the
  actual single-copy loss risk (the 53f4300b class).

### Option B — governed champion EXTENSION first (re-emit through 2026-09-21), then commit
- Fresh build: n=4821, SR 3.8086, ann 23.81%, MaxDD -3.73%, 0 neg yrs
  (vs sealed: SR 3.8204 / ann 23.92%). Would additionally require a 14-file
  re-pin wave (all cfa9ec4d pins → new hash) — the exact churn the frontier
  seal exists to prevent, for a −0.012 SR cosmetic extension.
- NOT recommended as a bundle: extension is a separate governed act
  (frontier-seal amendment), and bundling it converts a consistency fix into
  a champion move.

### Option C — revert disk to HEAD's ITER16 CSV (ann 38.11%)
- Would contradict 14 committed test pins, the CHAMPION_CARD supercede-guard,
  and the STANDUP record of ITER17-49. DO NOT — this is superseded history.

## 4. RECOMMENDATION

**Option A.** The operator decision reduces to: "should git match the documented
champion of record?" The 09-30 census deferred because it believed the on-disk
file was an unexplained rewrite; it is not — it is the sealed ITER49 book,
pinned by 14 committed tests, byte-reproducible from manifest-pinned inputs
(proven §1.5). Committing it is a provenance-closure commit (the 53f4300b /
9eff430e class), NOT a champion move: the champion does not change, only the
lagging git copy does.

After Option A, the remaining RED set should be re-diffed and the
rebuild-extends class documented as its own operator item (champion extension
through 2026-09-21: recommended cadence = next governed refresh round, with the
4-6 test re-pins done under the ITER47/49 dated-addendum convention).

## 5. VERIFICATION GAUNTLET FOR OPTION A (pre-registered)

1. `shasum` CSV == `cfa9ec4d38158691`, weights == `a384d6b92e258fd5` (post-add).
2. `python3 campaign/scripts/rawew13v2_build.py --verify` still prints the
   documented 17:02-vintage numbers (weights IDENTICAL 7.6e-17).
3. Full suite re-run: committed-CSV-lag REDs → GREEN; failure set strictly
   shrinks from 29; no new REDs.
4. `test_frontier_closure_manifest.py` CHAMPION_PAIR GREEN from repo root.
5. STANDUP_LOG + RESEARCH_LOG entries appended (dated), citing this memo.

## 6. PROVENANCE

- Forensic executed 2026-10-01 main session; all reproduction commands in the
  session transcript; sleeves restored byte-exact after the reproduction test
  (brwt7 `611b277ef72b9200`, C5ngsum `0f572f6f8fea2c0d` — verified).
- Numbers: on-disk champion SR 3.820357 / ann 23.9215% / n=4806 /
  2008-03-31..2026-08-28; HEAD (ITER16) SR 3.236 / ann 38.114% / MaxDD -6.56%;
  fresh-4821 SR 3.8086 / ann 23.81%.

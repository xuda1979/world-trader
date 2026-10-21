# FINDINGS.md — TDD_RETRY_TEST round-1 (2026-09-06)

Mission: the coordinator created `test_launch_retry.sh` (21:28) using my agent slot; there is NO
CHARTER.md for TDD_RETRY_TEST — the test file itself IS the assignment. It is a TDD test for the
429-retry logic in `launch_agent_chief.sh`, written because all 20 launch attempts in the
21:30 wave hit GLM rate limits (see coord/FINDINGS.md + STANDUP_LOG.md).

## 0. Safety actions taken FIRST (before any edit)
- My first test run (21:30–21:32) spawned a REAL `claude -p` duplicate of me via
  `launch_agent_chief.sh` (which then hardcoded `/Users/daxu/homebrew/bin/claude`, ignoring
  CLAUDE_BIN): stray pid 95297 (parent launcher 95292) running my exact charter prompt.
  Verified parentage via `ps -o pid,ppid,lstart` and killed ONLY the stray (95297+95292);
  preserved my own pid 89309 (started 21:30:14). No other agent touched.
- The test as written truncated AND deleted `logs/TDD_RETRY_TEST.log` — the transcript of the
  agent named TDD_RETRY_TEST (me). My first run destroyed my own transcript. Kept the only
  surviving fragment (the stray's end-line) as `TDD_RETRY_TEST/log_snapshot_pre_test.txt`.
- Backups before edits (sha256-verified identical):
  - `launch_agent_chief.sh.pre_tdd.bak` = b4b91a7c6215e573… (pre-fix launcher, which itself
    already contained the coordinator's 21:38 `CLAUDE_BIN` fix I found on disk mid-round)
  - `test_launch_retry.sh.orig.bak` = original test before hermetic fix.

## 1. RED — baseline (unfixed launcher, original test)
```
test_launch_retry.sh: line 38: [: : integer expression expected
FAIL: expected 2 invocations, got [] (stale-429 grep re-runs successful rounds, or CLAUDE_BIN ignored)
```
2m20.83s wall (launcher used real claude binary; stub never called → empty count file).
With the coordinator's CLAUDE_BIN fix in place and my hermetic log-seeding, RED became measurable:
```
FAIL: expected 2 invocations, got [3]
```
2m20.79s wall. Full anatomy traced with a scaled-backoff replica (1s instead of 30·n):
```
=== stale: Request rejected (429) ===
API Error: Request rejected (429) - rate limit
rate-limited attempt 1
stub success
rate-limited attempt 2
... (every success misclassified) ...
rate-limited attempt 8        <- all MAXTRY=8 burned, 6 pure wasted calls
=== invocations: 8 ===
```
Root cause: `grep -q "429\|速率限制\|Request rejected" "$LOG"` scans the ENTIRE accumulated
transcript, so a stale 429 from a previous attempt (or a seeded one) keeps matching forever:
successful attempts are misclassified as rate-limited and the loop runs to MAXTRY.

## 2. Fix (launcher) + test hermeticity
`launch_agent_chief.sh` (sha256 1e2b62d6a69111a8…, syntax OK via `bash -n`):
- Each attempt's output is captured to a per-attempt file `.${AGENT}.attempt.$$`, judged
  in isolation, then appended to the transcript — `grep` now targets `$ATTEMPT_LOG`, not `$LOG`.
- `LOG_DIR` env override (default unchanged: `coord/logs/`) so tests never again touch the
  shared logs dir / a real agent's transcript.
- `MAXTRY` env override (default 8) for fast testing.
Test made hermetic: uses `LOG_DIR` into mktemp dir, seeds a stale-429 line, never touches
shared `logs/TDD_RETRY_TEST.log`, `INVOCATIONS` defaults to 0 if count file missing.

## 3. GREEN
```
PASS: claude invoked exactly 2 invocations (1x 429, 1x success)
real 0m32.804s / sys 0m31.587s wall 32.804s → 32.587s on re-run, exit 0
```
(2 = 1 real 429 + 1 success; the seeded stale 429 no longer re-triggers the loop.)

## 4. Regression matrix (5 cases, stub-driven, MAXTRY=3, terminal-marker waits)
```
PASS [fresh-log+success]:            calls=1 expected=1   (success never retried)
PASS [real 429 then success]:        calls=2 expected=2   (genuine retry preserved)
PASS [real 429,429 then success]:    calls=3 expected=3   (genuine retry preserved)
PASS [STALE 429 + immediate success]:calls=1 expected=1   (stale log cannot re-trigger)
PASS [STALE 429 + 1 real fail]:      calls=2 expected=2   (stale line + real backoff correct)
```
Honest note: an earlier version of this matrix reported 3 false FAILs — my matrix harness
waited on `"round 1 end\|rate-limited"` and sampled the count file while the launcher was
still inside its 30s backoff sleep. Fixing the harness (wait on the terminal `"round 1 end"`
marker only) resolved all 3 without any further launcher change. Launcher untouched between
the two matrix runs; harness bug, not a product bug.

## 5. Residual risks / notes for coordinator
- `grep` pattern is line-substring based: a successful transcript that happens to contain
  "429" in its text (e.g. an agent writing a report about rate limits — like this FINDINGS
  file) would be misclassified as rate-limited on the NEXT round if it were captured in that
  attempt's output. Risk accepted for now (same pattern as pre-fix; per-attempt scoping means
  it only misfires if THIS attempt's own output contains the substring). Mitigation option:
  require `rc != 0` as a necessary condition before believing a 429 line, or match
  `API Error: Request rejected (429)` specifically. Note claude CLI emits 429s with exit 0
  (message-only), so rc-gating alone is insufficient — that is why a message match is needed.
- Real-wave validation still pending: the fix is stub-verified only. Recommend coordinator
  re-launch the 20-agent wave via `launch_all.sh` when API capacity returns; per-agent logs
  will now show `rate-limited (attempt N)` lines only on genuinely rate-limited attempts.
- `TDD_RETRY_TEST` is not in `AGENTS.txt`, so `launch_all.sh` / `monitor.sh` ignore me —
  correct (I am a test slot, not a fleet member); no fleet-side changes needed.
- `MAXTRY`/`LOG_DIR`/`CLAUDE_BIN` are all env-tunable now; defaults are unchanged behavior.
- Not committed (per instructions — no commits without explicit instruction); coordinator can
  `git add campaign/agents/chief/coord/{launch_agent_chief.sh,test_launch_retry.sh}` and review
  the diff; pre-fix backups live in this directory with sha256 pinned above.

ROUND 1 DONE
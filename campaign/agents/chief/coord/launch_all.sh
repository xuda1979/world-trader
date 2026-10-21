#!/bin/bash
# Launch roster agents (round passed via ROUND, default 1) with IDEMPOTENCY GUARDS.
# Guards added 2026-09-07 after two real failures:
#  (1) a DONE role was re-run all of round 1 by a leftover launcher (HUNT_INTERNATIONAL2);
#  (2) a role with a live launcher would get a duplicate racing on the same FINDINGS.md.
# Staggered launch (STAGGER secs between roles, default 20) avoids the 13/20 429 storm
# of 2026-09-06 (gateway caps CONCURRENT requests per key).
ROOT="${ROOT:-/Users/daxu/software/world-trader/campaign/agents/chief/coord}"
STAGGER="${STAGGER:-20}"
ROUND="${ROUND:-1}"
# Concurrency cap (TDD 2026-09-07 02:4x): the GLM gateway caps CONCURRENT requests
# per key; a 19-wide wave starves itself to death on 429 retries (real failure
# 01:51-02:40: 18/20 agents did zero round-2 work). COUNT_CHECK is a test seam
# returning the live-wrapper count.
# DEFAULT CAP (TDD 2026-09-07 12:1x, real failure 08:00-10:30): unset used to mean
# UNLIMITED, so the round-3 wave ran ~10 concurrent and 13 agents burned all 8
# backoff attempts on 429s with zero output. A cap that must be remembered at every
# invocation is absent exactly when a storm happens -> default 4; explicit env wins.
MAX_CONCURRENT="${MAX_CONCURRENT:-4}"
COUNT_CHECK="${COUNT_CHECK:-}"
PROC_CHECK="${PROC_CHECK:-}"   # optional override for tests: script <agent> -> rc 0 if alive
mkdir -p "$ROOT/logs"

# Single-instance lock (TDD P5/P6, real failure 2026-09-07 01:17): a
# launcher that kept running while this file was being rewritten misfired
# and re-ran 3 DONE combined roles. Only ONE launch_all.sh may hold the
# roster at a time. A lock older than LOCK_TTL_SECS is taken over, so a
# kill -9'd launcher cannot wedge the fleet forever.
LOCK_DIR="$ROOT/logs/.launch_all.lock"
LOCK_TTL_SECS="${LOCK_TTL_SECS:-3600}"
if mkdir "$LOCK_DIR" 2>/dev/null; then
  echo "$$" > "$LOCK_DIR/pid"
  date +%s > "$LOCK_DIR/ts"
  trap 'rm -rf "$LOCK_DIR"' EXIT
else
  lock_ts="$(cat "$LOCK_DIR/ts" 2>/dev/null || echo 0)"
  lock_pid="$(cat "$LOCK_DIR/pid" 2>/dev/null || echo unknown)"
  now="$(date +%s)"
  age=$((now - lock_ts))
  if [ "$age" -gt "$LOCK_TTL_SECS" ]; then
    echo "stale lock (pid $lock_pid, age ${age}s > ${LOCK_TTL_SECS}s) - taking over" >> "$ROOT/logs/launcher.log"
    rm -rf "$LOCK_DIR"
    mkdir "$LOCK_DIR" || { echo "failed to take over stale lock" >> "$ROOT/logs/launcher.log"; exit 1; }
    echo "$$" > "$LOCK_DIR/pid"
    date +%s > "$LOCK_DIR/ts"
    trap 'rm -rf "$LOCK_DIR"' EXIT
  else
    echo "skip launch_all (instance pid $lock_pid holds lock, age ${age}s < ${LOCK_TTL_SECS}s)" >> "$ROOT/logs/launcher.log"
    exit 0
  fi
fi

alive() {  # agent alive if a launcher bash for it is running (marker: .attempt file of a live proc is unreliable; use pgrep on the launcher name)
  if [ -n "$PROC_CHECK" ]; then "$PROC_CHECK" "$1"; return; fi
  pgrep -f "launch_agent_chief.sh $1 " >/dev/null 2>&1 \
    || pgrep -f "research agent $1 in the GOAL100" >/dev/null 2>&1
}

live_count() {  # number of live agent wrappers fleet-wide (test seam: COUNT_CHECK)
  local n=""
  if [ -n "$COUNT_CHECK" ]; then
    n="$("$COUNT_CHECK" 2>/dev/null | head -n 1)"
  else
    n="$(pgrep -f "launch_agent_chief.sh" | wc -l | tr -d " ")"
  fi
  # Fail-closed (C5, 2026-09-07): a count that is not a plain non-negative
  # integer previously made [ "" -ge N ] error false and the guard silently
  # DISABLED -> launcher fired into a saturated gateway. Unparseable = defer.
  case "$n" in
    ''|*[!0-9]*) echo "-1"; return ;;
  esac
  echo "$n"
}

COMBINED="HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
done_marker() {  # role DONE iff FINDINGS.md ends with the exact round marker
  f="$ROOT/$1/FINDINGS.md"
  # NOTE: [ ] does LITERAL string equality (glob-match on = is a [[ ]] extension).
  # Real bug caught by test_launch_all_skip 2026-09-07: the old [ " $COMBINED " = *" $1 "* ]
  # NEVER matched, so all 13 combined-dir roles would have been relaunched on round 2.
  if [ ! -f "$f" ] && case " $COMBINED " in *" $1 "*) true;; *) false;; esac; then
    # 13 round-1 roles share ONE combined dir whose literal name is the space-joined
    # role list; a per-role FINDINGS.md will never exist there. Real near-miss 2026-09-07:
    # a per-role-only check missed all 13 and would have relaunched completed roles.
    f="$ROOT/$COMBINED/FINDINGS.md"
  fi
  [ -f "$f" ] && [ "$(tail -n 1 "$f" 2>/dev/null | tr -d '[:space:]')" = "ROUND${ROUND}DONE" ]
}

while read -r a || [ -n "$a" ]; do
  [ -n "$a" ] || continue
  # Comment lines are roster annotations (e.g. CIO's 2026-09-07 HUNT_TIMESFM note),
  # never roles - the old parser tried to LAUNCH a role named "#" (TDD R1,
  # test_roster_comments.py: stub invocations were ['#', 'Z_READY']).
  case "$a" in "#"*) echo "skip comment line" >> "$ROOT/logs/launcher.log"; continue ;; esac
  if done_marker "$a"; then
    echo "skip $a (FINDINGS ends ROUND $ROUND DONE)" >> "$ROOT/logs/launcher.log"
    continue
  fi
  if alive "$a"; then
    echo "skip $a (launcher/agent already alive)" >> "$ROOT/logs/launcher.log"
    continue
  fi
  if [ -n "$MAX_CONCURRENT" ]; then
    n_live="$(live_count)"
    # Fail-closed: -1 = unparseable count -> treat as AT CAP (defer), never launch.
    if [ "$n_live" -eq -1 ] || [ "$n_live" -ge "$MAX_CONCURRENT" ]; then
      echo "defer $a (fleet at cap: ${n_live} live >= MAX_CONCURRENT=$MAX_CONCURRENT)" >> "$ROOT/logs/launcher.log"
      continue
    fi
  fi
  echo "launch $a round $ROUND at $(date +%H:%M:%S)" >> "$ROOT/logs/launcher.log"
  "$ROOT/launch_agent_chief.sh" "$a" "$ROUND" >> "$ROOT/logs/launcher.log" 2>&1
  sleep "$STAGGER"
done < "$ROOT/AGENTS.txt"
echo "== all launch commands issued at $(date +%H:%M:%S) =="

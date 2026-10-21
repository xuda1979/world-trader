#!/bin/bash
# Standup monitor v4.1 (2026-09-07, TDD: TDD_RETRY_TEST/test_monitor_v4.sh 9/9 green).
# v3 REAL FAILURE (07:04:04 snapshot): substring-grep "ROUND 1 DONE" + combined-dir
# credit marked ALL 20 DONE while 3 agents were mid-round-2. v4 mirrors
# launch_all.sh done_marker() exactly:
#   DONE     <- effective FINDINGS.md LAST LINE (whitespace-stripped) == "ROUND ${ROUND}DONE"
#   RUNNING  <- not DONE and per-role log mtime within LOG_TTL_SECS (default 900)
#   BLOCKED  <- everything else (fail-closed: unknown == not done)
# ROUND env selects the wave (default 2). ONE_SHOT=1 runs a single snapshot and exits
# (test seam; the background loop stays available for production use).
ROOT="${ROOT:-/Users/daxu/software/world-trader/campaign/agents/chief/coord}"
HIST="${HIST:-$ROOT/status_history.txt}"
LOG_TTL_SECS="${LOG_TTL_SECS:-900}"
ROUND="${ROUND:-2}"
COMBINED="HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
COMBINED_DIR="$ROOT/$COMBINED"

snapshot_once() {
  echo "===== STANDUP $(date '+%Y-%m-%d %H:%M:%S') round=$ROUND ====="
  while read -r a || [ -n "$a" ]; do
    [ -n "$a" ] || continue
    case "$a" in "#"*) continue ;; esac  # comments are annotations, not roles (TDD R3)
    st=""
    f="$ROOT/$a/FINDINGS.md"
    # 13 round-1 roles share ONE combined dir named by the space-joined role list;
    # a per-role FINDINGS.md will never exist there (same rule as launch_all.sh).
    if [ ! -f "$f" ] && case " $COMBINED " in *" $a "*) true;; *) false;; esac; then
      f="$COMBINED_DIR/FINDINGS.md"
    fi
    if [ -f "$f" ] && [ "$(tail -n 1 "$f" 2>/dev/null | tr -d '[:space:]')" = "ROUND${ROUND}DONE" ]; then
      st="DONE"
    fi
    if [ -z "$st" ]; then
      logf="$ROOT/logs/$a.log"
      if [ -f "$logf" ]; then
        age=$(( $(date +%s) - $(stat -f %m "$logf") ))
        if [ "$age" -le "$LOG_TTL_SECS" ]; then st="RUNNING"; fi
      fi
    fi
    if [ -z "$st" ]; then
      # v4.1 (TDD T9, real case 07:19:42): the launcher logs only at attempt
      # boundaries, so a healthy agent mid-attempt looks log-stale. Any fresh
      # file under the role dir (excl. FINDINGS.md, excl. hidden) proves life.
      if [ -n "$(find "$ROOT/$a" -type f ! -name "FINDINGS.md" ! -name ".*" -mmin -"$((LOG_TTL_SECS / 60))" -print -quit 2>/dev/null)" ]; then
        st="RUNNING"
      fi
    fi
    [ -n "$st" ] || st="BLOCKED"
    printf "  %-22s %s\n" "$a" "$st"
  done < "$ROOT/AGENTS.txt"
}

if [ "${ONE_SHOT:-0}" = "1" ]; then
  snapshot_once
  exit 0
fi
while true; do
  snapshot_once >> "$HIST" 2>&1
  sleep 90
done

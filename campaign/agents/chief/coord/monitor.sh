#!/bin/bash
# Background standup monitor: log the 20-agent wave status every 90s to status_history.txt
# v3 (2026-09-06 23:3x): fixes v2 bug — v2 credited the combined-role FINDINGS to ALL 20
# roles (every role greps the combined file, matches "ROUND 1 DONE", reads DONE). v3
# restricts combined-dir credit to the 13 roles that dir actually covers, and adds:
#   DONE     <- "ROUND 1 DONE" in per-role FINDINGS.md, or in combined FINDINGS.md
#               ONLY for the 13 combined-covered roles
#   RUNNING  <- not DONE and its log touched within LOG_TTL_SECS (default 900)
#   BLOCKED  <- everything else (never started / stalled past TTL)
ROOT=/Users/daxu/software/world-trader/campaign/agents/chief/coord
HIST="$ROOT/status_history.txt"
LOG_TTL_SECS="${LOG_TTL_SECS:-900}"
COMBINED="HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
COMBINED_DIR="$ROOT/HUNT_CRYPTO2 HUNT_CMDT2 HUNT_MACRO2 HUNT_FXCARRY2 HUNT_SECTOR2 HUNT_CREDIT2 CAMP_SHORT CAMP_BORROW CAMP_COST DATA_FREDMORE DATA_ETF_MORE AUDIT_FWBUGS AUDIT_RECON"
while true; do
  {
    echo "===== STANDUP $(date '+%Y-%m-%d %H:%M:%S') ====="
    while read -r a || [ -n "$a" ]; do
      [ -n "$a" ] || continue
      st=""
      f="$ROOT/$a/FINDINGS.md"
      if [ -f "$f" ] && grep -q "ROUND 1 DONE" "$f" 2>/dev/null; then
        st="DONE"
      else
        case " $COMBINED " in
          *" $a "*)
            if [ -f "$COMBINED_DIR/FINDINGS.md" ] && grep -q "ROUND 1 DONE" "$COMBINED_DIR/FINDINGS.md" 2>/dev/null; then
              st="DONE"
            fi
            ;;
        esac
      fi
      if [ -z "$st" ]; then
        logf="$ROOT/logs/$a.log"
        if [ -f "$logf" ]; then
          age=$(( $(date +%s) - $(stat -f %m "$logf") ))
          if [ "$age" -le "$LOG_TTL_SECS" ]; then st="RUNNING"; fi
        fi
      fi
      [ -n "$st" ] || st="BLOCKED"
      printf "  %-22s %s\n" "$a" "$st"
    done < "$ROOT/AGENTS.txt"
  } >> "$HIST" 2>&1
  sleep 90
done

#!/bin/bash
# STANDUP STATUS — aggregate agent status + latest FINDINGS tail (the "standup meeting").
ROOT="${ROOT:-/Users/daxu/software/world-trader/campaign/agents/chief/coord}"
echo "================ GOAL100 STANDUP $(date '+%H:%M:%S') ================"
while read -r a || [ -n "$a" ]; do  # newline-less last line (AUDIT_GATES2 drop bug)
  [ -n "$a" ] || continue
  case "$a" in "#"*) continue ;; esac  # comments are annotations, not roles (TDD R4)
  f="$ROOT/$a/FINDINGS.md"
  if [ -f "$f" ] && grep -q "ROUND 1 DONE" "$f" 2>/dev/null; then
    status="DONE"
    # extract a short headline line near the end
    headline=$(grep -iE "PASS|DEAD|SAVED|sleeve|SR|ann" "$f" | tail -1 | cut -c1-120)
  elif ps aux | grep -q "[c]hief/coord/$a"; then
    status="RUNNING"
    headline=""
  else
    status="NOT-STARTED"
    headline=""
  fi
  printf "  %-22s %-11s %s\n" "$a" "$status" "$headline"
done < "$ROOT/AGENTS.txt"

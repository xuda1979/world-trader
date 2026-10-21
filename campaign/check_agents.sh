#!/bin/bash
# Coordinator helper: report iter6.5 agent status (DONE / IN-FLIGHT / DEBUG).
cd /Users/daxu/software/world-trader/campaign
for a in BLOTTER_TESTER BLOTTER_FIXER HUNT_INDUSTRY48 HUNT_LIQREV HUNT_OVNIGHT AUDIT_LEVFRONTIER HUNT_CROSSASSET2 HUNT_FXDEPO HUNT_VOLOVERLAY AUDIT_V3 SKILL_ALPHAAGB_B AUDIT_FRAMEWORK VERIFY_BEST DATA_MORE_ETF DATA_MORE_FRED DATA_MORE_CRYPTO HUNT_VXV_TERM HUNT_CRYPTO_SAT HUNT_SECTOR_FULL; do
  f="agents/loop_team/$a/FINDINGS.md"
  if [ -f "$f" ] && [[ "$(tail -1 "$f")" == *"DONE"* ]]; then
    echo "DONE        $a"
  elif ps aux | grep "claude -p" | grep -v grep | grep -q "$a"; then
    n=$(ls agents/loop_team/$a/scratch 2>/dev/null | wc -l)
    echo "IN-FLIGHT   $a (scratch=$n)"
  else
    echo "STALLED     $a (no FINDINGS, not running)"
  fi
done

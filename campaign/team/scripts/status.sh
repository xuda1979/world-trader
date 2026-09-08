#!/bin/bash
# Team standup status: DONE / IN-FLIGHT / STALLED per chartered agent.
# DONE = FINDINGS tail == "<AGENT> DONE". IN-FLIGHT = a claude -p proc started after this agent
# (log is NOT the same second as launch). STALLED = neither. Per ai-devops: a proc that exited 0
# but did nothing (API 429 at start) must show STALLED, so also require a non-empty FINDINGS or
# growing log before trusting IN-FLIGHT.
TEAM="/Users/daxu/software/world-trader/campaign/team"
now=$(date +%s)
for AGENT in DATA_PULL DATA_ORGANIZE DATA_CLEAN DATA_MERGE DATA_MAESTRO \
             INFRA_STRUCTURE INFRA_REFACTOR QA_TESTS QA_AUDIT \
             RES_BASIS RES_CALENDAR RES_META RES_VOL RES_CREDIT \
             RES_CARRY RES_REVERSAL RES_STATARB; do
  F="$TEAM/agents/$AGENT/FINDINGS.md"; LOG="$TEAM/agents/$AGENT/LOG.log"
  if [ -f "$F" ] && [[ "$(tail -1 "$F")" == "$AGENT DONE" ]]; then
    echo "DONE      $AGENT"
    continue
  fi
  running=$(ps aux | grep -c "[c]laude -p")
  if [ "$running" -gt 0 ] && [ -f "$LOG" ]; then
    age=$(( now - $(stat -f %m "$LOG") ))
    # only call it IN-FLIGHT if we've seen agent output (a real session), not a 429 stub
    if [ "$age" -lt 600 ] || [ -s "$F" ]; then echo "IN-FLIGHT $AGENT (log ${age}s)"; continue; fi
  fi
  echo "STALLED   $AGENT"
done

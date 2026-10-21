#!/bin/bash
# Launch S independent audit/backtest agents in parallel (campaign multi-agent pattern)
cd /Users/daxu/software/world-trader/campaign/work_backtest_oos
N=${1:-12}
PIDS=()
for i in $(seq 0 $((N-1))); do
  python3 agent.py "$i" >> "agent_work/agent_${i}.runlog" 2>&1 &
  PIDS+=($!)
done
FAIL=0
for PID in "${PIDS[@]}"; do
  wait $PID || FAIL=1
done
if [ $FAIL -eq 0 ]; then echo "ALL $N AGENTS COMPLETE"; else echo "some agent(s) failed"; fi

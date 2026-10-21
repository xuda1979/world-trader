#!/bin/bash
# Standup 2026-09-07 21:3x: keeper pid 37891 (started 18:04) exits at ~00:04 on its
# 6h window with 9 agents still pending R4. This wrapper waits for that keeper to
# exit, then starts a fresh keeper. Safe: fleet_keeper defaults ROUND via
# ROUND_DEFAULT (kept current with the fleet); launch_all.sh skips DONE agents,
# holds a single-instance lock, caps concurrency 4.
# Standup 2026-09-08 19:2x: DROPPED the hardcoded `ROUND="${ROUND:-5}"` default -
# a stale wrapper default OVERRIDES fleet_keeper.py's maintained ROUND_DEFAULT and
# re-runs an old DONE round (the 09:00:41 / 19:00:12 env-loss incident class).
# Pass ROUND explicitly when you mean to override; otherwise the script default
# tracks the fleet via fleet_keeper.py.
OLD=${1:-37891}
while kill -0 "$OLD" 2>/dev/null; do sleep 60; done
if [ -n "$ROUND" ]; then
  exec env ROUND="$ROUND" python3 /Users/daxu/software/world-trader/campaign/agents/chief/coord/fleet_keeper.py
else
  exec python3 /Users/daxu/software/world-trader/campaign/agents/chief/coord/fleet_keeper.py
fi

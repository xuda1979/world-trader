#!/bin/bash
# gateway_login_retry.sh — single-attempt IB Gateway paper login + port-4002 check.
# Designed to be called by cron every 2 hours; exits fast if gateway already up.
# Paper-only: TradingMode=paper, port 4002 (IBKR paper API). Never touches live (4001).
#
# Usage: gateway_login_retry.sh [timeout_seconds]
# Exit codes: 0 = gateway up (port 4002 listening); 1 = login failed this attempt.

TIMEOUT=${1:-300}
IBC_START=/Users/daxu/software/ibc/scripts/ibcstart.sh
IBC_PATH=/Users/daxu/software/ibc
LOG=/Users/daxu/ibc/logs/retry-$(date +%Y%m%d-%H%M%S).log

# Fast exit: gateway already up?
if lsof -iTCP:4002 -sTCP:LISTEN >/dev/null 2>&1; then
    echo "$(date '+%F %T') port 4002 already listening — nothing to do"
    exit 0
fi

# No zombie sessions
pkill -f ibcalpha 2>/dev/null
sleep 2

echo "$(date '+%F %T') launching IBC gateway (paper mode, port 4002)" | tee -a "$LOG"
nohup bash "$IBC_START" 10.50 -g --ibc-path="$IBC_PATH" --mode=paper >> "$LOG" 2>&1 &
IBC_PID=$!

# Poll for port 4002
deadline=$(( $(date +%s) + TIMEOUT ))
while [ "$(date +%s)" -lt "$deadline" ]; do
    if lsof -iTCP:4002 -sTCP:LISTEN >/dev/null 2>&1; then
        echo "$(date '+%F %T') SUCCESS: port 4002 listening (pid $IBC_PID)" | tee -a "$LOG"
        exit 0
    fi
    # Early-exit on explicit auth failure in the IBC log
    if grep -q "Unrecognized Username or Password" "$LOG" 2>/dev/null; then
        echo "$(date '+%F %T') AUTH FAILED (Unrecognized Username or Password)" | tee -a "$LOG"
        pkill -f ibcalpha 2>/dev/null; pkill -P $IBC_PID 2>/dev/null; kill $IBC_PID 2>/dev/null
        exit 1
    fi
    sleep 10
done

echo "$(date '+%F %T') TIMEOUT after ${TIMEOUT}s — port 4002 not up; cleaning up" | tee -a "$LOG"
pkill -f ibcalpha 2>/dev/null; pkill -P $IBC_PID 2>/dev/null; kill $IBC_PID 2>/dev/null
exit 1

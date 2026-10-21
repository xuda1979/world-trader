#!/usr/bin/env bash
# world-trader loop scan: runs every 30m via launchd.
# Surfaces NEW funding-arb and cross-exchange edges vs the previous run.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${WT_PYTHON:-/Users/daxu/homebrew/bin/python3}"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"
STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAYLOG="$LOGDIR/loop-$(date '+%Y-%m-%d').log"
LATEST="$LOGDIR/loop-latest.txt"
{
  echo "########## LOOP $STAMP ##########"
  "$PY" "$HERE/loop_scan.py" 2>&1
  echo ""
} | tee "$LATEST" >> "$DAYLOG"

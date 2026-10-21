#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
PY="${WT_PYTHON:-/Users/daxu/homebrew/bin/python3}"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"
STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAYLOG="$LOGDIR/digest-$(date '+%Y-%m-%d').log"
{
  echo "########## DIGEST $STAMP ##########"
  "$PY" "$HERE/daily_digest.py" 2>&1
  echo ""
} | tee -a "$DAYLOG"

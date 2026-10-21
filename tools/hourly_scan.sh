#!/usr/bin/env bash
# Produce the world-trader opportunity table once, with timestamped logging.
# Designed to be run hourly by cron.
#
#   manual run:   tools/hourly_scan.sh
#   day log:      tools/logs/scan-YYYY-MM-DD.log   (appended, one file per day)
#   latest table: tools/logs/latest.txt            (overwritten each run)

set -euo pipefail

# Repo root = parent of this script's dir (so cron's cwd doesn't matter).
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
PY="${WT_PYTHON:-/Users/daxu/homebrew/bin/python3}"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"

cd "$ROOT"

STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAYLOG="$LOGDIR/scan-$(date '+%Y-%m-%d').log"
LATEST="$LOGDIR/latest.txt"

# --quiet prints just the ranked opportunity table; set WT_SCAN_ARGS=--full for news+altdata.
ARGS="${WT_SCAN_ARGS:---quiet}"

{
  echo "########## RUN $STAMP ##########"
  "$PY" tools/scan.py $ARGS 2>&1
  echo ""
} | tee "$LATEST" >> "$DAYLOG"

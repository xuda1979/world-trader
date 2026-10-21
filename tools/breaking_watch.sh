#!/usr/bin/env bash
# Breaking-news catalyst watcher: runs every 5 min via launchd.
#
# Single-pass detect -> resolve -> enrich -> alert. Dedups across runs via
# tools/logs/breaking-events.json. Only NEW events trigger an alert.
#
#   manual run:   tools/breaking_watch.sh
#   day log:      tools/logs/breaking-watch-YYYY-MM-DD.log
#   event cache:  tools/logs/breaking-events.json
#
# Tune detection thresholds via env vars:
#   WT_BREAKING_HOURS=6        # RSS lookback window
#   WT_BREAKING_MIN_SEV=3      # min severity (1-5)
#   WT_BREAKING_MIN_FEEDS=1    # min distinct feeds (2-3 = higher confidence)
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
PY="${WT_PYTHON:-/Users/daxu/homebrew/bin/python3}"
LOGDIR="$HERE/logs"
mkdir -p "$LOGDIR"

cd "$ROOT"

STAMP="$(date '+%Y-%m-%d %H:%M:%S %Z')"
DAYLOG="$LOGDIR/breaking-watch-$(date '+%Y-%m-%d').log"

HOURS="${WT_BREAKING_HOURS:-6}"
MIN_SEV="${WT_BREAKING_MIN_SEV:-3}"
MIN_FEEDS="${WT_BREAKING_MIN_FEEDS:-1}"

{
  echo "########## BREAKING-WATCH $STAMP (hours=$HOURS min_sev=$MIN_SEV min_feeds=$MIN_FEEDS) ##########"
  "$PY" tools/scan.py --breaking-watch --hours "$HOURS" \
      --min-severity "$MIN_SEV" --min-feeds "$MIN_FEEDS" 2>&1
  echo ""
} >> "$DAYLOG"

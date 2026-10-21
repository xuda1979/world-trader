#!/usr/bin/env bash
# Install/refresh the world-trader hourly scan as a launchd agent (sleep-safe,
# survives reboot, catches up after wake). Idempotent: safe to re-run.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.worldtrader.hourly-scan"
SRC="$HERE/$LABEL.plist"
DST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_NUM="$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents"
cp "$SRC" "$DST"
launchctl bootout "gui/$UID_NUM/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_NUM" "$DST"
echo "installed $LABEL -> runs hourly (minute 0). Logs: tools/logs/"
launchctl print "gui/$UID_NUM/$LABEL" 2>/dev/null | grep -E "state|path" | head -3 || true
